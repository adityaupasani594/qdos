import streamlit as st
import numpy as np
import pandas as pd
import plotly.graph_objects as go
from quantum_optimizer import DEFAULT_DRUG_LIBRARY, OptimizationConfig, run_optimization
from schedule_input import generate_standard_schedule_for_drugs
from simulator import TumorSimulator

# -----------------------------------------------------------------------------
# MOCK DATA GENERATION (API Integration Points)
# -----------------------------------------------------------------------------
# In a production environment, these functions should be replaced by real REST API
# calls to the backend Quantum Solver.
# e.g., requests.post("https://api.qdos.com/v1/simulate", json=patient_data)

def fetch_tumor_size_standard_care(days: int = 14) -> np.ndarray:
    """Mock API call: Returns an array representing tumor size under standard care."""
    # Starts at 100%, slowly decreases to ~70% over 14 days with some noise
    baseline = 100.0
    decline_rate = 0.025
    noise = np.random.normal(0, 1.5, days)
    tumor_size = baseline * np.exp(-decline_rate * np.arange(days)) + noise
    return np.clip(tumor_size, 0, None)

def fetch_tumor_size_qdos(days: int = 14) -> np.ndarray:
    """Mock API call: Returns an array representing tumor size under Q-DOS optimizing."""
    # Starts at 100%, steeply decreases to ~30% over 14 days
    baseline = 100.0
    decline_rate = 0.08
    noise = np.random.normal(0, 1.0, days)
    tumor_size = baseline * np.exp(-decline_rate * np.arange(days)) + noise
    return np.clip(tumor_size, 0, None)

def fetch_cumulative_toxicity_qdos(days: int = 14, max_threshold: float = 50.0) -> np.ndarray:
    """Mock API call: Returns an array representing cumulative toxicity under Q-DOS."""
    # Fluctuates but generally stays below the max_threshold
    # Simulates toxicity accumulated from treatments and eliminated on rest days
    toxicity = np.zeros(days)
    current_tox = 15.0
    for i in range(days):
        # Add random treatment spike or elimination drop
        step = np.random.uniform(-5.0, 15.0)
        current_tox += step
        
        # Natural clearance rate (body recovery)
        current_tox *= 0.85 
        
        # Keep the visualization realistically below the user's max threshold, 
        # allowing for some peaks.
        cap = max_threshold - np.random.uniform(2.0, 5.0)
        toxicity[i] = min(current_tox, cap)
        toxicity[i] = max(0, toxicity[i]) # Toxicity can't be negative
    return toxicity

def fetch_treatment_schedule(days: int = 14, available_drugs: list = None) -> dict:
    """Mock API call: Returns a dict mapping days 0-13 to drug administrations."""
    if not available_drugs:
        available_drugs = ["Drug A", "Drug B"]
        
    schedule = {}
    for day in range(days):
        # Administer drug roughly every 3 days
        if day % 3 == 0:
            schedule[day] = [np.random.choice(available_drugs)]
        # Combination therapy roughly every 5 days
        elif day % 5 == 0 and len(available_drugs) > 1:
            schedule[day] = np.random.choice(available_drugs, 2, replace=False).tolist()
        else:
            schedule[day] = ["Rest"]
    return schedule

# -----------------------------------------------------------------------------
# UI COMPONENTS AND RENDERING
# -----------------------------------------------------------------------------

