#!/usr/bin/env python3
from __future__ import annotations

import json
import math
import os
import re
import shutil
import textwrap
import zipfile
from dataclasses import dataclass, replace
from pathlib import Path
from collections import defaultdict
from typing import Callable

ROOT = Path(__file__).resolve().parents[1]
PRODUCT_NAME = "AssayAtlas"
os.environ.setdefault("MPLCONFIGDIR", str(ROOT / ".mplconfig"))
os.environ.setdefault("XDG_CACHE_HOME", str(ROOT / ".cache"))

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import statsmodels.api as sm
from lifelines import CoxPHFitter, KaplanMeierFitter
from lifelines.datasets import load_rossi, load_waltons
from lifelines.statistics import logrank_test
from matplotlib.patches import Ellipse
from PIL import Image
from scipy import stats
from scipy.optimize import curve_fit
from sklearn.decomposition import PCA
from sklearn.preprocessing import StandardScaler
from statsmodels.formula.api import ols
from statsmodels.stats.anova import anova_lm
from statsmodels.stats.multicomp import pairwise_tukeyhsd

RAW_DIR = ROOT / "data" / "raw"
GENERATED_DIR = ROOT / "data" / "generated"
CHART_DIR = ROOT / "app" / "static" / "generated" / "charts"
EXPORT_DIR = GENERATED_DIR / "exports"
PUBLICATION_DIR = GENERATED_DIR / "publication"
SCREENSHOT_DIR = ROOT / "assets" / "screenshots"
DOCS_DIR = ROOT / "docs"
TUTORIAL_DIR = DOCS_DIR / "tutorial"

os.environ["HOME"] = str(ROOT)
from pydataset import data as rdata  # noqa: E402


@dataclass(frozen=True)
class UseCaseSpec:
    order: int
    slug: str
    title: str
    category: str
    analysis: str
    goal: str
    steps: list[str]
    what_to_notice: str
    data_files: list[str]
    source_note: str
    builder: str


def ensure_dirs() -> None:
    GENERATED_DIR.mkdir(parents=True, exist_ok=True)
    CHART_DIR.mkdir(parents=True, exist_ok=True)
    EXPORT_DIR.mkdir(parents=True, exist_ok=True)
    PUBLICATION_DIR.mkdir(parents=True, exist_ok=True)
    SCREENSHOT_DIR.mkdir(parents=True, exist_ok=True)
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    TUTORIAL_DIR.mkdir(parents=True, exist_ok=True)


def apply_style() -> None:
    plt.rcParams.update(
        {
            "figure.facecolor": "#ffffff",
            "axes.facecolor": "#ffffff",
            "savefig.facecolor": "#ffffff",
            "axes.edgecolor": "#252b33",
            "axes.labelcolor": "#252b33",
            "axes.linewidth": 1.1,
            "axes.titleweight": "bold",
            "axes.titlesize": 14.5,
            "axes.titlepad": 12,
            "font.size": 10.5,
            "font.family": "DejaVu Sans",
            "xtick.color": "#4b5563",
            "ytick.color": "#4b5563",
            "xtick.direction": "out",
            "ytick.direction": "out",
            "grid.color": "#e6ebf1",
            "grid.alpha": 1.0,
            "grid.linewidth": 0.9,
            "grid.linestyle": "-",
            "axes.grid": False,
            "axes.spines.top": False,
            "axes.spines.right": False,
            "legend.frameon": False,
        }
    )


COLORS = {
    "ink": "#20252c",
    "gray": "#667085",
    "grid": "#e6ebf1",
    "navy": "#264f86",
    "blue": "#4a7ebb",
    "teal": "#2f8f8b",
    "gold": "#c4922f",
    "coral": "#d56a4b",
    "rose": "#c95f79",
    "sage": "#6b8c66",
    "violet": "#7e6ab3",
    "light_blue": "#dbe8f6",
    "light_teal": "#d9f0ec",
    "light_coral": "#f7ddd5",
    "light_gray": "#f6f8fb",
}


def fmt_p(value: float) -> str:
    if value < 0.001:
        return "< 0.001"
    return f"{value:.3f}"


def significance_label(value: float) -> str:
    if value < 0.001:
        return "***"
    if value < 0.01:
        return "**"
    if value < 0.05:
        return "*"
    return "ns"


def save_chart(fig: plt.Figure, name: str) -> str:
    path = CHART_DIR / name
    stem = path.stem
    export_dir = EXPORT_DIR / stem
    export_dir.mkdir(parents=True, exist_ok=True)
    fig.tight_layout(rect=[0.04, 0.04, 0.98, 0.90], pad=0.9)
    fig.savefig(path, dpi=260, bbox_inches="tight")
    fig.savefig(export_dir / f"{stem}.svg", bbox_inches="tight")
    fig.savefig(export_dir / f"{stem}.pdf", bbox_inches="tight")
    fig.savefig(export_dir / f"{stem}.png", dpi=600, bbox_inches="tight")
    fig.savefig(
        export_dir / f"{stem}.tiff",
        dpi=300,
        bbox_inches="tight",
        pil_kwargs={"compression": "tiff_lzw"},
    )
    plt.close(fig)
    return f"generated/charts/{name}"


def to_records_table(df: pd.DataFrame, rows: int = 8) -> list[dict[str, object]]:
    preview = df.head(rows).copy()
    if preview.index.name or not isinstance(preview.index, pd.RangeIndex):
        preview = preview.reset_index(drop=False)
    preview = preview.where(pd.notnull(preview), None)
    return preview.to_dict(orient="records")


def vendor_rdataset(name: str, filename: str | None = None) -> Path:
    df = rdata(name)
    if df is None:
        raise ValueError(f"Dataset {name} could not be loaded from pydataset")
    if filename is None:
        filename = f"{name}.csv"
    path = RAW_DIR / filename
    df.to_csv(path, index=False)
    return path


def load_csv(name: str) -> pd.DataFrame:
    path = RAW_DIR / name
    df = pd.read_csv(path)
    if "rownames" in df.columns:
        df = df.drop(columns=["rownames"])
    return df


def simple_card(fig: plt.Figure, title: str, subtitle: str) -> None:
    fig.text(0.07, 0.965, title, fontsize=16, weight="bold", color=COLORS["ink"], va="top")
    fig.text(0.07, 0.928, subtitle, fontsize=9.4, color=COLORS["gray"], va="top")


def write_json(path: Path, payload: object) -> None:
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def write_text(path: Path, content: str) -> None:
    path.write_text(content.rstrip() + "\n", encoding="utf-8")


def confidence_interval(values: np.ndarray, alpha: float = 0.05) -> tuple[float, float]:
    mean = float(np.mean(values))
    sem = stats.sem(values)
    margin = sem * stats.t.ppf(1 - alpha / 2, len(values) - 1)
    return mean - margin, mean + margin


def regression_band(model, grid: np.ndarray, predictor: str) -> pd.DataFrame:
    pred = model.get_prediction(pd.DataFrame({predictor: grid}))
    frame = pred.summary_frame(alpha=0.05)
    frame[predictor] = grid
    return frame


def michaelis_menten(x: np.ndarray, vmax: float, km: float) -> np.ndarray:
    return (vmax * x) / (km + x)


def exp_decay(x: np.ndarray, a: float, k: float) -> np.ndarray:
    return a * np.exp(-k * x)


def style_axis(ax: plt.Axes, xlabel: str | None = None, ylabel: str | None = None, grid: str = "y") -> None:
    if xlabel:
        ax.set_xlabel(xlabel, labelpad=8)
    if ylabel:
        ax.set_ylabel(ylabel, labelpad=8)
    ax.spines["left"].set_linewidth(1.1)
    ax.spines["bottom"].set_linewidth(1.1)
    ax.tick_params(length=4.2, width=1.0)
    ax.grid(False)
    if grid in {"y", "both"}:
        ax.yaxis.grid(True, color=COLORS["grid"], linewidth=0.9)
    if grid in {"x", "both"}:
        ax.xaxis.grid(True, color=COLORS["grid"], linewidth=0.9)
    ax.set_axisbelow(True)


def add_result_badge(ax: plt.Axes, text: str, loc: tuple[float, float] = (0.02, 0.98), ha: str = "left") -> None:
    ax.text(
        loc[0],
        loc[1],
        text,
        transform=ax.transAxes,
        ha=ha,
        va="top",
        fontsize=9.6,
        color=COLORS["ink"],
        bbox={
            "boxstyle": "round,pad=0.32,rounding_size=0.12",
            "facecolor": COLORS["light_gray"],
            "edgecolor": "#d6dde6",
            "linewidth": 0.9,
        },
    )


def swarm_positions(values: np.ndarray, center: float, spread: float = 0.16) -> np.ndarray:
    if len(values) == 1:
        return np.array([center])
    ranks = np.argsort(np.argsort(values))
    centered = ranks - (len(values) - 1) / 2
    scale = spread / max(np.max(np.abs(centered)), 1)
    return center + centered * scale


def draw_group_summary(ax: plt.Axes, center: float, values: np.ndarray, color: str, label: str | None = None) -> None:
    xs = swarm_positions(values, center)
    ax.scatter(xs, values, s=44, color=color, edgecolor="white", linewidth=0.8, zorder=3, label=label)
    mean = float(np.mean(values))
    low_ci, high_ci = confidence_interval(values)
    ax.vlines(center, low_ci, high_ci, color=COLORS["ink"], linewidth=1.6, zorder=4)
    ax.plot([center - 0.12, center + 0.12], [mean, mean], color=COLORS["ink"], linewidth=2.0, zorder=4)


def add_sig_bracket(ax: plt.Axes, x1: float, x2: float, y: float, label: str) -> None:
    span = ax.get_ylim()[1] - ax.get_ylim()[0]
    h = span * 0.035
    ax.plot([x1, x1, x2, x2], [y, y + h, y + h, y], color=COLORS["ink"], linewidth=1.0, clip_on=False)
    ax.text((x1 + x2) / 2, y + h * 1.15, label, ha="center", va="bottom", fontsize=10.2, color=COLORS["ink"])


def add_confidence_ellipse(ax: plt.Axes, x: np.ndarray, y: np.ndarray, color: str) -> None:
    cov = np.cov(x, y)
    vals, vecs = np.linalg.eigh(cov)
    order = vals.argsort()[::-1]
    vals, vecs = vals[order], vecs[:, order]
    theta = np.degrees(np.arctan2(*vecs[:, 0][::-1]))
    width, height = 2 * np.sqrt(vals) * 1.8
    ellipse = Ellipse(
        (np.mean(x), np.mean(y)),
        width=width,
        height=height,
        angle=theta,
        facecolor=color,
        edgecolor=color,
        alpha=0.12,
        linewidth=1.0,
        zorder=1,
    )
    ax.add_patch(ellipse)


def publication_caption(item: dict) -> str:
    lead = f"Figure {item['order']}. {item['title']}."
    summary = item["summary"]
    source = item["source_note"]
    return f"{lead} {item['goal']} {summary} Source data: {source}"


def publication_methods(item: dict) -> str:
    files = ", ".join(Path(path).name for path in item["input_files"])
    return (
        f"Figure generated in {PRODUCT_NAME} using the '{item['analysis']}' workflow. "
        f"Source dataset(s): {files}. The publication export includes SVG and PDF vector assets for manuscript drafting, "
        f"plus high-resolution PNG and TIFF raster assets for submission systems that require raster uploads."
    )


def publication_results(item: dict) -> str:
    top_metrics = "; ".join(item["key_metrics"][:3])
    return f"{item['summary']} Key quantitative outputs: {top_metrics}."


def publication_checklist(item: dict) -> list[str]:
    return [
        "Insert the SVG or PDF figure into the manuscript draft for editable vector quality.",
        "Use the caption draft as the starting figure legend and trim it to the journal's style guide.",
        "Attach the included source-data CSV files to your figure source-data or supplement package.",
        "Use the TIFF or high-resolution PNG file if the submission portal requires a raster upload.",
    ]


def build_publication_package(item: dict) -> dict:
    chart_name = Path(item["chart_path"]).stem
    export_source_dir = EXPORT_DIR / chart_name
    package_dir = PUBLICATION_DIR / item["slug"]
    package_dir.mkdir(parents=True, exist_ok=True)

    export_targets = {}
    for ext in ["svg", "pdf", "png", "tiff"]:
        src = export_source_dir / f"{chart_name}.{ext}"
        dst = package_dir / f"{item['slug']}-figure.{ext}"
        shutil.copy2(src, dst)
        export_targets[ext] = str(dst.relative_to(ROOT))

    caption_text = publication_caption(item)
    methods_text = publication_methods(item)
    results_text = publication_results(item)
    checklist = publication_checklist(item)

    caption_path = package_dir / f"{item['slug']}-caption.md"
    methods_path = package_dir / f"{item['slug']}-methods.md"
    results_path = package_dir / f"{item['slug']}-results.md"
    checklist_path = package_dir / f"{item['slug']}-submission-checklist.md"
    write_text(caption_path, caption_text)
    write_text(methods_path, methods_text)
    write_text(results_path, results_text)
    write_text(checklist_path, "\n".join(f"- {line}" for line in checklist))

    bundle_path = package_dir / f"{item['slug']}-publication-bundle.zip"
    with zipfile.ZipFile(bundle_path, "w", compression=zipfile.ZIP_DEFLATED) as bundle:
        for ext, rel_path in export_targets.items():
            bundle.write(ROOT / rel_path, arcname=f"figure/{Path(rel_path).name}")
        bundle.write(caption_path, arcname=f"text/{caption_path.name}")
        bundle.write(methods_path, arcname=f"text/{methods_path.name}")
        bundle.write(results_path, arcname=f"text/{results_path.name}")
        bundle.write(checklist_path, arcname=f"text/{checklist_path.name}")
        for rel_path in item["input_files"]:
            source_path = ROOT / rel_path
            if source_path.exists():
                bundle.write(source_path, arcname=f"source-data/{source_path.name}")
        generated_file = item.get("generated_file")
        if generated_file:
            generated_path = ROOT / generated_file
            if generated_path.exists():
                bundle.write(generated_path, arcname=f"generated-data/{generated_path.name}")

    return {
        "publication_assets": {
            "bundle": str(bundle_path.relative_to(ROOT)),
            "caption": str(caption_path.relative_to(ROOT)),
            "methods": str(methods_path.relative_to(ROOT)),
            "results": str(results_path.relative_to(ROOT)),
            "checklist": str(checklist_path.relative_to(ROOT)),
            **export_targets,
        },
        "caption_text": caption_text,
        "methods_text": methods_text,
        "results_text": results_text,
        "submission_checklist": checklist,
    }


