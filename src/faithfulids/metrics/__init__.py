"""metrics — L4, STRUCTURALLY generator-blind.

Consumes framework schemas + extracted claims + attributions + detector outputs
and returns numbers. Metric signatures cannot receive generator identity;
grouping keys are attached downstream by orchestration. May NOT import
``generation`` (import-linter edge 1).

Submodules are imported explicitly (``metrics.layer1``, ``metrics.layer2``,
``metrics.meta``, ``metrics.plausibility``, ``metrics.cost``) so a lightweight
consumer of only Layer-1/Layer-2 need not pull in ``scipy`` (used by meta /
plausibility). This ``__init__`` therefore imports nothing eagerly.
"""

from __future__ import annotations
