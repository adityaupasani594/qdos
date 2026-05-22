import numpy as np
from dataclasses import dataclass, field
from typing import Dict, List, Tuple
from qiskit_optimization import QuadraticProgram
from qiskit_algorithms.minimum_eigensolvers import QAOA
from qiskit_algorithms.optimizers import COBYLA
from qiskit_optimization.algorithms import MinimumEigenOptimizer


DEFAULT_DRUG_LIBRARY = {
    "Pembrolizumab": {"efficacy": 0.30, "toxicity": {"kidney": 0.2, "liver": 0.1, "marrow": 0.4, "immune": 0.1, "vascular": 0.2}},
    "Cisplatin": {"efficacy": 0.25, "toxicity": {"kidney": 0.1, "liver": 0.3, "marrow": 0.2, "immune": 0.3, "vascular": 0.1}},
    "Paclitaxel": {"efficacy": 0.35, "toxicity": {"kidney": 0.4, "liver": 0.2, "marrow": 0.1, "immune": 0.1, "vascular": 0.2}},
}

DEFAULT_SYNERGY = {
    ("Pembrolizumab", "Cisplatin"): {"base_synergy": 0.5, "optimal_delay": 0, "beta": 1.0, "pathway_weights": {"BRCA": 0.5, "PDL1": 0.1, "VEGF": 0.4}},
    ("Pembrolizumab", "Paclitaxel"): {"base_synergy": -0.2, "optimal_delay": 1, "beta": 0.5, "pathway_weights": {"BRCA": 0.2, "PDL1": 0.6, "VEGF": 0.2}},
}

@dataclass
class OptimizationConfig:
    days: int = 14
    selected_drugs: list = field(default_factory=list)
    patient_profile: dict = field(default_factory=dict)
    subtype_scores: dict = field(default_factory=dict)
    mutually_exclusive_pairs: list = field(default_factory=list)
    gap_constraints: dict = field(default_factory=dict)
    max_drugs_per_day: int = 2
    base_toxicity_budget: float = 10.0
    alpha: float = 1.0
    beta: float = 1.0
    gamma: float = 100.0
    lambda_daily: float = 50.0
    lambda_gap: float = 50.0

@dataclass
class OptimizationSolution:
    schedule: Dict[str, np.ndarray]
    per_day_drugs: Dict[int, List[str]]
    metrics: dict
    status: str

def get_effective_toxicity(drug, config):
    profile = config.patient_profile
    tox = DEFAULT_DRUG_LIBRARY.get(drug, {}).get("toxicity", {})
    if not tox: return 0.0
    eff_tox = 0.0
    for organ, val in tox.items():
        p_val = profile.get(organ, 1.0)
        if p_val > 0:
            eff_tox += val / p_val
    return eff_tox

