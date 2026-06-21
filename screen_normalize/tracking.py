from __future__ import annotations

import sys

import cv2
import numpy as np

from .detection import detect_screen_corners, select_tracking_points
from .geometry import (
    corner_edge_lengths,
    detected_corners_are_valid,
    geometry_update_is_reasonable,
    homography_inlier_screen_coverage,
    homography_median_reprojection_error,
    order_corners,
)


def append_tracker_debug_row(
    rows: list[dict[str, object]] | None,
    frame: int,
    accepted: bool,
    reason: str,
    corners: np.ndarray,
    point_count: int,
    mature_point_count: int,
    valid_count: int,
    mature_valid_count: int,
    inlier_count: int,
    inlier_ratio: float,
    reprojection_error: float,
    coverage_x: float,
    coverage_y: float,
    rejected_updates: int,
) -> None:
    if rows is None:
        return

    sides = corner_edge_lengths(corners)
    area = abs(cv2.contourArea(corners.astype(np.float32)))
    center = corners.mean(axis=0)
    row: dict[str, object] = {
        "frame": frame,
        "accepted": accepted,
        "reason": reason,
        "point_count": point_count,
        "mature_point_count": mature_point_count,
        "valid_count": valid_count,
        "mature_valid_count": mature_valid_count,
        "inlier_count": inlier_count,
        "inlier_ratio": inlier_ratio,
        "reprojection_error": reprojection_error,
        "coverage_x": coverage_x,
        "coverage_y": coverage_y,
        "rejected_updates": rejected_updates,
        "area": float(area),
        "center_x": float(center[0]),
        "center_y": float(center[1]),
        "top_edge": float(sides[0]),
        "right_edge": float(sides[1]),
        "bottom_edge": float(sides[2]),
        "left_edge": float(sides[3]),
    }
    for index, label in enumerate(("tl", "tr", "br", "bl")):
        row[f"{label}_x"] = float(corners[index, 0])
        row[f"{label}_y"] = float(corners[index, 1])
    rows.append(row)


def reference_reject_reason(
    current_to_reference: np.ndarray | None,
    inlier_mask: np.ndarray | None,
    mature_valid_count: int,
    inlier_count: int,
    inlier_ratio: float,
    reprojection_error: float,
    coverage_x: float,
    coverage_y: float,
    reference_min_inliers: int,
    reference_min_inlier_ratio: float,
    reference_max_reprojection_error: float,
    reference_min_coverage_x: float,
    reference_min_coverage_y: float,
) -> str:
    if mature_valid_count < 20:
        return "not_enough_mature_points"
    if current_to_reference is None or inlier_mask is None:
        return "homography_failed"
    if inlier_count < reference_min_inliers:
        return "not_enough_inliers"
    if inlier_ratio < reference_min_inlier_ratio:
        return "low_inlier_ratio"
    if reprojection_error > reference_max_reprojection_error:
        return "high_reprojection_error"
    if coverage_x < reference_min_coverage_x:
        return "low_coverage_x"
    if coverage_y < reference_min_coverage_y:
        return "low_coverage_y"
    return "invalid_geometry"


