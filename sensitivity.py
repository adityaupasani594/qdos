"""
sensitivity.py — One-at-a-time (OAT) sensitivity analysis for Q-DOS.

Varies each parameter across its valid range while keeping all others at
baseline. Computes a normalized sensitivity index:
    S_i = |Δf / f| / |Δp / p|
where f = objective score and p = parameter value.
"""

import numpy as np
from dataclasses import dataclass
from typing import List, Tuple
from copy import deepcopy

from quantum_optimizer import OptimizationConfig, run_optimization


@dataclass
class ParameterSensitivity:
    parameter: str
    values: List[float]
    objective_scores: List[float]
    sensitivity_index: float   # normalized |S_i|


@dataclass
class SensitivityReport:
    parameters: List[ParameterSensitivity]
    baseline_score: float


def _run(config: OptimizationConfig) -> float:
    """Run optimization and return objective score (minimized → negate for "higher=better")."""
    try:
        sol = run_optimization(config)
        return sol.metrics.get("score", 0.0)
    except Exception:
        return 0.0


def run_sensitivity_analysis(
    base_config: OptimizationConfig,
    n_points: int = 7,
) -> SensitivityReport:
    """
    OAT sensitivity over age, organ scores, and biomarker scores.
    Uses shortened horizon (≤5 days) so the NumPy solver stays fast.
    """
    # Shorten horizon for solver speed
    cfg = deepcopy(base_config)
    cfg.days = min(cfg.days, 5)

    baseline_score = _run(cfg)

    # (name, category, lo, hi, base_value)
    param_defs: List[Tuple[str, str, float, float, float]] = [
        ("age",     "profile",   20, 80,  cfg.patient_profile.get("age",     40)),
        ("kidney",  "profile",  0.2, 1.0, cfg.patient_profile.get("kidney",  1.0)),
        ("liver",   "profile",  0.2, 1.0, cfg.patient_profile.get("liver",   1.0)),
        ("marrow",  "profile",  0.2, 1.0, cfg.patient_profile.get("marrow",  1.0)),
        ("immune",  "profile",  0.2, 1.0, cfg.patient_profile.get("immune",  1.0)),
        ("vascular","profile",  0.2, 1.0, cfg.patient_profile.get("vascular",1.0)),
        ("PDL1",    "subtype",  0.0, 1.0, cfg.subtype_scores.get("PDL1",     0.5)),
        ("BRCA",    "subtype",  0.0, 1.0, cfg.subtype_scores.get("BRCA",     0.5)),
        ("VEGF",    "subtype",  0.0, 1.0, cfg.subtype_scores.get("VEGF",     0.5)),
    ]

    results: List[ParameterSensitivity] = []

    for name, category, lo, hi, base_val in param_defs:
        values = np.linspace(lo, hi, n_points).tolist()
        scores = []

        for v in values:
            c = deepcopy(cfg)
            if category == "profile":
                c.patient_profile[name] = v
            else:
                c.subtype_scores[name] = v
            scores.append(_run(c))

        # Normalized sensitivity index
        score_range = max(scores) - min(scores)
        val_range   = hi - lo
        base_f      = abs(baseline_score) if abs(baseline_score) > 1e-10 else 1e-6
        base_p      = abs(base_val)        if abs(base_val)       > 1e-10 else 1e-6

        s_i = (score_range / base_f) / (val_range / base_p) if val_range > 0 else 0.0

        results.append(ParameterSensitivity(
            parameter=name,
            values=values,
            objective_scores=scores,
            sensitivity_index=abs(s_i),
        ))

    return SensitivityReport(parameters=results, baseline_score=baseline_score)
