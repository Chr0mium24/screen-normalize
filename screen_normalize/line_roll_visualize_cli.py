from __future__ import annotations

import argparse
import csv
import shutil
import subprocess
import sys
from datetime import datetime
from pathlib import Path

import cv2
import numpy as np

from .common import byte_int, create_run_directory, percentile_float, positive_int, project_root
from .line_roll_diagnostics import detect_lines, draw_overlay, line_roll_mask


def nonnegative_float(value: str) -> float:
    parsed = float(value)
    if parsed < 0:
        raise argparse.ArgumentTypeError("value must be >= 0")
    return parsed


def crop_fraction(value: str) -> float:
    parsed = float(value)
    if not 0.0 <= parsed < 0.5:
        raise argparse.ArgumentTypeError("value must be >= 0 and < 0.5")
    return parsed


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Draw line-roll detection diagnostics over a normalized video."
    )
    parser.add_argument("input", type=Path)
    parser.add_argument("output", type=Path, nargs="?")
    parser.add_argument("--runs-dir", type=Path, default=None)
    parser.add_argument("--run-name", default=None)
    parser.add_argument("--mask-top", type=crop_fraction, default=0.34)
    parser.add_argument("--mask-right", type=crop_fraction, default=0.30)
    parser.add_argument("--mask-bottom", type=crop_fraction, default=0.0)
    parser.add_argument("--ignore-top", type=crop_fraction, default=0.0)
    parser.add_argument(
        "--full-mask",
        action="store_true",
        help="Use the whole frame instead of the top/right/bottom diagnostic mask.",
    )
    parser.add_argument(
        "--detector",
        choices=("binary-contour", "hough", "contour"),
        default="binary-contour",
        help="Line detector used for the diagnostic overlay.",
    )
    parser.add_argument(
        "--view",
        choices=("overlay", "binary", "horizontal"),
        default="overlay",
        help="Render the normal overlay, the inverse binary foreground, or the final horizontal edge mask.",
    )
    parser.add_argument("--angle-limit-deg", type=nonnegative_float, default=3.0)
    parser.add_argument("--cluster-deg", type=nonnegative_float, default=0.35)
    parser.add_argument("--min-segments", type=positive_int, default=2)
    parser.add_argument("--min-total-length", type=positive_int, default=1000)
    parser.add_argument("--horizontal-kernel", type=positive_int, default=81)
    parser.add_argument("--max-line-thickness", type=positive_int, default=24)
    parser.add_argument("--white-threshold", type=byte_int, default=246)
    parser.add_argument("--background-percentile", type=percentile_float, default=75.0)
    parser.add_argument("--dark-margin", type=nonnegative_float, default=24.0)
    parser.add_argument("--saturation-threshold", type=byte_int, default=24)
    parser.add_argument("--max-frames", type=positive_int, default=None)
    parser.add_argument("--crf", type=positive_int, default=18)
    parser.add_argument("--preset", default="medium")
    return parser.parse_args()


def resolve_outputs(args: argparse.Namespace, source: Path) -> tuple[Path, Path, Path]:
    runs_dir = args.runs_dir.resolve() if args.runs_dir else project_root() / "runs"
    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    run_name = args.run_name or f"{timestamp}_visualize_line_roll"
    run_dir = create_run_directory(runs_dir, run_name)

    output_name = args.output.name if args.output else f"{source.stem}_line_roll_debug.mp4"
    if not Path(output_name).suffix:
        output_name = f"{output_name}.mp4"
    output_video = run_dir / output_name
    output_csv = run_dir / f"{Path(output_name).stem}.csv"
    return output_video.resolve(), output_csv.resolve(), run_dir.resolve()


def require_ffmpeg() -> None:
    if shutil.which("ffmpeg") is None:
        raise SystemExit("ffmpeg is required but was not found on PATH")


