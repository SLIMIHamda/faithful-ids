"""Layer-2 targets the class the attribution explains (queue #5.4)."""

from __future__ import annotations

import pytest

from faithfulids.framework import AttributionArtifact
from faithfulids.metrics.layer2 import SimpleBackgroundErasure, comprehensiveness
from faithfulids.metrics.layer2.metrics import _target_class

_BG = SimpleBackgroundErasure({"A": 0.0, "B": 0.0})
_INSTANCE = {"A": 1.0, "B": 1.0}


class _MultiDetector:
    """3-class detector whose ARGMAX FLIPS when A is erased:
    A=1 -> DoS wins (0.7); A=0 -> BENIGN wins (0.6) and DoS collapses to 0.2."""

    feature_names = ("A", "B")
    class_names = ("BENIGN", "DoS", "PortScan")

    def predict_proba(self, rows):
        return [[0.1, 0.7, 0.2] if r["A"] >= 1.0 else [0.6, 0.2, 0.2] for r in rows]

    def predicted_class(self, rows):
        return [self.class_names[max(range(len(p)), key=p.__getitem__)]
                for p in self.predict_proba(rows)]


def _attr(explained_class):
    return AttributionArtifact(
        instance_id="i0", feature_names=("A", "B"), values=(0.9, 0.1),
        base_value=0.0, method="x", exact=True, background_policy="ref",
        explained_class=explained_class,
    )


def test_delta_is_taken_on_the_pinned_class_not_the_post_erasure_argmax():
    """The target is pinned from the UNERASED instance. Erasing A flips the argmax
    to BENIGN; the drop must still be measured on DoS (0.7 -> 0.2 = 0.5). Reading
    the post-erasure argmax instead would give 0.7 - 0.6 = 0.1 — a number that
    compares two DIFFERENT classes and means nothing."""
    got = comprehensiveness(_attr("DoS"), _MultiDetector(), _INSTANCE, _BG, k=1)
    assert got == pytest.approx(0.5)


def test_target_follows_the_class_the_attribution_explains():
    det = _MultiDetector()
    # the artifact's stamped class wins (5.3b provenance)
    assert _target_class(det, _INSTANCE, "PortScan") == "PortScan"
    # ...and a PortScan-explaining attribution is scored on PortScan: 0.2 -> 0.2 = 0.0
    assert comprehensiveness(_attr("PortScan"), det, _INSTANCE, _BG, k=1) == pytest.approx(0.0)


def test_unstamped_multiclass_attribution_falls_back_to_the_predicted_class():
    det = _MultiDetector()
    assert _target_class(det, _INSTANCE, None) == "DoS"  # argmax on the FULL instance
    assert comprehensiveness(_attr(None), det, _INSTANCE, _BG, k=1) == pytest.approx(0.5)


class _BinaryDetector:
    feature_names = ("A", "B")
    class_names = ("BENIGN", "ATTACK")

    def predict_proba(self, rows):
        # benign-PREDICTED instance (attack prob 0.2)
        return [[0.8, 0.2] for _ in rows]

    def predicted_class(self, rows):
        return ["BENIGN" for _ in rows]


def test_binary_keeps_the_attack_side_even_when_benign_is_predicted():
    """Continuity: a binary attribution explains the attack side for EVERY instance
    (5.3), so Layer-2 measures that side — the pilot's established semantics. Using
    the predicted class here would silently flip benign rows to the BENIGN column
    and move every existing binary Layer-2 number."""
    assert _target_class(_BinaryDetector(), _INSTANCE, None) == "ATTACK"


def test_unknown_target_class_fails_loudly():
    from faithfulids.metrics.layer2.metrics import _detector_score

    with pytest.raises(ValueError, match="not one of"):
        _detector_score(_MultiDetector(), [_INSTANCE], "prob", "Ransomware")
