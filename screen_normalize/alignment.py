from __future__ import annotations

import cv2
import numpy as np

from .trajectory import centered_window_filter
from .warp import warp_screen_frame


def select_reference_points(gray: np.ndarray) -> np.ndarray | None:
    margin_x = max(20, gray.shape[1] // 50)
    margin_y = max(20, gray.shape[0] // 50)
    mask = np.zeros(gray.shape, dtype=np.uint8)
    mask[margin_y : gray.shape[0] - margin_y, margin_x : gray.shape[1] - margin_x] = 255
    points = cv2.goodFeaturesToTrack(
        gray,
        maxCorners=1200,
        qualityLevel=0.004,
        minDistance=9,
        mask=mask,
        blockSize=7,
    )
    if points is None or len(points) < 20:
        return None
    return points.astype(np.float32)


def transform_motion_components(transform: np.ndarray | None) -> dict[str, float]:
    if transform is None:
        return {
            "translation_x": float("nan"),
            "translation_y": float("nan"),
            "rotation_deg": float("nan"),
            "scale_x": float("nan"),
            "scale_y": float("nan"),
            "scale_avg": float("nan"),
            "perspective_x": float("nan"),
            "perspective_y": float("nan"),
        }

    matrix = transform.astype(np.float64)
    a = matrix[0, 0]
    b = matrix[0, 1]
    c = matrix[1, 0]
    d = matrix[1, 1]
    scale_x = float(np.hypot(a, c))
    scale_y = float(np.hypot(b, d))
    return {
        "translation_x": float(matrix[0, 2]),
        "translation_y": float(matrix[1, 2]),
        "rotation_deg": float(np.degrees(np.arctan2(c, a))),
        "scale_x": scale_x,
        "scale_y": scale_y,
        "scale_avg": float((scale_x + scale_y) * 0.5),
        "perspective_x": float(matrix[2, 0]),
        "perspective_y": float(matrix[2, 1]),
    }


def similarity_transform_from_components(
    translation_x: float,
    translation_y: float,
    rotation_deg: float,
    scale: float,
) -> np.ndarray:
    angle = np.radians(rotation_deg)
    cos_value = float(np.cos(angle) * scale)
    sin_value = float(np.sin(angle) * scale)
    return np.array(
        [
            [cos_value, -sin_value, translation_x],
            [sin_value, cos_value, translation_y],
            [0.0, 0.0, 1.0],
        ],
        dtype=np.float32,
    )


def step_limited_value(previous: float, target: float, max_step: float) -> float:
    if max_step <= 0:
        return target
    return previous + float(np.clip(target - previous, -max_step, max_step))


def smooth_residual_affine_transform(
    previous_transform: np.ndarray,
    measured_transform: np.ndarray,
    smooth: float,
    max_translation_step: float,
    max_rotation_step_deg: float,
    max_scale_step: float,
) -> np.ndarray:
    if (
        smooth <= 0
        and max_translation_step <= 0
        and max_rotation_step_deg <= 0
        and max_scale_step <= 0
    ):
        return measured_transform

    previous = transform_motion_components(previous_transform)
    measured = transform_motion_components(measured_transform)

    previous_scale = float(previous["scale_avg"])
    measured_scale = float(measured["scale_avg"])

    target_tx = float(previous["translation_x"]) * smooth + float(measured["translation_x"]) * (
        1.0 - smooth
    )
    target_ty = float(previous["translation_y"]) * smooth + float(measured["translation_y"]) * (
        1.0 - smooth
    )
    target_rotation = float(previous["rotation_deg"]) * smooth + float(
        measured["rotation_deg"]
    ) * (1.0 - smooth)
    target_scale = previous_scale * smooth + measured_scale * (1.0 - smooth)

    translation_x = step_limited_value(
        float(previous["translation_x"]),
        target_tx,
        max_translation_step,
    )
    translation_y = step_limited_value(
        float(previous["translation_y"]),
        target_ty,
        max_translation_step,
    )
    rotation_deg = step_limited_value(
        float(previous["rotation_deg"]),
        target_rotation,
        max_rotation_step_deg,
    )
    scale = step_limited_value(previous_scale, target_scale, max_scale_step)
    return similarity_transform_from_components(translation_x, translation_y, rotation_deg, scale)


def smooth_residual_affine_trajectory(
    transforms: list[np.ndarray],
    median_window: int,
    average_window: int,
) -> list[np.ndarray]:
    if not transforms:
        return []

    components = np.asarray(
        [
            [
                transform_motion_components(transform)["translation_x"],
                transform_motion_components(transform)["translation_y"],
                transform_motion_components(transform)["rotation_deg"],
                transform_motion_components(transform)["scale_avg"],
            ]
            for transform in transforms
        ],
        dtype=np.float32,
    )
    components = centered_window_filter(components, median_window, "median")
    components = centered_window_filter(components, average_window, "mean")
    return [
        similarity_transform_from_components(
            translation_x=float(row[0]),
            translation_y=float(row[1]),
            rotation_deg=float(row[2]),
            scale=float(row[3]),
        )
        for row in components
    ]


def add_applied_alignment_components(row: dict[str, object], transform: np.ndarray) -> None:
    components = transform_motion_components(transform)
    for key, value in components.items():
        row[f"applied_{key}"] = value


def alignment_inlier_coverage(
    reference_points: np.ndarray,
    inlier_mask: np.ndarray | None,
    width: int,
    height: int,
) -> tuple[float, float]:
    if inlier_mask is None:
        return 0.0, 0.0
    inliers = inlier_mask.reshape(-1).astype(bool)
    if int(inliers.sum()) < 2:
        return 0.0, 0.0

    points = reference_points.reshape(-1, 2)[inliers]
    lower = np.percentile(points, 5, axis=0)
    upper = np.percentile(points, 95, axis=0)
    coverage = np.maximum(upper - lower, 0.0)
    return float(coverage[0] / max(1, width)), float(coverage[1] / max(1, height))


def alignment_median_reprojection_error(
    current_points: np.ndarray,
    reference_points: np.ndarray,
    transform: np.ndarray,
    inlier_mask: np.ndarray,
) -> float:
    inliers = inlier_mask.reshape(-1).astype(bool)
    if not np.any(inliers):
        return float("inf")
    projected = cv2.perspectiveTransform(
        current_points[inliers].reshape(-1, 1, 2).astype(np.float32),
        transform.astype(np.float32),
    ).reshape(-1, 2)
    errors = np.linalg.norm(projected - reference_points[inliers], axis=1)
    return float(np.median(errors))


def empty_alignment_debug(
    reason: str,
    motion: str,
    reference_point_count: int,
    valid_count: int = 0,
) -> dict[str, object]:
    row: dict[str, object] = {
        "accepted": False,
        "reason": reason,
        "motion": motion,
        "reference_point_count": reference_point_count,
        "valid_count": valid_count,
        "inlier_count": 0,
        "inlier_ratio": 0.0,
        "coverage_x": 0.0,
        "coverage_y": 0.0,
        "reprojection_error": float("inf"),
    }
    row.update(transform_motion_components(None))
    return row


def estimate_reference_alignment(
    reference_gray: np.ndarray,
    gray: np.ndarray,
    reference_points: np.ndarray | None,
    motion: str,
    min_inliers: int,
    min_inlier_ratio: float,
    min_coverage_x: float,
    min_coverage_y: float,
    max_reprojection_error: float,
    max_translation: float,
    max_rotation_deg: float,
    max_scale_delta: float,
) -> tuple[np.ndarray | None, dict[str, object]]:
    if reference_points is None or len(reference_points) < 20:
        return None, empty_alignment_debug(
            reason="not_enough_reference_points",
            motion=motion,
            reference_point_count=0 if reference_points is None else len(reference_points),
        )

    current_points, status, _ = cv2.calcOpticalFlowPyrLK(
        reference_gray,
        gray,
        reference_points,
        None,
        winSize=(41, 41),
        maxLevel=4,
        criteria=(cv2.TERM_CRITERIA_EPS | cv2.TERM_CRITERIA_COUNT, 60, 0.001),
    )
    if current_points is None or status is None:
        return None, empty_alignment_debug(
            reason="flow_failed",
            motion=motion,
            reference_point_count=len(reference_points),
        )

    reference_back, back_status, _ = cv2.calcOpticalFlowPyrLK(
        gray,
        reference_gray,
        current_points,
        None,
        winSize=(41, 41),
        maxLevel=4,
        criteria=(cv2.TERM_CRITERIA_EPS | cv2.TERM_CRITERIA_COUNT, 60, 0.001),
    )
    if reference_back is None or back_status is None:
        return None, empty_alignment_debug(
            reason="backflow_failed",
            motion=motion,
            reference_point_count=len(reference_points),
        )

    forward_ok = status.reshape(-1).astype(bool)
    backward_ok = back_status.reshape(-1).astype(bool)
    round_trip_error = np.linalg.norm(
        reference_points.reshape(-1, 2) - reference_back.reshape(-1, 2),
        axis=1,
    )
    valid = forward_ok & backward_ok & (round_trip_error < 1.5)
    reference_good = reference_points.reshape(-1, 2)[valid]
    current_good = current_points.reshape(-1, 2)[valid]
    valid_count = len(reference_good)
    if len(reference_good) < 20:
        return None, empty_alignment_debug(
            reason="not_enough_valid_points",
            motion=motion,
            reference_point_count=len(reference_points),
            valid_count=valid_count,
        )

    if motion == "homography":
        transform, inlier_mask = cv2.findHomography(current_good, reference_good, cv2.RANSAC, 2.0)
        if transform is None or inlier_mask is None:
            return None, empty_alignment_debug(
                reason="homography_failed",
                motion=motion,
                reference_point_count=len(reference_points),
                valid_count=valid_count,
            )
        if int(inlier_mask.sum()) < 20:
            return None, empty_alignment_debug(
                reason="too_few_inliers",
                motion=motion,
                reference_point_count=len(reference_points),
                valid_count=valid_count,
            )
        transform = transform.astype(np.float32)
    else:
        affine, inlier_mask = cv2.estimateAffinePartial2D(
            current_good,
            reference_good,
            method=cv2.RANSAC,
            ransacReprojThreshold=2.0,
            maxIters=3000,
            confidence=0.995,
        )
        if affine is None or inlier_mask is None:
            return None, empty_alignment_debug(
                reason="affine_failed",
                motion=motion,
                reference_point_count=len(reference_points),
                valid_count=valid_count,
            )
        if int(inlier_mask.sum()) < 20:
            return None, empty_alignment_debug(
                reason="too_few_inliers",
                motion=motion,
                reference_point_count=len(reference_points),
                valid_count=valid_count,
            )
        transform = np.eye(3, dtype=np.float32)
        transform[:2] = affine.astype(np.float32)

    inlier_count = int(inlier_mask.sum())
    debug_row: dict[str, object] = {
        "accepted": True,
        "reason": "accepted",
        "motion": motion,
        "reference_point_count": len(reference_points),
        "valid_count": valid_count,
        "inlier_count": inlier_count,
        "inlier_ratio": inlier_count / max(1, valid_count),
        "reprojection_error": alignment_median_reprojection_error(
            current_good,
            reference_good,
            transform,
            inlier_mask,
        ),
    }
    coverage_x, coverage_y = alignment_inlier_coverage(
        reference_good,
        inlier_mask,
        width=gray.shape[1],
        height=gray.shape[0],
    )
    debug_row["coverage_x"] = coverage_x
    debug_row["coverage_y"] = coverage_y
    components = transform_motion_components(transform)
    debug_row.update(components)

    translation = float(
        np.hypot(
            float(components["translation_x"]),
            float(components["translation_y"]),
        )
    )
    scale_delta = abs(float(components["scale_avg"]) - 1.0)
    reject_reason = None
    if inlier_count < min_inliers:
        reject_reason = "too_few_inliers"
    elif float(debug_row["inlier_ratio"]) < min_inlier_ratio:
        reject_reason = "low_inlier_ratio"
    elif coverage_x < min_coverage_x:
        reject_reason = "low_coverage_x"
    elif coverage_y < min_coverage_y:
        reject_reason = "low_coverage_y"
    elif (
        max_reprojection_error > 0
        and float(debug_row["reprojection_error"]) > max_reprojection_error
    ):
        reject_reason = "high_reprojection_error"
    elif max_translation > 0 and translation > max_translation:
        reject_reason = "large_translation"
    elif max_rotation_deg > 0 and abs(float(components["rotation_deg"])) > max_rotation_deg:
        reject_reason = "large_rotation"
    elif max_scale_delta > 0 and scale_delta > max_scale_delta:
        reject_reason = "large_scale_delta"

    if reject_reason is not None:
        debug_row["accepted"] = False
        debug_row["reason"] = reject_reason
        return None, debug_row
    return transform, debug_row


def reference_frame_alignment_debug(
    frame_index: int,
    reference_motion: str,
    reference_points: np.ndarray | None,
    width: int,
    height: int,
) -> dict[str, object]:
    point_count = 0 if reference_points is None else len(reference_points)
    debug_row: dict[str, object] = {
        "frame": frame_index,
        "accepted": True,
        "reason": "reference_frame",
        "motion": reference_motion,
        "reference_point_count": point_count,
        "valid_count": point_count,
        "inlier_count": point_count,
        "inlier_ratio": 1.0 if point_count else 0.0,
        "coverage_x": 0.0,
        "coverage_y": 0.0,
        "reprojection_error": 0.0,
    }
    if reference_points is not None:
        mask = np.ones((len(reference_points), 1), dtype=np.uint8)
        coverage_x, coverage_y = alignment_inlier_coverage(
            reference_points.reshape(-1, 2),
            mask,
            width=width,
            height=height,
        )
        debug_row["coverage_x"] = coverage_x
        debug_row["coverage_y"] = coverage_y
    debug_row.update(transform_motion_components(np.eye(3, dtype=np.float32)))
    return debug_row


def estimate_residual_alignment_trajectory(
    capture: cv2.VideoCapture,
    fallback_corners: np.ndarray,
    fallback_transform: np.ndarray,
    destination_corners: np.ndarray,
    corner_trajectory: list[np.ndarray] | None,
    width: int,
    height: int,
    smooth: float,
    auto_detect: bool,
    crop_left: float,
    crop_top: float,
    crop_right: float,
    crop_bottom: float,
    reference_motion: str,
    reference_align_min_inliers: int,
    reference_align_min_inlier_ratio: float,
    reference_align_min_coverage_x: float,
    reference_align_min_coverage_y: float,
    reference_align_max_reprojection_error: float,
    reference_align_max_translation: float,
    reference_align_max_rotation_deg: float,
    reference_align_max_scale_delta: float,
    median_window: int,
    average_window: int,
) -> tuple[list[np.ndarray], list[dict[str, object]], float]:
    frame_count = int(capture.get(cv2.CAP_PROP_FRAME_COUNT) or 0)
    reference_gray: np.ndarray | None = None
    reference_points: np.ndarray | None = None
    last_corners: np.ndarray | None = None
    measured_transforms: list[np.ndarray] = []
    debug_rows: list[dict[str, object]] = []
    previous_transform = np.eye(3, dtype=np.float32)
    processed = 0

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
        gray = cv2.cvtColor(warped, cv2.COLOR_BGR2GRAY)
        if reference_gray is None:
            reference_gray = gray
            reference_points = select_reference_points(reference_gray)
            measured_transform = np.eye(3, dtype=np.float32)
            debug_row = reference_frame_alignment_debug(
                frame_index=processed,
                reference_motion=reference_motion,
                reference_points=reference_points,
                width=gray.shape[1],
                height=gray.shape[0],
            )
        else:
            measured_transform, debug_row = estimate_reference_alignment(
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
            debug_row = {"frame": processed, **debug_row}
            if measured_transform is None:
                measured_transform = previous_transform

        measured_transforms.append(measured_transform)
        previous_transform = measured_transform
        debug_rows.append(debug_row)
        processed += 1
        if frame_count and (processed % 60 == 0 or processed == frame_count):
            print(
                f"precomputed residual alignment {processed}/{frame_count} frames",
                file=sys.stderr,
            )

    filtered_transforms = smooth_residual_affine_trajectory(
        measured_transforms,
        median_window=median_window,
        average_window=average_window,
    )
    accepted_count = sum(1 for row in debug_rows if row["accepted"])
    accept_ratio = accepted_count / max(1, len(debug_rows))
    capture.set(cv2.CAP_PROP_POS_FRAMES, 0)
    return filtered_transforms, debug_rows, accept_ratio
