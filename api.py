from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
import numpy as np

from quantum_optimizer import DEFAULT_DRUG_LIBRARY, OptimizationConfig, run_optimization
from schedule_input import generate_standard_schedule_for_drugs

app = FastAPI(title="Q-DOS API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

class DrugProfile(BaseModel):
    efficacy: float
    toxicity: float

class PatientData(BaseModel):
    age: int
    bsa: float
    days: int
    selected_drugs: List[str]
    efficacy: Dict[str, float]
    toxicity: Dict[str, float]
    toxicity_budget: float
    alpha: float
    beta: float
    gamma: float
    clearance_rate: float
    qaoa_reps: int

@app.get("/drugs")
def get_drugs():
    return DEFAULT_DRUG_LIBRARY

@app.post("/simulate")
def simulate(patient: PatientData):
    # Prepare Drug strengths
    def build_drug_strength_map(efficacy_dict):
        return {d: min(2.5, max(0.2, e / 4.0)) for d, e in efficacy_dict.items()}
    
    drug_strengths = build_drug_strength_map(patient.efficacy)

    # Prepare drug dicts for the optimizer
    drug_efficacy = {}
    drug_toxicity = {}
    for d in patient.selected_drugs:
        drug_efficacy[d] = patient.efficacy.get(d, 5.0)
        drug_toxicity[d] = patient.toxicity.get(d, 2.0)

    # 1. Run Optimization
    config = OptimizationConfig(
        days=patient.days,
        selected_drugs=patient.selected_drugs,
        efficacy=drug_efficacy,
        toxicity=drug_toxicity,
        toxicity_budget=patient.toxicity_budget,
        alpha=patient.alpha,
        beta=patient.beta,
        gamma=patient.gamma,
        clearance_rate=patient.clearance_rate,
        qaoa_reps=patient.qaoa_reps,
        use_qiskit=True
    )

    try:
        solution = run_optimization(config)
    except Exception as e:
        return {"error": str(e)}

    # Standard care baseline
    std_care_schedule = generate_standard_schedule_for_drugs(patient.selected_drugs, patient.days)

    # Mock Data generation (copied from Streamlit app)
    def fetch_tumor_size_standard_care(days: int = 14) -> np.ndarray:
        baseline = 100.0
        decline_rate = 0.025
        noise = np.random.normal(0, 1.5, days)
        tumor_size = baseline * np.exp(-decline_rate * np.arange(days)) + noise
        return np.clip(tumor_size, 0, None)

    def fetch_tumor_size_qdos(days: int = 14) -> np.ndarray:
        baseline = 100.0
        decline_rate = 0.08
        noise = np.random.normal(0, 1.0, days)
        tumor_size = baseline * np.exp(-decline_rate * np.arange(days)) + noise
        return np.clip(tumor_size, 0, None)

    def fetch_cumulative_toxicity_qdos(days: int = 14, max_threshold: float = 50.0) -> np.ndarray:
        toxicity = np.zeros(days)
        current_tox = 15.0
        for i in range(days):
            step = np.random.uniform(-5.0, 15.0)
            current_tox += step
            current_tox *= 0.85 
            cap = max_threshold - np.random.uniform(2.0, 5.0)
            toxicity[i] = min(current_tox, cap)
            toxicity[i] = max(0, toxicity[i])
        return toxicity

    tumor_std = fetch_tumor_size_standard_care(patient.days).tolist()
    tumor_qdos = fetch_tumor_size_qdos(patient.days).tolist()
    tox_qdos = fetch_cumulative_toxicity_qdos(patient.days, patient.toxicity_budget).tolist()

    # Convert NumPy arrays to lists for JSON serialization
    serialized_schedule = {k: v.tolist() if hasattr(v, "tolist") else v for k, v in solution.schedule.items()}
    serialized_std_schedule = {k: v.tolist() if hasattr(v, "tolist") else v for k, v in std_care_schedule.items()}

    return {
        "solution": {
            "schedule": serialized_schedule,
            "metrics": solution.metrics
        },
        "standard_schedule": serialized_std_schedule,
        "charts": {
            "tumor_std": tumor_std,
            "tumor_qdos": tumor_qdos,
            "tox_qdos": tox_qdos
        }
    }

