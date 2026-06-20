#!/usr/bin/env python3
# /// script
# dependencies = [
#   "numpy>=2.2.0",
#   "opencv-python-headless>=4.12.0.88",
# ]
# ///

from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

import cv2
import numpy as np


DEFAULT_CORNERS = "124,116:1488,132:1516,850:145,934"


def parse_corners(value: str) -> np.ndarray:
    points = []
    for raw_point in value.split(":"):
        coords = raw_point.split(",")
        if len(coords) != 2:
            raise argparse.ArgumentTypeError(
                "corners must be x,y:x,y:x,y:x,y in TL,TR,BR,BL order"
            )
        try:
            points.append([float(coords[0]), float(coords[1])])
        except ValueError as exc:
            raise argparse.ArgumentTypeError("corner coordinates must be numeric") from exc

    if len(points) != 4:
        raise argparse.ArgumentTypeError("exactly four corners are required")

    return np.array(points, dtype=np.float32)


def positive_int(value: str) -> int:
    parsed = int(value)
    if parsed <= 0:
        raise argparse.ArgumentTypeError("value must be positive")
    return parsed


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Perspective-correct a filmed monitor into a screen-recording-like video."
    )
    parser.add_argument("input", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument(
        "--corners",
        type=parse_corners,
        default=parse_corners(DEFAULT_CORNERS),
        help=(
            "Source screen corners in TL,TR,BR,BL order, formatted as "
            "x,y:x,y:x,y:x,y. Defaults are tuned for VID20260621024117.mp4."
        ),
    )
    parser.add_argument("--width", type=positive_int, default=1920)
    parser.add_argument("--height", type=positive_int, default=1080)
    parser.add_argument("--fps", type=float, default=None)
    parser.add_argument("--crf", type=positive_int, default=18)
    parser.add_argument("--preset", default="medium")
    return parser.parse_args()


def require_ffmpeg() -> None:
    if shutil.which("ffmpeg") is None:
        raise SystemExit("ffmpeg is required but was not found on PATH")


def open_capture(path: Path) -> cv2.VideoCapture:
    capture = cv2.VideoCapture(str(path))
    if not capture.isOpened():
        raise SystemExit(f"could not open input video: {path}")
    return capture


def encode_warped_video(
    capture: cv2.VideoCapture,
    output: Path,
    source_corners: np.ndarray,
    width: int,
    height: int,
    fps: float,
    crf: int,
    preset: str,
) -> int:
    destination_corners = np.array(
        [[0, 0], [width - 1, 0], [width - 1, height - 1], [0, height - 1]],
        dtype=np.float32,
    )
    transform = cv2.getPerspectiveTransform(source_corners, destination_corners)
    frame_count = int(capture.get(cv2.CAP_PROP_FRAME_COUNT) or 0)

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
        preset,
        "-crf",
        str(crf),
        "-pix_fmt",
        "yuv420p",
        str(output),
    ]
    process = subprocess.Popen(command, stdin=subprocess.PIPE)
    if process.stdin is None:
        raise RuntimeError("failed to open ffmpeg stdin")

    processed = 0
    try:
        while True:
            ok, frame = capture.read()
            if not ok:
                break
            warped = cv2.warpPerspective(
                frame,
                transform,
                (width, height),
                flags=cv2.INTER_CUBIC,
                borderMode=cv2.BORDER_REPLICATE,
            )
            process.stdin.write(warped.tobytes())
            processed += 1
            if frame_count and (processed % 60 == 0 or processed == frame_count):
                print(f"processed {processed}/{frame_count} frames", file=sys.stderr)
    finally:
        process.stdin.close()
        capture.release()

    return_code = process.wait()
    if return_code != 0:
        raise SystemExit(f"ffmpeg encode failed with exit code {return_code}")
    return processed


def mux_audio(video_without_audio: Path, source: Path, output: Path) -> None:
    command = [
        "ffmpeg",
        "-y",
        "-loglevel",
        "error",
        "-i",
        str(video_without_audio),
        "-i",
        str(source),
        "-map",
        "0:v:0",
        "-map",
        "1:a?",
        "-c:v",
        "copy",
        "-c:a",
        "copy",
        "-shortest",
        str(output),
    ]
    subprocess.run(command, check=True)


def main() -> None:
    args = parse_args()
    require_ffmpeg()

    source = args.input.resolve()
    output = args.output.resolve()
    if source == output:
        raise SystemExit("input and output must be different files")
    output.parent.mkdir(parents=True, exist_ok=True)

    capture = open_capture(source)
    fps = args.fps or float(capture.get(cv2.CAP_PROP_FPS) or 60.0)
    if fps <= 0:
        fps = 60.0

    with tempfile.TemporaryDirectory() as tmp:
        silent_video = Path(tmp) / "screen_normalized_silent.mp4"
        processed = encode_warped_video(
            capture=capture,
            output=silent_video,
            source_corners=args.corners,
            width=args.width,
            height=args.height,
            fps=fps,
            crf=args.crf,
            preset=args.preset,
        )
        mux_audio(silent_video, source, output)

    print(f"wrote {output} from {processed} frames")


if __name__ == "__main__":
    main()
