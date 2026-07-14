#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
from typing import Any

import cv2
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import numpy as np
from matplotlib import patches
from matplotlib.colors import LinearSegmentedColormap

from screen_normalize.experiments.annotations import load_annotations
from screen_normalize.experiments.paper_style import apply_paper_style


CATEGORIES = ("static", "scrolling", "screen_video", "weak_border", "hard")
EVAL_CLIPS = {
    "static": ("static_01", "static_02"),
    "scrolling": ("scrolling_01", "scrolling_02"),
    "screen_video": ("screen_video_01", "screen_video_02"),
    "weak_border": ("weak_border_01", "weak_border_02"),
    "hard": ("hard_01", "hard_02"),
}
METHODS = ("frame_wise", "optical_flow", "proposal_border")
PROPOSED_METHOD = "proposal_border"
METHOD_LABELS = {
    "frame_wise": "Frame-wise",
    "optical_flow": "Optical flow",
    "proposal_border": "Proposed",
}
METHOD_COLORS = {
    "frame_wise": "#5B6470",
    "optical_flow": "#7C8FB8",
    "proposal_border": "#2F7F73",
}
METHOD_MARKERS = {
    "frame_wise": "o",
    "optical_flow": "s",
    "proposal_border": "P",
}
CATEGORY_LABELS = {
    "static": "Static",
    "scrolling": "Scrolling",
    "screen_video": "Screen video",
    "weak_border": "Weak border",
    "hard": "Hard",
}
GRID = "#D9DDDF"
TEXT = "#242729"
HEATMAP_CMAP = LinearSegmentedColormap.from_list(
    "screen_normalize_heatmap",
    ["#DDEEEA", "#AFC7CD", "#7C8FB8", "#5B6470", "#242729"],
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build manuscript figures from the proposal-border evaluation run.")
    parser.add_argument("--input", type=Path, default=Path("inputs"))
    parser.add_argument("--main-run", type=Path, default=Path("runs/20260714_small_sample_with_proposal_border"))
    parser.add_argument("--output", type=Path, default=Path("doc/current/paper/manuscript/figures"))
    parser.add_argument("--dpi", type=int, default=300)
    return parser.parse_args()


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def read_json(path: Path) -> dict[str, Any]:
    with path.open(encoding="utf-8") as handle:
        data = json.load(handle)
    if not isinstance(data, dict):
        raise ValueError(f"expected JSON object in {path}")
    return data


def frame_count(video: Path) -> int:
    capture = cv2.VideoCapture(str(video))
    count = int(capture.get(cv2.CAP_PROP_FRAME_COUNT) or 0)
    capture.release()
    return count


def video_size(video: Path) -> tuple[int, int]:
    capture = cv2.VideoCapture(str(video))
    width = int(capture.get(cv2.CAP_PROP_FRAME_WIDTH) or 0)
    height = int(capture.get(cv2.CAP_PROP_FRAME_HEIGHT) or 0)
    capture.release()
    return width, height


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


def overlay_corners(image: np.ndarray, corners: np.ndarray | None, color: tuple[int, int, int] = (47, 127, 115)) -> np.ndarray:
    if corners is None:
        return image
    canvas = cv2.cvtColor(image.copy(), cv2.COLOR_RGB2BGR)
    points = np.round(corners).astype(np.int32)
    cv2.polylines(canvas, [points], True, color, 5, cv2.LINE_AA)
    for point in points:
        cv2.circle(canvas, tuple(point), 10, (255, 255, 255), -1, cv2.LINE_AA)
        cv2.circle(canvas, tuple(point), 10, color, 3, cv2.LINE_AA)
    return cv2.cvtColor(canvas, cv2.COLOR_BGR2RGB)


def normalized_frame(run: Path, category: str, clip: str, method: str, frame: int) -> np.ndarray:
    return read_frame(run / category / clip / method / "normalized.mp4", frame)


def show_image(axis: plt.Axes, image: np.ndarray, title: str) -> None:
    axis.imshow(image)
    axis.set_title(title, fontsize=7.8, pad=3)
    axis.axis("off")


def add_panel_label(axis: plt.Axes, label: str, color: str = TEXT) -> None:
    axis.text(-0.035, 1.035, label, transform=axis.transAxes, ha="left", va="bottom", fontsize=9, fontweight="bold", color=color)


def save(fig: plt.Figure, output: Path, dpi: int) -> None:
    output.parent.mkdir(parents=True, exist_ok=True)
    base = output.with_suffix("")
    fig.savefig(base.with_suffix(".svg"), bbox_inches="tight")
    fig.savefig(base.with_suffix(".pdf"), bbox_inches="tight")
    fig.savefig(base.with_suffix(".png"), dpi=dpi, bbox_inches="tight")
    plt.close(fig)


def collect_metrics(run: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for category in CATEGORIES:
        for clip in EVAL_CLIPS[category]:
            for method in METHODS:
                method_dir = run / category / clip / method
                geometry = read_json(method_dir / "geometry.json")
                temporal = read_json(method_dir / "temporal.json")
                if geometry.get("status") != "ok" or temporal.get("status") != "ok":
                    continue
                rows.append(
                    {
                        "category": category,
                        "clip": clip,
                        "method": method,
                        "rmse": float(geometry["corner_rmse_px_p50"]),
                        "iou": float(geometry["quad_iou_p50"]),
                        "translation": float(temporal["translation_px_p50"]),
                    }
                )
    return rows


def values(rows: list[dict[str, Any]], method: str, field: str, category: str | None = None) -> np.ndarray:
    selected = [row[field] for row in rows if row["method"] == method and (category is None or row["category"] == category)]
    return np.asarray(selected, dtype=float)


def median_iqr(rows: list[dict[str, Any]], method: str, field: str, category: str | None = None) -> tuple[float, float, float]:
    sample = values(rows, method, field, category)
    if sample.size == 0:
        return float("nan"), float("nan"), float("nan")
    return float(np.median(sample)), float(np.percentile(sample, 25)), float(np.percentile(sample, 75))


def metric_matrix(rows: list[dict[str, Any]], field: str) -> np.ndarray:
    return np.asarray([[median_iqr(rows, method, field, category)[0] for method in METHODS] for category in CATEGORIES], dtype=float)


def draw_pipeline(axis: plt.Axes) -> None:
    axis.set_axis_off()
    labels = [
        "Initial\ncorners",
        "Border search\nbands",
        "Physical edge\nevidence",
        "Line fit and\nintersections",
        "LK consistency\ncheck",
        "Smooth and\nwarp",
    ]
    x0, width, gap = 0.02, 0.135, 0.032
    for index, label in enumerate(labels):
        x = x0 + index * (width + gap)
        color = "#DDEEEA" if index in (2, 3) else "#E9EDF2"
        box = patches.FancyBboxPatch(
            (x, 0.30),
            width,
            0.42,
            boxstyle="round,pad=0.012,rounding_size=0.010",
            linewidth=0.85,
            edgecolor="#65717C",
            facecolor=color,
        )
        axis.add_patch(box)
        axis.text(x + width / 2, 0.51, label, ha="center", va="center", fontsize=8, color=TEXT)
        if index < len(labels) - 1:
            axis.annotate("", xy=(x + width + gap * 0.70, 0.51), xytext=(x + width, 0.51), arrowprops={"arrowstyle": "->", "lw": 1.0, "color": "#65717C"})
    axis.text(0.02, 0.94, "Border-guided screen-plane normalization", ha="left", va="top", fontsize=9.5, fontweight="bold", color=TEXT)
    axis.text(0.02, 0.12, "The screen boundary drives the homography; LK tracks are used as a consistency signal for content-motion conflicts.", ha="left", va="bottom", fontsize=7.8, color="#5B6470")


def figure_01(args: argparse.Namespace) -> None:
    category, clip = "scrolling", "scrolling_02"
    video = args.input / category / f"{clip}.mp4"
    frame, ground_truth = annotation_frame(video)
    input_frame = read_frame(video, frame)
    estimate = corners_at(args.main_run / category / clip / PROPOSED_METHOD / "estimated_corners.csv", frame)
    proposed = normalized_frame(args.main_run, category, clip, PROPOSED_METHOD, frame)
    optical = normalized_frame(args.main_run, category, clip, "optical_flow", frame)

    fig = plt.figure(figsize=(7.2, 2.9), constrained_layout=True)
    grid = fig.add_gridspec(2, 4, height_ratios=[0.58, 1.25])
    draw_pipeline(fig.add_subplot(grid[0, :]))
    panels = [
        (overlay_corners(input_frame, ground_truth, color=(90, 90, 90)), "Input + annotation"),
        (overlay_corners(input_frame, estimate), "Border estimate"),
        (optical, "Optical-flow output"),
        (proposed, "Proposed output"),
    ]
    for index, (image, title) in enumerate(panels):
        axis = fig.add_subplot(grid[1, index])
        show_image(axis, image, title)
        add_panel_label(axis, chr(ord("a") + index))
    save(fig, args.output / "figure_01_pipeline.png", args.dpi)


def style_metric_axis(axis: plt.Axes, title: str, ylabel: str) -> None:
    axis.set_title(title, loc="left", fontsize=8.5, fontweight="bold")
    axis.set_ylabel(ylabel)
    axis.grid(axis="y", color=GRID, linewidth=0.55)
    axis.spines[["top", "right"]].set_visible(False)
    axis.set_axisbelow(True)


def bar_metric(axis: plt.Axes, rows: list[dict[str, Any]], field: str, title: str, ylabel: str, log_scale: bool = False) -> None:
    medians, q1s, q3s = [], [], []
    for method in METHODS:
        median, q1, q3 = median_iqr(rows, method, field)
        medians.append(median)
        q1s.append(q1)
        q3s.append(q3)
    medians_arr = np.asarray(medians)
    yerr = np.vstack([medians_arr - np.asarray(q1s), np.asarray(q3s) - medians_arr])
    x = np.arange(len(METHODS))
    axis.bar(x, medians_arr, yerr=yerr, color=[METHOD_COLORS[m] for m in METHODS], edgecolor="#2B2B2B", linewidth=0.7, capsize=3)
    axis.set_xticks(x, [METHOD_LABELS[m] for m in METHODS], rotation=18, ha="right")
    if log_scale:
        axis.set_yscale("log")
        axis.yaxis.set_major_formatter(mticker.ScalarFormatter())
        axis.yaxis.set_minor_formatter(mticker.NullFormatter())
    style_metric_axis(axis, title, ylabel)
    for xpos, value in zip(x, medians_arr):
        label = f"{value:.3f}" if field == "iou" else f"{value:.2f}"
        if log_scale:
            y = value * 1.05
        elif field == "iou":
            y = value + 0.0008
        else:
            y = value + 0.03 * max(medians_arr)
        axis.text(xpos, y, label, ha="center", va="bottom", fontsize=7)


def figure_02(args: argparse.Namespace, rows: list[dict[str, Any]]) -> None:
    fig, axes = plt.subplots(1, 3, figsize=(7.2, 2.75), constrained_layout=True)
    bar_metric(axes[0], rows, "rmse", "a  Corner accuracy", "RMSE px", log_scale=True)
    bar_metric(axes[1], rows, "iou", "b  Overlap", "IoU")
    bar_metric(axes[2], rows, "translation", "c  Trajectory variation", "px/frame")
    axes[1].set_ylim(0.965, 1.000)
    save(fig, args.output / "figure_02_overall_results.png", args.dpi)


def heatmap(axis: plt.Axes, data: np.ndarray, title: str, cbar_label: str, fmt: str, log_color: bool = False) -> None:
    color_data = np.log10(np.maximum(data, 1e-6)) if log_color else data
    image = axis.imshow(color_data, aspect="auto", cmap=HEATMAP_CMAP)
    axis.set_xticks(np.arange(len(METHODS)), [METHOD_LABELS[m] for m in METHODS], rotation=20, ha="right")
    axis.set_yticks(np.arange(len(CATEGORIES)), [CATEGORY_LABELS[c] for c in CATEGORIES])
    axis.set_title(title, loc="left", fontsize=8.5, fontweight="bold")
    axis.set_xticks(np.arange(-0.5, len(METHODS), 1), minor=True)
    axis.set_yticks(np.arange(-0.5, len(CATEGORIES), 1), minor=True)
    axis.grid(which="minor", color="white", linewidth=0.8)
    axis.tick_params(which="minor", bottom=False, left=False)
    for row in range(data.shape[0]):
        for col in range(data.shape[1]):
            value = data[row, col]
            rgba = image.cmap(image.norm(color_data[row, col]))
            luminance = 0.299 * rgba[0] + 0.587 * rgba[1] + 0.114 * rgba[2]
            color = "white" if luminance < 0.46 else "#1F1F1F"
            axis.text(col, row, fmt.format(value), ha="center", va="center", fontsize=7, color=color)
    axis.tick_params(length=0)
    for spine in axis.spines.values():
        spine.set_visible(False)
    cbar = axis.figure.colorbar(image, ax=axis, fraction=0.046, pad=0.03)
    cbar.set_label(cbar_label, fontsize=7.5)


def figure_03(args: argparse.Namespace, rows: list[dict[str, Any]]) -> None:
    fig, axes = plt.subplots(1, 2, figsize=(7.2, 3.35), constrained_layout=True)
    heatmap(axes[0], metric_matrix(rows, "rmse"), "a  Geometry by capture condition", "log10 px", "{:.1f}", log_color=True)
    heatmap(axes[1], metric_matrix(rows, "translation"), "b  Trajectory variation by capture condition", "log10 px/frame", "{:.2f}", log_color=True)
    save(fig, args.output / "figure_03_category_results.png", args.dpi)


def clip_label(row: dict[str, Any]) -> str:
    return row["clip"].replace("_", " ")


def figure_04(args: argparse.Namespace, rows: list[dict[str, Any]]) -> None:
    proposed = [row for row in rows if row["method"] == PROPOSED_METHOD]
    proposed.sort(key=lambda row: (CATEGORIES.index(row["category"]), row["clip"]))
    labels = [clip_label(row) for row in proposed]
    x = np.arange(len(proposed))
    colors = [METHOD_COLORS[PROPOSED_METHOD] if row["rmse"] <= 10 else "#B8842D" for row in proposed]

    fig, axes = plt.subplots(2, 1, figsize=(7.2, 4.35), sharex=True, constrained_layout=True)
    axes[0].bar(x, [row["rmse"] for row in proposed], color=colors, edgecolor="#2B2B2B", linewidth=0.6)
    style_metric_axis(axes[0], "a  Proposed geometry by clip", "RMSE px")
    axes[0].axhline(10, color="#B55D5D", linewidth=0.8, linestyle="--")
    axes[1].bar(x, [row["translation"] for row in proposed], color=METHOD_COLORS[PROPOSED_METHOD], edgecolor="#2B2B2B", linewidth=0.6)
    style_metric_axis(axes[1], "b  Proposed trajectory variation by clip", "px/frame")
    axes[1].set_xticks(x, labels, rotation=35, ha="right")
    save(fig, args.output / "figure_04_proposed_clip_results.png", args.dpi)


def figure_05(args: argparse.Namespace) -> None:
    cases = [
        ("static", "static_02"),
        ("scrolling", "scrolling_02"),
        ("screen_video", "screen_video_02"),
        ("weak_border", "weak_border_02"),
        ("hard", "hard_01"),
    ]
    fig, axes = plt.subplots(len(cases), 4, figsize=(7.2, 8.1), constrained_layout=True)
    for row, (category, clip) in enumerate(cases):
        video = args.input / category / f"{clip}.mp4"
        frame, corners = annotation_frame(video)
        show_image(axes[row, 0], overlay_corners(read_frame(video, frame), corners, color=(90, 90, 90)), CATEGORY_LABELS[category])
        for col, method in enumerate(METHODS, start=1):
            title = METHOD_LABELS[method] if row == 0 else ""
            show_image(axes[row, col], normalized_frame(args.main_run, category, clip, method, frame), title)
    axes[0, 0].set_title("Input + annotation", fontsize=7.8, pad=3)
    save(fig, args.output / "figure_05_qualitative.png", args.dpi)


def main() -> int:
    args = parse_args()
    args.output.mkdir(parents=True, exist_ok=True)
    apply_paper_style()
    rows = collect_metrics(args.main_run)
    if len(rows) != len(CATEGORIES) * 2 * len(METHODS):
        raise RuntimeError(f"expected 30 method/clip metric rows, found {len(rows)}")
    figure_01(args)
    figure_02(args, rows)
    figure_03(args, rows)
    figure_04(args, rows)
    figure_05(args)
    print(f"wrote manuscript figures to {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
