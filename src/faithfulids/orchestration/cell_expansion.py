"""Cell expansion (L5).

Turns a factorial experiment design into the concrete list of
generator–LLM cells the runner executes. The single most important arithmetic in
the artifact lives here: a generator's ``llm_dependent`` flag decides whether it
multiplies across the LLM axis, so the Tier A core factorial expands to exactly

    datasets × detectors × (n_llm_independent + n_llm_dependent × n_llms)
    = 2 × 2 × (2 + 3 × 3) = 44

matching the count claimed in the paper (blueprint §3.5). B0/B1 declare
``llm_dependent: false`` and contribute one cell each; B2/B3/B4 multiply by the
LLM axis.
"""

from __future__ import annotations

from dataclasses import dataclass

from faithfulids.orchestration.config_loader import ConfigError, load_config


@dataclass(frozen=True)
class Cell:
    """One executable cell of an experiment."""

    dataset: str
    detector: str
    generator: str
    llm: str | None  # None for LLM-independent generators (B0/B1)

    @property
    def cell_id(self) -> str:
        return f"{self.dataset}__{self.detector}__{self.generator}__{self.llm or 'noLLM'}"


def _generator_is_llm_dependent(generator_id: str) -> bool:
    cfg = load_config("generator", generator_id)
    return bool(cfg["llm_dependent"])


def expand_factorial(axes: dict[str, list[str]]) -> list[Cell]:
    """Expand a factorial design's axes into cells (generator-blind LLM handling)."""
    cells: list[Cell] = []
    for dataset in axes["datasets"]:
        for detector in axes["detectors"]:
            for generator in axes["generators"]:
                if _generator_is_llm_dependent(generator):
                    for llm in axes["llms"]:
                        cells.append(Cell(dataset, detector, generator, llm))
                else:
                    cells.append(Cell(dataset, detector, generator, None))
    return cells


def expand_cells(experiment: dict) -> list[Cell]:
    """Expand any experiment design into its cell list."""
    design = experiment["design"]
    mode = design["mode"]
    if mode == "factorial":
        return expand_factorial(design["axes"])
    if mode in ("single", "toy"):
        cell = design.get("cell", {})
        return [
            Cell(
                dataset=cell.get("dataset", ""),
                detector=cell.get("detector", ""),
                generator=cell.get("generator", ""),
                llm=cell.get("llm"),
            )
        ]
    if mode == "anchored":
        return _expand_anchored(experiment)
    raise ConfigError(f"unknown design mode: {mode!r}")


def _expand_anchored(experiment: dict) -> list[Cell]:
    """Anchored one-factor design: anchor cell with declared overrides.

    Resolves the anchor's cell, then applies ``one_factor_overrides``: any of
    ``dataset``/``detector`` replaced directly; ``generators``/``llms`` given as
    lists become the swept axis. LLM-independent generators drop the LLM axis.
    """
    from faithfulids.orchestration.registry import load_experiment

    anchor = load_experiment(experiment["design"]["anchor_ref"])
    base = anchor["design"]["cell"]
    ov = experiment["design"].get("one_factor_overrides", {})

    datasets = [ov["dataset"]] if "dataset" in ov else [base["dataset"]]
    detectors = [ov["detector"]] if "detector" in ov else [base["detector"]]
    generators = ov.get("generators", [base.get("generator")])
    llms = ov.get("llms", [base.get("llm")])

    cells: list[Cell] = []
    for dataset in datasets:
        for detector in detectors:
            for generator in generators:
                if generator and _generator_is_llm_dependent(generator):
                    for llm in llms:
                        cells.append(Cell(dataset, detector, generator, llm))
                else:
                    cells.append(Cell(dataset, detector, generator, None))
    return cells
