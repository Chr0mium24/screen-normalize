from __future__ import annotations

from pathlib import Path
from typing import Any

import cv2

from ..annotations import load_annotations
from ..evaluation import evaluate_geometry_accuracy, read_corner_csv, read_frames, video_metadata
from .common import run_guarded


def evaluate_geometry(
    original_video: Path,
    annotation_csv: Path | None,
    estimated_csv: Path,
    output_dir: Path,
) -> dict[str, Any]:
    def calculate():
        if annotation_csv is None or not annotation_csv.exists():
            return [], {"status": "skipped", "reason": "corner annotation CSV is missing"}
        metadata = video_metadata(original_video)
        annotations = load_annotations(annotation_csv, metadata.width, metadata.height)
        estimates = read_corner_csv(estimated_csv)
        payload = evaluate_geometry_accuracy(annotations, estimates, metadata.width, metadata.height)
        matched = sorted(set(annotations) & set(estimates))
        if matched:
            frame = read_frames(original_video, [matched[0]]).get(matched[0])
            if frame is not None:
                cv2.polylines(frame, [annotations[matched[0]].round().astype("int32")], True, (0, 220, 0), 3)
                cv2.polylines(frame, [estimates[matched[0]].round().astype("int32")], True, (0, 0, 255), 3)
                cv2.imwrite(str(output_dir / "geometry_overlay.jpg"), frame)
        return payload

    return run_guarded(output_dir, "geometry", calculate)
