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


def _fake_ollama(monkeypatch, blob_sha, template="{{ .Prompt }}"):
    sent = []

    def urlopen(req, timeout=None):
        body = json.loads(req.data.decode("utf-8"))
        sent.append((req.full_url, body))
        if req.full_url.endswith("/api/show"):
            out = {"modelfile": f"FROM /root/.ollama/models/blobs/sha256-{blob_sha}\n",
                   "template": template}
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


def _library_model(template_text):
    import hashlib

    return {
        "id": "vte_verifier", "model_family": "phi", "provider": "local_open_weights",
        "runtime": "ollama", "weights": {"revision": f"sha256-{PIN}", "sha256": PIN},
        "ollama": {"model_name": "phi4-mini:3.8b-q4_K_M", "think": None,
                   "template_sha256": hashlib.sha256(template_text.encode("utf-8")).hexdigest()},
    }


def test_ollama_library_model_checks_its_template_and_sends_no_think(monkeypatch):
    # amendments 0008/0009: a library build's chat template is pinned too, and a
    # model with no thinking mode is not sent the field at all
    sent = _fake_ollama(monkeypatch, PIN, template="<|user|>{{ .Content }}")
    OllamaProvider(base_url="http://h:1").complete(
        "check", {"temperature": 0, "seed": 0}, model=_library_model("<|user|>{{ .Content }}"))
    assert "think" not in sent[-1][1]
    _fake_ollama(monkeypatch, PIN, template="<|user|>{{ .Content }} changed")
    with pytest.raises(RuntimeError, match="chat template"):
        OllamaProvider(base_url="http://h:1").complete(
            "check", {}, model=_library_model("<|user|>{{ .Content }}"))


def test_verifier_and_judge_pin_library_builds():
    from faithfulids.orchestration.config_loader import load_config

    b4 = load_config("generator", "b4_vte")["verifier"]
    b5 = load_config("generator", "b5_narrative_vte")["verifier"]
    judge = load_config("metric", "plausibility_judge")["judge"]
    assert b4["model"] == b5["model"]  # one verifier instrument for B4 and B5
    for block, family in ((b4, "phi"), (judge, "command_r")):
        m = block["model"]
        assert block["model_family"] == family and m["runtime"] == "ollama"
        assert m["weights"]["sha256"] in m["weights"]["revision"]
        assert m["ollama"]["model_name"] == m["weights"]["ref"]
        assert len(m["ollama"]["template_sha256"]) == 64 and m["ollama"]["think"] is None


def test_eval_extractor_pins_the_gguf_it_runs():
    from faithfulids.orchestration.config_loader import load_config

    m = load_config("extraction", "eval_extractor")["model"]
    assert m["runtime"] == "ollama" and m["model_family"] == "gemma"
    assert len(m["weights"]["sha256"]) == 64 and len(m["weights"]["revision"]) == 40
    assert m["weights"]["file"].endswith(".gguf") and m["ollama"]["model_name"]
