"""Feature-semantics KB (1.1.0) — coverage + integrity of the grounding corpus."""

from __future__ import annotations

import yaml

from faithfulids.provenance import repo_root


def _kb():
    p = repo_root() / "kb" / "feature_semantics" / "cicids2017.yaml"
    return yaml.safe_load(p.read_text(encoding="utf-8"))


def test_entries_are_unique_and_complete():
    kb = _kb()
    names = [e["name"] for e in kb["entries"]]
    assert len(names) == len(set(names)), "duplicate feature names in the KB"
    assert len(names) >= 76  # full runtime vocabulary (was 8 — near-empty prompts)
    for e in kb["entries"]:
        assert e.get("description", "").strip(), f"empty description: {e['name']}"
        assert e.get("units", "").strip(), f"missing units: {e['name']}"


def test_alias_canonical_targets_are_all_described():
    """Every canonical feature the extraction alias table can map TO must have a
    KB description — otherwise a recovered paraphrase cites a feature the
    grounding corpus cannot explain."""
    aliases = yaml.safe_load(
        (repo_root() / "configs" / "extraction_aliases" / "feature_aliases.yaml")
        .read_text(encoding="utf-8")
    )
    kb_names = {e["name"] for e in _kb()["entries"]}
    targets = set(aliases.get("aliases", {}).keys()) or {
        a["canonical"] for a in aliases.get("entries", [])
    }
    missing = sorted(t for t in targets if t not in kb_names)
    assert not missing, f"alias canonical targets with no KB entry: {missing}"
