"""tools/recheck_verifier.py (amendment 0010): stored verifier prompts, sent to the current pin."""

from __future__ import annotations

import csv
import json
import sys

from faithfulids.llm import load_prompt
from faithfulids.orchestration.config_loader import load_config
from faithfulids.provenance import repo_root

sys.path.insert(0, str(repo_root() / "tools"))
from recheck_verifier import recheck, split_prompt  # noqa: E402

EVIDENCE = "1. Flow Duration (increases DDoS score, magnitude 0.9000)"
DRAFT = "Flow Duration increases the DDoS score."


def _old_ledger(tmp_path):
    p = load_config("generator", "b4_vte")["verifier"]["prompt"]
    prompt = load_prompt(p["name"], p["version"], expected_sha256=p["sha256"]).replace(
        "{{ranked_feature_list}}", EVIDENCE).replace("{{draft_explanation}}", DRAFT)
    rec = {"model_id": "vte_verifier_phi4_mini", "prompt": prompt,
           "params": {"temperature": 0, "seed": 3}, "response_text": "UNSUPPORTED\n- invented"}
    d = tmp_path / "old"
    d.mkdir()
    (d / "ledger.jsonl").write_text(json.dumps(rec) + "\n", encoding="utf-8")
    return d, prompt


class _Phi:
    def __init__(self):
        self.sent = []

    def complete(self, prompt, params, *, model):
        self.sent.append((prompt, dict(params), model["id"]))
        return "1. yes\n2. yes\n3. no\nSUPPORTED", {"tokens": 6}


def test_split_prompt_recovers_evidence_and_draft(tmp_path):
    _, prompt = _old_ledger(tmp_path)
    assert split_prompt(prompt) == (EVIDENCE, DRAFT)


def test_recheck_sends_the_stored_prompt_to_the_current_pin(tmp_path):
    old, prompt = _old_ledger(tmp_path)
    phi = _Phi()
    s = recheck(old, tmp_path / "out", provider=phi)
    assert phi.sent == [(prompt, {"temperature": 0, "seed": 3}, "vte_verifier_phi4_14b")]
    assert s["old_verdicts"] == {"unsupported_token": 1} and s["new_verdicts"] == {"supported": 1}
    rows = list(csv.DictReader((tmp_path / "out" / "review.csv").open(encoding="utf-8-sig")))
    assert rows[0]["evidence"] == EVIDENCE and rows[0]["draft"] == DRAFT
    assert rows[0]["author_rejection_wrong"] == ""
    # the new ledger replays without the model
    assert recheck(old, tmp_path / "out", mode="replay")["new_verdicts"] == {"supported": 1}
