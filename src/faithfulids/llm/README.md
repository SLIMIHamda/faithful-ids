# llm/ - L2, provider-agnostic client

Caching, retry, full call logging, pinned-snapshot enforcement, cache-only replay mode (no network). The append-only ledger is what makes L3 replay possible.

> Contract source: `REPOSITORY_BLUEPRINT.md` section 2. Parameters live in `configs/`; this directory holds no scientific magic constants.
