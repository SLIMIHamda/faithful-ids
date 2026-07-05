"""Dataset loader interfaces (L1).

Loaders read the *frozen, processed* feature matrices produced upstream by the
correction + processing pipeline. They never download, never mutate raw data,
and fail loudly with acquisition guidance when the payload is absent (the
datasets are not redistributed — hostile-audit A3).
"""

from __future__ import annotations

import abc
from pathlib import Path

import pandas as pd


class DataUnavailable(RuntimeError):
    """Raised when a processed dataset payload has not been materialised."""


class DatasetLoader(abc.ABC):
    dataset_id: str

    @abc.abstractmethod
    def load_processed(self) -> pd.DataFrame:
        """Return the processed feature matrix for this dataset."""


class ProcessedParquetLoader(DatasetLoader):
    """Generic loader for a processed feature matrix stored as parquet."""

    def __init__(self, dataset_id: str, processed_root: str | Path) -> None:
        self.dataset_id = dataset_id
        self._path = Path(processed_root) / dataset_id / "features.parquet"

    def load_processed(self) -> pd.DataFrame:
        if not self._path.is_file():
            raise DataUnavailable(
                f"processed payload for {self.dataset_id!r} not found at {self._path}. "
                "Datasets are not redistributed — acquire the raw data and run "
                "`make data DATASET=<id>` (see REPRODUCING.md)."
            )
        return pd.read_parquet(self._path)


def get_loader(dataset_id: str, processed_root: str | Path) -> DatasetLoader:
    """Return the loader for a dataset. All current datasets share the parquet
    format; a dataset with a bespoke format registers its own subclass here."""
    return ProcessedParquetLoader(dataset_id, processed_root)
