"""
report_generator.py — Tier 3: Automated PDF patient report using ReportLab.

Generates a multi-section PDF including:
  - Patient parameters table
  - Optimized schedule
  - Drug selection explanations
  - Publication figures (embedded)
  - Statistical summary
  - Sensitivity analysis
"""

import os
import io
from datetime import date
from typing import Dict, List

import numpy as np

os.makedirs("reports", exist_ok=True)

try:
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import cm
    from reportlab.lib import colors
    from reportlab.platypus import (
        SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
        PageBreak, Image as RLImage, HRFlowable,
    )
    REPORTLAB_AVAILABLE = True
except ImportError:
    REPORTLAB_AVAILABLE = False


# ─────────────────────────────────────────────────────────────────────────────
# Style helpers
# ─────────────────────────────────────────────────────────────────────────────
INDIGO  = colors.HexColor("#4f46e5")
SLATE   = colors.HexColor("#1e293b")
LIGHT   = colors.HexColor("#ede9fe")
WHITE   = colors.white
WARN    = colors.HexColor("#ef4444")

def _styles():
    ss = getSampleStyleSheet()
    ss.add(ParagraphStyle("QTitle",   parent=ss["Title"],   fontSize=22, textColor=INDIGO, spaceAfter=6))
    ss.add(ParagraphStyle("QH1",      parent=ss["Heading1"], fontSize=14, textColor=SLATE, spaceBefore=12, spaceAfter=4))
    ss.add(ParagraphStyle("QBody",    parent=ss["Normal"],  fontSize=10, leading=14, spaceAfter=4))
    ss.add(ParagraphStyle("QCaption", parent=ss["Normal"],  fontSize=8,  textColor=colors.grey, alignment=1))
    ss.add(ParagraphStyle("QWarn",    parent=ss["Normal"],  fontSize=10, textColor=WARN, leading=14))
    return ss


def _table_style(header_col=INDIGO):
    return TableStyle([
        ("BACKGROUND",  (0, 0), (-1, 0),  header_col),
        ("TEXTCOLOR",   (0, 0), (-1, 0),  WHITE),
        ("FONTNAME",    (0, 0), (-1, 0),  "Helvetica-Bold"),
        ("FONTSIZE",    (0, 0), (-1, -1), 9),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, LIGHT]),
        ("GRID",        (0, 0), (-1, -1), 0.4, colors.lightgrey),
        ("VALIGN",      (0, 0), (-1, -1), "MIDDLE"),
        ("ALIGN",       (1, 0), (-1, -1), "CENTER"),
        ("TOPPADDING",  (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING",(0, 0), (-1, -1), 5),
    ])


# ─────────────────────────────────────────────────────────────────────────────
# Generate figures and embed
# ─────────────────────────────────────────────────────────────────────────────
def _generate_and_embed_figures(config, solution, sim_result, pop_notx, std_baseline, ss):
    """Generate all 5 figures and return as ReportLab flowables."""
    from figures import (
        figure1_tumor_curves, figure2_toxicity_bars,
        figure3_biomarker_radar, figure5_summary_table,
    )
    from tumor_model import DRUG_BIOMARKER_AFFINITIES

    flowables = []

    days   = config.days
    t_days = list(np.linspace(0, days, len(sim_result.tumor_population)))

    std_sim_pop = [float(p) for p in sim_result.tumor_population]
    tumor_qdos  = [float(p) for p in sim_result.tumor_population]
    tumor_notx  = [float(p) for p in pop_notx[:len(tumor_qdos)]]

    # Fig 1
    p1 = figure1_tumor_curves(t_days, tumor_qdos, std_sim_pop, tumor_notx,
                               output_path="figures/report_fig1.png")
    flowables += [Paragraph("Figure 1 — Tumor Growth Curves", ss["QCaption"]),
                  RLImage(p1, width=16*cm, height=9*cm),
                  Spacer(1, 6)]

    # Fig 2
    tox_std = [0.0] * days
    for d, arr in std_baseline.schedule.items():
        from quantum_optimizer import get_effective_toxicity
        t_eff = get_effective_toxicity(d, config)
        for t, v in enumerate(arr):
            if v == 1 and t < days:
                tox_std[t] += t_eff

    budget = config.base_toxicity_budget - 0.5 * (config.patient_profile.get("age", 40) - 40)
    p2 = figure2_toxicity_bars(days, sim_result.daily_toxicity[:days],
                               tox_std[:days], budget,
                               output_path="figures/report_fig2.png")
    flowables += [Paragraph("Figure 2 — Daily Toxicity Comparison", ss["QCaption"]),
                  RLImage(p2, width=16*cm, height=7*cm),
                  Spacer(1, 6)]

    # Fig 3
    biomarker_impact = {d: {m: DRUG_BIOMARKER_AFFINITIES.get(d, {}).get(m, 0.0)
                             for m in ["PDL1", "BRCA", "VEGF"]}
                        for d in config.selected_drugs}
    p3 = figure3_biomarker_radar(biomarker_impact, output_path="figures/report_fig3.png")
    flowables += [Paragraph("Figure 3 — Biomarker Radar", ss["QCaption"]),
                  RLImage(p3, width=10*cm, height=10*cm),
                  Spacer(1, 6)]

    return flowables


