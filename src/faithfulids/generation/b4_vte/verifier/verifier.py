"""VtE internal verifier — FIREWALL SIDE A (L3).

Checks a drafted explanation against its evidence *inside the generator*. This
module may NEVER import ``faithfulids.extraction`` (the evaluation extractor,
firewall side B) or ``faithfulids.metrics`` — enforced by import-linter edges 2b
and 3 and by ``tools/firewall_check.py`` (prompt-hash + model-family
disjointness). The verifier implements its own checking logic; it does not reuse
any evaluation code.
"""

from __future__ import annotations

import re
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
        supported, reason = read_verdict(resp.text)
        return VerifierVerdict(supported, resp.request_hash, reason)


_VERDICT_LINE = re.compile(r"^(?:(?:FINAL\s+)?VERDICT\s*)?(SUPPORTED|UNSUPPORTED)$")


def read_verdict(reply: str) -> tuple[bool, str]:
    """(supported, reason) from a verifier reply, read off its verdict line.

    The prompt asks for "a single verdict token on its own line", so the verdict
    is the LAST line holding only ``SUPPORTED`` or ``UNSUPPORTED`` (markdown,
    code fences, quotes and a "Verdict:" label stripped). Amendment 0011: the
    first reader searched the whole reply for the word, so a model that repeats
    the prompt's check 3 ("Are there unsupported ... claims?") before answering
    SUPPORTED was read as UNSUPPORTED — every Phi-4 approval was. A reply with no
    verdict line is still not supported (fail-safe: abstain, show B1).
    """
    verdict = None
    for line in reply.splitlines():
        cleaned = re.sub(r"[\s`*_\"'.:!>#-]+", " ", line).strip().upper()
        m = _VERDICT_LINE.match(cleaned)
        if m:
            verdict = m.group(1)
    if verdict == "SUPPORTED":
        return True, "supported"
    return False, "unsupported_token" if verdict == "UNSUPPORTED" else "no_verdict_token"
