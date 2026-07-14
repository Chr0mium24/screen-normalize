from __future__ import annotations

import argparse
import json
from pathlib import Path

import cv2
import numpy as np

from screen_normalize.algorithms.proposal_demo import (
    ProposalDemoConfig,
    estimate_proposal_border_trajectory,
    write_corner_trajectory_csv,
    write_proposal_debug_csv,
)
from screen_normalize.algorithms.trajectory import smooth_corner_trajectory
from screen_normalize.common import (
    nonnegative_fraction,
    open_capture,
    parse_corners,
    positive_int,
    resolve_run_output,
)
from screen_normalize.experiments.annotations import load_annotations


def parse_radii(value: str) -> tuple[int, ...]:
    radii = tuple(int(item) for item in value.split(",") if item.strip())
    if not radii or any(radius <= 0 for radius in radii):
        raise argparse.ArgumentTypeError("search radii must be positive integers")
    return radii


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Small proposal-method demo: border-guided homography with LK consistency checks."
    )
    parser.add_argument("input", type=Path)
    parser.add_argument("output", type=Path, nargs="?")
    parser.add_argument("--runs-dir", type=Path, default=None)
    parser.add_argument("--run-name", default=None)
    parser.add_argument("--corners", type=parse_corners, default=None)
    parser.add_argument(
        "--annotations",
        type=Path,
        default=None,
        help="Optional corner annotation CSV; frame 0 is used for initialization.",
    )
    parser.add_argument("--width", type=positive_int, default=1920)
    parser.add_argument("--height", type=positive_int, default=1080)
    parser.add_argument("--fps", type=float, default=None)
    parser.add_argument("--max-frames", type=int, default=0)
    parser.add_argument("--sample-count", type=positive_int, default=50)
    parser.add_argument("--search-radii", type=parse_radii, default=(20, 60, 120))
    parser.add_argument("--min-edge-confidence", type=nonnegative_fraction, default=0.35)
    parser.add_argument("--max-scale-step", type=nonnegative_fraction, default=0.10)
    parser.add_argument("--max-area-step", type=nonnegative_fraction, default=0.20)
    parser.add_argument("--min-lk-inliers", type=positive_int, default=24)
    parser.add_argument("--min-lk-inlier-ratio", type=nonnegative_fraction, default=0.25)
    parser.add_argument("--max-lk-disagreement", type=nonnegative_fraction, default=24.0)
    parser.add_argument("--median-window", type=positive_int, default=5)
    parser.add_argument("--trajectory-window", type=positive_int, default=9)
    parser.add_argument(
        "--no-overlay",
        action="store_true",
        help="Skip writing the source-frame overlay diagnostic video.",
    )
    return parser.parse_args()


def initial_corners_from_args(
    source: Path,
    args: argparse.Namespace,
    width: int,
    height: int,
) -> np.ndarray | None:
    if args.corners is not None:
        return args.corners
    annotation_path = args.annotations or source.with_suffix(".csv")
    if annotation_path.exists():
        annotations = load_annotations(annotation_path, width, height)
        if 0 in annotations:
            return annotations[0]
    return None


def open_writer(path: Path, fps: float, size: tuple[int, int]) -> cv2.VideoWriter:
    path.parent.mkdir(parents=True, exist_ok=True)
    writer = cv2.VideoWriter(str(path), cv2.VideoWriter_fourcc(*"mp4v"), fps, size)
    if not writer.isOpened():
        raise SystemExit(f"could not open video writer: {path}")
    return writer


def render_normalized_video(
    source: Path,
    output: Path,
    trajectory: list[np.ndarray],
    width: int,
    height: int,
    fps: float,
) -> int:
    capture = open_capture(source)
    writer = open_writer(output, fps, (width, height))
    destination = np.array(
        [[0, 0], [width - 1, 0], [width - 1, height - 1], [0, height - 1]],
        dtype=np.float32,
    )
    written = 0
    try:
        for corners in trajectory:
            ok, frame = capture.read()
            if not ok:
                break
            transform = cv2.getPerspectiveTransform(corners.astype(np.float32), destination)
            warped = cv2.warpPerspective(
                frame,
                transform,
                (width, height),
                flags=cv2.INTER_CUBIC,
                borderMode=cv2.BORDER_REPLICATE,
            )
            writer.write(warped)
            written += 1
    finally:
        capture.release()
        writer.release()
    return written


