"""The evaluation claim extractor — FIREWALL SIDE B (L3).

Parses an explanation's free text into structured :class:`ClaimTuple`s. Its
model family and prompt are disjoint from the VtE verifier (side A); it may NOT
import ``faithfulids.generation`` (import-linter edge 2a). Rule-assisted: it
tries the LLM's JSON output first, then a deterministic regex fallback over the
canonical feature vocabulary — so a faithful, template-shaped explanation (B1)
is parsed correctly even without a live model, which is what makes B1's
faithful-by-construction property checkable end-to-end.

Its validity as an instrument is established by gate EXP-G-001; orchestration
refuses Layer-1 metrics for any run without a passing extractor-audit reference.
"""

from __future__ import annotations

import json
import re
from typing import Any, Mapping, Sequence

from faithfulids.framework import (
    ClaimExtractor,
    ClaimSet,
    ClaimTuple,
    Direction,
    ExplanationRecord,
)
from faithfulids.llm import load_prompt

_POS_WORDS = ("increase", "increased", "raise", "raised", "higher", "elevat", "push")
_NEG_WORDS = ("decrease", "decreased", "lower", "lowered", "reduce", "reduced")


class RuleAssistedExtractor(ClaimExtractor):
    def __init__(
        self,
        config: Mapping[str, Any],
        llm_client,
        model_config: Mapping[str, Any],
        feature_vocabulary: Sequence[str],
    ) -> None:
        self.extractor_id = config["id"]
        self.extractor_version = config["prompt"]["version"]
        self.prompt_sha256 = config["prompt"]["sha256"]
        self._template = load_prompt(
            config["prompt"]["name"], config["prompt"]["version"],
            expected_sha256=self.prompt_sha256,
        )
        self._client = llm_client
        self._model = model_config
        self._vocab = list(feature_vocabulary)

    def extract(self, explanation: ExplanationRecord) -> ClaimSet:
        prompt = self._template.replace(
            "{{explanation_text}}", explanation.text
        ).replace("{{feature_vocabulary}}", ", ".join(self._vocab))
        resp = self._client.complete(
            model_config=self._model, prompt=prompt, params={"temperature": 0, "seed": 0}
        )
        claims = self._parse_json(resp.text)
        if claims is None:
            claims = self._rule_assisted(explanation.text)
        return ClaimSet(
            instance_id=explanation.instance_id,
            claims=tuple(claims),
            extractor_id=self.extractor_id,
            extractor_version=self.extractor_version,
            prompt_sha256=self.prompt_sha256,
        )

    def _parse_json(self, text: str) -> list[ClaimTuple] | None:
        start, end = text.find("["), text.rfind("]")
        if start == -1 or end == -1 or end < start:
            return None
        try:
            data = json.loads(text[start : end + 1])
        except json.JSONDecodeError:
            return None
        out: list[ClaimTuple] = []
        for d in data:
            try:
                out.append(
                    ClaimTuple(
                        feature=str(d["feature"]),
                        direction=Direction.from_str(d["direction"]),
                        rank=d.get("rank"),
                        magnitude=d.get("magnitude"),
                    )
                )
            except (KeyError, ValueError):
                continue
        return out

    def _rule_assisted(self, text: str) -> list[ClaimTuple]:
        """Deterministic fallback: locate vocab features + nearby direction words."""
        lowered = text.lower()
        found: list[tuple[int, str]] = []
        for feat in self._vocab:
            pos = lowered.find(feat.lower())
            if pos != -1:
                found.append((pos, feat))
        found.sort()
        claims: list[ClaimTuple] = []
        for rank, (pos, feat) in enumerate(found, start=1):
            window = lowered[pos : pos + len(feat) + 40]
            direction = Direction.NEGATIVE if any(w in window for w in _NEG_WORDS) else (
                Direction.POSITIVE if any(w in window for w in _POS_WORDS) else Direction.POSITIVE
            )
            claims.append(ClaimTuple(feature=feat, direction=direction, rank=rank))
        return claims


def build(
    config: Mapping[str, Any], *, llm_client, model_config: Mapping[str, Any],
    feature_vocabulary: Sequence[str],
) -> RuleAssistedExtractor:
    return RuleAssistedExtractor(config, llm_client, model_config, feature_vocabulary)
