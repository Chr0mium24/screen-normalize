#!/usr/bin/env python3
# /// script
# dependencies = [
#   "numpy>=2.2.0",
#   "opencv-python-headless>=4.12.0.88",
# ]
# ///

from __future__ import annotations

import argparse
import csv
import json
from datetime import datetime
from pathlib import Path

import cv2
import numpy as np


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


def project_root() -> Path:
    script_path = Path(__file__).resolve()
    for path in (script_path.parent, *script_path.parents):
        if (path / ".git").exists():
            return path
    if script_path.parent.name == "scripts":
        return script_path.parent.parent
    return Path.cwd()


def clean_path_component(value: str) -> str:
    cleaned = "".join(
        character if character.isalnum() or character in ("-", "_", ".") else "_"
        for character in value
    ).strip("._-")
    return cleaned or "run"


def create_run_directory(runs_dir: Path, run_name: str) -> Path:
    runs_dir.mkdir(parents=True, exist_ok=True)
    clean_name = clean_path_component(run_name)
    for index in range(1000):
        suffix = "" if index == 0 else f"_{index:02d}"
        candidate = runs_dir / f"{clean_name}{suffix}"
        try:
            candidate.mkdir()
        except FileExistsError:
            continue
        return candidate
    raise RuntimeError(f"could not create unique run directory under {runs_dir}")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Estimate residual adjacent-frame affine motion in normalized screen videos."
        )
    )
    parser.add_argument("videos", type=Path, nargs="+")
    parser.add_argument("--runs-dir", type=Path, default=None)
    parser.add_argument("--run-name", default=None)
    parser.add_argument(
        "--last-seconds",
        type=nonnegative_float,
        default=2.0,
        help="Also summarize frames whose timestamp is within this many seconds of the end.",
    )
    parser.add_argument("--max-corners", type=positive_int, default=800)
    parser.add_argument("--quality-level", type=float, default=0.01)
    parser.add_argument("--min-distance", type=positive_int, default=10)
    parser.add_argument("--min-points", type=positive_int, default=30)
    parser.add_argument("--ransac-threshold", type=nonnegative_float, default=2.0)
    return parser.parse_args()


def resolve_run_dir(args: argparse.Namespace) -> Path:
    runs_dir = args.runs_dir.resolve() if args.runs_dir else project_root() / "runs"
    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    run_name = args.run_name or f"{timestamp}_{Path(__file__).stem}"
    return create_run_directory(runs_dir, run_name).resolve()


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
    args: argparse.Namespace,
) -> dict[str, float | int | bool | str]:
    height, width = previous_gray.shape[:2]
    points = cv2.goodFeaturesToTrack(
        previous_gray,
        maxCorners=args.max_corners,
        qualityLevel=args.quality_level,
        minDistance=args.min_distance,
        blockSize=7,
    )
    if points is None or len(points) < args.min_points:
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
    if len(previous_good) < args.min_points:
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
        ransacReprojThreshold=args.ransac_threshold,
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
    inlier_coverage_x, inlier_coverage_y = normalized_coverage(
        previous_good[inliers],
        width,
        height,
    )
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
        "inlier_coverage_x": inlier_coverage_x,
        "inlier_coverage_y": inlier_coverage_y,
        "translation_x_px": dx,
        "translation_y_px": dy,
        "translation_px": float(np.hypot(dx, dy)),
        "rotation_deg": rotation_deg,
        "scale": scale,
        "scale_delta": float(scale - 1.0),
    }


def analyze_video(video: Path, args: argparse.Namespace) -> tuple[list[dict[str, object]], dict[str, object]]:
    capture = cv2.VideoCapture(str(video))
    if not capture.isOpened():
        raise SystemExit(f"could not open video: {video}")

    fps = float(capture.get(cv2.CAP_PROP_FPS) or 0.0)
    if fps <= 0:
        fps = 60.0
    frame_count = int(capture.get(cv2.CAP_PROP_FRAME_COUNT) or 0)
    width = int(capture.get(cv2.CAP_PROP_FRAME_WIDTH) or 0)
    height = int(capture.get(cv2.CAP_PROP_FRAME_HEIGHT) or 0)

    ok, previous = capture.read()
    if not ok:
        raise SystemExit(f"video has no frames: {video}")
    previous_gray = cv2.cvtColor(previous, cv2.COLOR_BGR2GRAY)

    rows: list[dict[str, object]] = []
    frame_index = 1
    while True:
        ok, frame = capture.read()
        if not ok:
            break
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        motion = estimate_pair_motion(previous_gray, gray, args)
        row: dict[str, object] = {
            "video": str(video),
            "frame": frame_index,
            "time_seconds": frame_index / fps,
        }
        row.update(motion)
        rows.append(row)
        previous_gray = gray
        frame_index += 1

    capture.release()
    metadata = {
        "path": str(video),
        "width": width,
        "height": height,
        "fps": fps,
        "frame_count": frame_count or frame_index,
        "measured_pairs": len(rows),
        "duration_seconds": (frame_count / fps) if frame_count else (frame_index / fps),
    }
    return rows, metadata


