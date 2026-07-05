"""orchestration — L5.

Registry loader, reference resolution, cell expansion, config validation, and
(from Phase 6) the stage runner, gate enforcement, and manifest emission.

This ``__init__`` is intentionally kept import-light: submodules are imported
explicitly (``from faithfulids.orchestration.config_loader import ...``) so that
lightweight CI jobs (config validation, cell-expansion tests) do not drag in the
scientific stack, and so that importing the package never triggers a heavy
detector/LLM import.
"""

from __future__ import annotations