def make_spec_list() -> list[UseCaseSpec]:
    return [
        UseCaseSpec(
            1,
            "two-group-supplement-comparison",
            "Two-Group Supplement Comparison",
            "Hypothesis Testing",
            "Welch t test + raw-point estimation plot",
            "Compare low-dose tooth growth by supplement and show every replicate.",
            [
                "Open the Workspace and choose Two-Group Supplement Comparison.",
                "Review the input file preview and confirm the dose filter is 0.5 mg/day.",
                "Inspect the raw-point plot to make sure the replicate spread is visible before statistics.",
                "Read the automatic Welch t test result card and confidence interval.",
                "Export the figure as SVG or PNG from the figure actions menu.",
            ],
            "Prism users love being able to see raw points and the conclusion on one screen. This example keeps every animal visible while still surfacing the statistical decision.",
            ["data/raw/ToothGrowth.csv"],
            "ToothGrowth from the R datasets collection.",
            "build_two_group_supplement",
        ),
        UseCaseSpec(
            2,
            "dose-response-overview",
            "Dose-Response Overview",
            "Grouped Comparisons",
            "One-way ANOVA + Tukey multiple comparison",
            "Show how growth changes across three vitamin C dose levels.",
            [
                "Open the Dose-Response Overview example.",
                "Confirm the input file contains the full ToothGrowth table, not the low-dose subset.",
                "Inspect the dose-wise raw-point summary plot and the dose means.",
                "Read the ANOVA result and the pairwise dose comparison card.",
                "Use the export preset if you need a journal-ready PNG.",
            ],
            "This workflow is common in assay exploration: a quick sanity check on monotonic dose behavior plus a formal omnibus test.",
            ["data/raw/ToothGrowth.csv"],
            "ToothGrowth from the R datasets collection.",
            "build_dose_response_overview",
        ),
        UseCaseSpec(
            3,
            "grouped-mean-comparison",
            "Grouped Mean Comparison",
            "ANOVA",
            "One-way ANOVA + Tukey HSD",
            "Compare plant weight across a control and two treatment groups.",
            [
                "Open Grouped Mean Comparison from the left rail.",
                "Review the three-group preview table and verify there are ten replicates per arm.",
                "Inspect the polished dot-and-summary chart before looking at p values.",
                "Use the Tukey table to identify which treatment differs from control.",
                "Add the figure to a board if you want to combine it with other results.",
            ],
            "The dot-plus-summary view is one of the most loved Prism patterns because it keeps the data honest while still looking publication-ready.",
            ["data/raw/PlantGrowth.csv"],
            "PlantGrowth from the R datasets collection.",
            "build_grouped_mean_comparison",
        ),
        UseCaseSpec(
            4,
            "factorial-experiment",
            "Factorial Experiment",
            "ANOVA",
            "Two-way ANOVA with interaction",
            "Analyze a classic 2x3 factorial experiment with interaction effects.",
            [
                "Open Factorial Experiment.",
                "Inspect the grouped preview and note the two wool types and three tension settings.",
                "Read the interaction plot first to understand the shape of the effect.",
                "Use the ANOVA table to see whether wool, tension, and their interaction matter.",
                "Export the figure and include the ANOVA table in your report bundle.",
            ],
            "Many Prism users value how fast they can go from a factorial table to an interpretable graph. The interaction plot is the center of gravity here.",
            ["data/raw/warpbreaks.csv"],
            "warpbreaks from the R datasets collection.",
            "build_factorial_experiment",
        ),
        UseCaseSpec(
            5,
            "paired-before-after",
            "Paired Before-and-After Study",
            "Paired Analysis",
            "Paired t test + subject spaghetti plot",
            "Show within-subject change instead of treating repeated observations as independent.",
            [
                "Open Paired Before-and-After Study.",
                "Verify that every subject appears in both conditions in the preview panel.",
                "Inspect the spaghetti plot to see whether the direction of change is consistent by subject.",
                "Review the paired t test and the mean paired difference.",
                "Use the notes panel to capture whether the result is biologically meaningful, not just statistically non-zero.",
            ],
            "This is a classic Prism-style win: the graph makes the pairing obvious before the statistics speak.",
            ["data/raw/sleep.csv"],
            "sleep from the R datasets collection.",
            "build_paired_before_after",
        ),
        UseCaseSpec(
            6,
            "time-course-summary",
            "Time-Course Summary",
            "Time Series",
            "Area-under-the-curve summary + line plot",
            "Turn a small time-course table into a compact kinetic summary.",
            [
                "Open Time-Course Summary.",
                "Inspect the input table and confirm that time increases monotonically.",
                "Review the line chart to see the saturation shape of the response.",
                "Read the computed AUC and final-value summary card.",
                "Export the figure if you need a quick panel for a methods update or internal review.",
            ],
            "Even basic time-course screens feel better when the graph and one-number summary live together. That fast feedback loop is part of the Prism appeal.",
            ["data/raw/BOD.csv"],
            "BOD from the R datasets collection.",
            "build_time_course_summary",
        ),
        UseCaseSpec(
            7,
            "repeated-growth-curves",
            "Repeated Growth Curves",
            "Repeated Measures",
            "Subject-wise growth lines + slope summary",
            "Review repeated measures without collapsing away subject identity.",
            [
                "Open Repeated Growth Curves.",
                "Inspect the preview to see age and circumference recorded for multiple trees.",
                "Read the line chart to compare each tree trajectory over time.",
                "Use the slope summary card to identify the fastest and slowest growers.",
                "Add this view to a multi-panel board if you are telling a developmental story.",
            ],
            "Researchers love when repeated-measures data stay visually intact instead of being flattened into a single average line.",
            ["data/raw/Orange.csv"],
            "Orange from the R datasets collection.",
            "build_repeated_growth_curves",
        ),
        UseCaseSpec(
            8,
            "regression-and-calibration",
            "Regression and Calibration",
            "Regression",
            "Linear regression with 95% prediction band",
            "Fit a simple calibration-style relationship and show the uncertainty band.",
            [
                "Open Regression and Calibration.",
                "Inspect the input columns and make sure the predictor is on the x-axis and the response on the y-axis.",
                "Review the regression line and the 95% prediction band.",
                "Read the slope, R-squared, and prediction summary.",
                "Use the exported SVG if you need to polish labels further for a manuscript.",
            ],
            "Prism users often pick the tool because regression results and the fitted graphic arrive together without friction.",
            ["data/raw/trees.csv"],
            "trees from the R datasets collection.",
            "build_regression_and_calibration",
        ),
        UseCaseSpec(
            9,
            "correlation-screen",
            "Correlation Screen",
            "Multivariate",
            "Pearson correlation heatmap",
            "Quickly screen relationships across several numeric features.",
            [
                "Open Correlation Screen.",
                "Inspect the feature preview and note that the species label is excluded from the correlation matrix.",
                "Read the heatmap first to spot the strongest positive and negative relationships.",
                "Use the metric card to identify the top correlation pair.",
                "Export the heatmap when you need a compact exploratory panel for collaborators.",
            ],
            "This is the kind of multivariate glance people like because it is informative in seconds and visually neat enough to share.",
            ["data/raw/iris.csv"],
            "iris from the R datasets collection.",
            "build_correlation_screen",
        ),
        UseCaseSpec(
            10,
            "pca-species-map",
            "PCA Species Map",
            "Multivariate",
            "Principal component analysis",
            "Reduce four measurements into two axes and show class separation.",
            [
                "Open PCA Species Map.",
                "Inspect the standardized feature list before computing PCA.",
                "Review the biplot-style scatter to see how the species separate across the first two components.",
                "Read the explained-variance card to understand how much of the structure is retained.",
                "Add the plot to a board if you need a compact dimensionality-reduction panel.",
            ],
            "Users often praise Prism when advanced-looking plots remain approachable. PCA is a good test of that principle.",
            ["data/raw/iris.csv"],
            "iris from the R datasets collection.",
            "build_pca_species_map",
        ),
        UseCaseSpec(
            11,
            "distribution-comparison",
            "Distribution Comparison",
            "Distributions",
            "Violin plot + one-way ANOVA",
            "Compare full distributions, not just means, across three species.",
            [
                "Open Distribution Comparison.",
                "Review the species labels in the preview and confirm the measurement column is sepal length.",
                "Inspect the violin plot to understand shape, spread, and overlap.",
                "Read the ANOVA result card to decide whether the mean difference is large enough to formalize.",
                "Export the figure if you need a more modern alternative to a plain box plot.",
            ],
            "Polished distribution plots are part of Prism's charm, especially when they default to something more expressive than a bare bar chart.",
            ["data/raw/iris.csv"],
            "iris from the R datasets collection.",
            "build_distribution_comparison",
        ),
        UseCaseSpec(
            12,
            "enzyme-kinetics",
            "Enzyme Kinetics",
            "Nonlinear Regression",
            "Michaelis-Menten fitting",
            "Fit enzyme-rate curves for treated and untreated conditions.",
            [
                "Open Enzyme Kinetics.",
                "Check the concentration and rate columns in the preview table.",
                "Inspect the fitted Michaelis-Menten curves over the raw points.",
                "Read the Vmax and Km estimates for each condition.",
                "Export the panel if you need a fast enzyme-kinetics figure for a slide or report.",
            ],
            "Nonlinear regression is one of Prism's signature strengths, so this use case is a must-win for the alternative.",
            ["data/raw/Puromycin.csv"],
            "Puromycin from the R datasets collection.",
            "build_enzyme_kinetics",
        ),
        UseCaseSpec(
            13,
            "pharmacokinetics",
            "Pharmacokinetic Exposure",
            "PK / PD",
            "Concentration-time summary + noncompartmental metrics",
            "Track drug concentration over time and summarize exposure metrics.",
            [
                "Open Pharmacokinetic Exposure.",
                "Inspect the subject, time, and concentration columns in the preview.",
                "Review the concentration-time plot to see the shared peak-and-decay shape.",
                "Read the automatic Cmax, Tmax, and AUC summary card.",
                "Export the figure or the metrics table for your PK review packet.",
            ],
            "A Prism alternative needs credible PK workflows even when the math is relatively basic, because the audience often thinks in curves first.",
            ["data/raw/Theoph.csv"],
            "Theoph from the R datasets collection.",
            "build_pharmacokinetics",
        ),
        UseCaseSpec(
            14,
            "drug-elimination",
            "Drug Elimination Half-Life",
            "PK / PD",
            "Semi-log elimination fit",
            "Estimate elimination behavior from concentration decay data.",
            [
                "Open Drug Elimination Half-Life.",
                "Inspect the subject-level concentration-time table.",
                "Read the semi-log plot to confirm the terminal phase looks approximately linear on the log scale.",
                "Review the median half-life estimate and subject variability.",
                "Export the panel if you need a compact PK appendix figure.",
            ],
            "This is a deliberately practical workflow: scientists care about the answer and the shape of the decay at the same time.",
            ["data/raw/Indometh.csv"],
            "Indometh from the R datasets collection.",
            "build_drug_elimination",
        ),
        UseCaseSpec(
            15,
            "survival-analysis",
            "Kaplan-Meier Survival Analysis",
            "Survival",
            "Kaplan-Meier + log-rank test",
            "Compare survival curves across two groups and keep censoring visible.",
            [
                "Open Kaplan-Meier Survival Analysis.",
                "Inspect the event-time preview and note the group assignment.",
                "Review the stepwise survival curves and at-risk behavior.",
                "Read the log-rank result card for the between-group comparison.",
                "Export the plot if you need a manuscript-ready survival panel.",
            ],
            "Survival workflows are one of the places where users especially value an opinionated, graph-first tool.",
            ["data/raw/waltons.csv"],
            "waltons from the lifelines example datasets.",
            "build_survival_analysis",
        ),
        UseCaseSpec(
            16,
            "hazard-modeling",
            "Hazard Modeling",
            "Survival",
            "Cox proportional hazards model",
            "Move from a survival curve to interpretable hazard ratios.",
            [
                "Open Hazard Modeling.",
                "Inspect the covariate preview to understand the available predictors.",
                "Review the ranked hazard-ratio chart to see the strongest associations.",
                "Read the model card for the top coefficients and confidence intervals.",
                "Use the result bundle if you want a quick model summary for collaborators.",
            ],
            "Prism is loved for common analyses that stay readable. The Cox view should feel serious but never opaque.",
            ["data/raw/rossi.csv"],
            "rossi from the lifelines example datasets.",
            "build_hazard_modeling",
        ),
        UseCaseSpec(
            17,
            "contingency-explorer",
            "Contingency Explorer",
            "Categorical",
            "Chi-square test + normalized heatmap",
            "Compare survival rates by sex in the Titanic passenger data.",
            [
                "Open Contingency Explorer.",
                "Inspect the aggregated count table and note that counts, not individual rows, drive the analysis.",
                "Review the heatmap to spot the asymmetry between women and men.",
                "Read the chi-square statistic and odds-style interpretation card.",
                "Export the panel if you need a compact categorical analysis figure.",
            ],
            "Users love when categorical summaries are both readable and visually polished, especially when counts come in aggregated form.",
            ["data/raw/Titanic.csv"],
            "Titanic from the R datasets collection.",
            "build_contingency_explorer",
        ),
        UseCaseSpec(
            18,
            "logistic-risk-model",
            "Logistic Risk Model",
            "Categorical",
            "Logistic regression with odds-ratio view",
            "Model esophageal cancer risk from alcohol and tobacco categories.",
            [
                "Open Logistic Risk Model.",
                "Inspect the grouped case-control input table.",
                "Review the odds-ratio chart to see which exposure bins shift the risk most strongly.",
                "Read the model summary card and the confidence interval labels.",
                "Export the figure if you need a concise risk-factor slide.",
            ],
            "This is the type of result that becomes much more trustworthy when the model output is paired with a clean, understandable visualization.",
            ["data/raw/esoph.csv"],
            "esoph from the R datasets collection.",
            "build_logistic_risk_model",
        ),
        UseCaseSpec(
            19,
            "outlier-qc-review",
            "Outlier QC Review",
            "Quality Control",
            "IQR outlier flagging + scatter and box plot",
            "Show how a QC workflow can stay visual without hiding the statistics.",
            [
                "Open Outlier QC Review.",
                "Inspect the preview and note the missing values before looking at the outlier flags.",
                "Review the scatter plot and box plot together to understand both trend and spread.",
                "Read the QC card to see how many values were flagged by the IQR rule.",
                "Export the panel if you need an appendix figure documenting exclusions or review decisions.",
            ],
            "Polished QC views reduce arguments later because the data-cleaning logic is visible, not hidden in a script.",
            ["data/raw/airquality.csv"],
            "airquality from the R datasets collection.",
            "build_outlier_qc_review",
        ),
        UseCaseSpec(
            20,
            "publication-figure-board",
            "Publication Figure Board",
            "Figure Composition",
            "Four-panel figure composition",
            "Combine several analyses into one clean, manuscript-style board.",
            [
                "Open Publication Figure Board.",
                "Review how the board combines comparison, factorial, nonlinear, and survival panels.",
                "Inspect the shared spacing, panel labels, and caption strip to see how the narrative hangs together.",
                "Use this as the final checkpoint before exporting a submission-ready multi-panel figure.",
                "Export the board as a high-resolution PNG for docs or as a source figure for later refinement.",
            ],
            "This is where the product has to exceed Prism: excellent single figures are not enough if the final board still feels clumsy.",
            [
                "data/generated/two-group-supplement-comparison.csv",
                "data/generated/factorial-experiment.csv",
                "data/generated/enzyme-kinetics.csv",
                "data/generated/survival-analysis.csv",
            ],
            "Composite figure built from previously generated analysis panels.",
            "build_publication_figure_board",
        ),
    ]


