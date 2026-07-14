from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import cv2
import numpy as np


@dataclass(frozen=True)
class FrequencyPreservationConfig:
    max_side: int = 720
    dc_radius_fraction: float = 0.05
    high_radius_fraction: float = 0.35
    band_min_fraction: float = 0.22
    band_max_fraction: float = 0.70
    orientation_bins: int = 36


def _to_gray_float(image: np.ndarray, max_side: int) -> np.ndarray:
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY) if image.ndim == 3 else image.copy()
    height, width = gray.shape[:2]
    if max_side > 0 and max(height, width) > max_side:
        scale = max_side / max(height, width)
        gray = cv2.resize(
            gray,
            (max(1, int(width * scale)), max(1, int(height * scale))),
            interpolation=cv2.INTER_AREA,
        )
    return gray.astype(np.float32) / 255.0


def _fft_fields(gray: np.ndarray) -> dict[str, np.ndarray]:
    height, width = gray.shape[:2]
    centered = gray - float(np.mean(gray))
    window = np.outer(np.hanning(height), np.hanning(width)).astype(np.float32)
    spectrum = np.fft.fftshift(np.fft.fft2(centered * window))
    magnitude = np.abs(spectrum).astype(np.float64)
    log_magnitude = np.log1p(magnitude)

    yy, xx = np.indices((height, width))
    center_y = height // 2
    center_x = width // 2
    dx = xx - center_x
    dy = yy - center_y
    radius = np.hypot(dx, dy)
    radius_norm = radius / max(1.0, 0.5 * min(height, width))
    angle = (np.degrees(np.arctan2(dy, dx)) + 180.0) % 180.0
    return {
        "log_magnitude": log_magnitude,
        "power": magnitude * magnitude,
        "radius_norm": radius_norm,
        "angle": angle,
    }


def _cosine_similarity(left: np.ndarray, right: np.ndarray) -> float | None:
    left_flat = left.astype(np.float64).ravel()
    right_flat = right.astype(np.float64).ravel()
    left_norm = float(np.linalg.norm(left_flat))
    right_norm = float(np.linalg.norm(right_flat))
    if left_norm == 0.0 or right_norm == 0.0:
        return None
    return float(np.dot(left_flat, right_flat) / (left_norm * right_norm))


def _energy_ratio(reference: np.ndarray, normalized: np.ndarray) -> float | None:
    reference_energy = float(np.sum(reference))
    if reference_energy <= 0.0:
        return None
    return float(np.sum(normalized) / reference_energy)


def _log_ratio_abs(ratio: float | None) -> float | None:
    if ratio is None or ratio <= 0.0:
        return None
    return float(abs(np.log(ratio)))


def _orientation_histogram(
    fields: dict[str, np.ndarray],
    mask: np.ndarray,
    bins: int,
) -> np.ndarray | None:
    weights = fields["log_magnitude"][mask]
    if weights.size == 0 or float(np.sum(weights)) <= 0.0:
        return None
    hist, _ = np.histogram(fields["angle"][mask], bins=bins, range=(0.0, 180.0), weights=weights)
    total = float(np.sum(hist))
    return hist.astype(np.float64) / total if total > 0.0 else None


def _histogram_intersection(left: np.ndarray | None, right: np.ndarray | None) -> float | None:
    if left is None or right is None:
        return None
    return float(np.minimum(left, right).sum())


def evaluate_frequency_preservation_pair(
    reference_image: np.ndarray,
    normalized_image: np.ndarray,
    config: FrequencyPreservationConfig | None = None,
) -> dict[str, Any]:
    """Compare frequency structure after geometric normalization.

    The reference image should be the original frame warped with ground-truth
    screen corners to the same canvas as the normalized output.
    """

    cfg = config or FrequencyPreservationConfig()
    reference_gray = _to_gray_float(reference_image, cfg.max_side)
    normalized_gray = _to_gray_float(normalized_image, cfg.max_side)
    if reference_gray.shape != normalized_gray.shape:
        normalized_gray = cv2.resize(
            normalized_gray,
            (reference_gray.shape[1], reference_gray.shape[0]),
            interpolation=cv2.INTER_AREA,
        )

    reference = _fft_fields(reference_gray)
    normalized = _fft_fields(normalized_gray)
    radius = reference["radius_norm"]
    valid = (radius > cfg.dc_radius_fraction) & (radius <= 1.0)
    high = valid & (radius >= cfg.high_radius_fraction)
    band = valid & (radius >= cfg.band_min_fraction) & (radius <= cfg.band_max_fraction)

    log_fft_similarity = _cosine_similarity(
        reference["log_magnitude"][valid],
        normalized["log_magnitude"][valid],
    )
    high_ratio = _energy_ratio(reference["power"][high], normalized["power"][high])
    band_ratio = _energy_ratio(reference["power"][band], normalized["power"][band])
    reference_hist = _orientation_histogram(reference, high, cfg.orientation_bins)
    normalized_hist = _orientation_histogram(normalized, high, cfg.orientation_bins)

    return {
        "status": "ok",
        "log_fft_magnitude_similarity": log_fft_similarity,
        "high_frequency_energy_ratio": high_ratio,
        "high_frequency_log_ratio_abs": _log_ratio_abs(high_ratio),
        "orientation_histogram_intersection": _histogram_intersection(reference_hist, normalized_hist),
        "band_energy_ratio": band_ratio,
        "band_log_ratio_abs": _log_ratio_abs(band_ratio),
        "reference_high_frequency_energy": float(np.sum(reference["power"][high])),
        "normalized_high_frequency_energy": float(np.sum(normalized["power"][high])),
    }
