from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import cv2
import numpy as np

from .alignment import (
    add_applied_alignment_components,
    estimate_reference_alignment,
    estimate_residual_alignment_trajectory,
    reference_frame_alignment_debug,
    select_reference_points,
    smooth_residual_affine_transform,
)
from .line_roll import (
    apply_roll_correction,
    estimate_line_roll_angle,
    update_line_roll_angle,
)
from .warp import warp_screen_frame


def encode_warped_video(
    capture: cv2.VideoCapture,
    output: Path,
    fallback_corners: np.ndarray,
    corner_trajectory: list[np.ndarray] | None,
    width: int,
    height: int,
    fps: float,
    crf: int,
    preset: str,
    smooth: float,
    median_window: int,
    auto_detect: bool,
    crop_left: float,
    crop_top: float,
    crop_right: float,
    crop_bottom: float,
    reference_align: bool,
    reference_motion: str,
    reference_align_smooth: float,
    reference_align_max_translation_step: float,
    reference_align_max_rotation_step_deg: float,
    reference_align_max_scale_step: float,
    reference_align_filter_window: int,
    reference_align_min_inliers: int,
    reference_align_min_inlier_ratio: float,
    reference_align_min_coverage_x: float,
    reference_align_min_coverage_y: float,
    reference_align_max_reprojection_error: float,
    reference_align_max_translation: float,
    reference_align_max_rotation_deg: float,
    reference_align_max_scale_delta: float,
    reference_align_min_accept_ratio: float,
    line_roll_correction: bool,
    line_detector: str,
    line_full_mask: bool,
    line_mask_top: float,
    line_mask_right: float,
    line_mask_bottom: float,
    line_ignore_top: float,
    line_min_segments: int,
    line_min_total_length: int,
    line_cluster_deg: float,
    line_horizontal_kernel: int,
    line_max_thickness: int,
    line_white_threshold: int,
    line_background_percentile: float,
    line_dark_margin: float,
    line_saturation_threshold: int,
    line_max_correction_deg: float,
    line_max_step_deg: float,
    line_max_measurement_step_deg: float,
    line_smooth: float,
    align_debug_rows: list[dict[str, object]] | None,
) -> int:
    destination_corners = np.array(
        [[0, 0], [width - 1, 0], [width - 1, height - 1], [0, height - 1]],
        dtype=np.float32,
    )
    frame_count = int(capture.get(cv2.CAP_PROP_FRAME_COUNT) or 0)
    last_corners: np.ndarray | None = None
    fallback_transform = cv2.getPerspectiveTransform(fallback_corners, destination_corners)
    reference_gray: np.ndarray | None = None
    reference_points: np.ndarray | None = None
    residual_applied_transform = np.eye(3, dtype=np.float32)
    line_roll_angle: float | None = None
    line_roll_updates = 0
    line_roll_misses = 0
    residual_alignment_trajectory: list[np.ndarray] | None = None
    residual_alignment_globally_disabled = False

    if (
        reference_align
        and reference_motion == "affine"
        and (reference_align_filter_window > 1 or reference_align_min_accept_ratio > 0)
        and not line_roll_correction
    ):
        residual_median_window = median_window if reference_align_filter_window > 1 else 1
        (
            candidate_alignment_trajectory,
            candidate_align_debug_rows,
            residual_accept_ratio,
        ) = estimate_residual_alignment_trajectory(
            capture=capture,
            fallback_corners=fallback_corners,
            fallback_transform=fallback_transform,
            destination_corners=destination_corners,
            corner_trajectory=corner_trajectory,
            width=width,
            height=height,
            smooth=smooth,
            auto_detect=auto_detect,
            crop_left=crop_left,
            crop_top=crop_top,
            crop_right=crop_right,
            crop_bottom=crop_bottom,
            reference_motion=reference_motion,
            reference_align_min_inliers=reference_align_min_inliers,
            reference_align_min_inlier_ratio=reference_align_min_inlier_ratio,
            reference_align_min_coverage_x=reference_align_min_coverage_x,
            reference_align_min_coverage_y=reference_align_min_coverage_y,
            reference_align_max_reprojection_error=reference_align_max_reprojection_error,
            reference_align_max_translation=reference_align_max_translation,
            reference_align_max_rotation_deg=reference_align_max_rotation_deg,
            reference_align_max_scale_delta=reference_align_max_scale_delta,
            median_window=residual_median_window,
            average_window=reference_align_filter_window,
        )
        residual_alignment_enabled = (
            reference_align_min_accept_ratio <= 0
            or residual_accept_ratio >= reference_align_min_accept_ratio
        )
        residual_alignment_globally_disabled = not residual_alignment_enabled
        if residual_alignment_enabled:
            residual_alignment_trajectory = candidate_alignment_trajectory
        if align_debug_rows is not None:
            for row, transform in zip(
                candidate_align_debug_rows,
                candidate_alignment_trajectory,
                strict=True,
            ):
                row["global_accept_ratio"] = residual_accept_ratio
                row["global_enabled"] = residual_alignment_enabled
                if residual_alignment_enabled:
                    add_applied_alignment_components(row, transform)
                else:
                    add_applied_alignment_components(row, np.eye(3, dtype=np.float32))
                align_debug_rows.append(row)

    command = [
        "ffmpeg",
        "-y",
        "-loglevel",
        "error",
        "-f",
        "rawvideo",
        "-vcodec",
        "rawvideo",
        "-pix_fmt",
        "bgr24",
        "-s",
        f"{width}x{height}",
        "-r",
        f"{fps:.6f}",
        "-i",
        "-",
        "-an",
        "-c:v",
        "libx264",
        "-preset",
        preset,
        "-crf",
        str(crf),
        "-pix_fmt",
        "yuv420p",
        str(output),
    ]
    process = subprocess.Popen(command, stdin=subprocess.PIPE)
    if process.stdin is None:
        raise RuntimeError("failed to open ffmpeg stdin")

    processed = 0
    try:
        while True:
            ok, frame = capture.read()
            if not ok:
                break
            warped, last_corners = warp_screen_frame(
                frame=frame,
                frame_index=processed,
                fallback_corners=fallback_corners,
                fallback_transform=fallback_transform,
                destination_corners=destination_corners,
                corner_trajectory=corner_trajectory,
                last_corners=last_corners,
                width=width,
                height=height,
                smooth=smooth,
                auto_detect=auto_detect,
                crop_left=crop_left,
                crop_top=crop_top,
                crop_right=crop_right,
                crop_bottom=crop_bottom,
            )

            if line_roll_correction:
                measured_angle, segment_count, total_length = estimate_line_roll_angle(
                    warped,
                    detector=line_detector,
                    full_mask=line_full_mask,
                    top_fraction=line_mask_top,
                    right_fraction=line_mask_right,
                    bottom_fraction=line_mask_bottom,
                    ignore_top_fraction=line_ignore_top,
                    min_segments=line_min_segments,
                    min_total_length=line_min_total_length,
                    cluster_deg=line_cluster_deg,
                    horizontal_kernel=line_horizontal_kernel,
                    max_thickness=line_max_thickness,
                    white_threshold=line_white_threshold,
                    background_percentile=line_background_percentile,
                    dark_margin=line_dark_margin,
                    saturation_threshold=line_saturation_threshold,
                )
                if measured_angle is None:
                    line_roll_misses += 1
                    if line_roll_angle is not None:
                        warped = apply_roll_correction(warped, line_roll_angle)
                elif (
                    line_roll_angle is not None
                    and line_max_measurement_step_deg > 0
                    and abs(measured_angle - line_roll_angle) > line_max_measurement_step_deg
                ):
                    line_roll_misses += 1
                    warped = apply_roll_correction(warped, line_roll_angle)
                else:
                    line_roll_angle = update_line_roll_angle(
                        previous_angle=line_roll_angle,
                        measured_angle=measured_angle,
                        max_correction=line_max_correction_deg,
                        max_step=line_max_step_deg,
                        smooth=line_smooth,
                    )
                    warped = apply_roll_correction(warped, line_roll_angle)
                    line_roll_updates += 1

            if residual_alignment_trajectory is not None:
                residual_transform = residual_alignment_trajectory[
                    min(processed, len(residual_alignment_trajectory) - 1)
                ]
                warped = cv2.warpPerspective(
                    warped,
                    residual_transform,
                    (width, height),
                    flags=cv2.INTER_CUBIC,
                    borderMode=cv2.BORDER_REPLICATE,
                )
            elif reference_align and not residual_alignment_globally_disabled:
                gray = cv2.cvtColor(warped, cv2.COLOR_BGR2GRAY)
                if reference_gray is None:
                    reference_gray = gray
                    reference_points = select_reference_points(reference_gray)
                    if align_debug_rows is not None:
                        debug_row = reference_frame_alignment_debug(
                            frame_index=processed,
                            reference_motion=reference_motion,
                            reference_points=reference_points,
                            width=gray.shape[1],
                            height=gray.shape[0],
                        )
                        add_applied_alignment_components(
                            debug_row,
                            np.eye(3, dtype=np.float32),
                        )
                        align_debug_rows.append(debug_row)
                else:
                    residual_transform, align_debug = estimate_reference_alignment(
                        reference_gray,
                        gray,
                        reference_points,
                        reference_motion,
                        min_inliers=reference_align_min_inliers,
                        min_inlier_ratio=reference_align_min_inlier_ratio,
                        min_coverage_x=reference_align_min_coverage_x,
                        min_coverage_y=reference_align_min_coverage_y,
                        max_reprojection_error=reference_align_max_reprojection_error,
                        max_translation=reference_align_max_translation,
                        max_rotation_deg=reference_align_max_rotation_deg,
                        max_scale_delta=reference_align_max_scale_delta,
                    )
                    if residual_transform is not None:
                        if reference_motion == "affine":
                            residual_transform = smooth_residual_affine_transform(
                                previous_transform=residual_applied_transform,
                                measured_transform=residual_transform,
                                smooth=reference_align_smooth,
                                max_translation_step=reference_align_max_translation_step,
                                max_rotation_step_deg=reference_align_max_rotation_step_deg,
                                max_scale_step=reference_align_max_scale_step,
                            )
                        residual_applied_transform = residual_transform
                    if align_debug_rows is not None:
                        if residual_transform is not None:
                            add_applied_alignment_components(align_debug, residual_transform)
                        else:
                            add_applied_alignment_components(
                                align_debug,
                                np.eye(3, dtype=np.float32),
                            )
                        align_debug_rows.append({"frame": processed, **align_debug})
                    if residual_transform is not None:
                        warped = cv2.warpPerspective(
                            warped,
                            residual_transform,
                            (width, height),
                            flags=cv2.INTER_CUBIC,
                            borderMode=cv2.BORDER_REPLICATE,
                        )
            process.stdin.write(warped.tobytes())
            processed += 1
            if frame_count and (processed % 60 == 0 or processed == frame_count):
                if line_roll_correction:
                    angle_text = "none" if line_roll_angle is None else f"{line_roll_angle:.3f} deg"
                    print(
                        f"processed {processed}/{frame_count} frames, "
                        f"line roll {angle_text}, updates {line_roll_updates}, "
                        f"misses {line_roll_misses}",
                        file=sys.stderr,
                    )
                else:
                    print(f"processed {processed}/{frame_count} frames", file=sys.stderr)
    finally:
        process.stdin.close()
        capture.release()

    return_code = process.wait()
    if return_code != 0:
        raise SystemExit(f"ffmpeg encode failed with exit code {return_code}")
    return processed


def mux_audio(video_without_audio: Path, source: Path, output: Path) -> None:
    command = [
        "ffmpeg",
        "-y",
        "-loglevel",
        "error",
        "-i",
        str(video_without_audio),
        "-i",
        str(source),
        "-map",
        "0:v:0",
        "-map",
        "1:a?",
        "-c:v",
        "copy",
        "-c:a",
        "copy",
        "-shortest",
        str(output),
    ]
    subprocess.run(command, check=True)
