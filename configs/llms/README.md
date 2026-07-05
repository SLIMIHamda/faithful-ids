# configs/llms/ - LLM identity configs

Per-LLM: weights hash / API snapshot ID, revision, quantisation. `frontier_api` declares provider, pinned snapshot ID, and replay-cache policy. The `model_family` field is firewall-load-bearing.

> Contract source: `REPOSITORY_BLUEPRINT.md` section 2. Parameters live in `configs/`; this directory holds no scientific magic constants.
