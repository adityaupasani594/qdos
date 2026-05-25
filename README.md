# Quantum Assisted Multi-Drug Scheduling for Precision Oncology

QDOS is a research-grade software toolkit for formulating and solving personalized oncology treatment scheduling problems using a Quadratic Unconstrained Binary Optimization (QUBO) representation. This project was developed as a submission for the Fujitsu Quantum Simulator Challenge 2025-2026 by Vivekanand Education Society's Institute of Technology. The repository integrates optimization, biological validation, and visualization components to generate and evaluate treatment schedules that balance therapeutic efficacy and patient-specific safety constraints.

Table of Contents
- [Overview](#overview)
- [Problem Statement](#problem-statement)
- [Key Capabilities](#key-capabilities)
- [End-to-End Workflow](#end-to-end-workflow)
- [Modeling and Optimization Approach](#modeling-and-optimization-approach)
- [Inputs and Outputs](#inputs-and-outputs)
- [Repository Layout](#repository-layout)
- [Quick Links](#quick-links)
- [Requirements and Installation](#requirements-and-installation)
- [Quick Start](#quick-start)
- [Examples and Reproducible Experiments](#examples-and-reproducible-experiments)
- [Software Architecture](#software-architecture)
- [Backend Integrations](#backend-integrations)
- [Testing and Development](#testing-and-development)
- [Usage: API & CLI Examples](#usage-api--cli-examples)
- [Troubleshooting](#troubleshooting)
- [Contribution Guidelines](#contribution-guidelines)
- [License and Contact](#license-and-contact)
- [Acknowledgements and References](#acknowledgements-and-references)

Overview
---------
QDOS encodes multi-drug, multi-day oncology scheduling as an algebraic Hamiltonian and searches for low-energy solutions using annealing-based optimizers. The system models dynamic drug synergy, organ-level toxicity budgets, and clinical scheduling constraints, then validates candidate schedules with pharmacokinetic/pharmacodynamic (PK/PD) simulations and a two-population tumor model.

Problem Statement
-----------------
Conventional treatment planning for oncology becomes difficult when the schedule must account for multiple drugs, multiple treatment days, drug interaction effects, organ-specific toxicity thresholds, spacing constraints, and patient-specific clinical limitations. These requirements create a combinatorial search space that is expensive to explore with conventional heuristics alone.

This project frames the scheduling task as an optimization problem and seeks treatment plans that minimize an energy function while satisfying safety and feasibility constraints. The aim is not to replace clinical judgment, but to provide a decision-support framework for exploring candidate schedules under structured constraints.

Key Capabilities
----------------
- Expresses clinical objectives and constraints as a QUBO/Hamiltonian.
- Models time-dependent synergy and dose–spacing relationships.
- Enforces individualized toxicity budgets and scheduling rules.
- Compiles Hamiltonians into BQMs compatible with `pyqubo`/`dimod`.
- Supports both hardware-accelerated annealers and classical solver fallbacks.
- Validates solutions using PK/PD ODEs and tumor-response simulation.
- Provides a React-based dashboard for interactive exploration (`/frontend`).

End-to-End Workflow
-------------------
1. Define a patient profile, treatment horizon, and candidate drug library.
2. Build the optimization objective by combining efficacy, toxicity, synergy, and scheduling penalties.
3. Compile the objective into a binary quadratic model.
4. Solve the model using hardware annealing or a local classical fallback.
5. Decode the binary solution into a treatment calendar.
6. Validate the schedule with PK/PD and tumor growth simulation.
7. Review the resulting plots, schedule tables, and performance summaries in the frontend or generated outputs.

Modeling and Optimization Approach
----------------------------------
The repository uses a layered representation so that the clinical problem can be interpreted both mathematically and operationally.

- **Decision variables** represent whether a specific drug is administered on a given day.
- **Synergy terms** reward combinations of drugs and administration sequences that improve efficacy.
- **Toxicity terms** penalize schedules that exceed individualized organ-level safety budgets.
- **Constraint terms** enforce practical clinical rules such as daily limits, mutual exclusion, and recovery gaps.
- **Simulation layers** estimate concentration decay, tumor response, and treatment impact over time.

The result is a schedule that is optimized at the discrete decision level and then validated against a biological model.

Inputs and Outputs
------------------
Typical inputs include:

- Patient age, body surface area, and organ-specific indicators
- Candidate drug list and baseline drug attributes
- Treatment horizon in days
- Safety thresholds and scheduling limits
- Optional solver configuration and backend selection

Typical outputs include:

- A binary schedule or treatment calendar
- Optimization energy / objective value
- Solver timing and comparison metrics
- PK/PD concentration curves
- Tumor growth and response plots
- Summary CSV or other reproducible artifacts in `benchmark_results/`

The repository is organized so that these outputs can be inspected both programmatically and through the frontend dashboard.

Repository Layout
-----------------
- `app.py` — Experiment orchestration and example workflows.
- `api.py` — Minimal API exposing optimization endpoints.
- `simulator.py` — Simulation harness and experiment runner.
- `quantum_optimizer.py` — QUBO/Hamiltonian construction and solver interface.
- `tumor_model.py` — Tumor dynamics and PK/PD integration.
- `hamiltonian/` — Modules that assemble Hamiltonian terms and penalties.
- `benchmark.py` — Scripts to benchmark solver runtimes and compare methods.
- `figures.py`, `plot_results.py` — Scripts to generate figures from experiment outputs.
- `benchmark_results/` — Directory containing example outputs and CSV summaries.
- `frontend/` — React/Vite prototype dashboard and UI components.

If you are reading the repository for the first time, start with `app.py`, `quantum_optimizer.py`, and `tumor_model.py` to understand the flow from optimization to biological validation.

Quick Links
-----------
Direct links to commonly inspected files and folders:

- [app.py](app.py)
- [api.py](api.py)
- [simulator.py](simulator.py)
- [quantum_optimizer.py](quantum_optimizer.py)
- [tumor_model.py](tumor_model.py)
- [hamiltonian/](hamiltonian)
- [benchmark.py](benchmark.py)
- [figures.py](figures.py)
- [frontend/](frontend)

These links open the corresponding repository files when viewed on GitHub or in compatible editors.


Requirements and Installation
-----------------------------

Supported environment

- Python 3.10+. Python 3.11 recommended for improved performance.
- Typical development machine: 8+ GB RAM, modern CPU. Hardware annealers are optional and require vendor access.

Install (recommended)

1. Create and activate a virtual environment:

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1    # PowerShell (Windows)
```

2. Install Python dependencies:

```powershell
pip install --upgrade pip
pip install -r requirements.txt
```

3. Optional solver SDKs and hardware clients

- If you plan to use a vendor annealer (Fujitsu, D-Wave, etc.), install their SDK and set any required credentials (API keys, endpoints) as environment variables. Inspect `quantum_optimizer.py` for integration points.

Notes

- If `requirements.txt` pins heavy numerical packages, prefer installing with a conda environment on older systems.
- If you see numerical errors during ODE integration, ensure `scipy` and `numpy` are recent versions.

Quick Start
-----------
Perform a basic environment check:

```powershell
python smoke_test.py
```

Run a sample simulation or experiment:

```powershell
python simulator.py
# or a higher-level orchestrator/demo
python app.py
```

Start the API server (serves endpoints used by the frontend):

```powershell
python api.py
```

Run the frontend (development mode):

```powershell
cd frontend
npm install
npm run dev
```

Open the UI at the Vite dev server URL (typically `http://localhost:5173`).

Usage: API & CLI Examples
------------------------
Example: call the optimization API (if `api.py` exposes endpoints):

```bash
curl -X POST http://localhost:5000/optimize \
	-H "Content-Type: application/json" \
	-d '{"patient_profile": {...}, "drugs": [...], "horizon": 14}'
```

Example: run a deterministic local optimization with a preset configuration:

```powershell
python app.py --config experiments/example_config.yaml --mode local
```

When running experiments, the code writes outputs to `benchmark_results/` by default; consult `benchmark.py` or `simulator.py` to change output paths and formats.

Examples and Reproducible Experiments
-----------------------------------
Benchmarking and figure generation rely on the `benchmark.py` and plotting scripts. Example workflow:

```powershell
python benchmark.py --output benchmark_results/summary.csv
python figures.py
python plot_results.py benchmark_results/summary.csv
```

See the header docstrings of `benchmark.py` and `simulator.py` for parameter descriptions and experiment presets.

Reproducibility checklist
-------------------------
- Use a clean virtual environment and record your `pip freeze > requirements-lock.txt` so runs are reproducible.
- Store experiment configurations (JSON/YAML) alongside results.
- Use the provided scripts rather than ad-hoc calls where possible:

```powershell
python benchmark.py --output benchmark_results/summary.csv --seed 1234
python figures.py --input benchmark_results/summary.csv --out figures/
```

This repository includes example outputs in `benchmark_results/` that can be used to validate plotting and figure reproduction.

Software Architecture
---------------------
- QUBO Builder (`hamiltonian/`): Constructs the objective and penalty terms that comprise the Hamiltonian (dynamic synergy reward, toxicity penalty, mutual exclusion, daily limits, recovery gaps).
- Optimizer (`quantum_optimizer.py`): Translates the symbolic Hamiltonian to a BQM and dispatches to a solver backend (hardware or classical).
- Validation Engine (`tumor_model.py`): Converts discrete schedules into continuous concentration trajectories, integrates PK/PD ODEs with SciPy, and simulates tumor and resistant-cell dynamics.
- Binary Schedule Interpreter: Maps solver bitstrings to human-readable schedules and validates clinical feasibility.
- Frontend (`frontend/`): React components for patient profile input, schedule visualization, tumor curves, and solver result inspection.

Backend Integrations
--------------------
The codebase supports two solver modes:

- Hardware-accelerated annealing: Submit the compiled Hamiltonian to vendor APIs (requires credentials and SDK). The implementation serializes the Hamiltonian as a physical energy landscape for submission.
- Classical fallback: Local BQM evaluation and simulated annealing provide a reproducible development path without specialized hardware.

Scope and Limitations
---------------------
- This project is intended for research, prototyping, and decision-support exploration.
- It should not be used as a substitute for clinical decision-making.
- The quality of the generated schedules depends on the completeness of the patient profile, the validity of model assumptions, and the calibration of toxicity and synergy parameters.
- Hardware backend behavior may vary depending on vendor SDK versions and available credentials.

Testing and Development
-----------------------
- Run unit tests with `pytest`:

```powershell
pip install pytest
pytest -q
```

- Use `smoke_test.py` for a quick runtime validation of numerical libraries and plotting backends.
- Add tests alongside modules (`test_*.py`) for new functionality.

Troubleshooting
---------------
- ODE integration fails or returns NaNs: upgrade `numpy` and `scipy`, and verify input parameter ranges. Run `smoke_test.py` to check core dependencies.
- Missing plotting/GUI behavior: ensure `matplotlib` and frontend dependencies are installed. For frontend issues, run `npm run dev` in `frontend/` and inspect the browser console.
- Hardware submission errors: verify vendor credentials, network connectivity, and that the Hamiltonian serialization matches the vendor SDK expectations.

How to Read the Results
-----------------------
- A low optimization energy indicates that the solver found a schedule that better satisfies the encoded objective.
- Schedule plots show when each drug is administered across the horizon.
- Tumor response curves show how the model predicts the effect of the selected schedule over time.
- Solver comparison charts summarize runtime and quality differences across approaches.
- If the biological validation shows weak control or high toxicity, the schedule should be treated as a candidate for further refinement rather than a final recommendation.

Contribution Guidelines
-----------------------
- Use feature branches and open pull requests against the repository's default branch.
- Provide unit tests and documentation for new functionality.
- Keep changes focused; include a clear description of design and rationale in PRs.
- For substantial design changes (new solver backends, different tumor models), open an issue to discuss the proposal before implementing.

License and Contact
-------------------
This repository does not include a license file by default. If the code is to be redistributed or published, add a `LICENSE` file at the project root (common choices: MIT, Apache-2.0, BSD-3-Clause).

For technical inquiries or reproducibility assistance, open an issue or contact the maintainers via the project metadata.

Acknowledgements and References
-------------------------------
This project was developed as a submission for the Fujitsu Quantum Simulator Challenge 2025-2026 by Vivekanand Education Society's Institute of Technology. The work builds on literature in oncology scheduling, QUBO formulations, and annealing-based optimization. See inline references in the report and source docstrings for citations and background.

Participants
------------
- Aditya Upasani
- Ranjan Bala Jain
- Rushikesh Shembade
- Yash Mahajan
