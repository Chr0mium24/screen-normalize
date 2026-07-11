from __future__ import annotations

from pathlib import Path
from typing import Any

from ..evaluation import FrequencyConfig, evaluate_spectral_regularity
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
        return rows, summary

    return run_guarded(output_dir, "frequency", calculate)

