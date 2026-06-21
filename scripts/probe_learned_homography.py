#!/usr/bin/env python3
# /// script
# dependencies = [
#   "numpy>=2.2.0",
#   "opencv-python-headless>=4.12.0.88",
#   "torch>=2.8.0",
#   "torchvision>=0.23.0",
#   "lightglue @ git+https://github.com/cvg/LightGlue",
# ]
# ///

from __future__ import annotations

import argparse
import csv
import json
import sys
import time
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

import cv2
import numpy as np
import torch
from lightglue import LightGlue, SuperPoint
from lightglue.utils import numpy_image_to_torch, rbd

from normalize_screen import (
    DEFAULT_FALLBACK_CORNERS,
    create_run_directory,
    detected_corners_are_valid,
    detect_screen_corners,
    geometry_update_is_reasonable,
    homography_inlier_screen_coverage,
    homography_median_reprojection_error,
    open_capture,
    order_corners,
    parse_corners,
    project_root,
)


@dataclass
class LearnedMatcher:
    extractor: SuperPoint
    matcher: LightGlue
    reference_features: dict
    reference_keypoints: np.ndarray
    device: str


def positive_int(value: str) -> int:
    parsed = int(value)
    if parsed <= 0:
        raise argparse.ArgumentTypeError("value must be positive")
    return parsed


def nonnegative_float(value: str) -> float:
    parsed = float(value)
    if parsed < 0:
        raise argparse.ArgumentTypeError("value must be >= 0")
    return parsed


def fraction(value: str) -> float:
    parsed = float(value)
    if not 0 <= parsed <= 1:
        raise argparse.ArgumentTypeError("value must be between 0 and 1")
    return parsed


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Probe SuperPoint + LightGlue homography estimates for filmed-screen video."
        )
    )
    parser.add_argument("input", type=Path)
    parser.add_argument("--runs-dir", type=Path, default=None)
    parser.add_argument("--run-name", default=None)
    parser.add_argument(
        "--corners",
        type=parse_corners,
        default=None,
        help="Manual first-frame corners in TL,TR,BR,BL order.",
    )
    parser.add_argument("--reference-width", type=positive_int, default=960)
    parser.add_argument("--reference-height", type=positive_int, default=540)
    parser.add_argument("--sample-stride", type=positive_int, default=10)
    parser.add_argument("--max-samples", type=positive_int, default=32)
    parser.add_argument("--max-keypoints", type=positive_int, default=2048)
    parser.add_argument("--ransac-threshold", type=nonnegative_float, default=4.0)
    parser.add_argument("--min-matches", type=positive_int, default=40)
    parser.add_argument("--min-inliers", type=positive_int, default=30)
    parser.add_argument("--min-inlier-ratio", type=fraction, default=0.25)
    parser.add_argument("--min-coverage-x", type=fraction, default=0.20)
    parser.add_argument("--min-coverage-y", type=fraction, default=0.15)
    parser.add_argument("--max-reprojection-error", type=nonnegative_float, default=4.0)
    parser.add_argument("--max-scale-step", type=nonnegative_float, default=0.08)
    parser.add_argument("--max-area-step", type=nonnegative_float, default=0.16)
    parser.add_argument(
        "--device",
        choices=("auto", "cpu", "cuda", "mps"),
        default="auto",
    )
    parser.add_argument(
        "--write-match-debug",
        action="store_true",
        help="Write side-by-side match visualizations for accepted sampled frames.",
    )
    parser.add_argument("--debug-limit", type=positive_int, default=6)
    return parser.parse_args()


def resolve_device(requested: str) -> str:
    if requested != "auto":
        return requested
    if torch.cuda.is_available():
        return "cuda"
    if torch.backends.mps.is_available():
        return "mps"
    return "cpu"


def resolve_run_dir(args: argparse.Namespace) -> Path:
    runs_dir = args.runs_dir.resolve() if args.runs_dir else project_root() / "runs"
    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    run_name = args.run_name or f"{timestamp}_{Path(__file__).stem}"
    return create_run_directory(runs_dir, run_name).resolve()