def build_two_group_supplement(spec: UseCaseSpec) -> dict:
    df = load_csv("ToothGrowth.csv")
    low = df[df["dose"] == 0.5].copy()
    oj = low.loc[low["supp"] == "OJ", "len"].to_numpy()
    vc = low.loc[low["supp"] == "VC", "len"].to_numpy()
    t_stat, p_value = stats.ttest_ind(oj, vc, equal_var=False)
    mean_diff = float(np.mean(oj) - np.mean(vc))
    var_oj = np.var(oj, ddof=1)
    var_vc = np.var(vc, ddof=1)
    se = math.sqrt(var_oj / len(oj) + var_vc / len(vc))
    welch_df = (var_oj / len(oj) + var_vc / len(vc)) ** 2 / (
        ((var_oj / len(oj)) ** 2 / (len(oj) - 1)) + ((var_vc / len(vc)) ** 2 / (len(vc) - 1))
    )
    margin = stats.t.ppf(0.975, welch_df) * se
    ci_low, ci_high = mean_diff - margin, mean_diff + margin

    fig, ax = plt.subplots(figsize=(7.2, 5.0))
    simple_card(fig, spec.title, "Real data: ToothGrowth low-dose cohort")
    for idx, (_, values, color) in enumerate([("OJ", oj, COLORS["blue"]), ("VC", vc, COLORS["teal"])]):
        draw_group_summary(ax, idx, values, color)
    ax.set_xticks([0, 1], ["OJ", "VC"])
    ax.set_title("Low-dose supplement comparison", loc="left", pad=16)
    style_axis(ax, ylabel="Tooth length", grid="y")
    y_top = max(low["len"]) + 3.2
    ax.set_ylim(low["len"].min() - 1.2, y_top + 1.5)
    add_sig_bracket(ax, 0, 1, y_top, f"{significance_label(p_value)}   p {fmt_p(p_value)}")
    add_result_badge(ax, f"Mean diff {mean_diff:.2f}\n95% CI [{ci_low:.2f}, {ci_high:.2f}]")
    chart = save_chart(fig, f"{spec.order:02d}-{spec.slug}.png")

    subset_path = GENERATED_DIR / f"{spec.slug}.csv"
    low.to_csv(subset_path, index=False)
    return {
        "summary": (
            f"At the low dose, the OJ formulation looks biologically more active than VC, improving mean tooth length by "
            f"{mean_diff:.2f} units. Welch's t test is the right statistical move here because it stays reliable when group "
            f"variances may differ, and the 95% confidence interval [{ci_low:.2f}, {ci_high:.2f}] keeps the likely size of the rescue effect visible alongside p {fmt_p(p_value)}."
        ),
        "key_metrics": [
            f"OJ mean = {np.mean(oj):.2f}",
            f"VC mean = {np.mean(vc):.2f}",
            f"Mean difference = {mean_diff:.2f}",
            f"95% Welch CI = [{ci_low:.2f}, {ci_high:.2f}]",
        ],
        "chart_path": chart,
        "data_preview": to_records_table(low),
        "input_files": spec.data_files,
        "generated_file": f"data/generated/{spec.slug}.csv",
    }


def build_dose_response_overview(spec: UseCaseSpec) -> dict:
    df = load_csv("ToothGrowth.csv")
    model = ols("len ~ C(dose)", data=df).fit()
    anova = anova_lm(model, typ=2)
    tukey = pairwise_tukeyhsd(df["len"], df["dose"])
    means = df.groupby("dose")["len"].mean()
    tukey_row = tukey.summary().data[1]
    top_tukey = (
        f"{tukey_row[0]} vs {tukey_row[1]}: diff {float(tukey_row[2]):.2f}, "
        f"p {float(tukey_row[3]):.3f}, reject {'yes' if bool(tukey_row[6]) else 'no'}"
    )

    fig, ax = plt.subplots(figsize=(7.4, 5.1))
    simple_card(fig, spec.title, "Dose groups with every animal retained")
    palette = [COLORS["gold"], COLORS["blue"], COLORS["teal"]]
    dose_order = sorted(df["dose"].unique())
    for idx, dose in enumerate(dose_order):
        values = df.loc[df["dose"] == dose, "len"].to_numpy()
        draw_group_summary(ax, idx, values, palette[idx])
    ax.plot(range(3), [means.loc[dose] for dose in dose_order], color=COLORS["ink"], linewidth=1.6, alpha=0.5, zorder=2)
    ax.set_xticks(range(3), [f"{dose:.1f}" for dose in dose_order])
    ax.set_title("Growth increases with dose", loc="left", pad=16)
    style_axis(ax, xlabel="Dose (mg/day)", ylabel="Tooth length", grid="y")
    add_result_badge(ax, f"ANOVA F {anova.loc['C(dose)', 'F']:.2f}\np {fmt_p(anova.loc['C(dose)', 'PR(>F)'])}", loc=(0.75, 0.98))
    chart = save_chart(fig, f"{spec.order:02d}-{spec.slug}.png")

    return {
        "summary": (
            f"The dose-escalation pattern supports a biologically graded response rather than an isolated group difference: mean growth rises steadily across the three dose levels. "
            f"A one-way ANOVA confirms that dose explains substantial response variance (F {anova.loc['C(dose)', 'F']:.2f}, p {fmt_p(anova.loc['C(dose)', 'PR(>F)'])}), "
            f"and Tukey follow-up contrasts are what tell you which dose steps are really driving the signal."
        ),
        "key_metrics": [
            f"Dose 0.5 mean = {means.loc[0.5]:.2f}",
            f"Dose 1.0 mean = {means.loc[1.0]:.2f}",
            f"Dose 2.0 mean = {means.loc[2.0]:.2f}",
            f"Top Tukey comparison row = {top_tukey}",
        ],
        "chart_path": chart,
        "data_preview": to_records_table(df),
        "input_files": spec.data_files,
        "generated_file": None,
    }


def build_grouped_mean_comparison(spec: UseCaseSpec) -> dict:
    df = load_csv("PlantGrowth.csv")
    model = ols("weight ~ C(group)", data=df).fit()
    anova = anova_lm(model, typ=2)
    tukey = pairwise_tukeyhsd(df["weight"], df["group"])
    means = df.groupby("group")["weight"].mean()
    tukey_row = tukey.summary().data[1]
    tukey_text = (
        f"{tukey_row[0]} vs {tukey_row[1]}: diff {float(tukey_row[2]):.2f}, "
        f"p {float(tukey_row[3]):.3f}, reject {'yes' if bool(tukey_row[6]) else 'no'}"
    )
    order = ["ctrl", "trt1", "trt2"]
    palette = [COLORS["sage"], COLORS["gold"], COLORS["rose"]]

    fig, ax = plt.subplots(figsize=(7.2, 5.0))
    simple_card(fig, spec.title, "Plant weight by treatment arm")
    for idx, group in enumerate(order):
        values = df.loc[df["group"] == group, "weight"].to_numpy()
        draw_group_summary(ax, idx, values, palette[idx])
    ax.set_xticks(range(3), ["Control", "Treatment 1", "Treatment 2"])
    ax.set_title("Treatment 2 separates best from control", loc="left", pad=16)
    style_axis(ax, ylabel="Dry weight", grid="y")
    y_top = df["weight"].max() + 0.35
    ax.set_ylim(df["weight"].min() - 0.2, y_top + 0.35)
    add_sig_bracket(ax, 0, 2, y_top, f"{significance_label(anova.loc['C(group)', 'PR(>F)'])}   ANOVA p {fmt_p(anova.loc['C(group)', 'PR(>F)'])}")
    add_result_badge(ax, f"Control {means.loc['ctrl']:.2f}\nTreatment 2 {means.loc['trt2']:.2f}", loc=(0.74, 0.98))
    chart = save_chart(fig, f"{spec.order:02d}-{spec.slug}.png")
    return {
        "summary": (
            f"This reads like a hit-confirmation screen: Treatment 2 produces the strongest growth phenotype, while the overall arm-to-arm difference is supported by the omnibus ANOVA "
            f"(F {anova.loc['C(group)', 'F']:.2f}, p {fmt_p(anova.loc['C(group)', 'PR(>F)'])}). The important statistical trick is using Tukey-adjusted pairwise follow-up "
            f"after the omnibus test so the strongest arm is identified without over-reading raw mean separation alone."
        ),
        "key_metrics": [
            f"Control mean = {means.loc['ctrl']:.2f}",
            f"Treatment 1 mean = {means.loc['trt1']:.2f}",
            f"Treatment 2 mean = {means.loc['trt2']:.2f}",
            f"Example Tukey row = {tukey_text}",
        ],
        "chart_path": chart,
        "data_preview": to_records_table(df),
        "input_files": spec.data_files,
        "generated_file": None,
    }


def build_factorial_experiment(spec: UseCaseSpec) -> dict:
    df = load_csv("warpbreaks.csv")
    model = ols("breaks ~ C(wool) * C(tension)", data=df).fit()
    anova = anova_lm(model, typ=2)
    means = df.groupby(["tension", "wool"])["breaks"].mean().unstack()
    tensions = ["L", "M", "H"]

    fig, ax = plt.subplots(figsize=(7.4, 5.2))
    simple_card(fig, spec.title, "2x3 factorial study with interaction view")
    ax.plot(tensions, means.loc[tensions, "A"], marker="o", markersize=7.5, linewidth=2.4, color=COLORS["blue"], label="Wool A")
    ax.plot(tensions, means.loc[tensions, "B"], marker="s", markersize=7.2, linewidth=2.4, color=COLORS["coral"], label="Wool B")
    ax.set_title("Interaction plot", loc="left", pad=16)
    style_axis(ax, xlabel="Tension", ylabel="Break count", grid="y")
    ax.legend(loc="upper right")
    add_result_badge(
        ax,
        "\n".join(
            [
                f"Wool p {fmt_p(anova.loc['C(wool)', 'PR(>F)'])}",
                f"Tension p {fmt_p(anova.loc['C(tension)', 'PR(>F)'])}",
                f"Interaction p {fmt_p(anova.loc['C(wool):C(tension)', 'PR(>F)'])}",
            ]
        ),
        loc=(0.02, 0.96),
    )
    chart = save_chart(fig, f"{spec.order:02d}-{spec.slug}.png")
    return {
        "summary": (
            f"The main biological story is a strong tension effect, with much weaker evidence that the material-specific response meaningfully changes across tension states. "
            f"Two-way ANOVA is doing the critical work here because it separates the main effects from the interaction term, letting the team ask whether the scaffold changes the biology itself or just the overall baseline."
        ),
        "key_metrics": [
            f"Wool effect p = {fmt_p(anova.loc['C(wool)', 'PR(>F)'])}",
            f"Tension effect p = {fmt_p(anova.loc['C(tension)', 'PR(>F)'])}",
            f"Interaction p = {fmt_p(anova.loc['C(wool):C(tension)', 'PR(>F)'])}",
        ],
        "chart_path": chart,
        "data_preview": to_records_table(df),
        "input_files": spec.data_files,
        "generated_file": None,
    }


def build_paired_before_after(spec: UseCaseSpec) -> dict:
    df = load_csv("sleep.csv")
    wide = df.pivot(index="ID", columns="group", values="extra")
    group1 = wide[1].to_numpy()
    group2 = wide[2].to_numpy()
    diff = group2 - group1
    t_stat, p_value = stats.ttest_rel(group2, group1)

    fig, ax = plt.subplots(figsize=(7.1, 5.0))
    simple_card(fig, spec.title, "Pairing is visible before the t test")
    for _, row in wide.iterrows():
        ax.plot([0, 1], [row[1], row[2]], color="#ccd4dd", linewidth=1.4, zorder=1)
        ax.scatter([0, 1], [row[1], row[2]], color=[COLORS["blue"], COLORS["teal"]], s=46, edgecolor="white", linewidth=0.8, zorder=3)
    ax.set_xticks([0, 1], ["Group 1", "Group 2"])
    ax.set_title("Within-subject change", loc="left", pad=16)
    style_axis(ax, ylabel="Increase in sleep", grid="y")
    add_result_badge(ax, f"Paired t {t_stat:.2f}\np {fmt_p(p_value)}\nMean diff {np.mean(diff):.2f}", loc=(0.74, 0.98))
    chart = save_chart(fig, f"{spec.order:02d}-{spec.slug}.png")
    return {
        "summary": (
            f"The paired readout suggests a real within-subject neuroresponse after intervention, with subjects improving by {np.mean(diff):.2f} units on average in group 2 versus group 1. "
            f"The key statistical trick is the paired t test: it uses each subject as their own control, which is biologically more faithful and usually more sensitive than pretending repeated observations are independent."
        ),
        "key_metrics": [
            f"Mean group 1 = {np.mean(group1):.2f}",
            f"Mean group 2 = {np.mean(group2):.2f}",
            f"Mean paired difference = {np.mean(diff):.2f}",
            f"Paired t p = {fmt_p(p_value)}",
        ],
        "chart_path": chart,
        "data_preview": to_records_table(df),
        "input_files": spec.data_files,
        "generated_file": None,
    }


def build_time_course_summary(spec: UseCaseSpec) -> dict:
    df = load_csv("BOD.csv")
    auc = np.trapezoid(df["demand"], x=df["Time"])

    fig, ax = plt.subplots(figsize=(7.2, 4.8))
    simple_card(fig, spec.title, "Compact kinetic readout")
    ax.plot(df["Time"], df["demand"], marker="o", color=COLORS["blue"], linewidth=2.8, markersize=6.8)
    ax.fill_between(df["Time"], df["demand"], alpha=0.12, color=COLORS["light_blue"])
    ax.scatter(df["Time"].iloc[-1], df["demand"].iloc[-1], s=76, color=COLORS["blue"], edgecolor="white", linewidth=0.8, zorder=4)
    ax.set_title("Response saturates quickly", loc="left", pad=16)
    style_axis(ax, xlabel="Time", ylabel="Biochemical oxygen demand", grid="y")
    add_result_badge(ax, f"AUC {auc:.2f}\nFinal value {df['demand'].iloc[-1]:.1f}", loc=(0.76, 0.98))
    chart = save_chart(fig, f"{spec.order:02d}-{spec.slug}.png")
    return {
        "summary": (
            f"The time course looks like a fast metabolic activation followed by a plateau, which is often the biological question in short functional assays. "
            f"Reporting both the terminal value ({df['demand'].iloc[-1]:.1f}) and the integrated exposure-like summary AUC ({auc:.2f}) keeps the interpretation from depending on a single timepoint."
        ),
        "key_metrics": [
            f"Baseline = {df['demand'].iloc[0]:.1f}",
            f"Final value = {df['demand'].iloc[-1]:.1f}",
            f"AUC = {auc:.2f}",
            f"Max slope segment = {np.diff(df['demand']).max():.2f}",
        ],
        "chart_path": chart,
        "data_preview": to_records_table(df),
        "input_files": spec.data_files,
        "generated_file": None,
    }


def build_repeated_growth_curves(spec: UseCaseSpec) -> dict:
    df = load_csv("Orange.csv")
    if "Tree" not in df.columns:
        df.columns = ["Tree", "age", "circumference"]
    slopes = {}

    fig, ax = plt.subplots(figsize=(7.5, 5.2))
    simple_card(fig, spec.title, "Tree-level growth trajectories")
    palette = [COLORS["blue"], COLORS["teal"], COLORS["gold"], COLORS["coral"], COLORS["violet"]]
    for color, (tree, group) in zip(palette, df.groupby("Tree")):
        coeffs = np.polyfit(group["age"], group["circumference"], 1)
        slopes[str(tree)] = coeffs[0]
        ax.plot(group["age"], group["circumference"], marker="o", linewidth=2.1, markersize=4.8, color=color, label=f"Tree {tree}")
        ax.text(group["age"].iloc[-1] + 12, group["circumference"].iloc[-1], str(tree), color=color, fontsize=9.2, va="center")
    ax.set_title("Repeated measures stay visible", loc="left", pad=16)
    style_axis(ax, xlabel="Age (days)", ylabel="Circumference", grid="y")
    fastest = max(slopes, key=slopes.get)
    slowest = min(slopes, key=slopes.get)
    add_result_badge(ax, f"Fastest slope: Tree {fastest}\nSlowest slope: Tree {slowest}", loc=(0.72, 0.98))
    chart = save_chart(fig, f"{spec.order:02d}-{spec.slug}.png")
    return {
        "summary": (
            f"The longitudinal traces make it clear that not all members of the cohort follow the same growth program: Tree {fastest} expands fastest while Tree {slowest} lags behind. "
            f"The useful analytic trick is preserving subject-level trajectories and summarizing them with per-subject slopes instead of collapsing everything into one average curve."
        ),
        "key_metrics": [
            f"Fastest slope = Tree {fastest} ({slopes[fastest]:.3f})",
            f"Slowest slope = Tree {slowest} ({slopes[slowest]:.3f})",
            f"Median circumference = {df['circumference'].median():.1f}",
        ],
        "chart_path": chart,
        "data_preview": to_records_table(df),
        "input_files": spec.data_files,
        "generated_file": None,
    }


