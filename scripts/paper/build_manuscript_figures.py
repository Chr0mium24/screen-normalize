#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
from pathlib import Path
from typing import Any

import cv2
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import numpy as np
from matplotlib import patches

from screen_normalize.experiments.annotations import load_annotations
from screen_normalize.experiments.paper_style import apply_paper_style


CATEGORIES = ("static", "screen_video", "scrolling", "weak_border", "hard")
METHODS = ("frame_wise", "optical_flow", "proposed")
METHOD_LABELS = {
    "frame_wise": "Frame-wise",
    "optical_flow": "Optical flow",
    "proposed": "Proposed",
    "no_reliability_gates": "w/o gates",
    "no_trajectory_smoothing": "w/o smoothing",
    "no_offline_repair": "w/o repair",
}
METHOD_COLORS = {
    "frame_wise": "#5B6470",
    "optical_flow": "#7C8FB8",
    "proposed": "#0F4D92",
    "no_reliability_gates": "#B8842D",
    "no_trajectory_smoothing": "#7C8FB8",
    "no_offline_repair": "#806491",
}
METHOD_MARKERS = {
    "frame_wise": "o",
    "optical_flow": "s",
    "proposed": "D",
    "no_reliability_gates": "^",
    "no_trajectory_smoothing": "v",
    "no_offline_repair": "P",
}
CATEGORY_LABELS = {
    "static": "Static",
    "screen_video": "Screen video",
    "scrolling": "Scrolling",
    "weak_border": "Weak border",
    "hard": "Hard",
}
GRID = "#D9DDDF"
TEXT = "#242729"

def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build manuscript figures from first-pass outputs.")
    parser.add_argument("--input", type=Path, default=Path("inputs"))
    parser.add_argument("--main-run", type=Path, default=Path("runs/20260714_full_pipeline_first_pass"))
    parser.add_argument("--results", type=Path, default=Path("doc/paper/results"))
    parser.add_argument("--output", type=Path, default=Path("doc/paper/manuscript/figures"))
    parser.add_argument("--dpi", type=int, default=300)
    return parser.parse_args()

def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))

def frame_count(video: Path) -> int:
    capture = cv2.VideoCapture(str(video))
    count = int(capture.get(cv2.CAP_PROP_FRAME_COUNT) or 0)
    capture.release()
    return count

def read_frame(video: Path, frame: int) -> np.ndarray:
    capture = cv2.VideoCapture(str(video))
    if not capture.isOpened():
        raise RuntimeError(f"could not open {video}")
    capture.set(cv2.CAP_PROP_POS_FRAMES, max(0, frame))
    ok, image = capture.read()
    capture.release()
    if not ok:
        raise RuntimeError(f"could not read frame {frame} from {video}")
    return cv2.cvtColor(image, cv2.COLOR_BGR2RGB)

def video_size(video: Path) -> tuple[int, int]:
    capture = cv2.VideoCapture(str(video))
    width = int(capture.get(cv2.CAP_PROP_FRAME_WIDTH) or 0)
    height = int(capture.get(cv2.CAP_PROP_FRAME_HEIGHT) or 0)
    capture.release()
    return width, height

