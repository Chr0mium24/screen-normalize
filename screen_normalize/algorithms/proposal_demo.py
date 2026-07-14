from __future__ import annotations

import csv
from dataclasses import dataclass
from pathlib import Path

import cv2
import numpy as np

from .boundary import corners_from_lines, observe_quad_edges
from .detection import detect_screen_corners, select_tracking_points
from .geometry import (
    detected_corners_are_valid,
    geometry_update_is_reasonable,
    homography_median_reprojection_error,
    order_corners,
)


@dataclass(frozen=True)
class ProposalDemoConfig:
    sample_count: int = 50
    search_radii: tuple[int, ...] = (20, 60, 120)
    min_edge_confidence: float = 0.35
    max_scale_step: float = 0.10
    max_area_step: float = 0.20
    min_lk_inliers: int = 24
    min_lk_inlier_ratio: float = 0.25
    max_lk_disagreement: float = 24.0
    max_frames: int = 0


def estimate_lk_consistency(
    previous_gray: np.ndarray | None,
    gray: np.ndarray,
    previous_corners: np.ndarray,
    border_corners: np.ndarray,
    config: ProposalDemoConfig,
) -> dict[str, object]:
    if previous_gray is None:
        return {"lk_status": "initial"}

    points = select_tracking_points(previous_gray, previous_corners)
    if points is None:
        return {"lk_status": "no_points"}

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
        return {"lk_status": "flow_failed", "lk_point_count": len(points)}

    valid = status.reshape(-1).astype(bool)
    previous_good = points.reshape(-1, 2)[valid]
    current_good = next_points.reshape(-1, 2)[valid]
    if len(previous_good) < max(8, config.min_lk_inliers):
        return {
            "lk_status": "too_few_tracks",
            "lk_point_count": len(points),
            "lk_valid_count": len(previous_good),
        }

    homography, inlier_mask = cv2.findHomography(
        previous_good,
        current_good,
        cv2.RANSAC,
        3.0,
    )
    if homography is None or inlier_mask is None:
        return {
            "lk_status": "homography_failed",
            "lk_point_count": len(points),
            "lk_valid_count": len(previous_good),
        }

    inlier_count = int(inlier_mask.sum())
    inlier_ratio = inlier_count / max(1, len(previous_good))
    projected = cv2.perspectiveTransform(
        previous_corners.reshape(1, 4, 2).astype(np.float32),
        homography,
    ).reshape(4, 2)
    disagreement = float(np.mean(np.linalg.norm(projected - border_corners, axis=1)))
    reprojection_error = homography_median_reprojection_error(
        previous_good,
        current_good,
        homography,
        inlier_mask,
    )
    consistent = (
        inlier_count >= config.min_lk_inliers
        and inlier_ratio >= config.min_lk_inlier_ratio
        and disagreement <= config.max_lk_disagreement
    )
    return {
        "lk_status": "consistent" if consistent else "content_conflict",
        "lk_point_count": len(points),
        "lk_valid_count": len(previous_good),
        "lk_inlier_count": inlier_count,
        "lk_inlier_ratio": inlier_ratio,
        "lk_reprojection_error": reprojection_error,
        "lk_border_disagreement": disagreement,
    }


def observe_border_candidate(
    gray: np.ndarray,
    predicted: np.ndarray,
    polarities: np.ndarray | None,
    config: ProposalDemoConfig,
) -> tuple[np.ndarray | None, list[dict[str, object]], np.ndarray | None, str]:
    attempts: list[dict[str, object]] = []
    best_measured: np.ndarray | None = None
    best_candidate: np.ndarray | None = None
    best_confidence = -1.0
    best_reason = "edge_not_found"

    for radius in config.search_radii:
        observations, measured = observe_quad_edges(
            gray,
            predicted,
            config.sample_count,
            radius,
            polarities,
        )
        candidate = corners_from_lines([item.line for item in observations])
        confidences = [float(item.confidence) for item in observations]
        min_confidence = min(confidences) if confidences else 0.0
        attempts.append(
            {
                "radius": radius,
                "candidate_found": candidate is not None,
                "min_edge_confidence": min_confidence,
                **{f"edge_{index}_confidence": value for index, value in enumerate(confidences)},
                **{
                    f"edge_{index}_inliers": int(item.inliers.sum())
                    for index, item in enumerate(observations)
                },
            }
        )

        if min_confidence > best_confidence:
            best_confidence = min_confidence
            best_measured = measured
            best_candidate = candidate

        if candidate is None:
            best_reason = "edge_line_missing"
            continue
        if min_confidence < config.min_edge_confidence:
            best_reason = "edge_low_confidence"
            continue
        if not detected_corners_are_valid(candidate, gray.shape):
            best_reason = "edge_invalid_quad"
            continue
        if not geometry_update_is_reasonable(
            candidate,
            predicted,
            config.max_scale_step,
            config.max_area_step,
        ):
            best_reason = "edge_geometry_jump"
            continue
        return candidate.astype(np.float32), attempts, measured, "edge_accepted"

    if best_candidate is not None and best_confidence >= 0:
        best_reason = f"{best_reason}_best_conf_{best_confidence:.3f}"
    return None, attempts, best_measured, best_reason


