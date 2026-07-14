"""VtE internal verifier — FIREWALL SIDE A (L3).

Checks a drafted explanation against its evidence *inside the generator*. This
module may NEVER import ``faithfulids.extraction`` (the evaluation extractor,
firewall side B) or ``faithfulids.metrics`` — enforced by import-linter edges 2b
and 3 and by ``tools/firewall_check.py`` (prompt-hash + model-family
disjointness). The verifier implements its own checking logic; it does not reuse
any evaluation code.
"""

from __future__ import annotations

from typing import Any, Mapping

from faithfulids.generation.b4_vte.verifier.verdict import VerifierVerdict
from faithfulids.llm import load_prompt


class Verifier:
    def __init__(self, verifier_config: Mapping[str, Any], llm_client, model_config: Mapping[str, Any]) -> None:
        p = verifier_config["prompt"]
        self.template = load_prompt(p["name"], p["version"], expected_sha256=p["sha256"])
        self.client = llm_client
        self.model = model_config
        self.model_family = verifier_config["model_family"]

    def verify(self, draft_text: str, ranked_feature_list: str, *, seed: int) -> VerifierVerdict:
        """Return a :class:`VerifierVerdict` (``call_id`` = the verifier call hash).

        The verifier prompt emits a ``SUPPORTED`` / ``UNSUPPORTED`` verdict token;
        anything not clearly SUPPORTED is treated as unsupported (fail-safe →
        abstention → B1 fallback, never silence). ``reason`` records which token
        pattern drove the verdict, for the abstention trace.
        """
        prompt = self.template.replace(
            "{{ranked_feature_list}}", ranked_feature_list
        ).replace("{{draft_explanation}}", draft_text)
        resp = self.client.complete(
            model_config=self.model, prompt=prompt, params={"temperature": 0, "seed": seed}
        )
        text = resp.text.upper()
        supported = "SUPPORTED" in text and "UNSUPPORTED" not in text
        reason = "supported" if supported else (
            "unsupported_token" if "UNSUPPORTED" in text else "no_verdict_token"
        )
        return VerifierVerdict(supported, resp.request_hash, reason)
