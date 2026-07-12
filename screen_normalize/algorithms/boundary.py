from __future__ import annotations

from dataclasses import dataclass

import cv2
import numpy as np

from .geometry import order_corners


@dataclass(frozen=True)
class EdgeObservation:
    points: np.ndarray
    strengths: np.ndarray
    line: np.ndarray | None
    inliers: np.ndarray
    confidence: float


def sample_quad_edge(corners: np.ndarray, edge: int, count: int) -> tuple[np.ndarray, np.ndarray]:
    start = np.asarray(corners[edge], dtype=np.float32)
    end = np.asarray(corners[(edge + 1) % 4], dtype=np.float32)
    tangent = end - start
    length = float(np.linalg.norm(tangent))
    if length < 1.0:
        return np.empty((0, 2), np.float32), np.zeros(2, np.float32)
    tangent /= length
    normal = np.array([-tangent[1], tangent[0]], dtype=np.float32)
    center = np.asarray(corners, dtype=np.float32).mean(axis=0)
    midpoint = (start + end) * 0.5
    if float(np.dot(center - midpoint, normal)) < 0:
        normal *= -1.0
    positions = np.linspace(0.04, 0.96, count, dtype=np.float32)
    samples = start[None, :] + positions[:, None] * (end - start)[None, :]
    return samples, normal


def normal_gradient_candidates(
    gray: np.ndarray,
    samples: np.ndarray,
    inward_normal: np.ndarray,
    radius: int,
    expected_polarity: float = 0.0,
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    if len(samples) == 0:
        return np.empty((0, 2), np.float32), np.empty(0, np.float32), np.empty(0, np.float32)
    offsets = np.arange(-radius, radius + 1, dtype=np.float32)
    coordinates = samples[:, None, :] + offsets[None, :, None] * inward_normal[None, None, :]
    map_x = coordinates[:, :, 0].astype(np.float32)
    map_y = coordinates[:, :, 1].astype(np.float32)
    profiles = cv2.remap(gray, map_x, map_y, cv2.INTER_LINEAR, borderMode=cv2.BORDER_REPLICATE)
    profiles = cv2.GaussianBlur(profiles, (1, 5), 0)
    gradients = np.gradient(profiles.astype(np.float32), axis=1)
    scores = np.abs(gradients)
    if expected_polarity:
        scores = np.where(gradients * expected_polarity > 0, scores, 0.0)
    proximity = np.exp(-0.5 * (offsets / max(4.0, radius * 0.55)) ** 2)
    scores *= proximity[None, :]
    indices = np.argmax(scores, axis=1)
    row = np.arange(len(samples))
    chosen_offsets = offsets[indices]
    points = samples + chosen_offsets[:, None] * inward_normal[None, :]
    strengths = np.abs(gradients[row, indices])
    polarities = np.sign(gradients[row, indices])
    return points.astype(np.float32), strengths.astype(np.float32), polarities.astype(np.float32)


def robust_fit_line(points: np.ndarray, strengths: np.ndarray, threshold: float = 3.0) -> tuple[np.ndarray | None, np.ndarray]:
    points = np.asarray(points, dtype=np.float32).reshape(-1, 2)
    strengths = np.asarray(strengths, dtype=np.float32).reshape(-1)
    inliers = np.isfinite(points).all(axis=1) & np.isfinite(strengths)
    if int(inliers.sum()) < 8:
        return None, inliers
    minimum_strength = max(3.0, float(np.percentile(strengths[inliers], 30)))
    inliers &= strengths >= minimum_strength
    for _ in range(4):
        if int(inliers.sum()) < 8:
            return None, inliers
        vx, vy, x0, y0 = cv2.fitLine(points[inliers], cv2.DIST_HUBER, 0, 0.01, 0.01).reshape(-1)
        line = np.array([vy, -vx, -(vy * x0 - vx * y0)], dtype=np.float64)
        line /= max(np.linalg.norm(line[:2]), 1e-12)
        distances = np.abs(points @ line[:2] + line[2])
        median = float(np.median(distances[inliers]))
        mad = float(np.median(np.abs(distances[inliers] - median)))
        limit = max(threshold, median + 3.0 * 1.4826 * mad)
        updated = (distances <= limit) & (strengths >= minimum_strength)
        if np.array_equal(updated, inliers):
            break
        inliers = updated
    if int(inliers.sum()) < 8:
        return None, inliers
    vx, vy, x0, y0 = cv2.fitLine(points[inliers], cv2.DIST_HUBER, 0, 0.01, 0.01).reshape(-1)
    line = np.array([vy, -vx, -(vy * x0 - vx * y0)], dtype=np.float64)
    line /= max(np.linalg.norm(line[:2]), 1e-12)
    return line, inliers


def intersect_lines(first: np.ndarray, second: np.ndarray) -> np.ndarray | None:
    matrix = np.asarray([first[:2], second[:2]], dtype=np.float64)
    determinant = float(np.linalg.det(matrix))
    if abs(determinant) < 1e-5:
        return None
    return np.linalg.solve(matrix, -np.asarray([first[2], second[2]], dtype=np.float64)).astype(np.float32)


def corners_from_lines(lines: list[np.ndarray | None]) -> np.ndarray | None:
    if len(lines) != 4 or any(line is None for line in lines):
        return None
    top, right, bottom, left = lines
    intersections = [
        intersect_lines(top, left),
        intersect_lines(top, right),
        intersect_lines(bottom, right),
        intersect_lines(bottom, left),
    ]
    if any(point is None for point in intersections):
        return None
    corners = order_corners(np.asarray(intersections, dtype=np.float32))
    if not np.isfinite(corners).all() or not cv2.isContourConvex(corners.reshape(-1, 1, 2)):
        return None
    return corners


def observe_quad_edges(
    gray: np.ndarray,
    predicted_corners: np.ndarray,
    sample_count: int,
    radius: int,
    polarities: np.ndarray | None = None,
) -> tuple[list[EdgeObservation], np.ndarray]:
    observations: list[EdgeObservation] = []
    measured_polarities = np.zeros(4, dtype=np.float32)
    for edge in range(4):
        samples, normal = sample_quad_edge(predicted_corners, edge, sample_count)
        expected = float(polarities[edge]) if polarities is not None else 0.0
        points, strengths, signs = normal_gradient_candidates(gray, samples, normal, radius, expected)
        line, inliers = robust_fit_line(points, strengths)
        confidence = float(inliers.sum() / max(1, len(points)))
        if np.any(inliers):
            measured_polarities[edge] = float(np.sign(np.median(signs[inliers])))
        observations.append(EdgeObservation(points, strengths, line, inliers, confidence))
    return observations, measured_polarities
