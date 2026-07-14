from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import cv2
import numpy as np


@dataclass(frozen=True)
class DetailPreservationConfig:
    max_side: int = 720
    canny_low: int = 80
    canny_high: int = 160
    edge_tolerance: int = 1


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


def _resize_to_reference(reference: np.ndarray, normalized: np.ndarray) -> np.ndarray:
    if reference.shape == normalized.shape:
        return normalized
    return cv2.resize(normalized, (reference.shape[1], reference.shape[0]), interpolation=cv2.INTER_AREA)


def _gradient_magnitude(gray: np.ndarray) -> np.ndarray:
    grad_x = cv2.Sobel(gray, cv2.CV_32F, 1, 0, ksize=3)
    grad_y = cv2.Sobel(gray, cv2.CV_32F, 0, 1, ksize=3)
    return cv2.magnitude(grad_x, grad_y)


def _cosine_similarity(left: np.ndarray, right: np.ndarray) -> float | None:
    left_flat = left.astype(np.float64).ravel()
    right_flat = right.astype(np.float64).ravel()
    left_norm = float(np.linalg.norm(left_flat))
    right_norm = float(np.linalg.norm(right_flat))
    if left_norm == 0.0 or right_norm == 0.0:
        return None
    return float(np.dot(left_flat, right_flat) / (left_norm * right_norm))


def _ratio(reference_value: float, normalized_value: float) -> float | None:
    if reference_value <= 0.0:
        return None
    return float(normalized_value / reference_value)


def _log_ratio_abs(ratio: float | None) -> float | None:
    if ratio is None or ratio <= 0.0:
        return None
    return float(abs(np.log(ratio)))


def _ssim(reference: np.ndarray, normalized: np.ndarray) -> float:
    c1 = 0.01**2
    c2 = 0.03**2
    mu_ref = cv2.GaussianBlur(reference, (11, 11), 1.5)
    mu_norm = cv2.GaussianBlur(normalized, (11, 11), 1.5)
    mu_ref_sq = mu_ref * mu_ref
    mu_norm_sq = mu_norm * mu_norm
    mu_ref_norm = mu_ref * mu_norm
    sigma_ref_sq = cv2.GaussianBlur(reference * reference, (11, 11), 1.5) - mu_ref_sq
    sigma_norm_sq = cv2.GaussianBlur(normalized * normalized, (11, 11), 1.5) - mu_norm_sq
    sigma_ref_norm = cv2.GaussianBlur(reference * normalized, (11, 11), 1.5) - mu_ref_norm
    numerator = (2.0 * mu_ref_norm + c1) * (2.0 * sigma_ref_norm + c2)
    denominator = (mu_ref_sq + mu_norm_sq + c1) * (sigma_ref_sq + sigma_norm_sq + c2)
    return float(np.mean(numerator / np.maximum(denominator, 1.0e-12)))


def _edge_metrics(reference: np.ndarray, normalized: np.ndarray, config: DetailPreservationConfig) -> dict[str, float | None]:
    reference_u8 = np.clip(reference * 255.0, 0, 255).astype(np.uint8)
    normalized_u8 = np.clip(normalized * 255.0, 0, 255).astype(np.uint8)
    reference_edges = cv2.Canny(reference_u8, config.canny_low, config.canny_high)
    normalized_edges = cv2.Canny(normalized_u8, config.canny_low, config.canny_high)
    kernel_size = 2 * config.edge_tolerance + 1
    kernel = np.ones((kernel_size, kernel_size), dtype=np.uint8)
    reference_dilated = cv2.dilate(reference_edges, kernel, iterations=1)
    normalized_dilated = cv2.dilate(normalized_edges, kernel, iterations=1)

    pred_count = int(np.count_nonzero(normalized_edges))
    ref_count = int(np.count_nonzero(reference_edges))
    true_pred = int(np.count_nonzero((normalized_edges > 0) & (reference_dilated > 0)))
    true_ref = int(np.count_nonzero((reference_edges > 0) & (normalized_dilated > 0)))
    precision = true_pred / pred_count if pred_count else None
    recall = true_ref / ref_count if ref_count else None
    f1 = None if precision is None or recall is None or precision + recall == 0 else 2.0 * precision * recall / (precision + recall)
    return {
        "edge_precision": float(precision) if precision is not None else None,
        "edge_recall": float(recall) if recall is not None else None,
        "edge_f1": float(f1) if f1 is not None else None,
        "reference_edge_density": float(ref_count / reference_edges.size),
        "normalized_edge_density": float(pred_count / normalized_edges.size),
    }


def evaluate_detail_preservation_pair(
    reference_image: np.ndarray,
    normalized_image: np.ndarray,
    config: DetailPreservationConfig | None = None,
) -> dict[str, Any]:
    """Compare local detail after geometric normalization.

    The reference image should be the original frame warped with ground-truth
    screen corners to the same canvas as the normalized output.
    """

    cfg = config or DetailPreservationConfig()
    reference = _to_gray_float(reference_image, cfg.max_side)
    normalized = _resize_to_reference(reference, _to_gray_float(normalized_image, cfg.max_side))

    reference_gradient = _gradient_magnitude(reference)
    normalized_gradient = _gradient_magnitude(normalized)
    reference_gradient_mean = float(np.mean(reference_gradient))
    normalized_gradient_mean = float(np.mean(normalized_gradient))
    gradient_ratio = _ratio(reference_gradient_mean, normalized_gradient_mean)

    reference_laplacian = cv2.Laplacian(reference, cv2.CV_32F, ksize=3)
    normalized_laplacian = cv2.Laplacian(normalized, cv2.CV_32F, ksize=3)
    reference_laplacian_energy = float(np.mean(reference_laplacian * reference_laplacian))
    normalized_laplacian_energy = float(np.mean(normalized_laplacian * normalized_laplacian))
    laplacian_ratio = _ratio(reference_laplacian_energy, normalized_laplacian_energy)

    return {
        "status": "ok",
        "ssim": _ssim(reference, normalized),
        "gradient_magnitude_similarity": _cosine_similarity(reference_gradient, normalized_gradient),
        "gradient_magnitude_ratio": gradient_ratio,
        "gradient_log_ratio_abs": _log_ratio_abs(gradient_ratio),
        "laplacian_energy_ratio": laplacian_ratio,
        "laplacian_log_ratio_abs": _log_ratio_abs(laplacian_ratio),
        **_edge_metrics(reference, normalized, cfg),
    }