def flow_predict_corners(
    previous_gray: np.ndarray,
    gray: np.ndarray,
    previous_points: np.ndarray | None,
    previous_corners: np.ndarray,
) -> tuple[np.ndarray | None, np.ndarray | None, int]:
    if previous_points is None or len(previous_points) < 12:
        return None, None, 0

    next_points, status, _ = cv2.calcOpticalFlowPyrLK(
        previous_gray,
        gray,
        previous_points,
        None,
        winSize=(31, 31),
        maxLevel=3,
        criteria=(cv2.TERM_CRITERIA_EPS | cv2.TERM_CRITERIA_COUNT, 30, 0.01),
    )
    if next_points is None or status is None:
        return None, None, 0

    previous_back, back_status, _ = cv2.calcOpticalFlowPyrLK(
        gray,
        previous_gray,
        next_points,
        None,
        winSize=(31, 31),
        maxLevel=3,
        criteria=(cv2.TERM_CRITERIA_EPS | cv2.TERM_CRITERIA_COUNT, 30, 0.01),
    )
    if previous_back is None or back_status is None:
        return None, None, 0

    forward_ok = status.reshape(-1).astype(bool)
    backward_ok = back_status.reshape(-1).astype(bool)
    round_trip_error = np.linalg.norm(
        previous_points.reshape(-1, 2) - previous_back.reshape(-1, 2),
        axis=1,
    )
    valid = forward_ok & backward_ok & (round_trip_error < 2.0)
    previous_good = previous_points.reshape(-1, 2)[valid]
    next_good = next_points.reshape(-1, 2)[valid]
    if len(previous_good) < 12:
        return None, next_good.reshape(-1, 1, 2).astype(np.float32), len(previous_good)

    homography, inlier_mask = cv2.findHomography(
        previous_good,
        next_good,
        cv2.RANSAC,
        3.0,
    )
    if homography is None or inlier_mask is None:
        return None, next_good.reshape(-1, 1, 2).astype(np.float32), len(previous_good)

    inliers = inlier_mask.reshape(-1).astype(bool)
    if int(inliers.sum()) < 12:
        return None, next_good.reshape(-1, 1, 2).astype(np.float32), int(inliers.sum())

    predicted = cv2.perspectiveTransform(
        previous_corners.reshape(1, 4, 2),
        homography,
    ).reshape(4, 2)
    predicted = order_corners(predicted)
    if not detected_corners_are_valid(predicted, gray.shape):
        return None, next_good[inliers].reshape(-1, 1, 2).astype(np.float32), int(inliers.sum())

    return predicted, next_good[inliers].reshape(-1, 1, 2).astype(np.float32), int(inliers.sum())


