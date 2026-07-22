#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import math
from pathlib import Path
from statistics import median
from typing import Any

import cv2
import matplotlib
import numpy as np

matplotlib.use("Agg")
import matplotlib.pyplot as plt

from screen_normalize.experiments.annotations import load_annotations
from screen_normalize.experiments.evaluation import read_frames, video_metadata, warp_to_screen
from screen_normalize.experiments.paper_style import apply_paper_style
from screen_normalize.metrics.frequency_preservation import (
    FrequencyPreservationConfig,
    evaluate_frequency_preservation_pair,
)


ROOT = Path(__file__).resolve().parents[2]
METHODS = ("frame_wise", "optical_flow", "proposal_border")
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
GRID = "#D9DDDF"
TEXT = "#242729"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Analyze local moire ROI frequency preservation.")
    parser.add_argument("--original", type=Path, default=ROOT / "inputs" / "scrolling" / "scrolling_01.mp4")
    parser.add_argument("--annotations", type=Path, default=None)
    parser.add_argument("--moire-rois", type=Path, default=None)
    parser.add_argument(
        "--run-dir",
        type=Path,
        default=ROOT / "runs" / "20260714_small_sample_with_proposal_border" / "scrolling" / "scrolling_01",
    )
    parser.add_argument("--methods", nargs="+", default=list(METHODS))
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=ROOT / "doc" / "current" / "paper" / "results" / "20260722_moire_roi_preservation_demo_scrolling_01",
    )
    parser.add_argument(
        "--figure",
        type=Path,
        default=ROOT
        / "doc"
        / "current"
        / "paper"
        / "manuscript"
        / "figures"
        / "figure_06b_moire_roi_preservation.png",
    )
    parser.add_argument("--dpi", type=int, default=300)
    return parser.parse_args()


def read_moire_rois(path: Path) -> list[dict[str, Any]]:
    with path.open(newline="", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))
    rois: list[dict[str, Any]] = []
    for row in rows:
        rois.append(
            {
                "frame": int(row["frame"]),
                "roi_id": row["roi_id"],
                "x1": float(row["x1"]),
                "y1": float(row["y1"]),
                "x2": float(row["x2"]),
                "y2": float(row["y2"]),
                "label": row.get("label", "moire"),
            }
        )
    return rois


def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    fields: list[str] = []
    for row in rows:
        fields.extend(key for key in row if key not in fields)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def homography_to_canvas(corners: np.ndarray, width: int, height: int) -> np.ndarray:
    destination = np.array(
        [[0, 0], [width - 1, 0], [width - 1, height - 1], [0, height - 1]],
        dtype=np.float32,
    )
    return cv2.getPerspectiveTransform(corners.astype(np.float32), destination)


def transform_roi_bbox(roi: dict[str, Any], homography: np.ndarray, width: int, height: int) -> tuple[int, int, int, int]:
    points = np.array(
        [
            [[roi["x1"], roi["y1"]]],
            [[roi["x2"], roi["y1"]]],
            [[roi["x2"], roi["y2"]]],
            [[roi["x1"], roi["y2"]]],
        ],
        dtype=np.float32,
    )
    mapped = cv2.perspectiveTransform(points, homography).reshape(-1, 2)
    x1 = int(max(0, math.floor(float(np.min(mapped[:, 0])))))
    y1 = int(max(0, math.floor(float(np.min(mapped[:, 1])))))
    x2 = int(min(width, math.ceil(float(np.max(mapped[:, 0])))))
    y2 = int(min(height, math.ceil(float(np.max(mapped[:, 1])))))
    return x1, y1, x2, y2


def crop(image: np.ndarray, box: tuple[int, int, int, int]) -> np.ndarray | None:
    x1, y1, x2, y2 = box
    if x2 - x1 < 32 or y2 - y1 < 32:
        return None
    return image[y1:y2, x1:x2].copy()


def to_gray(image: np.ndarray) -> np.ndarray:
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY) if image.ndim == 3 else image.copy()
    return gray.astype(np.float32) / 255.0


def peak_descriptor(image: np.ndarray) -> dict[str, float] | None:
    gray = to_gray(image)
    height, width = gray.shape[:2]
    if min(height, width) < 32:
        return None
    window = np.outer(np.hanning(height), np.hanning(width)).astype(np.float32)
    spectrum = np.fft.fftshift(np.fft.fft2((gray - float(np.mean(gray))) * window))
    power = np.abs(spectrum).astype(np.float64) ** 2
    yy, xx = np.indices((height, width))
    cy, cx = height // 2, width // 2
    radius = np.hypot(xx - cx, yy - cy)
    valid = (radius > 0.08 * min(height, width)) & (radius <= 0.5 * min(height, width))
    if not np.any(valid):
        return None
    masked = np.where(valid, power, 0.0)
    y, x = np.unravel_index(int(np.argmax(masked)), masked.shape)
    local = masked[max(0, y - 4) : min(height, y + 5), max(0, x - 4) : min(width, x + 5)]
    energy = float(np.sum(local))
    if energy <= 0.0:
        return None
    local_yy, local_xx = np.indices(local.shape)
    local_xx = local_xx + max(0, x - 4)
    local_yy = local_yy + max(0, y - 4)
    variance = np.sum(((local_xx - x) ** 2 + (local_yy - y) ** 2) * local) / energy
    return {
        "x": float(x),
        "y": float(y),
        "radius_norm": float(radius[y, x] / max(1.0, 0.5 * min(height, width))),
        "angle_deg": float((np.degrees(np.arctan2(y - cy, x - cx)) + 180.0) % 180.0),
        "energy": energy,
        "width_px": float(np.sqrt(max(0.0, variance))),
    }


