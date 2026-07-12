from __future__ import annotations

from pathlib import Path
from typing import Any

import cv2

from ..experiments.annotations import load_annotations
from ..experiments.evaluation import SignalConfig, evaluate_signal_preservation, read_frames, video_metadata, warp_to_screen
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
        payload = evaluate_signal_preservation(
            normalized_video,
            original_video,
            annotations,
            SignalConfig(sample_stride=sample_stride, max_frames=max_frames),
        )
        if annotations:
            frame_index = sorted(annotations)[0]
            original = read_frames(original_video, [frame_index]).get(frame_index)
            normalized = read_frames(normalized_video, [frame_index]).get(frame_index)
            if original is not None and normalized is not None:
                reference = warp_to_screen(original, annotations[frame_index], normalized.shape[1], normalized.shape[0])
                comparison = cv2.hconcat([reference, normalized])
                cv2.imwrite(str(output_dir / "detail_comparison.jpg"), comparison)
        return payload

    return run_guarded(output_dir, "detail", calculate)
