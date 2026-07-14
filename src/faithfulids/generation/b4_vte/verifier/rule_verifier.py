"""Rule-based VtE verifier — FIREWALL SIDE A (L3).

A deterministic grounding checker used for the **pilot** (so only one LLM need be
loaded on constrained hardware). It checks a drafted explanation against the
ranked SHAP evidence with rules — no model, no evaluation-code import. Declares
model family ``rule_verifier`` (disjoint from every generator LLM and the
extractor). The confirmatory path uses the LLM :class:`Verifier` instead.
"""

from __future__ import annotations

import re

from faithfulids.generation.b4_vte.verifier.verdict import VerifierVerdict

_EVIDENCE_RE = re.compile(r"^\s*\d+\.\s*(?P<feat>.+?)\s*\((?P<dir>increases|decreases)\b", re.M)
_POS = ("increase", "increased", "higher", "raise", "raised", "elevat", "push", "more")
_NEG = ("decrease", "decreased", "lower", "lowered", "reduce", "reduced", "less")


class RuleVerifier:
    model_family = "rule_verifier"

    def verify(self, draft_text: str, ranked_feature_list: str, *, seed: int = 0) -> VerifierVerdict:
        """Return a :class:`VerifierVerdict`.

        SUPPORTED iff the draft cites at least one evidence feature and every
        cited feature's stated direction is consistent with the evidence sign.
        Anything else → UNSUPPORTED (→ abstain → B1 fallback, never silence). The
        verdict's ``reason``/``detail`` record which of those gates failed (the
        abstention trace).
        """
        def _v(supported: bool, reason: str, **detail) -> VerifierVerdict:
            return VerifierVerdict(supported, self.model_family, reason, detail)

        evidence = {m.group("feat").strip().lower(): m.group("dir") for m in _EVIDENCE_RE.finditer(ranked_feature_list)}
        if not evidence:
            return _v(False, "no_evidence")
        draft = draft_text.lower()
        cited = [f for f in evidence if f in draft]
        if not cited:
            return _v(False, "no_cited_feature", n_evidence=len(evidence))
        for feat in cited:
            pos = draft.find(feat)
            window = draft[pos : pos + len(feat) + 60]
            says_pos = any(w in window for w in _POS)
            says_neg = any(w in window for w in _NEG)
            ev = evidence[feat]
            if ev == "increases" and says_neg and not says_pos:
                return _v(False, "direction_mismatch", feature=feat, evidence_dir=ev)
            if ev == "decreases" and says_pos and not says_neg:
                return _v(False, "direction_mismatch", feature=feat, evidence_dir=ev)
        return _v(True, "supported", n_cited=len(cited))