def build_quadratic_program(config: OptimizationConfig):
    qp = QuadraticProgram()
    drugs = config.selected_drugs
    days = config.days

    budget = config.base_toxicity_budget - 0.5 * (config.patient_profile.get("age", 40) - 40)
    
    # Variables
    for d in drugs:
        for t in range(days):
            qp.binary_var(f"x_{d}_{t}")

    linear = {}
    quadratic = {}
    
    # 1. H_sym (efficacy and synergy)
    for d in drugs:
        eff = DEFAULT_DRUG_LIBRARY.get(d, {}).get("efficacy", 0.1)
        for t in range(days):
            var = f"x_{d}_{t}"
            linear[var] = linear.get(var, 0) - config.alpha * eff
    
    # Dynamic Synergy
    for (d1, d2), syn_data in DEFAULT_SYNERGY.items():
        if d1 in drugs and d2 in drugs:
            base = syn_data["base_synergy"]
            opt_delay = syn_data["optimal_delay"]
            beta = syn_data["beta"]
            p_weights = syn_data["pathway_weights"]
            
            subtype_f = sum(p_weights.get(pw, 0) * config.subtype_scores.get(pw, 0) for pw in p_weights)
            subtype_f = subtype_f if subtype_f > 0 else 1.0
            
            for t1 in range(days):
                for t2 in range(days):
                    timing_factor = np.exp(-beta * abs((t2 - t1) - opt_delay))
                    # assuming dose factor 4 * d1 * d2 = 4 (binary)
                    val = base * 4 * timing_factor * subtype_f
                    if val != 0:
                        v1, v2 = f"x_{d1}_{t1}", f"x_{d2}_{t2}"
                        if v1 != v2:
                            quadratic[(v1, v2)] = quadratic.get((v1, v2), 0) - config.alpha * val
                            
    # 2. H_tox (Toxicity Penalty)
    # \lambda_{tox} (C - B)^2
    # C = sum_{d,t} T^{eff}_d x_{d,t}
    # (C - B)^2 = C^2 - 2BC + B^2
    for d in drugs:
        t_eff = get_effective_toxicity(d, config)
        for t in range(days):
            var = f"x_{d}_{t}"
            linear[var] = linear.get(var, 0) - 2 * budget * t_eff * config.beta + (t_eff**2) * config.beta
            for d2 in drugs:
                t_eff2 = get_effective_toxicity(d2, config)
                for t2 in range(days):
                    var2 = f"x_{d2}_{t2}"
                    if var != var2:
                        quadratic[(var, var2)] = quadratic.get((var, var2), 0) + config.beta * t_eff * t_eff2

    # 3. H_daily (Max drugs per day)
    # \lambda_daily sum_t (\sum_d x_{d,t} - M)^2
    for t in range(days):
        M = config.max_drugs_per_day
        for d in drugs:
            v1 = f"x_{d}_{t}"
            linear[v1] = linear.get(v1, 0) + config.lambda_daily * (1 - 2*M)
            for d2 in drugs:
                if d != d2:
                    v2 = f"x_{d2}_{t}"
                    quadratic[(v1, v2)] = quadratic.get((v1, v2), 0) + config.lambda_daily

    # 4. H_mutual (Mutually exclusive)
    for (d1, d2) in config.mutually_exclusive_pairs:
        if d1 in drugs and d2 in drugs:
            for t in range(days):
                v1, v2 = f"x_{d1}_{t}", f"x_{d2}_{t}"
                quadratic[(v1, v2)] = quadratic.get((v1, v2), 0) + config.gamma

    # 5. H_gap (Inter-Dose gap)
    for d, min_gap in config.gap_constraints.items():
        if d in drugs:
            for t in range(days - 1):
                for gap_step in range(1, min_gap + 1):
                    if t + gap_step < days:
                        v1, v2 = f"x_{d}_{t}", f"x_{d}_{t + gap_step}"
                        quadratic[(v1, v2)] = quadratic.get((v1, v2), 0) + config.lambda_gap

    # Normalize coefficients to prevent explosion
    max_lin = max(abs(v) for v in linear.values()) if linear else 1.0
    max_quad = max(abs(v) for v in quadratic.values()) if quadratic else 1.0
    scale = max(max_lin, max_quad)
    if scale > 0:
        for k in linear: linear[k] /= scale
        for k in quadratic: quadratic[k] /= scale

    qp.minimize(linear=linear, quadratic=quadratic)
    return qp

def _solve_with_numpy(qp):
    from qiskit_optimization.algorithms import MinimumEigenOptimizer
    
    # Optional: Swap to QAOA for a true quantum approach to avoid exact diagonalization overhead on large N
    # from qiskit_algorithms.minimum_eigensolvers import QAOA
    # from qiskit_algorithms.optimizers import COBYLA
    # from qiskit.primitives import Sampler
    # mes = QAOA(sampler=Sampler(), optimizer=COBYLA(maxiter=30))
    
    from qiskit_algorithms import NumPyMinimumEigensolver
    
    # If number of variables is too large, exact eigensolver will freeze the server with OOM
    if qp.get_num_vars() > 14:
        raise ValueError(f"Too many variables ({qp.get_num_vars()}) for exact classical solver. Reduce days or selected drugs.")
        
    mes = NumPyMinimumEigensolver()
    optimizer = MinimumEigenOptimizer(mes)
    return qp, optimizer.solve(qp)

def run_optimization(config: OptimizationConfig):
    qp = build_quadratic_program(config)
    
    _, result = _solve_with_numpy(qp)
    
    schedule = {d: np.zeros(config.days) for d in config.selected_drugs}
    per_day_drugs = {t: [] for t in range(config.days)}
    
    if result and result.status.name == "SUCCESS":
        for i, val in enumerate(result.x):
            if val > 0.5:
                var_name = qp.variables[i].name
                _, d, t = var_name.split("_")
                t = int(t)
                schedule[d][t] = 1
                per_day_drugs[t].append(d)
                
    return OptimizationSolution(
        schedule=schedule,
        per_day_drugs=per_day_drugs,
        metrics={"score": result.fval if result else 0.0},
        status=result.status.name if result else "FAILED"
    )
