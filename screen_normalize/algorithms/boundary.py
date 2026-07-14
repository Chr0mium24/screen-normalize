from __future__ import annotations

from dataclasses import dataclass

import cv2
import numpy as np

from .geometry import detected_corners_are_valid, geometry_update_is_reasonable, order_corners


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


def line_from_points(start: np.ndarray, end: np.ndarray) -> np.ndarray | None:
    start = np.asarray(start, dtype=np.float32)
    end = np.asarray(end, dtype=np.float32)
    direction = end - start
    length = float(np.linalg.norm(direction))
    if length < 1.0:
        return None
    vx, vy = direction / length
    line = np.array([vy, -vx, -(vy * start[0] - vx * start[1])], dtype=np.float64)
    line /= max(np.linalg.norm(line[:2]), 1e-12)
    return line


def detect_hough_segments(gray: np.ndarray) -> np.ndarray:
    blurred = cv2.GaussianBlur(gray, (3, 3), 0)
    edges = cv2.Canny(blurred, 60, 160)
    min_length = max(50, min(gray.shape[:2]) // 28)
    lines = cv2.HoughLinesP(
        edges,
        1,
        np.pi / 180.0,
        threshold=80,
        minLineLength=min_length,
        maxLineGap=28,
    )
    if lines is None:
        return np.empty((0, 4), dtype=np.float32)
    return lines.reshape(-1, 4).astype(np.float32)


def detect_lsd_segments(gray: np.ndarray) -> np.ndarray:
    detector = cv2.createLineSegmentDetector()
    lines = detector.detect(gray)[0]
    if lines is None:
        return np.empty((0, 4), dtype=np.float32)
    return lines.reshape(-1, 4).astype(np.float32)


def detect_line_segments(gray: np.ndarray, detector: str) -> np.ndarray:
    if detector == "hough":
        return detect_hough_segments(gray)
    if detector == "lsd":
        return detect_lsd_segments(gray)
    raise ValueError(f"unsupported line detector: {detector}")


def angle_delta_degrees(first: np.ndarray, second: np.ndarray) -> float:
    first = np.asarray(first, dtype=np.float32)
    second = np.asarray(second, dtype=np.float32)
    first_norm = float(np.linalg.norm(first))
    second_norm = float(np.linalg.norm(second))
    if first_norm < 1e-6 or second_norm < 1e-6:
        return 180.0
    cosine = abs(float(np.dot(first / first_norm, second / second_norm)))
    return float(np.degrees(np.arccos(np.clip(cosine, -1.0, 1.0))))


def sample_segment_points(segment: np.ndarray, step: float = 12.0) -> np.ndarray:
    start = segment[:2]
    end = segment[2:]
    length = float(np.linalg.norm(end - start))
    count = max(2, min(80, int(length / step) + 1))
    positions = np.linspace(0.0, 1.0, count, dtype=np.float32)
    return start[None, :] + positions[:, None] * (end - start)[None, :]


def line_segment_edge_observation(
    segments: np.ndarray,
    predicted_corners: np.ndarray,
    edge: int,
    radius: int,
    angle_tolerance_deg: float = 12.0,
) -> EdgeObservation:
    start = np.asarray(predicted_corners[edge], dtype=np.float32)
    end = np.asarray(predicted_corners[(edge + 1) % 4], dtype=np.float32)
    edge_vector = end - start
    edge_length = float(np.linalg.norm(edge_vector))
    if edge_length < 1.0:
        return EdgeObservation(
            np.empty((0, 2), np.float32),
            np.empty(0, np.float32),
            None,
            np.zeros(0, dtype=bool),
            0.0,
        )
    tangent = edge_vector / edge_length
    predicted_line = line_from_points(start, end)
    if predicted_line is None:
        return EdgeObservation(
            np.empty((0, 2), np.float32),
            np.empty(0, np.float32),
            None,
            np.zeros(0, dtype=bool),
            0.0,
        )

    selected_points: list[np.ndarray] = []
    selected_strengths: list[np.ndarray] = []
    covered_length = 0.0
    min_segment_length = max(30.0, edge_length * 0.015)
    for segment in segments:
        first = segment[:2]
        second = segment[2:]
        segment_vector = second - first
        segment_length = float(np.linalg.norm(segment_vector))
        if segment_length < min_segment_length:
            continue
        if angle_delta_degrees(segment_vector, tangent) > angle_tolerance_deg:
            continue
        midpoint = (first + second) * 0.5
        distance = abs(float(midpoint @ predicted_line[:2] + predicted_line[2]))
        if distance > radius:
            continue
        projections = np.array(
            [float((first - start) @ tangent), float((second - start) @ tangent)]
        )
        overlap = max(0.0, min(float(projections.max()), edge_length) - max(float(projections.min()), 0.0))
        if overlap < max(10.0, segment_length * 0.15):
            continue
        points = sample_segment_points(segment)
        selected_points.append(points)
        selected_strengths.append(np.full((len(points),), segment_length, dtype=np.float32))
        covered_length += min(overlap, segment_length)

    if not selected_points:
        return EdgeObservation(
            np.empty((0, 2), np.float32),
            np.empty(0, np.float32),
            None,
            np.zeros(0, dtype=bool),
            0.0,
        )

    points = np.concatenate(selected_points).astype(np.float32)
    strengths = np.concatenate(selected_strengths).astype(np.float32)
    line, inliers = robust_fit_line(points, strengths, threshold=max(3.0, radius * 0.08))
    confidence = min(1.0, covered_length / max(1.0, edge_length)) if line is not None else 0.0
    return EdgeObservation(points, strengths, line, inliers, confidence)


def observe_quad_edges_by_line_detector(
    gray: np.ndarray,
    predicted_corners: np.ndarray,
    radius: int,
    detector: str,
) -> tuple[list[EdgeObservation], np.ndarray]:
    segments = detect_line_segments(gray, detector)
    observations = [
        line_segment_edge_observation(segments, predicted_corners, edge, radius)
        for edge in range(4)
    ]
    return observations, np.zeros(4, dtype=np.float32)


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


def estimate_boundary_corner_trajectory(
    capture: cv2.VideoCapture,
    initial_corners: np.ndarray,
    debug_rows: list[dict[str, object]] | None = None,
    sample_count: int = 50,
    search_radii: tuple[int, ...] = (20, 60, 120),
) -> list[np.ndarray]:
    """Track a full quadrilateral from dense observations along its four edges."""
    trajectory: list[np.ndarray] = []
    predicted = order_corners(initial_corners).astype(np.float32)
    polarities: np.ndarray | None = None
    frame_index = 0
    while True:
        ok, frame = capture.read()
        if not ok:
            break
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        accepted = frame_index == 0
        chosen: list[EdgeObservation] = []
        measured = np.zeros(4, dtype=np.float32)
        used_radius = 0
        candidate = predicted.copy() if accepted else None
        for radius in search_radii:
            observations, current_polarities = observe_quad_edges(
                gray, predicted, sample_count, radius, polarities
            )
            proposed = corners_from_lines([item.line for item in observations])
            confidences = np.asarray([item.confidence for item in observations])
            chosen, measured, used_radius = observations, current_polarities, radius
            if (
                proposed is not None
                and float(confidences.min()) >= 0.35
                and detected_corners_are_valid(proposed, frame.shape)
                and geometry_update_is_reasonable(proposed, predicted, 0.08, 0.15)
            ):
                candidate = proposed
                accepted = True
                break
        if accepted and candidate is not None:
            predicted = candidate.astype(np.float32)
            nonzero = measured != 0
            if polarities is None:
                polarities = measured.copy()
            else:
                polarities[nonzero] = measured[nonzero]
        trajectory.append(predicted.copy())
        if debug_rows is not None:
            row: dict[str, object] = {
                "frame": frame_index,
                "accepted": accepted,
                "reason": "edge_accepted" if accepted else "edge_held",
                "search_radius": used_radius,
            }
            for edge, observation in enumerate(chosen):
                row[f"edge_{edge}_confidence"] = observation.confidence
                row[f"edge_{edge}_inliers"] = int(observation.inliers.sum())
            debug_rows.append(row)
        frame_index += 1
    return trajectory
