"""B4 — Verify-then-Explain (L3).

kb_retrieval + generator + internal verifier (firewall side A) + abstention.
On abstention the output degrades to B1 (never silence).
"""

from __future__ import annotations

from faithfulids.generation.b4_vte.generator import B4VtE, build

__all__ = ["B4VtE", "build"]
