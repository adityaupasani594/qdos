"""
statistics_engine.py — Monte Carlo statistical evaluation for Q-DOS.

Runs N simulations with ±10% Gaussian-perturbed patient parameters.
Returns mean tumor reduction %, toxicity, and 95% confidence intervals
for Q-DOS, Standard Care, Greedy, and Random schedules.
"""

import numpy as np
from scipy import stats as scipy_stats
from dataclasses import dataclass, field
from typing import Dict, List
from copy import deepcopy

from quantum_optimizer import OptimizationConfig, run_optimization, get_effective_toxicity
from simulator import TumorSimulator
from baselines import generate_standard_care, generate_greedy, generate_random


@dataclass
class ScheduleStats:
    strategy: str
    mean_tumor_reduction: float
    std_tumor_reduction: float
    ci_low: float
    ci_high: float
    mean_toxicity: float
    std_toxicity: float
    tox_ci_low: float
    tox_ci_high: float
    n_simulations: int


@dataclass
class StatisticsReport:
    schedules: List[ScheduleStats] = field(default_factory=list)
    n_simulations: int = 0
    confidence_level: float = 0.95


def _perturb(config: OptimizationConfig, rng: np.random.Generator, std: float = 0.10) -> OptimizationConfig:
    """Return a copy of config with patient parameters perturbed by Gaussian noise."""
    c = deepcopy(config)
    for organ in ["kidney", "liver", "marrow", "immune", "vascular"]:
        v = c.patient_profile.get(organ, 1.0)
        c.patient_profile[organ] = float(np.clip(v + rng.normal(0, std * v), 0.1, 1.0))
    for marker in ["BRCA", "PDL1", "VEGF"]:
        v = c.subtype_scores.get(marker, 0.5)
        c.subtype_scores[marker] = float(np.clip(v + rng.normal(0, std * max(v, 0.1)), 0.0, 1.0))
    return c


def _measure(schedule: Dict, config: OptimizationConfig):
    """Run tumor ODE simulation; return (tumor_reduction_pct, total_toxicity)."""
    sim = TumorSimulator(
        days=config.days,
        patient_profile=config.patient_profile,
        subtype_scores=config.subtype_scores,
    )
    _, pop_notx = sim.simulate_no_treatment()
    _, pop_tx   = sim.simulate_treatment(schedule)

    final_notx = pop_notx[-1]
    final_tx   = pop_tx[-1]
    reduction  = (final_notx - final_tx) / max(final_notx, 1e-6) * 100.0

    total_tox = 0.0
    for d, arr in schedule.items():
        t_eff = get_effective_toxicity(d, config)
        total_tox += float(np.sum(arr)) * t_eff

    return reduction, total_tox


def run_monte_carlo(
    config: OptimizationConfig,
    n: int = 30,
    seed: int = 0,
    confidence: float = 0.95,
) -> StatisticsReport:
    """
    Monte Carlo evaluation of Q-DOS vs baselines.
    Each iteration perturbs patient params by ±10% Gaussian noise.
    Q-DOS is limited to days ≤ 5 (NumPy solver); baselines run full horizon.
    """
    rng = np.random.default_rng(seed)

    buckets: Dict[str, Dict[str, List[float]]] = {
        name: {"reduction": [], "toxicity": []}
        for name in ["Q-DOS", "Standard Care", "Greedy", "Random"]
    }

    # Use short horizon for quantum solver to stay within variable limit
    qdos_days = min(config.days, 5)

    for i in range(n):
        pc = _perturb(config, rng)

        # --- Q-DOS (short horizon) ---
        qdos_config = deepcopy(pc)
        qdos_config.days = qdos_days
        try:
            sol = run_optimization(qdos_config)
            red, tox = _measure(sol.schedule, qdos_config)
        except Exception:
            red, tox = 0.0, 0.0
        buckets["Q-DOS"]["reduction"].append(red)
        buckets["Q-DOS"]["toxicity"].append(tox)

        # --- Baselines (full horizon) ---
        for strategy, fn in [("Standard Care", generate_standard_care),
                              ("Greedy",         generate_greedy)]:
            b = fn(pc)
            r, t = _measure(b.schedule, pc)
            buckets[strategy]["reduction"].append(r)
            buckets[strategy]["toxicity"].append(t)

        rb = generate_random(pc, seed=i)
        r, t = _measure(rb.schedule, pc)
        buckets["Random"]["reduction"].append(r)
        buckets["Random"]["toxicity"].append(t)

    alpha = 1.0 - confidence
    stats_list: List[ScheduleStats] = []

    for strategy, data in buckets.items():
        red = np.array(data["reduction"])
        tox = np.array(data["toxicity"])
        n_eff = len(red)
        t_crit = scipy_stats.t.ppf(1 - alpha / 2, df=max(n_eff - 1, 1))

        red_mean = float(np.mean(red))
        red_std  = float(np.std(red, ddof=1))
        red_sem  = red_std / np.sqrt(n_eff)

        tox_mean = float(np.mean(tox))
        tox_std  = float(np.std(tox, ddof=1))
        tox_sem  = tox_std / np.sqrt(n_eff)

        stats_list.append(ScheduleStats(
            strategy=strategy,
            mean_tumor_reduction=red_mean,
            std_tumor_reduction=red_std,
            ci_low=red_mean - t_crit * red_sem,
            ci_high=red_mean + t_crit * red_sem,
            mean_toxicity=tox_mean,
            std_toxicity=tox_std,
            tox_ci_low=tox_mean  - t_crit * tox_sem,
            tox_ci_high=tox_mean + t_crit * tox_sem,
            n_simulations=n_eff,
        ))

    return StatisticsReport(schedules=stats_list, n_simulations=n, confidence_level=confidence)
