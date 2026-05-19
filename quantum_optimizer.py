from __future__ import annotations

from dataclasses import dataclass, field
from itertools import combinations
from typing import Any

import numpy as np

from qiskit_algorithms import NumPyMinimumEigensolver
from qiskit_optimization import QuadraticProgram
from qiskit_optimization.algorithms import MinimumEigenOptimizer
from qiskit_optimization.converters import QuadraticProgramToQubo


DEFAULT_DRUG_LIBRARY: dict[str, dict[str, float]] = {
    "Pembrolizumab": {"efficacy": 6.5, "toxicity": 1.8},
    "Cisplatin": {"efficacy": 7.5, "toxicity": 3.8},
    "Paclitaxel": {"efficacy": 6.8, "toxicity": 3.2},
    "Fluorouracil": {"efficacy": 5.6, "toxicity": 2.4},
    "Doxorubicin": {"efficacy": 8.0, "toxicity": 4.4},
    "Drug_A": {"efficacy": 5.0, "toxicity": 2.0},
    "Drug_B": {"efficacy": 4.4, "toxicity": 1.7},
    "Drug_C": {"efficacy": 6.0, "toxicity": 2.4},
}

DEFAULT_SYNERGY: dict[tuple[str, str], float] = {
    ("Cisplatin", "Paclitaxel"): 1.2,
    ("Pembrolizumab", "Paclitaxel"): 0.8,
    ("Drug_A", "Drug_B"): 0.5,
    ("Drug_B", "Drug_C"): 0.4,
}


@dataclass
class OptimizationConfig:
    days: int = 14
    selected_drugs: list[str] = field(default_factory=list)
    efficacy: dict[str, float] = field(default_factory=dict)
    toxicity: dict[str, float] = field(default_factory=dict)
    synergy: dict[tuple[str, str], float] = field(default_factory=dict)
    mutually_exclusive_pairs: list[tuple[str, str]] = field(default_factory=list)
    alpha: float = 1.0
    beta: float = 1.0
    gamma: float = 100.0
    clearance_rate: float = 0.3
    toxicity_budget: float = 50.0
    qaoa_reps: int = 1  # kept for API compatibility, unused with NumPy solver
    use_qiskit: bool = True
    max_global_qubits: int = 16
    qaoa_window_days: int = 7
    max_qaoa_drugs: int = 3


@dataclass
class OptimizationSolution:
    schedule: dict[str, np.ndarray]
    per_day_drugs: dict[int, list[str]]
    metrics: dict[str, float]
    status: str
    qp: QuadraticProgram | None = None
    qubo: QuadraticProgram | None = None
    raw_result: Any = None
    resolved_profiles: dict[str, dict[str, float]] = field(default_factory=dict)


def _normalize_pair(drug_a: str, drug_b: str) -> tuple[str, str]:
    return tuple(sorted((drug_a, drug_b)))


def _generic_profile(drug: str) -> dict[str, float]:
    seed = sum(ord(char) for char in drug)
    efficacy = 4.5 + (seed % 35) / 10.0
    toxicity = 1.5 + (seed % 25) / 10.0
    return {"efficacy": round(efficacy, 2), "toxicity": round(toxicity, 2)}


def _scale_constraint_value(value: float, scale: int = 1) -> int:
    return max(1, int(round(value * scale)))


def resolve_profiles(
    selected_drugs: list[str],
    efficacy: dict[str, float] | None = None,
    toxicity: dict[str, float] | None = None,
) -> dict[str, dict[str, float]]:
    resolved: dict[str, dict[str, float]] = {}

    for drug in selected_drugs:
        base = DEFAULT_DRUG_LIBRARY.get(drug, _generic_profile(drug))
        resolved[drug] = {
            "efficacy": float((efficacy or {}).get(drug, base["efficacy"])),
            "toxicity": float((toxicity or {}).get(drug, base["toxicity"])),
        }

    return resolved


def resolve_synergy(
    selected_drugs: list[str],
    synergy: dict[tuple[str, str], float] | None = None,
) -> dict[tuple[str, str], float]:
    resolved: dict[tuple[str, str], float] = {}
    source = synergy or {}

    for first, second in combinations(selected_drugs, 2):
        pair = _normalize_pair(first, second)
        if pair in source:
            resolved[pair] = float(source[pair])
        elif pair in DEFAULT_SYNERGY:
            resolved[pair] = float(DEFAULT_SYNERGY[pair])
        else:
            resolved[pair] = 0.0

    return resolved


