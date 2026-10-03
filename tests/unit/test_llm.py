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


# --- OllamaProvider (amendment 0005): no server needed, urlopen is faked ------

import io  # noqa: E402
import json  # noqa: E402

from faithfulids.llm.providers import OllamaProvider  # noqa: E402

PIN = "3eca3b8f" + "0" * 56
OLLAMA_MODEL = {
    "id": "eval_extractor", "model_family": "gemma", "provider": "local_open_weights",
    "runtime": "ollama", "weights": {"revision": "rev-gguf", "sha256": PIN},
    "ollama": {"model_name": "fids-gemma"},
}


def _fake_ollama(monkeypatch, blob_sha):
    sent = []

    def urlopen(req, timeout=None):
        body = json.loads(req.data.decode("utf-8"))
        sent.append((req.full_url, body))
        if req.full_url.endswith("/api/show"):
            out = {"modelfile": f"FROM /root/.ollama/models/blobs/sha256-{blob_sha}\n"}
        else:
            out = {"message": {"content": ' [{"feature": "A", "direction": "+"}] '},
                   "eval_count": 12, "done_reason": "stop"}
        return io.BytesIO(json.dumps(out).encode("utf-8"))

    monkeypatch.setattr("urllib.request.urlopen", urlopen)
    return sent


def test_ollama_provider_sends_greedy_no_thinking_request(monkeypatch):
    sent = _fake_ollama(monkeypatch, PIN)
    p = OllamaProvider(base_url="http://h:1", max_new_tokens=1024)
    text, meta = p.complete("parse this", {"temperature": 0, "seed": 0}, model=OLLAMA_MODEL)
    assert text == '[{"feature": "A", "direction": "+"}]'
    assert meta == {"tokens": 12}
    url, body = sent[-1]
    assert url == "http://h:1/api/chat"
    assert body["model"] == "fids-gemma" and body["think"] is False
    assert body["options"]["temperature"] == 0.0 and body["options"]["seed"] == 0
    assert body["options"]["num_predict"] == 1024
    # the blob check runs once, not per call
    p.complete("again", {"temperature": 0, "seed": 0}, model=OLLAMA_MODEL)
    assert [u for u, _ in sent].count("http://h:1/api/show") == 1


def test_ollama_provider_refuses_unpinned_blob(monkeypatch):
    _fake_ollama(monkeypatch, "f" * 64)
    with pytest.raises(RuntimeError, match="not the pinned file"):
        OllamaProvider(base_url="http://h:1").complete("p", {}, model=OLLAMA_MODEL)


def test_ollama_provider_refuses_missing_sha(monkeypatch):
    _fake_ollama(monkeypatch, PIN)
    model = {**OLLAMA_MODEL, "weights": {"revision": "rev-gguf", "sha256": None}}
    with pytest.raises(RuntimeError, match="not pinned"):
        OllamaProvider(base_url="http://h:1").complete("p", {}, model=model)


def test_eval_extractor_pins_the_gguf_it_runs():
    from faithfulids.orchestration.config_loader import load_config

    m = load_config("extraction", "eval_extractor")["model"]
    assert m["runtime"] == "ollama" and m["model_family"] == "gemma"
    assert len(m["weights"]["sha256"]) == 64 and len(m["weights"]["revision"]) == 40
    assert m["weights"]["file"].endswith(".gguf") and m["ollama"]["model_name"]
