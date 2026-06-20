#!/usr/bin/env python3
# /// script
# dependencies = [
#   "numpy>=2.2.0",
#   "opencv-python-headless>=4.12.0.88",
# ]
# ///

from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

import cv2
import numpy as np


DEFAULT_FALLBACK_CORNERS = "124,116:1488,132:1516,850:145,934"


def parse_corners(value: str) -> np.ndarray:
    points = []
    for raw_point in value.split(":"):
        coords = raw_point.split(",")
        if len(coords) != 2:
            raise argparse.ArgumentTypeError(
                "corners must be x,y:x,y:x,y:x,y in TL,TR,BR,BL order"
            )
        try:
            points.append([float(coords[0]), float(coords[1])])
        except ValueError as exc:
            raise argparse.ArgumentTypeError("corner coordinates must be numeric") from exc

    if len(points) != 4:
        raise argparse.ArgumentTypeError("exactly four corners are required")

    return np.array(points, dtype=np.float32)


def positive_int(value: str) -> int:
    parsed = int(value)
    if parsed <= 0:
        raise argparse.ArgumentTypeError("value must be positive")
    return parsed


def odd_positive_int(value: str) -> int:
    parsed = positive_int(value)
    if parsed % 2 == 0:
        raise argparse.ArgumentTypeError("value must be odd")
    return parsed


def smoothing_weight(value: str) -> float:
    parsed = float(value)
    if not 0.0 <= parsed < 1.0:
        raise argparse.ArgumentTypeError("value must be >= 0 and < 1")
    return parsed


def crop_fraction(value: str) -> float:
    parsed = float(value)
    if not 0.0 <= parsed < 0.4:
        raise argparse.ArgumentTypeError("value must be >= 0 and < 0.4")
    return parsed


