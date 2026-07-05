"""The append-only LLM call ledger (L2).

Every request/response is logged with its request hash, full payload, model
snapshot id, timestamp, latency, and tokens. This ledger is what makes
reproduction tier **L3** possible: deterministic replay without GPU/API access
(hostile-audit A1). It is append-only — a request hash maps to the response that
was recorded for it; entries are never rewritten.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

LEDGER_FILE = "ledger.jsonl"


class CallLedger:
    """Append-only JSONL ledger keyed by request hash."""

    def __init__(self, ledger_dir: str | Path) -> None:
        self.dir = Path(ledger_dir)
        self.path = self.dir / LEDGER_FILE
        self._index: dict[str, dict[str, Any]] | None = None

    def _load_index(self) -> dict[str, dict[str, Any]]:
        index: dict[str, dict[str, Any]] = {}
        if self.path.is_file():
            for line in self.path.read_text(encoding="utf-8").splitlines():
                if not line.strip():
                    continue
                rec = json.loads(line)
                # append-only: first occurrence of a request_hash wins
                index.setdefault(rec["request_hash"], rec)
        self._index = index
        return index

    @property
    def index(self) -> dict[str, dict[str, Any]]:
        if self._index is None:
            return self._load_index()
        return self._index

    def lookup(self, request_hash: str) -> dict[str, Any] | None:
        return self.index.get(request_hash)

    def append(self, record: dict[str, Any]) -> None:
        if "request_hash" not in record:
            raise ValueError("ledger record must carry request_hash")
        self.dir.mkdir(parents=True, exist_ok=True)
        with open(self.path, "a", encoding="utf-8") as fh:
            fh.write(json.dumps(record, sort_keys=True) + "\n")
        if self._index is not None:
            self._index.setdefault(record["request_hash"], record)

    def __len__(self) -> int:
        return len(self.index)
