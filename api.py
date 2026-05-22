from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
import numpy as np

from quantum_optimizer import DEFAULT_DRUG_LIBRARY, OptimizationConfig, run_optimization
from simulator import TumorSimulator

app = FastAPI(title="Q-DOS API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

class PatientData(BaseModel):
    age: int = 40
    days: int = 14
    selected_drugs: List[str] = ["Pembrolizumab", "Cisplatin", "Paclitaxel"]
    patient_profile: Dict[str, float] = {"kidney": 1.0, "liver": 1.0, "marrow": 1.0, "immune": 1.0, "vascular": 1.0}
    subtype_scores: Dict[str, float] = {"BRCA": 0.5, "PDL1": 0.5, "VEGF": 0.5}
    mutually_exclusive_pairs: List[List[str]] = []
    gap_constraints: Dict[str, int] = {}
    max_drugs_per_day: int = 2
    base_toxicity_budget: float = 10.0

@app.get("/drugs")
def get_drugs():
    return DEFAULT_DRUG_LIBRARY

@app.post("/simulate")
def simulate(patient: PatientData):
    profile_with_age = {**patient.patient_profile, "age": patient.age}
    
    config = OptimizationConfig(
        days=patient.days,
        selected_drugs=patient.selected_drugs,
        patient_profile=profile_with_age,
        subtype_scores=patient.subtype_scores,
        mutually_exclusive_pairs=[tuple(p) for p in patient.mutually_exclusive_pairs],
        gap_constraints=patient.gap_constraints,
        max_drugs_per_day=patient.max_drugs_per_day,
        base_toxicity_budget=patient.base_toxicity_budget
    )

    try:
        solution = run_optimization(config)
    except Exception as e:
        return {"error": str(e)}

    simulator = TumorSimulator(
        days=patient.days,
        dt=1.0, # Run with 1.0 step for easier plotting on frontend to match "days"
        patient_profile=profile_with_age,
        subtype_scores=patient.subtype_scores
    )

    t_notx, pop_notx = simulator.simulate_no_treatment()
    t_tx, pop_tx = simulator.simulate_treatment(solution.schedule)

    # Calculate daily toxicity array
    from quantum_optimizer import get_effective_toxicity
    budget = patient.base_toxicity_budget - 0.5 * (patient.age - 40)
    tox_daily = np.zeros(patient.days)
    for d in patient.selected_drugs:
        t_eff = get_effective_toxicity(d, config)
        if d in solution.schedule:
            for t, val in enumerate(solution.schedule[d]):
                tox_daily[t] += val * t_eff
                
    tox_qdos = tox_daily.tolist()
    
    # We will send the cumulative or just daily? Let's just send daily tox_qdos as it mimics current.
    cum_tox = np.cumsum(tox_qdos).tolist() # the old plot was cumulative?
    # Actually the old frontend says "Cumulative Toxicity (Q-DOS)", so let's send cumulative.

    serialized_schedule = {k: v.tolist() if hasattr(v, "tolist") else v for k, v in solution.schedule.items()}

    return {
        "solution": {
            "schedule": serialized_schedule,
            "metrics": {
                "objective_score": solution.metrics.get("score", 0.0),
                "total_efficacy": 0.0, # We can omit or calculate
                "total_toxicity": sum(tox_qdos)
            }
        },
        "charts": {
            "tumor_std": pop_notx.tolist(),
            "tumor_qdos": pop_tx.tolist(),
            "tox_qdos": cum_tox,
            "t_days": t_notx.tolist(),
            "budget": budget
        }
    }
