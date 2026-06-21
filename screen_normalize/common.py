from __future__ import annotations

import argparse
import shutil
from datetime import datetime
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


def byte_int(value: str) -> int:
    parsed = int(value)
    if not 0 <= parsed <= 255:
        raise argparse.ArgumentTypeError("value must be between 0 and 255")
    return parsed


def odd_positive_int(value: str) -> int:
    parsed = positive_int(value)
    if parsed % 2 == 0:
        raise argparse.ArgumentTypeError("value must be odd")
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


def percentile_float(value: str) -> float:
    parsed = float(value)
    if not 0.0 <= parsed <= 100.0:
        raise argparse.ArgumentTypeError("value must be between 0 and 100")
    return parsed


def nonnegative_fraction(value: str) -> float:
    parsed = float(value)
    if parsed < 0.0:
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


def resolve_run_output(
    args: argparse.Namespace,
    source: Path,
    script_name: str = "normalize_screen",
) -> tuple[Path, Path]:
    runs_dir = args.runs_dir.resolve() if args.runs_dir else project_root() / "runs"
    script_name = clean_path_component(script_name)
    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    run_name = args.run_name or f"{timestamp}_{script_name}"
    run_dir = create_run_directory(runs_dir, run_name)

    output_name = args.output.name if args.output else f"{source.stem}_normalized.mp4"
    if not Path(output_name).suffix:
        output_name = f"{output_name}.mp4"
    output = run_dir / output_name
    return output.resolve(), run_dir.resolve()


def require_ffmpeg() -> None:
    if shutil.which("ffmpeg") is None:
        raise SystemExit("ffmpeg is required but was not found on PATH")


def open_capture(path: Path) -> cv2.VideoCapture:
    capture = cv2.VideoCapture(str(path))
    if not capture.isOpened():
        raise SystemExit(f"could not open input video: {path}")
    return capture
