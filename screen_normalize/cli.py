from __future__ import annotations

import argparse

import tempfile
from pathlib import Path

from .common import (
    DEFAULT_FALLBACK_CORNERS,
    open_capture,
    parse_corners,
    require_ffmpeg,
    resolve_run_output,
)
from .debug_io import write_align_debug_csv, write_tracker_debug_csv, write_trajectory_debug_csv
from .encoding import encode_warped_video, mux_audio
from .normalize_args import apply_reference_profile, parse_args
from .tracking import estimate_corner_trajectory
from .trajectory import (
    apply_offline_geometry_gate,
    build_trajectory_debug_rows,
    interpolate_corner_trajectory,
    reliable_mask_from_tracker_rows,
    smooth_corner_trajectory,
)


def main() -> None:
    args = parse_args()
    apply_reference_profile(args)
    require_ffmpeg()

    source = args.input.resolve()
    capture = open_capture(source)
    output, run_dir = resolve_run_output(args, source)
    if source == output:
        raise SystemExit("input and output must be different files")

    fps = args.fps or float(capture.get(cv2.CAP_PROP_FPS) or 60.0)
    if fps <= 0:
        fps = 60.0

    fallback_corners = args.corners
    auto_detect = fallback_corners is None
    if fallback_corners is None:
        fallback_corners = parse_corners(DEFAULT_FALLBACK_CORNERS)

    with tempfile.TemporaryDirectory() as tmp:
        corner_trajectory = None
        tracker_debug_rows: list[dict[str, object]] | None = (
            [] if args.write_tracker_debug else None
        )
        trajectory_debug_rows: list[dict[str, object]] | None = (
            [] if args.write_trajectory_debug else None
        )
        needs_internal_tracker_rows = args.trajectory_interpolate or args.write_trajectory_debug
        trajectory_tracker_rows = (
            tracker_debug_rows
            if tracker_debug_rows is not None
            else ([] if needs_internal_tracker_rows else None)
        )
        align_debug_rows: list[dict[str, object]] | None = [] if args.write_align_debug else None
        should_estimate_trajectory = auto_detect or args.tracker in ("flow", "reference")
        if should_estimate_trajectory:
            raw_corner_trajectory = estimate_corner_trajectory(
                capture=capture,
                fallback_corners=fallback_corners,
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
                tracker_debug_rows=trajectory_tracker_rows,
            )
            capture.release()
            reliable_mask = reliable_mask_from_tracker_rows(
                trajectory_tracker_rows,
                len(raw_corner_trajectory),
            )
            if args.trajectory_geometry_gate:
                reliable_mask = apply_offline_geometry_gate(
                    raw_corner_trajectory,
                    reliable_mask,
                    max_scale_step=args.reference_max_scale_step,
                    max_area_step=args.reference_max_area_step,
                )
            interpolated_corner_trajectory = (
                interpolate_corner_trajectory(raw_corner_trajectory, reliable_mask)
                if args.trajectory_interpolate
                else raw_corner_trajectory
            )
            corner_trajectory = smooth_corner_trajectory(
                interpolated_corner_trajectory,
                median_window=args.median_window,
                average_window=args.trajectory_window,
            )
            if trajectory_debug_rows is not None:
                trajectory_debug_rows.extend(
                    build_trajectory_debug_rows(
                        raw_trajectory=raw_corner_trajectory,
                        reliable=reliable_mask,
                        interpolated_trajectory=interpolated_corner_trajectory,
                        smoothed_trajectory=corner_trajectory,
                    )
                )
            capture = open_capture(source)

        silent_video = Path(tmp) / "screen_normalized_silent.mp4"
        processed = encode_warped_video(
            capture=capture,
            output=silent_video,
            fallback_corners=fallback_corners,
            corner_trajectory=corner_trajectory,
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
            align_debug_rows=align_debug_rows,
        )
        mux_audio(silent_video, source, output)

    if tracker_debug_rows is not None:
        tracker_debug_output = run_dir / "tracker_debug.csv"
        write_tracker_debug_csv(tracker_debug_output, tracker_debug_rows)
        print(f"wrote {tracker_debug_output}")
    if trajectory_debug_rows is not None:
        trajectory_debug_output = run_dir / "trajectory_debug.csv"
        write_trajectory_debug_csv(trajectory_debug_output, trajectory_debug_rows)
        print(f"wrote {trajectory_debug_output}")
    if align_debug_rows is not None:
        align_debug_output = run_dir / "align_debug.csv"
        write_align_debug_csv(align_debug_output, align_debug_rows)
        print(f"wrote {align_debug_output}")

    print(f"run directory: {run_dir}")
    print(f"wrote {output} from {processed} frames")
