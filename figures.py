"""
figures.py — Publication-quality figure generation for Q-DOS (300 DPI PNG).

Figures:
  1. Tumor growth curves (all 4 schedules + no-treatment, with CI bands)
  2. Daily toxicity bar chart vs budget threshold
  3. Biomarker radar chart (PDL1 / BRCA / VEGF vs drug)
  4. Sensitivity tornado plot
  5. Statistical summary table
"""

import os
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import seaborn as sns
from typing import Dict, List, Optional

from statistics_engine import StatisticsReport
from sensitivity import SensitivityReport

os.makedirs("figures", exist_ok=True)

sns.set_theme(style="whitegrid", font_scale=1.15)
plt.rcParams.update({
    "font.family":     "DejaVu Sans",
    "axes.titleweight": "bold",
    "axes.spines.top":  False,
    "axes.spines.right": False,
})

PALETTE = {
    "Q-DOS":          "#4f46e5",
    "Standard Care":  "#64748b",
    "Greedy":         "#f59e0b",
    "Random":         "#ef4444",
    "No Treatment":   "#0f172a",
}
DRUG_COLORS = ["#4f46e5", "#10b981", "#f59e0b", "#ef4444", "#a855f7"]


# ─────────────────────────────────────────────────────────────────────────────
# Figure 1 — Tumor growth curves
# ─────────────────────────────────────────────────────────────────────────────
def figure1_tumor_curves(
    t_days,
    tumor_qdos,
    tumor_std,
    tumor_no_tx,
    tumor_greedy=None,
    tumor_random=None,
    ci_qdos: Optional[tuple] = None,
    output_path: str = "figures/fig1_tumor_curves.png",
):
    fig, ax = plt.subplots(figsize=(11, 6))

    ax.plot(t_days, tumor_no_tx,
            color=PALETTE["No Treatment"], lw=2, ls="--",
            label="No Treatment", alpha=0.70)
    ax.plot(t_days, tumor_std,
            color=PALETTE["Standard Care"], lw=2,
            label="Standard Care", alpha=0.85)
    if tumor_greedy is not None:
        ax.plot(t_days, tumor_greedy,
                color=PALETTE["Greedy"], lw=2,
                label="Greedy", alpha=0.85)
    if tumor_random is not None:
        ax.plot(t_days, tumor_random,
                color=PALETTE["Random"], lw=2,
                label="Random", alpha=0.75)
    ax.plot(t_days, tumor_qdos,
            color=PALETTE["Q-DOS"], lw=3.5,
            label="Q-DOS Optimized", zorder=5)
    if ci_qdos is not None:
        lo, hi = ci_qdos
        ax.fill_between(t_days, lo, hi,
                        color=PALETTE["Q-DOS"], alpha=0.12,
                        label="Q-DOS 95% CI")

    ax.set_xlabel("Time (Days)", fontsize=13)
    ax.set_ylabel("Tumor Cell Count", fontsize=13)
    ax.set_title("Tumor Growth Curves: Q-DOS vs Baselines", fontsize=15)
    ax.legend(frameon=True, loc="upper right")
    ax.yaxis.get_major_formatter().set_scientific(True)
    ax.yaxis.get_major_formatter().set_powerlimits((0, 0))
    ax.yaxis.set_major_formatter(
        matplotlib.ticker.FuncFormatter(lambda x, _: f"{x:.2e}")
    )

    fig.tight_layout()
    fig.savefig(output_path, dpi=300, bbox_inches="tight")
    plt.close(fig)
    return output_path


# ─────────────────────────────────────────────────────────────────────────────
# Figure 2 — Daily toxicity bars
# ─────────────────────────────────────────────────────────────────────────────
def figure2_toxicity_bars(
    days: int,
    tox_qdos: list,
    tox_std: list,
    budget: float,
    output_path: str = "figures/fig2_toxicity.png",
):
    fig, ax = plt.subplots(figsize=(12, 5))
    x = np.arange(days)
    w = 0.38

    ax.bar(x - w / 2, tox_std[:days],  w,
           color=PALETTE["Standard Care"], alpha=0.85, label="Standard Care")
    ax.bar(x + w / 2, tox_qdos[:days], w,
           color=PALETTE["Q-DOS"],         alpha=0.90, label="Q-DOS")

    daily_budget = budget / max(days, 1)
    ax.axhline(daily_budget, color="#dc2626", lw=2, ls="--",
               label=f"Per-Day Budget ({daily_budget:.2f})")

    ax.set_xlabel("Day", fontsize=13)
    ax.set_ylabel("Daily Toxicity Index", fontsize=13)
    ax.set_title("Daily Toxicity: Q-DOS vs Standard Care", fontsize=15)
    ax.legend(frameon=True)

    fig.tight_layout()
    fig.savefig(output_path, dpi=300, bbox_inches="tight")
    plt.close(fig)
    return output_path


