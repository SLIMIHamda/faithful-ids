"""The comprehensiveness x sufficiency 2x2 (prereg amendment 0003).

Comprehensiveness alone cannot distinguish a cited set whose signal is carried by
a correlated *substitute* from one that is simply irrelevant: both erase to
nearly no score change. Sufficiency separates them, because the two quantities
fail in OPPOSITE directions under correlation.

Conventions, as implemented in ``faithfulids.metrics.layer2.metrics``::

    comprehensiveness = s_full - s_erased   HIGH is good
    sufficiency       = s_full - s_kept     LOW  is good

                    | sufficiency LOW          | sufficiency HIGH
    compr. LOW      | redundant                | irrelevant
    compr. HIGH     | load_bearing             | necessary_not_sufficient

This module is pure arithmetic over already-computed metric values; it never
re-runs erasure. Every verdict is relative to the run's removal operator R
(``resolved_config.layer2_erasure_operator``) — a redundancy verdict under the
conditional imputer is a statement about that operator, not about the detector.
"""

from __future__ import annotations

from typing import Iterable, Sequence

#: Fixed order — reported tables and their tests iterate this, not dict order.
CELLS: tuple[str, ...] = (
    "load_bearing",
    "necessary_not_sufficient",
    "redundant",
    "irrelevant",
)


def classify(comprehensiveness: float, sufficiency: float, threshold: float) -> str:
    """Return the 2x2 cell for one (comprehensiveness, sufficiency) pair.

    ``threshold`` is applied to both axes as ``value >= threshold`` => HIGH, so a
    value exactly on the threshold counts as HIGH on both axes.
    """
    high_c = float(comprehensiveness) >= threshold
    high_s = float(sufficiency) >= threshold
    if high_c:
        return "necessary_not_sufficient" if high_s else "load_bearing"
    return "irrelevant" if high_s else "redundant"


def _empty_counts() -> dict[str, int]:
    return {cell: 0 for cell in CELLS}


def tabulate(
    records: Iterable[dict],
    threshold: float,
    group_keys: Sequence[str] = ("predicted_class", "generator_id"),
) -> dict:
    """Classify ``records`` and count cells overall and per grouping key.

    Each record is ``{"comprehensiveness": float, "sufficiency": float, ...}``
    plus any of ``group_keys``. Records whose grouping value is ``None`` (e.g.
    ``predicted_class`` on a binary run, ``generator_id`` on generator-blind
    eps_att rows) are counted in the total but omitted from that breakdown, so
    an absent breakdown reads as absent rather than as a "None" class.
    """
    counts = _empty_counts()
    breakdowns: dict[str, dict[str, dict[str, int]]] = {k: {} for k in group_keys}
    n = 0
    for rec in records:
        cell = classify(rec["comprehensiveness"], rec["sufficiency"], threshold)
        counts[cell] += 1
        n += 1
        for key in group_keys:
            value = rec.get(key)
            if value is None:
                continue
            breakdowns[key].setdefault(str(value), _empty_counts())[cell] += 1
    return {
        "n": n,
        "threshold": threshold,
        "counts": counts,
        "fractions": {cell: (counts[cell] / n if n else 0.0) for cell in CELLS},
        "by": {
            key: {g: table for g, table in sorted(tables.items())}
            for key, tables in breakdowns.items()
            if tables
        },
    }
