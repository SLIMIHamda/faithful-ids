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

# Direction cues are matched as substrings, so entries are STEMS: "increas"
# covers increase/increases/increased/increasing. Extractor 1.2.0: the previous
# inflected-form lists missed participles — "has a decreasing effect on the
# attack score" (Qwen3-8B's dominant B4 phrasing) matched nothing and fell to
# the default-POSITIVE branch, mis-signing 63/150 instances (blind audit
# 2026-07-11, extractor_audit_batch_v1). "increasing" fell through identically
# but the POSITIVE default made it accidentally correct, hiding the bug.
_POS_WORDS = ("increas", "rais", "higher", "elevat", "push")
_NEG_WORDS = ("decreas", "lower", "reduc")

# A signed attribution value attached to a feature. B0 dumps raw SHAP as
# "Feature=-7.9774" (sign-only, NO direction word), which the word-based parser
# was defaulting to POSITIVE — collapsing DSA. Prefer the '=' form, then a
# standalone explicitly-signed number. Unsigned magnitudes ("(magnitude 0.80)",
# "by 4.55") deliberately do NOT match, so B1/B3 keep their word-driven signs.
_NUM_AFTER_EQ = re.compile(r"=\s*([+-]?\d+(?:\.\d+)?)")
_NUM_SIGNED = re.compile(r"(?<![\w.])([+-]\d+(?:\.\d+)?)")


class RuleAssistedExtractor(ClaimExtractor):
    def __init__(
        self,
        config: Mapping[str, Any],
        llm_client,
        model_config: Mapping[str, Any],
        feature_vocabulary: Sequence[str],
    ) -> None:
        self.extractor_id = config["id"]
        # Instrument version (bumps on prompt OR rule-engine change), NOT the
        # prompt-asset version — a rule-engine fix must be visible in provenance.
        self.extractor_version = config["version"]
        self.prompt_sha256 = config["prompt"]["sha256"]
        self._template = load_prompt(
            config["prompt"]["name"], config["prompt"]["version"],
            expected_sha256=self.prompt_sha256,
        )
        self._client = llm_client
        self._model = model_config
        self._vocab = list(feature_vocabulary)

    def extract(self, explanation: ExplanationRecord) -> ClaimSet:
        if self._client is None:
            # rule-only mode (pilot / no extractor model loaded): deterministic
            # regex parse over the canonical feature vocabulary.
            claims = self._rule_assisted(explanation.text)
        else:
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
        """Deterministic fallback: locate vocab features + their claimed sign.

        Two audit fixes (extractor 1.1.0, gate EXP-G-001): (1) match features
        longest-first and mask consumed spans so a shorter feature name cannot
        also match *inside* a longer one (e.g. "Packet Length Mean" inside "Fwd
        Packet Length Mean") — residual-span guard; (2) recover the claimed sign
        from an attached signed number when no direction word is present, so a
        raw-SHAP dump (B0) is parsed with the correct sign instead of defaulting
        every claim to POSITIVE. Extractor 1.2.0: direction words are stem-
        matched so participle phrasings ("a decreasing effect") carry their sign
        instead of falling through to the default (see _NEG_WORDS note).
        """
        lowered = text.lower()
        consumed = [False] * len(lowered)
        found: list[tuple[int, str]] = []
        for feat in sorted(self._vocab, key=len, reverse=True):
            fl = feat.lower()
            start = lowered.find(fl)
            while start != -1:
                if not any(consumed[start : start + len(fl)]):
                    for i in range(start, start + len(fl)):
                        consumed[i] = True
                    found.append((start, feat))
                    break
                start = lowered.find(fl, start + 1)
        found.sort()
        claims: list[ClaimTuple] = []
        for rank, (pos, feat) in enumerate(found, start=1):
            end = pos + len(feat)
            nxt = found[rank][0] if rank < len(found) else len(lowered)
            window = lowered[end : min(nxt, end + 60)]
            direction, magnitude = self._direction_of(window)
            claims.append(
                ClaimTuple(feature=feat, direction=direction, rank=rank, magnitude=magnitude)
            )
        return claims

    @staticmethod
    def _direction_of(window: str) -> tuple[Direction, float | None]:
        """Claimed sign for a feature, from the text span up to the next feature.

        Precedence: an explicit direction *word* (B1/B3 wording) wins; else a
        *signed number* attached to the feature (B0 raw-SHAP dump); else default
        POSITIVE. Word-first keeps B1/B3 unchanged — the numeric branch only ever
        fires on sign-only dumps, which is exactly where DSA was collapsing.
        """
        if any(w in window for w in _NEG_WORDS):
            return Direction.NEGATIVE, None
        if any(w in window for w in _POS_WORDS):
            return Direction.POSITIVE, None
        m = _NUM_AFTER_EQ.search(window) or _NUM_SIGNED.search(window)
        if m:
            value = float(m.group(1))
            return Direction.from_value(value), abs(value)
        return Direction.POSITIVE, None


def build(
    config: Mapping[str, Any], *, llm_client, model_config: Mapping[str, Any],
    feature_vocabulary: Sequence[str],
) -> RuleAssistedExtractor:
    return RuleAssistedExtractor(config, llm_client, model_config, feature_vocabulary)
