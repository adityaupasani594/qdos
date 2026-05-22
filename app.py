import streamlit as st
import numpy as np
import pandas as pd
import plotly.graph_objects as go
from quantum_optimizer import OptimizationConfig, run_optimization
from simulator import TumorSimulator

st.set_page_config(page_title="Q-DOS: Quantum Drug Optimization System", layout="wide")

st.title("?? Q-DOS: Quantum Drug Optimization System")
st.markdown("Optimize cancer drug schedules using dynamic synergy and organ-specific toxicity constraints via Quantum formulation.")

# Sidebar Settings
st.sidebar.header("Patient Profile")
age = st.sidebar.slider("Age", 18, 100, 40)
st.sidebar.subheader("Organ Function (0.0=Failure, 1.0=Normal)")
kidney = st.sidebar.slider("Kidney", 0.1, 1.0, 1.0)
liver = st.sidebar.slider("Liver", 0.1, 1.0, 1.0)
marrow = st.sidebar.slider("Bone Marrow", 0.1, 1.0, 1.0)
immune = st.sidebar.slider("Immune System", 0.1, 1.0, 1.0)
vascular = st.sidebar.slider("Vascular", 0.1, 1.0, 1.0)

st.sidebar.header("Tumor Subtype")
brca = st.sidebar.slider("BRCA Score", 0.0, 1.0, 0.5)
pdl1 = st.sidebar.slider("PD-L1 Score", 0.0, 1.0, 0.5)
vegf = st.sidebar.slider("VEGF Score", 0.0, 1.0, 0.5)

st.sidebar.header("Treatment Constraints")
max_drugs = st.sidebar.number_input("Max Drugs / Day", 1, 5, 2)
base_budget = st.sidebar.number_input("Base Toxicity Budget", 5.0, 50.0, 10.0)

if st.button("Run Quantum Optimization"):
    with st.spinner("Compiling QUBO & Solving..."):
        config = OptimizationConfig(
            days=14,
            selected_drugs=["Drug_A", "Drug_B", "Drug_C"],
            patient_profile={"age": age, "kidney": kidney, "liver": liver, "marrow": marrow, "immune": immune, "vascular": vascular},
            subtype_scores={"BRCA": brca, "PDL1": pdl1, "VEGF": vegf},
            mutually_exclusive_pairs=[("Drug_B", "Drug_C")],
            gap_constraints={"Drug_A": 1}, # Minimum 1 day gap
            max_drugs_per_day=max_drugs,
            base_toxicity_budget=base_budget
        )
        
        # 1. Run Optimization
        solution = run_optimization(config)
        st.success(f"Optimization Complete! Status: {solution.status}")
        
        # 2. Run Simulation
        simulator = TumorSimulator(
            days=14,
            patient_profile=config.patient_profile,
            subtype_scores=config.subtype_scores
        )
        
        t_notx, pop_notx = simulator.simulate_no_treatment()
        t_tx, pop_tx = simulator.simulate_treatment(solution.schedule)
        
        # 3. Plot Tumor Pop
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=t_notx, y=pop_notx, mode='lines', name='No Treatment'))
        fig.add_trace(go.Scatter(x=t_tx, y=pop_tx, mode='lines', name='Q-DOS Schedule'))
        fig.update_layout(title="Tumor Cell Population Over Time", xaxis_title="Days", yaxis_title="Number of Cells")
        st.plotly_chart(fig)
        
        # 4. Display Schedule Highlights
        st.subheader("Generated Schedule")
        st.json(solution.per_day_drugs)
