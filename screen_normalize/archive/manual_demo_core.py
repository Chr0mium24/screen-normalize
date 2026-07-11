from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

import cv2
import numpy as np


POINT_LABELS = ("TL", "TR", "BR", "BL")


@dataclass(frozen=True)
class VideoMetadata:
    path: Path
    width: int
    height: int
    fps: float
    frame_count: int


@dataclass
class FrameAnnotation:
    frame: int
    time_seconds: float
    corners: list[tuple[float, float]]


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


def choose_frames(metadata: VideoMetadata, count: int) -> list[int]:
    if metadata.frame_count <= 0:
        raise SystemExit(f"video does not report frame count: {metadata.path}")
    if count == 1:
        return [0]
    raw = np.linspace(0, metadata.frame_count - 1, count)
    return [int(round(value)) for value in raw]


def format_corners(points: list[tuple[float, float]]) -> str:
    return ":".join(f"{round(x)},{round(y)}" for x, y in points)


def warp_frame(frame: np.ndarray, corners: list[tuple[float, float]], output_size: tuple[int, int]) -> np.ndarray:
    source = np.asarray(corners, dtype=np.float32)
    width, height = output_size
    destination = np.asarray(
        [[0, 0], [width - 1, 0], [width - 1, height - 1], [0, height - 1]],
        dtype=np.float32,
    )
    transform = cv2.getPerspectiveTransform(source, destination)
    return cv2.warpPerspective(frame, transform, (width, height))


def draw_points(
    image: np.ndarray,
    source_size: tuple[int, int],
    points: list[tuple[float, float]],
) -> None:
    source_width, source_height = source_size
    scale_x = image.shape[1] / source_width
    scale_y = image.shape[0] / source_height
    scaled = [(int(round(x * scale_x)), int(round(y * scale_y))) for x, y in points]

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


def make_tile(frame: np.ndarray, thumb_width: int, label_height: int, label: str) -> np.ndarray:
    source_height, source_width = frame.shape[:2]
    scale = thumb_width / source_width
    thumb_height = max(1, int(round(source_height * scale)))
    tile = cv2.resize(frame, (thumb_width, thumb_height), interpolation=cv2.INTER_AREA)
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


def build_demo_strip(
    input_path: Path,
    annotations: list[FrameAnnotation],
    output_size: tuple[int, int],
    thumb_width: int,
    label_height: int,
) -> np.ndarray:
    original_tiles: list[np.ndarray] = []
    target_tiles: list[np.ndarray] = []
    for annotation in annotations:
        frame = read_frame(input_path, annotation.frame)
        original = frame.copy()
        frame_height, frame_width = frame.shape[:2]
        draw_points(original, (frame_width, frame_height), annotation.corners)

        label = f"f{annotation.frame}  {annotation.time_seconds:.2f}s"
        original_tiles.append(make_tile(original, thumb_width, label_height, label))
        warped = warp_frame(frame, annotation.corners, output_size)
        target_tiles.append(make_tile(warped, thumb_width, label_height, label))

    original_row = np.hstack(original_tiles)
    target_row = np.hstack(target_tiles)
    row_height = max(original_row.shape[0], target_row.shape[0])
    original_row = pad_to_height(original_row, row_height)
    target_row = pad_to_height(target_row, row_height)

    label_width = 160
    original_row = np.hstack([make_row_label(row_height, label_width, "marked input"), original_row])
    target_row = np.hstack([make_row_label(row_height, label_width, "manual target"), target_row])
    separator = np.full((12, original_row.shape[1], 3), 255, dtype=np.uint8)
    return np.vstack([original_row, separator, target_row])


def save_annotations(
    path: Path,
    input_path: Path,
    output_size: tuple[int, int],
    annotations: list[FrameAnnotation],
) -> None:
    payload = {
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "video": str(input_path),
        "output_size": {"width": output_size[0], "height": output_size[1]},
        "frames": [
            {
                "frame": annotation.frame,
                "time_seconds": annotation.time_seconds,
                "corners": [[x, y] for x, y in annotation.corners],
            }
            for annotation in annotations
        ],
    }
    with path.open("w") as handle:
        json.dump(payload, handle, indent=2)
        handle.write("\n")


def load_annotations(path: Path) -> tuple[tuple[int, int] | None, list[FrameAnnotation]]:
    with path.open() as handle:
        payload = json.load(handle)

    output_size = None
    raw_output_size = payload.get("output_size")
    if isinstance(raw_output_size, dict):
        width = raw_output_size.get("width")
        height = raw_output_size.get("height")
        if isinstance(width, int) and isinstance(height, int):
            output_size = (width, height)

    annotations = []
    for raw_frame in payload.get("frames", []):
        corners = [(float(x), float(y)) for x, y in raw_frame["corners"]]
        if len(corners) != 4:
            raise SystemExit(f"annotation frame {raw_frame.get('frame')} does not have 4 corners")
        annotations.append(
            FrameAnnotation(
                frame=int(raw_frame["frame"]),
                time_seconds=float(raw_frame["time_seconds"]),
                corners=corners,
            )
        )
    if not annotations:
        raise SystemExit(f"no annotations found in {path}")
    return output_size, annotations