def render_sidebar():
    """Renders the settings and patient input sidebar."""
    st.sidebar.title("🧬 Q-DOS Configuration")
    st.sidebar.markdown("Configure patient parameters, drug profiles, and Hamiltonian weights.")
    
    st.sidebar.header("Patient Data")
    age = st.sidebar.number_input("Age (Years)", min_value=18, max_value=100, value=55)
    bsa = st.sidebar.number_input("Body Surface Area (m²)", min_value=1.0, max_value=3.0, value=1.8, step=0.1)
    days = st.sidebar.number_input("Planning Horizon (Days)", min_value=7, max_value=30, value=14, step=1)
    
    st.sidebar.header("Drug Library")
    drug_options = ["Pembrolizumab", "Cisplatin", "Paclitaxel", "Fluorouracil", "Doxorubicin"]
    selected_drugs = st.sidebar.multiselect(
        "Available Therapeutics",
        options=drug_options,
        default=["Pembrolizumab", "Cisplatin", "Paclitaxel"]
    )
    
    efficacy = {}
    toxicity = {}

    for drug in selected_drugs:
        defaults = DEFAULT_DRUG_LIBRARY.get(drug, {"efficacy": 5.0, "toxicity": 2.0})
        with st.sidebar.expander(drug, expanded=False):
            efficacy[drug] = st.number_input(
                f"{drug} efficacy score",
                min_value=0.0,
                max_value=20.0,
                value=float(defaults["efficacy"]),
                step=0.1,
                key=f"{drug}_efficacy",
            )
            toxicity[drug] = st.number_input(
                f"{drug} toxicity score",
                min_value=0.0,
                max_value=20.0,
                value=float(defaults["toxicity"]),
                step=0.1,
                key=f"{drug}_toxicity",
            )

    st.sidebar.header("Constraints")
    toxicity_budget = st.sidebar.slider("Toxicity Budget", 10.0, 100.0, 50.0, 1.0)
    alpha = st.sidebar.slider("Efficacy Weight (alpha)", 0.1, 5.0, 1.0, 0.1)
    beta = st.sidebar.slider("Toxicity Weight (beta)", 0.1, 5.0, 1.0, 0.1)
    gamma = st.sidebar.slider("Exclusion Penalty (gamma)", 10.0, 500.0, 100.0, 5.0)
    clearance_rate = st.sidebar.slider("Clearance Rate", 0.05, 1.0, 0.3, 0.05)
    qaoa_reps = st.sidebar.slider("QAOA Reps", 1, 3, 1, 1)
    
    # Run Simulation trigger
    if st.sidebar.button("Run Quantum Optimization", type="primary", use_container_width=True):
        st.session_state['run_sim'] = True
        
    return {
        "age": age,
        "bsa": bsa,
        "days": int(days),
        "selected_drugs": selected_drugs,
        "efficacy": efficacy,
        "toxicity": toxicity,
        "toxicity_budget": toxicity_budget,
        "alpha": alpha,
        "beta": beta,
        "gamma": gamma,
        "clearance_rate": clearance_rate,
        "qaoa_reps": int(qaoa_reps),
    }

def render_efficacy_chart(time_points, no_treatment, std_care, qdos_care):
    """Renders the tumor size comparison line chart."""
    fig = go.Figure()
    
    fig.add_trace(go.Scatter(
        x=time_points, y=no_treatment,
        mode='lines',
        name='No Treatment',
        line=dict(color='#9E9E9E', width=2, dash='dot')
    ))

    fig.add_trace(go.Scatter(
        x=time_points, y=std_care,
        mode='lines+markers',
        name='Standard Care',
        line=dict(color='gray', width=2, dash='dash'),
        marker=dict(symbol='circle', size=6)
    ))
    
    fig.add_trace(go.Scatter(
        x=time_points, y=qdos_care,
        mode='lines+markers',
        name='Q-DOS Optimized',
        line=dict(color='#00E676', width=3), # Distinctive green
        marker=dict(symbol='diamond', size=8)
    ))
    
    fig.update_layout(
        title="Projected Tumor Volume Over 14-Day Cycle",
        xaxis_title="Days",
        yaxis_title="Tumor Size (% of Baseline)",
        template="plotly_dark",
        hovermode="x unified",
        margin=dict(l=20, r=20, t=70, b=20),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
    )
    
    st.plotly_chart(fig, use_container_width=True)

