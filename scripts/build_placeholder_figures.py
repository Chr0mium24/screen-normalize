#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.patches import FancyArrowPatch, Polygon, Rectangle

from screen_normalize.experiments.paper_style import (
    GRID_COLOR,
    METHOD_COLORS,
    METHOD_LINES,
    METHOD_MARKERS,
    apply_paper_style,
)


ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "doc" / "paper" / "manuscript" / "figures" / "placeholders"
METHODS = ("Frame-wise", "Optical flow", "Proposed")
METHOD_IDS = ("frame_wise", "optical_flow", "proposed")
COLORS = tuple(METHOD_COLORS[method] for method in METHOD_IDS)
CATEGORIES = ("Static", "Scrolling", "Screen video", "Weak border", "Hard")


def setup() -> None:
    OUTPUT.mkdir(parents=True, exist_ok=True)
    apply_paper_style()


def finish(figure: plt.Figure, name: str) -> None:
    figure.text(
        0.5,
        -0.055,
        "PLACEHOLDER - ALL VALUES ARE 1.0 - REPLACE FROM THE REVIEWED FORMAL RUN",
        ha="center",
        color="#A61B1B",
        fontsize=7,
        fontweight="bold",
    )
    figure.savefig(OUTPUT / name, bbox_inches="tight")
    plt.close(figure)


def panel_label(axis: plt.Axes, label: str, title: str) -> None:
    axis.set_title(f"({label}) {title}", loc="left", fontweight="bold")


def placeholder_frame(axis: plt.Axes, title: str, corners: bool = False) -> None:
    axis.add_patch(Rectangle((0, 0), 1, 1, facecolor="#ECEFF1", edgecolor="#89939B"))
    axis.add_patch(Rectangle((0.12, 0.15), 0.76, 0.68, facecolor="#D8DEE2", edgecolor="#5D6870"))
    axis.text(0.5, 0.5, "IMAGE\nTBD", ha="center", va="center", color="#5D6870", fontweight="bold")
    if corners:
        points = np.asarray([[0.15, 0.2], [0.86, 0.17], [0.83, 0.79], [0.13, 0.82]])
        axis.add_patch(Polygon(points, closed=True, fill=False, edgecolor="#D1495B", linewidth=1.5))
        axis.scatter(points[:, 0], points[:, 1], s=10, color="#D1495B")
    axis.set_title(title, fontsize=8)
    axis.set_xlim(0, 1)
    axis.set_ylim(0, 1)
    axis.set_aspect("equal")
    axis.axis("off")


def figure_1() -> None:
    figure, axes = plt.subplots(1, 5, figsize=(7.2, 1.8), constrained_layout=True)
    labels = ("Input frames", "Screen plane", "Homography", "Rectification", "Stabilized output")
    for index, (axis, label) in enumerate(zip(axes, labels)):
        placeholder_frame(axis, f"({chr(97 + index)}) {label}", corners=index in (1, 2))
        if index < 4:
            figure.add_artist(FancyArrowPatch((0.19 + 0.195 * index, 0.5), (0.225 + 0.195 * index, 0.5), transform=figure.transFigure, arrowstyle="-|>", mutation_scale=10, color="#444"))
    finish(figure, "figure_01_pipeline.svg")


def figure_2() -> None:
    figure, axes = plt.subplots(2, 5, figsize=(7.2, 3.0), constrained_layout=True)
    for column, category in enumerate(CATEGORIES):
        placeholder_frame(axes[0, column], category)
        placeholder_frame(axes[1, column], f"{category} + corners", corners=True)
    axes[0, 0].text(-0.22, 0.5, "Examples", rotation=90, va="center", transform=axes[0, 0].transAxes, fontweight="bold")
    axes[1, 0].text(-0.22, 0.5, "Annotations", rotation=90, va="center", transform=axes[1, 0].transAxes, fontweight="bold")
    finish(figure, "figure_02_dataset.svg")


def style_numeric(axis: plt.Axes, ylabel: str) -> None:
    x = np.arange(len(CATEGORIES))
    width = 0.24
    for index, (method, color) in enumerate(zip(METHODS, COLORS)):
        axis.bar(x + (index - 1) * width, np.ones(len(x)), width, label=method, color=color, edgecolor="white")
    axis.set_xticks(x, CATEGORIES, rotation=20, ha="right")
    axis.set_ylabel(ylabel)
    axis.set_ylim(0, 1.35)
    axis.grid(axis="y", color=GRID_COLOR, linewidth=0.6)
    axis.spines[["top", "right"]].set_visible(False)


def figure_3() -> None:
    figure, axes = plt.subplots(1, 3, figsize=(7.2, 2.4), constrained_layout=True)
    for label, axis, title, unit in zip("abc", axes, ("Corner error", "Quadrilateral IoU", "Aspect-ratio error"), ("Error (px)", "IoU", "Relative error")):
        style_numeric(axis, unit)
        panel_label(axis, label, title)
    handles, names = axes[0].get_legend_handles_labels()
    figure.legend(handles, names, loc="upper center", bbox_to_anchor=(0.5, 1.08), ncol=3, frameon=False)
    finish(figure, "figure_03_quantitative.svg")