def angle_error(a: float, b: float) -> float:
    return abs(((a - b + 90.0) % 180.0) - 90.0)


def peak_metrics(reference: np.ndarray, normalized: np.ndarray) -> dict[str, float | None]:
    ref = peak_descriptor(reference)
    out = peak_descriptor(normalized)
    if ref is None or out is None:
        return {
            "peak_position_error_px": None,
            "peak_radius_error": None,
            "peak_angle_error_deg": None,
            "peak_energy_delta_db": None,
            "peak_energy_delta_abs_db": None,
            "peak_width_log_ratio_abs": None,
        }
    energy_delta = 10.0 * math.log10(out["energy"] / ref["energy"]) if ref["energy"] > 0 else None
    width_ratio = out["width_px"] / ref["width_px"] if ref["width_px"] > 0 else None
    return {
        "peak_position_error_px": float(np.hypot(out["x"] - ref["x"], out["y"] - ref["y"])),
        "peak_radius_error": abs(out["radius_norm"] - ref["radius_norm"]),
        "peak_angle_error_deg": angle_error(out["angle_deg"], ref["angle_deg"]),
        "peak_energy_delta_db": energy_delta,
        "peak_energy_delta_abs_db": abs(energy_delta) if energy_delta is not None else None,
        "peak_width_log_ratio_abs": abs(math.log(width_ratio)) if width_ratio and width_ratio > 0 else None,
    }


def finite(values: list[Any]) -> list[float]:
    return [float(value) for value in values if isinstance(value, int | float) and np.isfinite(value)]


def summarize(rows: list[dict[str, Any]], methods: list[str]) -> list[dict[str, Any]]:
    fields = [
        "log_fft_magnitude_similarity",
        "high_frequency_energy_ratio",
        "high_frequency_log_ratio_abs",
        "orientation_histogram_intersection",
        "band_energy_ratio",
        "band_log_ratio_abs",
        "peak_position_error_px",
        "peak_radius_error",
        "peak_angle_error_deg",
        "peak_energy_delta_db",
        "peak_energy_delta_abs_db",
        "peak_width_log_ratio_abs",
    ]
    summaries: list[dict[str, Any]] = []
    for method in methods:
        method_rows = [row for row in rows if row["method"] == method and row["status"] == "ok"]
        summary: dict[str, Any] = {"method": method, "roi_count": len(method_rows)}
        for field in fields:
            values = finite([row.get(field) for row in method_rows])
            summary[f"{field}_median"] = median(values) if values else None
        summaries.append(summary)
    return summaries


def style_axis(axis: plt.Axes, panel: str, title: str, ylabel: str) -> None:
    axis.set_title(f"{panel}  {title}", loc="left", fontsize=8.5, fontweight="bold")
    axis.set_ylabel(ylabel)
    axis.grid(axis="y", color=GRID, linewidth=0.6, alpha=0.9)
    axis.spines[["top", "right"]].set_visible(False)
    axis.set_axisbelow(True)


def label_bars(axis: plt.Axes, bars: object, fmt: str = "{:.3f}") -> None:
    ymin, ymax = axis.get_ylim()
    offset = 0.018 * (ymax - ymin)
    for bar in bars:
        height = float(bar.get_height())
        axis.text(
            bar.get_x() + bar.get_width() / 2,
            height + offset,
            fmt.format(height),
            ha="center",
            va="bottom",
            fontsize=5.7,
            color=TEXT,
        )


def grouped_bars(
    axis: plt.Axes,
    summary: dict[str, dict[str, float]],
    fields: list[tuple[str, str]],
    title: str,
    ylabel: str,
    panel: str,
    ylim: tuple[float, float] | None = None,
) -> None:
    x = np.arange(len(fields))
    width = 0.23
    offsets = np.linspace(-width, width, len(METHODS))
    for offset, method in zip(offsets, METHODS):
        values = [summary[method][field] for field, _ in fields]
        bars = axis.bar(
            x + offset,
            values,
            width=width,
            label=METHOD_LABELS[method],
            color=METHOD_COLORS[method],
            edgecolor="#2B2B2B",
            linewidth=0.55,
        )
        label_bars(axis, bars)
    axis.set_xticks(x, [label for _, label in fields])
    if ylim is not None:
        axis.set_ylim(*ylim)
    style_axis(axis, panel, title, ylabel)


