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

    def __init__(self, *, max_new_tokens: int = 160) -> None:
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
        kwargs: dict[str, Any] = {}
        if torch.cuda.is_available():
            # Pin to ONE GPU: the pilot models fit a single T4. 'auto' needlessly
            # splits a small model across GPUs and serialises generation (slower,
            # CPU-bound coordination). Override with $FAITHFULIDS_DEVICE_MAP=auto.
            import os as _os

            dm = _os.environ.get("FAITHFULIDS_DEVICE_MAP", "single")
            if dm == "auto":
                kwargs["device_map"] = "auto"
                # 'auto' fills GPUs sequentially with NO headroom, and bnb
                # quantizes module-by-module ON the target device — each module
                # transiently needs its fp16 size there (a 5120x25600 MLP shard
                # = 250 MiB), so a GPU packed to capacity with 4-bit weights
                # OOMs during load (seen with Qwen3-32B on 2x T4). Reserve
                # per-GPU headroom, which generation also needs for KV cache
                # and activations. Override: $FAITHFULIDS_GPU_HEADROOM_GIB.
                headroom_gib = float(_os.environ.get("FAITHFULIDS_GPU_HEADROOM_GIB", "2.0"))
                kwargs["max_memory"] = {
                    i: int(torch.cuda.get_device_properties(i).total_memory
                           - headroom_gib * 1024**3)
                    for i in range(torch.cuda.device_count())
                }
            else:
                kwargs["device_map"] = {"": 0}
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
        if torch.cuda.is_available():
            # Loud placement report: a 1-GPU session (wrong Kaggle accelerator)
            # or a lopsided map should be visible here, not as an OOM later.
            n = torch.cuda.device_count()
            alloc = {i: f"{torch.cuda.memory_allocated(i) / 2**30:.1f}GiB" for i in range(n)}
            devmap = getattr(mdl, "hf_device_map", None)
            spread: dict[str, int] = {}
            for v in (devmap or {}).values():
                spread[str(v)] = spread.get(str(v), 0) + 1
            print(
                f"[TransformersProvider] {repo}: loaded | visible_gpus={n} | "
                f"allocated={alloc} | modules_per_device={spread or kwargs.get('device_map')}"
            )
        self._cache[key] = (tok, mdl)
        return tok, mdl

    def complete(
        self, prompt: str, params: Mapping[str, Any], *, model: Mapping[str, Any]
    ) -> tuple[str, dict[str, Any]]:
        import torch

        tok, mdl = self._load(model)
        torch.manual_seed(int(params.get("seed", 0)))
        temperature = float(params.get("temperature", 0.0))

        # Qwen3 defaults to emitting a long <think>…</think> chain-of-thought
        # before its answer. At max_new_tokens=160 that reasoning is truncated
        # before the real explanation ever appears, so Layer-1 sees garbage
        # claims and collapses. Turn thinking OFF for Qwen3 only — guarded by
        # (model_family == "qwen" AND repo name starts with "Qwen3") so no other
        # model's chat template is touched. `enable_thinking` is a Qwen3
        # chat-template variable; escape hatch for debugging: set
        # $FAITHFULIDS_QWEN3_THINKING=1 to leave reasoning on.
        import os as _os

        template_kwargs: dict[str, Any] = {}
        hf_repo = (model.get("weights") or {}).get("hf_repo") or ""
        is_qwen3 = (
            model.get("model_family") == "qwen"
            and hf_repo.rsplit("/", 1)[-1].lower().startswith("qwen3")
        )
        if is_qwen3 and _os.environ.get("FAITHFULIDS_QWEN3_THINKING", "0") != "1":
            template_kwargs["enable_thinking"] = False

        # apply_chat_template may return a bare tensor OR a BatchEncoding depending
        # on the transformers version; normalise to a dict of tensors so
        # generate(**enc) works either way (a BatchEncoding passed positionally
        # would crash on .shape).
        try:
            raw = tok.apply_chat_template(
                [{"role": "user", "content": prompt}],
                add_generation_prompt=True, return_tensors="pt",
                **template_kwargs,
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
