"""Figure/table specs: the committed generated asset matches its expected hash.

This is the unit-test form of the figure-regen gate: a spec whose generated
(deterministic) asset does not hash to ``expected_sha256`` fails. Skips when the
asset has not been generated in this checkout.
"""

from __future__ import annotations

import hashlib
from pathlib import Path

import pytest
import yaml

REPO = Path(__file__).resolve().parents[2]
SPECS = [
    "paper/figures/specs/fig_cd_diagram.yaml",
    "paper/figures/specs/fig_coverage_risk.yaml",
    "paper/tables/specs/tab_layer1_summary.yaml",
]


@pytest.mark.parametrize("spec_path", SPECS)
def test_generated_asset_matches_spec_hash(spec_path):
    spec = yaml.safe_load((REPO / spec_path).read_text(encoding="utf-8"))
    generated = REPO / spec["generated"]
    if not generated.is_file():
        pytest.skip(f"{spec['generated']} not generated in this checkout")
    digest = hashlib.sha256(generated.read_bytes()).hexdigest()
    assert digest == spec["expected_sha256"], f"{spec['id']}: regenerate + update the spec hash"