def build_figure(summary_rows: list[dict[str, Any]], output: Path, dpi: int) -> None:
    apply_paper_style()
    summary = {row["method"]: row for row in summary_rows}
    fig, axes = plt.subplots(2, 2, figsize=(7.2, 5.15))
    fig.subplots_adjust(left=0.08, right=0.985, top=0.81, bottom=0.10, wspace=0.18, hspace=0.44)
    grouped_bars(
        axes[0, 0],
        summary,
        [
            ("log_fft_magnitude_similarity_median", "FFT sim"),
            ("orientation_histogram_intersection_median", "Orient hist"),
        ],
        "Local frequency structure similarity",
        "higher is better",
        "a",
        (0.80, 1.02),
    )
    grouped_bars(
        axes[0, 1],
        summary,
        [
            ("high_frequency_log_ratio_abs_median", "HF"),
            ("band_log_ratio_abs_median", "Band"),
        ],
        "Local energy-ratio distance",
        "lower is better",
        "b",
        (0.0, 3.2),
    )
    grouped_bars(
        axes[1, 0],
        summary,
        [
            ("peak_radius_error_median", "Radius"),
            ("peak_width_log_ratio_abs_median", "Width"),
        ],
        "Dominant-peak distance",
        "lower is better",
        "c",
        (0.0, 0.45),
    )
    grouped_bars(
        axes[1, 1],
        summary,
        [
            ("peak_angle_error_deg_median", "Angle deg"),
            ("peak_energy_delta_abs_db_median", "|Energy dB|"),
        ],
        "Dominant-peak change",
        "lower is better",
        "d",
        (0.0, 35.0),
    )
    handles, labels = axes[0, 0].get_legend_handles_labels()
    fig.legend(handles, labels, loc="upper center", ncol=3, frameon=False, bbox_to_anchor=(0.5, 0.90))
    fig.suptitle(
        "Moire ROI frequency preservation diagnostics on scrolling_01",
        fontsize=9.6,
        fontweight="bold",
        color=TEXT,
        y=0.98,
    )
    output.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(output.with_suffix(".svg"), bbox_inches="tight")
    fig.savefig(output.with_suffix(".png"), dpi=dpi, bbox_inches="tight")
    plt.close(fig)


def main() -> int:
    args = parse_args()
    original = args.original.resolve()
    annotations_path = (args.annotations or original.with_suffix(".csv")).resolve()
    roi_path = (args.moire_rois or original.with_name(f"{original.stem}_moire_rois.csv")).resolve()
    output_dir = args.output_dir.resolve()

    metadata = video_metadata(original)
    annotations = load_annotations(annotations_path, metadata.width, metadata.height)
    rois = [roi for roi in read_moire_rois(roi_path) if roi["frame"] in annotations]
    frames = sorted({int(roi["frame"]) for roi in rois})
    original_frames = read_frames(original, frames)
    config = FrequencyPreservationConfig(max_side=0)

    rows: list[dict[str, Any]] = []
    for method in args.methods:
        normalized_video = args.run_dir.resolve() / method / "normalized.mp4"
        normalized_meta = video_metadata(normalized_video)
        normalized_frames = read_frames(normalized_video, frames)
        for frame in frames:
            original_frame = original_frames.get(frame)
            normalized_frame = normalized_frames.get(frame)
            if original_frame is None or normalized_frame is None:
                continue
            homography = homography_to_canvas(annotations[frame], normalized_meta.width, normalized_meta.height)
            reference = warp_to_screen(original_frame, annotations[frame], normalized_meta.width, normalized_meta.height)
            for roi in [item for item in rois if item["frame"] == frame]:
                box = transform_roi_bbox(roi, homography, normalized_meta.width, normalized_meta.height)
                ref_crop = crop(reference, box)
                out_crop = crop(normalized_frame, box)
                base = {
                    "method": method,
                    "frame": frame,
                    "roi_id": roi["roi_id"],
                    "source_x1": roi["x1"],
                    "source_y1": roi["y1"],
                    "source_x2": roi["x2"],
                    "source_y2": roi["y2"],
                    "canvas_x1": box[0],
                    "canvas_y1": box[1],
                    "canvas_x2": box[2],
                    "canvas_y2": box[3],
                }
                if ref_crop is None or out_crop is None:
                    rows.append({**base, "status": "skipped", "reason": "roi_too_small_after_warp"})
                    continue
                metrics = evaluate_frequency_preservation_pair(ref_crop, out_crop, config)
                rows.append({**base, **metrics, **peak_metrics(ref_crop, out_crop)})

    summary_rows = summarize(rows, list(args.methods))
    write_csv(output_dir / "moire_roi_frequency_rows.csv", rows)
    write_csv(output_dir / "moire_roi_frequency_summary.csv", summary_rows)
    build_figure(summary_rows, args.figure.resolve(), args.dpi)
    print(f"wrote {output_dir / 'moire_roi_frequency_rows.csv'}")
    print(f"wrote {output_dir / 'moire_roi_frequency_summary.csv'}")
    print(f"wrote {args.figure.resolve().with_suffix('.png')}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