def tensor_from_bgr(frame: np.ndarray, device: str) -> torch.Tensor:
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    return numpy_image_to_torch(gray).to(device)


def initialize_matcher(reference_bgr: np.ndarray, args: argparse.Namespace) -> LearnedMatcher:
    device = resolve_device(args.device)
    extractor = SuperPoint(max_num_keypoints=args.max_keypoints).eval().to(device)
    matcher = LightGlue(features="superpoint").eval().to(device)
    with torch.inference_mode():
        reference_tensor = tensor_from_bgr(reference_bgr, device)
        reference_features = extractor.extract(reference_tensor)
    reference_keypoints = rbd(reference_features)["keypoints"].detach().cpu().numpy()
    return LearnedMatcher(
        extractor=extractor,
        matcher=matcher,
        reference_features=reference_features,
        reference_keypoints=reference_keypoints,
        device=device,
    )


def match_frame(
    learned: LearnedMatcher,
    frame: np.ndarray,
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    with torch.inference_mode():
        frame_tensor = tensor_from_bgr(frame, learned.device)
        frame_features = learned.extractor.extract(frame_tensor)
        matches01 = learned.matcher(
            {"image0": learned.reference_features, "image1": frame_features}
        )
    frame_keypoints = rbd(frame_features)["keypoints"].detach().cpu().numpy()
    matches = rbd(matches01)["matches"].detach().cpu().numpy()
    if len(matches) == 0:
        return (
            np.empty((0, 2), dtype=np.float32),
            np.empty((0, 2), dtype=np.float32),
            matches,
        )
    reference_points = learned.reference_keypoints[matches[:, 0]].astype(np.float32)
    frame_points = frame_keypoints[matches[:, 1]].astype(np.float32)
    return reference_points, frame_points, matches


def reference_canvas(
    first_frame: np.ndarray,
    first_corners: np.ndarray,
    width: int,
    height: int,
) -> tuple[np.ndarray, np.ndarray]:
    reference_corners = np.array(
        [[0, 0], [width - 1, 0], [width - 1, height - 1], [0, height - 1]],
        dtype=np.float32,
    )
    source_to_reference = cv2.getPerspectiveTransform(
        first_corners.astype(np.float32),
        reference_corners,
    )
    return cv2.warpPerspective(first_frame, source_to_reference, (width, height)), reference_corners


def reject_reason(
    match_count: int,
    homography: np.ndarray | None,
    inlier_mask: np.ndarray | None,
    inlier_count: int,
    inlier_ratio: float,
    reprojection_error: float,
    coverage_x: float,
    coverage_y: float,
    corners_valid: bool,
    geometry_reasonable: bool,
    args: argparse.Namespace,
) -> str:
    if match_count < args.min_matches:
        return "not_enough_matches"
    if homography is None or inlier_mask is None:
        return "homography_failed"
    if inlier_count < args.min_inliers:
        return "not_enough_inliers"
    if inlier_ratio < args.min_inlier_ratio:
        return "low_inlier_ratio"
    if reprojection_error > args.max_reprojection_error:
        return "high_reprojection_error"
    if coverage_x < args.min_coverage_x:
        return "low_coverage_x"
    if coverage_y < args.min_coverage_y:
        return "low_coverage_y"
    if not corners_valid:
        return "invalid_corners"
    if not geometry_reasonable:
        return "large_geometry_step"
    return "ok"


def draw_match_debug(
    reference_bgr: np.ndarray,
    frame: np.ndarray,
    reference_points: np.ndarray,
    frame_points: np.ndarray,
    inlier_mask: np.ndarray,
    output: Path,
) -> None:
    inliers = inlier_mask.reshape(-1).astype(bool)
    sample_indices = np.flatnonzero(inliers)[:80]
    left = reference_bgr
    right = frame
    scale = left.shape[0] / right.shape[0]
    right_small = cv2.resize(right, (int(right.shape[1] * scale), left.shape[0]))
    canvas = np.concatenate([left, right_small], axis=1)
    x_offset = left.shape[1]
    for index in sample_indices:
        p0 = tuple(np.round(reference_points[index]).astype(int))
        p1 = frame_points[index].copy()
        p1 *= scale
        p1[0] += x_offset
        p1_tuple = tuple(np.round(p1).astype(int))
        cv2.circle(canvas, p0, 3, (0, 255, 0), -1)
        cv2.circle(canvas, p1_tuple, 3, (0, 255, 0), -1)
        cv2.line(canvas, p0, p1_tuple, (0, 180, 0), 1, cv2.LINE_AA)
    cv2.imwrite(str(output), canvas)


def summarize(rows: list[dict[str, object]]) -> dict[str, object]:
    accepted = [row for row in rows if row["accepted"]]
    summary: dict[str, object] = {
        "sampled_frames": len(rows),
        "accepted_frames": len(accepted),
        "accept_ratio": len(accepted) / max(1, len(rows)),
    }
    for key in (
        "match_count",
        "inlier_count",
        "inlier_ratio",
        "reprojection_error",
        "coverage_x",
        "coverage_y",
        "runtime_seconds",
    ):
        values = np.array(
            [float(row[key]) for row in rows if np.isfinite(float(row[key]))],
            dtype=np.float64,
        )
        if len(values) == 0:
            continue
        summary[f"{key}_median"] = float(np.median(values))
        summary[f"{key}_p05"] = float(np.percentile(values, 5))
        summary[f"{key}_p95"] = float(np.percentile(values, 95))

    reasons: dict[str, int] = {}
    for row in rows:
        reason = str(row["reason"])
        reasons[reason] = reasons.get(reason, 0) + 1
    summary["reasons"] = reasons
    return summary


def main() -> None:
    args = parse_args()
    source = args.input.resolve()
    run_dir = resolve_run_dir(args)

    capture = open_capture(source)
    frame_count = int(capture.get(cv2.CAP_PROP_FRAME_COUNT) or 0)
    fps = float(capture.get(cv2.CAP_PROP_FPS) or 0.0)
    ok, first_frame = capture.read()
    if not ok:
        raise SystemExit(f"video has no frames: {source}")

    first_corners = args.corners
    if first_corners is None:
        first_corners = detect_screen_corners(first_frame)
    if first_corners is None:
        first_corners = parse_corners(DEFAULT_FALLBACK_CORNERS)
    first_corners = order_corners(first_corners).astype(np.float32)

    reference_bgr, reference_corners = reference_canvas(
        first_frame,
        first_corners,
        args.reference_width,
        args.reference_height,
    )
    cv2.imwrite(str(run_dir / "reference_screen.png"), reference_bgr)

    learned = initialize_matcher(reference_bgr, args)
    rows: list[dict[str, object]] = []
    previous_accepted_corners = first_corners
    debug_written = 0

    sample_indices = list(range(0, frame_count or 1, args.sample_stride))
    if 0 not in sample_indices:
        sample_indices.insert(0, 0)
    sample_indices = sample_indices[: args.max_samples]

    for sample_number, frame_index in enumerate(sample_indices):
        capture.set(cv2.CAP_PROP_POS_FRAMES, frame_index)
        ok, frame = capture.read()
        if not ok:
            continue

        started = time.perf_counter()
        reference_points, frame_points, _matches = match_frame(learned, frame)
        runtime_seconds = time.perf_counter() - started
        match_count = len(reference_points)

        homography = None
        inlier_mask = None
        inlier_count = 0
        inlier_ratio = 0.0
        reprojection_error = float("inf")
        coverage_x = 0.0
        coverage_y = 0.0
        predicted_corners = previous_accepted_corners
        corners_valid = False
        geometry_reasonable = False

        if match_count >= 4:
            homography, inlier_mask = cv2.findHomography(
                reference_points,
                frame_points,
                cv2.RANSAC,
                args.ransac_threshold,
            )
        if homography is not None and inlier_mask is not None:
            inliers = inlier_mask.reshape(-1).astype(bool)
            inlier_count = int(inliers.sum())
            inlier_ratio = inlier_count / max(1, match_count)
            reprojection_error = homography_median_reprojection_error(
                reference_points,
                frame_points,
                homography,
                inlier_mask,
            )
            coverage_x, coverage_y = homography_inlier_screen_coverage(
                reference_points,
                inlier_mask,
                reference_corners,
            )
            predicted_corners = cv2.perspectiveTransform(
                reference_corners.reshape(1, 4, 2),
                homography,
            ).reshape(4, 2)
            predicted_corners = order_corners(predicted_corners).astype(np.float32)
            corners_valid = detected_corners_are_valid(predicted_corners, frame.shape)
            geometry_reasonable = geometry_update_is_reasonable(
                predicted_corners,
                previous_accepted_corners,
                max_scale_step=args.max_scale_step,
                max_area_step=args.max_area_step,
            )

        reason = reject_reason(
            match_count=match_count,
            homography=homography,
            inlier_mask=inlier_mask,
            inlier_count=inlier_count,
            inlier_ratio=inlier_ratio,
            reprojection_error=reprojection_error,
            coverage_x=coverage_x,
            coverage_y=coverage_y,
            corners_valid=corners_valid,
            geometry_reasonable=geometry_reasonable,
            args=args,
        )
        accepted = reason == "ok"
        if accepted:
            previous_accepted_corners = predicted_corners
            if args.write_match_debug and debug_written < args.debug_limit:
                draw_match_debug(
                    reference_bgr,
                    frame,
                    reference_points,
                    frame_points,
                    inlier_mask,
                    run_dir / f"matches_frame_{frame_index:05d}.jpg",
                )
                debug_written += 1

        center = predicted_corners.mean(axis=0)
        row: dict[str, object] = {
            "sample": sample_number,
            "frame": frame_index,
            "time_seconds": frame_index / fps if fps > 0 else 0.0,
            "accepted": accepted,
            "reason": reason,
            "match_count": match_count,
            "inlier_count": inlier_count,
            "inlier_ratio": inlier_ratio,
            "reprojection_error": reprojection_error,
            "coverage_x": coverage_x,
            "coverage_y": coverage_y,
            "runtime_seconds": runtime_seconds,
            "center_x": float(center[0]),
            "center_y": float(center[1]),
        }
        for index, label in enumerate(("tl", "tr", "br", "bl")):
            row[f"{label}_x"] = float(predicted_corners[index, 0])
            row[f"{label}_y"] = float(predicted_corners[index, 1])
        rows.append(row)

        print(
            f"frame {frame_index}: {reason}, matches={match_count}, "
            f"inliers={inlier_count}, reproj={reprojection_error:.3f}, "
            f"coverage=({coverage_x:.2f},{coverage_y:.2f}), "
            f"time={runtime_seconds:.2f}s"
        )
        sys.stdout.flush()

    capture.release()

    csv_path = run_dir / "learned_homography_probe.csv"
    if rows:
        with csv_path.open("w", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()))
            writer.writeheader()
            writer.writerows(rows)

    summary = summarize(rows)
    summary.update(
        {
            "input": str(source),
            "frame_count": frame_count,
            "fps": fps,
            "device": learned.device,
            "reference_width": args.reference_width,
            "reference_height": args.reference_height,
            "sample_stride": args.sample_stride,
            "max_samples": args.max_samples,
            "max_keypoints": args.max_keypoints,
        }
    )
    with (run_dir / "learned_homography_probe_summary.json").open("w") as handle:
        json.dump(summary, handle, indent=2)

    print(f"run directory: {run_dir}")
    print(f"wrote {csv_path}")
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
