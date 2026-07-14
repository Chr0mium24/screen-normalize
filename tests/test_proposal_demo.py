from __future__ import annotations

import cv2
import numpy as np

from screen_normalize.algorithms.proposal_demo import (
    ProposalDemoConfig,
    estimate_proposal_border_trajectory,
)


def test_proposal_demo_tracks_border_with_moving_content(tmp_path) -> None:
    path = tmp_path / "proposal_demo.avi"
    writer = cv2.VideoWriter(str(path), cv2.VideoWriter_fourcc(*"MJPG"), 10.0, (640, 480))
    initial = np.asarray([[110, 80], [520, 82], [535, 390], [95, 388]], dtype=np.float32)
    expected = []
    for frame_index in range(7):
        offset = np.asarray([frame_index * 3.0, frame_index * 1.5], dtype=np.float32)
        corners = initial + offset
        expected.append(corners)
        frame = np.zeros((480, 640, 3), dtype=np.uint8)
        cv2.fillConvexPoly(frame, np.round(corners).astype(np.int32), (230, 230, 230))

        # Moving interior bars emulate scrolling content that should not define the screen plane.
        x_base = int(140 + frame_index * 18)
        for index in range(5):
            x = x_base + index * 42
            cv2.line(frame, (x, 120), (x + 20, 355), (40, 40, 40), 5)
        writer.write(frame)
    writer.release()

    capture = cv2.VideoCapture(str(path))
    rows: list[dict[str, object]] = []
    trajectory = estimate_proposal_border_trajectory(
        capture,
        initial_corners=initial,
        config=ProposalDemoConfig(max_frames=7, min_edge_confidence=0.25),
        debug_rows=rows,
    )
    capture.release()

    assert len(trajectory) == 7
    assert len(rows) == 7
    assert any(row["reason"].startswith("edge_accept") for row in rows[1:])
    mean_error = float(np.mean(np.linalg.norm(trajectory[-1] - expected[-1], axis=1)))
    assert mean_error < 4.0
