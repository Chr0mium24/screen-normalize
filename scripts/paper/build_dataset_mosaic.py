#!/usr/bin/env python3
"""Build a category-row mosaic from annotated dataset samples."""

from __future__ import annotations

import argparse
import csv
from pathlib import Path

import cv2
import numpy as np

from screen_normalize.experiments.annotations import load_annotations


CATEGORIES = ("scrolling", "screen_video", "static", "weak_border", "hard")
SAMPLES_PER_CATEGORY = 3
IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png"}
VIDEO_EXTENSIONS = {".mp4"}
THUMB_SIZE = (360, 203)
ROW_LABEL_WIDTH = 130
TITLE_HEIGHT = 34
PADDING = 8


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, default=Path("inputs"))
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("doc/paper/results/dataset/annotated_dataset_mosaic.jpg"),
    )
    parser.add_argument(
        "--manifest",
        type=Path,
        default=Path("doc/paper/results/dataset/annotated_dataset_mosaic_manifest.csv"),
    )
    parser.add_argument("--jpeg-quality", type=int, default=92)
    return parser.parse_args()


def video_shape(path: Path) -> tuple[int, int, int]:
    capture = cv2.VideoCapture(str(path))
    if not capture.isOpened():
        raise RuntimeError(f"could not open video: {path}")
    width = int(capture.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(capture.get(cv2.CAP_PROP_FRAME_HEIGHT))
    count = int(capture.get(cv2.CAP_PROP_FRAME_COUNT))
    capture.release()
    return width, height, count


def image_shape(path: Path) -> tuple[int, int, int]:
    image = cv2.imread(str(path), cv2.IMREAD_COLOR)
    if image is None:
        raise RuntimeError(f"could not open image: {path}")
    height, width = image.shape[:2]
    return width, height, 1


def media_shape(path: Path) -> tuple[int, int, int]:
    if path.suffix.lower() in IMAGE_EXTENSIONS:
        return image_shape(path)
    if path.suffix.lower() in VIDEO_EXTENSIONS:
        return video_shape(path)
    raise RuntimeError(f"unsupported media file: {path}")


def read_video_frame(path: Path, frame_index: int) -> np.ndarray:
    capture = cv2.VideoCapture(str(path))
    if not capture.isOpened():
        raise RuntimeError(f"could not open video: {path}")
    capture.set(cv2.CAP_PROP_POS_FRAMES, frame_index)
    ok, frame = capture.read()
    capture.release()
    if not ok:
        raise RuntimeError(f"could not read frame {frame_index}: {path}")
    return frame


def read_media_frame(path: Path, frame_index: int) -> np.ndarray:
    if path.suffix.lower() in IMAGE_EXTENSIONS:
        image = cv2.imread(str(path), cv2.IMREAD_COLOR)
        if image is None:
            raise RuntimeError(f"could not read image: {path}")
        return image
    return read_video_frame(path, frame_index)


def choose_annotation(csv_path: Path, width: int, height: int) -> tuple[int, np.ndarray]:
    annotations = load_annotations(csv_path, width, height)
    if not annotations:
        raise RuntimeError(f"no annotations found: {csv_path}")
    frame_index = 0 if 0 in annotations else min(annotations)
    return frame_index, annotations[frame_index]


def draw_overlay(frame: np.ndarray, corners: np.ndarray) -> np.ndarray:
    canvas = frame.copy()
    polygon = np.round(corners).astype(np.int32)
    cv2.polylines(canvas, [polygon], True, (80, 255, 130), 10, cv2.LINE_AA)
    for index, point in enumerate(polygon):
        cv2.circle(canvas, tuple(point), 24, (0, 70, 255), -1, cv2.LINE_AA)
        cv2.putText(
            canvas,
            ("TL", "TR", "BR", "BL")[index],
            tuple(point + np.array([28, -20])),
            cv2.FONT_HERSHEY_SIMPLEX,
            1.8,
            (255, 255, 255),
            5,
            cv2.LINE_AA,
        )
    return canvas


def make_tile(frame: np.ndarray, label: str) -> np.ndarray:
    thumb = cv2.resize(frame, THUMB_SIZE, interpolation=cv2.INTER_AREA)
    tile = np.full((THUMB_SIZE[1] + TITLE_HEIGHT, THUMB_SIZE[0], 3), 18, np.uint8)
    tile[TITLE_HEIGHT:, :] = thumb
    cv2.putText(tile, label, (10, 23), cv2.FONT_HERSHEY_SIMPLEX, 0.65, (235, 240, 245), 2, cv2.LINE_AA)
    return tile


def sample_media(input_dir: Path, category: str) -> list[tuple[Path, str]]:
    if category == "hard":
        source_indices = (11, 12, 13)
    else:
        source_indices = tuple(range(1, SAMPLES_PER_CATEGORY + 1))

    samples: list[tuple[Path, str]] = []
    for display_index, source_index in enumerate(source_indices, start=1):
        stem = f"{category}_{source_index:02d}"
        candidates = [
            input_dir / category / f"{stem}{extension}"
            for extension in [".mp4", ".jpg", ".jpeg", ".png"]
        ]
        media_path = next((candidate for candidate in candidates if candidate.exists()), None)
        if media_path is None:
            raise RuntimeError(f"missing sample media for {category}: {stem}")
        samples.append((media_path, f"{category}_{display_index:02d}"))
    return samples


def build_mosaic(input_dir: Path) -> tuple[np.ndarray, list[dict[str, object]]]:
    rows: list[np.ndarray] = []
    manifest: list[dict[str, object]] = []
    tile_height = THUMB_SIZE[1] + TITLE_HEIGHT

    for category in CATEGORIES:
        samples = sample_media(input_dir, category)
        tiles = []
        for media_path, display_id in samples:
            width, height, frame_count = media_shape(media_path)
            csv_path = media_path.with_suffix(".csv")
            frame_index, corners = choose_annotation(csv_path, width, height)
            frame = read_media_frame(media_path, frame_index)
            tile = make_tile(draw_overlay(frame, corners), f"{display_id}  f{frame_index}")
            tiles.append(tile)
            manifest.append(
                {
                    "category": category,
                    "display_id": display_id,
                    "source_id": media_path.stem,
                    "media_type": "image" if media_path.suffix.lower() in IMAGE_EXTENSIONS else "video",
                    "media": media_path.as_posix(),
                    "annotation_csv": csv_path.as_posix(),
                    "selected_frame": frame_index,
                    "used_frame_zero": frame_index == 0,
                    "frame_count": frame_count,
                }
            )

        row = np.full((tile_height, ROW_LABEL_WIDTH + len(tiles) * THUMB_SIZE[0], 3), 12, np.uint8)
        cv2.putText(row, category, (12, tile_height // 2 + 8), cv2.FONT_HERSHEY_SIMPLEX, 0.75, (235, 240, 245), 2, cv2.LINE_AA)
        x = ROW_LABEL_WIDTH
        for tile in tiles:
            row[:, x : x + THUMB_SIZE[0]] = tile
            x += THUMB_SIZE[0]
        rows.append(row)

    gap = np.full((PADDING, rows[0].shape[1], 3), 28, np.uint8)
    mosaic = rows[0]
    for row in rows[1:]:
        mosaic = np.vstack([mosaic, gap, row])
    return mosaic, manifest


def write_manifest(path: Path, rows: list[dict[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = [
        "category",
        "display_id",
        "source_id",
        "media_type",
        "media",
        "annotation_csv",
        "selected_frame",
        "used_frame_zero",
        "frame_count",
    ]
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def main() -> int:
    args = parse_args()
    mosaic, manifest = build_mosaic(args.input)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    ok = cv2.imwrite(str(args.output), mosaic, [cv2.IMWRITE_JPEG_QUALITY, args.jpeg_quality])
    if not ok:
        raise RuntimeError(f"could not write {args.output}")
    write_manifest(args.manifest, manifest)
    print(f"wrote {args.output}")
    print(f"wrote {args.manifest}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
