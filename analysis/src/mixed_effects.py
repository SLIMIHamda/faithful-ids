"""Mixed-effects model (variance components as random effects).

Thin wrapper over statsmodels MixedLM for the pre-registered random-effects
specification (instance, generation, extraction). Consumer of run artifacts
only; no execution capability.
"""

from __future__ import annotations

from typing import Sequence


def fit_random_intercept(values: Sequence[float], groups: Sequence, exog=None) -> dict:
    """Fit a random-intercept model ``value ~ 1 + (1|group)`` and report the
    variance split between the group random effect and the residual."""
    import numpy as np
    import pandas as pd
    import statsmodels.formula.api as smf

    df = pd.DataFrame({"value": np.asarray(values, dtype=float), "group": list(groups)})
    model = smf.mixedlm("value ~ 1", df, groups=df["group"])
    result = model.fit(method="lbfgs", reml=True, disp=False)
    group_var = float(result.cov_re.iloc[0, 0])
    resid_var = float(result.scale)
    total = group_var + resid_var
    return {
        "group_variance": group_var,
        "residual_variance": resid_var,
        "icc": (group_var / total) if total > 0 else 0.0,
        "intercept": float(result.fe_params.iloc[0]),
    }
