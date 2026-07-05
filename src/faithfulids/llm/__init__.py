"""llm — L2, the provider-agnostic client.

Ledger-backed calls, pinned-snapshot enforcement, cache-only replay, and prompt
loading with hash verification. Concrete providers are imported lazily by the
caller; importing this package pulls in no model framework.
"""

from __future__ import annotations

from faithfulids.llm.client import (
    LLMClient,
    LLMProvider,
    LLMRequest,
    LLMResponse,
    ReplayMiss,
    UnpinnedModelError,
    pinned_snapshot,
)
from faithfulids.llm.ledger import CallLedger
from faithfulids.llm.prompts import PromptError, load_prompt, prompt_path

__all__ = [
    "LLMClient",
    "LLMProvider",
    "LLMRequest",
    "LLMResponse",
    "ReplayMiss",
    "UnpinnedModelError",
    "pinned_snapshot",
    "CallLedger",
    "load_prompt",
    "prompt_path",
    "PromptError",
]