def annotation_frame(video: Path, prefer_nonzero: bool = True) -> tuple[int, np.ndarray | None]:
    csv_path = video.with_suffix(".csv")
    if not csv_path.exists():
        return min(120, max(0, frame_count(video) - 1)), None
    width, height = video_size(video)
    annotations = load_annotations(csv_path, width, height)
    if not annotations:
        return min(120, max(0, frame_count(video) - 1)), None
    frames = sorted(annotations)
    if prefer_nonzero:
        frames = [frame for frame in frames if frame != 0] or sorted(annotations)
    frame = frames[len(frames) // 2]
    return frame, annotations[frame]

def corners_at(csv_path: Path, frame: int) -> np.ndarray | None:
    if not csv_path.exists():
        return None
    best: tuple[int, np.ndarray] | None = None
    for row in read_csv(csv_path):
        try:
            current = int(row["frame"])
            corners = np.asarray(
                [
                    [float(row["tl_x"]), float(row["tl_y"])],
                    [float(row["tr_x"]), float(row["tr_y"])],
                    [float(row["br_x"]), float(row["br_y"])],
                    [float(row["bl_x"]), float(row["bl_y"])],
                ],
                dtype=np.float32,
            )
        except (KeyError, ValueError):
            continue
        distance = abs(current - frame)
        if best is None or distance < best[0]:
            best = (distance, corners)
    return best[1] if best else None

def overlay_corners(image: np.ndarray, corners: np.ndarray | None, color: tuple[int, int, int] = (15, 77, 146)) -> np.ndarray:
    if corners is None:
        return image
    canvas = cv2.cvtColor(image.copy(), cv2.COLOR_RGB2BGR)
    points = np.round(corners).astype(np.int32)
    cv2.polylines(canvas, [points], True, color, 5, cv2.LINE_AA)
    for point in points:
        cv2.circle(canvas, tuple(point), 10, (255, 255, 255), -1, cv2.LINE_AA)
        cv2.circle(canvas, tuple(point), 10, color, 3, cv2.LINE_AA)
    return cv2.cvtColor(canvas, cv2.COLOR_BGR2RGB)

def show_image(axis: plt.Axes, image: np.ndarray, title: str) -> None:
    axis.imshow(image)
    axis.set_title(title, fontsize=7.8, pad=3)
    axis.axis("off")

def save(fig: plt.Figure, output: Path, dpi: int) -> None:
    output.parent.mkdir(parents=True, exist_ok=True)
    base = output.with_suffix("")
    fig.savefig(base.with_suffix(".svg"), bbox_inches="tight")
    fig.savefig(base.with_suffix(".pdf"), bbox_inches="tight")
    fig.savefig(base.with_suffix(".png"), dpi=dpi, bbox_inches="tight")
    plt.close(fig)

def normalized_frame(run: Path, category: str, clip: str, method: str, frame: int) -> np.ndarray:
    return read_frame(run / category / clip / method / "normalized.mp4", frame)

def add_panel_label(axis: plt.Axes, label: str, color: str = TEXT) -> None:
    axis.text(-0.04, 1.04, label, transform=axis.transAxes, ha="left", va="bottom", fontsize=9, fontweight="bold", color=color)

def median_value(rows: list[dict[str, str]], field: str, **filters: str) -> float:
    values = []
    for row in rows:
        if any(row.get(key) != value for key, value in filters.items()):
            continue
        try:
            values.append(float(row[field]))
        except (KeyError, TypeError, ValueError):
            continue
    return float(np.median(values)) if values else float("nan")

def style_metric_axis(axis: plt.Axes, title: str, ylabel: str = "") -> None:
    axis.set_title(title, loc="left", fontsize=8.5, fontweight="bold")
    if ylabel:
        axis.set_ylabel(ylabel)
    axis.grid(axis="y", color=GRID, linewidth=0.55)
    axis.spines[["top", "right"]].set_visible(False)
    axis.set_axisbelow(True)

def draw_pipeline(axis: plt.Axes) -> None:
    axis.set_axis_off()
    labels = [
        "Frame-0\ncorners",
        "Reference\nLK tracks",
        "RANSAC\nhomography",
        "Reliability\ngates",
        "Repair and\nsmoothing",
        "Frontal\nrendering",
    ]
    x0, width, gap = 0.02, 0.135, 0.032
    for index, label in enumerate(labels):
        x = x0 + index * (width + gap)
        color = "#E8EEF6" if index != 3 else "#F7E7C6"
        box = patches.FancyBboxPatch(
            (x, 0.28),
            width,
            0.44,
            boxstyle="round,pad=0.012,rounding_size=0.018",
            linewidth=0.9,
            edgecolor="#65717C",
            facecolor=color,
        )
        axis.add_patch(box)
        axis.text(x + width / 2, 0.50, label, ha="center", va="center", fontsize=8, color=TEXT)
        if index < len(labels) - 1:
            axis.annotate("", xy=(x + width + gap * 0.70, 0.50), xytext=(x + width, 0.50), arrowprops={"arrowstyle": "->", "lw": 1.0, "color": "#65717C"})
    axis.text(0.02, 0.94, "Reference-anchored screen-plane normalization", ha="left", va="top", fontsize=9.5, fontweight="bold", color=TEXT)
    axis.text(0.02, 0.10, "The implemented system favors explicit update acceptance over unconstrained frame-to-frame motion.", ha="left", va="bottom", fontsize=7.8, color="#5B6470")

def figure_01(args: argparse.Namespace) -> None:
    category, clip = "static", "static_01"
    video = args.input / category / f"{clip}.mp4"
    frame, gt = annotation_frame(video, prefer_nonzero=True)
    input_frame = read_frame(video, frame)
    estimate = corners_at(args.main_run / category / clip / "proposed" / "estimated_corners.csv", frame)
    proposed = normalized_frame(args.main_run, category, clip, "proposed", frame)
    optical = normalized_frame(args.main_run, category, clip, "optical_flow", frame)
    fig = plt.figure(figsize=(7.2, 2.85), constrained_layout=True)
    grid = fig.add_gridspec(2, 4, height_ratios=[0.58, 1.25])
    ax_flow = fig.add_subplot(grid[0, :])
    draw_pipeline(ax_flow)
    panels = [
        (input_frame, "Input frame"),
        (overlay_corners(input_frame, estimate), "Estimated screen plane"),
        (optical, "Optical-flow output"),
        (proposed, "Proposed output"),
    ]
    for index, (image, title) in enumerate(panels):
        axis = fig.add_subplot(grid[1, index])
        show_image(axis, image, title)
        add_panel_label(axis, chr(ord("a") + index))
    if gt is None:
        ax_flow.text(0.98, 0.10, "No non-initialization annotation for selected frame", ha="right", va="bottom", fontsize=7)
    save(fig, args.output / "figure_01_pipeline.png", args.dpi)

def figure_02(args: argparse.Namespace) -> None:
    frame_counts = [sum(frame_count(path) for path in sorted((args.input / category).glob("*.mp4"))) for category in CATEGORIES]
    fig = plt.figure(figsize=(7.2, 4.9), constrained_layout=True)
    grid = fig.add_gridspec(2, 5, height_ratios=[0.9, 1.4])
    axis = fig.add_subplot(grid[0, :])
    bars = axis.bar(range(len(CATEGORIES)), frame_counts, color="#AFC4DD", edgecolor="#354052", linewidth=0.8)
    for bar, value in zip(bars, frame_counts):
        axis.text(bar.get_x() + bar.get_width() / 2, value + 55, f"{value}", ha="center", va="bottom", fontsize=7.5)
    axis.set_xticks(range(len(CATEGORIES)), [CATEGORY_LABELS[c] for c in CATEGORIES], rotation=15, ha="right")
    axis.set_ylabel("Frames")
    style_metric_axis(axis, "a  Fifty clips across five capture conditions")
    for col, category in enumerate(CATEGORIES):
        clip = f"{category}_01"
        video = args.input / category / f"{clip}.mp4"
        frame, corners = annotation_frame(video, prefer_nonzero=True)
        ax_img = fig.add_subplot(grid[1, col])
        show_image(ax_img, overlay_corners(read_frame(video, frame), corners), CATEGORY_LABELS[category])
        add_panel_label(ax_img, chr(ord("b") + col))
    save(fig, args.output / "figure_02_dataset.png", args.dpi)


def aggregate_metric(rows: list[dict[str, str]], metric: str, method: str, field: str = "median") -> float:
    for row in rows:
        if row["metric"] == metric and row["method"] == method:
            return float(row[field])
    return float("nan")


def iqr_bar(axis: plt.Axes, rows: list[dict[str, str]], metric: str, title: str, ylabel: str) -> None:
    values = np.asarray([aggregate_metric(rows, metric, method, "median") for method in METHODS])
    q1 = np.asarray([aggregate_metric(rows, metric, method, "q1") for method in METHODS])
    q3 = np.asarray([aggregate_metric(rows, metric, method, "q3") for method in METHODS])
    yerr = np.vstack([values - q1, q3 - values])
    x = np.arange(len(METHODS))
    axis.bar(x, values, yerr=yerr, color=[METHOD_COLORS[m] for m in METHODS], edgecolor="#2B2B2B", linewidth=0.7, capsize=3)
    axis.set_xticks(x, [METHOD_LABELS[m] for m in METHODS], rotation=18, ha="right")
    style_metric_axis(axis, title, ylabel)


def figure_03(args: argparse.Namespace) -> None:
    rows = read_csv(args.results / "full_pipeline_first_pass" / "aggregate_metrics.csv")
    fig = plt.figure(figsize=(7.2, 5.0), constrained_layout=True)
    grid = fig.add_gridspec(2, 3, width_ratios=[1.35, 1.0, 1.0])
    ax = fig.add_subplot(grid[:, 0])
    offsets = {"frame_wise": (10, 4), "optical_flow": (8, -12), "proposed": (-66, 10)}
    for method in METHODS:
        rmse = aggregate_metric(rows, "geometry", method)
        temporal = aggregate_metric(rows, "temporal", method)
        edge = aggregate_metric(rows, "detail", method)
        size = 380 + 780 * max(edge, 0)
        ax.scatter(rmse, temporal, s=size, marker=METHOD_MARKERS[method], color=METHOD_COLORS[method], edgecolor="white", linewidth=1.2, zorder=3)
        ax.annotate(METHOD_LABELS[method], (rmse, temporal), xytext=offsets[method], textcoords="offset points", fontsize=8, color=TEXT)
    ax.set_xscale("log")
    ax.set_yscale("log")
    ax.set_xlabel("Median corner RMSE (px, lower is better)")
    ax.set_ylabel("Median translation variation (px/frame, lower is better)")
    ax.set_xlim(25, 250)
    ax.set_ylim(0.16, 20)
    ax.xaxis.set_major_locator(mticker.FixedLocator([30, 50, 100, 200]))
    ax.xaxis.set_major_formatter(mticker.FixedFormatter(["30", "50", "100", "200"]))
    ax.xaxis.set_minor_formatter(mticker.NullFormatter())
    ax.set_title("a  Main trade-off", loc="left", fontsize=9, fontweight="bold")
    ax.grid(color=GRID, linewidth=0.55, which="both")
    ax.spines[["top", "right"]].set_visible(False)
    ax.text(0.04, 0.03, "Bubble area encodes edge preservation", transform=ax.transAxes, fontsize=7.4, color="#5B6470")
    iqr_bar(fig.add_subplot(grid[0, 1]), rows, "geometry", "b  Geometry", "RMSE px")
    iqr_bar(fig.add_subplot(grid[0, 2]), rows, "temporal", "c  Trajectory", "px/frame")
    iqr_bar(fig.add_subplot(grid[1, 1]), rows, "detail", "d  Edge preservation", "F1")
    iqr_bar(fig.add_subplot(grid[1, 2]), rows, "frequency", "e  FFT orthogonality", "deg")
    save(fig, args.output / "figure_03_core_tradeoff.png", args.dpi)


def heatmap(axis: plt.Axes, data: np.ndarray, row_labels: list[str], col_labels: list[str], title: str, cbar_label: str, fmt: str, log_color: bool = False) -> None:
    color_data = np.log10(np.maximum(data, 1e-6)) if log_color else data
    image = axis.imshow(color_data, aspect="auto", cmap="YlGnBu_r")
    axis.set_xticks(np.arange(len(col_labels)), col_labels, rotation=20, ha="right")
    axis.set_yticks(np.arange(len(row_labels)), row_labels)
    axis.set_title(title, loc="left", fontsize=8.5, fontweight="bold")
    for row in range(data.shape[0]):
        for col in range(data.shape[1]):
            value = data[row, col]
            text = "NA" if np.isnan(value) else fmt.format(value)
            rgba = image.cmap(image.norm(color_data[row, col]))
            luminance = 0.299 * rgba[0] + 0.587 * rgba[1] + 0.114 * rgba[2]
            color = "white" if luminance < 0.46 else "#1F1F1F"
            axis.text(col, row, text, ha="center", va="center", fontsize=7, color=color)
    axis.tick_params(length=0)
    for spine in axis.spines.values():
        spine.set_visible(False)
    cbar = axis.figure.colorbar(image, ax=axis, fraction=0.046, pad=0.03)
    cbar.set_label(cbar_label, fontsize=7.5)


def debug_acceptance(run: Path, category: str, clip: str) -> tuple[np.ndarray, str]:
    rows = read_csv(run / category / clip / "proposed" / "debug.csv")
    accepted = np.asarray([1.0 if row.get("accepted") == "True" else 0.0 for row in rows], dtype=float)
    label = f"{int(accepted.sum())}/{len(accepted)} accepted"
    return accepted, label


def acceptance_ratio(run: Path, category: str, clip: str) -> float:
    accepted, _ = debug_acceptance(run, category, clip)
    return float(np.mean(accepted)) if accepted.size else float("nan")


def figure_04(args: argparse.Namespace) -> None:
    geom = read_csv(args.results / "full_pipeline_first_pass" / "geometry_table.csv")
    temporal = read_csv(args.results / "full_pipeline_first_pass" / "temporal_table.csv")
    rmse = np.asarray([[median_value(geom, "corner_rmse_px_mean", category=cat, method=method, status="ok") for method in METHODS] for cat in CATEGORIES])
    trans = np.asarray([[median_value(temporal, "translation_px_mean", category=cat, method=method, status="ok") for method in METHODS] for cat in CATEGORIES])
    accept = np.asarray([[acceptance_ratio(args.main_run, cat, f"{cat}_{index:02d}") for index in range(1, 11)] for cat in CATEGORIES])
    accept = np.asarray([[np.nanmedian(row)] for row in accept])
    labels = [CATEGORY_LABELS[c] for c in CATEGORIES]
    fig, axes = plt.subplots(1, 3, figsize=(7.2, 3.7), constrained_layout=True)
    heatmap(axes[0], rmse, labels, [METHOD_LABELS[m] for m in METHODS], "a  Geometry stress", "log10 px", "{:.0f}", log_color=True)
    heatmap(axes[1], trans, labels, [METHOD_LABELS[m] for m in METHODS], "b  Trajectory stress", "log10 px/frame", "{:.2f}", log_color=True)
    heatmap(axes[2], accept, labels, ["Proposed"], "c  Accepted updates", "ratio", "{:.2f}")
    save(fig, args.output / "figure_04_category_stress.png", args.dpi)


def figure_05(args: argparse.Namespace) -> None:
    cases = [
        ("static", "static_02"),
        ("screen_video", "screen_video_08"),
        ("scrolling", "scrolling_05"),
        ("weak_border", "weak_border_03"),
        ("hard", "hard_01"),
    ]
    fig, axes = plt.subplots(len(cases), 4, figsize=(7.2, 8.2), constrained_layout=True)
    for row, (category, clip) in enumerate(cases):
        video = args.input / category / f"{clip}.mp4"
        frame, corners = annotation_frame(video, prefer_nonzero=True)
        show_image(axes[row, 0], overlay_corners(read_frame(video, frame), corners), CATEGORY_LABELS[category])
        for col, method in enumerate(METHODS, start=1):
            show_image(axes[row, col], normalized_frame(args.main_run, category, clip, method, frame), METHOD_LABELS[method] if row == 0 else "")
    axes[0, 0].set_title("Input + annotation", fontsize=7.8, pad=3)
    save(fig, args.output / "figure_05_qualitative.png", args.dpi)


def box_panel(axis: plt.Axes, rows: list[dict[str, str]], metric: str, field: str, title: str, ylabel: str) -> None:
    samples: list[list[float]] = []
    for method in METHODS:
        samples.append([float(row[field]) for row in rows if row["metric"] == metric and row["method"] == method and row["status"] == "ok" and row.get(field)])
    plot = axis.boxplot(samples, patch_artist=True, tick_labels=[METHOD_LABELS[m] for m in METHODS], showmeans=True, widths=0.55)
    for patch, method in zip(plot["boxes"], METHODS):
        patch.set_facecolor(METHOD_COLORS[method])
        patch.set_alpha(0.78)
    axis.tick_params(axis="x", rotation=16)
    style_metric_axis(axis, title, ylabel)


def figure_06(args: argparse.Namespace) -> None:
    rows = read_csv(args.results / "full_pipeline_first_pass" / "all_metrics.csv")
    fig, axes = plt.subplots(1, 3, figsize=(7.2, 3.1), constrained_layout=True)
    box_panel(axes[0], rows, "detail", "edge_preservation_index_mean", "a  Edge preservation", "F1")
    box_panel(axes[1], rows, "detail", "gradient_magnitude_ratio_mean", "b  Gradient ratio", "ratio")
    box_panel(axes[2], rows, "frequency", "fft_orthogonality_error_deg_mean", "c  FFT orthogonality", "deg")
    save(fig, args.output / "figure_06_detail_frequency.png", args.dpi)


def ablation_value(rows: list[dict[str, str]], method: str, field: str) -> float:
    for row in rows:
        if row["method"] == method and row["field"] == field:
            return float(row["median"])
    return float("nan")


def figure_07(args: argparse.Namespace) -> None:
    rows = read_csv(args.results / "full_ablation_first_pass" / "ablation_aggregate_metrics.csv")
    methods = ("proposed", "no_reliability_gates", "no_trajectory_smoothing", "no_offline_repair")
    fig = plt.figure(figsize=(7.2, 3.9), constrained_layout=True)
    grid = fig.add_gridspec(1, 3, width_ratios=[1.25, 1.0, 1.0])
    ax = fig.add_subplot(grid[0, 0])
    offsets = {
        "proposed": (8, 8),
        "no_reliability_gates": (8, 8),
        "no_trajectory_smoothing": (8, -2),
        "no_offline_repair": (8, -14),
    }
    for method in methods:
        rmse = ablation_value(rows, method, "corner_rmse_px")
        trans = ablation_value(rows, method, "translation_px")
        edge = ablation_value(rows, method, "edge_preservation_index")
        ax.scatter(rmse, trans, s=260 + 650 * max(edge, 0), marker=METHOD_MARKERS[method], color=METHOD_COLORS[method], edgecolor="white", linewidth=1.0)
        ax.annotate(METHOD_LABELS[method], (rmse, trans), xytext=offsets[method], textcoords="offset points", fontsize=7.5)
    ax.set_xscale("log")
    ax.set_yscale("log")
    ax.set_xlabel("Median RMSE (px)")
    ax.set_ylabel("Median translation variation")
    ax.set_xlim(30, 260)
    ax.set_ylim(0.18, 8.5)
    ax.xaxis.set_major_locator(mticker.FixedLocator([40, 100, 200]))
    ax.xaxis.set_major_formatter(mticker.FixedFormatter(["40", "100", "200"]))
    ax.xaxis.set_minor_formatter(mticker.NullFormatter())
    ax.set_title("a  Gate-driven trade-off", loc="left", fontsize=8.5, fontweight="bold")
    ax.grid(color=GRID, linewidth=0.55, which="both")
    ax.spines[["top", "right"]].set_visible(False)
    for col, (field, title, ylabel) in enumerate([("quad_iou", "b  Geometry fit", "IoU"), ("edge_preservation_index", "c  Local structure", "F1")], start=1):
        axis = fig.add_subplot(grid[0, col])
        values = [ablation_value(rows, method, field) for method in methods]
        axis.barh(np.arange(len(methods)), values, color=[METHOD_COLORS[m] for m in methods], edgecolor="#2B2B2B", linewidth=0.6)
        axis.set_yticks(np.arange(len(methods)), [METHOD_LABELS[m] for m in methods])
        axis.invert_yaxis()
        style_metric_axis(axis, title, ylabel)
    save(fig, args.output / "figure_07_ablation.png", args.dpi)


def parse_ratio(text: str) -> float:
    left, right = text.split("/")
    return float(left) / float(right)


def tuning_lookup(path: Path) -> dict[str, dict[str, str]]:
    if not path.exists():
        return {}
    return {row["clip"]: row for row in read_csv(path)}


def figure_08(args: argparse.Namespace) -> None:
    cases = [
        ("hard", "hard_01", "Hard sample"),
        ("weak_border", "weak_border_10", "Weak-border sample"),
        ("scrolling", "scrolling_10", "Scrolling sample"),
    ]
    tuned = tuning_lookup(args.results / "proposed_tuning_smoke.csv")
    fig, axes = plt.subplots(len(cases), 4, figsize=(7.2, 6.1), constrained_layout=True)
    for row, (category, clip, title) in enumerate(cases):
        video = args.input / category / f"{clip}.mp4"
        frame = min(150, frame_count(video) - 1)
        image = read_frame(video, frame)
        estimate = corners_at(args.main_run / category / clip / "proposed" / "estimated_corners.csv", frame)
        show_image(axes[row, 0], overlay_corners(image, estimate, color=(182, 67, 66)), title)
        show_image(axes[row, 1], normalized_frame(args.main_run, category, clip, "proposed", frame), "Original Proposed output" if row == 0 else "")
        accepted, label = debug_acceptance(args.main_run, category, clip)
        axes[row, 2].plot(np.arange(len(accepted)), accepted, color=METHOD_COLORS["proposed"], linewidth=1.0)
        axes[row, 2].set_ylim(-0.08, 1.08)
        axes[row, 2].set_title(label, fontsize=7.8, pad=3)
        axes[row, 2].set_xlabel("Frame")
        axes[row, 2].set_ylabel("Accepted")
        axes[row, 2].grid(color=GRID, linewidth=0.55)
        axes[row, 2].spines[["top", "right"]].set_visible(False)
        smoke = tuned.get(clip)
        values = [parse_ratio(smoke["accept_old"]), parse_ratio(smoke["accept_tuned"])] if smoke else [float(np.mean(accepted)), float("nan")]
        axes[row, 3].bar([0, 1], values, color=["#CFCECE", "#0F4D92"], edgecolor="#2B2B2B", linewidth=0.6)
        axes[row, 3].set_xticks([0, 1], ["Old", "Tuned"])
        axes[row, 3].set_ylim(0, 1.05)
        style_metric_axis(axes[row, 3], "Smoke acceptance" if row == 0 else "", "ratio")
    save(fig, args.output / "figure_08_failures.png", args.dpi)


def main() -> int:
    args = parse_args()
    args.output.mkdir(parents=True, exist_ok=True)
    apply_paper_style()
    builders = (figure_01, figure_02, figure_03, figure_04, figure_05, figure_06, figure_07, figure_08)
    for builder in builders:
        builder(args)
    print(f"wrote manuscript figures to {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
