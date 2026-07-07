"""Detector competence evaluation (L2) — imbalance-aware gate.

A near-perfect *aggregate* F1 on CICIDS2017 can hide a detector that is blind on a
rare attack family (e.g. Infiltration). Faithfulness measured on instances the
model classifies by luck is noise, so a run is gated on **macro-F1** AND a
**per-(attack-)family detection-recall floor** — evaluated on the very (held-out,
stratified) instances whose explanations will be scored. An explicit, logged
**exemption list** (in the detector config) covers families untrainable at pilot
scale. The full per-family table is emitted so the Tier-A stratification decision
has data behind it.

The detector is binary (attack vs benign); ``families`` carries the original
multiclass ``attack_class`` so recall can be reported per attack family even
though the classifier itself is binary.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping, Sequence


def _is_attack_family(name: str) -> bool:
    return str(name).strip().upper() != "BENIGN"


def classification_table(
    y_true: Sequence[int],
    y_pred: Sequence[int],
    families: Sequence[str],
    *,
    y_score: Sequence[float] | None = None,
) -> dict[str, Any]:
    """Binary macro-F1 / AUC / confusion + per-family detection recall.

    ``y_true`` / ``y_pred`` are 0/1 attack labels; ``families`` is the per-row
    ``attack_class`` (benign rows carry 'BENIGN'); ``y_score`` is the attack
    probability (for AUC), optional. Detection recall for an attack family is the
    fraction of its instances flagged attack; for benign it is the fraction
    correctly left benign (specificity).
    """
    from sklearn.metrics import confusion_matrix, f1_score, roc_auc_score

    yt = [int(v) for v in y_true]
    yp = [int(v) for v in y_pred]
    fam = [str(f).strip() for f in families]
    if not (len(yt) == len(yp) == len(fam)):
        raise ValueError("y_true, y_pred, families must be the same length")
    n = len(yt)

    macro_f1 = float(f1_score(yt, yp, average="macro", zero_division=0))
    accuracy = float(sum(int(a == b) for a, b in zip(yt, yp)) / n) if n else 0.0
    auc = None
    if y_score is not None and len(set(yt)) == 2:
        auc = float(roc_auc_score(yt, list(y_score)))
    tn, fp, fn, tp = (int(x) for x in confusion_matrix(yt, yp, labels=[0, 1]).ravel())

    per_family: dict[str, dict[str, Any]] = {}
    for f in sorted(set(fam)):
        idx = [i for i, g in enumerate(fam) if g == f]
        support = len(idx)
        is_atk = _is_attack_family(f)
        detected = sum(1 for i in idx if yp[i] == (1 if is_atk else 0))
        per_family[f] = {
            "support": support,
            "is_attack": is_atk,
            "detection_recall": float(detected / support) if support else 0.0,
        }

    return {
        "n": n,
        "macro_f1": macro_f1,
        "accuracy": accuracy,
        "auc": auc,
        "confusion": {"tn": tn, "fp": fp, "fn": fn, "tp": tp},
        "per_family": per_family,
    }


class DetectorNotCompetent(RuntimeError):
    """Raised when a trained detector fails the pre-registered competence gate."""


@dataclass(frozen=True)
class CompetenceResult:
    passed: bool
    macro_f1: float
    macro_f1_min: float
    recall_floor: float
    failures: tuple[tuple[str, float], ...]  # (attack family, recall) below floor, not exempted
    exemptions: tuple[str, ...]


def evaluate_competence(
    table: Mapping[str, Any],
    *,
    macro_f1_min: float,
    recall_floor: float,
    exemptions: Sequence[str] = (),
) -> CompetenceResult:
    """Apply the pre-registered gate to a ``classification_table`` result."""
    ex = {str(e).strip() for e in exemptions}
    failures = [
        (fam, float(row["detection_recall"]))
        for fam, row in table["per_family"].items()
        if row["is_attack"] and fam not in ex and row["detection_recall"] < recall_floor
    ]
    passed = (float(table["macro_f1"]) >= macro_f1_min) and not failures
    return CompetenceResult(
        passed=passed,
        macro_f1=float(table["macro_f1"]),
        macro_f1_min=macro_f1_min,
        recall_floor=recall_floor,
        failures=tuple(sorted(failures)),
        exemptions=tuple(sorted(ex)),
    )
