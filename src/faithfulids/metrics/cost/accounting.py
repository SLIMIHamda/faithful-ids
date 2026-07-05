"""Cost accounting (L4).

Latency, tokens, $/explanation, and abstention/coverage accounting from the LLM
call records and the per-explanation abstention flags. Coverage–risk is a
mandatory output of every B4 cell (firewall rule 3).
"""

from __future__ import annotations

from typing import Any, Mapping, Sequence


def cost_accounting(
    call_records: Sequence[Mapping[str, Any]],
    abstentions: Sequence[bool],
    *,
    price_per_1k_tokens: float | None = None,
) -> dict[str, Any]:
    n = len(abstentions)
    total_tokens = sum(int(r.get("tokens") or 0) for r in call_records)
    latencies = [r["latency_ms"] for r in call_records if r.get("latency_ms") is not None]
    n_abstained = sum(1 for a in abstentions if a)
    coverage = 1.0 - (n_abstained / n) if n else 0.0
    dollars = (total_tokens / 1000.0 * price_per_1k_tokens) if price_per_1k_tokens is not None else None
    return {
        "n_explanations": n,
        "total_tokens": total_tokens,
        "mean_latency_ms": (sum(latencies) / len(latencies)) if latencies else None,
        "coverage": coverage,
        "abstention_rate": 1.0 - coverage,
        "dollars": dollars,
    }
