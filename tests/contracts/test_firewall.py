"""The circularity firewall passes its mechanical audit."""

from __future__ import annotations

import importlib.util
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]


def _load_firewall_module():
    spec = importlib.util.spec_from_file_location(
        "firewall_check", REPO / "tools" / "firewall_check.py"
    )
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def test_firewall_audit_passes():
    mod = _load_firewall_module()
    errors = mod.run()
    assert errors == [], "firewall violations:\n" + "\n".join(errors)