def render_overlay_video(
    source: Path,
    output: Path,
    trajectory: list[np.ndarray],
    debug_rows: list[dict[str, object]],
    fps: float,
) -> int:
    capture = open_capture(source)
    frame_width = int(capture.get(cv2.CAP_PROP_FRAME_WIDTH) or 0)
    frame_height = int(capture.get(cv2.CAP_PROP_FRAME_HEIGHT) or 0)
    writer = open_writer(output, fps, (frame_width, frame_height))
    written = 0
    try:
        for corners, row in zip(trajectory, debug_rows, strict=False):
            ok, frame = capture.read()
            if not ok:
                break
            canvas = frame.copy()
            color = (0, 220, 0) if row.get("accepted") else (0, 170, 255)
            cv2.polylines(canvas, [np.round(corners).astype(np.int32)], True, color, 4)
            label = f"frame {row.get('frame')}  {row.get('reason')}"
            cv2.putText(
                canvas,
                label,
                (24, 42),
                cv2.FONT_HERSHEY_SIMPLEX,
                1.0,
                (255, 255, 255),
                3,
                cv2.LINE_AA,
            )
            cv2.putText(
                canvas,
                label,
                (24, 42),
                cv2.FONT_HERSHEY_SIMPLEX,
                1.0,
                (30, 30, 30),
                1,
                cv2.LINE_AA,
            )
            writer.write(canvas)
            written += 1
    finally:
        capture.release()
        writer.release()
    return written


def write_summary(path: Path, rows: list[dict[str, object]], frame_count: int) -> None:
    accepted_frames = sum(1 for row in rows if row.get("accepted"))
    accepted_updates = sum(
        1 for row in rows if row.get("accepted") and int(row.get("frame", -1)) > 0
    )
    reasons: dict[str, int] = {}
    for row in rows:
        reason = str(row.get("reason", "unknown"))
        reasons[reason] = reasons.get(reason, 0) + 1
    summary = {
        "frames": frame_count,
        "accepted_frames": accepted_frames,
        "accepted_updates_after_initialization": accepted_updates,
        "held_frames": frame_count - accepted_frames,
        "accept_ratio": accepted_frames / max(1, frame_count),
        "reasons": reasons,
    }
    path.write_text(json.dumps(summary, indent=2), encoding="utf-8")


def main() -> None:
    args = parse_args()
    source = args.input.resolve()
    capture = open_capture(source)
    source_width = int(capture.get(cv2.CAP_PROP_FRAME_WIDTH) or 0)
    source_height = int(capture.get(cv2.CAP_PROP_FRAME_HEIGHT) or 0)
    fps = args.fps or float(capture.get(cv2.CAP_PROP_FPS) or 30.0)
    if fps <= 0:
        fps = 30.0
    initial = initial_corners_from_args(source, args, source_width, source_height)

    config = ProposalDemoConfig(
        sample_count=args.sample_count,
        search_radii=args.search_radii,
        min_edge_confidence=args.min_edge_confidence,
        max_scale_step=args.max_scale_step,
        max_area_step=args.max_area_step,
        min_lk_inliers=args.min_lk_inliers,
        min_lk_inlier_ratio=args.min_lk_inlier_ratio,
        max_lk_disagreement=args.max_lk_disagreement,
        max_frames=args.max_frames,
    )
    rows: list[dict[str, object]] = []
    raw_trajectory = estimate_proposal_border_trajectory(
        capture,
        initial_corners=initial,
        config=config,
        debug_rows=rows,
    )
    capture.release()

    trajectory = smooth_corner_trajectory(
        raw_trajectory,
        median_window=args.median_window,
        average_window=args.trajectory_window,
    )
    output, run_dir = resolve_run_output(args, source, script_name="proposal_demo")
    normalized_frames = render_normalized_video(
        source,
        output,
        trajectory,
        width=args.width,
        height=args.height,
        fps=fps,
    )
    if not args.no_overlay:
        render_overlay_video(source, run_dir / "proposal_overlay.mp4", raw_trajectory, rows, fps)
    write_proposal_debug_csv(run_dir / "proposal_debug.csv", rows)
    write_corner_trajectory_csv(run_dir / "raw_corners.csv", raw_trajectory)
    write_corner_trajectory_csv(run_dir / "smoothed_corners.csv", trajectory)
    write_summary(run_dir / "summary.json", rows, normalized_frames)

    print(f"run directory: {run_dir}")
    print(f"wrote {output} from {normalized_frames} frames")
    if not args.no_overlay:
        print(f"wrote {run_dir / 'proposal_overlay.mp4'}")
    print(f"wrote {run_dir / 'proposal_debug.csv'}")


if __name__ == "__main__":
    main()
