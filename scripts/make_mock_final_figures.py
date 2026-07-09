#!/usr/bin/env python3
# /// script
# dependencies = [
#   "matplotlib>=3.10.0",
#   "numpy>=2.2.0",
#   "pandas>=2.3.0",
#   "seaborn>=0.13.2",
# ]
# ///

from __future__ import annotations

import argparse
import os
import textwrap
from pathlib import Path

os.environ.setdefault("MPLCONFIGDIR", "/tmp/matplotlib")

import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import numpy as np
import pandas as pd
import seaborn as sns
from matplotlib import colors as mcolors
from matplotlib.patches import Rectangle


FONT_FAMILY = ["Aptos", "Inter", "Segoe UI", "DejaVu Sans", "Arial", "sans-serif"]
MONO_FONT_FAMILY = ["DejaVu Sans Mono", "Menlo", "Consolas", "monospace"]

TOKENS = {
    "surface": "#FCFCFD",
    "panel": "#FFFFFF",
    "ink": "#1F2430",
    "muted": "#6F768A",
    "grid": "#E6E8F0",
    "axis": "#D7DBE7",
}

NEUTRAL_MARKS = {
    "open": TOKENS["panel"],
    "xlight": "#F4F5F7",
    "light": "#E2E5EA",
    "base": "#C5CAD3",
    "mid": "#7A828F",
    "dark": "#464C55",
}

COLOR_FAMILIES = {
    "blue": {
        "open": TOKENS["panel"],
        "xlight": "#EAF1FE",
        "light": "#CEDFFE",
        "base": "#A3BEFA",
        "mid": "#5477C4",
        "dark": "#2E4780",
    },
    "gold": {
        "open": TOKENS["panel"],
        "xlight": "#FFF4C2",
        "light": "#FFEA8F",
        "base": "#FFE15B",
        "mid": "#B8A037",
        "dark": "#736422",
    },
    "orange": {
        "open": TOKENS["panel"],
        "xlight": "#FFEDDE",
        "light": "#FFBDA1",
        "base": "#F0986E",
        "mid": "#CC6F47",
        "dark": "#804126",
    },
    "olive": {
        "open": TOKENS["panel"],
        "xlight": "#D8ECBD",
        "light": "#BEEB96",
        "base": "#A3D576",
        "mid": "#71B436",
        "dark": "#386411",
    },
    "pink": {
        "open": TOKENS["panel"],
        "xlight": "#FCDAD6",
        "light": "#F5BACC",
        "base": "#F390CA",
        "mid": "#BD569B",
        "dark": "#8A3A6F",
    },
}

METHOD_ORDER = [
    "Frame-wise detection",
    "Content optical flow",
    "Reference tracking",
    "Reference + residual align",
]

SCENARIO_ORDER = [
    "Static page",
    "Scrolling page",
    "In-screen video",
    "Weak-border slide",
    "Moire / glare",
]


def use_chart_theme() -> None:
    sns.set_theme(
        style="whitegrid",
        rc={
            "figure.facecolor": TOKENS["surface"],
            "figure.edgecolor": "none",
            "savefig.facecolor": TOKENS["surface"],
            "savefig.edgecolor": "none",
            "axes.facecolor": TOKENS["panel"],
            "axes.edgecolor": TOKENS["axis"],
            "axes.labelcolor": TOKENS["ink"],
            "axes.grid": True,
            "axes.spines.top": False,
            "axes.spines.right": False,
            "grid.color": TOKENS["grid"],
            "grid.linewidth": 0.8,
            "font.family": "sans-serif",
            "font.sans-serif": FONT_FAMILY,
            "font.monospace": MONO_FONT_FAMILY,
            "patch.linewidth": 1.0,
        },
    )


