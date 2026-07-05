"""paper — figure/table generation + assembly.

**Boundary:** nothing under ``paper/`` imports ``faithfulids`` (enforced by a
grep gate in ``figure-regen.yml``). Figure/table scripts read only
``analysis/outputs/**``; the manuscript includes graphics only from
``*/generated/``.
"""

from __future__ import annotations
