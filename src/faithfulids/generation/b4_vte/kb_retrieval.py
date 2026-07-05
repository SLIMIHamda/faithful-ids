"""KB retrieval for VtE grounding (L3).

Retrieval *code* lives here (not in ``kb/``, which holds only the versioned
corpus). Given the top-k feature names, returns the feature-semantics snippets
that ground the drafted explanation.
"""

from __future__ import annotations

from typing import Mapping, Sequence

import yaml

from faithfulids.provenance import repo_root


class KBRetriever:
    def __init__(self, feature_semantics: Mapping[str, str]) -> None:
        self._map = dict(feature_semantics)

    def snippets(self, features: Sequence[str]) -> str:
        lines = []
        for f in features:
            desc = self._map.get(f)
            if desc:
                lines.append(f"- {f}: {desc}")
        return "\n".join(lines)


def load_feature_semantics(dataset_id: str) -> dict[str, str]:
    """Load ``kb/feature_semantics/<dataset>.yaml`` as {feature -> description}."""
    path = repo_root() / "kb" / "feature_semantics" / f"{dataset_id}.yaml"
    if not path.is_file():
        return {}
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    return {e["name"]: e["description"] for e in data.get("entries", [])}
