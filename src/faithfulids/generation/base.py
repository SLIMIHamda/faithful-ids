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


def ranked_feature_list(rows: list[RankedFeature]) -> str:
    """Deterministic ranked list with direction words for DTE/VtE prompts."""
    lines = []
    for r in rows:
        word = "increases" if r.direction is Direction.POSITIVE else "decreases"
        lines.append(f"{r.rank}. {r.feature} ({word} attack score, magnitude {abs(r.value):.4f})")
    return "\n".join(lines)


def get_generator(config: dict, **deps) -> Generator:
    """Lazily import the generator subpackage for ``config['code']`` and build it."""
    code = config["code"]
    if code not in GENERATOR_MODULES:
        raise KeyError(f"unknown generator code: {code!r}")
    mod = importlib.import_module(GENERATOR_MODULES[code])
    return mod.build(config, **deps)
