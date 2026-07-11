from __future__ import annotations

from pathlib import Path
from typing import Any

import cv2
import numpy as np

from ..evaluation import read_corner_csv, summarize_numeric
from .common import run_guarded


def _trajectory_motion(estimates: dict[int, np.ndarray]):
    rows: list[dict[str, Any]] = []
    frames = sorted(estimates)
    for previous_index, current_index in zip(frames, frames[1:]):
        previous = estimates[previous_index].astype(np.float32)
        current = estimates[current_index].astype(np.float32)
        transform = cv2.getPerspectiveTransform(previous, current)
        affine = transform[:2, :2]
        rotation = float(np.degrees(np.arctan2(affine[1, 0], affine[0, 0])))
        scale = float(np.sqrt(abs(np.linalg.det(affine))))
        dx, dy = float(transform[0, 2]), float(transform[1, 2])
        rows.append(
            {
                "frame": current_index,
                "previous_frame": previous_index,
                "ok": True,
                "translation_x_px": dx,
                "translation_y_px": dy,
                "translation_px": float(np.hypot(dx, dy)),
                "rotation_deg": rotation,
                "scale": scale,
                "scale_delta": scale - 1.0,
            }
        )
    metrics = {
        "translation_px": ("translation_px", False),
        "rotation_deg": ("rotation_abs_deg", True),
        "scale_delta": ("scale_abs_delta", True),
    }
    summary = {
        "status": "ok" if rows else "skipped",
        "reason": None if rows else "fewer than two estimated corner frames",
        "definition": "frame-to-frame projective motion of the estimated screen quadrilateral",
        **summarize_numeric(rows, metrics),
    }
    return rows, summary


def evaluate_temporal(estimated_csv: Path, output_dir: Path) -> dict[str, Any]:
    return run_guarded(output_dir, "temporal", lambda: _trajectory_motion(read_corner_csv(estimated_csv)))