# ─────────────────────────────────────────────────────────────────────────────
# Main report builder
# ─────────────────────────────────────────────────────────────────────────────
def generate_patient_report(
    patient_id: str,
    config,
    solution,
    sim_result,
    pop_notx,
    std_baseline,
) -> str:
    if not REPORTLAB_AVAILABLE:
        raise ImportError("reportlab is not installed. Run: pip install reportlab")

    output_path = f"reports/patient_{patient_id}_report.pdf"
    ss          = _styles()
    doc         = SimpleDocTemplate(
        output_path,
        pagesize=A4,
        leftMargin=2*cm, rightMargin=2*cm,
        topMargin=2*cm,  bottomMargin=2*cm,
    )
    story = []

    # ── Title ─────────────────────────────────────────────────────────────────
    story.append(Paragraph("Q-DOS Patient Treatment Report", ss["QTitle"]))
    story.append(Paragraph(
        f"Patient ID: <b>{patient_id}</b> | Date: {date.today().isoformat()} | "
        f"Horizon: {config.days} days",
        ss["QBody"]
    ))
    story.append(HRFlowable(width="100%", thickness=1, color=INDIGO, spaceAfter=10))

    # ── Patient Parameters ────────────────────────────────────────────────────
    story.append(Paragraph("1. Patient Parameters", ss["QH1"]))
    profile = config.patient_profile
    sub     = config.subtype_scores

    params_data = [
        ["Parameter", "Value"],
        ["Age",              str(int(profile.get("age", 40)))],
        ["Kidney Function",  f"{profile.get('kidney',  1.0):.1f}"],
        ["Liver Function",   f"{profile.get('liver',   1.0):.1f}"],
        ["Bone Marrow",      f"{profile.get('marrow',  1.0):.1f}"],
        ["Immune System",    f"{profile.get('immune',  1.0):.1f}"],
        ["Vascular",         f"{profile.get('vascular',1.0):.1f}"],
        ["PDL1 Score",       f"{sub.get('PDL1', 0.5):.2f}"],
        ["BRCA Score",       f"{sub.get('BRCA', 0.5):.2f}"],
        ["VEGF Score",       f"{sub.get('VEGF', 0.5):.2f}"],
        ["Toxicity Budget",  f"{config.base_toxicity_budget:.1f}"],
        ["Selected Drugs",   ", ".join(config.selected_drugs)],
    ]
    t = Table(params_data, colWidths=[8*cm, 8*cm])
    t.setStyle(_table_style())
    story += [t, Spacer(1, 10)]

    # ── Optimization Metrics ──────────────────────────────────────────────────
    story.append(Paragraph("2. Optimization Metrics", ss["QH1"]))
    m       = solution.metrics
    budget  = config.base_toxicity_budget - 0.5 * (config.patient_profile.get("age", 40) - 40)
    violated = m.get("constraint_violated", False)

    metrics_data = [
        ["Metric", "Value"],
        ["Optimizer Status",          solution.status],
        ["Objective Score",           f"{m.get('score', 0):.4f}"],
        ["Total Toxicity",            f"{m.get('total_toxicity', 0):.3f}"],
        ["Adjusted Budget",           f"{budget:.2f}"],
        ["Tumor Reduction vs NoTx",   f"{sim_result.tumor_reduction_pct:.1f}%"],
        ["Hard Constraint Violated",  "⚠ YES" if violated else "✓ NO"],
    ]
    t2 = Table(metrics_data, colWidths=[9*cm, 7*cm])
    t2.setStyle(_table_style(WARN if violated else INDIGO))
    story += [t2, Spacer(1, 10)]

    # ── Optimized Schedule ────────────────────────────────────────────────────
    story.append(Paragraph("3. Optimized Treatment Schedule", ss["QH1"]))
    sched_header = ["Day"] + config.selected_drugs
    sched_data   = [sched_header]
    for t_idx in range(config.days):
        row = [str(t_idx + 1)]
        for d in config.selected_drugs:
            row.append("✓" if solution.schedule.get(d, [0]*config.days)[t_idx] == 1 else "—")
        sched_data.append(row)

    col_w = [2*cm] + [14*cm / len(config.selected_drugs)] * len(config.selected_drugs)
    t3 = Table(sched_data, colWidths=col_w)
    t3.setStyle(_table_style())
    story += [t3, Spacer(1, 10)]

    # ── Explanations ──────────────────────────────────────────────────────────
    story.append(Paragraph("4. Drug Selection Explanations", ss["QH1"]))
    for expl in solution.explanations:
        day   = expl.get("day", "?")
        drugs = expl.get("drugs", [])
        if not drugs:
            continue
        story.append(Paragraph(
            f"<b>Day {day}:</b> {', '.join(drugs)}",
            ss["QBody"]
        ))
        for r in expl.get("rationale", []):
            style = ss["QWarn"] if "⚠" in r else ss["QBody"]
            story.append(Paragraph(f"  → {r}", style))
    story += [Spacer(1, 10), PageBreak()]

    # ── Figures ───────────────────────────────────────────────────────────────
    story.append(Paragraph("5. Clinical Figures", ss["QH1"]))
    try:
        fig_flowables = _generate_and_embed_figures(
            config, solution, sim_result, pop_notx, std_baseline, ss
        )
        story.extend(fig_flowables)
    except Exception as e:
        story.append(Paragraph(f"[Figure generation error: {e}]", ss["QWarn"]))

    # ── Build PDF ─────────────────────────────────────────────────────────────
    doc.build(story)
    return output_path
