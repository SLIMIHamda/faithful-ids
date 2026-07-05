"""Concrete LLM providers (L2).

The client is provider-agnostic; a provider actually runs a model. Real
providers (open-weights via ``transformers``, frontier API) import heavy
dependencies and are structured but marked TODO so they fail loudly rather than
returning fabricated text. The deterministic stub is **not a scientific model**:
it exists solely so the toy pipeline and the L3-replay determinism CI have a
byte-stable, offline "LLM"; the runner selects it only for EXP-TOY-* and never
for a citable run.
"""

from __future__ import annotations

import hashlib
from typing import Any, Mapping


class DeterministicStubProvider:
    """A byte-stable, offline pseudo-LLM for the toy pipeline / replay CI ONLY.

    Produces a deterministic function of (prompt, params) — never a scientific
    output. Its purpose is to make the determinism gate meaningful without a GPU
    or network, exactly as the implementation prompt's toy pipeline requires.
    """

    #: exposed so the ledger/manifest can record that a NON-CITABLE stub was used
    snapshot_id = "deterministic-stub-v1"

    def complete(
        self, prompt: str, params: Mapping[str, Any], *, model: Mapping[str, Any]
    ) -> tuple[str, dict[str, Any]]:
        seed = int(params.get("seed", 0))
        digest = hashlib.sha256(
            (prompt + "|" + repr(sorted(params.items()))).encode("utf-8")
        ).hexdigest()
        # A deterministic, clearly-synthetic response. NOT a scientific result.
        text = f"[STUB:{digest[:8]}:seed{seed}] deterministic toy response."
        return text, {"tokens": len(prompt.split()), "stub": True}


class TransformersProvider:
    """Open-weights provider via HuggingFace ``transformers`` (hard dependency)."""

    def complete(
        self, prompt: str, params: Mapping[str, Any], *, model: Mapping[str, Any]
    ) -> tuple[str, dict[str, Any]]:
        import transformers  # noqa: F401  hard dep; imported here to keep client light

        raise NotImplementedError(
            "TODO: load the pinned open-weights model (model['weights']) at the "
            "recorded revision, run generation at params temperature/top_k/seed, and "
            "return (text, meta). Fails loudly rather than emitting fabricated text."
        )


class FrontierAPIProvider:
    """Frontier-API provider with a pinned model snapshot id (replay-cache required)."""

    def complete(
        self, prompt: str, params: Mapping[str, Any], *, model: Mapping[str, Any]
    ) -> tuple[str, dict[str, Any]]:
        raise NotImplementedError(
            "TODO: call the frontier provider at model['api']['snapshot_id'] and log "
            "the full request/response to the ledger. All frontier numbers are "
            "replay-verifiable (L3), not re-executable."
        )
