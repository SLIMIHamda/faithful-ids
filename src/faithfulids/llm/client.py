"""Provider-agnostic LLM client (L2).

The client wraps a *provider* (the thing that actually runs a model) with:

* an **append-only ledger** of every call (enables L3 replay);
* **pinned-snapshot enforcement** (a model with no pinned revision/snapshot is
  refused — an unpinned model is irreproducible);
* a **cache-only replay mode** (no network / no GPU; a cache miss is a hard error).

Generators and the extractor talk only to this client, never to a provider
directly, so provenance is captured uniformly. The client imports no model
framework — the concrete provider (transformers / API) is injected.
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Mapping, Protocol, runtime_checkable

from faithfulids.llm.ledger import CallLedger
from faithfulids.provenance.hashing import content_address


class UnpinnedModelError(RuntimeError):
    """Raised when a model config lacks a pinned snapshot/revision."""


class ReplayMiss(RuntimeError):
    """Raised in replay mode when a request is absent from the ledger."""


@runtime_checkable
class LLMProvider(Protocol):
    """Runs a prompt on a concrete model and returns text + metadata."""

    def complete(
        self, prompt: str, params: Mapping[str, Any], *, model: Mapping[str, Any]
    ) -> tuple[str, dict[str, Any]]: ...


def pinned_snapshot(model_config: Mapping[str, Any]) -> str:
    """Return the pinned snapshot/revision, or raise if the model is unpinned."""
    provider = model_config.get("provider")
    if provider == "frontier_api":
        sid = (model_config.get("api") or {}).get("snapshot_id")
    else:
        sid = (model_config.get("weights") or {}).get("revision")
    if not sid:
        raise UnpinnedModelError(
            f"model {model_config.get('id', '<?>')} has no pinned snapshot/revision — "
            "an unpinned model is not reproducible (refused)."
        )
    return str(sid)


@dataclass(frozen=True)
class LLMRequest:
    model_id: str
    model_family: str
    snapshot_id: str
    prompt: str
    params: Mapping[str, Any] = field(default_factory=dict)

    @property
    def request_hash(self) -> str:
        return content_address(
            {
                "model_id": self.model_id,
                "snapshot_id": self.snapshot_id,
                "prompt": self.prompt,
                "params": dict(self.params),
            }
        )


@dataclass(frozen=True)
class LLMResponse:
    text: str
    model_snapshot_id: str
    request_hash: str
    tokens: int | None
    latency_ms: float | None
    timestamp_utc: str
    cached: bool


class LLMClient:
    """Ledger-backed client. ``mode`` is ``"live"`` or ``"replay"``."""

    def __init__(self, provider: LLMProvider | None, ledger: CallLedger, *, mode: str = "live") -> None:
        if mode not in ("live", "replay"):
            raise ValueError("mode must be 'live' or 'replay'")
        if mode == "live" and provider is None:
            raise ValueError("live mode requires a provider")
        self.provider = provider
        self.ledger = ledger
        self.mode = mode

    def complete(
        self, *, model_config: Mapping[str, Any], prompt: str, params: Mapping[str, Any]
    ) -> LLMResponse:
        snapshot = pinned_snapshot(model_config)
        req = LLMRequest(
            model_id=model_config["id"],
            model_family=model_config["model_family"],
            snapshot_id=snapshot,
            prompt=prompt,
            params=params,
        )
        h = req.request_hash

        hit = self.ledger.lookup(h)
        if hit is not None:
            return LLMResponse(
                text=hit["response_text"],
                model_snapshot_id=hit["snapshot_id"],
                request_hash=h,
                tokens=hit.get("tokens"),
                latency_ms=hit.get("latency_ms"),
                timestamp_utc=hit["timestamp_utc"],
                cached=True,
            )

        if self.mode == "replay":
            raise ReplayMiss(
                f"replay miss for request {h[:12]}… (model {req.model_id}@{snapshot}). "
                "Cache-only replay does not contact the network — the ledger is "
                "missing this call."
            )

        assert self.provider is not None
        t0 = time.perf_counter()
        text, meta = self.provider.complete(prompt, params, model=model_config)
        latency_ms = (time.perf_counter() - t0) * 1000.0
        ts = datetime.now(timezone.utc).isoformat()
        record = {
            "request_hash": h,
            "model_id": req.model_id,
            "model_family": req.model_family,
            "snapshot_id": snapshot,
            "prompt": prompt,
            "params": dict(params),
            "response_text": text,
            "tokens": meta.get("tokens"),
            "latency_ms": latency_ms,
            "timestamp_utc": ts,
        }
        self.ledger.append(record)
        return LLMResponse(
            text=text,
            model_snapshot_id=snapshot,
            request_hash=h,
            tokens=meta.get("tokens"),
            latency_ms=latency_ms,
            timestamp_utc=ts,
            cached=False,
        )
