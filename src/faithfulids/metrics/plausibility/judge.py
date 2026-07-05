"""Plausibility LLM-as-judge harness + validation (L4).

Plausibility ONLY, never faithfulness. The judge family is disjoint from every
explainer family (enforced by ``tools/firewall_check.py``). The judge is admitted
only if it validates against human ratings at Spearman ρ ≥ threshold, else it is
dropped. Order randomisation + length stratification are applied by the harness.
"""

from __future__ import annotations

import json
from typing import Any, Mapping, Sequence

from scipy.stats import spearmanr

from faithfulids.llm import load_prompt

DIMENSIONS = ("clarity", "helpfulness", "believability")


class PlausibilityJudge:
    def __init__(self, config: Mapping[str, Any], llm_client, model_config: Mapping[str, Any]) -> None:
        p = config["judge"]["prompt"]
        self._template = load_prompt(p["name"], p["version"], expected_sha256=p["sha256"])
        self._client = llm_client
        self._model = model_config
        self.family = config["judge"]["model_family"]

    def rate(self, explanation_text: str, *, seed: int = 0) -> dict[str, float] | None:
        prompt = self._template.replace("{{explanation_text}}", explanation_text)
        resp = self._client.complete(
            model_config=self._model, prompt=prompt, params={"temperature": 0, "seed": seed}
        )
        return parse_judge_scores(resp.text)


def parse_judge_scores(text: str) -> dict[str, float] | None:
    start, end = text.find("{"), text.rfind("}")
    if start == -1 or end == -1 or end < start:
        return None
    try:
        data = json.loads(text[start : end + 1])
    except json.JSONDecodeError:
        return None
    if not all(d in data for d in DIMENSIONS):
        return None
    return {d: float(data[d]) for d in DIMENSIONS}


def validate_judge(
    judge_scores: Sequence[float], human_scores: Sequence[float], threshold: float
) -> dict[str, Any]:
    """Judge validation gate: Spearman ρ vs human ratings; dropped if below."""
    rho, _p = spearmanr(judge_scores, human_scores)
    rho = float(rho) if rho == rho else 0.0
    return {"rho": rho, "threshold": threshold, "passed": rho >= threshold}