def main() -> None:
    args = parse_args()
    require_ffmpeg()
    source = args.input.resolve()
    capture = cv2.VideoCapture(str(source))
    if not capture.isOpened():
        raise SystemExit(f"could not open input video: {source}")

    fps = float(capture.get(cv2.CAP_PROP_FPS) or 60.0)
    if fps <= 0:
        fps = 60.0
    width = int(capture.get(cv2.CAP_PROP_FRAME_WIDTH) or 0)
    height = int(capture.get(cv2.CAP_PROP_FRAME_HEIGHT) or 0)
    frame_count = int(capture.get(cv2.CAP_PROP_FRAME_COUNT) or 0)
    if width <= 0 or height <= 0:
        raise SystemExit("input video has invalid dimensions")

    output_video, output_csv, run_dir = resolve_outputs(args, source)
    if args.full_mask:
        mask = np.full((height, width), 255, dtype=np.uint8)
        if args.ignore_top:
            mask[: int(round(height * args.ignore_top)), :] = 0
    else:
        mask = line_roll_mask(
            (height, width),
            args.mask_top,
            args.mask_right,
            args.mask_bottom,
            args.ignore_top,
        )

    command = [
        "ffmpeg",
        "-y",
        "-loglevel",
        "error",
        "-f",
        "rawvideo",
        "-vcodec",
        "rawvideo",
        "-pix_fmt",
        "bgr24",
        "-s",
        f"{width}x{height}",
        "-r",
        f"{fps:.6f}",
        "-i",
        "-",
        "-an",
        "-c:v",
        "libx264",
        "-preset",
        args.preset,
        "-crf",
        str(args.crf),
        "-pix_fmt",
        "yuv420p",
        str(output_video),
    ]
    process = subprocess.Popen(command, stdin=subprocess.PIPE)
    if process.stdin is None:
        raise RuntimeError("failed to open ffmpeg stdin")

    rows = []
    processed = 0
    try:
        while True:
            ok, frame = capture.read()
            if not ok:
                break
            detection = detect_lines(
                frame,
                mask,
                detector=args.detector,
                angle_limit=args.angle_limit_deg,
                cluster_deg=args.cluster_deg,
                min_segments=args.min_segments,
                min_total_length=args.min_total_length,
                horizontal_kernel=args.horizontal_kernel,
                max_line_thickness=args.max_line_thickness,
                white_threshold=args.white_threshold,
                background_percentile=args.background_percentile,
                dark_margin=args.dark_margin,
                saturation_threshold=args.saturation_threshold,
            )
            overlay = draw_overlay(
                frame,
                mask,
                detection,
                processed,
                detector=args.detector,
                view=args.view,
            )
            process.stdin.write(overlay.tobytes())
            rows.append(
                {
                    "frame": processed,
                    "raw_candidates": len(detection["candidates"]),
                    "same_direction_inliers": len(detection["inliers"]),
                    "dominant_angle_deg": detection["dominant_angle"],
                    "accepted_angle_deg": detection["accepted_angle"],
                    "total_inlier_length_px": detection["total_length"],
                    "accepted": detection["accepted"],
                }
            )
            processed += 1
            if args.max_frames and processed >= args.max_frames:
                break
            if frame_count and (processed % 60 == 0 or processed == frame_count):
                print(f"processed {processed}/{frame_count} frames", file=sys.stderr)
    finally:
        process.stdin.close()
        capture.release()

    return_code = process.wait()
    if return_code != 0:
        raise SystemExit(f"ffmpeg encode failed with exit code {return_code}")

    with output_csv.open("w", newline="") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=[
                "frame",
                "raw_candidates",
                "same_direction_inliers",
                "dominant_angle_deg",
                "accepted_angle_deg",
                "total_inlier_length_px",
                "accepted",
            ],
        )
        writer.writeheader()
        writer.writerows(rows)

    accepted_angles = [
        float(row["accepted_angle_deg"]) for row in rows if row["accepted_angle_deg"] is not None
    ]
    print(f"run directory: {run_dir}")
    print(f"wrote {output_video} from {processed} frames")
    print(f"wrote {output_csv}")
    if accepted_angles:
        print(
            "accepted angle summary: "
            f"mean={np.mean(accepted_angles):.4f} deg, "
            f"std={np.std(accepted_angles):.4f} deg, "
            f"p95_abs={np.percentile(np.abs(accepted_angles), 95):.4f} deg"
        )