def build_quadratic_program(
    config: OptimizationConfig,
    profiles: dict[str, dict[str, float]],
    synergy: dict[tuple[str, str], float],
) -> QuadraticProgram:
    if not config.selected_drugs:
        raise ValueError("At least one drug is required to build the Hamiltonian.")

    qp = QuadraticProgram()

    for drug_index, _drug in enumerate(config.selected_drugs):
        for day in range(config.days):
            qp.binary_var(name=f"x_{drug_index}_{day}")

    linear: dict[str, float] = {}
    quadratic: dict[tuple[str, str], float] = {}
    exclusive_pairs = {_normalize_pair(*pair) for pair in config.mutually_exclusive_pairs}

    for drug_index, drug in enumerate(config.selected_drugs):
        profile = profiles[drug]
        for day in range(config.days):
            variable = f"x_{drug_index}_{day}"
            toxicity_penalty = sum(
                np.exp(-config.clearance_rate * (future_day - day))
                for future_day in range(day, config.days)
            )
            linear[variable] = linear.get(variable, 0.0) - config.alpha * profile["efficacy"]
            linear[variable] += config.beta * profile["toxicity"] * toxicity_penalty

    for day in range(config.days):
        for first_index, first_drug in enumerate(config.selected_drugs):
            first_var = f"x_{first_index}_{day}"
            for second_index in range(first_index + 1, len(config.selected_drugs)):
                second_drug = config.selected_drugs[second_index]
                second_var = f"x_{second_index}_{day}"
                pair = _normalize_pair(first_drug, second_drug)
                synergy_bonus = synergy.get(pair, 0.0)
                if synergy_bonus:
                    quadratic[(first_var, second_var)] = quadratic.get((first_var, second_var), 0.0) - config.alpha * synergy_bonus
                if pair in exclusive_pairs:
                    quadratic[(first_var, second_var)] = quadratic.get((first_var, second_var), 0.0) + config.gamma

    qp.minimize(linear=linear, quadratic=quadratic)

    toxicity_constraint = {
        f"x_{drug_index}_{day}": _scale_constraint_value(profiles[drug]["toxicity"])
        for drug_index, drug in enumerate(config.selected_drugs)
        for day in range(config.days)
    }
    qp.linear_constraint(
        linear=toxicity_constraint,
        sense="<=",
        rhs=_scale_constraint_value(float(config.toxicity_budget)),
        name="toxicity_budget",
    )

    return qp


def _solve_with_numpy(qp: QuadraticProgram) -> tuple[QuadraticProgram, Any]:
    """Classical exact solver — drop-in placeholder for Fujitsu annealer."""
    converter = QuadraticProgramToQubo()
    qubo = converter.convert(qp)
    solver = NumPyMinimumEigensolver()
    optimizer = MinimumEigenOptimizer(solver)
    result = optimizer.solve(qubo)
    return qubo, result


def _solve_with_qulacs(qp: QuadraticProgram) -> tuple[QuadraticProgram, Any]:
    """Quantum solver using qulacs and mpiqulacs."""
    converter = QuadraticProgramToQubo()
    qubo = converter.convert(qp)
    
    op, offset = qubo.to_ising()
    n_qubits = op.num_qubits
    
    from mpiqulacs import Observable
    observable = Observable(n_qubits)
    
    for pauli, coeff in zip(op.paulis, op.coeffs):
        pauli_str = str(pauli)
        term = []
        for i, p in enumerate(reversed(pauli_str)):
            if p != 'I':
                term.append(f"{p} {i}")
        observable.add_operator(coeff.real, " ".join(term) if term else "")

    from qulacs import QuantumCircuit, QuantumState
    from scipy.optimize import minimize
    
    depth = 2

    def cost_function(params):
        state = QuantumState(n_qubits)
        state.set_zero_state()
        circuit = QuantumCircuit(n_qubits)
        idx = 0
        for _ in range(depth):
            for i in range(n_qubits):
                circuit.add_RY_gate(i, params[idx])
                idx += 1
            for i in range(n_qubits - 1):
                circuit.add_CZ_gate(i, i + 1)
        circuit.update_quantum_state(state)
        return observable.get_expectation_value(state)

    initial_params = np.random.rand(n_qubits * depth) * 2 * np.pi
    result = minimize(cost_function, initial_params, method="COBYLA")
    
    class DummyResult:
        def __init__(self, x, fval):
            self.x = x
            self.fval = fval
            from qiskit_optimization.problems.quadratic_program import QuadraticProgram
            self.variables_dict = {f"y_{i}": round(x[i]) if i < len(x) else 0.0 for i in range(n_qubits)} 
            
    return qubo, DummyResult(result.x, result.fun)

