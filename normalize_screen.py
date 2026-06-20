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


DEFAULT_FALLBACK_CORNERS = "124,116:1488,132:1516,850:145,934"


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


def smoothing_weight(value: str) -> float:
    parsed = float(value)
    if not 0.0 <= parsed < 1.0:
        raise argparse.ArgumentTypeError("value must be >= 0 and < 1")
    return parsed


def crop_fraction(value: str) -> float:
    parsed = float(value)
    if not 0.0 <= parsed < 0.4:
        raise argparse.ArgumentTypeError("value must be >= 0 and < 0.4")
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
        default=None,
        help=(
            "Manual source screen corners in TL,TR,BR,BL order, formatted as "
            "x,y:x,y:x,y:x,y. If omitted, corners are detected per frame."
        ),
    )
    parser.add_argument(
        "--smooth",
        type=smoothing_weight,
        default=0.0,
        help="Previous-frame corner smoothing weight for auto detection.",
    )
    parser.add_argument("--width", type=positive_int, default=1920)
    parser.add_argument("--height", type=positive_int, default=1080)
    parser.add_argument("--fps", type=float, default=None)
    parser.add_argument("--crf", type=positive_int, default=18)
    parser.add_argument("--preset", default="medium")
    parser.add_argument("--crop-left", type=crop_fraction, default=0.0)
    parser.add_argument("--crop-top", type=crop_fraction, default=0.0)
    parser.add_argument("--crop-right", type=crop_fraction, default=0.0)
    parser.add_argument("--crop-bottom", type=crop_fraction, default=0.0)
    return parser.parse_args()


def require_ffmpeg() -> None:
    if shutil.which("ffmpeg") is None:
        raise SystemExit("ffmpeg is required but was not found on PATH")


def open_capture(path: Path) -> cv2.VideoCapture:
    capture = cv2.VideoCapture(str(path))
    if not capture.isOpened():
        raise SystemExit(f"could not open input video: {path}")
    return capture


def order_corners(points: np.ndarray) -> np.ndarray:
    points = np.asarray(points, dtype=np.float32).reshape(-1, 2)
    sums = points.sum(axis=1)
    diffs = np.diff(points, axis=1).reshape(-1)
    return np.array(
        [
            points[np.argmin(sums)],
            points[np.argmin(diffs)],
            points[np.argmax(sums)],
            points[np.argmax(diffs)],
        ],
        dtype=np.float32,
    )


def detected_corners_are_valid(corners: np.ndarray, frame_shape: tuple[int, ...]) -> bool:
    height, width = frame_shape[:2]
    area = abs(cv2.contourArea(corners))
    frame_area = float(width * height)
    if not frame_area * 0.20 <= area <= frame_area * 0.85:
        return False

    top = np.linalg.norm(corners[1] - corners[0])
    bottom = np.linalg.norm(corners[2] - corners[3])
    left = np.linalg.norm(corners[3] - corners[0])
    right = np.linalg.norm(corners[2] - corners[1])
    avg_width = (top + bottom) / 2.0
    avg_height = (left + right) / 2.0
    if avg_height <= 0:
        return False

    projected_aspect = avg_width / avg_height
    return 1.25 <= projected_aspect <= 2.35


def detect_screen_corners(frame: np.ndarray) -> np.ndarray | None:
    hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
    mask = cv2.inRange(hsv, (85, 20, 50), (130, 255, 255))
    mask = cv2.morphologyEx(
        mask,
        cv2.MORPH_CLOSE,
        cv2.getStructuringElement(cv2.MORPH_RECT, (25, 25)),
        iterations=2,
    )
    mask = cv2.morphologyEx(
        mask,
        cv2.MORPH_OPEN,
        cv2.getStructuringElement(cv2.MORPH_RECT, (5, 5)),
        iterations=1,
    )

    contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    if not contours:
        return None

    contour = max(contours, key=cv2.contourArea)
    frame_area = frame.shape[0] * frame.shape[1]
    if cv2.contourArea(contour) < frame_area * 0.20:
        return None

    perimeter = cv2.arcLength(contour, True)
    for epsilon_fraction in (0.010, 0.012, 0.015, 0.018, 0.020, 0.025, 0.030, 0.040):
        approximate = cv2.approxPolyDP(contour, epsilon_fraction * perimeter, True)
        if len(approximate) != 4:
            continue

        corners = order_corners(approximate.reshape(-1, 2))
        if detected_corners_are_valid(corners, frame.shape):
            return corners

    return None


def encode_warped_video(
    capture: cv2.VideoCapture,
    output: Path,
    fallback_corners: np.ndarray,
    width: int,
    height: int,
    fps: float,
    crf: int,
    preset: str,
    smooth: float,
    auto_detect: bool,
    crop_left: float,
    crop_top: float,
    crop_right: float,
    crop_bottom: float,
) -> int:
    destination_corners = np.array(
        [[0, 0], [width - 1, 0], [width - 1, height - 1], [0, height - 1]],
        dtype=np.float32,
    )
    frame_count = int(capture.get(cv2.CAP_PROP_FRAME_COUNT) or 0)
    last_corners: np.ndarray | None = None
    fallback_transform = cv2.getPerspectiveTransform(fallback_corners, destination_corners)

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
            if auto_detect:
                detected_corners = detect_screen_corners(frame)
                if detected_corners is None:
                    source_corners = last_corners if last_corners is not None else fallback_corners
                elif last_corners is None:
                    source_corners = detected_corners
                else:
                    source_corners = (last_corners * smooth) + (detected_corners * (1.0 - smooth))
                last_corners = source_corners
                transform = cv2.getPerspectiveTransform(source_corners, destination_corners)
            else:
                transform = fallback_transform

            warped = cv2.warpPerspective(
                frame,
                transform,
                (width, height),
                flags=cv2.INTER_CUBIC,
                borderMode=cv2.BORDER_REPLICATE,
            )
            if crop_left or crop_top or crop_right or crop_bottom:
                x1 = int(round(width * crop_left))
                y1 = int(round(height * crop_top))
                x2 = int(round(width * (1.0 - crop_right)))
                y2 = int(round(height * (1.0 - crop_bottom)))
                if x1 >= x2 or y1 >= y2:
                    raise SystemExit("crop values leave no output area")
                warped = cv2.resize(
                    warped[y1:y2, x1:x2],
                    (width, height),
                    interpolation=cv2.INTER_CUBIC,
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

    fallback_corners = args.corners
    auto_detect = fallback_corners is None
    if fallback_corners is None:
        fallback_corners = parse_corners(DEFAULT_FALLBACK_CORNERS)

    with tempfile.TemporaryDirectory() as tmp:
        silent_video = Path(tmp) / "screen_normalized_silent.mp4"
        processed = encode_warped_video(
            capture=capture,
            output=silent_video,
            fallback_corners=fallback_corners,
            width=args.width,
            height=args.height,
            fps=fps,
            crf=args.crf,
            preset=args.preset,
            smooth=args.smooth,
            auto_detect=auto_detect,
            crop_left=args.crop_left,
            crop_top=args.crop_top,
            crop_right=args.crop_right,
            crop_bottom=args.crop_bottom,
        )
        mux_audio(silent_video, source, output)

    print(f"wrote {output} from {processed} frames")


if __name__ == "__main__":
    main()
