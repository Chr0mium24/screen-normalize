from __future__ import annotations

import cv2
import numpy as np

from screen_normalize.algorithms.boundary import (
    corners_from_lines,
    estimate_boundary_corner_trajectory,
    observe_quad_edges,
    observe_quad_edges_by_line_detector,
)


def test_dense_edge_observation_recovers_synthetic_quad() -> None:
    image = np.zeros((480, 640), dtype=np.uint8)
    expected = np.asarray([[95, 72], [548, 91], [520, 405], [76, 388]], dtype=np.float32)
    cv2.fillConvexPoly(image, expected.astype(np.int32), 230)
    predicted = expected + np.asarray([[3, -2], [-4, 2], [2, 3], [-3, -2]], dtype=np.float32)
    observations, _ = observe_quad_edges(image, predicted, sample_count=60, radius=20)
    recovered = corners_from_lines([item.line for item in observations])
    assert recovered is not None
    assert float(np.mean(np.linalg.norm(recovered - expected, axis=1))) < 2.5
    assert min(item.confidence for item in observations) >= 0.7


def test_parallel_lines_do_not_produce_quad() -> None:
    horizontal = np.asarray([0.0, 1.0, -20.0])
    assert corners_from_lines([horizontal, horizontal, horizontal, horizontal]) is None


def test_hough_and_lsd_observations_recover_synthetic_quad() -> None:
    image = np.zeros((480, 640), dtype=np.uint8)
    expected = np.asarray([[95, 72], [548, 91], [520, 405], [76, 388]], dtype=np.float32)
    cv2.fillConvexPoly(image, expected.astype(np.int32), 230)
    predicted = expected + np.asarray([[3, -2], [-4, 2], [2, 3], [-3, -2]], dtype=np.float32)

    for detector in ("hough", "lsd"):
        observations, _ = observe_quad_edges_by_line_detector(
            image,
            predicted,
            radius=24,
            detector=detector,
        )
        recovered = corners_from_lines([item.line for item in observations])
        assert recovered is not None, detector
        error = float(np.mean(np.linalg.norm(recovered - expected, axis=1)))
        assert error < 3.5, detector


def test_boundary_trajectory_tracks_translating_quad(tmp_path) -> None:
    path = tmp_path / "translation.avi"
    writer = cv2.VideoWriter(str(path), cv2.VideoWriter_fourcc(*"MJPG"), 10.0, (640, 480))
    initial = np.asarray([[100, 80], [540, 80], [540, 400], [100, 400]], dtype=np.float32)
    for offset in range(5):
        frame = np.zeros((480, 640, 3), dtype=np.uint8)
        moved = initial + np.asarray([offset * 2, offset], dtype=np.float32)
        cv2.fillConvexPoly(frame, moved.astype(np.int32), (230, 230, 230))
        writer.write(frame)
    writer.release()
    capture = cv2.VideoCapture(str(path))
    rows = []
    trajectory = estimate_boundary_corner_trajectory(capture, initial, rows)
    capture.release()
    assert len(trajectory) == 5
    expected = initial + np.asarray([8, 4], dtype=np.float32)
    assert float(np.mean(np.linalg.norm(trajectory[-1] - expected, axis=1))) < 3.0
    assert all(row["accepted"] for row in rows)
