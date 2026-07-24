"""results — L5, the READ-ONLY results API.

Load ``runs/**`` by id with hash verification. The only ``src`` module
``analysis/`` may import; exposes no execution capability. Imports only L0
(``provenance``) — never ``orchestration``/``generation``/``llm``.
"""

from __future__ import annotations

from faithfulids.results.api import (
    ResultError,
    RunHandle,
    is_complete_and_verified,
    list_runs,
    load_metrics,
    load_run,
    run_extractor_version,
)

__all__ = [
    "ResultError",
    "RunHandle",
    "load_run",
    "load_metrics",
    "list_runs",
    "is_complete_and_verified",
    "run_extractor_version",
]