def add_chart_header(
    fig: plt.Figure,
    ax: plt.Axes,
    title: str,
    subtitle: str,
    *,
    title_width: int = 78,
    subtitle_width: int = 112,
) -> None:
    title = textwrap.fill(title.strip(), width=title_width, break_long_words=False)
    subtitle = textwrap.fill(subtitle.strip(), width=subtitle_width, break_long_words=False)
    title_lines = title.count("\n") + 1
    subtitle_lines = subtitle.count("\n") + 1
    ax.set_title("")
    fig.subplots_adjust(
        top=max(0.62, 0.86 - 0.045 * (title_lines - 1) - 0.032 * (subtitle_lines - 1))
    )
    left = ax.get_position().x0
    fig.text(
        left,
        0.985,
        title,
        ha="left",
        va="top",
        fontsize=13,
        fontweight="bold",
        color=TOKENS["ink"],
        linespacing=1.08,
    )
    fig.text(
        left,
        0.93 - 0.045 * (title_lines - 1),
        subtitle,
        ha="left",
        va="top",
        fontsize=9,
        color=TOKENS["muted"],
        linespacing=1.18,
    )
    sns.despine(ax=ax)


def project_root() -> Path:
    script_path = Path(__file__).resolve()
    for path in (script_path.parent, *script_path.parents):
        if (path / ".git").exists():
            return path
    return Path.cwd()


def mock_metrics() -> pd.DataFrame:
    rows = []
    base = {
        "Static page": {
            "Frame-wise detection": (1.42, 0.053, 0.00130, 4.8, 0.947, 1.21, 0.88, 0.76),
            "Content optical flow": (0.61, 0.020, 0.00055, 3.2, 0.965, 0.82, 0.91, 0.67),
            "Reference tracking": (0.078, 0.0015, 0.000079, 1.1, 0.992, 0.21, 0.96, 0.58),
            "Reference + residual align": (0.055, 0.0012, 0.000052, 1.0, 0.994, 0.19, 0.97, 0.54),
        },
        "Scrolling page": {
            "Frame-wise detection": (2.35, 0.082, 0.00210, 6.4, 0.928, 2.10, 0.82, 0.88),
            "Content optical flow": (1.78, 0.061, 0.00160, 9.8, 0.891, 2.85, 0.76, 0.95),
            "Reference tracking": (0.36, 0.011, 0.00034, 1.9, 0.984, 0.48, 0.93, 0.70),
            "Reference + residual align": (0.31, 0.010, 0.00031, 1.8, 0.985, 0.45, 0.94, 0.68),
        },
        "In-screen video": {
            "Frame-wise detection": (1.96, 0.071, 0.00180, 5.8, 0.936, 1.76, 0.84, 0.81),
            "Content optical flow": (2.24, 0.087, 0.00230, 12.7, 0.854, 3.35, 0.69, 1.04),
            "Reference tracking": (0.42, 0.014, 0.00041, 2.2, 0.979, 0.62, 0.91, 0.73),
            "Reference + residual align": (0.37, 0.013, 0.00037, 2.1, 0.980, 0.58, 0.92, 0.71),
        },
        "Weak-border slide": {
            "Frame-wise detection": (2.86, 0.104, 0.00280, 8.9, 0.904, 3.10, 0.75, 0.64),
            "Content optical flow": (1.15, 0.041, 0.00100, 5.6, 0.936, 1.80, 0.83, 0.71),
            "Reference tracking": (0.54, 0.017, 0.00048, 2.8, 0.970, 0.80, 0.89, 0.52),
            "Reference + residual align": (0.49, 0.016, 0.00045, 2.7, 0.972, 0.76, 0.90, 0.50),
        },
        "Moire / glare": {
            "Frame-wise detection": (3.40, 0.132, 0.00330, 11.2, 0.872, 4.40, 0.64, 1.35),
            "Content optical flow": (2.92, 0.118, 0.00300, 15.6, 0.821, 5.20, 0.57, 1.50),
            "Reference tracking": (0.88, 0.031, 0.00084, 4.6, 0.941, 1.30, 0.80, 0.92),
            "Reference + residual align": (0.82, 0.030, 0.00081, 4.5, 0.942, 1.25, 0.81, 0.90),
        },
    }
    for scenario, methods in base.items():
        for method, values in methods.items():
            (
                translation,
                rotation,
                scale_delta,
                corner_rmse,
                quad_iou,
                aspect_error_pct,
                edge_f1,
                fft_orthogonality_error,
            ) = values
            rows.append(
                {
                    "scenario": scenario,
                    "method": method,
                    "translation_p95_px": translation,
                    "rotation_p95_deg": rotation,
                    "scale_delta_p95": scale_delta,
                    "corner_rmse_px": corner_rmse,
                    "quad_iou": quad_iou,
                    "aspect_error_pct": aspect_error_pct,
                    "edge_preservation_f1": edge_f1,
                    "gradient_ratio": 0.96 if "Reference" in method else 0.91,
                    "fft_orthogonality_error_deg": fft_orthogonality_error,
                }
            )
    return pd.DataFrame(rows)


