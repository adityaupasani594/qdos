"""
baselines.py — Baseline treatment schedule generators for Q-DOS comparison.

Provides:
  - Standard Care  (protocol-based fixed intervals)
  - Greedy         (max efficacy-per-toxicity each day)
  - Random         (budget-satisfying random selection)
"""

import numpy as np
from dataclasses import dataclass
from typing import Dict, List

from quantum_optimizer import DEFAULT_DRUG_LIBRARY, OptimizationConfig, get_effective_toxicity


@dataclass
class BaselineSolution:
    schedule: Dict[str, np.ndarray]
    per_day_drugs: Dict[int, List[str]]
    strategy: str
    total_toxicity: float
    total_efficacy: float


def _tox_and_eff(schedule, drugs, days, config):
    """Compute aggregate toxicity and efficacy for a schedule."""
    total_tox = 0.0
    total_eff = 0.0
    for d in drugs:
        t_eff = get_effective_toxicity(d, config)
        eff = DEFAULT_DRUG_LIBRARY.get(d, {}).get("efficacy", 0.0)
        for t in range(days):
            if schedule[d][t] == 1:
                total_tox += t_eff
                total_eff += eff
    return total_tox, total_eff


def generate_standard_care(config: OptimizationConfig) -> BaselineSolution:
    """
    Standard-of-care schedule: rank drugs by efficacy, administer on
    fixed clinical intervals (3 / 5 / 7 day cycles) without exceeding budget.
    """
    drugs = config.selected_drugs
    days  = config.days
    schedule = {d: np.zeros(days) for d in drugs}
    budget = config.base_toxicity_budget - 0.5 * (config.patient_profile.get("age", 40) - 40)
    budget = max(budget, 1.0)

    ranked = sorted(drugs,
                    key=lambda d: DEFAULT_DRUG_LIBRARY.get(d, {}).get("efficacy", 0),
                    reverse=True)
    intervals = [3, 5, 7, 10]
    cumulative_tox = 0.0

    for t in range(days):
        drugs_today = 0
        for i, drug in enumerate(ranked):
            if drugs_today >= config.max_drugs_per_day:
                break
            interval = intervals[min(i, len(intervals) - 1)]
            if t % interval == 0:
                t_eff = get_effective_toxicity(drug, config)
                if cumulative_tox + t_eff <= budget:
                    schedule[drug][t] = 1
                    cumulative_tox += t_eff
                    drugs_today += 1

    per_day = {t: [d for d in drugs if schedule[d][t] == 1] for t in range(days)}
    tox, eff = _tox_and_eff(schedule, drugs, days, config)
    return BaselineSolution(schedule=schedule, per_day_drugs=per_day,
                            strategy="Standard Care",
                            total_toxicity=tox, total_efficacy=eff)


def generate_greedy(config: OptimizationConfig) -> BaselineSolution:
    """
    Greedy schedule: each day select drugs ranked by efficacy/toxicity ratio
    until the daily or cumulative budget is exhausted.
    """
    drugs = config.selected_drugs
    days  = config.days
    schedule = {d: np.zeros(days) for d in drugs}
    budget = config.base_toxicity_budget - 0.5 * (config.patient_profile.get("age", 40) - 40)
    budget = max(budget, 1.0)

    ranked = sorted(drugs,
                    key=lambda d: DEFAULT_DRUG_LIBRARY.get(d, {}).get("efficacy", 0) /
                                  max(get_effective_toxicity(d, config), 1e-6),
                    reverse=True)
    cumulative_tox = 0.0

    for t in range(days):
        drugs_today = 0
        for drug in ranked:
            if drugs_today >= config.max_drugs_per_day:
                break
            t_eff = get_effective_toxicity(drug, config)
            if cumulative_tox + t_eff <= budget:
                schedule[drug][t] = 1
                cumulative_tox += t_eff
                drugs_today += 1

    per_day = {t: [d for d in drugs if schedule[d][t] == 1] for t in range(days)}
    tox, eff = _tox_and_eff(schedule, drugs, days, config)
    return BaselineSolution(schedule=schedule, per_day_drugs=per_day,
                            strategy="Greedy",
                            total_toxicity=tox, total_efficacy=eff)


def generate_random(config: OptimizationConfig, seed: int = 42) -> BaselineSolution:
    """
    Random schedule: randomly assign drugs each day while satisfying
    the toxicity budget and max-drugs-per-day constraint.
    """
    rng   = np.random.default_rng(seed)
    drugs = config.selected_drugs
    days  = config.days
    schedule = {d: np.zeros(days) for d in drugs}
    budget = config.base_toxicity_budget - 0.5 * (config.patient_profile.get("age", 40) - 40)
    budget = max(budget, 1.0)
    cumulative_tox = 0.0

    for t in range(days):
        shuffled = list(drugs)
        rng.shuffle(shuffled)
        drugs_today = 0
        for drug in shuffled:
            if drugs_today >= config.max_drugs_per_day:
                break
            t_eff = get_effective_toxicity(drug, config)
            if cumulative_tox + t_eff <= budget and rng.random() > 0.4:
                schedule[drug][t] = 1
                cumulative_tox += t_eff
                drugs_today += 1

    per_day = {t: [d for d in drugs if schedule[d][t] == 1] for t in range(days)}
    tox, eff = _tox_and_eff(schedule, drugs, days, config)
    return BaselineSolution(schedule=schedule, per_day_drugs=per_day,
                            strategy="Random",
                            total_toxicity=tox, total_efficacy=eff)
