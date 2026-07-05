"""datasets.loaders — frozen processed-matrix loaders (L1)."""

from __future__ import annotations

from faithfulids.datasets.loaders.base import (
    DatasetLoader,
    DataUnavailable,
    ProcessedParquetLoader,
    get_loader,
)

__all__ = ["DatasetLoader", "DataUnavailable", "ProcessedParquetLoader", "get_loader"]
