from __future__ import annotations

import csv
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import cv2
import numpy as np

from .geometry import corner_edge_lengths, order_corners


CORNER_LABELS = ("tl", "tr", "br", "bl")


@dataclass(frozen=True)
class VideoMetadata:
    path: str
    width: int
    height: int
    fps: float
    frame_count: int
    duration_seconds: float


@dataclass(frozen=True)
class MotionConfig:
    max_corners: int = 800
    quality_level: float = 0.01
    min_distance: int = 10
    min_points: int = 30
    ransac_threshold: float = 2.0


@dataclass(frozen=True)
class SignalConfig:
    sample_stride: int = 30
    max_frames: int = 120
    canny_low: int = 80
    canny_high: int = 160


@dataclass(frozen=True)
class FrequencyConfig:
    sample_stride: int = 30
    max_frames: int = 120
    max_side: int = 720
    dc_radius_fraction: float = 0.05
    peak_percentile: float = 99.5
    min_peak_points: int = 20


def video_metadata(path: Path) -> VideoMetadata:
    capture = cv2.VideoCapture(str(path))
    if not capture.isOpened():
        raise SystemExit(f"could not open video: {path}")

    width = int(capture.get(cv2.CAP_PROP_FRAME_WIDTH) or 0)
    height = int(capture.get(cv2.CAP_PROP_FRAME_HEIGHT) or 0)
    fps = float(capture.get(cv2.CAP_PROP_FPS) or 0.0)
    if fps <= 0:
        fps = 60.0
    frame_count = int(capture.get(cv2.CAP_PROP_FRAME_COUNT) or 0)
    capture.release()
    duration = frame_count / fps if frame_count else 0.0
    return VideoMetadata(
        path=str(path),
        width=width,
        height=height,
        fps=fps,
        frame_count=frame_count,
        duration_seconds=duration,
    )


def as_jsonable(value: Any) -> Any:
    if isinstance(value, dict):
        return {str(key): as_jsonable(item) for key, item in value.items()}
    if isinstance(value, list | tuple):
        return [as_jsonable(item) for item in value]
    if isinstance(value, np.integer):
        return int(value)
    if isinstance(value, np.floating):
        return float(value)
    if isinstance(value, np.ndarray):
        return value.tolist()
    return value


def write_dict_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    fieldnames: list[str] = []
    for row in rows:
        for key in row:
            if key not in fieldnames:
                fieldnames.append(key)
    with path.open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def normalized_coverage(points: np.ndarray, width: int, height: int) -> tuple[float, float]:
    if len(points) < 2 or width <= 1 or height <= 1:
        return 0.0, 0.0
    normalized = points.astype(np.float32).copy()
    normalized[:, 0] /= float(width - 1)
    normalized[:, 1] /= float(height - 1)
    lower = np.percentile(normalized, 5, axis=0)
    upper = np.percentile(normalized, 95, axis=0)
    coverage = np.maximum(upper - lower, 0.0)
    return float(coverage[0]), float(coverage[1])