def finite_values(rows: list[dict[str, object]], key: str) -> np.ndarray:
    values = []
    for row in rows:
        if not row.get("ok"):
            continue
        value = row.get(key)
        if isinstance(value, int | float) and np.isfinite(value):
            values.append(float(value))
    return np.asarray(values, dtype=np.float64)


def summarize_rows(rows: list[dict[str, object]]) -> dict[str, float | int | None]:
    ok_rows = [row for row in rows if row.get("ok")]
    summary: dict[str, float | int | None] = {
        "pairs": len(rows),
        "ok_pairs": len(ok_rows),
    }
    metrics = {
        "translation_px": "translation",
        "rotation_abs_deg": "rotation_abs",
        "scale_abs_delta": "scale_abs_delta",
        "inlier_ratio": "inlier_ratio",
        "inlier_coverage_x": "inlier_coverage_x",
        "inlier_coverage_y": "inlier_coverage_y",
    }
    for source, prefix in metrics.items():
        if source == "rotation_abs_deg":
            values = np.abs(finite_values(rows, "rotation_deg"))
        elif source == "scale_abs_delta":
            values = np.abs(finite_values(rows, "scale_delta"))
        else:
            values = finite_values(rows, source)

        if values.size == 0:
            summary[f"{prefix}_mean"] = None
            summary[f"{prefix}_p95"] = None
            summary[f"{prefix}_max"] = None
            continue
        summary[f"{prefix}_mean"] = float(np.mean(values))
        summary[f"{prefix}_p95"] = float(np.percentile(values, 95))
        summary[f"{prefix}_max"] = float(np.max(values))
    return summary


def summarize_video(
    rows: list[dict[str, object]],
    metadata: dict[str, object],
    last_seconds: float,
) -> dict[str, object]:
    duration = float(metadata["duration_seconds"])
    last_start = max(0.0, duration - last_seconds)
    last_rows = [row for row in rows if float(row["time_seconds"]) >= last_start]
    return {
        "video": metadata,
        "all": summarize_rows(rows),
        "last_seconds": {
            "seconds": last_seconds,
            "start_time_seconds": last_start,
            **summarize_rows(last_rows),
        },
    }


def write_csv(path: Path, rows: list[dict[str, object]]) -> None:
    fieldnames = [
        "video",
        "frame",
        "time_seconds",
        "ok",
        "reason",
        "feature_count",
        "tracked_count",
        "inlier_count",
        "inlier_ratio",
        "inlier_coverage_x",
        "inlier_coverage_y",
        "translation_x_px",
        "translation_y_px",
        "translation_px",
        "rotation_deg",
        "scale",
        "scale_delta",
    ]
    with path.open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def main() -> None:
    args = parse_args()
    run_dir = resolve_run_dir(args)

    all_rows: list[dict[str, object]] = []
    summaries = []
    for video in args.videos:
        rows, metadata = analyze_video(video.resolve(), args)
        all_rows.extend(rows)
        summaries.append(summarize_video(rows, metadata, args.last_seconds))

    csv_path = run_dir / "stability_metrics.csv"
    json_path = run_dir / "stability_summary.json"
    write_csv(csv_path, all_rows)
    with json_path.open("w") as handle:
        json.dump(
            {
                "generated_at": datetime.now().isoformat(timespec="seconds"),
                "summary": summaries,
            },
            handle,
            indent=2,
        )
        handle.write("\n")

    print(f"run directory: {run_dir}")
    print(f"wrote {csv_path}")
    print(f"wrote {json_path}")
    for summary in summaries:
        video = summary["video"]["path"]
        last = summary["last_seconds"]
        print(
            f"{video}: last {last['seconds']:.1f}s "
            f"translation_p95={last['translation_p95']:.3f}px, "
            f"rotation_p95={last['rotation_abs_p95']:.4f}deg, "
            f"scale_delta_p95={last['scale_abs_delta_p95']:.6f}"
        )


if __name__ == "__main__":
    main()
