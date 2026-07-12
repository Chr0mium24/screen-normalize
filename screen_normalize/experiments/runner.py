from __future__ import annotations

import tempfile
import time
from dataclasses import asdict, dataclass
from pathlib import Path

import cv2
import numpy as np

from ..algorithms.encoding import encode_warped_video, mux_audio
from ..algorithms.tracking import estimate_corner_trajectory
from ..algorithms.trajectory import (
    apply_offline_geometry_gate,
    interpolate_corner_trajectory,
    reliable_mask_from_tracker_rows,
    smooth_corner_trajectory,
)
from ..common import DEFAULT_FALLBACK_CORNERS, open_capture, parse_corners, require_ffmpeg
from ..normalize_args import apply_reference_profile, parse_args
from .run_io import METHOD_IDS, write_csv, write_json


@dataclass(frozen=True)
class MethodConfig:
    method: str
    tracker: str
    smooth: float
    median_window: int
    trajectory_window: int
    interpolate: bool
    geometry_gate: bool
    reference_align: bool


METHOD_CONFIGS = {
    "frame_wise": MethodConfig("frame_wise", "detect", 0.0, 1, 1, False, False, False),
    "optical_flow": MethodConfig("optical_flow", "flow", 0.0, 1, 1, False, False, False),
    "proposed": MethodConfig("proposed", "reference", 0.85, 5, 9, True, True, True),
}


@dataclass(frozen=True)
class RunResult:
    method: str
    output: Path
    frames: int
    elapsed_seconds: float


def _method_args(source: Path, config: MethodConfig):
    args = parse_args([str(source)])
    if config.method == "proposed":
        args.reference_profile = "dynamic"
        apply_reference_profile(args)
    args.tracker = config.tracker
    args.smooth = config.smooth
    args.median_window = config.median_window
    args.trajectory_window = config.trajectory_window
    args.trajectory_interpolate = config.interpolate
    args.trajectory_geometry_gate = config.geometry_gate
    args.reference_align = config.reference_align
    return args


def method_config(method: str) -> MethodConfig:
    try:
        return METHOD_CONFIGS[method]
    except KeyError as exc:
        raise ValueError(f"unsupported method {method!r}; choose from {', '.join(METHOD_IDS)}") from exc


def _corner_rows(trajectory: np.ndarray) -> list[dict[str, float | int]]:
    labels = ("tl", "tr", "br", "bl")
    rows: list[dict[str, float | int]] = []
    for frame, corners in enumerate(trajectory):
        row: dict[str, float | int] = {"frame": frame}
        for label, point in zip(labels, corners):
            row[f"{label}_x"] = float(point[0])
            row[f"{label}_y"] = float(point[1])
        rows.append(row)
    return rows


