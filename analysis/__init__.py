"""analysis — statistics as a pure consumer of ``runs/**``.

This package may import **only** ``faithfulids.results`` (the read-only results
API) and ``faithfulids.framework`` (schemas). It can never trigger, import, or
re-run experiment code — enforced by import-linter forbidden edge 4
(``analysis -> orchestration | generation | llm | ...``).

Each analysis config enumerates the EXACT run IDs it consumes (no glob patterns).
"""

from __future__ import annotations