def append_reference_points(
    gray: np.ndarray,
    current_corners: np.ndarray,
    current_to_reference: np.ndarray,
    reference_points: np.ndarray,
    current_points: np.ndarray,
    point_ages: np.ndarray,
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    new_points = select_tracking_points(gray, current_corners)
    if new_points is None:
        return reference_points, current_points, point_ages

    existing = current_points.reshape(-1, 2)
    fresh = []
    for point in new_points.reshape(-1, 2):
        if len(existing) and np.min(np.linalg.norm(existing - point, axis=1)) < 8:
            continue
        fresh.append(point)
        if len(fresh) >= 250:
            break

    if not fresh:
        return reference_points, current_points, point_ages

    fresh_current = np.asarray(fresh, dtype=np.float32).reshape(-1, 1, 2)
    fresh_reference = cv2.perspectiveTransform(fresh_current, current_to_reference)
    reference_points = np.concatenate([reference_points, fresh_reference.astype(np.float32)])
    current_points = np.concatenate([current_points, fresh_current.astype(np.float32)])
    point_ages = np.concatenate(
        [point_ages, np.zeros((len(fresh_current),), dtype=np.int32)]
    )
    return reference_points, current_points, point_ages


def estimate_reference_corner_trajectory(
    capture: cv2.VideoCapture,
    fallback_corners: np.ndarray,
    auto_detect: bool,
    feature_refresh: int,
    reference_min_inliers: int,
    reference_min_inlier_ratio: float,
    reference_max_reprojection_error: float,
    reference_max_scale_step: float,
    reference_max_area_step: float,
    reference_min_point_age: int,
    reference_min_coverage_x: float,
    reference_min_coverage_y: float,
    tracker_debug_rows: list[dict[str, object]] | None,
) -> list[np.ndarray]:
    frame_count = int(capture.get(cv2.CAP_PROP_FRAME_COUNT) or 0)
    ok, first_frame = capture.read()
    if not ok:
        return []

    reference_corners = detect_screen_corners(first_frame) if auto_detect else fallback_corners
    if reference_corners is None:
        reference_corners = fallback_corners
    reference_corners = order_corners(reference_corners).astype(np.float32)

    previous_gray = cv2.cvtColor(first_frame, cv2.COLOR_BGR2GRAY)
    reference_points = select_tracking_points(previous_gray, reference_corners)
    if reference_points is None:
        reference_points = reference_corners.reshape(-1, 1, 2).astype(np.float32)
    current_points = reference_points.copy()
    point_ages = np.full((len(reference_points),), reference_min_point_age, dtype=np.int32)

    trajectory = [reference_corners]
    previous_corners = reference_corners
    frame_index = 1
    rejected_updates = 0
    append_tracker_debug_row(
        tracker_debug_rows,
        frame=0,
        accepted=True,
        reason="initial_reference",
        corners=previous_corners,
        point_count=len(current_points),
        mature_point_count=int(np.count_nonzero(point_ages >= reference_min_point_age)),
        valid_count=len(current_points),
        mature_valid_count=int(np.count_nonzero(point_ages >= reference_min_point_age)),
        inlier_count=len(current_points),
        inlier_ratio=1.0,
        reprojection_error=0.0,
        coverage_x=1.0,
        coverage_y=1.0,
        rejected_updates=rejected_updates,
    )

    while True:
        ok, frame = capture.read()
        if not ok:
            break

        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        next_points, status, _ = cv2.calcOpticalFlowPyrLK(
            previous_gray,
            gray,
            current_points,
            None,
            winSize=(31, 31),
            maxLevel=3,
            criteria=(cv2.TERM_CRITERIA_EPS | cv2.TERM_CRITERIA_COUNT, 30, 0.01),
        )
        if next_points is None or status is None:
            trajectory.append(previous_corners)
            append_tracker_debug_row(
                tracker_debug_rows,
                frame=frame_index,
                accepted=False,
                reason="flow_failed",
                corners=previous_corners,
                point_count=len(current_points),
                mature_point_count=int(np.count_nonzero(point_ages >= reference_min_point_age)),
                valid_count=0,
                mature_valid_count=0,
                inlier_count=0,
                inlier_ratio=0.0,
                reprojection_error=float("inf"),
                coverage_x=0.0,
                coverage_y=0.0,
                rejected_updates=rejected_updates,
            )
            previous_gray = gray
            frame_index += 1
            continue

        previous_back, back_status, _ = cv2.calcOpticalFlowPyrLK(
            gray,
            previous_gray,
            next_points,
            None,
            winSize=(31, 31),
            maxLevel=3,
            criteria=(cv2.TERM_CRITERIA_EPS | cv2.TERM_CRITERIA_COUNT, 30, 0.01),
        )
        if previous_back is None or back_status is None:
            trajectory.append(previous_corners)
            append_tracker_debug_row(
                tracker_debug_rows,
                frame=frame_index,
                accepted=False,
                reason="backflow_failed",
                corners=previous_corners,
                point_count=len(current_points),
                mature_point_count=int(np.count_nonzero(point_ages >= reference_min_point_age)),
                valid_count=0,
                mature_valid_count=0,
                inlier_count=0,
                inlier_ratio=0.0,
                reprojection_error=float("inf"),
                coverage_x=0.0,
                coverage_y=0.0,
                rejected_updates=rejected_updates,
            )
            previous_gray = gray
            frame_index += 1
            continue

        forward_ok = status.reshape(-1).astype(bool)
        backward_ok = back_status.reshape(-1).astype(bool)
        round_trip_error = np.linalg.norm(
            current_points.reshape(-1, 2) - previous_back.reshape(-1, 2),
            axis=1,
        )
        valid = forward_ok & backward_ok & (round_trip_error < 2.0)
        mature = valid & (point_ages >= reference_min_point_age)
        reference_good = reference_points.reshape(-1, 2)[mature]
        current_good = next_points.reshape(-1, 2)[mature]
        valid_count = int(np.count_nonzero(valid))
        mature_valid_count = int(np.count_nonzero(mature))

        if len(reference_good) >= 20:
            current_to_reference, inlier_mask = cv2.findHomography(
                current_good,
                reference_good,
                cv2.RANSAC,
                3.0,
            )
        else:
            current_to_reference, inlier_mask = None, None

        accepted_transform = None
        if current_to_reference is not None and inlier_mask is not None:
            inlier_count = int(inlier_mask.sum())
            inlier_ratio = inlier_count / max(1, len(reference_good))
            reprojection_error = homography_median_reprojection_error(
                current_good,
                reference_good,
                current_to_reference,
                inlier_mask,
            )
            coverage_x, coverage_y = homography_inlier_screen_coverage(
                reference_good,
                inlier_mask,
                reference_corners,
            )
        else:
            inlier_count = 0
            inlier_ratio = 0.0
            reprojection_error = float("inf")
            coverage_x = 0.0
            coverage_y = 0.0

        if (
            current_to_reference is not None
            and inlier_mask is not None
            and inlier_count >= reference_min_inliers
            and inlier_ratio >= reference_min_inlier_ratio
            and reprojection_error <= reference_max_reprojection_error
            and coverage_x >= reference_min_coverage_x
            and coverage_y >= reference_min_coverage_y
        ):
            reject_reason = "accepted"
            reference_to_current = np.linalg.inv(current_to_reference)
            corners = cv2.perspectiveTransform(
                reference_corners.reshape(1, 4, 2),
                reference_to_current,
            ).reshape(4, 2)
            corners = order_corners(corners).astype(np.float32)
            if detected_corners_are_valid(corners, gray.shape) and geometry_update_is_reasonable(
                corners,
                previous_corners,
                max_scale_step=reference_max_scale_step,
                max_area_step=reference_max_area_step,
            ):
                previous_corners = corners
                accepted_transform = current_to_reference
            else:
                rejected_updates += 1
                reject_reason = "invalid_geometry"
        elif current_to_reference is not None:
            rejected_updates += 1
            reject_reason = reference_reject_reason(
                current_to_reference=current_to_reference,
                inlier_mask=inlier_mask,
                mature_valid_count=mature_valid_count,
                inlier_count=inlier_count,
                inlier_ratio=inlier_ratio,
                reprojection_error=reprojection_error,
                coverage_x=coverage_x,
                coverage_y=coverage_y,
                reference_min_inliers=reference_min_inliers,
                reference_min_inlier_ratio=reference_min_inlier_ratio,
                reference_max_reprojection_error=reference_max_reprojection_error,
                reference_min_coverage_x=reference_min_coverage_x,
                reference_min_coverage_y=reference_min_coverage_y,
            )
        else:
            reject_reason = reference_reject_reason(
                current_to_reference=current_to_reference,
                inlier_mask=inlier_mask,
                mature_valid_count=mature_valid_count,
                inlier_count=inlier_count,
                inlier_ratio=inlier_ratio,
                reprojection_error=reprojection_error,
                coverage_x=coverage_x,
                coverage_y=coverage_y,
                reference_min_inliers=reference_min_inliers,
                reference_min_inlier_ratio=reference_min_inlier_ratio,
                reference_max_reprojection_error=reference_max_reprojection_error,
                reference_min_coverage_x=reference_min_coverage_x,
                reference_min_coverage_y=reference_min_coverage_y,
            )
        trajectory.append(previous_corners)

        keep = valid
        if accepted_transform is not None:
            valid_indices = np.flatnonzero(valid)
            valid_current = next_points.reshape(-1, 2)[valid]
            valid_reference = reference_points.reshape(-1, 2)[valid]
            projected_reference = cv2.perspectiveTransform(
                valid_current.reshape(-1, 1, 2).astype(np.float32),
                accepted_transform,
            ).reshape(-1, 2)
            reprojection_errors = np.linalg.norm(projected_reference - valid_reference, axis=1)
            max_keep_error = max(3.0, reference_max_reprojection_error * 1.5)
            keep = np.zeros_like(valid)
            keep[valid_indices[reprojection_errors <= max_keep_error]] = True

        reference_points = reference_points[keep]
        current_points = next_points[keep].astype(np.float32)
        point_ages = point_ages[keep]
        if accepted_transform is not None:
            point_ages += 1
        if (
            len(current_points) < 140
            or frame_index % feature_refresh == 0
        ) and accepted_transform is not None:
            reference_points, current_points, point_ages = append_reference_points(
                gray,
                previous_corners,
                accepted_transform,
                reference_points,
                current_points,
                point_ages,
            )

        append_tracker_debug_row(
            tracker_debug_rows,
            frame=frame_index,
            accepted=accepted_transform is not None,
            reason=reject_reason,
            corners=previous_corners,
            point_count=len(current_points),
            mature_point_count=int(np.count_nonzero(point_ages >= reference_min_point_age)),
            valid_count=valid_count,
            mature_valid_count=mature_valid_count,
            inlier_count=inlier_count,
            inlier_ratio=inlier_ratio,
            reprojection_error=reprojection_error,
            coverage_x=coverage_x,
            coverage_y=coverage_y,
            rejected_updates=rejected_updates,
        )

        previous_gray = gray
        frame_index += 1
        if frame_count and (frame_index % 60 == 0 or frame_index == frame_count):
            print(
                f"reference-tracked corners {frame_index}/{frame_count} frames "
                f"with {len(current_points)} points "
                f"({int(np.count_nonzero(point_ages >= reference_min_point_age))} mature), "
                f"rejected {rejected_updates} updates",
                file=sys.stderr,
            )

    return trajectory


def estimate_corner_trajectory(
    capture: cv2.VideoCapture,
    fallback_corners: np.ndarray,
    auto_detect: bool,
    tracker: str,
    smooth: float,
    detect_correction: float,
    feature_refresh: int,
    reference_min_inliers: int,
    reference_min_inlier_ratio: float,
    reference_max_reprojection_error: float,
    reference_max_scale_step: float,
    reference_max_area_step: float,
    reference_min_point_age: int,
    reference_min_coverage_x: float,
    reference_min_coverage_y: float,
    tracker_debug_rows: list[dict[str, object]] | None,
) -> list[np.ndarray]:
    if tracker == "reference":
        return estimate_reference_corner_trajectory(
            capture=capture,
            fallback_corners=fallback_corners,
            auto_detect=auto_detect,
            feature_refresh=feature_refresh,
            reference_min_inliers=reference_min_inliers,
            reference_min_inlier_ratio=reference_min_inlier_ratio,
            reference_max_reprojection_error=reference_max_reprojection_error,
            reference_max_scale_step=reference_max_scale_step,
            reference_max_area_step=reference_max_area_step,
            reference_min_point_age=reference_min_point_age,
            reference_min_coverage_x=reference_min_coverage_x,
            reference_min_coverage_y=reference_min_coverage_y,
            tracker_debug_rows=tracker_debug_rows,
        )

    frame_count = int(capture.get(cv2.CAP_PROP_FRAME_COUNT) or 0)
    trajectory: list[np.ndarray] = []
    previous_gray: np.ndarray | None = None
    previous_points: np.ndarray | None = None
    previous_corners: np.ndarray | None = None
    frame_index = 0

    while True:
        ok, frame = capture.read()
        if not ok:
            break

        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        detected_corners = detect_screen_corners(frame) if auto_detect else None
        predicted_corners = None
        tracked_points = None
        inliers = 0

        if tracker == "flow" and previous_gray is not None and previous_corners is not None:
            predicted_corners, tracked_points, inliers = flow_predict_corners(
                previous_gray,
                gray,
                previous_points,
                previous_corners,
            )

        if previous_corners is None:
            corners = detected_corners if detected_corners is not None else fallback_corners
        elif predicted_corners is not None:
            if detected_corners is not None:
                corners = (predicted_corners * (1.0 - detect_correction)) + (
                    detected_corners * detect_correction
                )
            else:
                corners = predicted_corners
        elif detected_corners is not None:
            corners = detected_corners
        else:
            corners = previous_corners

        if previous_corners is not None and smooth:
            corners = (previous_corners * smooth) + (corners * (1.0 - smooth))

        corners = order_corners(corners)
        trajectory.append(corners.astype(np.float32))

        previous_gray = gray
        previous_corners = corners.astype(np.float32)
        if tracker == "flow":
            should_refresh = (
                tracked_points is None
                or len(tracked_points) < 80
                or inliers < 60
                or frame_index % feature_refresh == 0
            )
            previous_points = select_tracking_points(gray, previous_corners) if should_refresh else tracked_points

        frame_index += 1
        if frame_count and (frame_index % 60 == 0 or frame_index == frame_count):
            print(f"estimated corners {frame_index}/{frame_count} frames", file=sys.stderr)

    return trajectory