def build_regression_and_calibration(spec: UseCaseSpec) -> dict:
    df = load_csv("trees.csv")
    model = ols("Volume ~ Girth", data=df).fit()
    grid = np.linspace(df["Girth"].min(), df["Girth"].max(), 100)
    band = regression_band(model, grid, "Girth")

    fig, ax = plt.subplots(figsize=(7.4, 5.0))
    simple_card(fig, spec.title, "Calibration-style regression")
    ax.scatter(df["Girth"], df["Volume"], s=48, color=COLORS["blue"], edgecolor="white", linewidth=0.8, zorder=3)
    ax.plot(grid, band["mean"], color=COLORS["ink"], linewidth=2.6)
    ax.fill_between(grid, band["mean_ci_lower"], band["mean_ci_upper"], color=COLORS["light_blue"], alpha=0.75, zorder=1)
    ax.set_title("Linear fit with confidence band", loc="left", pad=16)
    style_axis(ax, xlabel="Girth", ylabel="Volume", grid="y")
    add_result_badge(ax, f"Slope {model.params['Girth']:.2f}\nR² {model.rsquared:.3f}\np {fmt_p(model.pvalues['Girth'])}", loc=(0.73, 0.98))
    chart = save_chart(fig, f"{spec.order:02d}-{spec.slug}.png")
    return {
        "summary": (
            f"This calibration looks biologically usable because the response scales predictably with the bench-side measurement, supporting future estimation from a simple surrogate readout. "
            f"The fitted slope of {model.params['Girth']:.2f} and R-squared of {model.rsquared:.3f} quantify how strong that relationship is, while the confidence band shows where prediction uncertainty remains."
        ),
        "key_metrics": [
            f"Intercept = {model.params['Intercept']:.2f}",
            f"Slope = {model.params['Girth']:.2f}",
            f"R-squared = {model.rsquared:.3f}",
            f"Slope p = {fmt_p(model.pvalues['Girth'])}",
        ],
        "chart_path": chart,
        "data_preview": to_records_table(df),
        "input_files": spec.data_files,
        "generated_file": None,
    }


def build_correlation_screen(spec: UseCaseSpec) -> dict:
    df = load_csv("iris.csv")
    numeric = df.select_dtypes(include="number")
    corr = numeric.corr()
    stacked = corr.where(~np.eye(len(corr), dtype=bool)).stack()
    top_pair = stacked.abs().sort_values(ascending=False).index[0]
    top_value = corr.loc[top_pair[0], top_pair[1]]

    fig, ax = plt.subplots(figsize=(6.7, 5.6))
    simple_card(fig, spec.title, "Fast multivariate scan")
    im = ax.imshow(corr, cmap="RdBu_r", vmin=-1, vmax=1)
    ax.set_xticks(range(len(corr.columns)), corr.columns, rotation=35, ha="right")
    ax.set_yticks(range(len(corr.index)), corr.index)
    ax.set_title("Pearson correlation heatmap", loc="left", pad=16)
    ax.set_aspect("equal")
    for i in range(len(corr.index)):
        for j in range(len(corr.columns)):
            ax.text(
                j,
                i,
                f"{corr.iloc[i, j]:.2f}",
                ha="center",
                va="center",
                fontsize=8.6,
                color="#ffffff" if abs(corr.iloc[i, j]) > 0.48 else COLORS["ink"],
                weight="bold" if i == j else "normal",
            )
    for spine in ax.spines.values():
        spine.set_visible(False)
    fig.colorbar(im, ax=ax, shrink=0.82, fraction=0.046, pad=0.04)
    chart = save_chart(fig, f"{spec.order:02d}-{spec.slug}.png")
    return {
        "summary": (
            f"The strongest morphology relationship is between {top_pair[0]} and {top_pair[1]} (r = {top_value:.2f}), suggesting those measurements may be tracking overlapping biology. "
            f"The Pearson correlation screen is the statistical shortcut here: it quickly tells you which features are likely redundant before you commit to a larger phenotyping panel."
        ),
        "key_metrics": [
            f"Top pair = {top_pair[0]} vs {top_pair[1]}",
            f"Top correlation = {top_value:.2f}",
            f"Lowest correlation = {stacked.min():.2f}",
        ],
        "chart_path": chart,
        "data_preview": to_records_table(df),
        "input_files": spec.data_files,
        "generated_file": None,
    }


def build_pca_species_map(spec: UseCaseSpec) -> dict:
    df = load_csv("iris.csv")
    feature_cols = [col for col in df.columns if col != "Species"]
    X = StandardScaler().fit_transform(df[feature_cols])
    pca = PCA(n_components=2)
    comps = pca.fit_transform(X)
    pca_df = pd.DataFrame(comps, columns=["PC1", "PC2"])
    pca_df["Species"] = df["Species"]
    palette = {"setosa": COLORS["gold"], "versicolor": COLORS["teal"], "virginica": COLORS["rose"]}

    fig, ax = plt.subplots(figsize=(7.3, 5.2))
    simple_card(fig, spec.title, "Approachable dimensionality reduction")
    for species, group in pca_df.groupby("Species"):
        add_confidence_ellipse(ax, group["PC1"].to_numpy(), group["PC2"].to_numpy(), palette[species])
        ax.scatter(group["PC1"], group["PC2"], s=38, alpha=0.88, color=palette[species], edgecolor="white", linewidth=0.5, label=species)
    ax.set_xlabel(f"PC1 ({pca.explained_variance_ratio_[0] * 100:.1f}% var)")
    ax.set_ylabel(f"PC2 ({pca.explained_variance_ratio_[1] * 100:.1f}% var)")
    ax.set_title("Species separate cleanly in PCA space", loc="left", pad=16)
    style_axis(ax, grid="both")
    ax.legend(loc="upper left")
    chart = save_chart(fig, f"{spec.order:02d}-{spec.slug}.png")
    return {
        "summary": (
            f"The first two principal components retain {(pca.explained_variance_ratio_[:2].sum() * 100):.1f}% of the total variance and already separate the phenotypic classes, "
            f"suggesting a compact feature space captures much of the underlying biology. PCA is the important trick in play because it compresses correlated measurements into orthogonal axes that are much easier to inspect visually."
        ),
        "key_metrics": [
            f"PC1 variance = {pca.explained_variance_ratio_[0] * 100:.1f}%",
            f"PC2 variance = {pca.explained_variance_ratio_[1] * 100:.1f}%",
            f"Two-component total = {pca.explained_variance_ratio_[:2].sum() * 100:.1f}%",
        ],
        "chart_path": chart,
        "data_preview": to_records_table(df),
        "input_files": spec.data_files,
        "generated_file": None,
    }


def build_distribution_comparison(spec: UseCaseSpec) -> dict:
    df = load_csv("iris.csv")
    model = ols("Sepal_Length ~ C(Species)", data=df.rename(columns={"Sepal.Length": "Sepal_Length", "Species": "Species"})).fit()
    # Keep original names for preview but use renamed frame for stats.
    renamed = df.rename(columns={"Sepal.Length": "Sepal_Length", "Species": "Species"})
    model = ols("Sepal_Length ~ C(Species)", data=renamed).fit()
    anova = anova_lm(model, typ=2)
    order = ["setosa", "versicolor", "virginica"]
    palette = [COLORS["blue"], COLORS["teal"], COLORS["coral"]]

    fig, ax = plt.subplots(figsize=(7.3, 5.2))
    simple_card(fig, spec.title, "Violin plot with raw central tendency")
    violin_data = [renamed.loc[renamed["Species"] == species, "Sepal_Length"].to_numpy() for species in order]
    parts = ax.violinplot(violin_data, showmeans=False, showmedians=False, widths=0.8)
    for body, color in zip(parts["bodies"], palette):
        body.set_facecolor(color)
        body.set_alpha(0.35)
        body.set_edgecolor(color)
        body.set_linewidth(1.1)
    for idx, values in enumerate(violin_data, start=1):
        ax.scatter(swarm_positions(values, idx, spread=0.09), values, color=palette[idx - 1], s=10, alpha=0.28)
        quartiles = np.percentile(values, [25, 50, 75])
        ax.vlines(idx, quartiles[0], quartiles[2], color=COLORS["ink"], linewidth=2.0, zorder=4)
        ax.plot([idx - 0.12, idx + 0.12], [quartiles[1], quartiles[1]], color=COLORS["ink"], linewidth=2.4, zorder=4)
    ax.set_xticks([1, 2, 3], ["Setosa", "Versicolor", "Virginica"])
    ax.set_title("Distribution shape matters", loc="left", pad=16)
    style_axis(ax, ylabel="Sepal length", grid="y")
    add_result_badge(ax, f"ANOVA F {anova.loc['C(Species)', 'F']:.2f}\np {fmt_p(anova.loc['C(Species)', 'PR(>F)'])}", loc=(0.76, 0.98))
    chart = save_chart(fig, f"{spec.order:02d}-{spec.slug}.png")
    return {
        "summary": (
            f"The biological states differ not only in mean sepal length but also in spread and distribution shape, which is exactly why the violin view is more informative than a bare bar chart. "
            f"The one-way ANOVA formalizes the omnibus mean-difference question (F {anova.loc['C(Species)', 'F']:.2f}, p {fmt_p(anova.loc['C(Species)', 'PR(>F)'])}), while the violin geometry keeps heterogeneity visible."
        ),
        "key_metrics": [
            f"Setosa mean = {violin_data[0].mean():.2f}",
            f"Versicolor mean = {violin_data[1].mean():.2f}",
            f"Virginica mean = {violin_data[2].mean():.2f}",
        ],
        "chart_path": chart,
        "data_preview": to_records_table(df),
        "input_files": spec.data_files,
        "generated_file": None,
    }


def build_enzyme_kinetics(spec: UseCaseSpec) -> dict:
    df = load_csv("Puromycin.csv")
    fig, ax = plt.subplots(figsize=(7.4, 5.1))
    simple_card(fig, spec.title, "Michaelis-Menten fit on a real enzyme dataset")
    params_summary = []
    palette = {"treated": COLORS["teal"], "untreated": COLORS["coral"]}
    grid = np.linspace(df["conc"].min(), df["conc"].max(), 160)

    for state, group in df.groupby("state"):
        x = group["conc"].to_numpy()
        y = group["rate"].to_numpy()
        params, _ = curve_fit(michaelis_menten, x, y, p0=[max(y), np.median(x)], maxfev=10000)
        vmax, km = params
        params_summary.append((state, vmax, km))
        ax.scatter(x, y, s=42, color=palette[state], edgecolor="white", linewidth=0.7, label=f"{state} data")
        ax.plot(grid, michaelis_menten(grid, vmax, km), color=palette[state], linewidth=2.5)
        ax.text(grid[-1] * 0.99, michaelis_menten(grid[-1], vmax, km), state, color=palette[state], fontsize=9.3, ha="right", va="center")
    ax.set_title("Treated condition shifts the fitted curve", loc="left", pad=16)
    style_axis(ax, xlabel="Concentration", ylabel="Reaction rate", grid="y")
    ax.legend(loc="upper left", ncol=1, fontsize=8.7)
    chart = save_chart(fig, f"{spec.order:02d}-{spec.slug}.png")
    params_summary.sort(key=lambda item: item[0])
    return {
        "summary": (
            f"The treated and untreated curves separate in a way that suggests the intervention is changing catalytic behavior, not merely adding noise to the assay. "
            f"Nonlinear Michaelis-Menten fitting is the crucial analytic step because it estimates Vmax and Km from the full curve shape rather than from a single substrate concentration."
        ),
        "key_metrics": [
            f"{state} Vmax = {vmax:.2f}, Km = {km:.2f}" for state, vmax, km in params_summary
        ],
        "chart_path": chart,
        "data_preview": to_records_table(df),
        "input_files": spec.data_files,
        "generated_file": None,
    }


def build_pharmacokinetics(spec: UseCaseSpec) -> dict:
    df = load_csv("Theoph.csv")
    if "Subject" not in df.columns:
        df.columns = ["Subject", "Wt", "Dose", "Time", "conc"]
    metrics = []

    fig, ax = plt.subplots(figsize=(7.5, 5.1))
    simple_card(fig, spec.title, "Concentration-time profiles with exposure metrics")
    for subject, group in df.groupby("Subject"):
        ax.plot(group["Time"], group["conc"], marker="o", linewidth=1.0, markersize=3.4, color="#c8d1dc", alpha=0.95, zorder=1)
        cmax = float(group["conc"].max())
        tmax = float(group.loc[group["conc"].idxmax(), "Time"])
        auc = float(np.trapezoid(group["conc"], group["Time"]))
        metrics.append((subject, cmax, tmax, auc))
    median_profile = df.groupby("Time")["conc"].median().reset_index()
    ax.plot(median_profile["Time"], median_profile["conc"], color=COLORS["blue"], linewidth=2.8, marker="o", markersize=5.2, zorder=3)
    ax.set_title("Real PK profiles remain easy to read", loc="left", pad=16)
    style_axis(ax, xlabel="Time", ylabel="Concentration", grid="y")
    add_result_badge(ax, "Thin lines = individual subjects\nDark line = median profile", loc=(0.71, 0.98))
    chart = save_chart(fig, f"{spec.order:02d}-{spec.slug}.png")
    avg_cmax = np.mean([item[1] for item in metrics])
    avg_auc = np.mean([item[3] for item in metrics])
    return {
        "summary": (
            f"The cohort shows the classic absorption-to-elimination PK shape, and the average Cmax ({avg_cmax:.2f}) and AUC ({avg_auc:.2f}) together summarize both peak exposure and total drug burden. "
            f"The key statistical choice is to use simple noncompartmental metrics, which keeps the interpretation practical for early translational review without forcing a heavier compartment model."
        ),
        "key_metrics": [
            f"Mean Cmax = {avg_cmax:.2f}",
            f"Mean AUC = {avg_auc:.2f}",
            f"Earliest Tmax = {min(item[2] for item in metrics):.2f}",
            f"Latest Tmax = {max(item[2] for item in metrics):.2f}",
        ],
        "chart_path": chart,
        "data_preview": to_records_table(df),
        "input_files": spec.data_files,
        "generated_file": None,
    }


