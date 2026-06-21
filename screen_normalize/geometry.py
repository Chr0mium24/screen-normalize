from __future__ import annotations

import cv2
import numpy as np


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


def homography_inlier_screen_coverage(
    reference_points: np.ndarray,
    inlier_mask: np.ndarray,
    reference_corners: np.ndarray,
) -> tuple[float, float]:
    inliers = inlier_mask.reshape(-1).astype(bool)
    if int(inliers.sum()) < 2:
        return 0.0, 0.0

    unit_corners = np.array(
        [[0.0, 0.0], [1.0, 0.0], [1.0, 1.0], [0.0, 1.0]],
        dtype=np.float32,
    )
    reference_to_unit = cv2.getPerspectiveTransform(
        reference_corners.astype(np.float32),
        unit_corners,
    )
    unit_points = cv2.perspectiveTransform(
        reference_points.reshape(-1, 1, 2).astype(np.float32),
        reference_to_unit,
    ).reshape(-1, 2)[inliers]
    lower = np.percentile(unit_points, 5, axis=0)
    upper = np.percentile(unit_points, 95, axis=0)
    coverage = np.maximum(upper - lower, 0.0)
    return float(coverage[0]), float(coverage[1])
