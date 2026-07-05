# Experiment registry (append-only index)

Human-readable index of the append-only registry. One row per registered
experiment. A change to a *run* experiment is a NEW entry with a `supersedes:`
field — never an edit. The paper's appendix auto-generates this table from the
registry so nothing can be silently omitted (hostile-audit A7).

| ID | Tier | RQ / hypothesis | Gates | Exploratory | Status | Superseded by |
|---|---|---|---|---|---|---|
| ANCHOR | anchor | anchor cell (referenced, not run) | — | no | registered | — |
| EXP-G-001 | gate | H0 — extractor audit (F1 ≥ 0.95) | — | no | registered | — |
| EXP-G-002 | gate | H0 — RQ0 calibration (sens/spec ≥ 0.9) | — | no | registered | — |
| EXP-A-001 | tier_a | H1, H2 — core factorial (44 cells) | G-001, G-002 | no | registered | — |
| EXP-B-001 | tier_b | H-T — transfer to IDS2018 | G-001, G-002 | no | registered | — |
| EXP-B-002 | tier_b | H-T — 4-bit quantisation | G-001, G-002 | no | registered | — |
| EXP-B-003 | tier_b | H-T — RF detector continuity | G-001, G-002 | no | registered | — |
| EXP-B-004 | tier_b | H-T — sensitivity micro-sweeps | G-001, G-002 | no | registered | — |
| EXP-S-001 | stochasticity | generation variance (k=3) | G-001, G-002 | no | registered | — |
| EXP-H-001 | human_study | H4 — SOC triage study | — | no | registered | — |
| EXP-X-001 | exploratory | CTI-RAG at the anchor | G-001, G-002 | **yes** | registered | — |
| EXP-TOY-001 | toy | CI determinism fixture (NON-CITABLE) | — | no | registered | — |

See `docs/registering-experiments.md` for the propose → validate → register →
tag → run workflow.
