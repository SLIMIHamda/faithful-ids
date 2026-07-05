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
    """Open-weights provider via HuggingFace ``transformers`` (hard dependency).

    Loads the model named in ``model['weights']`` at its pinned revision, honours
    ``model['quantisation']`` (``none`` -> fp16, ``4bit`` -> nf4), caches loaded
    models across calls, and generates deterministically at the given seed.
    ``transformers``/``torch`` are imported lazily so importing this module (and
    the orchestration layer) never pulls them in.
    """

    def __init__(self, *, max_new_tokens: int = 220) -> None:
        self.max_new_tokens = max_new_tokens
        self._cache: dict[tuple, tuple] = {}

    def _load(self, model: Mapping[str, Any]):
        weights = model.get("weights") or {}
        repo = weights.get("hf_repo")
        revision = weights.get("revision")
        quant = model.get("quantisation", "none")
        key = (repo, revision, quant)
        if key in self._cache:
            return self._cache[key]
        import torch
        from transformers import AutoModelForCausalLM, AutoTokenizer

        tok = AutoTokenizer.from_pretrained(repo, revision=revision)
        kwargs: dict[str, Any] = {"device_map": "auto"}
        if quant == "4bit":
            from transformers import BitsAndBytesConfig

            kwargs["quantization_config"] = BitsAndBytesConfig(
                load_in_4bit=True,
                bnb_4bit_compute_dtype=torch.float16,
                bnb_4bit_quant_type="nf4",
            )
        else:
            kwargs["torch_dtype"] = torch.float16
        mdl = AutoModelForCausalLM.from_pretrained(repo, revision=revision, **kwargs)
        mdl.eval()
        self._cache[key] = (tok, mdl)
        return tok, mdl

    def complete(
        self, prompt: str, params: Mapping[str, Any], *, model: Mapping[str, Any]
    ) -> tuple[str, dict[str, Any]]:
        import torch

        tok, mdl = self._load(model)
        torch.manual_seed(int(params.get("seed", 0)))
        temperature = float(params.get("temperature", 0.0))
        try:
            input_ids = tok.apply_chat_template(
                [{"role": "user", "content": prompt}],
                add_generation_prompt=True, return_tensors="pt",
            ).to(mdl.device)
        except Exception:
            input_ids = tok(prompt, return_tensors="pt").input_ids.to(mdl.device)

        gen_kwargs: dict[str, Any] = {
            "max_new_tokens": self.max_new_tokens,
            "do_sample": temperature > 0,
            "pad_token_id": tok.eos_token_id,
        }
        if temperature > 0:
            gen_kwargs["temperature"] = temperature
        with torch.no_grad():
            out = mdl.generate(input_ids, **gen_kwargs)
        new_tokens = out[0][input_ids.shape[1]:]
        text = tok.decode(new_tokens, skip_special_tokens=True).strip()
        return text, {"tokens": int(new_tokens.shape[0])}


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
