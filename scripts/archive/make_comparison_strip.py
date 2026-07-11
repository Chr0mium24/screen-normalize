#!/usr/bin/env python3
# /// script
# dependencies = [
#   "numpy>=2.2.0",
#   "opencv-python-headless>=4.12.0.88",
# ]
# ///

from __future__ import annotations

import argparse
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

import cv2
import numpy as np


@dataclass(frozen=True)
class VideoMetadata:
    path: Path
    width: int
    height: int
    fps: float
    frame_count: int

    @property
    def duration_seconds(self) -> float:
        if self.frame_count <= 0 or self.fps <= 0:
            return 0.0
        return self.frame_count / self.fps


def positive_int(value: str) -> int:
    parsed = int(value)
    if parsed <= 0:
        raise argparse.ArgumentTypeError("value must be positive")
    return parsed


def nonnegative_int(value: str) -> int:
    parsed = int(value)
    if parsed < 0:
        raise argparse.ArgumentTypeError("value must be >= 0")
    return parsed


def parse_frames(value: str) -> list[int]:
    frames: list[int] = []
    for raw in value.split(","):
        raw = raw.strip()
        if not raw:
            continue
        try:
            frame = int(raw)
        except ValueError as exc:
            raise argparse.ArgumentTypeError("frames must be comma-separated integers") from exc
        if frame < 0:
            raise argparse.ArgumentTypeError("frame indices must be >= 0")
        frames.append(frame)
    if not frames:
        raise argparse.ArgumentTypeError("at least one frame index is required")
    return frames


def parse_points(value: str) -> list[tuple[float, float]]:
    points: list[tuple[float, float]] = []
    for raw_point in value.split(":"):
        coords = raw_point.split(",")
        if len(coords) != 2:
            raise argparse.ArgumentTypeError("points must be x,y:x,y[:x,y...]")
        try:
            points.append((float(coords[0]), float(coords[1])))
        except ValueError as exc:
            raise argparse.ArgumentTypeError("point coordinates must be numeric") from exc
    if not points:
        raise argparse.ArgumentTypeError("at least one point is required")
    return points


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
            "Sample frames from an original video and a normalized video, then "
            "write a two-row horizontal comparison strip."
        )
    )
    parser.add_argument("original", type=Path, help="Raw filmed-screen video.")
    parser.add_argument("normalized", type=Path, help="Corrected/normalized output video.")
    parser.add_argument(
        "--frames",
        type=parse_frames,
        default=None,
        help="Comma-separated original-video frame indices, for example 0,30,60,90.",
    )
    parser.add_argument(
        "--count",
        type=positive_int,
        default=8,
        help="Number of evenly spaced frames when --frames is not provided.",
    )
    parser.add_argument(
        "--points",
        type=parse_points,
        default=None,
        help=(
            "Optional manually selected points in original-frame coordinates, "
            "formatted as x,y:x,y[:x,y...]. Four points are drawn as a closed quadrilateral."
        ),
    )
    parser.add_argument(
        "--thumb-width",
        type=positive_int,
        default=320,
        help="Width of each sampled frame tile in the output image.",
    )
    parser.add_argument(
        "--label-height",
        type=nonnegative_int,
        default=28,
        help="Top label band height for each tile. Use 0 to disable frame labels.",
    )
    parser.add_argument(
        "--runs-dir",
        type=Path,
        default=None,
        help="Directory that receives run folders. Defaults to ./runs.",
    )
    parser.add_argument(
        "--run-name",
        default=None,
        help="Override the generated run folder name.",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=None,
        help="Optional output PNG path. If omitted, writes inside runs/<run-name>/.",
    )
    return parser.parse_args()


def read_metadata(path: Path) -> VideoMetadata:
    capture = cv2.VideoCapture(str(path))
    if not capture.isOpened():
        raise SystemExit(f"could not open video: {path}")
    fps = float(capture.get(cv2.CAP_PROP_FPS) or 0.0)
    frame_count = int(capture.get(cv2.CAP_PROP_FRAME_COUNT) or 0)
    width = int(capture.get(cv2.CAP_PROP_FRAME_WIDTH) or 0)
    height = int(capture.get(cv2.CAP_PROP_FRAME_HEIGHT) or 0)
    capture.release()
    if fps <= 0 or width <= 0 or height <= 0:
        raise SystemExit(f"could not read video metadata: {path}")
    return VideoMetadata(path=path, width=width, height=height, fps=fps, frame_count=frame_count)


def read_frame(path: Path, index: int) -> np.ndarray:
    capture = cv2.VideoCapture(str(path))
    if not capture.isOpened():
        raise SystemExit(f"could not open video: {path}")
    capture.set(cv2.CAP_PROP_POS_FRAMES, index)
    ok, frame = capture.read()
    capture.release()
    if not ok:
        raise SystemExit(f"could not read frame {index} from {path}")
    return frame


def choose_original_frames(metadata: VideoMetadata, count: int) -> list[int]:
    if metadata.frame_count <= 0:
        raise SystemExit(f"video does not report frame count: {metadata.path}")
    if count == 1:
        return [0]
    raw = np.linspace(0, metadata.frame_count - 1, count)
    return [int(round(value)) for value in raw]


def frame_at_time(metadata: VideoMetadata, seconds: float) -> int:
    index = int(round(seconds * metadata.fps))
    if metadata.frame_count > 0:
        index = min(index, metadata.frame_count - 1)
    return max(index, 0)


