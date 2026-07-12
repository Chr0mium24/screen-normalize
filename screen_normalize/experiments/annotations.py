from __future__ import annotations

import csv
import os
import tempfile
from pathlib import Path

import cv2
import numpy as np


CORNER_NAMES = ("tl", "tr", "br", "bl")
FIELDS = ("frame", *(f"{name}_{axis}" for name in CORNER_NAMES for axis in ("x", "y")))


class AnnotationError(ValueError):
    pass


def validate_corners(corners: np.ndarray, width: int, height: int) -> np.ndarray:
    points = np.asarray(corners, dtype=np.float32)
    if points.shape != (4, 2) or not np.isfinite(points).all():
        raise AnnotationError("corners must contain four finite x,y points")
    if width <= 0 or height <= 0:
        raise AnnotationError("video dimensions must be positive")
    if np.any(points[:, 0] < 0) or np.any(points[:, 0] >= width):
        raise AnnotationError("corner x coordinate is outside the video")
    if np.any(points[:, 1] < 0) or np.any(points[:, 1] >= height):
        raise AnnotationError("corner y coordinate is outside the video")
    contour = points.reshape(-1, 1, 2)
    if not cv2.isContourConvex(contour) or abs(cv2.contourArea(contour)) < 4.0:
        raise AnnotationError("corners must be a non-degenerate convex TL,TR,BR,BL quadrilateral")
    first = points[1] - points[0]
    second = points[2] - points[1]
    cross = float(first[0] * second[1] - first[1] * second[0])
    if cross <= 0:
        raise AnnotationError("corners must be ordered TL,TR,BR,BL")
    return points


def load_annotations(path: Path, width: int, height: int) -> dict[int, np.ndarray]:
    if not path.exists():
        return {}
    result: dict[int, np.ndarray] = {}
    with path.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        if tuple(reader.fieldnames or ()) != FIELDS:
            raise AnnotationError(f"annotation columns must be: {','.join(FIELDS)}")
        for line, row in enumerate(reader, start=2):
            try:
                frame = int(row["frame"])
                points = np.asarray(
                    [[float(row[f"{name}_x"]), float(row[f"{name}_y"])] for name in CORNER_NAMES],
                    dtype=np.float32,
                )
            except (TypeError, ValueError) as exc:
                raise AnnotationError(f"invalid annotation at line {line}") from exc
            if frame < 0 or frame in result:
                raise AnnotationError(f"frame must be unique and non-negative at line {line}")
            result[frame] = validate_corners(points, width, height)
    return dict(sorted(result.items()))


def save_annotations(
    path: Path,
    annotations: dict[int, np.ndarray],
    width: int,
    height: int,
) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    rows = []
    for frame, corners in sorted(annotations.items()):
        if frame < 0:
            raise AnnotationError("frame must be non-negative")
        points = validate_corners(corners, width, height)
        row: dict[str, int | float] = {"frame": frame}
        for name, (x, y) in zip(CORNER_NAMES, points):
            row[f"{name}_x"] = float(x)
            row[f"{name}_y"] = float(y)
        rows.append(row)

    fd, temporary = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent, text=True)
    try:
        with os.fdopen(fd, "w", newline="", encoding="utf-8") as handle:
            writer = csv.DictWriter(handle, fieldnames=FIELDS)
            writer.writeheader()
            writer.writerows(rows)
        os.replace(temporary, path)
    except BaseException:
        Path(temporary).unlink(missing_ok=True)
        raise