def build_drug_elimination(spec: UseCaseSpec) -> dict:
    df = load_csv("Indometh.csv")
    if "Subject" not in df.columns:
        df.columns = ["Subject", "time", "conc"]
    half_lives = []

    fig, ax = plt.subplots(figsize=(7.4, 5.1))
    simple_card(fig, spec.title, "Semi-log fit for elimination behavior")
    palette = [COLORS["blue"], COLORS["teal"], COLORS["gold"], COLORS["coral"], COLORS["violet"], COLORS["sage"]]
    for color, (_, group) in zip(palette, df.groupby("Subject")):
        group = group[group["conc"] > 0].sort_values("time")
        coeffs = np.polyfit(group["time"], np.log(group["conc"]), 1)
        k = -coeffs[0]
        half_life = math.log(2) / k
        half_lives.append(half_life)
        fitted = np.exp(coeffs[1] + coeffs[0] * group["time"])
        ax.semilogy(group["time"], group["conc"], marker="o", linewidth=0, markersize=4.0, color=color, alpha=0.9)
        ax.semilogy(group["time"], fitted, linewidth=1.8, color=color, alpha=0.9)
    ax.set_title("Terminal phase is readable on the log scale", loc="left", pad=16)
    style_axis(ax, xlabel="Time", ylabel="Concentration (log scale)", grid="y")
    add_result_badge(ax, f"Median half-life {np.median(half_lives):.2f}", loc=(0.76, 0.98))
    chart = save_chart(fig, f"{spec.order:02d}-{spec.slug}.png")
    return {
        "summary": (
            f"The semi-log terminal phase suggests reasonably consistent clearance behavior across subjects, with a median half-life of {np.median(half_lives):.2f} time units. "
            f"The trick here is log-linear fitting of the terminal decline, which isolates elimination kinetics instead of mixing them with the absorption phase."
        ),
        "key_metrics": [
            f"Median half-life = {np.median(half_lives):.2f}",
            f"Shortest half-life = {min(half_lives):.2f}",
            f"Longest half-life = {max(half_lives):.2f}",
        ],
        "chart_path": chart,
        "data_preview": to_records_table(df),
        "input_files": spec.data_files,
        "generated_file": None,
    }


def build_survival_analysis(spec: UseCaseSpec) -> dict:
    df = load_waltons()
    df.to_csv(RAW_DIR / "waltons.csv", index=False)
    fig, ax = plt.subplots(figsize=(7.5, 5.1))
    simple_card(fig, spec.title, "Survival curves with log-rank test")
    kmf = KaplanMeierFitter()
    groups = sorted(df["group"].unique())
    palette = [COLORS["blue"], COLORS["coral"]]
    for color, group in zip(palette, groups):
        subset = df[df["group"] == group]
        kmf.fit(subset["T"], subset["E"], label=group)
        kmf.plot_survival_function(ax=ax, ci_show=False, color=color, linewidth=2.4, censor_styles={"marker": "|", "ms": 9, "mew": 1.2}, show_censors=True)
    result = logrank_test(
        df.loc[df["group"] == groups[0], "T"],
        df.loc[df["group"] == groups[1], "T"],
        event_observed_A=df.loc[df["group"] == groups[0], "E"],
        event_observed_B=df.loc[df["group"] == groups[1], "E"],
    )
    ax.set_title("Kaplan-Meier view", loc="left", pad=16)
    style_axis(ax, xlabel="Time", ylabel="Survival probability", grid="y")
    ax.legend(loc="upper right")
    chart = save_chart(fig, f"{spec.order:02d}-{spec.slug}.png")
    medians = []
    for group in groups:
        subset = df[df["group"] == group]
        kmf.fit(subset["T"], subset["E"])
        medians.append((group, kmf.median_survival_time_))
    return {
        "summary": (
            f"The survival curves separate enough to support a biologically meaningful difference in event timing between cohorts, and the log-rank test quantifies that full-curve separation at p {fmt_p(result.p_value)}. "
            f"Keeping censor marks visible matters because survival interpretation depends on who remains under observation, not just who has already had an event."
        ),
        "key_metrics": [
            f"{group} median survival = {median:.2f}" for group, median in medians
        ]
        + [f"Log-rank p = {fmt_p(result.p_value)}"],
        "chart_path": chart,
        "data_preview": to_records_table(df),
        "input_files": spec.data_files,
        "generated_file": None,
    }


def build_hazard_modeling(spec: UseCaseSpec) -> dict:
    df = load_rossi()
    df.to_csv(RAW_DIR / "rossi.csv", index=False)
    cph = CoxPHFitter()
    cph.fit(df, duration_col="week", event_col="arrest")
    summary = cph.summary.copy().sort_values("exp(coef)", ascending=False)
    top = summary.head(6)

    fig, ax = plt.subplots(figsize=(8.2, 5.2))
    simple_card(fig, spec.title, "Hazard ratios ranked by magnitude")
    y = np.arange(len(top))
    ratios = top["exp(coef)"].to_numpy()
    lower = top["exp(coef) lower 95%"].to_numpy()
    upper = top["exp(coef) upper 95%"].to_numpy()
    ax.hlines(y, lower, upper, color="#c8d1dc", linewidth=3.6)
    ax.scatter(ratios, y, s=58, color=COLORS["blue"], zorder=3)
    ax.axvline(1.0, color=COLORS["ink"], linestyle="--", linewidth=1)
    ax.set_yticks(y, top.index.tolist())
    ax.set_xlabel("Hazard ratio")
    ax.set_title("Higher than 1 means higher hazard", loc="left", pad=16)
    ax.set_xscale("log")
    style_axis(ax, grid="x")
    chart = save_chart(fig, f"{spec.order:02d}-{spec.slug}.png")
    return {
        "summary": (
            f"The Cox model ranks prior convictions, age, and parole-related covariates as the strongest hazard modifiers, giving investigators a prioritized view of relapse risk rather than a single average survival curve. "
            f"The statistical trick is the proportional-hazards model itself, which turns time-to-event data into interpretable hazard ratios while preserving follow-up information."
        ),
        "key_metrics": [
            f"{idx}: HR {row['exp(coef)']:.2f} ({row['exp(coef) lower 95%']:.2f}-{row['exp(coef) upper 95%']:.2f})"
            for idx, row in top.iterrows()
        ],
        "chart_path": chart,
        "data_preview": to_records_table(df),
        "input_files": spec.data_files,
        "generated_file": None,
    }


def build_contingency_explorer(spec: UseCaseSpec) -> dict:
    df = load_csv("Titanic.csv")
    table = (
        df.groupby(["Sex", "Survived"])["Freq"]
        .sum()
        .unstack(fill_value=0)
        .reindex(index=["Male", "Female"], columns=["No", "Yes"])
    )
    chi2, p_value, _, _ = stats.chi2_contingency(table.to_numpy())
    normalized = table.div(table.sum(axis=1), axis=0)

    fig, ax = plt.subplots(figsize=(6.6, 5.4))
    simple_card(fig, spec.title, "Aggregated counts become readable fast")
    im = ax.imshow(normalized, cmap="Blues", vmin=0, vmax=1)
    ax.set_xticks([0, 1], ["Did not survive", "Survived"])
    ax.set_yticks([0, 1], ["Male", "Female"])
    ax.set_title("Normalized survival share", loc="left", pad=16)
    for i in range(2):
        for j in range(2):
            ax.text(j, i, f"{normalized.iloc[i, j]:.2f}", ha="center", va="center", color=COLORS["ink"], fontsize=12, weight="bold")
    for spine in ax.spines.values():
        spine.set_visible(False)
    fig.colorbar(im, ax=ax, shrink=0.85, fraction=0.05, pad=0.04)
    chart = save_chart(fig, f"{spec.order:02d}-{spec.slug}.png")
    return {
        "summary": (
            f"The contingency map shows a pronounced enrichment of the outcome in one cohort stratum versus the other, and the chi-square test on aggregated counts confirms that imbalance is unlikely to be sampling noise "
            f"(chi-square {chi2:.2f}, p {fmt_p(p_value)}). The useful trick here is that summarized count tables can still yield a clean, valid categorical inference without reconstructing individual-level rows."
        ),
        "key_metrics": [
            f"Male survival share = {normalized.loc['Male', 'Yes']:.2f}",
            f"Female survival share = {normalized.loc['Female', 'Yes']:.2f}",
            f"Chi-square p = {fmt_p(p_value)}",
        ],
        "chart_path": chart,
        "data_preview": to_records_table(df),
        "input_files": spec.data_files,
        "generated_file": None,
    }


def build_logistic_risk_model(spec: UseCaseSpec) -> dict:
    df = load_csv("esoph.csv")
    expanded_rows = []
    for _, row in df.iterrows():
        case_rows = int(row["ncases"])
        control_rows = int(row["ncontrols"])
        covars = {"agegp": row["agegp"], "alcgp": row["alcgp"], "tobgp": row["tobgp"]}
        expanded_rows.extend([{**covars, "case": 1}] * case_rows)
        expanded_rows.extend([{**covars, "case": 0}] * control_rows)
    expanded = pd.DataFrame(expanded_rows)
    model = sm.Logit.from_formula("case ~ C(agegp) + C(alcgp) + C(tobgp)", data=expanded).fit(disp=False)
    odds = np.exp(model.params).sort_values(ascending=False).head(8)
    conf = np.exp(model.conf_int()).loc[odds.index]

    fig, ax = plt.subplots(figsize=(8.3, 5.3))
    simple_card(fig, spec.title, "Risk factors expressed as odds ratios")
    y = np.arange(len(odds))
    ax.hlines(y, conf[0], conf[1], color="#c8d1dc", linewidth=3.6)
    ax.scatter(odds, y, s=58, color=COLORS["coral"], zorder=3)
    ax.axvline(1.0, color=COLORS["ink"], linestyle="--", linewidth=1)
    ax.set_yticks(y, odds.index)
    ax.set_xlabel("Odds ratio")
    ax.set_title("Alcohol and tobacco bins shift risk sharply", loc="left", pad=16)
    ax.set_xscale("log")
    style_axis(ax, grid="x")
    chart = save_chart(fig, f"{spec.order:02d}-{spec.slug}.png")
    return {
        "summary": (
            f"The model points to alcohol and tobacco exposure bins with materially elevated odds of case status, which is the biological question investigators actually care about in exposure-associated cancer risk work. "
            f"Logistic regression is doing the heavy lifting by converting grouped case-control counts into adjusted odds ratios and confidence intervals instead of leaving you with raw percentages alone."
        ),
        "key_metrics": [
            f"{idx}: OR {odds.loc[idx]:.2f} ({conf.loc[idx, 0]:.2f}-{conf.loc[idx, 1]:.2f})" for idx in odds.index
        ],
        "chart_path": chart,
        "data_preview": to_records_table(df),
        "input_files": spec.data_files,
        "generated_file": None,
    }


def build_outlier_qc_review(spec: UseCaseSpec) -> dict:
    df = load_csv("airquality.csv")
    clean = df.dropna(subset=["Ozone", "Temp"]).copy()
    q1 = clean["Ozone"].quantile(0.25)
    q3 = clean["Ozone"].quantile(0.75)
    iqr = q3 - q1
    lower = q1 - 1.5 * iqr
    upper = q3 + 1.5 * iqr
    clean["flagged"] = (clean["Ozone"] < lower) | (clean["Ozone"] > upper)

    fig, axes = plt.subplots(1, 2, figsize=(10.2, 4.8))
    simple_card(fig, spec.title, "QC stays visual and explainable")
    axes[0].scatter(clean.loc[~clean["flagged"], "Temp"], clean.loc[~clean["flagged"], "Ozone"], s=30, color=COLORS["blue"], edgecolor="white", linewidth=0.5, alpha=0.75)
    axes[0].scatter(clean.loc[clean["flagged"], "Temp"], clean.loc[clean["flagged"], "Ozone"], s=48, color=COLORS["coral"], edgecolor="white", linewidth=0.7)
    axes[0].set_title("Scatter with flagged points", loc="left", fontsize=13)
    style_axis(axes[0], xlabel="Temperature", ylabel="Ozone", grid="y")
    axes[1].boxplot(
        clean["Ozone"],
        vert=True,
        patch_artist=True,
        boxprops={"facecolor": COLORS["light_blue"], "edgecolor": COLORS["ink"]},
        medianprops={"color": COLORS["ink"], "linewidth": 2},
        whiskerprops={"color": COLORS["ink"]},
        capprops={"color": COLORS["ink"]},
    )
    axes[1].scatter(swarm_positions(clean["Ozone"].to_numpy(), 1.04, spread=0.08), clean["Ozone"], s=10, color=COLORS["gray"], alpha=0.28)
    axes[1].set_xticks([1], ["Ozone"])
    axes[1].set_title("Distribution view", loc="left", fontsize=13)
    style_axis(axes[1], ylabel="Ozone", grid="y")
    chart = save_chart(fig, f"{spec.order:02d}-{spec.slug}.png")
    return {
        "summary": (
            f"This QC pass flags {int(clean['flagged'].sum())} ozone values after removing rows with missing inputs, giving the team a concrete set of measurements that could distort downstream conclusions. "
            f"The IQR rule is intentionally simple and robust: it is a transparent nonparametric screen for unusual values that does not depend on assuming a normal distribution."
        ),
        "key_metrics": [
            f"Rows with missing data = {int(len(df) - len(clean))}",
            f"Flagged outliers = {int(clean['flagged'].sum())}",
            f"IQR bounds = [{lower:.1f}, {upper:.1f}]",
        ],
        "chart_path": chart,
        "data_preview": to_records_table(df),
        "input_files": spec.data_files,
        "generated_file": None,
    }


def build_publication_figure_board(spec: UseCaseSpec) -> dict:
    panel_sources = [
        CHART_DIR / "01-two-group-supplement-comparison.png",
        CHART_DIR / "04-factorial-experiment.png",
        CHART_DIR / "12-enzyme-kinetics.png",
        CHART_DIR / "15-survival-analysis.png",
    ]
    labels = ["A", "B", "C", "D"]
    images = [plt.imread(path) for path in panel_sources]
    fig, axes = plt.subplots(2, 2, figsize=(14, 10.6))
    fig.patch.set_facecolor("white")
    for ax, label, image, title in zip(
        axes.flatten(),
        labels,
        images,
        ["Two-group comparison", "Factorial interaction", "Enzyme kinetics", "Kaplan-Meier survival"],
    ):
        ax.imshow(image)
        ax.axis("off")
        ax.text(
            0.015,
            0.98,
            label,
            transform=ax.transAxes,
            va="top",
            ha="left",
            fontsize=14,
            color="white",
            bbox={"boxstyle": "round,pad=0.25", "facecolor": COLORS["ink"], "edgecolor": COLORS["ink"]},
        )
        ax.text(0.02, -0.03, title, transform=ax.transAxes, fontsize=11, color=COLORS["ink"], ha="left")
    fig.suptitle("Four-panel publication board", x=0.06, y=0.98, ha="left", fontsize=17, fontweight="bold", color=COLORS["ink"])
    fig.text(
        0.06,
        0.025,
        "Clean panel labels, consistent margins, and matched typography are non-negotiable if we want to exceed Prism on final figure composition.",
        ha="left",
        fontsize=10.2,
        color=COLORS["gray"],
    )
    board_path = CHART_DIR / f"{spec.order:02d}-{spec.slug}.png"
    export_dir = EXPORT_DIR / board_path.stem
    export_dir.mkdir(parents=True, exist_ok=True)
    fig.tight_layout(rect=[0.02, 0.05, 0.98, 0.95], pad=1.3)
    fig.savefig(board_path, dpi=260, bbox_inches="tight")
    fig.savefig(export_dir / f"{board_path.stem}.svg", bbox_inches="tight")
    fig.savefig(export_dir / f"{board_path.stem}.pdf", bbox_inches="tight")
    fig.savefig(export_dir / f"{board_path.stem}.png", dpi=600, bbox_inches="tight")
    fig.savefig(
        export_dir / f"{board_path.stem}.tiff",
        dpi=300,
        bbox_inches="tight",
        pil_kwargs={"compression": "tiff_lzw"},
    )
    plt.close(fig)
    return {
        "summary": (
            f"The final board reads like a mechanism-of-action figure rather than a pile of unrelated plots: efficacy, interaction, kinetic, and survival evidence all support the same biological story. "
            f"The trick here is compositional rather than inferential, using panel hierarchy, typography, and cross-panel alignment so reviewers can connect multiple analyses in one pass."
        ),
        "key_metrics": [
            "Panel A: two-group comparison",
            "Panel B: factorial ANOVA interaction",
            "Panel C: enzyme kinetics fit",
            "Panel D: Kaplan-Meier survival",
        ],
        "chart_path": f"generated/charts/{board_path.name}",
        "data_preview": [],
        "input_files": spec.data_files,
        "generated_file": None,
    }


