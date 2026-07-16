"""Generation shared helpers + lazy generator dispatch (L3).

Adding a generator (B5) is a new subpackage + config + prompt tree with **zero**
evaluation-code edits (blueprint §7). Generators are dispatched lazily by their
config ``code``; the runner injects the dependencies a given generator needs
(LLM client + model config for B2–B4; KB for B4). Generators may not import
``metrics`` (import-linter edge 3).
"""

from __future__ import annotations

import importlib
from dataclasses import dataclass

from faithfulids.framework import AttributionArtifact, Direction, Generator

# generator config `code` -> implementing subpackage
GENERATOR_MODULES: dict[str, str] = {
    "b0_raw_shap": "faithfulids.generation.b0_raw_shap",
    "b1_template": "faithfulids.generation.b1_template",
    "b2_zeroshot": "faithfulids.generation.b2_zeroshot",
    "b3_dte_style": "faithfulids.generation.b3_dte_style",
    "b4_vte": "faithfulids.generation.b4_vte",
}


@dataclass(frozen=True)
class RankedFeature:
    feature: str
    value: float
    direction: Direction
    rank: int  # 1-indexed


def ranked_topk(attribution: AttributionArtifact, top_k: int) -> list[RankedFeature]:
    """Top-k features by descending |attribution|, with sign-derived direction."""
    order = sorted(
        range(len(attribution.values)),
        key=lambda i: abs(attribution.values[i]),
        reverse=True,
    )[:top_k]
    out: list[RankedFeature] = []
    for rank, i in enumerate(order, start=1):
        val = attribution.values[i]
        out.append(
            RankedFeature(
                feature=attribution.feature_names[i],
                value=val,
                direction=Direction.from_value(val),
                rank=rank,
            )
        )
    return out


def feature_value_table(feature_values: dict) -> str:
    """Deterministic 'name = value' table (sorted by name) for zero-shot prompts."""
    return "\n".join(f"- {k} = {feature_values[k]}" for k in sorted(feature_values))


def ranked_feature_list(rows: list[RankedFeature], score_label: str = "attack") -> str:
    """Deterministic ranked list with direction words for DTE/VtE prompts.

    ``score_label`` is the noun of the score the attribution explains
    (``GenerationContext.score_label``): the binary default "attack" keeps the
    rendered string byte-identical to every cached run (request-hash continuity);
    a multi-class run passes the predicted class name so "increases BENIGN score"
    is literally true. Keeps the increases/decreases verbs the extractor's
    direction stems and the rule verifier's evidence regex parse.
    """
    lines = []
    for r in rows:
        word = "increases" if r.direction is Direction.POSITIVE else "decreases"
        lines.append(f"{r.rank}. {r.feature} ({word} {score_label} score, magnitude {abs(r.value):.4f})")
    return "\n".join(lines)


def load_prompt_pair(config: dict) -> tuple[str, str | None]:
    """Load a generator's frozen prompt template plus its optional multi-class
    variant (``prompt_multiclass`` in the generator config), both hash-verified.

    Two pinned versions, selected at runtime by ``select_template``: the binary
    v1.0.0 wording is baked into every cached run's LLM request hashes, so it can
    never be edited in place — multi-class rewording lives in its own registered
    semver instead.
    """
    from faithfulids.llm import load_prompt

    p = config["prompt"]
    template = load_prompt(p["name"], p["version"], expected_sha256=p["sha256"])
    mp = config.get("prompt_multiclass")
    template_mc = (
        load_prompt(mp["name"], mp["version"], expected_sha256=mp["sha256"]) if mp else None
    )
    return template, template_mc


def select_template(template: str, template_multiclass: str | None, score_label: str) -> str:
    """Pick the prompt variant for this instance's task (see GenerationContext).

    ``score_label == "attack"`` is the binary task -> the frozen binary template.
    Anything else is a class name from a K-way run -> the multi-class variant,
    and its absence is a hard error: falling back to attack-framed wording would
    render false directions for BENIGN-predicted instances.
    """
    if score_label == "attack":
        return template
    if template_multiclass is None:
        raise ValueError(
            f"multi-class generation (score_label={score_label!r}) requires a "
            "prompt_multiclass entry in the generator config; the binary prompt's "
            "attack-framed wording would be false for BENIGN-predicted instances."
        )
    return template_multiclass


def get_generator(config: dict, **deps) -> Generator:
    """Lazily import the generator subpackage for ``config['code']`` and build it."""
    code = config["code"]
    if code not in GENERATOR_MODULES:
        raise KeyError(f"unknown generator code: {code!r}")
    mod = importlib.import_module(GENERATOR_MODULES[code])
    return mod.build(config, **deps)