def mock_timeline() -> pd.DataFrame:
    rng = np.random.default_rng(13)
    frames = np.arange(0, 180)
    rows = []
    profiles = {
        "Frame-wise detection": 1.25 + 0.45 * np.sin(frames / 7.0),
        "Content optical flow": 0.86 + 0.35 * np.sin(frames / 12.0 + 0.8),
        "Reference tracking": 0.18 + 0.055 * np.sin(frames / 18.0),
        "Reference + residual align": 0.13 + 0.040 * np.sin(frames / 21.0 + 0.4),
    }
    for method, values in profiles.items():
        noise = rng.normal(0.0, 0.06 if "Reference" not in method else 0.012, size=len(frames))
        for frame, value in zip(frames, np.maximum(values + noise, 0.0), strict=True):
            rows.append(
                {
                    "frame": int(frame),
                    "method": method,
                    "translation_px": float(value),
                }
            )
    return pd.DataFrame(rows)


def save_figure(fig: plt.Figure, output_dir: Path, stem: str) -> None:
    output = output_dir / f"{stem}.svg"
    fig.savefig(output, bbox_inches="tight")
    plt.close(fig)
    clean_svg(output)


def clean_svg(path: Path) -> None:
    lines = path.read_text().splitlines()
    path.write_text("\n".join(line.rstrip() for line in lines) + "\n")


def plot_ablation_summary(df: pd.DataFrame, output_dir: Path) -> None:
    summary = (
        df.groupby("method", as_index=False)["translation_p95_px"]
        .mean()
        .assign(method=lambda d: pd.Categorical(d["method"], METHOD_ORDER, ordered=True))
        .sort_values("translation_p95_px", ascending=True)
    )
    family = COLOR_FAMILIES["blue"]
    colors = [
        family["base"] if method == "Reference tracking" else NEUTRAL_MARKS["light"]
        for method in summary["method"].astype(str)
    ]
    edge_colors = [
        family["dark"] if method == "Reference tracking" else NEUTRAL_MARKS["mid"]
        for method in summary["method"].astype(str)
    ]
    fig, ax = plt.subplots(figsize=(8.6, 5.2))
    bars = ax.barh(summary["method"].astype(str), summary["translation_p95_px"], color=colors)
    for bar, edge_color, value in zip(bars, edge_colors, summary["translation_p95_px"], strict=True):
        bar.set_edgecolor(edge_color)
        ax.text(
            value + 0.03,
            bar.get_y() + bar.get_height() / 2,
            f"{value:.2f}px",
            ha="left",
            va="center",
            fontsize=8,
            color=TOKENS["ink"],
            family=MONO_FONT_FAMILY[0],
        )
    ax.set_xlabel("Mean p95 residual translation across scenarios, px")
    ax.set_ylabel("")
    ax.set_xlim(0, max(summary["translation_p95_px"]) * 1.18)
    ax.grid(axis="x", color=TOKENS["grid"])
    ax.grid(axis="y", visible=False)
    add_chart_header(
        fig,
        ax,
        "Reference tracking is the expected stability winner",
        "Mock final ablation summary; lower mean p95 adjacent-frame residual translation is better.",
    )
    save_figure(fig, output_dir, "mock_ablation_translation_bar")