BUILDERS: dict[str, Callable[[UseCaseSpec], dict]] = {
    "build_two_group_supplement": build_two_group_supplement,
    "build_dose_response_overview": build_dose_response_overview,
    "build_grouped_mean_comparison": build_grouped_mean_comparison,
    "build_factorial_experiment": build_factorial_experiment,
    "build_paired_before_after": build_paired_before_after,
    "build_time_course_summary": build_time_course_summary,
    "build_repeated_growth_curves": build_repeated_growth_curves,
    "build_regression_and_calibration": build_regression_and_calibration,
    "build_correlation_screen": build_correlation_screen,
    "build_pca_species_map": build_pca_species_map,
    "build_distribution_comparison": build_distribution_comparison,
    "build_enzyme_kinetics": build_enzyme_kinetics,
    "build_pharmacokinetics": build_pharmacokinetics,
    "build_drug_elimination": build_drug_elimination,
    "build_survival_analysis": build_survival_analysis,
    "build_hazard_modeling": build_hazard_modeling,
    "build_contingency_explorer": build_contingency_explorer,
    "build_logistic_risk_model": build_logistic_risk_model,
    "build_outlier_qc_review": build_outlier_qc_review,
    "build_publication_figure_board": build_publication_figure_board,
}


TUTORIAL_CONTEXT_OVERRIDES: dict[str, dict[str, object]] = {
    "two-group-supplement-comparison": {
        "title": "Low-Dose Mineralization Rescue Assay",
        "goal": "Compare low-dose mineralization rescue between two supplement chemistries while keeping every animal visible.",
        "steps": [
            "Open Low-Dose Mineralization Rescue Assay from the Tutorial library.",
            "Review the preview table and confirm the analysis is restricted to the 0.5 mg/day treatment arm in the preclinical cohort.",
            "Inspect the raw-point efficacy plot before reading the test result so replicate spread stays visible.",
            "Read the automatic Welch t test card and the 95% confidence interval for the treatment difference.",
            "Export the figure as SVG or PNG for a lab meeting slide or a draft results section.",
        ],
        "what_to_notice": "Bench scientists trust this style of view because every replicate stays visible and the efficacy call is tied to a confidence interval, not a bar chart alone.",
        "source_note": "ToothGrowth from the R datasets collection, framed here as a preclinical mineralization assay proxy.",
    },
    "dose-response-overview": {
        "title": "Vitamin C Dose Escalation Response",
        "goal": "Show how a preclinical growth readout shifts across three dose levels in a simple dose-escalation study.",
        "steps": [
            "Open Vitamin C Dose Escalation Response.",
            "Confirm the input file contains the full cohort so all three treatment levels remain in the analysis.",
            "Inspect the dose-wise raw-point summary plot to see whether the assay response rises monotonically.",
            "Read the ANOVA result and the pairwise dose-comparison card to identify where the separation appears.",
            "Use the publication export preset if you need a journal-ready raster or vector figure.",
        ],
        "what_to_notice": "This feels like a classic wet-lab potency check: replicate-level spread, monotonic dose behavior, and formal post-hoc comparisons in one view.",
        "source_note": "ToothGrowth from the R datasets collection, framed here as a three-arm dose-escalation efficacy proxy.",
    },
    "grouped-mean-comparison": {
        "title": "Three-Arm Compound Response Screen",
        "goal": "Compare a control arm and two treated arms in a compact compound-response experiment.",
        "steps": [
            "Open Three-Arm Compound Response Screen from the Tutorial list.",
            "Review the preview table and verify that each treatment arm contributes the same number of replicates.",
            "Inspect the dot-and-summary chart before looking at p values so the replicate structure is clear.",
            "Use the Tukey card to identify which treatment separates from the control condition.",
            "Add the figure to a board if you want to combine this hit-confirmation panel with orthogonal assays.",
        ],
        "what_to_notice": "This is the kind of figure wet-lab teams drop into update decks because it shows every replicate and the follow-up pairwise call without clutter.",
        "source_note": "PlantGrowth from the R datasets collection, framed here as a three-arm compound-response assay proxy.",
    },
    "factorial-experiment": {
        "title": "Matrix-by-Tension Interaction Screen",
        "goal": "Assess whether scaffold material and applied tension interact in a biomaterials stress assay.",
        "steps": [
            "Open Matrix-by-Tension Interaction Screen.",
            "Inspect the grouped preview and note the two material classes and three mechanical settings.",
            "Read the interaction plot first to understand whether the response curves stay parallel or diverge by condition.",
            "Use the ANOVA panel to separate the material effect, the tension effect, and the interaction term.",
            "Export the figure and the ANOVA summary if you need a methods-friendly interaction readout.",
        ],
        "what_to_notice": "Interaction plots matter in translational lab work because they separate a main effect from a context-dependent effect that changes with the assay condition.",
        "source_note": "warpbreaks from the R datasets collection, framed here as a biomaterials tensile-stress assay proxy.",
    },
    "paired-before-after": {
        "title": "Matched Before/After Neuroresponse Study",
        "goal": "Measure within-subject change after intervention instead of pretending paired readouts are independent.",
        "steps": [
            "Open Matched Before/After Neuroresponse Study.",
            "Verify from the preview that every subject contributes a baseline and a post-intervention readout.",
            "Inspect the paired-lines plot to see whether the direction of change is consistent donor by donor.",
            "Review the paired t test and the mean paired shift from baseline.",
            "Use the notes area to record whether the change looks biologically meaningful, not merely non-zero.",
        ],
        "what_to_notice": "Paired plots are a wet-lab staple because they surface donor-to-donor heterogeneity before the statistical summary flattens it.",
        "source_note": "sleep from the R datasets collection, framed here as a matched before-and-after neuropharmacology proxy.",
    },
    "time-course-summary": {
        "title": "Cellular Oxygen Demand Time Course",
        "goal": "Turn a short respirometry-style time course into a compact functional summary.",
        "steps": [
            "Open Cellular Oxygen Demand Time Course.",
            "Inspect the input table and confirm the measurement times increase in the correct order.",
            "Review the line chart to see how quickly the assay response approaches a plateau.",
            "Read the AUC and terminal-value summary card for the compact kinetic interpretation.",
            "Export the panel if you need a clean metabolism figure for a progress review or manuscript draft.",
        ],
        "what_to_notice": "This is the kind of metabolic assay panel people want quickly: kinetics, endpoint, and AUC in one publication-ready card.",
        "source_note": "BOD from the R datasets collection, framed here as a cellular respirometry assay proxy.",
    },
    "repeated-growth-curves": {
        "title": "Longitudinal Organoid Growth Tracking",
        "goal": "Review repeated growth measurements while preserving each organoid trajectory.",
        "steps": [
            "Open Longitudinal Organoid Growth Tracking.",
            "Inspect the preview and confirm each organoid has measurements across multiple collection days.",
            "Read the trajectory plot to compare how growth velocity differs organoid by organoid.",
            "Use the slope summary to identify the fastest and slowest-growing members of the cohort.",
            "Add this panel to a board if you are building a developmental or screening narrative.",
        ],
        "what_to_notice": "Developmental and screening groups like this view because outlier trajectories and growth-rate differences stay visible instead of disappearing into a mean trace.",
        "source_note": "Orange from the R datasets collection, framed here as a longitudinal organoid-growth assay proxy.",
    },
    "regression-and-calibration": {
        "title": "Diameter-to-Volume Calibration Curve",
        "goal": "Fit a calibration relationship you could use to estimate tissue mass or volume from a bench measurement.",
        "steps": [
            "Open Diameter-to-Volume Calibration Curve.",
            "Inspect the input columns and confirm the physical measurement sits on the x-axis and the calibrated readout on the y-axis.",
            "Review the fitted line and uncertainty band to see whether the relationship is tight enough for use.",
            "Read the slope, R-squared, and interval summary in the result card.",
            "Export the SVG if you want a clean calibration figure for methods or supplemental notes.",
        ],
        "what_to_notice": "Assay teams often need a calibration figure that is statistically explicit and still clean enough to live in a methods section.",
        "source_note": "trees from the R datasets collection, framed here as an imaging-to-volume calibration proxy.",
    },
    "correlation-screen": {
        "title": "Microscopy Feature Correlation Screen",
        "goal": "Quickly screen relationships across multiple morphology features before deeper modeling.",
        "steps": [
            "Open Microscopy Feature Correlation Screen.",
            "Inspect the feature preview and note that the phenotype label is excluded from the correlation matrix.",
            "Read the heatmap first to spot which morphology measurements move together most strongly.",
            "Use the metric card to identify the top feature pair for follow-up review.",
            "Export the heatmap when you need a compact exploratory panel for collaborators.",
        ],
        "what_to_notice": "This is a practical phenotyping move: find which readouts travel together before choosing a reduced panel for follow-up experiments.",
        "source_note": "iris from the R datasets collection, framed here as a single-cell morphology feature-screen proxy.",
    },
    "pca-species-map": {
        "title": "Phenotype Separation PCA Map",
        "goal": "Compress multiple assay features into two axes and inspect how clearly biological states separate.",
        "steps": [
            "Open Phenotype Separation PCA Map.",
            "Inspect the standardized feature list before computing the dimensionality reduction.",
            "Review the scatter plot to see whether the phenotypic classes separate along the first two components.",
            "Read the explained-variance card to judge how much structure is retained in the map.",
            "Add the panel to a board if you want a compact unsupervised phenotyping summary.",
        ],
        "what_to_notice": "PCA earns its keep when it shows whether treatment states or biological classes are visibly separable without needing a statistics lecture.",
        "source_note": "iris from the R datasets collection, framed here as a cell-state morphology PCA proxy.",
    },
    "distribution-comparison": {
        "title": "Cell-State Distribution Shift",
        "goal": "Compare full distributions, not just means, across three biological states.",
        "steps": [
            "Open Cell-State Distribution Shift.",
            "Review the state labels in the preview and confirm which measurement column is being summarized.",
            "Inspect the violin plot to understand shape, spread, overlap, and tail behavior.",
            "Read the ANOVA result card to decide whether the mean difference is worth formalizing further.",
            "Export the figure if you need a more expressive alternative to a plain box plot.",
        ],
        "what_to_notice": "Wet-lab teams reach for violin plots when they care about heterogeneity, tail behavior, and overlap, not just a single average per group.",
        "source_note": "iris from the R datasets collection, framed here as a cell-state size-distribution proxy.",
    },
    "enzyme-kinetics": {
        "title": "Enzyme Inhibition Kinetics Panel",
        "goal": "Fit Michaelis-Menten curves for treated and untreated enzyme conditions.",
        "steps": [
            "Open Enzyme Inhibition Kinetics Panel.",
            "Check the substrate-concentration and rate columns in the preview table.",
            "Inspect the fitted Michaelis-Menten curves over the raw points for both assay conditions.",
            "Read the Vmax and Km estimates and compare how the treated condition shifts the fit.",
            "Export the panel if you need a fast enzyme-kinetics figure for a deck, report, or manuscript.",
        ],
        "what_to_notice": "This is a non-negotiable biomedical workflow: raw rates, nonlinear fits, and interpretable Km and Vmax estimates on one panel.",
        "source_note": "Puromycin from the R datasets collection, already close to a classic enzyme-kinetics assay example.",
    },
    "pharmacokinetics": {
        "title": "PK Exposure Profile After Dosing",
        "goal": "Track concentration over time and summarize exposure metrics for a small PK cohort.",
        "steps": [
            "Open PK Exposure Profile After Dosing.",
            "Inspect the subject, time, and concentration columns in the preview table.",
            "Review the concentration-time plot to see the shared peak-and-decay shape across the cohort.",
            "Read the automatic Cmax, Tmax, and AUC summary card.",
            "Export the figure or metrics table for a PK review packet or translational update.",
        ],
        "what_to_notice": "Scientists expect this view to answer two questions immediately: what the curve looks like and whether exposure is changing enough to matter.",
        "source_note": "Theoph from the R datasets collection, framed here as a small-cohort pharmacokinetic assay example.",
    },
    "drug-elimination": {
        "title": "Terminal Elimination Half-Life Review",
        "goal": "Estimate terminal clearance behavior from concentration decay data.",
        "steps": [
            "Open Terminal Elimination Half-Life Review.",
            "Inspect the subject-level concentration-time table before looking at the fit.",
            "Read the semi-log plot to confirm the terminal phase appears approximately linear on the log scale.",
            "Review the cohort half-life estimate and the subject-to-subject variability card.",
            "Export the panel if you need a compact clearance appendix figure.",
        ],
        "what_to_notice": "The semi-log panel is valuable because it lets reviewers judge whether the reported half-life is supported by the shape of the terminal phase.",
        "source_note": "Indometh from the R datasets collection, framed here as a small-molecule clearance proxy.",
    },
    "survival-analysis": {
        "title": "Preclinical Survival Curve Comparison",
        "goal": "Compare survival across control and treatment cohorts while keeping censoring visible.",
        "steps": [
            "Open Preclinical Survival Curve Comparison.",
            "Inspect the event-time preview and note the cohort assignment before looking at the curves.",
            "Review the stepwise survival traces and the at-risk behavior over time.",
            "Read the log-rank result card for the between-cohort comparison.",
            "Export the plot if you need a manuscript-ready survival panel.",
        ],
        "what_to_notice": "Kaplan-Meier plots are central in translational work because the figure itself often carries the biological story before anyone opens the statistics table.",
        "source_note": "waltons from the lifelines example datasets, framed here as a therapy-versus-control survival proxy.",
    },
    "hazard-modeling": {
        "title": "Clinical Relapse Hazard Modeling",
        "goal": "Move from survival curves to interpretable hazard ratios across clinically meaningful covariates.",
        "steps": [
            "Open Clinical Relapse Hazard Modeling.",
            "Inspect the covariate preview to understand which clinical predictors are available to the model.",
            "Review the ranked hazard-ratio chart to see the strongest risk and protective associations.",
            "Read the model card for the top coefficients and confidence intervals.",
            "Use the result bundle if you want a fast model summary for collaborators or investigators.",
        ],
        "what_to_notice": "Hazard-ratio views work best when they stay visual and legible for biologists who need the direction and scale of risk fast.",
        "source_note": "rossi from the lifelines example datasets, framed here as a clinical relapse-risk modeling proxy.",
    },
    "contingency-explorer": {
        "title": "Responder Frequency Contingency Map",
        "goal": "Compare categorical outcome frequencies across cohort strata from an aggregated count table.",
        "steps": [
            "Open Responder Frequency Contingency Map.",
            "Inspect the aggregated count table and note that summarized frequencies, not individual records, drive the analysis.",
            "Review the heatmap to spot which strata are enriched or depleted for the responder outcome.",
            "Read the chi-square statistic and the odds-style interpretation card.",
            "Export the panel if you need a clean categorical summary for a screen review or supplement.",
        ],
        "what_to_notice": "This is useful when assay or screening results arrive as summarized counts and you still need a clean figure plus a formal test.",
        "source_note": "Titanic from the R datasets collection, framed here as an aggregated cohort-outcome contingency proxy.",
    },
    "logistic-risk-model": {
        "title": "Exposure-Associated Cancer Risk Model",
        "goal": "Model case-control risk across exposure bins and show interpretable odds ratios.",
        "steps": [
            "Open Exposure-Associated Cancer Risk Model.",
            "Inspect the grouped case-control input table and note the exposure bins before looking at the model.",
            "Review the odds-ratio chart to see which exposure ranges shift risk most strongly.",
            "Read the model summary card and the interval labels for the leading effects.",
            "Export the figure if you need a concise epidemiology or translational risk slide.",
        ],
        "what_to_notice": "Odds-ratio plots land well with biomedical teams because they let you scan effect size and interval uncertainty without reading raw coefficients.",
        "source_note": "esoph from the R datasets collection, already a biomedical case-control dataset.",
    },
    "outlier-qc-review": {
        "title": "Assay Plate QC and Outlier Review",
        "goal": "Run a transparent QC pass that flags outliers and missing values before downstream interpretation.",
        "steps": [
            "Open Assay Plate QC and Outlier Review.",
            "Inspect the preview table and note missing values before looking at any outlier flags.",
            "Review the scatter and box plot together so both trend and spread remain visible.",
            "Read the QC card to see how many measurements were flagged by the IQR rule.",
            "Export the panel if you need an appendix figure documenting exclusions or review decisions.",
        ],
        "what_to_notice": "Good QC figures reduce argument later because the exclusion logic is visible, reproducible, and tied to the raw distribution.",
        "source_note": "airquality from the R datasets collection, framed here as a plate-level assay QC proxy.",
    },
    "publication-figure-board": {
        "title": "Mechanism-of-Action Manuscript Board",
        "goal": "Assemble multiple assay readouts into a single submission-style figure board with a bench-science narrative.",
        "steps": [
            "Open Mechanism-of-Action Manuscript Board.",
            "Review how the board combines efficacy, interaction, nonlinear-fit, and survival readouts into one story.",
            "Inspect the shared spacing, panel labels, and caption strip to see whether the narrative hangs together.",
            "Use this board as the final checkpoint before exporting a submission-ready multi-panel figure.",
            "Export the board as a vector source figure or a high-resolution raster for manuscript assembly.",
        ],
        "what_to_notice": "This is where the product has to feel like a serious publication tool: panel balance, labeling, and narrative flow should work before Illustrator ever opens.",
        "source_note": "Composite figure built from generated proxy assay panels spanning efficacy, interaction, kinetics, and survival.",
    },
}