def estimate_pair_motion(
    previous_gray: np.ndarray,
    gray: np.ndarray,
    config: MotionConfig,
) -> dict[str, float | int | bool | str]:
    height, width = previous_gray.shape[:2]
    points = cv2.goodFeaturesToTrack(
        previous_gray,
        maxCorners=config.max_corners,
        qualityLevel=config.quality_level,
        minDistance=config.min_distance,
        blockSize=7,
    )
    if points is None or len(points) < config.min_points:
        return {
            "ok": False,
            "reason": "not_enough_features",
            "feature_count": 0 if points is None else int(len(points)),
        }

    next_points, status, _ = cv2.calcOpticalFlowPyrLK(
        previous_gray,
        gray,
        points,
        None,
        winSize=(31, 31),
        maxLevel=3,
        criteria=(cv2.TERM_CRITERIA_EPS | cv2.TERM_CRITERIA_COUNT, 30, 0.01),
    )
    if next_points is None or status is None:
        return {"ok": False, "reason": "flow_failed", "feature_count": int(len(points))}

    valid = status.reshape(-1).astype(bool)
    previous_good = points.reshape(-1, 2)[valid]
    current_good = next_points.reshape(-1, 2)[valid]
    if len(previous_good) < config.min_points:
        return {
            "ok": False,
            "reason": "not_enough_tracked_points",
            "feature_count": int(len(points)),
            "tracked_count": int(len(previous_good)),
        }

    affine, inlier_mask = cv2.estimateAffinePartial2D(
        previous_good,
        current_good,
        method=cv2.RANSAC,
        ransacReprojThreshold=config.ransac_threshold,
    )
    if affine is None or inlier_mask is None:
        return {
            "ok": False,
            "reason": "affine_failed",
            "feature_count": int(len(points)),
            "tracked_count": int(len(previous_good)),
        }

    inliers = inlier_mask.reshape(-1).astype(bool)
    inlier_count = int(inliers.sum())
    inlier_ratio = inlier_count / max(1, len(previous_good))
    coverage_x, coverage_y = normalized_coverage(previous_good[inliers], width, height)
    dx = float(affine[0, 2])
    dy = float(affine[1, 2])
    rotation_deg = float(np.degrees(np.arctan2(affine[1, 0], affine[0, 0])))
    scale = float(np.hypot(affine[0, 0], affine[1, 0]))
    return {
        "ok": True,
        "reason": "ok",
        "feature_count": int(len(points)),
        "tracked_count": int(len(previous_good)),
        "inlier_count": inlier_count,
        "inlier_ratio": float(inlier_ratio),
        "inlier_coverage_x": coverage_x,
        "inlier_coverage_y": coverage_y,
        "translation_x_px": dx,
        "translation_y_px": dy,
        "translation_px": float(np.hypot(dx, dy)),
        "rotation_deg": rotation_deg,
        "scale": scale,
        "scale_delta": float(scale - 1.0),
    }


def finite_values(
    rows: list[dict[str, Any]],
    key: str,
    *,
    require_ok: bool = True,
    absolute: bool = False,
) -> np.ndarray:
    values = []
    for row in rows:
        if require_ok and not row.get("ok"):
            continue
        value = row.get(key)
        if isinstance(value, int | float) and np.isfinite(value):
            values.append(abs(float(value)) if absolute else float(value))
    return np.asarray(values, dtype=np.float64)


def summarize_numeric(
    rows: list[dict[str, Any]],
    metrics: dict[str, tuple[str, bool]],
    *,
    require_ok: bool = True,
) -> dict[str, float | int | None]:
    summary: dict[str, float | int | None] = {"rows": len(rows)}
    if require_ok:
        summary["ok_rows"] = sum(1 for row in rows if row.get("ok"))
    for source, (prefix, absolute) in metrics.items():
        values = finite_values(rows, source, require_ok=require_ok, absolute=absolute)
        if values.size == 0:
            summary[f"{prefix}_mean"] = None
            summary[f"{prefix}_p50"] = None
            summary[f"{prefix}_p95"] = None
            summary[f"{prefix}_max"] = None
            continue
        summary[f"{prefix}_mean"] = float(np.mean(values))
        summary[f"{prefix}_p50"] = float(np.percentile(values, 50))
        summary[f"{prefix}_p95"] = float(np.percentile(values, 95))
        summary[f"{prefix}_max"] = float(np.max(values))
    return summary