def nonnegative_fraction(value: str) -> float:
    parsed = float(value)
    if parsed < 0.0:
        raise argparse.ArgumentTypeError("value must be >= 0")
    return parsed


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Perspective-correct a filmed monitor into a screen-recording-like video."
    )
    parser.add_argument("input", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument(
        "--corners",
        type=parse_corners,
        default=None,
        help=(
            "Manual source screen corners in TL,TR,BR,BL order, formatted as "
            "x,y:x,y:x,y:x,y. If omitted, corners are detected per frame."
        ),
    )
    parser.add_argument(
        "--smooth",
        type=smoothing_weight,
        default=0.0,
        help="Previous-frame corner smoothing weight for auto detection.",
    )
    parser.add_argument("--width", type=positive_int, default=1920)
    parser.add_argument("--height", type=positive_int, default=1080)
    parser.add_argument("--fps", type=float, default=None)
    parser.add_argument("--crf", type=positive_int, default=18)
    parser.add_argument("--preset", default="medium")
    parser.add_argument(
        "--tracker",
        choices=("detect", "flow", "reference"),
        default="flow",
        help=(
            "Corner trajectory source. reference locks all frames to the first "
            "screen plane using LK optical flow."
        ),
    )
    parser.add_argument(
        "--trajectory-window",
        type=odd_positive_int,
        default=31,
        help="Centered moving-average window for offline corner trajectory smoothing.",
    )
    parser.add_argument(
        "--median-window",
        type=odd_positive_int,
        default=5,
        help="Centered median window used before averaging to reject corner jumps.",
    )
    parser.add_argument(
        "--detect-correction",
        type=smoothing_weight,
        default=0.08,
        help="Blend weight for color-detected corners when optical-flow tracking is valid.",
    )
    parser.add_argument("--feature-refresh", type=positive_int, default=15)
    parser.add_argument(
        "--reference-min-inliers",
        type=positive_int,
        default=40,
        help="Minimum RANSAC inliers required before accepting a reference tracker update.",
    )
    parser.add_argument(
        "--reference-min-inlier-ratio",
        type=nonnegative_fraction,
        default=0.25,
        help="Minimum inlier ratio required before accepting a reference tracker update.",
    )
    parser.add_argument(
        "--reference-max-reprojection-error",
        type=nonnegative_fraction,
        default=2.5,
        help="Maximum median inlier reprojection error in pixels for reference tracking.",
    )
    parser.add_argument(
        "--reference-max-scale-step",
        type=nonnegative_fraction,
        default=0.035,
        help="Maximum accepted frame-to-frame side-length scale change; 0 disables.",
    )
    parser.add_argument(
        "--reference-max-area-step",
        type=nonnegative_fraction,
        default=0.08,
        help="Maximum accepted frame-to-frame screen-area change; 0 disables.",
    )
    parser.add_argument(
        "--reference-align",
        action="store_true",
        help="After perspective correction, align each frame back to the first corrected frame.",
    )
    parser.add_argument(
        "--reference-motion",
        choices=("affine", "homography"),
        default="affine",
        help="Residual motion model used by --reference-align.",
    )
    parser.add_argument("--crop-left", type=crop_fraction, default=0.0)
    parser.add_argument("--crop-top", type=crop_fraction, default=0.0)
    parser.add_argument("--crop-right", type=crop_fraction, default=0.0)
    parser.add_argument("--crop-bottom", type=crop_fraction, default=0.0)
    return parser.parse_args()


def require_ffmpeg() -> None:
    if shutil.which("ffmpeg") is None:
        raise SystemExit("ffmpeg is required but was not found on PATH")


def open_capture(path: Path) -> cv2.VideoCapture:
    capture = cv2.VideoCapture(str(path))
    if not capture.isOpened():
        raise SystemExit(f"could not open input video: {path}")
    return capture


def order_corners(points: np.ndarray) -> np.ndarray:
    points = np.asarray(points, dtype=np.float32).reshape(-1, 2)
    sums = points.sum(axis=1)
    diffs = np.diff(points, axis=1).reshape(-1)
    return np.array(
        [
            points[np.argmin(sums)],
            points[np.argmin(diffs)],
            points[np.argmax(sums)],
            points[np.argmax(diffs)],
        ],
        dtype=np.float32,
    )


def detected_corners_are_valid(corners: np.ndarray, frame_shape: tuple[int, ...]) -> bool:
    height, width = frame_shape[:2]
    area = abs(cv2.contourArea(corners))
    frame_area = float(width * height)
    if not frame_area * 0.20 <= area <= frame_area * 0.85:
        return False

    top = np.linalg.norm(corners[1] - corners[0])
    bottom = np.linalg.norm(corners[2] - corners[3])
    left = np.linalg.norm(corners[3] - corners[0])
    right = np.linalg.norm(corners[2] - corners[1])
    avg_width = (top + bottom) / 2.0
    avg_height = (left + right) / 2.0
    if avg_height <= 0:
        return False

    projected_aspect = avg_width / avg_height
    return 1.25 <= projected_aspect <= 2.35


def corner_edge_lengths(corners: np.ndarray) -> np.ndarray:
    return np.array(
        [
            np.linalg.norm(corners[1] - corners[0]),
            np.linalg.norm(corners[2] - corners[1]),
            np.linalg.norm(corners[2] - corners[3]),
            np.linalg.norm(corners[3] - corners[0]),
        ],
        dtype=np.float32,
    )


def ratio_is_within(value: float, previous: float, max_step: float) -> bool:
    if max_step <= 0:
        return True
    if previous <= 0:
        return False
    ratio = value / previous
    return (1.0 - max_step) <= ratio <= (1.0 + max_step)


def geometry_update_is_reasonable(
    corners: np.ndarray,
    previous_corners: np.ndarray,
    max_scale_step: float,
    max_area_step: float,
) -> bool:
    previous_edges = corner_edge_lengths(previous_corners)
    edges = corner_edge_lengths(corners)
    if np.any(previous_edges <= 0) or np.any(edges <= 0):
        return False
    for edge, previous_edge in zip(edges, previous_edges, strict=True):
        if not ratio_is_within(float(edge), float(previous_edge), max_scale_step):
            return False

    area = abs(cv2.contourArea(corners))
    previous_area = abs(cv2.contourArea(previous_corners))
    return ratio_is_within(float(area), float(previous_area), max_area_step)


def homography_median_reprojection_error(
    source_points: np.ndarray,
    target_points: np.ndarray,
    homography: np.ndarray,
    inlier_mask: np.ndarray,
) -> float:
    inliers = inlier_mask.reshape(-1).astype(bool)
    if not np.any(inliers):
        return float("inf")
    projected = cv2.perspectiveTransform(
        source_points[inliers].reshape(-1, 1, 2).astype(np.float32),
        homography,
    ).reshape(-1, 2)
    errors = np.linalg.norm(projected - target_points[inliers], axis=1)
    return float(np.median(errors))


def detect_screen_corners(frame: np.ndarray) -> np.ndarray | None:
    hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
    mask = cv2.inRange(hsv, (85, 20, 50), (130, 255, 255))
    mask = cv2.morphologyEx(
        mask,
        cv2.MORPH_CLOSE,
        cv2.getStructuringElement(cv2.MORPH_RECT, (25, 25)),
        iterations=2,
    )
    mask = cv2.morphologyEx(
        mask,
        cv2.MORPH_OPEN,
        cv2.getStructuringElement(cv2.MORPH_RECT, (5, 5)),
        iterations=1,
    )

    contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    if not contours:
        return None

    contour = max(contours, key=cv2.contourArea)
    frame_area = frame.shape[0] * frame.shape[1]
    if cv2.contourArea(contour) < frame_area * 0.20:
        return None

    perimeter = cv2.arcLength(contour, True)
    for epsilon_fraction in (0.010, 0.012, 0.015, 0.018, 0.020, 0.025, 0.030, 0.040):
        approximate = cv2.approxPolyDP(contour, epsilon_fraction * perimeter, True)
        if len(approximate) != 4:
            continue

        corners = order_corners(approximate.reshape(-1, 2))
        if detected_corners_are_valid(corners, frame.shape):
            return corners

    return None


def corner_mask(shape: tuple[int, ...], corners: np.ndarray, inset_pixels: int = 12) -> np.ndarray:
    mask = np.zeros(shape[:2], dtype=np.uint8)
    cv2.fillConvexPoly(mask, corners.astype(np.int32), 255)
    if inset_pixels > 0:
        kernel = cv2.getStructuringElement(
            cv2.MORPH_ELLIPSE,
            (inset_pixels * 2 + 1, inset_pixels * 2 + 1),
        )
        mask = cv2.erode(mask, kernel, iterations=1)
    return mask


def select_tracking_points(gray: np.ndarray, corners: np.ndarray) -> np.ndarray | None:
    points = cv2.goodFeaturesToTrack(
        gray,
        maxCorners=900,
        qualityLevel=0.005,
        minDistance=8,
        mask=corner_mask(gray.shape, corners),
        blockSize=7,
    )
    if points is None or len(points) < 12:
        return None
    return points.astype(np.float32)


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
) -> tuple[np.ndarray, np.ndarray]:
    new_points = select_tracking_points(gray, current_corners)
    if new_points is None:
        return reference_points, current_points

    existing = current_points.reshape(-1, 2)
    fresh = []
    for point in new_points.reshape(-1, 2):
        if len(existing) and np.min(np.linalg.norm(existing - point, axis=1)) < 8:
            continue
        fresh.append(point)
        if len(fresh) >= 250:
            break

    if not fresh:
        return reference_points, current_points

    fresh_current = np.asarray(fresh, dtype=np.float32).reshape(-1, 1, 2)
    fresh_reference = cv2.perspectiveTransform(fresh_current, current_to_reference)
    reference_points = np.concatenate([reference_points, fresh_reference.astype(np.float32)])
    current_points = np.concatenate([current_points, fresh_current.astype(np.float32)])
    return reference_points, current_points


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

    trajectory = [reference_corners]
    previous_corners = reference_corners
    frame_index = 1
    rejected_updates = 0

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
        reference_good = reference_points.reshape(-1, 2)[valid]
        current_good = next_points.reshape(-1, 2)[valid]

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
        else:
            inlier_count = 0
            inlier_ratio = 0.0
            reprojection_error = float("inf")

        if (
            current_to_reference is not None
            and inlier_mask is not None
            and inlier_count >= reference_min_inliers
            and inlier_ratio >= reference_min_inlier_ratio
            and reprojection_error <= reference_max_reprojection_error
        ):
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
        elif current_to_reference is not None:
            rejected_updates += 1
        trajectory.append(previous_corners)

        keep = valid
        if accepted_transform is not None and inlier_mask is not None and len(reference_good) == int(valid.sum()):
            valid_indices = np.flatnonzero(valid)
            keep = np.zeros_like(valid)
            keep[valid_indices[inlier_mask.reshape(-1).astype(bool)]] = True

        reference_points = reference_points[keep]
        current_points = next_points[keep].astype(np.float32)
        if (
            len(current_points) < 140
            or frame_index % feature_refresh == 0
        ) and accepted_transform is not None:
            reference_points, current_points = append_reference_points(
                gray,
                previous_corners,
                accepted_transform,
                reference_points,
                current_points,
            )

        previous_gray = gray
        frame_index += 1
        if frame_count and (frame_index % 60 == 0 or frame_index == frame_count):
            print(
                f"reference-tracked corners {frame_index}/{frame_count} frames "
                f"with {len(current_points)} points, rejected {rejected_updates} updates",
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
        detected_corners = detect_screen_corners(frame) if auto_detect else fallback_corners
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


def centered_window_filter(trajectory: np.ndarray, window: int, reducer: str) -> np.ndarray:
    if window <= 1 or len(trajectory) < 3:
        return trajectory

    radius = window // 2
    padded = np.pad(trajectory, ((radius, radius), (0, 0), (0, 0)), mode="edge")
    filtered = np.empty_like(trajectory)
    for index in range(len(trajectory)):
        chunk = padded[index : index + window]
        if reducer == "median":
            filtered[index] = np.median(chunk, axis=0)
        elif reducer == "mean":
            filtered[index] = np.mean(chunk, axis=0)
        else:
            raise ValueError(f"unknown reducer: {reducer}")
    return filtered


def smooth_corner_trajectory(
    trajectory: list[np.ndarray],
    median_window: int,
    average_window: int,
) -> list[np.ndarray]:
    points = np.asarray(trajectory, dtype=np.float32)
    if len(points) == 0:
        return []
    points = centered_window_filter(points, median_window, "median")
    points = centered_window_filter(points, average_window, "mean")
    return [order_corners(corners).astype(np.float32) for corners in points]


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


def estimate_reference_alignment(
    reference_gray: np.ndarray,
    gray: np.ndarray,
    reference_points: np.ndarray | None,
    motion: str,
) -> np.ndarray | None:
    if reference_points is None or len(reference_points) < 20:
        return None

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
        return None

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
        return None

    forward_ok = status.reshape(-1).astype(bool)
    backward_ok = back_status.reshape(-1).astype(bool)
    round_trip_error = np.linalg.norm(
        reference_points.reshape(-1, 2) - reference_back.reshape(-1, 2),
        axis=1,
    )
    valid = forward_ok & backward_ok & (round_trip_error < 1.5)
    reference_good = reference_points.reshape(-1, 2)[valid]
    current_good = current_points.reshape(-1, 2)[valid]
    if len(reference_good) < 20:
        return None

    if motion == "homography":
        transform, inlier_mask = cv2.findHomography(current_good, reference_good, cv2.RANSAC, 2.0)
        if transform is None or inlier_mask is None or int(inlier_mask.sum()) < 20:
            return None
        return transform.astype(np.float32)

    affine, inlier_mask = cv2.estimateAffinePartial2D(
        current_good,
        reference_good,
        method=cv2.RANSAC,
        ransacReprojThreshold=2.0,
        maxIters=3000,
        confidence=0.995,
    )
    if affine is None or inlier_mask is None or int(inlier_mask.sum()) < 20:
        return None
    transform = np.eye(3, dtype=np.float32)
    transform[:2] = affine.astype(np.float32)
    return transform


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
    auto_detect: bool,
    crop_left: float,
    crop_top: float,
    crop_right: float,
    crop_bottom: float,
    reference_align: bool,
    reference_motion: str,
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
            if corner_trajectory is not None:
                source_corners = corner_trajectory[min(processed, len(corner_trajectory) - 1)]
                transform = cv2.getPerspectiveTransform(source_corners, destination_corners)
            elif auto_detect:
                detected_corners = detect_screen_corners(frame)
                if detected_corners is None:
                    source_corners = last_corners if last_corners is not None else fallback_corners
                elif last_corners is None:
                    source_corners = detected_corners
                else:
                    source_corners = (last_corners * smooth) + (detected_corners * (1.0 - smooth))
                last_corners = source_corners
                transform = cv2.getPerspectiveTransform(source_corners, destination_corners)
            else:
                transform = fallback_transform

            warped = cv2.warpPerspective(
                frame,
                transform,
                (width, height),
                flags=cv2.INTER_CUBIC,
                borderMode=cv2.BORDER_REPLICATE,
            )
            if crop_left or crop_top or crop_right or crop_bottom:
                x1 = int(round(width * crop_left))
                y1 = int(round(height * crop_top))
                x2 = int(round(width * (1.0 - crop_right)))
                y2 = int(round(height * (1.0 - crop_bottom)))
                if x1 >= x2 or y1 >= y2:
                    raise SystemExit("crop values leave no output area")
                warped = cv2.resize(
                    warped[y1:y2, x1:x2],
                    (width, height),
                    interpolation=cv2.INTER_CUBIC,
                )

            if reference_align:
                gray = cv2.cvtColor(warped, cv2.COLOR_BGR2GRAY)
                if reference_gray is None:
                    reference_gray = gray
                    reference_points = select_reference_points(reference_gray)
                else:
                    residual_transform = estimate_reference_alignment(
                        reference_gray,
                        gray,
                        reference_points,
                        reference_motion,
                    )
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


def main() -> None:
    args = parse_args()
    require_ffmpeg()

    source = args.input.resolve()
    output = args.output.resolve()
    if source == output:
        raise SystemExit("input and output must be different files")
    output.parent.mkdir(parents=True, exist_ok=True)

    capture = open_capture(source)
    fps = args.fps or float(capture.get(cv2.CAP_PROP_FPS) or 60.0)
    if fps <= 0:
        fps = 60.0

    fallback_corners = args.corners
    auto_detect = fallback_corners is None
    if fallback_corners is None:
        fallback_corners = parse_corners(DEFAULT_FALLBACK_CORNERS)

    with tempfile.TemporaryDirectory() as tmp:
        corner_trajectory = None
        if auto_detect:
            corner_trajectory = estimate_corner_trajectory(
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
            )
            capture.release()
            if args.tracker != "reference":
                corner_trajectory = smooth_corner_trajectory(
                    corner_trajectory,
                    median_window=args.median_window,
                    average_window=args.trajectory_window,
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
            auto_detect=auto_detect,
            crop_left=args.crop_left,
            crop_top=args.crop_top,
            crop_right=args.crop_right,
            crop_bottom=args.crop_bottom,
            reference_align=args.reference_align,
            reference_motion=args.reference_motion,
        )
        mux_audio(silent_video, source, output)

    print(f"wrote {output} from {processed} frames")


if __name__ == "__main__":
    main()
