from __future__ import annotations

from pathlib import Path
from typing import Any

from ..annotations import load_annotations
from ..evaluation import evaluate_geometry_accuracy, read_corner_csv, video_metadata
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
        return evaluate_geometry_accuracy(annotations, estimates, metadata.width, metadata.height)

    return run_guarded(output_dir, "geometry", calculate)