def plot_scenario_heatmap(df: pd.DataFrame, output_dir: Path) -> None:
    pivot = (
        df.pivot(index="scenario", columns="method", values="translation_p95_px")
        .reindex(index=SCENARIO_ORDER, columns=METHOD_ORDER)
    )
    fig, ax = plt.subplots(figsize=(9.6, 5.8))
    cmap = mcolors.LinearSegmentedColormap.from_list(
        "orange_vector_heatmap",
        [TOKENS["panel"], COLOR_FAMILIES["orange"]["xlight"], COLOR_FAMILIES["orange"]["base"]],
    )
    norm = mcolors.Normalize(vmin=float(pivot.min().min()), vmax=float(pivot.max().max()))
    for y, scenario in enumerate(pivot.index):
        for x, method in enumerate(pivot.columns):
            value = float(pivot.loc[scenario, method])
            face = cmap(norm(value))
            ax.add_patch(
                Rectangle(
                    (x, y),
                    1,
                    1,
                    facecolor=face,
                    edgecolor=TOKENS["panel"],
                    linewidth=1.0,
                )
            )
            ax.text(
                x + 0.5,
                y + 0.5,
                f"{value:.2f}",
                ha="center",
                va="center",
                fontsize=8,
                color=TOKENS["ink"],
                family=MONO_FONT_FAMILY[0],
            )
    ax.set_xlim(0, len(pivot.columns))
    ax.set_ylim(len(pivot.index), 0)
    ax.set_xticks(np.arange(len(pivot.columns)) + 0.5, pivot.columns)
    ax.set_yticks(np.arange(len(pivot.index)) + 0.5, pivot.index)
    ax.set_xlabel("")
    ax.set_ylabel("")
    ax.tick_params(axis="x", labelrotation=25)
    ax.tick_params(axis="y", labelrotation=0)
    ax.grid(False)
    add_chart_header(
        fig,
        ax,
        "Hard cases remain measurable instead of anecdotal",
        "Mock scenario-by-method heatmap in p95 residual translation pixels; darker cells indicate larger residual motion.",
    )
    save_figure(fig, output_dir, "mock_scenario_method_heatmap")


def plot_signal_geometry_panel(df: pd.DataFrame, output_dir: Path) -> None:
    plot_df = df.loc[df["method"] == "Reference tracking"].copy()
    plot_df["quad_iou_pct"] = plot_df["quad_iou"] * 100.0
    fig, axes = plt.subplots(1, 3, figsize=(12.4, 4.8), sharey=True)
    metrics = [
        ("corner_rmse_px", "Corner RMSE", "px", COLOR_FAMILIES["orange"]),
        ("quad_iou_pct", "Quad IoU", "%", COLOR_FAMILIES["olive"]),
        ("edge_preservation_f1", "Edge preservation", "F1", COLOR_FAMILIES["blue"]),
    ]
    for ax, (metric, title, unit, family) in zip(axes, metrics, strict=True):
        data = plot_df.sort_values(metric, ascending=True)
        ax.scatter(
            data[metric],
            data["scenario"],
            s=90,
            facecolor=family["base"],
            edgecolor=family["dark"],
            linewidth=1.0,
            zorder=3,
        )
        ax.set_title(title, fontsize=9, color=TOKENS["ink"], pad=8)
        ax.set_xlabel(unit)
        ax.grid(axis="x", color=TOKENS["grid"])
        ax.grid(axis="y", color=TOKENS["grid"])
        if metric == "quad_iou_pct":
            ax.set_xlim(92, 100)
        elif metric == "edge_preservation_f1":
            ax.set_xlim(0.75, 1.0)
        else:
            ax.set_xlim(0, max(data[metric]) * 1.25)
        for value, scenario in zip(data[metric], data["scenario"], strict=True):
            label = f"{value:.1f}" if metric != "edge_preservation_f1" else f"{value:.2f}"
            ax.text(value, scenario, f"  {label}", va="center", fontsize=8, color=TOKENS["ink"])
    axes[0].set_ylabel("")
    for ax in axes[1:]:
        ax.set_ylabel("")
    add_chart_header(
        fig,
        axes[0],
        "Geometry and signal metrics should move together",
        "Mock reference-tracking results by scenario; exact values will come from annotated frames and warped source comparisons.",
    )
    save_figure(fig, output_dir, "mock_geometry_signal_panel")