def draw_points(
    image: np.ndarray,
    source_size: tuple[int, int],
    points: list[tuple[float, float]],
) -> None:
    source_width, source_height = source_size
    scale_x = image.shape[1] / source_width
    scale_y = image.shape[0] / source_height
    scaled = [(int(round(x * scale_x)), int(round(y * scale_y))) for x, y in points]

    if len(scaled) == 4:
        polygon = np.asarray(scaled, dtype=np.int32).reshape((-1, 1, 2))
        cv2.polylines(image, [polygon], isClosed=True, color=(0, 255, 96), thickness=2)

    for index, point in enumerate(scaled, start=1):
        cv2.circle(image, point, 5, (40, 40, 255), -1)
        cv2.circle(image, point, 6, (255, 255, 255), 1)
        cv2.putText(
            image,
            str(index),
            (point[0] + 8, point[1] - 8),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.45,
            (255, 255, 255),
            2,
            cv2.LINE_AA,
        )


def make_tile(
    frame: np.ndarray,
    thumb_width: int,
    label_height: int,
    label: str,
    points: list[tuple[float, float]] | None = None,
) -> np.ndarray:
    source_height, source_width = frame.shape[:2]
    scale = thumb_width / source_width
    thumb_height = max(1, int(round(source_height * scale)))
    tile = cv2.resize(frame, (thumb_width, thumb_height), interpolation=cv2.INTER_AREA)
    if points:
        draw_points(tile, (source_width, source_height), points)

    if label_height <= 0:
        return tile

    labeled = cv2.copyMakeBorder(
        tile,
        label_height,
        0,
        0,
        0,
        cv2.BORDER_CONSTANT,
        value=(20, 20, 20),
    )
    cv2.putText(
        labeled,
        label,
        (8, max(18, label_height - 8)),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.48,
        (240, 240, 240),
        1,
        cv2.LINE_AA,
    )
    return labeled


def make_row_label(height: int, width: int, text: str) -> np.ndarray:
    label = np.full((height, width, 3), 245, dtype=np.uint8)
    cv2.rectangle(label, (0, 0), (width - 1, height - 1), (210, 210, 210), 1)
    cv2.putText(
        label,
        text,
        (10, max(24, height // 2)),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.58,
        (20, 20, 20),
        2,
        cv2.LINE_AA,
    )
    return label


def pad_to_height(image: np.ndarray, height: int) -> np.ndarray:
    missing = height - image.shape[0]
    if missing <= 0:
        return image
    return cv2.copyMakeBorder(
        image,
        0,
        missing,
        0,
        0,
        cv2.BORDER_CONSTANT,
        value=(255, 255, 255),
    )


def build_strip(args: argparse.Namespace) -> tuple[np.ndarray, list[int]]:
    original_meta = read_metadata(args.original)
    normalized_meta = read_metadata(args.normalized)
    original_frames = args.frames or choose_original_frames(original_meta, args.count)

    original_tiles: list[np.ndarray] = []
    normalized_tiles: list[np.ndarray] = []
    for original_index in original_frames:
        if original_meta.frame_count > 0 and original_index >= original_meta.frame_count:
            raise SystemExit(
                f"frame {original_index} is outside original video frame count "
                f"{original_meta.frame_count}"
            )
        seconds = original_index / original_meta.fps
        normalized_index = frame_at_time(normalized_meta, seconds)

        original_frame = read_frame(args.original, original_index)
        normalized_frame = read_frame(args.normalized, normalized_index)
        label = f"f{original_index}  {seconds:.2f}s"
        original_tiles.append(
            make_tile(
                original_frame,
                args.thumb_width,
                args.label_height,
                label,
                points=args.points,
            )
        )
        normalized_tiles.append(
            make_tile(normalized_frame, args.thumb_width, args.label_height, label)
        )

    original_row = np.hstack(original_tiles)
    normalized_row = np.hstack(normalized_tiles)
    row_height = max(original_row.shape[0], normalized_row.shape[0])
    original_row = pad_to_height(original_row, row_height)
    normalized_row = pad_to_height(normalized_row, row_height)

    label_width = 112
    original_row = np.hstack([make_row_label(row_height, label_width, "original"), original_row])
    normalized_row = np.hstack([make_row_label(row_height, label_width, "corrected"), normalized_row])
    separator = np.full((12, original_row.shape[1], 3), 255, dtype=np.uint8)
    return np.vstack([original_row, separator, normalized_row]), original_frames


def resolve_output(args: argparse.Namespace) -> Path:
    if args.output:
        output = args.output
        output.parent.mkdir(parents=True, exist_ok=True)
        return output.resolve()

    runs_dir = args.runs_dir.resolve() if args.runs_dir else project_root() / "runs"
    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    run_name = args.run_name or f"{timestamp}_comparison_strip"
    run_dir = create_run_directory(runs_dir, run_name)
    return (run_dir / f"{args.original.stem}_comparison_strip.png").resolve()


def main() -> None:
    args = parse_args()
    strip, frames = build_strip(args)
    output = resolve_output(args)
    ok = cv2.imwrite(str(output), strip)
    if not ok:
        raise SystemExit(f"could not write {output}")
    print(f"frames: {','.join(str(frame) for frame in frames)}")
    print(f"wrote {output}")


if __name__ == "__main__":
    main()
