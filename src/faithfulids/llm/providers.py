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
        import os

        weights = model.get("weights") or {}
        repo = weights.get("hf_repo")
        revision = weights.get("revision")
        quant = model.get("quantisation", "none")
        # 'pin-pending' is the honest "not yet pinned" sentinel; passing it to the
        # Hub raises (it is not a valid ref). For a NON-CITABLE run fall back to the
        # model's default branch and say so. Pin a real commit sha for a citable run.
        if not revision or revision == "pin-pending":
            print(
                f"[TransformersProvider] {repo}: revision unpinned ({revision!r}) -> "
                "using the default branch (NON-CITABLE; pin a commit sha to make it citable)."
            )
            revision = None
        token = os.environ.get("HF_TOKEN") or None

        key = (repo, revision, quant)
        if key in self._cache:
            return self._cache[key]
        import torch
        from transformers import AutoModelForCausalLM, AutoTokenizer

        tok = AutoTokenizer.from_pretrained(repo, revision=revision, token=token)
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
        mdl = AutoModelForCausalLM.from_pretrained(
            repo, revision=revision, token=token, **kwargs
        )
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

        # apply_chat_template may return a bare tensor OR a BatchEncoding depending
        # on the transformers version; normalise to a dict of tensors so
        # generate(**enc) works either way (a BatchEncoding passed positionally
        # would crash on .shape).
        try:
            raw = tok.apply_chat_template(
                [{"role": "user", "content": prompt}],
                add_generation_prompt=True, return_tensors="pt",
            )
        except Exception:
            raw = tok(prompt, return_tensors="pt")
        if isinstance(raw, torch.Tensor):
            enc = {"input_ids": raw}
        else:  # BatchEncoding / dict
            enc = {k: raw[k] for k in raw.keys()}
        enc = {k: v.to(mdl.device) for k, v in enc.items()}
        input_len = enc["input_ids"].shape[1]

        gen_kwargs: dict[str, Any] = {
            "max_new_tokens": self.max_new_tokens,
            "do_sample": temperature > 0,
            "pad_token_id": tok.eos_token_id,
        }
        if temperature > 0:
            gen_kwargs["temperature"] = temperature
        with torch.no_grad():
            out = mdl.generate(**enc, **gen_kwargs)
        new_tokens = out[0][input_len:]
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
