import sys
sys.path.insert(0, '.')
from quantum_optimizer import (
    build_quadratic_program, OptimizationConfig,
    get_effective_toxicity, _biomarker_efficacy_boost, DEFAULT_DRUG_LIBRARY
)
import numpy as np

config = OptimizationConfig(
    days=5,
    selected_drugs=['Pembrolizumab', 'Cisplatin', 'Paclitaxel'],
    patient_profile={'kidney':1.0,'liver':1.0,'marrow':1.0,'immune':1.0,'vascular':1.0,'age':40},
    subtype_scores={'BRCA':0.5,'PDL1':0.5,'VEGF':0.5},
    max_drugs_per_day=2,
    base_toxicity_budget=10.0,
    nonlinear_tox=True
)

# Print effective toxicities and efficacies
print("=== Drug properties ===")
for d in config.selected_drugs:
    t_eff = get_effective_toxicity(d, config)
    boost = _biomarker_efficacy_boost(d, config)
    base_eff = DEFAULT_DRUG_LIBRARY[d]['efficacy']
    print(f"{d}: t_eff={t_eff:.4f}, base_eff={base_eff:.4f}, boost={boost:.4f}, boosted_eff={base_eff*boost:.4f}")

qp = build_quadratic_program(config)
print(f"\nNum vars: {qp.get_num_vars()}")

# Check linear coefficients
lin_dict = qp.objective.linear.to_dict(use_name=True)
print("\n=== Linear coefficients (normalized, first day) ===")
for var in ['x_Pembrolizumab_0', 'x_Cisplatin_0', 'x_Paclitaxel_0']:
    v = lin_dict.get(var, 'NOT FOUND')
    print(f"  {var}: {v}")

# Compute QUBO matrix
from qiskit_optimization.converters import QuadraticProgramToQubo
qubo_converter = QuadraticProgramToQubo()
qubo = qubo_converter.convert(qp)
qubo_lin = qubo.objective.linear.to_array()
qubo_matrix = qubo.objective.quadratic.to_array()

n = qp.get_num_vars()
x_zero = np.zeros(n)

# Test: apply Pembrolizumab on day 0
x_pemb = np.zeros(n)
x_pemb[0] = 1.0
val_zero = float(qubo_lin @ x_zero + 0.5 * x_zero @ qubo_matrix @ x_zero)
val_pemb = float(qubo_lin @ x_pemb + 0.5 * x_pemb @ qubo_matrix @ x_pemb)
print(f"\nObjective (no drugs): {val_zero:.6f}")
print(f"Objective (Pemb day0): {val_pemb:.6f}")
print(f"Diff: {val_pemb - val_zero:.6f}  (negative = better to give drug)")

# Brute force: what's the minimum for just day 0 drugs?
print("\n=== Evaluating all 8 combinations for day 0 ===")
# vars: x_Pembro_0, x_Cisplatin_0, x_Paclitaxel_0 -> indices 0, 5, 10
for pemb in [0,1]:
    for cis in [0,1]:
        for pac in [0,1]:
            x = np.zeros(n)
            x[0] = pemb   # Pembrolizumab_0
            x[5] = cis    # Cisplatin_0
            x[10] = pac   # Paclitaxel_0
            val = float(qubo_lin @ x + 0.5 * x @ qubo_matrix @ x)
            combo = f"Pemb={pemb} Cis={cis} Pac={pac}"
            print(f"  {combo}: {val:.6f}")
