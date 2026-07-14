#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
from pathlib import Path
from typing import Any

import cv2
import matplotlib.pyplot as plt
import numpy as np

from screen_normalize.experiments.annotations import load_annotations
from screen_normalize.experiments.paper_style import apply_paper_style


CATEGORIES = ("static", "scrolling", "screen_video", "weak_border", "hard")
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
    "frame_wise": "#526D82",
    "optical_flow": "#C58B3A",
    "proposed": "#2F7F73",
    "no_reliability_gates": "#C58B3A",
    "no_trajectory_smoothing": "#526D82",
    "no_offline_repair": "#806491",
}
CATEGORY_LABELS = {
    "static": "Static",
    "scrolling": "Scrolling",
    "screen_video": "Screen video",
    "weak_border": "Weak border",
    "hard": "Hard",
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build real manuscript figures from first-pass outputs.")
    parser.add_argument("--input", type=Path, default=Path("inputs"))
    parser.add_argument("--main-run", type=Path, default=Path("runs/20260714_full_pipeline_first_pass"))
    parser.add_argument("--results", type=Path, default=Path("doc/paper/results"))
    parser.add_argument("--output", type=Path, default=Path("doc/paper/manuscript/figures"))
    parser.add_argument("--dpi", type=int, default=180)
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
    rows = read_csv(csv_path)
    best: tuple[int, np.ndarray] | None = None
    for row in rows:
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


def overlay_corners(image: np.ndarray, corners: np.ndarray | None, color: tuple[int, int, int] = (0, 220, 90)) -> np.ndarray:
    if corners is None:
        return image
    canvas = cv2.cvtColor(image.copy(), cv2.COLOR_RGB2BGR)
    points = np.round(corners).astype(np.int32)
    cv2.polylines(canvas, [points], True, color, 6, cv2.LINE_AA)
    for point in points:
        cv2.circle(canvas, tuple(point), 12, (255, 80, 40), -1, cv2.LINE_AA)
    return cv2.cvtColor(canvas, cv2.COLOR_BGR2RGB)


def show_image(axis: plt.Axes, image: np.ndarray, title: str) -> None:
    axis.imshow(image)
    axis.set_title(title, fontsize=8.2, pad=4)
    axis.axis("off")


def save(fig: plt.Figure, output: Path, dpi: int) -> None:
    output.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(output, dpi=dpi, bbox_inches="tight")
    plt.close(fig)


def normalized_frame(run: Path, category: str, clip: str, method: str, frame: int) -> np.ndarray:
    return read_frame(run / category / clip / method / "normalized.mp4", frame)


def figure_01(args: argparse.Namespace) -> None:
    category, clip = "static", "static_01"
    video = args.input / category / f"{clip}.mp4"
    frame, gt = annotation_frame(video, prefer_nonzero=True)
    input_frame = read_frame(video, frame)
    estimate = corners_at(args.main_run / category / clip / "proposed" / "estimated_corners.csv", frame)
    proposed = normalized_frame(args.main_run, category, clip, "proposed", frame)
    framewise = normalized_frame(args.main_run, category, clip, "frame_wise", frame)
    warped_gt = input_frame
    if gt is not None:
        h, w = proposed.shape[:2]
        dst = np.asarray([[0, 0], [w - 1, 0], [w - 1, h - 1], [0, h - 1]], dtype=np.float32)
        transform = cv2.getPerspectiveTransform(gt.astype(np.float32), dst)
        warped_gt = cv2.warpPerspective(input_frame, transform, (w, h))
    fig, axes = plt.subplots(1, 5, figsize=(9.6, 2.15), constrained_layout=True)
    panels = [
        (input_frame, "(a) Input"),
        (overlay_corners(input_frame, estimate), "(b) Estimated plane"),
        (warped_gt, "(c) Homography warp"),
        (framewise, "(d) Frame-wise output"),
        (proposed, "(e) Proposed output"),
    ]
    for axis, (image, title) in zip(axes, panels):
        show_image(axis, image, title)
    save(fig, args.output / "figure_01_pipeline.png", args.dpi)


def figure_02(args: argparse.Namespace) -> None:
    fig, axes = plt.subplots(len(CATEGORIES), 2, figsize=(5.8, 8.4), constrained_layout=True)
    for row, category in enumerate(CATEGORIES):
        clip = f"{category}_01"
        video = args.input / category / f"{clip}.mp4"
        frame, corners = annotation_frame(video, prefer_nonzero=True)
        image = read_frame(video, frame)
        show_image(axes[row, 0], image, f"{CATEGORY_LABELS[category]} input")
        show_image(axes[row, 1], overlay_corners(image, corners), f"{CATEGORY_LABELS[category]} annotation")
    save(fig, args.output / "figure_02_dataset.png", args.dpi)


def grouped_bar(axis: plt.Axes, rows: list[dict[str, str]], field: str, title: str, ylabel: str) -> None:
    x = np.arange(len(CATEGORIES))
    width = 0.25
    for index, method in enumerate(METHODS):
        values = []
        for category in CATEGORIES:
            samples = [
                float(row[field])
                for row in rows
                if row["category"] == category and row["method"] == method and row["status"] == "ok" and row.get(field)
            ]
            values.append(float(np.median(samples)) if samples else np.nan)
        axis.bar(x + (index - 1) * width, values, width, label=METHOD_LABELS[method], color=METHOD_COLORS[method])
    axis.set_title(title, loc="left", fontsize=9, fontweight="bold")
    axis.set_ylabel(ylabel)
    axis.set_xticks(x, [CATEGORY_LABELS[c] for c in CATEGORIES], rotation=25, ha="right")
    axis.grid(axis="y", color="#D9DDDF", linewidth=0.6)
    axis.spines[["top", "right"]].set_visible(False)


def figure_03(args: argparse.Namespace) -> None:
    rows = read_csv(args.results / "full_pipeline_first_pass" / "geometry_table.csv")
    fig, axes = plt.subplots(1, 3, figsize=(10.2, 3.2), constrained_layout=True)
    grouped_bar(axes[0], rows, "corner_rmse_px_mean", "(a) Corner RMSE", "px, median per category")
    grouped_bar(axes[1], rows, "quad_iou_mean", "(b) Quadrilateral IoU", "IoU, median per category")
    grouped_bar(axes[2], rows, "aspect_relative_error_mean", "(c) Aspect-ratio error", "relative error, median")
    handles, labels = axes[0].get_legend_handles_labels()
    fig.legend(handles, labels, loc="upper center", ncol=3, bbox_to_anchor=(0.5, 1.08), frameon=False)
    save(fig, args.output / "figure_03_geometry.png", args.dpi)


def numeric_rows(path: Path) -> list[dict[str, float]]:
    rows: list[dict[str, float]] = []
    with path.open(newline="", encoding="utf-8") as handle:
        for row in csv.DictReader(handle):
            try:
                rows.append({key: float(row[key]) for key in ("frame", "translation_px", "rotation_deg", "scale_delta")})
            except (KeyError, ValueError):
                continue
    return rows


def figure_04(args: argparse.Namespace) -> None:
    category, clip = "static", "static_01"
    fig, axes = plt.subplots(1, 3, figsize=(10.2, 3.0), constrained_layout=True)
    specs = [
        ("translation_px", "(a) Translation", "px", 1.0),
        ("rotation_deg", "(b) Rotation", "deg", 1.0),
        ("scale_delta", "(c) Scale change", "%", 100.0),
    ]
    for method in METHODS:
        rows = numeric_rows(args.main_run / category / clip / method / "temporal_frames.csv")
        frames = np.asarray([row["frame"] for row in rows])
        for axis, (field, title, ylabel, multiplier) in zip(axes, specs):
            values = np.asarray([row[field] * multiplier for row in rows])
            axis.plot(frames, values, label=METHOD_LABELS[method], color=METHOD_COLORS[method], linewidth=1.2)
    for axis, (_, title, ylabel, _) in zip(axes, specs):
        axis.set_title(title, loc="left", fontsize=9, fontweight="bold")
        axis.set_xlabel("Frame")
        axis.set_ylabel(ylabel)
        axis.grid(color="#D9DDDF", linewidth=0.6)
        axis.spines[["top", "right"]].set_visible(False)
    handles, labels = axes[0].get_legend_handles_labels()
    fig.legend(handles, labels, loc="upper center", ncol=3, bbox_to_anchor=(0.5, 1.08), frameon=False)
    save(fig, args.output / "figure_04_temporal.png", args.dpi)


def figure_05(args: argparse.Namespace) -> None:
    fig, axes = plt.subplots(len(CATEGORIES), 4, figsize=(9.4, 8.0), constrained_layout=True)
    for row, category in enumerate(CATEGORIES):
        clip = f"{category}_01"
        video = args.input / category / f"{clip}.mp4"
        frame, corners = annotation_frame(video, prefer_nonzero=True)
        show_image(axes[row, 0], overlay_corners(read_frame(video, frame), corners), CATEGORY_LABELS[category])
        for col, method in enumerate(METHODS, start=1):
            show_image(axes[row, col], normalized_frame(args.main_run, category, clip, method, frame), METHOD_LABELS[method] if row == 0 else "")
    axes[0, 0].set_title("Input + label", fontsize=8.2, pad=4)
    save(fig, args.output / "figure_05_qualitative.png", args.dpi)


def box_panel(axis: plt.Axes, rows: list[dict[str, str]], metric: str, field: str, title: str, ylabel: str) -> None:
    samples = []
    labels = []
    colors = []
    for method in METHODS:
        values = [float(row[field]) for row in rows if row["metric"] == metric and row["method"] == method and row["status"] == "ok" and row.get(field)]
        samples.append(values)
        labels.append(METHOD_LABELS[method])
        colors.append(METHOD_COLORS[method])
    plot = axis.boxplot(samples, patch_artist=True, tick_labels=labels, showmeans=True)
    for patch, color in zip(plot["boxes"], colors):
        patch.set_facecolor(color)
        patch.set_alpha(0.75)
    axis.set_title(title, loc="left", fontsize=9, fontweight="bold")
    axis.set_ylabel(ylabel)
    axis.tick_params(axis="x", rotation=12)
    axis.grid(axis="y", color="#D9DDDF", linewidth=0.6)
    axis.spines[["top", "right"]].set_visible(False)


def figure_06(args: argparse.Namespace) -> None:
    rows = read_csv(args.results / "full_pipeline_first_pass" / "all_metrics.csv")
    fig, axes = plt.subplots(1, 2, figsize=(7.6, 3.2), constrained_layout=True)
    box_panel(axes[0], rows, "detail", "edge_preservation_index_mean", "(a) Edge preservation", "F1")
    box_panel(axes[1], rows, "frequency", "fft_orthogonality_error_deg_mean", "(b) FFT orthogonality error", "degrees")
    save(fig, args.output / "figure_06_detail_frequency.png", args.dpi)


def figure_07(args: argparse.Namespace) -> None:
    rows = read_csv(args.results / "full_ablation_first_pass" / "ablation_aggregate_metrics.csv")
    methods = ("proposed", "no_reliability_gates", "no_trajectory_smoothing", "no_offline_repair")
    specs = [
        ("corner_rmse_px", "(a) Corner RMSE", "px"),
        ("quad_iou", "(b) Quad IoU", "IoU"),
        ("translation_px", "(c) Translation", "px"),
        ("edge_preservation_index", "(d) Edge preservation", "F1"),
    ]
    fig, axes = plt.subplots(1, 4, figsize=(11.2, 3.0), constrained_layout=True)
    for axis, (field, title, ylabel) in zip(axes, specs):
        values = []
        for method in methods:
            match = next(row for row in rows if row["method"] == method and row["field"] == field)
            values.append(float(match["median"]))
        axis.bar(np.arange(len(methods)), values, color=[METHOD_COLORS[m] for m in methods], width=0.68)
        axis.set_title(title, loc="left", fontsize=9, fontweight="bold")
        axis.set_ylabel(ylabel)
        axis.set_xticks(np.arange(len(methods)), [METHOD_LABELS[m] for m in methods], rotation=20, ha="right")
        axis.grid(axis="y", color="#D9DDDF", linewidth=0.6)
        axis.spines[["top", "right"]].set_visible(False)
    save(fig, args.output / "figure_07_ablation.png", args.dpi)


def debug_acceptance(run: Path, category: str, clip: str) -> tuple[np.ndarray, str]:
    rows = read_csv(run / category / clip / "proposed" / "debug.csv")
    accepted = np.asarray([1.0 if row.get("accepted") == "True" else 0.0 for row in rows], dtype=float)
    label = f"{int(accepted.sum())}/{len(accepted)} accepted"
    return accepted, label


def figure_08(args: argparse.Namespace) -> None:
    cases = [
        ("scrolling", "scrolling_10", "Scrolling drift / long rejection"),
        ("weak_border", "weak_border_10", "Weak-border freeze"),
        ("hard", "hard_01", "Hard sample freeze"),
    ]
    fig, axes = plt.subplots(len(cases), 3, figsize=(9.4, 6.4), constrained_layout=True)
    for row, (category, clip, title) in enumerate(cases):
        video = args.input / category / f"{clip}.mp4"
        frame = min(150, frame_count(video) - 1)
        image = read_frame(video, frame)
        estimate = corners_at(args.main_run / category / clip / "proposed" / "estimated_corners.csv", frame)
        show_image(axes[row, 0], overlay_corners(image, estimate, color=(0, 0, 255)), title)
        show_image(axes[row, 1], normalized_frame(args.main_run, category, clip, "proposed", frame), "Proposed output" if row == 0 else "")
        accepted, label = debug_acceptance(args.main_run, category, clip)
        axes[row, 2].plot(np.arange(len(accepted)), accepted, color=METHOD_COLORS["proposed"], linewidth=1.0)
        axes[row, 2].set_ylim(-0.08, 1.08)
        axes[row, 2].set_title(label, fontsize=8.2, pad=4)
        axes[row, 2].set_xlabel("Frame")
        axes[row, 2].set_ylabel("Accepted")
        axes[row, 2].grid(color="#D9DDDF", linewidth=0.6)
        axes[row, 2].spines[["top", "right"]].set_visible(False)
    save(fig, args.output / "figure_08_failures.png", args.dpi)


def main() -> int:
    args = parse_args()
    args.output.mkdir(parents=True, exist_ok=True)
    apply_paper_style()
    for builder in (figure_01, figure_02, figure_03, figure_04, figure_05, figure_06, figure_07, figure_08):
        builder(args)
    print(f"wrote manuscript figures to {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
