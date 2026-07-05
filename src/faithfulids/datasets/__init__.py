"""datasets — L1.

Loaders, the deterministic Engelen/Lanvin correction pipeline, and frozen split
materialisation. Imports only L0 (framework, provenance). One-directional data
flow: raw -> corrected -> processed -> splits.
"""

from __future__ import annotations