def plot_frequency_diagnostics(df: pd.DataFrame, output_dir: Path) -> None:
    plot_df = (
        df.loc[df["method"] == "Reference tracking", ["scenario", "fft_orthogonality_error_deg"]]
        .set_index("scenario")
        .loc[SCENARIO_ORDER]
        .reset_index()
    )
    family = COLOR_FAMILIES["gold"]
    fig, ax = plt.subplots(figsize=(8.8, 5.2))
    bars = ax.barh(
        plot_df["scenario"],
        plot_df["fft_orthogonality_error_deg"],
        color=family["base"],
        edgecolor=family["dark"],
    )
    ax.axvline(1.0, color=TOKENS["ink"], linestyle=":", linewidth=1.0)
    ax.text(1.03, -0.52, "ideal target band", fontsize=8, color=TOKENS["muted"])
    for bar, value in zip(bars, plot_df["fft_orthogonality_error_deg"], strict=True):
        ax.text(
            value + 0.03,
            bar.get_y() + bar.get_height() / 2,
            f"{value:.2f}deg",
            ha="left",
            va="center",
            fontsize=8,
            color=TOKENS["ink"],
            family=MONO_FONT_FAMILY[0],
        )
    ax.set_xlabel("FFT orthogonality error, degrees")
    ax.set_ylabel("")
    ax.set_xlim(0, max(1.6, plot_df["fft_orthogonality_error_deg"].max() * 1.25))
    ax.grid(axis="x", color=TOKENS["grid"])
    ax.grid(axis="y", visible=False)
    add_chart_header(
        fig,
        ax,
        "FFT diagnostics turn grid regularity into a checkable metric",
        "Mock reference-tracking results; lower error means dominant frequency directions are closer to an orthogonal screen grid.",
    )
    save_figure(fig, output_dir, "mock_fft_orthogonality_bar")


def plot_stability_timeline(timeline: pd.DataFrame, output_dir: Path) -> None:
    fig, ax = plt.subplots(figsize=(10.4, 5.4))
    style_map = {
        "Frame-wise detection": ("--", NEUTRAL_MARKS["mid"]),
        "Content optical flow": (":", COLOR_FAMILIES["orange"]["base"]),
        "Reference tracking": ("-", COLOR_FAMILIES["blue"]["base"]),
        "Reference + residual align": ("-", COLOR_FAMILIES["olive"]["base"]),
    }
    for method in METHOD_ORDER:
        part = timeline.loc[timeline["method"] == method]
        line_style, color = style_map[method]
        ax.plot(
            part["frame"],
            part["translation_px"],
            label=method,
            linestyle=line_style,
            color=color,
            linewidth=1.2,
        )
    ax.set_xlabel("Frame")
    ax.set_ylabel("Adjacent-frame residual translation, px")
    ax.set_ylim(0, timeline["translation_px"].max() * 1.16)
    ax.legend(
        loc="lower left",
        bbox_to_anchor=(0, 1.02),
        frameon=False,
        ncol=2,
        borderaxespad=0,
    )
    add_chart_header(
        fig,
        ax,
        "Frame-level diagnostics show whether stability is sustained",
        "Mock static-page timeline; final plots should use real temporal_metrics.csv from the evaluation script.",
    )
    save_figure(fig, output_dir, "mock_temporal_stability_timeline")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate mock final metrics and SVG figures.")
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=None,
        help="Defaults to deliverables/final_20260622/mock_figures.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    output_dir = (
        args.output_dir.resolve()
        if args.output_dir is not None
        else project_root() / "deliverables" / "final_20260622" / "mock_figures"
    )
    output_dir.mkdir(parents=True, exist_ok=True)
    use_chart_theme()

    metrics = mock_metrics()
    timeline = mock_timeline()
    metrics.to_csv(output_dir / "mock_final_metrics.csv", index=False)
    timeline.to_csv(output_dir / "mock_temporal_metrics.csv", index=False)

    plot_ablation_summary(metrics, output_dir)
    plot_scenario_heatmap(metrics, output_dir)
    plot_signal_geometry_panel(metrics, output_dir)
    plot_frequency_diagnostics(metrics, output_dir)
    plot_stability_timeline(timeline, output_dir)

    print(f"wrote mock metrics and SVG figures to {output_dir}")


if __name__ == "__main__":
    main()