def render_safety_chart(days, qdos_tox, max_tox):
    """Renders the cumulative toxicity chart (area)."""
    fig = go.Figure()
    
    fig.add_trace(go.Scatter(
        x=days, y=qdos_tox,
        fill='tozeroy',
        mode='lines+markers',
        name='Cumulative Toxicity (Q-DOS)',
        line=dict(color='#FF3D00', width=2),
        fillcolor='rgba(255, 61, 0, 0.2)'
    ))
    
    # Horizontal Safety Threshold Line
    fig.add_trace(go.Scatter(
        x=[days[0], days[-1]], y=[max_tox, max_tox],
        mode='lines',
        name='Safety Threshold',
        line=dict(color='red', width=2, dash='dot')
    ))
    
    fig.update_layout(
        title="Safety Profile: Cumulative Toxicity Monitor",
        xaxis_title="Days",
        yaxis_title="Toxicity Index",
        template="plotly_dark",
        hovermode="x unified",
        margin=dict(l=20, r=20, t=70, b=20),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        yaxis=dict(range=[0, max(max_tox * 1.5, max(qdos_tox) * 1.2)])
    )
    
    st.plotly_chart(fig, use_container_width=True)

def render_calendar(schedule_dict):
    """Renders the 14-day treatment schedule grid visually."""
    st.markdown("### 📅 14-Day Treatment Schedule")
    
    days = list(schedule_dict.keys())
    if not days:
        st.info("No treatment schedule was generated.")
        return
    
    # Split the 14 days into two rows of 7 columns
    midpoint = max(len(days) // 2, 1)
    row1 = days[:midpoint]
    row2 = days[midpoint:]
    
    # Render Row 1
    cols1 = st.columns(len(row1))
    for i, col in enumerate(cols1):
        day = row1[i]
        drugs = schedule_dict[day]
        is_rest = len(drugs) == 0 or ("Rest" in drugs)
        
        with col:
            bg_color = "#1E1E1E" if is_rest else "#004D40"
            border_color = "#333333" if is_rest else "#00BFA5"
            text_color = "#888888" if is_rest else "#FFFFFF"
            
            drug_html = "Rest" if is_rest else "<br>".join(drugs)
            
            html = f'''
            <div style="background-color: {bg_color}; border: 1px solid {border_color}; 
                        border-radius: 8px; padding: 10px; text-align: center; height: 100px; 
                        display: flex; flex-direction: column; justify-content: center; margin-bottom: 10px;">
                <div style="color: #AAAAAA; font-size: 0.8rem; margin-bottom: 5px;">Day {day + 1}</div>
                <div style="color: {text_color}; font-weight: bold; font-size: 0.9rem; line-height: 1.2;">
                    {drug_html}
                </div>
            </div>
            '''
            st.markdown(html, unsafe_allow_html=True)
            
    # Render Row 2
    if row2:
        cols2 = st.columns(len(row2))
        for i, col in enumerate(cols2):
            day = row2[i]
            drugs = schedule_dict[day]
            is_rest = len(drugs) == 0 or ("Rest" in drugs)

            with col:
                bg_color = "#1E1E1E" if is_rest else "#004D40"
                border_color = "#333333" if is_rest else "#00BFA5"
                text_color = "#888888" if is_rest else "#FFFFFF"

                drug_html = "Rest" if is_rest else "<br>".join(drugs)

                html = f'''
                <div style="background-color: {bg_color}; border: 1px solid {border_color}; 
                            border-radius: 8px; padding: 10px; text-align: center; height: 100px; 
                            display: flex; flex-direction: column; justify-content: center; margin-bottom: 10px;">
                    <div style="color: #AAAAAA; font-size: 0.8rem; margin-bottom: 5px;">Day {day + 1}</div>
                    <div style="color: {text_color}; font-weight: bold; font-size: 0.9rem; line-height: 1.2;">
                        {drug_html}
                    </div>
                </div>
                '''
                st.markdown(html, unsafe_allow_html=True)


def render_results_summary(solution, optimized_final_size, optimized_reduction, standard_final_size, standard_reduction):
    col2, col3, col4 = st.columns(3)
    col2.metric("Final Tumor Size", f"{optimized_final_size:,.0f}")
    col3.metric("Tumor Reduction", f"{optimized_reduction:.1f}%")
    col4.metric("Objective Score", f"{solution.metrics['objective_score']:.2f}")
    
    st.markdown("")  # Vertical spacing

    st.caption(
        f"Standard-care comparison: final tumor size {standard_final_size:,.0f}, reduction {standard_reduction:.1f}%"
    )


def build_schedule_by_day(schedule):
    if not schedule:
        return {}

    days = len(next(iter(schedule.values())))
    schedule_by_day = {}
    for day in range(days):
        schedule_by_day[day] = [drug for drug, values in schedule.items() if int(values[day]) == 1]
    return schedule_by_day


def build_drug_strength_map(profiles):
    return {
        drug: min(2.5, max(0.2, profile["efficacy"] / 4.0))
        for drug, profile in profiles.items()
    }

def main():
    # Page setup
    st.set_page_config(page_title="Q-DOS Dashboard", page_icon="🧬", layout="wide")
    
    # App Header
    st.title("Q-DOS: Quantum Drug Optimization System")
    st.markdown("*Precision Oncology Multidrug Regimen Solver*")
    st.divider()
    
    # Initialize session state 
    if 'run_sim' not in st.session_state:
        st.session_state['run_sim'] = False
        
    # Sidebar
    params = render_sidebar()
    
    # Initial State (Waiting for user)
    if not st.session_state['run_sim']:
        st.info("👈 Please configure the patient profile and drug library, then click 'Run Quantum Optimization' to generate a regimen.")
        return
        
    # --- Execute Mock "API Calls" ---
    if not params["selected_drugs"]:
        st.error("Please select at least one drug from the library to proceed.")
        return
        
    with st.spinner("Querying Quantum Solver..."):
        config = OptimizationConfig(
            days=params["days"],
            selected_drugs=params["selected_drugs"],
            efficacy=params["efficacy"],
            toxicity=params["toxicity"],
            alpha=params["alpha"],
            beta=params["beta"],
            gamma=params["gamma"],
            clearance_rate=params["clearance_rate"],
            toxicity_budget=params["toxicity_budget"],
            qaoa_reps=params["qaoa_reps"],
            use_qiskit=True,
        )

        solution = run_optimization(config)

        schedule_by_day = build_schedule_by_day(solution.schedule)
        standard_schedule = generate_standard_schedule_for_drugs(params["selected_drugs"], params["days"])

        optimized_sim = TumorSimulator(
            solution.schedule,
            drug_strength=build_drug_strength_map(solution.resolved_profiles),
            drug_toxicity={drug: profile["toxicity"] for drug, profile in solution.resolved_profiles.items()},
            clearance_rate=params["clearance_rate"],
        )
        standard_sim = TumorSimulator(
            standard_schedule,
            drug_strength=build_drug_strength_map(solution.resolved_profiles),
            drug_toxicity={drug: profile["toxicity"] for drug, profile in solution.resolved_profiles.items()},
            clearance_rate=params["clearance_rate"],
        )

        no_treatment = optimized_sim.run_without_treatment()
        optimized_curve = optimized_sim.run_with_treatment()
        standard_curve = standard_sim.run_with_treatment()
        qdos_tox = optimized_sim.calculate_toxicity()
        standard_tox = standard_sim.calculate_toxicity()

        optimized_final_size, optimized_reduction = optimized_sim.calculate_statistics(optimized_curve)
        standard_final_size, standard_reduction = standard_sim.calculate_statistics(standard_curve)
        
    # --- Dashboard View ---
    st.success(f"✅ Optimization complete for Patient (Age: {params['age']}, BSA: {params['bsa']} m²)")
    render_results_summary(solution, optimized_final_size, optimized_reduction, standard_final_size, standard_reduction)
    st.caption(f"Selected drugs: {', '.join(params['selected_drugs'])}")
    
    st.markdown("---")
    st.markdown("")  # Vertical spacing
    
    # Render Plots side-by-side
    col_chart1, col_chart2 = st.columns(2)
    with col_chart1:
        render_efficacy_chart(optimized_sim.time, no_treatment, standard_curve, optimized_curve)
    with col_chart2:
        render_safety_chart(np.arange(1, params["days"] + 1), qdos_tox, params["toxicity_budget"])
    
    st.markdown("")  # Vertical spacing
    st.divider()
    st.markdown("")  # Vertical spacing
    
    # Render the 14-day Calendar view at the bottom
    render_calendar(schedule_by_day)

if __name__ == "__main__":
    main()