def analyze_temporal_stability(
    video: Path,
    config: MotionConfig,
    last_seconds: float,
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    metadata = video_metadata(video)
    capture = cv2.VideoCapture(str(video))
    if not capture.isOpened():
        raise SystemExit(f"could not open video: {video}")

    ok, previous = capture.read()
    if not ok:
        raise SystemExit(f"video has no frames: {video}")
    previous_gray = cv2.cvtColor(previous, cv2.COLOR_BGR2GRAY)

    rows: list[dict[str, Any]] = []
    frame_index = 1
    while True:
        ok, frame = capture.read()
        if not ok:
            break
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        motion = estimate_pair_motion(previous_gray, gray, config)
        row: dict[str, Any] = {
            "dimension": "temporal_stability",
            "frame": frame_index,
            "time_seconds": frame_index / metadata.fps,
        }
        row.update(motion)
        rows.append(row)
        previous_gray = gray
        frame_index += 1

    capture.release()
    metrics = {
        "translation_px": ("translation_px", False),
        "rotation_deg": ("rotation_abs_deg", True),
        "scale_delta": ("scale_abs_delta", True),
        "inlier_ratio": ("inlier_ratio", False),
        "inlier_coverage_x": ("inlier_coverage_x", False),
        "inlier_coverage_y": ("inlier_coverage_y", False),
    }
    duration = metadata.duration_seconds or (frame_index / metadata.fps)
    last_start = max(0.0, duration - last_seconds)
    last_rows = [row for row in rows if float(row["time_seconds"]) >= last_start]
    return rows, {
        "status": "ok",
        "video": as_jsonable(metadata.__dict__),
        "all": summarize_numeric(rows, metrics),
        "last_seconds": {
            "seconds": last_seconds,
            "start_time_seconds": last_start,
            **summarize_numeric(last_rows, metrics),
        },
    }


def corners_from_row(row: dict[str, str], prefix: str) -> np.ndarray | None:
    points = []
    for label in CORNER_LABELS:
        x_key = f"{prefix}{label}_x"
        y_key = f"{prefix}{label}_y"
        if x_key not in row or y_key not in row:
            return None
        try:
            points.append([float(row[x_key]), float(row[y_key])])
        except ValueError:
            return None
    return order_corners(np.asarray(points, dtype=np.float32))


def detect_corner_prefix(fieldnames: list[str], requested: str = "auto") -> str:
    if requested != "auto":
        return requested
    for prefix in ("", "smoothed_", "interpolated_", "raw_", "gt_", "estimated_"):
        if all(f"{prefix}{label}_x" in fieldnames for label in CORNER_LABELS):
            return prefix
    raise SystemExit("could not detect corner columns in CSV")


def read_corner_csv(path: Path, prefix: str = "auto") -> dict[int, np.ndarray]:
    with path.open(newline="") as handle:
        reader = csv.DictReader(handle)
        if reader.fieldnames is None or "frame" not in reader.fieldnames:
            raise SystemExit(f"corner CSV must include a frame column: {path}")
        chosen_prefix = detect_corner_prefix(reader.fieldnames, prefix)
        corners_by_frame: dict[int, np.ndarray] = {}
        for row in reader:
            try:
                frame = int(row["frame"])
            except ValueError:
                continue
            corners = corners_from_row(row, chosen_prefix)
            if corners is not None:
                corners_by_frame[frame] = corners
    return corners_by_frame


def read_corner_json(path: Path) -> dict[int, np.ndarray]:
    with path.open() as handle:
        payload = json.load(handle)
    if isinstance(payload, dict):
        raw_frames = payload.get("frames") or payload.get("annotations")
        if raw_frames is None:
            raw_frames = [
                {"frame": frame, "corners": corners}
                for frame, corners in payload.items()
                if str(frame).isdigit()
            ]
    elif isinstance(payload, list):
        raw_frames = payload
    else:
        raise SystemExit(f"unsupported annotation JSON shape: {path}")

    corners_by_frame: dict[int, np.ndarray] = {}
    for item in raw_frames:
        try:
            frame = int(item["frame"])
            corners = np.asarray(item["corners"], dtype=np.float32).reshape(4, 2)
        except (KeyError, TypeError, ValueError):
            continue
        corners_by_frame[frame] = order_corners(corners)
    return corners_by_frame


def read_corner_map(path: Path, prefix: str = "auto") -> dict[int, np.ndarray]:
    suffix = path.suffix.lower()
    if suffix == ".json":
        return read_corner_json(path)
    if suffix == ".csv":
        return read_corner_csv(path, prefix=prefix)
    raise SystemExit(f"corner file must be .csv or .json: {path}")


def quadrilateral_aspect(corners: np.ndarray) -> float:
    top, right, bottom, left = corner_edge_lengths(corners)
    avg_width = (float(top) + float(bottom)) / 2.0
    avg_height = (float(left) + float(right)) / 2.0
    if avg_height <= 0:
        return float("nan")
    return avg_width / avg_height


def quadrilateral_iou(
    a: np.ndarray,
    b: np.ndarray,
    width: int,
    height: int,
) -> float:
    if width <= 0 or height <= 0:
        all_points = np.vstack([a, b])
        width = int(max(1.0, np.ceil(float(np.max(all_points[:, 0])) + 4.0)))
        height = int(max(1.0, np.ceil(float(np.max(all_points[:, 1])) + 4.0)))
    mask_a = np.zeros((height, width), dtype=np.uint8)
    mask_b = np.zeros((height, width), dtype=np.uint8)
    cv2.fillConvexPoly(mask_a, np.round(a).astype(np.int32), 1)
    cv2.fillConvexPoly(mask_b, np.round(b).astype(np.int32), 1)
    union = int(np.count_nonzero(mask_a | mask_b))
    if union == 0:
        return 0.0
    intersection = int(np.count_nonzero(mask_a & mask_b))
    return intersection / union


def evaluate_geometry_accuracy(
    annotations: dict[int, np.ndarray],
    estimates: dict[int, np.ndarray],
    width: int,
    height: int,
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for frame in sorted(set(annotations) & set(estimates)):
        gt = annotations[frame]
        pred = estimates[frame]
        distances = np.linalg.norm(pred - gt, axis=1)
        gt_aspect = quadrilateral_aspect(gt)
        pred_aspect = quadrilateral_aspect(pred)
        aspect_error = abs(pred_aspect - gt_aspect)
        relative_aspect_error = (
            aspect_error / gt_aspect if np.isfinite(gt_aspect) and gt_aspect else None
        )
        rows.append(
            {
                "dimension": "geometry_accuracy",
                "frame": frame,
                "ok": True,
                "corner_rmse_px": float(np.sqrt(np.mean(distances**2))),
                "corner_mean_px": float(np.mean(distances)),
                "corner_max_px": float(np.max(distances)),
                "quad_iou": quadrilateral_iou(gt, pred, width, height),
                "gt_aspect": float(gt_aspect),
                "estimated_aspect": float(pred_aspect),
                "aspect_abs_error": float(aspect_error),
                "aspect_relative_error": (
                    float(relative_aspect_error)
                    if relative_aspect_error is not None
                    else None
                ),
            }
        )

    metrics = {
        "corner_rmse_px": ("corner_rmse_px", False),
        "corner_mean_px": ("corner_mean_px", False),
        "corner_max_px": ("corner_max_px", False),
        "quad_iou": ("quad_iou", False),
        "aspect_abs_error": ("aspect_abs_error", False),
        "aspect_relative_error": ("aspect_relative_error", False),
    }
    status = "ok" if rows else "skipped"
    reason = None if rows else "no overlapping annotation and estimate frames"
    summary: dict[str, Any] = {
        "status": status,
        "reason": reason,
        "annotation_frames": len(annotations),
        "estimate_frames": len(estimates),
        "matched_frames": len(rows),
        **summarize_numeric(rows, metrics),
    }
    return rows, summary


def select_sample_frames(
    frame_count: int,
    stride: int,
    max_frames: int,
    preferred_frames: list[int] | None = None,
) -> list[int]:
    if preferred_frames:
        frames = sorted(frame for frame in set(preferred_frames) if frame >= 0)
        if frame_count > 0:
            frames = [frame for frame in frames if frame < frame_count]
    else:
        step = max(1, stride)
        frames = list(range(0, max(0, frame_count), step))
        if not frames and frame_count > 0:
            frames = [0]
    if max_frames > 0 and len(frames) > max_frames:
        positions = np.linspace(0, len(frames) - 1, max_frames).round().astype(int)
        frames = [frames[int(index)] for index in positions]
    return frames


def read_frames(video: Path, indexes: list[int]) -> dict[int, np.ndarray]:
    wanted = sorted(set(indexes))
    if not wanted:
        return {}
    capture = cv2.VideoCapture(str(video))
    if not capture.isOpened():
        raise SystemExit(f"could not open video: {video}")

    frames: dict[int, np.ndarray] = {}
    wanted_set = set(wanted)
    max_index = wanted[-1]
    frame_index = 0
    while frame_index <= max_index:
        ok, frame = capture.read()
        if not ok:
            break
        if frame_index in wanted_set:
            frames[frame_index] = frame.copy()
            if len(frames) == len(wanted_set):
                break
        frame_index += 1
    capture.release()
    return frames


def warp_to_screen(frame: np.ndarray, corners: np.ndarray, width: int, height: int) -> np.ndarray:
    destination = np.array(
        [[0, 0], [width - 1, 0], [width - 1, height - 1], [0, height - 1]],
        dtype=np.float32,
    )
    transform = cv2.getPerspectiveTransform(corners.astype(np.float32), destination)
    return cv2.warpPerspective(
        frame,
        transform,
        (width, height),
        flags=cv2.INTER_CUBIC,
        borderMode=cv2.BORDER_REPLICATE,
    )


def mean_gradient_magnitude(gray: np.ndarray) -> float:
    gray_float = gray.astype(np.float32) / 255.0
    grad_x = cv2.Sobel(gray_float, cv2.CV_32F, 1, 0, ksize=3)
    grad_y = cv2.Sobel(gray_float, cv2.CV_32F, 0, 1, ksize=3)
    magnitude = cv2.magnitude(grad_x, grad_y)
    return float(np.mean(magnitude))


def edge_metrics(
    reference_gray: np.ndarray | None,
    normalized_gray: np.ndarray,
    config: SignalConfig,
) -> dict[str, float | None]:
    normalized_edges = cv2.Canny(normalized_gray, config.canny_low, config.canny_high)
    normalized_edge_density = float(np.count_nonzero(normalized_edges) / normalized_edges.size)
    if reference_gray is None:
        return {
            "reference_edge_density": None,
            "normalized_edge_density": normalized_edge_density,
            "edge_precision": None,
            "edge_recall": None,
            "edge_preservation_index": None,
        }

    reference_edges = cv2.Canny(reference_gray, config.canny_low, config.canny_high)
    reference_edge_density = float(np.count_nonzero(reference_edges) / reference_edges.size)
    kernel = np.ones((3, 3), dtype=np.uint8)
    reference_dilated = cv2.dilate(reference_edges, kernel, iterations=1)
    normalized_dilated = cv2.dilate(normalized_edges, kernel, iterations=1)

    pred_count = int(np.count_nonzero(normalized_edges))
    ref_count = int(np.count_nonzero(reference_edges))
    true_pred = int(np.count_nonzero((normalized_edges > 0) & (reference_dilated > 0)))
    true_ref = int(np.count_nonzero((reference_edges > 0) & (normalized_dilated > 0)))
    precision = true_pred / pred_count if pred_count else None
    recall = true_ref / ref_count if ref_count else None
    if precision is None or recall is None or precision + recall == 0:
        f1 = None
    else:
        f1 = 2.0 * precision * recall / (precision + recall)
    return {
        "reference_edge_density": reference_edge_density,
        "normalized_edge_density": normalized_edge_density,
        "edge_precision": float(precision) if precision is not None else None,
        "edge_recall": float(recall) if recall is not None else None,
        "edge_preservation_index": float(f1) if f1 is not None else None,
    }


def evaluate_signal_preservation(
    normalized_video: Path,
    original_video: Path | None,
    annotations: dict[int, np.ndarray] | None,
    config: SignalConfig,
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    normalized_meta = video_metadata(normalized_video)
    preferred = sorted(annotations) if annotations else None
    sample_frames = select_sample_frames(
        normalized_meta.frame_count,
        config.sample_stride,
        config.max_frames,
        preferred,
    )
    normalized_frames = read_frames(normalized_video, sample_frames)
    original_frames = (
        read_frames(original_video, sample_frames)
        if original_video is not None and annotations
        else {}
    )

    rows: list[dict[str, Any]] = []
    has_reference = bool(original_frames and annotations)
    for frame in sample_frames:
        normalized = normalized_frames.get(frame)
        if normalized is None:
            continue
        normalized_gray = cv2.cvtColor(normalized, cv2.COLOR_BGR2GRAY)
        reference_gray: np.ndarray | None = None
        if has_reference:
            original = original_frames.get(frame)
            corners = annotations.get(frame) if annotations else None
            if original is not None and corners is not None:
                reference = warp_to_screen(
                    original,
                    corners,
                    normalized_meta.width,
                    normalized_meta.height,
                )
                reference_gray = cv2.cvtColor(reference, cv2.COLOR_BGR2GRAY)

        normalized_gradient = mean_gradient_magnitude(normalized_gray)
        reference_gradient = (
            mean_gradient_magnitude(reference_gray) if reference_gray is not None else None
        )
        gradient_ratio = (
            normalized_gradient / reference_gradient
            if reference_gradient is not None and reference_gradient > 0
            else None
        )
        row: dict[str, Any] = {
            "dimension": "signal_preservation",
            "frame": frame,
            "ok": True,
            "has_reference": reference_gray is not None,
            "reference_gradient_mean": reference_gradient,
            "normalized_gradient_mean": normalized_gradient,
            "gradient_magnitude_ratio": gradient_ratio,
        }
        row.update(edge_metrics(reference_gray, normalized_gray, config))
        rows.append(row)

    metrics = {
        "normalized_gradient_mean": ("normalized_gradient_mean", False),
        "reference_gradient_mean": ("reference_gradient_mean", False),
        "gradient_magnitude_ratio": ("gradient_magnitude_ratio", False),
        "normalized_edge_density": ("normalized_edge_density", False),
        "reference_edge_density": ("reference_edge_density", False),
        "edge_precision": ("edge_precision", False),
        "edge_recall": ("edge_recall", False),
        "edge_preservation_index": ("edge_preservation_index", False),
    }
    status = "ok" if has_reference else "partial"
    reason = None if has_reference else "no original video plus annotation reference warp"
    return rows, {
        "status": status if rows else "skipped",
        "reason": reason if rows else "no sampled frames",
        "sampled_frames": len(rows),
        "has_reference": has_reference,
        **summarize_numeric(rows, metrics),
    }


def angle_diff_deg(a: float, b: float) -> float:
    return abs(((a - b + 90.0) % 180.0) - 90.0)


def strongest_bin_near(histogram: np.ndarray, center: int, radius: int) -> int:
    indexes = np.asarray([(center + offset) % 180 for offset in range(-radius, radius + 1)])
    best_local = int(np.argmax(histogram[indexes]))
    return int(indexes[best_local])


def fft_direction_metrics(gray: np.ndarray, config: FrequencyConfig) -> dict[str, Any]:
    height, width = gray.shape[:2]
    max_side = max(height, width)
    if config.max_side > 0 and max_side > config.max_side:
        scale = config.max_side / max_side
        gray = cv2.resize(
            gray,
            (max(1, int(width * scale)), max(1, int(height * scale))),
            interpolation=cv2.INTER_AREA,
        )
        height, width = gray.shape[:2]

    image = gray.astype(np.float32)
    image -= float(np.mean(image))
    window = np.outer(np.hanning(height), np.hanning(width)).astype(np.float32)
    spectrum = np.fft.fftshift(np.fft.fft2(image * window))
    magnitude = np.log1p(np.abs(spectrum))

    yy, xx = np.indices((height, width))
    center_y = height // 2
    center_x = width // 2
    dx = xx - center_x
    dy = yy - center_y
    radius = np.hypot(dx, dy)
    valid = radius > (min(height, width) * config.dc_radius_fraction)
    values = magnitude[valid]
    if values.size == 0:
        return {"ok": False, "reason": "empty_fft"}

    threshold = np.percentile(values, config.peak_percentile)
    peaks = valid & (magnitude >= threshold)
    peak_count = int(np.count_nonzero(peaks))
    if peak_count < config.min_peak_points:
        return {"ok": False, "reason": "not_enough_frequency_peaks", "peak_count": peak_count}

    ys, xs = np.where(peaks)
    weights = magnitude[ys, xs]
    angles = (np.degrees(np.arctan2(ys - center_y, xs - center_x)) + 180.0) % 180.0
    histogram, _ = np.histogram(angles, bins=180, range=(0.0, 180.0), weights=weights)
    kernel = np.asarray([1.0, 2.0, 3.0, 2.0, 1.0], dtype=np.float64)
    kernel /= kernel.sum()
    padded = np.r_[histogram[-2:], histogram, histogram[:2]]
    smoothed = np.convolve(padded, kernel, mode="valid")

    primary = int(np.argmax(smoothed))
    expected_orthogonal = (primary + 90) % 180
    secondary = strongest_bin_near(smoothed, expected_orthogonal, radius=25)
    separation = angle_diff_deg(primary, secondary)
    primary_axis_error = min(angle_diff_deg(primary, 0.0), angle_diff_deg(primary, 90.0))
    secondary_axis_error = min(angle_diff_deg(secondary, 0.0), angle_diff_deg(secondary, 90.0))
    total_weight = float(np.sum(smoothed))
    return {
        "ok": True,
        "reason": "ok",
        "peak_count": peak_count,
        "fft_primary_angle_deg": float(primary),
        "fft_secondary_angle_deg": float(secondary),
        "fft_angle_separation_deg": float(separation),
        "fft_orthogonality_error_deg": float(abs(90.0 - separation)),
        "fft_axis_alignment_error_deg": float((primary_axis_error + secondary_axis_error) / 2.0),
        "fft_primary_weight_share": float(smoothed[primary] / total_weight) if total_weight else None,
    }


def evaluate_spectral_regularity(
    normalized_video: Path,
    config: FrequencyConfig,
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    metadata = video_metadata(normalized_video)
    sample_frames = select_sample_frames(
        metadata.frame_count,
        config.sample_stride,
        config.max_frames,
    )
    frames = read_frames(normalized_video, sample_frames)
    rows: list[dict[str, Any]] = []
    for frame_index in sample_frames:
        frame = frames.get(frame_index)
        if frame is None:
            continue
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        row: dict[str, Any] = {
            "dimension": "spectral_regularity",
            "frame": frame_index,
        }
        row.update(fft_direction_metrics(gray, config))
        rows.append(row)

    metrics = {
        "fft_angle_separation_deg": ("fft_angle_separation_deg", False),
        "fft_orthogonality_error_deg": ("fft_orthogonality_error_deg", False),
        "fft_axis_alignment_error_deg": ("fft_axis_alignment_error_deg", False),
        "fft_primary_weight_share": ("fft_primary_weight_share", False),
        "peak_count": ("fft_peak_count", False),
    }
    return rows, {
        "status": "ok" if rows else "skipped",
        "reason": None if rows else "no sampled frames",
        "sampled_frames": len(rows),
        **summarize_numeric(rows, metrics),
    }


def flatten_summary(
    dimensions: dict[str, dict[str, Any]],
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []

    def visit(dimension: str, prefix: str, value: Any) -> None:
        if isinstance(value, dict):
            for key, item in value.items():
                next_prefix = f"{prefix}.{key}" if prefix else str(key)
                visit(dimension, next_prefix, item)
            return
        if isinstance(value, int | float | str | bool) or value is None:
            rows.append(
                {
                    "dimension": dimension,
                    "metric": prefix,
                    "value": value,
                }
            )

    for dimension, summary in dimensions.items():
        visit(dimension, "", summary)
    return rows
