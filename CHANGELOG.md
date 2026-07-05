# Changelog

Versioned artifact history. `v1.0` = submission, `v1.1` = camera-ready, etc.
Metric *formula versions* and superseding registry entries are recorded here so
that a corrected metric or a re-run experiment leaves a public trail rather than
silently replacing history (see hostile-audit remediation A12 in
`docs/architecture.md`).

The format follows [Keep a Changelog](https://keepachangelog.com/) and the
project adheres to [Semantic Versioning](https://semver.org/) for the artifact.

## [Unreleased]

### Infrastructure (no scientific results produced)

This artifact is being built phase by phase per `IMPLEMENTATION_PROMPT.md`.
No experiment has been run, no dataset downloaded, no LLM called.

- **Phase 0** — Repository skeleton and governance: full directory tree with
  per-directory contracts, packaging (`pyproject.toml`), `Makefile` entry
  points, container definitions, CI workflow set, import-linter layered
  contracts + the seven named forbidden edges, licenses, citation metadata.

<!--
Template for future entries:

## [1.0.0] - YYYY-MM-DD  (submission)
### Added
### Changed
### Metric formula versions
### Superseding registry entries
-->
