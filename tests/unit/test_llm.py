"""LLM client: ledger, replay mode, pinned-snapshot enforcement."""

from __future__ import annotations

import pytest

from faithfulids.llm import CallLedger, LLMClient, ReplayMiss, UnpinnedModelError
from faithfulids.llm.providers import DeterministicStubProvider

MODEL = {
    "id": "llama31_8b_instruct",
    "model_family": "llama3",
    "provider": "local_open_weights",
    "weights": {"revision": "rev-abc"},
}


def test_live_call_is_logged_then_replayed_from_cache(tmp_path):
    ledger = CallLedger(tmp_path)
    client = LLMClient(DeterministicStubProvider(), ledger, mode="live")
    r1 = client.complete(model_config=MODEL, prompt="hello", params={"seed": 1})
    assert r1.cached is False
    assert len(ledger) == 1
    r2 = client.complete(model_config=MODEL, prompt="hello", params={"seed": 1})
    assert r2.cached is True
    assert r2.text == r1.text  # deterministic + cached


def test_replay_mode_hits_and_misses(tmp_path):
    ledger = CallLedger(tmp_path)
    LLMClient(DeterministicStubProvider(), ledger, mode="live").complete(
        model_config=MODEL, prompt="seen", params={"seed": 1}
    )
    replay = LLMClient(None, ledger, mode="replay")
    hit = replay.complete(model_config=MODEL, prompt="seen", params={"seed": 1})
    assert hit.cached is True
    with pytest.raises(ReplayMiss):
        replay.complete(model_config=MODEL, prompt="unseen", params={"seed": 9})


def test_unpinned_model_is_refused(tmp_path):
    client = LLMClient(DeterministicStubProvider(), CallLedger(tmp_path), mode="live")
    unpinned = {
        "id": "x", "model_family": "y", "provider": "local_open_weights",
        "weights": {"revision": None},
    }
    with pytest.raises(UnpinnedModelError):
        client.complete(model_config=unpinned, prompt="p", params={})


def test_stub_provider_is_deterministic():
    p = DeterministicStubProvider()
    a, _ = p.complete("prompt", {"seed": 3}, model=MODEL)
    b, _ = p.complete("prompt", {"seed": 3}, model=MODEL)
    assert a == b
