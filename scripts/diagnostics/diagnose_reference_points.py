#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
from pathlib import Path

import cv2
import numpy as np

from screen_normalize.algorithms.detection import select_tracking_points
from screen_normalize.algorithms.geometry import (
    detected_corners_are_valid,
    geometry_update_is_reasonable,
    homography_inlier_screen_coverage,
    homography_median_reprojection_error,
    order_corners,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Visualize reference-tracker points with coverage gates disabled.")
    parser.add_argument("input", type=Path)
    parser.add_argument("annotations", type=Path)
    parser.add_argument("output_dir", type=Path)
    parser.add_argument("--display-width", type=int, default=1920)
    parser.add_argument("--feature-refresh", type=int, default=15)
    parser.add_argument("--min-point-age", type=int, default=15)
    return parser.parse_args()


def first_corners(path: Path) -> np.ndarray:
    with path.open(newline="", encoding="utf-8-sig") as handle:
        row = next(csv.DictReader(handle))
    return np.asarray(
        [[row[f"{p}_x"], row[f"{p}_y"]] for p in ("tl", "tr", "br", "bl")],
        dtype=np.float32,
    )


def draw_text(frame: np.ndarray, lines: list[str], scale: float) -> None:
    font_scale = max(0.55, 0.85 * scale)
    thickness = max(1, round(2 * scale))
    line_height = max(25, round(35 * scale))
    x, y = max(12, round(20 * scale)), max(28, round(40 * scale))
    for line in lines:
        (width, height), _ = cv2.getTextSize(line, cv2.FONT_HERSHEY_SIMPLEX, font_scale, thickness)
        cv2.rectangle(frame, (x - 7, y - height - 7), (x + width + 7, y + 7), (0, 0, 0), -1)
        cv2.putText(frame, line, (x, y), cv2.FONT_HERSHEY_SIMPLEX, font_scale, (255, 255, 255), thickness, cv2.LINE_AA)
        y += line_height


def main() -> None:
    args = parse_args()
    args.output_dir.mkdir(parents=True, exist_ok=True)
    capture = cv2.VideoCapture(str(args.input))
    if not capture.isOpened():
        raise SystemExit(f"cannot open {args.input}")
    fps = float(capture.get(cv2.CAP_PROP_FPS) or 30.0)
    ok, first = capture.read()
    if not ok:
        raise SystemExit("video has no frames")

    height, width = first.shape[:2]
    display_scale = min(1.0, args.display_width / width)
    display_size = (round(width * display_scale), round(height * display_scale))
    output_video = args.output_dir / "coverage_gate_disabled_points.mp4"
    writer = cv2.VideoWriter(str(output_video), cv2.VideoWriter_fourcc(*"mp4v"), fps, display_size)

    corners = order_corners(first_corners(args.annotations))
    reference_corners = corners.copy()
    previous_gray = cv2.cvtColor(first, cv2.COLOR_BGR2GRAY)
    reference_points = select_tracking_points(previous_gray, corners)
    if reference_points is None:
        raise SystemExit("no initial tracking points")
    current_points = reference_points.copy()
    ages = np.full(len(current_points), args.min_point_age, dtype=np.int32)
    rows: list[dict[str, object]] = []

    def render(frame: np.ndarray, frame_index: int, valid_points: np.ndarray, inliers: np.ndarray, coverage: tuple[float, float], reason: str) -> None:
        canvas = cv2.resize(frame, display_size, interpolation=cv2.INTER_AREA)
        scaled_corners = np.round(corners * display_scale).astype(np.int32)
        cv2.polylines(canvas, [scaled_corners], True, (255, 255, 0), max(1, round(3 * display_scale)), cv2.LINE_AA)
        for index, point in enumerate(valid_points):
            color = (0, 255, 0) if index < len(inliers) and inliers[index] else (0, 0, 255)
            p = tuple(np.round(point * display_scale).astype(int))
            cv2.circle(canvas, p, max(2, round(4 * display_scale)), color, -1, cv2.LINE_AA)
        draw_text(canvas, [
            f"frame={frame_index} coverage gates=OFF status={reason}",
            f"valid={len(valid_points)} inliers={int(inliers.sum()) if len(inliers) else 0} coverage=({coverage[0]:.3f}, {coverage[1]:.3f})",
            "green=RANSAC inlier  red=RANSAC outlier  cyan=estimated quad",
        ], display_scale)
        writer.write(canvas)

    initial = reference_points.reshape(-1, 2)
    render(first, 0, initial, np.ones(len(initial), dtype=bool), (1.0, 1.0), "initial")
    rows.append({"frame": 0, "accepted": True, "reason": "initial", "valid": len(initial), "inliers": len(initial), "coverage_x": 1.0, "coverage_y": 1.0})

    frame_index = 1
    while True:
        ok, frame = capture.read()
        if not ok:
            break
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        next_points, status, _ = cv2.calcOpticalFlowPyrLK(previous_gray, gray, current_points, None, winSize=(31, 31), maxLevel=3, criteria=(cv2.TERM_CRITERIA_EPS | cv2.TERM_CRITERIA_COUNT, 30, 0.01))
        back, back_status, _ = cv2.calcOpticalFlowPyrLK(gray, previous_gray, next_points, None, winSize=(31, 31), maxLevel=3, criteria=(cv2.TERM_CRITERIA_EPS | cv2.TERM_CRITERIA_COUNT, 30, 0.01)) if next_points is not None else (None, None, None)
        if next_points is None or status is None or back is None or back_status is None:
            render(frame, frame_index, np.empty((0, 2)), np.empty(0, dtype=bool), (0.0, 0.0), "flow_failed")
            previous_gray = gray
            frame_index += 1
            continue

        round_trip = np.linalg.norm(current_points.reshape(-1, 2) - back.reshape(-1, 2), axis=1)
        valid = status.reshape(-1).astype(bool) & back_status.reshape(-1).astype(bool) & (round_trip < 2.0)
        mature = valid & (ages >= args.min_point_age)
        ref_good = reference_points.reshape(-1, 2)[mature]
        cur_good = next_points.reshape(-1, 2)[mature]
        homography, mask = (cv2.findHomography(cur_good, ref_good, cv2.RANSAC, 3.0) if len(ref_good) >= 20 else (None, None))
        inliers = mask.reshape(-1).astype(bool) if mask is not None else np.zeros(len(cur_good), dtype=bool)
        coverage = homography_inlier_screen_coverage(ref_good, mask, reference_corners) if homography is not None and mask is not None else (0.0, 0.0)
        reprojection = homography_median_reprojection_error(cur_good, ref_good, homography, mask) if homography is not None and mask is not None else float("inf")
        accepted = False
        reason = "homography_failed"
        if homography is not None and mask is not None:
            ratio = int(inliers.sum()) / max(1, len(cur_good))
            if int(inliers.sum()) < 40:
                reason = "not_enough_inliers"
            elif ratio < 0.25:
                reason = "low_inlier_ratio"
            elif reprojection > 2.5:
                reason = "high_reprojection_error"
            else:
                candidate = order_corners(cv2.perspectiveTransform(reference_corners.reshape(1, 4, 2), np.linalg.inv(homography)).reshape(4, 2)).astype(np.float32)
                if detected_corners_are_valid(candidate, gray.shape) and geometry_update_is_reasonable(candidate, corners, max_scale_step=0.035, max_area_step=0.08):
                    corners = candidate
                    accepted = True
                    reason = "accepted_no_coverage_gate"
                else:
                    reason = "invalid_geometry"

        render(frame, frame_index, cur_good, inliers, coverage, reason)
        rows.append({"frame": frame_index, "accepted": accepted, "reason": reason, "valid": int(valid.sum()), "mature_valid": len(cur_good), "inliers": int(inliers.sum()), "inlier_ratio": int(inliers.sum()) / max(1, len(cur_good)), "reprojection_error": reprojection, "coverage_x": coverage[0], "coverage_y": coverage[1]})

        keep = valid
        reference_points = reference_points[keep]
        current_points = next_points[keep].astype(np.float32)
        ages = ages[keep]
        if accepted:
            ages += 1
            if len(current_points) < 140 or frame_index % args.feature_refresh == 0:
                fresh = select_tracking_points(gray, corners)
                if fresh is not None:
                    existing = current_points.reshape(-1, 2)
                    selected = []
                    for p in fresh.reshape(-1, 2):
                        if len(existing) and np.min(np.linalg.norm(existing - p, axis=1)) < 8:
                            continue
                        selected.append(p)
                        if len(selected) >= 250:
                            break
                    if selected:
                        fresh_current = np.asarray(selected, dtype=np.float32).reshape(-1, 1, 2)
                        fresh_reference = cv2.perspectiveTransform(fresh_current, homography)
                        reference_points = np.concatenate([reference_points, fresh_reference])
                        current_points = np.concatenate([current_points, fresh_current])
                        ages = np.concatenate([ages, np.zeros(len(fresh_current), dtype=np.int32)])
        previous_gray = gray
        frame_index += 1

    capture.release()
    writer.release()
    with (args.output_dir / "coverage_gate_disabled_points.csv").open("w", newline="", encoding="utf-8") as handle:
        fields = sorted({key for row in rows for key in row})
        csv_writer = csv.DictWriter(handle, fieldnames=fields)
        csv_writer.writeheader()
        csv_writer.writerows(rows)
    print(output_video)


if __name__ == "__main__":
    main()
