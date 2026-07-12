from __future__ import annotations

from pathlib import Path
from typing import Any

import cv2
import numpy as np

from ..experiments.evaluation import FrequencyConfig, evaluate_spectral_regularity, read_frames, video_metadata
from .common import run_guarded


def evaluate_frequency(
    normalized_video: Path,
    output_dir: Path,
    sample_stride: int = 30,
    max_frames: int = 120,
) -> dict[str, Any]:
    def calculate():
        rows, summary = evaluate_spectral_regularity(
            normalized_video,
            FrequencyConfig(sample_stride=sample_stride, max_frames=max_frames),
        )
        summary["interpretation"] = (
            "frequency direction and axis regularity after geometric resampling; "
            "this is not a moire-suppression measurement"
        )
        metadata = video_metadata(normalized_video)
        first = read_frames(normalized_video, [0]).get(0)
        if first is not None:
            gray = cv2.cvtColor(first, cv2.COLOR_BGR2GRAY).astype(np.float32)
            spectrum = np.log1p(np.abs(np.fft.fftshift(np.fft.fft2(gray - gray.mean()))))
            image = cv2.normalize(spectrum, None, 0, 255, cv2.NORM_MINMAX).astype(np.uint8)
            cv2.imwrite(str(output_dir / "frequency_spectrum.png"), image)
        summary["video_frame_count"] = metadata.frame_count
        return rows, summary

    return run_guarded(output_dir, "frequency", calculate)
