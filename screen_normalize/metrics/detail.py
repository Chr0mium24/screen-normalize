from __future__ import annotations

from pathlib import Path
from typing import Any

from ..annotations import load_annotations
from ..evaluation import SignalConfig, evaluate_signal_preservation, video_metadata
from .common import run_guarded


def evaluate_detail(
    normalized_video: Path,
    original_video: Path,
    annotation_csv: Path | None,
    output_dir: Path,
    sample_stride: int = 30,
    max_frames: int = 120,
) -> dict[str, Any]:
    def calculate():
        if annotation_csv is None or not annotation_csv.exists():
            return [], {"status": "skipped", "reason": "aligned detail comparison requires corner annotations"}
        metadata = video_metadata(original_video)
        annotations = load_annotations(annotation_csv, metadata.width, metadata.height)
        return evaluate_signal_preservation(
            normalized_video,
            original_video,
            annotations,
            SignalConfig(sample_stride=sample_stride, max_frames=max_frames),
        )

    return run_guarded(output_dir, "detail", calculate)

