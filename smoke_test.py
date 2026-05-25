from quantum_optimizer import OptimizationConfig, run_optimization
from simulator import TumorSimulator
from baselines import generate_standard_care, generate_greedy, generate_random
from sensitivity import run_sensitivity_analysis

cfg = OptimizationConfig(
    days=5,
    selected_drugs=["Pembrolizumab","Cisplatin","Paclitaxel"],
    patient_profile={"kidney":0.7,"liver":1.0,"marrow":0.9,"immune":1.0,"vascular":1.0,"age":55},
    subtype_scores={"PDL1":0.9,"BRCA":0.3,"VEGF":0.5},
    max_drugs_per_day=2,
    base_toxicity_budget=12.0,
)

sol = run_optimization(cfg)
print("Status:", sol.status)
print("Per-day:", sol.per_day_drugs)
print("Constraint violated:", sol.metrics.get("constraint_violated"))
print()

print("== Explanations ==")
for e in sol.explanations:
    if e["drugs"]:
        day = e["day"]
        drugs = e["drugs"]
        print(f"Day {day}: {drugs}")
        for r in e["rationale"]:
            print("  -", r)

print()
std  = generate_standard_care(cfg)
grdy = generate_greedy(cfg)
rnd  = generate_random(cfg)
print(f"Std tox:{std.total_toxicity:.2f}  Greedy tox:{grdy.total_toxicity:.2f}  Rand tox:{rnd.total_toxicity:.2f}")

sens = run_sensitivity_analysis(cfg, n_points=4)
top3 = sorted(sens.parameters, key=lambda p: p.sensitivity_index, reverse=True)[:3]
print()
print("Top-3 sensitive params:")
for p in top3:
    print(f"  {p.parameter}: S_i={p.sensitivity_index:.4f}")

print()
print("SMOKE TEST PASSED")