def update_polarities(
    previous: np.ndarray | None,
    measured: np.ndarray | None,
) -> np.ndarray | None:
    if measured is None:
        return previous
    if previous is None:
        return measured.copy()
    updated = previous.copy()
    nonzero = measured != 0
    updated[nonzero] = measured[nonzero]
    return updated


def estimate_proposal_border_trajectory(
    capture: cv2.VideoCapture,
    initial_corners: np.ndarray | None,
    config: ProposalDemoConfig | None = None,
    debug_rows: list[dict[str, object]] | None = None,
) -> list[np.ndarray]:
    config = config or ProposalDemoConfig()
    ok, frame = capture.read()
    if not ok:
        return []

    predicted = initial_corners
    if predicted is None:
        predicted = detect_screen_corners(frame)
    if predicted is None:
        raise ValueError("proposal demo needs manual corners or detectable first-frame corners")

    predicted = order_corners(predicted).astype(np.float32)
    trajectory = [predicted.copy()]
    previous_gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    polarities: np.ndarray | None = None
    append_debug_row(
        debug_rows,
        frame_index=0,
        accepted=True,
        reason="initial",
        corners=predicted,
        extra={"lk_status": "initial"},
    )

    frame_index = 1
    while True:
        if config.max_frames and frame_index >= config.max_frames:
            break
        ok, frame = capture.read()
        if not ok:
            break
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        candidate, attempts, measured, edge_reason = observe_border_candidate(
            gray,
            predicted,
            polarities,
            config,
        )
        accepted = False
        reason = edge_reason
        extra = flatten_latest_attempt(attempts)

        if candidate is not None:
            lk = estimate_lk_consistency(previous_gray, gray, predicted, candidate, config)
            predicted = candidate
            polarities = update_polarities(polarities, measured)
            accepted = True
            reason = "edge_accept_lk_conflict" if lk.get("lk_status") == "content_conflict" else "edge_accept"
            extra.update(lk)
        else:
            redetected = detect_screen_corners(frame)
            if (
                redetected is not None
                and detected_corners_are_valid(redetected, gray.shape)
                and geometry_update_is_reasonable(
                    redetected,
                    predicted,
                    config.max_scale_step * 1.5,
                    config.max_area_step * 1.5,
                )
            ):
                candidate = order_corners(redetected).astype(np.float32)
                lk = estimate_lk_consistency(previous_gray, gray, predicted, candidate, config)
                predicted = candidate
                accepted = True
                reason = "redetect_accept"
                extra.update(lk)
            else:
                extra.update({"lk_status": "skipped_no_border_candidate"})

        trajectory.append(predicted.copy())
        append_debug_row(
            debug_rows,
            frame_index=frame_index,
            accepted=accepted,
            reason=reason,
            corners=predicted,
            extra=extra,
        )
        previous_gray = gray
        frame_index += 1

    return trajectory


def flatten_latest_attempt(attempts: list[dict[str, object]]) -> dict[str, object]:
    if not attempts:
        return {}
    latest = attempts[-1].copy()
    latest["edge_attempt_count"] = len(attempts)
    return latest


def append_debug_row(
    rows: list[dict[str, object]] | None,
    frame_index: int,
    accepted: bool,
    reason: str,
    corners: np.ndarray,
    extra: dict[str, object],
) -> None:
    if rows is None:
        return
    labels = ("tl", "tr", "br", "bl")
    row: dict[str, object] = {
        "frame": frame_index,
        "accepted": accepted,
        "reason": reason,
        **extra,
    }
    for label, point in zip(labels, corners, strict=True):
        row[f"{label}_x"] = float(point[0])
        row[f"{label}_y"] = float(point[1])
    rows.append(row)


def write_proposal_debug_csv(path: Path, rows: list[dict[str, object]]) -> None:
    base = [
        "frame",
        "accepted",
        "reason",
        "radius",
        "edge_attempt_count",
        "candidate_found",
        "min_edge_confidence",
        "lk_status",
        "lk_point_count",
        "lk_valid_count",
        "lk_inlier_count",
        "lk_inlier_ratio",
        "lk_reprojection_error",
        "lk_border_disagreement",
    ]
    edge_fields = [
        field
        for index in range(4)
        for field in (f"edge_{index}_confidence", f"edge_{index}_inliers")
    ]
    corner_fields = [
        field
        for label in ("tl", "tr", "br", "bl")
        for field in (f"{label}_x", f"{label}_y")
    ]
    fieldnames = [*base, *edge_fields, *corner_fields]
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def write_corner_trajectory_csv(path: Path, trajectory: list[np.ndarray]) -> None:
    fieldnames = [
        "frame",
        *[
            field
            for label in ("tl", "tr", "br", "bl")
            for field in (f"{label}_x", f"{label}_y")
        ],
    ]
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for frame_index, corners in enumerate(trajectory):
            row: dict[str, object] = {"frame": frame_index}
            for label, point in zip(("tl", "tr", "br", "bl"), corners, strict=True):
                row[f"{label}_x"] = float(point[0])
                row[f"{label}_y"] = float(point[1])
            writer.writerow(row)
