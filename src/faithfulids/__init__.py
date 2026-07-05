"""faithfulids — the layered library serving the beyond-plausibility registry.

Layers (import strictly downward; enforced by import-linter in CI):

    L0  framework, provenance
    L1  datasets
    L2  detectors, attribution, llm
    L3  generation, extraction, corruption
    L4  metrics
    L5  orchestration, results

There is deliberately no ``utils``/``common``/``helpers``/``misc`` module: every
module maps to a scientific responsibility named in ``REPOSITORY_BLUEPRINT.md``.

The version here is the *library* version. The *artifact* version (v1.0 =
submission, ...) is tracked in ``CHANGELOG.md`` and ``CITATION.cff``.
"""

from __future__ import annotations

__all__ = ["__version__"]
__version__ = "1.0.0-dev"