def figure_4() -> None:
    figure, axes = plt.subplots(1, 3, figsize=(7.2, 2.3), constrained_layout=True)
    frames = np.arange(150)
    for label, axis, title, unit in zip("abc", axes, ("Translation", "Rotation", "Scale"), ("Translation (px)", "Rotation (deg)", "Scale change (%)")):
        for method, method_id, color in zip(METHODS, METHOD_IDS, COLORS):
            axis.plot(
                frames,
                np.ones_like(frames),
                label=method,
                color=color,
                linestyle=METHOD_LINES[method_id],
                marker=METHOD_MARKERS[method_id],
                markevery=35,
                markersize=2.8,
                linewidth=1.25 if method_id == "proposed" else 0.95,
            )
        panel_label(axis, label, title)
        axis.set_xlabel("Frame")
        axis.set_ylabel(unit)
        axis.set_ylim(0.5, 1.5)
        axis.grid(color=GRID_COLOR, linewidth=0.6)
        axis.spines[["top", "right"]].set_visible(False)
    handles, names = axes[0].get_legend_handles_labels()
    figure.legend(handles, names, loc="upper center", bbox_to_anchor=(0.5, 1.08), ncol=3, frameon=False)
    finish(figure, "figure_04_temporal.svg")


def figure_5() -> None:
    columns = ("Input", *METHODS)
    figure, axes = plt.subplots(5, 4, figsize=(7.2, 6.7), constrained_layout=True)
    for row, category in enumerate(CATEGORIES):
        for column, title in enumerate(columns):
            placeholder_frame(axes[row, column], title if row == 0 else "")
        axes[row, 0].text(-0.25, 0.5, category, rotation=90, va="center", transform=axes[row, 0].transAxes, fontweight="bold")
    finish(figure, "figure_05_qualitative.svg")


def figure_6() -> None:
    figure = plt.figure(figsize=(7.2, 4.2), constrained_layout=True)
    grid = figure.add_gridspec(2, 4)
    crop_axes = [figure.add_subplot(grid[0, index]) for index in range(4)]
    for axis, title in zip(crop_axes, ("Reference", *METHODS)):
        placeholder_frame(axis, title)
    bar_axis = figure.add_subplot(grid[1, :2])
    bar_axis.bar(METHODS, np.ones(3), color=COLORS)
    bar_axis.set_ylim(0, 1.35)
    bar_axis.set_ylabel("Edge preservation index")
    panel_label(bar_axis, "b", "Aligned detail metric")
    bar_axis.spines[["top", "right"]].set_visible(False)
    fft_axes = [figure.add_subplot(grid[1, index]) for index in (2, 3)]
    for axis, title in zip(fft_axes, ("Original FFT", "Rectified FFT")):
        placeholder_frame(axis, title)
        axis.plot([0.2, 0.8], [0.5, 0.5], color="#806491")
        axis.plot([0.5, 0.5], [0.2, 0.8], color="#806491")
    crop_axes[0].text(-0.18, 1.12, "(a) Aligned texture crops", transform=crop_axes[0].transAxes, fontweight="bold")
    fft_axes[0].text(-0.18, 1.12, "(c) Frequency diagnostics", transform=fft_axes[0].transAxes, fontweight="bold")
    finish(figure, "figure_06_detail_frequency.svg")


def figure_7() -> None:
    figure, axis = plt.subplots(figsize=(7.2, 2.8), constrained_layout=True)
    variants = ("Full", "w/o gates", "w/o smoothing", "w/o recovery")
    axis.bar(variants, np.ones(4), color=(METHOD_COLORS["proposed"], "#806491", "#6F7478", "#B55D5D"), width=0.62)
    axis.set_ylabel("Primary metric (TBD)")
    axis.set_ylim(0, 1.35)
    axis.grid(axis="y", color=GRID_COLOR, linewidth=0.6)
    axis.spines[["top", "right"]].set_visible(False)
    panel_label(axis, "a", "Code-matched ablation")
    finish(figure, "figure_07_ablation.svg")


def figure_8() -> None:
    figure, axes = plt.subplots(3, 3, figsize=(7.2, 5.8), constrained_layout=True)
    rows = ("Glare / weak evidence", "Partial occlusion", "Fast motion / blur")
    columns = ("Input + estimate", "Rectified output", "Diagnostic")
    for row, row_name in enumerate(rows):
        for column, title in enumerate(columns):
            placeholder_frame(axes[row, column], title if row == 0 else "", corners=column == 0)
        axes[row, 0].text(-0.22, 0.5, row_name, rotation=90, va="center", transform=axes[row, 0].transAxes, fontweight="bold")
    finish(figure, "figure_08_failures.svg")


def main() -> None:
    setup()
    for function in (figure_1, figure_2, figure_3, figure_4, figure_5, figure_6, figure_7, figure_8):
        function()
    print(f"wrote placeholder figures to {OUTPUT}")


if __name__ == "__main__":
    main()