def _solve_windowed(
    config: OptimizationConfig,
    profiles: dict[str, dict[str, float]],
    synergy: dict[tuple[str, str], float],
) -> dict[str, np.ndarray]:
    schedule = {
        drug: np.zeros(config.days, dtype=int)
        for drug in config.selected_drugs
    }
    toxicity_state = 0.0
    exclusive_pairs = {_normalize_pair(*pair) for pair in config.mutually_exclusive_pairs}

    ranked_drugs = sorted(
        config.selected_drugs,
        key=lambda drug: profiles[drug]["efficacy"] / max(profiles[drug]["toxicity"], 0.1),
        reverse=True,
    )
    active_drugs = ranked_drugs[: max(1, int(config.max_qaoa_drugs))]

    window_days = max(1, int(config.qaoa_window_days))
    for window_start in range(0, config.days, window_days):
        toxicity_state *= float(np.exp(-config.clearance_rate))
        max_daily_toxicity = max(0.0, float(config.toxicity_budget) - toxicity_state)
        if max_daily_toxicity <= 0:
            break

        block_length = min(window_days, config.days - window_start)

        day_qp = QuadraticProgram()
        day_vars = []
        for drug_index, _drug in enumerate(active_drugs):
            var_name = f"y_{drug_index}"
            day_qp.binary_var(var_name)
            day_vars.append(var_name)

        linear: dict[str, float] = {}
        quadratic: dict[tuple[str, str], float] = {}

        for drug_index, drug in enumerate(active_drugs):
            var_name = day_vars[drug_index]
            profile = profiles[drug]
            linear[var_name] = -config.alpha * profile["efficacy"] + config.beta * profile["toxicity"]

        for first_index, first_drug in enumerate(active_drugs):
            for second_index in range(first_index + 1, len(active_drugs)):
                second_drug = active_drugs[second_index]
                pair = _normalize_pair(first_drug, second_drug)
                pair_vars = (day_vars[first_index], day_vars[second_index])

                pair_synergy = synergy.get(pair, 0.0)
                if pair_synergy:
                    quadratic[pair_vars] = quadratic.get(pair_vars, 0.0) - config.alpha * pair_synergy

                if pair in exclusive_pairs:
                    quadratic[pair_vars] = quadratic.get(pair_vars, 0.0) + config.gamma

        day_qp.minimize(linear=linear, quadratic=quadratic)
        day_constraint = {
            day_vars[drug_index]: _scale_constraint_value(profiles[drug]["toxicity"])
            for drug_index, drug in enumerate(active_drugs)
        }
        day_qp.linear_constraint(
            linear=day_constraint,
            sense="<=",
            rhs=_scale_constraint_value(max_daily_toxicity),
            name=f"window_budget_{window_start}",
        )

        _qubo, day_result = _solve_with_qulacs(day_qp)

        selected_drugs_window = []
        selected_daily_toxicity = 0.0
        for variable_name, variable_value in day_result.variables_dict.items():
            if variable_value < 0.5 or not variable_name.startswith("y_"):
                continue

            parts = variable_name.split("_")
            if len(parts) < 2:
                continue
            drug_index = int(parts[1])
            drug = active_drugs[drug_index]
            selected_drugs_window.append(drug)
            selected_daily_toxicity += profiles[drug]["toxicity"]

        for offset in range(block_length):
            day = window_start + offset
            toxicity_state *= float(np.exp(-config.clearance_rate))

            if offset % 2 == 1:
                continue

            if toxicity_state + selected_daily_toxicity > float(config.toxicity_budget):
                continue

            for drug in selected_drugs_window:
                schedule[drug][day] = 1

            toxicity_state += selected_daily_toxicity

    return schedule


def _build_schedule_from_variables(
    variables: dict[str, float],
    selected_drugs: list[str],
    days: int,
) -> dict[str, np.ndarray]:
    schedule = {
        drug: np.zeros(days, dtype=int)
        for drug in selected_drugs
    }

    for variable, value in variables.items():
        if value < 0.5 or not variable.startswith("x_"):
            continue

        _, drug_index_text, day_text = variable.split("_")
        drug_index = int(drug_index_text)
        day = int(day_text)
        if 0 <= drug_index < len(selected_drugs) and 0 <= day < days:
            schedule[selected_drugs[drug_index]][day] = 1

    return schedule


