# Contributing

Contributions are welcome, but this is a **reproducibility artifact**: several
ordinary software conveniences are forbidden because they would compromise the
scientific record.

## What is FORBIDDEN

- **Editing anything under [`runs/`](../runs).** The ledger is write-once.
  "Cleanup", deletion, or manual file placement in a run directory is never
  acceptable. A failed run keeps `STATUS=FAILED` forever.
- **Running an unregistered experiment.** No registry entry → it does not exist.
  Do not add a CLI flag or environment variable to sneak parameters past the
  resolved-config snapshot.
- **Editing a run experiment entry.** Supersede with a new versioned entry.
- **Editing the pre-registered `configs/statistics/` tree after tag
  `prereg-v1`.** Use an append-only amendment.
- **Hand-editing generated assets** under `paper/**/generated/` or hand-drawing
  figures. Figures are produced by scripts from analysis outputs.
- **Importing from `notebooks/`** in any pipeline code, or letting a notebook
  write a run/analysis/paper artifact. Notebooks are quarantine.
- **Crossing the firewall** — no import bridge, shared prompt, or shared model
  family between `extraction/` and `generation/b4_vte/verifier/`.
- **Fabricating results** or placeholder metric values, downloading datasets, or
  calling an LLM as part of "just testing".
- **Adding an unpinned dependency**, or an optional-dependency `try/except
  ImportError` for a scientific component.

## The workflow

1. Open an issue describing the scientific responsibility of the change.
2. Branch; implement; keep the layers (`make import-contracts`).
3. `make lint typecheck test firewall validate-configs` all green.
4. For a new experiment, follow
   [`registering-experiments.md`](registering-experiments.md).
5. For a new metric, add its module, a formula version in `configs/metrics/`, a
   hand-computed fixture in `tests/metrics_fixtures/`, **and** an RQ0
   calibration entry — a metric is admissible only after passing the corruption
   battery (blueprint §7).
6. Open a PR; all CI gates must pass.

## Adding things without redesign (blueprint §7)

| Extension | Add | Edit |
|---|---|---|
| New dataset | dataset config + KB dictionary + split manifest | nothing |
| New detector | `detectors/<name>/` + config | nothing else |
| New attribution | subpackage + config (declare exact/approx) | nothing |
| New generator (B5) | subpackage + config + prompt tree | **zero** evaluation code |
| New metric | module + formula version + fixture + RQ0 entry | nothing |

## Code of conduct

Be rigorous and kind. Disagreements about method are resolved by making the
disagreement *checkable* — a CI gate, a fixture, a lineage query — not by
argument.