# ─────────────────────────────────────────────────────────────────────────────
# Figure 3 — Biomarker radar chart
# ─────────────────────────────────────────────────────────────────────────────
def figure3_biomarker_radar(
    biomarker_impact: Dict[str, Dict[str, float]],
    output_path: str = "figures/fig3_biomarker_radar.png",
):
    """
    biomarker_impact = {
        "Pembrolizumab": {"PDL1": 0.9, "BRCA": 0.2, "VEGF": 0.1},
        ...
    }
    """
    drugs      = list(biomarker_impact.keys())
    categories = ["PDL1", "BRCA", "VEGF"]
    N          = len(categories)
    angles     = (np.linspace(0, 2 * np.pi, N, endpoint=False) + np.pi / 2).tolist()
    angles    += angles[:1]

    fig, ax = plt.subplots(figsize=(7, 7), subplot_kw=dict(polar=True))

    for i, drug in enumerate(drugs):
        vals  = [biomarker_impact[drug].get(c, 0.0) for c in categories]
        vals += vals[:1]
        color = DRUG_COLORS[i % len(DRUG_COLORS)]
        ax.plot(angles, vals, color=color, lw=2.5, label=drug)
        ax.fill(angles, vals, color=color, alpha=0.12)

    ax.set_xticks(angles[:-1])
    ax.set_xticklabels(categories, fontsize=13, fontweight="bold")
    ax.set_ylim(0, 1.05)
    ax.set_title("Biomarker–Drug Sensitivity Radar", fontsize=14, pad=24)
    ax.legend(loc="upper right", bbox_to_anchor=(1.35, 1.15))

    fig.tight_layout()
    fig.savefig(output_path, dpi=300, bbox_inches="tight")
    plt.close(fig)
    return output_path


# ─────────────────────────────────────────────────────────────────────────────
# Figure 4 — Sensitivity tornado
# ─────────────────────────────────────────────────────────────────────────────
def figure4_sensitivity_tornado(
    sensitivity_report: SensitivityReport,
    output_path: str = "figures/fig4_sensitivity_tornado.png",
):
    params  = sorted(sensitivity_report.parameters,
                     key=lambda p: p.sensitivity_index, reverse=True)
    names   = [p.parameter  for p in params]
    indices = [p.sensitivity_index for p in params]

    median_idx = float(np.median(indices)) if indices else 0.0
    colors = [PALETTE["Q-DOS"] if v > median_idx else "#a5b4fc" for v in indices]

    fig, ax = plt.subplots(figsize=(9, 6))
    bars = ax.barh(names, indices, color=colors, edgecolor="white", linewidth=0.5)

    for bar, val in zip(bars, indices):
        ax.text(bar.get_width() + max(indices) * 0.01,
                bar.get_y() + bar.get_height() / 2,
                f"{val:.3f}", va="center", fontsize=10)

    ax.set_xlabel("Normalized Sensitivity Index |S_i|", fontsize=12)
    ax.set_title("Sensitivity Analysis: Parameter Impact on Objective",
                 fontsize=14)
    ax.invert_yaxis()

    fig.tight_layout()
    fig.savefig(output_path, dpi=300, bbox_inches="tight")
    plt.close(fig)
    return output_path


# ─────────────────────────────────────────────────────────────────────────────
# Figure 5 — Summary comparison table
# ─────────────────────────────────────────────────────────────────────────────
def figure5_summary_table(
    stats_report: StatisticsReport,
    output_path: str = "figures/fig5_summary_table.png",
):
    col_labels = [
        "Strategy",
        "Mean Tumor\nReduction (%)",
        "95% CI (Reduction)",
        "Mean Toxicity",
        "95% CI (Toxicity)",
    ]
    table_data = []
    for s in stats_report.schedules:
        table_data.append([
            s.strategy,
            f"{s.mean_tumor_reduction:.1f}%",
            f"[{s.ci_low:.1f},  {s.ci_high:.1f}]",
            f"{s.mean_toxicity:.2f}",
            f"[{s.tox_ci_low:.2f},  {s.tox_ci_high:.2f}]",
        ])

    fig, ax = plt.subplots(figsize=(13, max(3, 1 + len(table_data))))
    ax.axis("off")

    tbl = ax.table(
        cellText=table_data,
        colLabels=col_labels,
        cellLoc="center",
        loc="center",
    )
    tbl.auto_set_font_size(False)
    tbl.set_fontsize(11)
    tbl.scale(1, 2.2)

    for j in range(len(col_labels)):
        tbl[(0, j)].set_facecolor("#4f46e5")
        tbl[(0, j)].set_text_props(color="white", fontweight="bold")

    for i, s in enumerate(stats_report.schedules):
        if s.strategy == "Q-DOS":
            for j in range(len(col_labels)):
                tbl[(i + 1, j)].set_facecolor("#ede9fe")

    ax.set_title(
        f"Statistical Summary: Q-DOS vs Baselines  "
        f"(N={stats_report.n_simulations}, "
        f"{int(stats_report.confidence_level * 100)}% CI)",
        fontsize=14, pad=16,
    )

    fig.tight_layout()
    fig.savefig(output_path, dpi=300, bbox_inches="tight")
    plt.close(fig)
    return output_path


# ─────────────────────────────────────────────────────────────────────────────
# Convenience wrapper
# ─────────────────────────────────────────────────────────────────────────────
def generate_all_figures(
    t_days,
    tumor_qdos,
    tumor_std,
    tumor_no_tx,
    tox_qdos_daily: list,
    tox_std_daily: list,
    budget: float,
    biomarker_impact: Dict[str, Dict[str, float]],
    stats_report: StatisticsReport,
    sensitivity_report: SensitivityReport,
    tumor_greedy=None,
    tumor_random=None,
) -> Dict[str, str]:
    """Generate all five figures and return dict of paths."""
    return {
        "fig1": figure1_tumor_curves(
            t_days, tumor_qdos, tumor_std, tumor_no_tx,
            tumor_greedy, tumor_random
        ),
        "fig2": figure2_toxicity_bars(
            len(list(t_days)), tox_qdos_daily, tox_std_daily, budget
        ),
        "fig3": figure3_biomarker_radar(biomarker_impact),
        "fig4": figure4_sensitivity_tornado(sensitivity_report),
        "fig5": figure5_summary_table(stats_report),
    }
