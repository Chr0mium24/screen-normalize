from __future__ import annotations

import cv2
import numpy as np

from screen_normalize.algorithms.boundary import corners_from_lines, observe_quad_edges


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
