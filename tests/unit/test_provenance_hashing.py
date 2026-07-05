"""Content hashing: canonicalisation, stability, and content-addressing."""

from __future__ import annotations

from faithfulids.provenance import (
    canonical_json,
    content_address,
    sha256_file,
    sha256_json,
    sha256_text,
)


def test_canonical_json_is_key_order_independent():
    a = {"b": 1, "a": 2, "nested": {"y": 1, "x": 2}}
    b = {"a": 2, "nested": {"x": 2, "y": 1}, "b": 1}
    assert canonical_json(a) == canonical_json(b)
    assert sha256_json(a) == sha256_json(b)


def test_sha256_text_is_stable_and_hex64():
    h = sha256_text("beyond-plausibility")
    assert len(h) == 64
    assert h == sha256_text("beyond-plausibility")


def test_content_address_changes_when_any_input_changes():
    base = {"model_sha": "a" * 64, "data_sha": "b" * 64, "attr_cfg_sha": "c" * 64}
    addr = content_address(base)
    changed = dict(base, data_sha="d" * 64)
    assert content_address(changed) != addr
    # unchanged inputs reproduce the same address (no silent regeneration)
    assert content_address(dict(base)) == addr


def test_sha256_file(tmp_path):
    p = tmp_path / "x.bin"
    p.write_bytes(b"hello world")
    assert sha256_file(p) == sha256_text("hello world")