def run_method(source: Path, output_dir: Path, method: str) -> RunResult:
    source = source.resolve()
    if not source.exists():
        raise FileNotFoundError(source)
    config = method_config(method)
    args = _method_args(source, config)
    require_ffmpeg()
    output_dir.mkdir(parents=True, exist_ok=True)
    output = output_dir / "normalized.mp4"
    started = time.perf_counter()

    capture = open_capture(source)
    fps = args.fps or float(capture.get(cv2.CAP_PROP_FPS) or 60.0)
    fps = fps if fps > 0 else 60.0
    fallback = args.corners
    auto_detect = fallback is None
    if fallback is None:
        fallback = parse_corners(DEFAULT_FALLBACK_CORNERS)

    tracker_rows: list[dict[str, object]] = []
    trajectory = estimate_corner_trajectory(
        capture=capture,
        fallback_corners=fallback,
        auto_detect=auto_detect,
        tracker=args.tracker,
        smooth=args.smooth,
        detect_correction=args.detect_correction,
        feature_refresh=args.feature_refresh,
        reference_min_inliers=args.reference_min_inliers,
        reference_min_inlier_ratio=args.reference_min_inlier_ratio,
        reference_max_reprojection_error=args.reference_max_reprojection_error,
        reference_max_scale_step=args.reference_max_scale_step,
        reference_max_area_step=args.reference_max_area_step,
        reference_min_point_age=args.reference_min_point_age,
        reference_min_coverage_x=args.reference_min_coverage_x,
        reference_min_coverage_y=args.reference_min_coverage_y,
        tracker_debug_rows=tracker_rows,
    )
    capture.release()
    reliable = reliable_mask_from_tracker_rows(tracker_rows, len(trajectory))
    if args.trajectory_geometry_gate:
        reliable = apply_offline_geometry_gate(
            trajectory,
            reliable,
            max_scale_step=args.reference_max_scale_step,
            max_area_step=args.reference_max_area_step,
        )
    if args.trajectory_interpolate:
        trajectory = interpolate_corner_trajectory(trajectory, reliable)
    trajectory = smooth_corner_trajectory(
        trajectory,
        median_window=args.median_window,
        average_window=args.trajectory_window,
    )

    capture = open_capture(source)
    align_rows: list[dict[str, object]] = []
    with tempfile.TemporaryDirectory() as temporary:
        silent = Path(temporary) / "normalized_silent.mp4"
        processed = encode_warped_video(
            capture=capture,
            output=silent,
            fallback_corners=fallback,
            corner_trajectory=trajectory,
            width=args.width,
            height=args.height,
            fps=fps,
            crf=args.crf,
            preset=args.preset,
            smooth=args.smooth,
            median_window=args.median_window,
            auto_detect=auto_detect,
            crop_left=args.crop_left,
            crop_top=args.crop_top,
            crop_right=args.crop_right,
            crop_bottom=args.crop_bottom,
            reference_align=args.reference_align,
            reference_motion=args.reference_motion,
            reference_align_smooth=args.reference_align_smooth,
            reference_align_max_translation_step=args.reference_align_max_translation_step,
            reference_align_max_rotation_step_deg=args.reference_align_max_rotation_step_deg,
            reference_align_max_scale_step=args.reference_align_max_scale_step,
            reference_align_filter_window=args.reference_align_filter_window,
            reference_align_min_inliers=args.reference_align_min_inliers,
            reference_align_min_inlier_ratio=args.reference_align_min_inlier_ratio,
            reference_align_min_coverage_x=args.reference_align_min_coverage_x,
            reference_align_min_coverage_y=args.reference_align_min_coverage_y,
            reference_align_max_reprojection_error=args.reference_align_max_reprojection_error,
            reference_align_max_translation=args.reference_align_max_translation,
            reference_align_max_rotation_deg=args.reference_align_max_rotation_deg,
            reference_align_max_scale_delta=args.reference_align_max_scale_delta,
            reference_align_min_accept_ratio=args.reference_align_min_accept_ratio,
            line_roll_correction=args.line_roll_correction,
            line_detector=args.line_detector,
            line_full_mask=args.line_full_mask,
            line_mask_top=args.line_mask_top,
            line_mask_right=args.line_mask_right,
            line_mask_bottom=args.line_mask_bottom,
            line_ignore_top=args.line_ignore_top,
            line_min_segments=args.line_min_segments,
            line_min_total_length=args.line_min_total_length,
            line_cluster_deg=args.line_cluster_deg,
            line_horizontal_kernel=args.line_horizontal_kernel,
            line_max_thickness=args.line_max_thickness,
            line_white_threshold=args.line_white_threshold,
            line_background_percentile=args.line_background_percentile,
            line_dark_margin=args.line_dark_margin,
            line_saturation_threshold=args.line_saturation_threshold,
            line_max_correction_deg=args.line_max_correction_deg,
            line_max_step_deg=args.line_max_step_deg,
            line_max_measurement_step_deg=args.line_max_measurement_step_deg,
            line_smooth=args.line_smooth,
            align_debug_rows=align_rows,
        )
        mux_audio(silent, source, output)

    elapsed = time.perf_counter() - started
    write_csv(output_dir / "estimated_corners.csv", _corner_rows(trajectory))
    write_csv(output_dir / "debug.csv", tracker_rows)
    if align_rows:
        write_csv(output_dir / "align_debug.csv", align_rows)
    write_json(
        output_dir / "method.json",
        {
            "status": "ok",
            "method": method,
            "config": asdict(config),
            "processed_frames": processed,
            "elapsed_seconds": elapsed,
        },
    )
    return RunResult(method, output, processed, elapsed)
