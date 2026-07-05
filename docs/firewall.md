# The circularity firewall

> The single most dangerous methodological attack on this paper is *"the
> Verify-then-Explain generator is graded by its own verifier."* A policy
> statement in a README does not survive hostile review; a package structure
> with CI-enforced contracts does.

The **VtE internal verifier** (`src/faithfulids/generation/b4_vte/verifier/`)
and the **evaluation claim extractor** (`src/faithfulids/extraction/`) are kept
apart by *structure*, not discipline:

- **different packages** (siblings in L3, mutually non-importing);
- **different prompt trees** (`prompts/generation/b4_vte/verifier/` vs
  `prompts/extraction/eval_extractor/`) with CI-checked hash disjointness;
- **different model families**, declared in schema-validated configs and checked
  for disjointness;
- **no shared modules**, verified by an import scan.

This gives the methods section a checkable sentence: *"enforced mechanically in
the released artifact (CI job `firewall-audit`)."*

## The four master-plan firewall rules → mechanism (blueprint §8-A4)

| Rule | Statement | Enforcing mechanism |
|---|---|---|
| 1 | H3 headline evidence uses only verifier-independent signals | analysis configs for H3 enumerate only verifier-independent metric columns; schema-checked |
| 2 | Distinct extractor / verifier implementations | this audit — import contracts + prompt-hash + model-family disjointness (`firewall-audit.yml`) |
| 3 | Abstention reported as coverage–risk | coverage–risk analysis is a mandatory output of every B4 cell |
| 4 | Verifier threshold tuned on held-out dev split only | verifier threshold appears only in dev-split-scoped configs; schema-checked |

## Mechanical enforcement

`tools/firewall_check.py` (CI job `firewall-audit.yml`) verifies:

1. **Prompt-hash disjointness** — the set of sha256 hashes under the verifier
   prompt tree and the extractor prompt tree do not intersect, and their
   normalized wording is disjoint (no copy with trivial edits).
2. **Model-family disjointness** — the `model_family` declared by the verifier
   config and by the extractor config differ, and neither equals any generator's
   family.
3. **No import bridge** — a static scan confirms no module under `extraction/`
   imports `generation.*` and no module under `generation/b4_vte/verifier/`
   imports `extraction.*` (belt-and-braces on top of the import-linter
   contracts in [`dependency-graph.md`](dependency-graph.md)).

## Why the verifier may implement checking logic but not import evaluation code

VtE's verifier legitimately performs its own internal checking — that is the
method. What it may **never** do is import the evaluation machinery (`metrics`,
`extraction`), which would let the generator "peek at how it will be scored"
(forbidden edges 2 and 3). The verifier's logic is self-contained.