def _build_per_day_drugs(schedule: dict[str, np.ndarray]) -> dict[int, list[str]]:
    days = len(next(iter(schedule.values()))) if schedule else 0
    per_day: dict[int, list[str]] = {day: [] for day in range(days)}

    for drug, values in schedule.items():
        for day, value in enumerate(values):
            if int(value) == 1:
                per_day[day].append(drug)

    return per_day


def _fallback_schedule(
    config: OptimizationConfig,
    profiles: dict[str, dict[str, float]],
    synergy: dict[tuple[str, str], float],
) -> dict[str, np.ndarray]:
    schedule = {
        drug: np.zeros(config.days, dtype=int)
        for drug in config.selected_drugs
    }
    budget_remaining = float(config.toxicity_budget)
    exclusive_pairs = {_normalize_pair(*pair) for pair in config.mutually_exclusive_pairs}

    for day in range(config.days):
        best_subset: list[str] = []
        best_score = 0.0

        for subset_mask in range(1, 1 << len(config.selected_drugs)):
            subset = [
                config.selected_drugs[index]
                for index in range(len(config.selected_drugs))
                if subset_mask & (1 << index)
            ]

            if any(_normalize_pair(first, second) in exclusive_pairs for first, second in combinations(subset, 2)):
                continue

            subset_toxicity = sum(profiles[drug]["toxicity"] for drug in subset)
            if subset_toxicity > budget_remaining:
                continue

            subset_efficacy = sum(profiles[drug]["efficacy"] for drug in subset)
            subset_synergy = sum(
                synergy.get(_normalize_pair(first, second), 0.0)
                for first, second in combinations(subset, 2)
            )
            score = config.alpha * subset_efficacy + config.alpha * subset_synergy - config.beta * subset_toxicity

            if score > best_score:
                best_score = score
                best_subset = subset

        for drug in best_subset:
            schedule[drug][day] = 1
            budget_remaining -= profiles[drug]["toxicity"]

    return schedule


def calculate_metrics(
    schedule: dict[str, np.ndarray],
    profiles: dict[str, dict[str, float]],
    synergy: dict[tuple[str, str], float],
    alpha: float,
    beta: float,
) -> dict[str, float]:
    total_efficacy = 0.0
    total_toxicity = 0.0
    total_synergy = 0.0

    days = len(next(iter(schedule.values()))) if schedule else 0
    for day in range(days):
        active_drugs = [drug for drug, values in schedule.items() if int(values[day]) == 1]
        total_efficacy += sum(profiles[drug]["efficacy"] for drug in active_drugs)
        total_toxicity += sum(profiles[drug]["toxicity"] for drug in active_drugs)
        total_synergy += sum(
            synergy.get(_normalize_pair(first, second), 0.0)
            for first, second in combinations(active_drugs, 2)
        )

    objective_score = alpha * (total_efficacy + total_synergy) - beta * total_toxicity
    total_doses = float(sum(float(values.sum()) for values in schedule.values()))

    return {
        "total_efficacy": float(total_efficacy),
        "total_toxicity": float(total_toxicity),
        "total_synergy": float(total_synergy),
        "objective_score": float(objective_score),
        "total_doses": total_doses,
    }


def run_optimization(config: OptimizationConfig) -> OptimizationSolution:
    selected_drugs = list(config.selected_drugs)
    profiles = resolve_profiles(selected_drugs, config.efficacy, config.toxicity)
    synergy = resolve_synergy(selected_drugs, config.synergy)

    qp = build_quadratic_program(config, profiles, synergy)

    try:
        if config.use_qiskit:
            num_variables = len(selected_drugs) * config.days
            if num_variables <= config.max_global_qubits:
                qubo, raw_result = _solve_with_qulacs(qp)
                schedule = _build_schedule_from_variables(raw_result.variables_dict, selected_drugs, config.days)
                status = "qulacs-global"
            else:
                qubo = None
                raw_result = None
                schedule = _solve_windowed(config, profiles, synergy)
                status = "numpy-windowed"
        else:
            qubo = None
            raw_result = None
            schedule = _fallback_schedule(config, profiles, synergy)
            status = "deterministic"
    except Exception as exc:
        qubo = None
        raw_result = exc
        schedule = _fallback_schedule(config, profiles, synergy)
        status = f"fallback: {exc}"

    per_day_drugs = _build_per_day_drugs(schedule)
    metrics = calculate_metrics(schedule, profiles, synergy, config.alpha, config.beta)

    return OptimizationSolution(
        schedule=schedule,
        per_day_drugs=per_day_drugs,
        metrics=metrics,
        status=str(status),
        qp=qp,
        qubo=qubo,
        raw_result=raw_result,
        resolved_profiles=profiles,
    )