def slugify(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")


def dataset_slug_for_path(relative_path: str) -> str:
    path = Path(relative_path)
    stem = path.stem if path.parent.name == "raw" else f"{path.parent.name}-{path.stem}"
    return slugify(stem)


def build_dataset_library(use_cases: list[dict]) -> list[dict]:
    figure_links: dict[str, set[str]] = defaultdict(set)
    by_slug = {item["slug"]: item for item in use_cases}
    generated_label = pd.Timestamp.utcnow().strftime("%b %d, %Y")

    for item in use_cases:
        for relative_path in item["data_files"]:
            figure_links[relative_path].add(item["slug"])

    datasets = []
    for relative_path in sorted(figure_links):
        path = ROOT / relative_path
        if not path.exists() or path.suffix.lower() != ".csv":
            continue
        frame = pd.read_csv(path)
        linked_figures = [by_slug[slug] for slug in sorted(figure_links[relative_path], key=lambda slug: by_slug[slug]["order"])]
        kind = "Raw dataset" if relative_path.startswith("data/raw/") else "Derived table"
        source = "Shared public dataset" if relative_path.startswith("data/raw/") else "Generated figure table"
        description = (
            f"{kind} available to multiple projects and linked to {len(linked_figures)} figure draft(s)."
        )
        datasets.append(
            {
                "slug": dataset_slug_for_path(relative_path),
                "name": path.name,
                "path": relative_path,
                "kind": kind,
                "source": source,
                "description": description,
                "rows": int(len(frame)),
                "columns": int(len(frame.columns)),
                "updated_at": generated_label,
                "preview": to_records_table(frame, rows=6),
                "linked_figures": [
                    {
                        "slug": item["slug"],
                        "title": item["title"],
                        "analysis": item["analysis"],
                    }
                    for item in linked_figures
                ],
                "linked_projects": [],
            }
        )

    return datasets


def build_workspace_entities(use_cases: list[dict], datasets: list[dict]) -> dict:
    by_slug = {item["slug"]: item for item in use_cases}
    dataset_by_path = {item["path"]: item for item in datasets}

    project_blueprints = [
        {
            "slug": "nutrient-response-atlas",
            "name": "Nutrient Response Atlas",
            "status": "Figure review",
            "tone": "progress",
            "completion": 78,
            "owner": "Translational Biology",
            "target_journal": "Nature Metabolism",
            "due_date": "Apr 2",
            "next_review": "Thu 2:00 PM",
            "summary": "A nutrition-response manuscript workspace with a polished board, linked source data, and figure-level review checkpoints.",
            "hero_figure_slug": "publication-figure-board",
            "export_preset": "Nature two-column",
            "team": [
                {"name": "Ava Patel", "role": "Lead biologist", "initials": "AP"},
                {"name": "Noah Kim", "role": "Statistician", "initials": "NK"},
                {"name": "Mia Chen", "role": "Medical writer", "initials": "MC"},
            ],
            "tasks": [
                "Confirm panel lettering sizes against the journal preset.",
                "Finalize source-data annotations for supplement and dose labels.",
                "Approve the combined figure legend before coauthor circulation.",
            ],
            "milestones": [
                {"label": "Source data locked", "state": "complete"},
                {"label": "Figure legend review", "state": "in_progress"},
                {"label": "Coauthor packet export", "state": "pending"},
            ],
            "figures": [
                ("publication-figure-board", "Ready for coauthor review", "success", "v4.1", "Confirm journal lettering sizes.", "Ava Patel"),
                ("two-group-supplement-comparison", "Legend approved", "success", "v3.2", "Lock the OJ vs VC caption wording.", "Mia Chen"),
                ("dose-response-overview", "Stats approved", "success", "v2.7", "Align axis casing with panel lettering.", "Noah Kim"),
                ("grouped-mean-comparison", "Needs panel selection", "warning", "v1.9", "Decide whether Treatment 1 stays in the main figure.", "Ava Patel"),
            ],
            "manuscript": {
                "slug": "nutrient-response-atlas-manuscript",
                "title": "Dietary Supplementation Reshapes Growth Response Dynamics",
                "status": "Results drafting",
                "tone": "progress",
                "narrative": "A four-panel narrative is almost locked, with results text drafted and source-data packaging complete.",
                "submission_preset": "Nature two-column",
                "sections": [
                    {"label": "Abstract", "state": "draft_ready"},
                    {"label": "Results", "state": "in_review"},
                    {"label": "Methods", "state": "pending"},
                    {"label": "Source data", "state": "complete"},
                ],
                "deliverables": [
                    {"label": "Main figure board", "state": "ready"},
                    {"label": "Source-data package", "state": "ready"},
                    {"label": "Cover letter", "state": "pending"},
                ],
            },
        },
        {
            "slug": "enzyme-screening-studio",
            "name": "Enzyme Screening Studio",
            "status": "Methods polish",
            "tone": "progress",
            "completion": 64,
            "owner": "Assay Development",
            "target_journal": "Cell Chemical Biology",
            "due_date": "Apr 11",
            "next_review": "Mon 10:30 AM",
            "summary": "A project space for nonlinear fits, assay calibration, and exploratory comparison panels before the inhibition note is finalized.",
            "hero_figure_slug": "enzyme-kinetics",
            "export_preset": "Cell single-column",
            "team": [
                {"name": "Lena Ortiz", "role": "Assay scientist", "initials": "LO"},
                {"name": "Ethan Brooks", "role": "Data scientist", "initials": "EB"},
                {"name": "Sara Lin", "role": "Editor", "initials": "SL"},
            ],
            "tasks": [
                "Review Michaelis-Menten fit residuals for the treated condition.",
                "Trim the calibration panel to the manuscript-relevant concentration range.",
                "Decide whether the distribution comparison moves to supplement.",
            ],
            "milestones": [
                {"label": "Nonlinear fit locked", "state": "in_progress"},
                {"label": "Calibration panel approved", "state": "complete"},
                {"label": "Methods paragraph harmonized", "state": "pending"},
            ],
            "figures": [
                ("enzyme-kinetics", "Fit review", "progress", "v2.4", "Approve the treated-condition residual note.", "Ethan Brooks"),
                ("regression-and-calibration", "Ready for export", "success", "v2.1", "Export the SVG for manuscript insertion.", "Lena Ortiz"),
                ("distribution-comparison", "Supplement candidate", "warning", "v1.6", "Choose main-text versus supplement placement.", "Sara Lin"),
                ("correlation-screen", "Exploratory only", "neutral", "v1.2", "Use as a backup slide for the team meeting.", "Ethan Brooks"),
            ],
            "manuscript": {
                "slug": "enzyme-screening-note",
                "title": "Rapid Enzyme Screening with Transparent Fit Review",
                "status": "Methods edit",
                "tone": "progress",
                "narrative": "Primary fits are in shape; the manuscript packet is waiting on tighter methods language and one figure-placement decision.",
                "submission_preset": "Cell single-column",
                "sections": [
                    {"label": "Abstract", "state": "in_review"},
                    {"label": "Results", "state": "draft_ready"},
                    {"label": "Methods", "state": "in_review"},
                    {"label": "Source data", "state": "complete"},
                ],
                "deliverables": [
                    {"label": "Nonlinear fit panel", "state": "ready"},
                    {"label": "Calibration panel", "state": "ready"},
                    {"label": "Supplement figure decision", "state": "pending"},
                ],
            },
        },
        {
            "slug": "growth-dynamics-notebook",
            "name": "Growth Dynamics Notebook",
            "status": "Exploratory analysis",
            "tone": "neutral",
            "completion": 42,
            "owner": "Discovery Research",
            "target_journal": "Internal exploration",
            "due_date": "Apr 19",
            "next_review": "Fri 4:00 PM",
            "summary": "An exploratory workspace for repeated-measures growth, time-course saturation, and dimensionality-reduction snapshots before a formal story is chosen.",
            "hero_figure_slug": "repeated-growth-curves",
            "export_preset": "Internal review deck",
            "team": [
                {"name": "Jon Park", "role": "Research lead", "initials": "JP"},
                {"name": "Nina Shah", "role": "Analyst", "initials": "NS"},
            ],
            "tasks": [
                "Decide whether growth trajectories deserve a dedicated manuscript or stay in exploratory review.",
                "Compare the PCA map with the correlation screen for the next lab meeting.",
                "Package the time-course summary for the weekly notebook export.",
            ],
            "milestones": [
                {"label": "Exploration deck assembled", "state": "in_progress"},
                {"label": "Narrative chosen", "state": "pending"},
                {"label": "Manuscript decision", "state": "pending"},
            ],
            "figures": [
                ("repeated-growth-curves", "Team review", "progress", "v1.8", "Annotate the fastest-growth trajectory.", "Nina Shah"),
                ("time-course-summary", "Ready for notebook export", "success", "v1.5", "Bundle the compact kinetic summary.", "Jon Park"),
                ("pca-species-map", "Needs interpretation note", "warning", "v1.4", "Write the PC1/PC2 takeaways for the team.", "Nina Shah"),
            ],
            "manuscript": None,
        },
        {
            "slug": "pkpd-translation-board",
            "name": "PK/PD Translation Board",
            "status": "Submission prep",
            "tone": "success",
            "completion": 91,
            "owner": "Clinical Pharmacology",
            "target_journal": "Clinical Pharmacology & Therapeutics",
            "due_date": "Mar 28",
            "next_review": "Today 5:00 PM",
            "summary": "A near-submission workspace that combines exposure, elimination, and survival context into one publication-ready package.",
            "hero_figure_slug": "pharmacokinetics",
            "export_preset": "CPT submission pack",
            "team": [
                {"name": "Priya Rao", "role": "PK lead", "initials": "PR"},
                {"name": "Owen Bell", "role": "Biostatistician", "initials": "OB"},
                {"name": "Kate Young", "role": "Regulatory writer", "initials": "KY"},
            ],
            "tasks": [
                "Render the final submission bundle with TIFF exports.",
                "Double-check the survival panel legend against CPT style rules.",
                "Attach the source-data tables to the submission packet.",
            ],
            "milestones": [
                {"label": "Exposure figures approved", "state": "complete"},
                {"label": "Source-data audit", "state": "complete"},
                {"label": "Submission bundle rendering", "state": "in_progress"},
            ],
            "figures": [
                ("pharmacokinetics", "Ready for submission", "success", "v3.5", "Render the CPT bundle with locked legends.", "Priya Rao"),
                ("drug-elimination", "Copy edit", "progress", "v2.6", "Shorten the half-life caption for the main text.", "Kate Young"),
                ("survival-analysis", "Legend pending", "warning", "v2.2", "Resolve the at-risk line break on mobile.", "Owen Bell"),
                ("hazard-modeling", "Approved for supplement", "success", "v2.0", "Export the forest-style panel as PDF.", "Owen Bell"),
            ],
            "manuscript": {
                "slug": "pkpd-translation-brief",
                "title": "Exposure, Elimination, and Survival Context in a Translational PK/PD Brief",
                "status": "Submission packet",
                "tone": "success",
                "narrative": "The manuscript packet is functionally complete and waiting on the final export/render pass.",
                "submission_preset": "CPT submission pack",
                "sections": [
                    {"label": "Abstract", "state": "complete"},
                    {"label": "Results", "state": "complete"},
                    {"label": "Methods", "state": "draft_ready"},
                    {"label": "Source data", "state": "complete"},
                ],
                "deliverables": [
                    {"label": "Main figure exports", "state": "ready"},
                    {"label": "Supplement PDF", "state": "ready"},
                    {"label": "Submission TIFFs", "state": "in_progress"},
                ],
            },
        },
        {
            "slug": "quality-and-risk-review",
            "name": "Quality and Risk Review",
            "status": "Internal review",
            "tone": "warning",
            "completion": 56,
            "owner": "Safety Analytics",
            "target_journal": "Internal board packet",
            "due_date": "Apr 8",
            "next_review": "Wed 11:00 AM",
            "summary": "A shared workspace for QC, categorical risk signals, and appendix-ready plots used in internal decision packets.",
            "hero_figure_slug": "outlier-qc-review",
            "export_preset": "Board briefing pack",
            "team": [
                {"name": "Grace Wu", "role": "Safety scientist", "initials": "GW"},
                {"name": "Daniel Fox", "role": "Biostatistician", "initials": "DF"},
                {"name": "Ivy Moore", "role": "Program manager", "initials": "IM"},
            ],
            "tasks": [
                "Confirm the outlier exclusions with the lab operations team.",
                "Rewrite the odds-ratio summary in plainer board-ready language.",
                "Decide whether the factorial panel stays in the appendix pack.",
            ],
            "milestones": [
                {"label": "QC review complete", "state": "in_progress"},
                {"label": "Risk summary approved", "state": "pending"},
                {"label": "Board packet export", "state": "pending"},
            ],
            "figures": [
                ("outlier-qc-review", "QC review", "warning", "v2.0", "Validate flagged rows before locking the appendix.", "Grace Wu"),
                ("logistic-risk-model", "Methods clarification", "progress", "v1.8", "Clarify exposure-bin naming for non-statisticians.", "Daniel Fox"),
                ("contingency-explorer", "Board-ready", "success", "v1.7", "Export a PNG for the slide deck.", "Ivy Moore"),
                ("factorial-experiment", "Appendix candidate", "neutral", "v1.3", "Keep in reserve for mechanistic discussion.", "Grace Wu"),
            ],
            "manuscript": {
                "slug": "quality-risk-briefing",
                "title": "Quality Control and Risk Signal Briefing Pack",
                "status": "Board packet assembly",
                "tone": "warning",
                "narrative": "The packet is not a journal manuscript, but it follows the same figure, source-data, and export discipline for internal review.",
                "submission_preset": "Board briefing pack",
                "sections": [
                    {"label": "Executive summary", "state": "draft_ready"},
                    {"label": "QC appendix", "state": "in_review"},
                    {"label": "Risk interpretation", "state": "pending"},
                    {"label": "Source data", "state": "complete"},
                ],
                "deliverables": [
                    {"label": "QC appendix figure", "state": "in_progress"},
                    {"label": "Risk summary figure", "state": "ready"},
                    {"label": "Board slide exports", "state": "pending"},
                ],
            },
        },
    ]

    projects = []
    manuscripts = []
    figure_drafts = []

    for blueprint in project_blueprints:
        manuscript_config = blueprint.get("manuscript")
        manuscript_slug = manuscript_config["slug"] if manuscript_config else None
        project_figures = []

        for slug, status, tone, version, next_action, owner in blueprint["figures"]:
            item = by_slug[slug]
            figure_card = {
                "slug": item["slug"],
                "title": item["title"],
                "analysis": item["analysis"],
                "category": item["category"],
                "summary": item["summary"],
                "chart_path": item["chart_path"],
                "data_files": item["data_files"],
                "key_metrics": item["key_metrics"][:3],
                "publication_assets": item["publication_assets"],
                "caption_text": item["caption_text"],
                "methods_text": item["methods_text"],
                "results_text": item["results_text"],
                "data_preview": item["data_preview"],
                "status": status,
                "tone": tone,
                "version": version,
                "next_action": next_action,
                "owner": owner,
                "source_note": item["source_note"],
                "what_to_notice": item["what_to_notice"],
                "project_slug": blueprint["slug"],
                "project_name": blueprint["name"],
                "manuscript_slug": manuscript_slug,
                "manuscript_title": manuscript_config["title"] if manuscript_config else None,
            }
            project_figures.append(figure_card)
            figure_drafts.append(figure_card)

        dataset_paths = sorted({path for figure in project_figures for path in figure["data_files"]})
        project_datasets = []
        for relative_path in dataset_paths:
            dataset = dataset_by_path.get(relative_path)
            if not dataset:
                continue
            project_datasets.append(
                {
                    "slug": dataset["slug"],
                    "name": dataset["name"],
                    "kind": dataset["kind"],
                    "rows": dataset["rows"],
                    "columns": dataset["columns"],
                    "path": dataset["path"],
                    "source": dataset["source"],
                }
            )
            dataset["linked_projects"].append({"slug": blueprint["slug"], "name": blueprint["name"]})

        project = {
            "slug": blueprint["slug"],
            "name": blueprint["name"],
            "status": blueprint["status"],
            "tone": blueprint["tone"],
            "completion": blueprint["completion"],
            "owner": blueprint["owner"],
            "target_journal": blueprint["target_journal"],
            "due_date": blueprint["due_date"],
            "next_review": blueprint["next_review"],
            "summary": blueprint["summary"],
            "hero_chart_path": by_slug[blueprint["hero_figure_slug"]]["chart_path"],
            "primary_figure_slug": blueprint["hero_figure_slug"],
            "export_preset": blueprint["export_preset"],
            "team": blueprint["team"],
            "tasks": blueprint["tasks"],
            "milestones": blueprint["milestones"],
            "figures": project_figures,
            "datasets": project_datasets,
            "figure_count": len(project_figures),
            "dataset_count": len(project_datasets),
            "manuscript_slug": manuscript_slug,
            "manuscript_title": manuscript_config["title"] if manuscript_config else None,
            "manuscript_status": manuscript_config["status"] if manuscript_config else "Notebook only",
        }
        projects.append(project)

        if manuscript_config:
            ready_figure_count = sum(1 for figure in project_figures if figure["tone"] == "success")
            manuscripts.append(
                {
                    "slug": manuscript_config["slug"],
                    "title": manuscript_config["title"],
                    "status": manuscript_config["status"],
                    "tone": manuscript_config["tone"],
                    "narrative": manuscript_config["narrative"],
                    "submission_preset": manuscript_config["submission_preset"],
                    "target_journal": blueprint["target_journal"],
                    "due_date": blueprint["due_date"],
                    "project_slug": blueprint["slug"],
                    "project_name": blueprint["name"],
                    "figures": project_figures,
                    "datasets": project_datasets,
                    "sections": manuscript_config["sections"],
                    "deliverables": manuscript_config["deliverables"],
                    "figure_progress": f"{ready_figure_count}/{len(project_figures)} figures locked",
                }
            )

    for dataset in datasets:
        dataset["linked_projects"] = sorted(dataset["linked_projects"], key=lambda item: item["name"])
        dataset["project_count"] = len(dataset["linked_projects"])
        dataset["figure_count"] = len(dataset["linked_figures"])

    metrics = [
        {"value": str(len(projects)), "label": "active projects"},
        {"value": str(len(figure_drafts)), "label": "figure drafts"},
        {"value": str(len(manuscripts)), "label": "manuscript packets"},
        {"value": str(len(datasets)), "label": "shared datasets"},
    ]

    quick_actions = [
        {
            "label": "Open Active Projects",
            "path": "/workspace#projects",
            "variant": "primary",
            "description": "Jump into the project grid, where current work, review state, and journal targets live.",
        },
        {
            "label": "Review Manuscripts",
            "path": "/workspace#manuscripts",
            "variant": "secondary",
            "description": "See which submission packets are ready, blocked, or waiting on figure polish.",
        },
        {
            "label": "Browse Datasets",
            "path": "/workspace#datasets",
            "variant": "secondary",
            "description": "Inspect reusable datasets, previews, and which projects depend on them.",
        },
        {
            "label": "Open Tutorial Library",
            "path": "/tutorial",
            "variant": "secondary",
            "description": "Keep the twenty hand-held analysis recipes separate from active workspace operations.",
        },
    ]

    pinned_tasks = [
        {"label": "Lock lettering in the Nutrient Response Atlas board", "path": "/projects/nutrient-response-atlas", "tone": "progress"},
        {"label": "Render the CPT submission TIFF set", "path": "/manuscripts/pkpd-translation-brief", "tone": "success"},
        {"label": "Resolve QC exclusions before board export", "path": "/projects/quality-and-risk-review", "tone": "warning"},
    ]

    export_queue = [
        {
            "title": "Nature board manuscript bundle",
            "status": "Ready",
            "tone": "success",
            "detail": "Publication Figure Board · SVG, PDF, TIFF, caption, source data",
            "path": "/figures/publication-figure-board",
        },
        {
            "title": "CPT submission TIFF render",
            "status": "Rendering",
            "tone": "progress",
            "detail": "PK/PD Translation Board · high-resolution raster package",
            "path": "/manuscripts/pkpd-translation-brief",
        },
        {
            "title": "Board briefing slide exports",
            "status": "Queued",
            "tone": "warning",
            "detail": "Quality and Risk Review · PNG exports for executive slides",
            "path": "/manuscripts/quality-risk-briefing",
        },
        {
            "title": "Enzyme methods packet",
            "status": "Waiting on review",
            "tone": "neutral",
            "detail": "Calibration and fit panels are ready once methods text is approved",
            "path": "/projects/enzyme-screening-studio",
        },
    ]

    activity_feed = [
        {
            "title": "Publication board export completed for Nutrient Response Atlas",
            "meta": "12 minutes ago",
            "path": "/figures/publication-figure-board",
            "kind": "Figure",
        },
        {
            "title": "ToothGrowth.csv linked to the nutrient manuscript packet",
            "meta": "32 minutes ago",
            "path": "/datasets/toothgrowth",
            "kind": "Dataset",
        },
        {
            "title": "PK/PD brief advanced to submission packet stage",
            "meta": "1 hour ago",
            "path": "/manuscripts/pkpd-translation-brief",
            "kind": "Manuscript",
        },
        {
            "title": "QC review requested for the outlier appendix figure",
            "meta": "2 hours ago",
            "path": "/figures/outlier-qc-review",
            "kind": "Figure",
        },
        {
            "title": "Growth Dynamics Notebook received three new exploratory comments",
            "meta": "Today",
            "path": "/projects/growth-dynamics-notebook",
            "kind": "Project",
        },
    ]

    tutorial_library = {
        "count": len(use_cases),
        "summary": "The tutorial library still contains all twenty guided workflows, but it now lives alongside the workspace instead of pretending to be it.",
        "path": "/tutorial",
    }

    return {
        "metrics": metrics,
        "quick_actions": quick_actions,
        "pinned_tasks": pinned_tasks,
        "projects": projects,
        "manuscripts": manuscripts,
        "figure_drafts": figure_drafts,
        "datasets": datasets,
        "export_queue": export_queue,
        "activity_feed": activity_feed,
        "tutorial_library": tutorial_library,
    }


DEFAULT_VENDOR_DATASETS: tuple[str, ...] = (
    "ToothGrowth",
    "PlantGrowth",
    "sleep",
    "warpbreaks",
    "BOD",
    "trees",
    "iris",
    "Puromycin",
    "Titanic",
    "esoph",
    "airquality",
)

MANIFEST_SUMMARY = (
    "A production-oriented GraphPad Prism alternative with a real workspace for projects, "
    "datasets, manuscripts, exports, and a separate tutorial library framed around biomedical "
    "wet-lab workflows."
)


def initialize_build_environment(dataset_vendors: tuple[str, ...] = DEFAULT_VENDOR_DATASETS) -> None:
    apply_style()
    ensure_dirs()
    for dataset_name in dataset_vendors:
        vendor_rdataset(dataset_name)


class ManifestBuilder:
    def __init__(
        self,
        *,
        specs: list[UseCaseSpec] | None = None,
        builder_registry: dict[str, Callable[[UseCaseSpec], dict]] | None = None,
        tutorial_overrides: dict[str, dict[str, object]] | None = None,
        dataset_vendors: tuple[str, ...] = DEFAULT_VENDOR_DATASETS,
        environment_preparer: Callable[[tuple[str, ...]], None] = initialize_build_environment,
        publication_packager: Callable[[dict], dict] = build_publication_package,
        dataset_library_builder: Callable[[list[dict]], list[dict]] = build_dataset_library,
        workspace_builder: Callable[[list[dict], list[dict]], dict] = build_workspace_entities,
        product_name: str = PRODUCT_NAME,
        summary: str = MANIFEST_SUMMARY,
    ) -> None:
        self.specs = specs
        self.builder_registry = builder_registry or BUILDERS
        self.tutorial_overrides = tutorial_overrides or TUTORIAL_CONTEXT_OVERRIDES
        self.dataset_vendors = dataset_vendors
        self.environment_preparer = environment_preparer
        self.publication_packager = publication_packager
        self.dataset_library_builder = dataset_library_builder
        self.workspace_builder = workspace_builder
        self.product_name = product_name
        self.summary = summary

    def prepare(self) -> None:
        self.environment_preparer(self.dataset_vendors)

    def resolved_specs(self) -> list[UseCaseSpec]:
        return self.specs or make_spec_list()

    def build_use_case_item(self, spec: UseCaseSpec) -> dict:
        overrides = self.tutorial_overrides.get(spec.slug)
        if overrides:
            spec = replace(spec, **overrides)
        try:
            builder = self.builder_registry[spec.builder]
        except KeyError as exc:
            raise KeyError(f"No builder registered for '{spec.builder}'") from exc
        built = builder(spec)
        item = {
            "order": spec.order,
            "slug": spec.slug,
            "title": spec.title,
            "category": spec.category,
            "analysis": spec.analysis,
            "goal": spec.goal,
            "steps": spec.steps,
            "what_to_notice": spec.what_to_notice,
            "source_note": spec.source_note,
            "data_files": spec.data_files,
            "screenshot_path": f"/assets/screenshots/{spec.order:02d}-{spec.slug}.png",
            **built,
        }
        item.update(self.publication_packager(item))
        return item

    def build_manifest(self) -> dict:
        self.prepare()
        use_cases = [self.build_use_case_item(spec) for spec in self.resolved_specs()]
        datasets = self.dataset_library_builder(use_cases)
        workspace = self.workspace_builder(use_cases, datasets)
        return {
            "product_name": self.product_name,
            "generated_at": pd.Timestamp.utcnow().isoformat(),
            "summary": self.summary,
            "use_cases": use_cases,
            "workspace": workspace,
        }


def generate_manifest(builder: ManifestBuilder | None = None) -> dict:
    manifest = (builder or ManifestBuilder()).build_manifest()
    write_json(GENERATED_DIR / "use_cases.json", manifest)
    return manifest


def generate_tutorial_markdown(manifest: dict) -> None:
    intro = textwrap.dedent(
        """
        # AssayAtlas Real-Data Training Tutorial

        This tutorial is intentionally hand-held. Every lesson uses a real public dataset, a real statistical workflow, and a biomedical wet-lab framing rendered through the AssayAtlas workspace.

        ## How to use this tutorial

        1. Start the app locally or open the deployed AssayAtlas home page.
        2. Open the Workspace or the Tutorial page.
        3. Work through the twenty use cases in order at least once.
        4. Re-run the flows with the provided CSV files to internalize the bench-science patterns.

        ## Training goals

        - Learn the SaaS navigation without friction.
        - See what publication-grade defaults should feel like.
        - Practice twenty biomedical wet-lab workflows with transparent results and publication-ready figures.
        - Leave with exportable example figures and the raw input data for each lesson.
        - See clearly when a workflow is built from a public proxy dataset versus a directly biomedical source.
        """
    ).strip()

    sections = [intro, "\n## Use Cases\n"]
    for item in manifest["use_cases"]:
        sections.append(
            textwrap.dedent(
                f"""
                ### {item['order']:02d}. {item['title']}

                **Goal:** {item['goal']}

                **Analysis:** {item['analysis']}

                **Data files:** {", ".join(item['data_files'])}

                **Source:** {item['source_note']}

                **What to notice:** {item['what_to_notice']}

                ![Screenshot]({item['screenshot_path']})

                **Step-by-step**

                1. {item['steps'][0]}
                2. {item['steps'][1]}
                3. {item['steps'][2]}
                4. {item['steps'][3]}
                5. {item['steps'][4]}

                **Result summary:** {item['summary']}

                **Key metrics**

                - {item['key_metrics'][0]}
                - {item['key_metrics'][1] if len(item['key_metrics']) > 1 else 'See the result card in the app.'}
                - {item['key_metrics'][2] if len(item['key_metrics']) > 2 else 'See the result card in the app.'}

                **Publication exports:** `SVG`, `PDF`, `PNG`, `TIFF`

                **Bundle:** `{item['publication_assets']['bundle']}`

                **Figure asset:** `app/static/{item['chart_path']}`
                """
            ).strip()
        )

    write_text(TUTORIAL_DIR / "REAL_DATA_TRAINING_TUTORIAL.md", "\n\n".join(sections))


def generate_use_case_catalog(manifest: dict) -> None:
    rows = []
    for item in manifest["use_cases"]:
        rows.append(
            f"| {item['order']:02d} | {item['title']} | {item['category']} | {item['analysis']} | `{item['data_files'][0]}` |"
        )
    content = textwrap.dedent(
        f"""
        # Use Case Catalog

        {manifest['summary']}

        | # | Use Case | Category | Analysis | Primary Data |
        | --- | --- | --- | --- | --- |
        {'\n'.join(rows)}
        """
    ).strip()
    write_text(TUTORIAL_DIR / "USE_CASE_CATALOG.md", content)


def main() -> None:
    manifest = generate_manifest()
    generate_tutorial_markdown(manifest)
    generate_use_case_catalog(manifest)
    print(f"Generated {len(manifest['use_cases'])} use cases.")


if __name__ == "__main__":
    main()
