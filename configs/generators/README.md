# configs/generators/ - generator configs (the paper's axis)

One per generator B0-B4. `llm_dependent` flag drives cell expansion (B0/B1 are LLM-independent). B4 declares KB version, verifier model family, threshold ref, abstention policy. Prompts referenced by hash, never inlined.

> Contract source: `REPOSITORY_BLUEPRINT.md` section 2. Parameters live in `configs/`; this directory holds no scientific magic constants.
