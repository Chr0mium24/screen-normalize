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
import shutil
import subprocess
import sys
import tempfile
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


def resolve_run_output(args: argparse.Namespace, source: Path) -> tuple[Path, Path]:
    runs_dir = args.runs_dir.resolve() if args.runs_dir else project_root() / "runs"
    script_name = clean_path_component(Path(__file__).stem)
    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    run_name = args.run_name or f"{timestamp}_{script_name}"
    run_dir = create_run_directory(runs_dir, run_name)

    output_name = args.output.name if args.output else f"{source.stem}_normalized.mp4"
    if not Path(output_name).suffix:
        output_name = f"{output_name}.mp4"
    output = run_dir / output_name
    return output.resolve(), run_dir.resolve()


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Perspective-correct a filmed monitor into a screen-recording-like video."
    )
    parser.add_argument("input", type=Path)
    parser.add_argument(
        "output",
        type=Path,
        nargs="?",
        help=(
            "Optional output filename. The file is always written inside a "
            "timestamped runs/<time>_<script>/ directory."
        ),
    )
    parser.add_argument(
        "--runs-dir",
        type=Path,
        default=None,
        help="Directory that receives timestamped run folders. Defaults to ./runs.",
    )
    parser.add_argument(
        "--run-name",
        default=None,
        help="Override the generated run folder name.",
    )
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
    parser.add_argument(
        "--tracker",
        choices=("detect", "flow", "reference"),
        default="flow",
        help=(
            "Corner trajectory source. reference locks all frames to the first "
            "screen plane using LK optical flow."
        ),
    )
    parser.add_argument(
        "--reference-profile",
        choices=("dynamic", "low-latency"),
        default=None,
        help=(
            "Preset reference-tracker parameters. dynamic uses mature points and "
            "offline smoothing; low-latency uses immediate points with no trajectory smoothing."
        ),
    )
    parser.add_argument(
        "--trajectory-window",
        type=odd_positive_int,
        default=31,
        help="Centered moving-average window for offline corner trajectory smoothing.",
    )
    parser.add_argument(
        "--median-window",
        type=odd_positive_int,
        default=5,
        help="Centered median window used before averaging to reject corner jumps.",
    )
    parser.add_argument(
        "--detect-correction",
        type=smoothing_weight,
        default=0.08,
        help="Blend weight for color-detected corners when optical-flow tracking is valid.",
    )
    parser.add_argument("--feature-refresh", type=positive_int, default=15)
    parser.add_argument(
        "--reference-min-inliers",
        type=positive_int,
        default=40,
        help="Minimum RANSAC inliers required before accepting a reference tracker update.",
    )
    parser.add_argument(
        "--reference-min-inlier-ratio",
        type=nonnegative_fraction,
        default=0.25,
        help="Minimum inlier ratio required before accepting a reference tracker update.",
    )
    parser.add_argument(
        "--reference-max-reprojection-error",
        type=nonnegative_fraction,
        default=2.5,
        help="Maximum median inlier reprojection error in pixels for reference tracking.",
    )
    parser.add_argument(
        "--reference-max-scale-step",
        type=nonnegative_fraction,
        default=0.035,
        help="Maximum accepted frame-to-frame side-length scale change; 0 disables.",
    )
    parser.add_argument(
        "--reference-max-area-step",
        type=nonnegative_fraction,
        default=0.08,
        help="Maximum accepted frame-to-frame screen-area change; 0 disables.",
    )
    parser.add_argument(
        "--reference-min-point-age",
        type=positive_int,
        default=15,
        help="Newly refreshed reference points must survive this many accepted frames before driving homography.",
    )
    parser.add_argument(
        "--reference-min-coverage-x",
        type=nonnegative_fraction,
        default=0.25,
        help="Minimum robust normalized x coverage of RANSAC inliers; 0 disables.",
    )
    parser.add_argument(
        "--reference-min-coverage-y",
        type=nonnegative_fraction,
        default=0.20,
        help="Minimum robust normalized y coverage of RANSAC inliers; 0 disables.",
    )
    parser.add_argument(
        "--reference-align",
        action="store_true",
        help="After perspective correction, align each frame back to the first corrected frame.",
    )
    parser.add_argument(
        "--reference-motion",
        choices=("affine", "homography"),
        default="affine",
        help="Residual motion model used by --reference-align.",
    )
    parser.add_argument(
        "--reference-align-smooth",
        type=smoothing_weight,
        default=0.0,
        help="Previous-frame smoothing weight for residual affine alignment; 0 keeps raw estimates.",
    )
    parser.add_argument(
        "--reference-align-max-translation-step",
        type=nonnegative_fraction,
        default=0.0,
        help="Maximum per-frame residual affine translation step in pixels; 0 disables.",
    )
    parser.add_argument(
        "--reference-align-max-rotation-step-deg",
        type=nonnegative_fraction,
        default=0.0,
        help="Maximum per-frame residual affine rotation step in degrees; 0 disables.",
    )
    parser.add_argument(
        "--reference-align-max-scale-step",
        type=nonnegative_fraction,
        default=0.0,
        help="Maximum per-frame residual affine scale step; 0 disables.",
    )
    parser.add_argument(
        "--reference-align-filter-window",
        type=odd_positive_int,
        default=1,
        help="Centered moving-average window for offline residual affine alignment; 1 disables.",
    )
    parser.add_argument(
        "--reference-align-min-inliers",
        type=positive_int,
        default=80,
        help="Minimum residual alignment RANSAC inliers before applying correction.",
    )
    parser.add_argument(
        "--reference-align-min-inlier-ratio",
        type=nonnegative_fraction,
        default=0.60,
        help="Minimum residual alignment inlier ratio before applying correction.",
    )
    parser.add_argument(
        "--reference-align-min-coverage-x",
        type=nonnegative_fraction,
        default=0.25,
        help="Minimum normalized x coverage for residual alignment inliers; 0 disables.",
    )
    parser.add_argument(
        "--reference-align-min-coverage-y",
        type=nonnegative_fraction,
        default=0.20,
        help="Minimum normalized y coverage for residual alignment inliers; 0 disables.",
    )
    parser.add_argument(
        "--reference-align-max-reprojection-error",
        type=nonnegative_fraction,
        default=1.0,
        help="Maximum residual alignment median reprojection error in pixels; 0 disables.",
    )
    parser.add_argument(
        "--reference-align-max-translation",
        type=nonnegative_fraction,
        default=12.0,
        help="Maximum residual alignment translation magnitude in pixels; 0 disables.",
    )
    parser.add_argument(
        "--reference-align-max-rotation-deg",
        type=nonnegative_fraction,
        default=0.50,
        help="Maximum absolute residual alignment rotation in degrees; 0 disables.",
    )
    parser.add_argument(
        "--reference-align-max-scale-delta",
        type=nonnegative_fraction,
        default=0.010,
        help="Maximum residual alignment scale distance from 1.0; 0 disables.",
    )
    parser.add_argument(
        "--reference-align-min-accept-ratio",
        type=nonnegative_fraction,
        default=0.90,
        help="Minimum whole-video residual alignment accept ratio; below this, correction is disabled.",
    )
    parser.add_argument(
        "--write-tracker-debug",
        action="store_true",
        help="Write per-frame tracker diagnostics to tracker_debug.csv in the run directory.",
    )
    parser.add_argument(
        "--write-align-debug",
        action="store_true",
        help="Write per-frame residual alignment diagnostics to align_debug.csv in the run directory.",
    )
    parser.add_argument(
        "--line-roll-correction",
        action="store_true",
        help="Use stable horizontal UI lines to apply a small residual roll correction.",
    )
    parser.add_argument(
        "--line-detector",
        choices=("binary-contour", "contour", "hough"),
        default="binary-contour",
        help="Horizontal-line detector used by --line-roll-correction.",
    )
    parser.add_argument(
        "--line-full-mask",
        action=argparse.BooleanOptionalAction,
        default=True,
        help="Use the whole normalized frame for line detection; disable to use top/right/bottom masks.",
    )
    parser.add_argument(
        "--line-mask-top",
        type=crop_fraction,
        default=0.34,
        help="Top screen fraction used for line roll estimation.",
    )
    parser.add_argument(
        "--line-mask-right",
        type=crop_fraction,
        default=0.30,
        help="Right screen fraction used for line roll estimation.",
    )
    parser.add_argument(
        "--line-mask-bottom",
        type=crop_fraction,
        default=0.0,
        help="Bottom screen fraction used for line roll estimation.",
    )
    parser.add_argument(
        "--line-ignore-top",
        type=crop_fraction,
        default=0.0,
        help="Top screen fraction excluded from line roll estimation.",
    )
    parser.add_argument(
        "--line-min-segments",
        type=positive_int,
        default=2,
        help="Minimum horizontal line segments before accepting a roll estimate.",
    )
    parser.add_argument(
        "--line-min-total-length",
        type=positive_int,
        default=1000,
        help="Minimum total accepted horizontal line length in pixels.",
    )
    parser.add_argument(
        "--line-cluster-deg",
        type=nonnegative_fraction,
        default=0.35,
        help="Maximum angle distance from the dominant horizontal-line direction.",
    )
    parser.add_argument(
        "--line-horizontal-kernel",
        type=positive_int,
        default=81,
        help="Horizontal morphology kernel width used by the contour line detector.",
    )
    parser.add_argument(
        "--line-max-thickness",
        type=positive_int,
        default=24,
        help="Maximum contour thickness in pixels for structural line candidates.",
    )
    parser.add_argument(
        "--line-white-threshold",
        type=byte_int,
        default=246,
        help="Binary detector cap for adaptive background brightness.",
    )
    parser.add_argument(
        "--line-background-percentile",
        type=percentile_float,
        default=75.0,
        help="Binary detector percentile used to estimate the light page background.",
    )
    parser.add_argument(
        "--line-dark-margin",
        type=nonnegative_fraction,
        default=24.0,
        help="Binary detector foreground margin below the estimated background brightness.",
    )
    parser.add_argument(
        "--line-saturation-threshold",
        type=byte_int,
        default=24,
        help="Binary detector threshold for saturated foreground below the light background.",
    )
    parser.add_argument(
        "--line-max-correction-deg",
        type=nonnegative_fraction,
        default=1.0,
        help="Maximum absolute roll correction in degrees.",
    )
    parser.add_argument(
        "--line-max-step-deg",
        type=nonnegative_fraction,
        default=0.12,
        help="Maximum frame-to-frame change in the smoothed roll correction.",
    )
    parser.add_argument(
        "--line-max-measurement-step-deg",
        type=nonnegative_fraction,
        default=0.45,
        help="Reject line roll measurements this far from the current smoothed correction; 0 disables.",
    )
    parser.add_argument(
        "--line-smooth",
        type=smoothing_weight,
        default=0.80,
        help="Previous-frame smoothing weight for line roll estimates.",
    )
    parser.add_argument("--crop-left", type=crop_fraction, default=0.0)
    parser.add_argument("--crop-top", type=crop_fraction, default=0.0)
    parser.add_argument("--crop-right", type=crop_fraction, default=0.0)
    parser.add_argument("--crop-bottom", type=crop_fraction, default=0.0)
    return parser.parse_args()


def apply_reference_profile(args: argparse.Namespace) -> None:
    if args.reference_profile == "dynamic":
        args.reference_min_point_age = 15
        args.median_window = 5
        args.trajectory_window = 31
    elif args.reference_profile == "low-latency":
        args.reference_min_point_age = 1
        args.median_window = 1
        args.trajectory_window = 1


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


def corner_edge_lengths(corners: np.ndarray) -> np.ndarray:
    return np.array(
        [
            np.linalg.norm(corners[1] - corners[0]),
            np.linalg.norm(corners[2] - corners[1]),
            np.linalg.norm(corners[2] - corners[3]),
            np.linalg.norm(corners[3] - corners[0]),
        ],
        dtype=np.float32,
    )


def ratio_is_within(value: float, previous: float, max_step: float) -> bool:
    if max_step <= 0:
        return True
    if previous <= 0:
        return False
    ratio = value / previous
    return (1.0 - max_step) <= ratio <= (1.0 + max_step)


def geometry_update_is_reasonable(
    corners: np.ndarray,
    previous_corners: np.ndarray,
    max_scale_step: float,
    max_area_step: float,
) -> bool:
    previous_edges = corner_edge_lengths(previous_corners)
    edges = corner_edge_lengths(corners)
    if np.any(previous_edges <= 0) or np.any(edges <= 0):
        return False
    for edge, previous_edge in zip(edges, previous_edges, strict=True):
        if not ratio_is_within(float(edge), float(previous_edge), max_scale_step):
            return False

    area = abs(cv2.contourArea(corners))
    previous_area = abs(cv2.contourArea(previous_corners))
    return ratio_is_within(float(area), float(previous_area), max_area_step)


def homography_median_reprojection_error(
    source_points: np.ndarray,
    target_points: np.ndarray,
    homography: np.ndarray,
    inlier_mask: np.ndarray,
) -> float:
    inliers = inlier_mask.reshape(-1).astype(bool)
    if not np.any(inliers):
        return float("inf")
    projected = cv2.perspectiveTransform(
        source_points[inliers].reshape(-1, 1, 2).astype(np.float32),
        homography,
    ).reshape(-1, 2)
    errors = np.linalg.norm(projected - target_points[inliers], axis=1)
    return float(np.median(errors))


def homography_inlier_screen_coverage(
    reference_points: np.ndarray,
    inlier_mask: np.ndarray,
    reference_corners: np.ndarray,
) -> tuple[float, float]:
    inliers = inlier_mask.reshape(-1).astype(bool)
    if int(inliers.sum()) < 2:
        return 0.0, 0.0

    unit_corners = np.array(
        [[0.0, 0.0], [1.0, 0.0], [1.0, 1.0], [0.0, 1.0]],
        dtype=np.float32,
    )
    reference_to_unit = cv2.getPerspectiveTransform(
        reference_corners.astype(np.float32),
        unit_corners,
    )
    unit_points = cv2.perspectiveTransform(
        reference_points.reshape(-1, 1, 2).astype(np.float32),
        reference_to_unit,
    ).reshape(-1, 2)[inliers]
    lower = np.percentile(unit_points, 5, axis=0)
    upper = np.percentile(unit_points, 95, axis=0)
    coverage = np.maximum(upper - lower, 0.0)
    return float(coverage[0]), float(coverage[1])


def append_tracker_debug_row(
    rows: list[dict[str, object]] | None,
    frame: int,
    accepted: bool,
    reason: str,
    corners: np.ndarray,
    point_count: int,
    mature_point_count: int,
    valid_count: int,
    mature_valid_count: int,
    inlier_count: int,
    inlier_ratio: float,
    reprojection_error: float,
    coverage_x: float,
    coverage_y: float,
    rejected_updates: int,
) -> None:
    if rows is None:
        return

    sides = corner_edge_lengths(corners)
    area = abs(cv2.contourArea(corners.astype(np.float32)))
    center = corners.mean(axis=0)
    row: dict[str, object] = {
        "frame": frame,
        "accepted": accepted,
        "reason": reason,
        "point_count": point_count,
        "mature_point_count": mature_point_count,
        "valid_count": valid_count,
        "mature_valid_count": mature_valid_count,
        "inlier_count": inlier_count,
        "inlier_ratio": inlier_ratio,
        "reprojection_error": reprojection_error,
        "coverage_x": coverage_x,
        "coverage_y": coverage_y,
        "rejected_updates": rejected_updates,
        "area": float(area),
        "center_x": float(center[0]),
        "center_y": float(center[1]),
        "top_edge": float(sides[0]),
        "right_edge": float(sides[1]),
        "bottom_edge": float(sides[2]),
        "left_edge": float(sides[3]),
    }
    for index, label in enumerate(("tl", "tr", "br", "bl")):
        row[f"{label}_x"] = float(corners[index, 0])
        row[f"{label}_y"] = float(corners[index, 1])
    rows.append(row)


def reference_reject_reason(
    current_to_reference: np.ndarray | None,
    inlier_mask: np.ndarray | None,
    mature_valid_count: int,
    inlier_count: int,
    inlier_ratio: float,
    reprojection_error: float,
    coverage_x: float,
    coverage_y: float,
    reference_min_inliers: int,
    reference_min_inlier_ratio: float,
    reference_max_reprojection_error: float,
    reference_min_coverage_x: float,
    reference_min_coverage_y: float,
) -> str:
    if mature_valid_count < 20:
        return "not_enough_mature_points"
    if current_to_reference is None or inlier_mask is None:
        return "homography_failed"
    if inlier_count < reference_min_inliers:
        return "not_enough_inliers"
    if inlier_ratio < reference_min_inlier_ratio:
        return "low_inlier_ratio"
    if reprojection_error > reference_max_reprojection_error:
        return "high_reprojection_error"
    if coverage_x < reference_min_coverage_x:
        return "low_coverage_x"
    if coverage_y < reference_min_coverage_y:
        return "low_coverage_y"
    return "invalid_geometry"


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


def corner_mask(shape: tuple[int, ...], corners: np.ndarray, inset_pixels: int = 12) -> np.ndarray:
    mask = np.zeros(shape[:2], dtype=np.uint8)
    cv2.fillConvexPoly(mask, corners.astype(np.int32), 255)
    if inset_pixels > 0:
        kernel = cv2.getStructuringElement(
            cv2.MORPH_ELLIPSE,
            (inset_pixels * 2 + 1, inset_pixels * 2 + 1),
        )
        mask = cv2.erode(mask, kernel, iterations=1)
    return mask


def select_tracking_points(gray: np.ndarray, corners: np.ndarray) -> np.ndarray | None:
    points = cv2.goodFeaturesToTrack(
        gray,
        maxCorners=900,
        qualityLevel=0.005,
        minDistance=8,
        mask=corner_mask(gray.shape, corners),
        blockSize=7,
    )
    if points is None or len(points) < 12:
        return None
    return points.astype(np.float32)


def flow_predict_corners(
    previous_gray: np.ndarray,
    gray: np.ndarray,
    previous_points: np.ndarray | None,
    previous_corners: np.ndarray,
) -> tuple[np.ndarray | None, np.ndarray | None, int]:
    if previous_points is None or len(previous_points) < 12:
        return None, None, 0

    next_points, status, _ = cv2.calcOpticalFlowPyrLK(
        previous_gray,
        gray,
        previous_points,
        None,
        winSize=(31, 31),
        maxLevel=3,
        criteria=(cv2.TERM_CRITERIA_EPS | cv2.TERM_CRITERIA_COUNT, 30, 0.01),
    )
    if next_points is None or status is None:
        return None, None, 0

    previous_back, back_status, _ = cv2.calcOpticalFlowPyrLK(
        gray,
        previous_gray,
        next_points,
        None,
        winSize=(31, 31),
        maxLevel=3,
        criteria=(cv2.TERM_CRITERIA_EPS | cv2.TERM_CRITERIA_COUNT, 30, 0.01),
    )
    if previous_back is None or back_status is None:
        return None, None, 0

    forward_ok = status.reshape(-1).astype(bool)
    backward_ok = back_status.reshape(-1).astype(bool)
    round_trip_error = np.linalg.norm(
        previous_points.reshape(-1, 2) - previous_back.reshape(-1, 2),
        axis=1,
    )
    valid = forward_ok & backward_ok & (round_trip_error < 2.0)
    previous_good = previous_points.reshape(-1, 2)[valid]
    next_good = next_points.reshape(-1, 2)[valid]
    if len(previous_good) < 12:
        return None, next_good.reshape(-1, 1, 2).astype(np.float32), len(previous_good)

    homography, inlier_mask = cv2.findHomography(
        previous_good,
        next_good,
        cv2.RANSAC,
        3.0,
    )
    if homography is None or inlier_mask is None:
        return None, next_good.reshape(-1, 1, 2).astype(np.float32), len(previous_good)

    inliers = inlier_mask.reshape(-1).astype(bool)
    if int(inliers.sum()) < 12:
        return None, next_good.reshape(-1, 1, 2).astype(np.float32), int(inliers.sum())

    predicted = cv2.perspectiveTransform(
        previous_corners.reshape(1, 4, 2),
        homography,
    ).reshape(4, 2)
    predicted = order_corners(predicted)
    if not detected_corners_are_valid(predicted, gray.shape):
        return None, next_good[inliers].reshape(-1, 1, 2).astype(np.float32), int(inliers.sum())

    return predicted, next_good[inliers].reshape(-1, 1, 2).astype(np.float32), int(inliers.sum())


def append_reference_points(
    gray: np.ndarray,
    current_corners: np.ndarray,
    current_to_reference: np.ndarray,
    reference_points: np.ndarray,
    current_points: np.ndarray,
    point_ages: np.ndarray,
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    new_points = select_tracking_points(gray, current_corners)
    if new_points is None:
        return reference_points, current_points, point_ages

    existing = current_points.reshape(-1, 2)
    fresh = []
    for point in new_points.reshape(-1, 2):
        if len(existing) and np.min(np.linalg.norm(existing - point, axis=1)) < 8:
            continue
        fresh.append(point)
        if len(fresh) >= 250:
            break

    if not fresh:
        return reference_points, current_points, point_ages

    fresh_current = np.asarray(fresh, dtype=np.float32).reshape(-1, 1, 2)
    fresh_reference = cv2.perspectiveTransform(fresh_current, current_to_reference)
    reference_points = np.concatenate([reference_points, fresh_reference.astype(np.float32)])
    current_points = np.concatenate([current_points, fresh_current.astype(np.float32)])
    point_ages = np.concatenate(
        [point_ages, np.zeros((len(fresh_current),), dtype=np.int32)]
    )
    return reference_points, current_points, point_ages


def estimate_reference_corner_trajectory(
    capture: cv2.VideoCapture,
    fallback_corners: np.ndarray,
    auto_detect: bool,
    feature_refresh: int,
    reference_min_inliers: int,
    reference_min_inlier_ratio: float,
    reference_max_reprojection_error: float,
    reference_max_scale_step: float,
    reference_max_area_step: float,
    reference_min_point_age: int,
    reference_min_coverage_x: float,
    reference_min_coverage_y: float,
    tracker_debug_rows: list[dict[str, object]] | None,
) -> list[np.ndarray]:
    frame_count = int(capture.get(cv2.CAP_PROP_FRAME_COUNT) or 0)
    ok, first_frame = capture.read()
    if not ok:
        return []

    reference_corners = detect_screen_corners(first_frame) if auto_detect else fallback_corners
    if reference_corners is None:
        reference_corners = fallback_corners
    reference_corners = order_corners(reference_corners).astype(np.float32)

    previous_gray = cv2.cvtColor(first_frame, cv2.COLOR_BGR2GRAY)
    reference_points = select_tracking_points(previous_gray, reference_corners)
    if reference_points is None:
        reference_points = reference_corners.reshape(-1, 1, 2).astype(np.float32)
    current_points = reference_points.copy()
    point_ages = np.full((len(reference_points),), reference_min_point_age, dtype=np.int32)

    trajectory = [reference_corners]
    previous_corners = reference_corners
    frame_index = 1
    rejected_updates = 0
    append_tracker_debug_row(
        tracker_debug_rows,
        frame=0,
        accepted=True,
        reason="initial_reference",
        corners=previous_corners,
        point_count=len(current_points),
        mature_point_count=int(np.count_nonzero(point_ages >= reference_min_point_age)),
        valid_count=len(current_points),
        mature_valid_count=int(np.count_nonzero(point_ages >= reference_min_point_age)),
        inlier_count=len(current_points),
        inlier_ratio=1.0,
        reprojection_error=0.0,
        coverage_x=1.0,
        coverage_y=1.0,
        rejected_updates=rejected_updates,
    )

    while True:
        ok, frame = capture.read()
        if not ok:
            break

        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        next_points, status, _ = cv2.calcOpticalFlowPyrLK(
            previous_gray,
            gray,
            current_points,
            None,
            winSize=(31, 31),
            maxLevel=3,
            criteria=(cv2.TERM_CRITERIA_EPS | cv2.TERM_CRITERIA_COUNT, 30, 0.01),
        )
        if next_points is None or status is None:
            trajectory.append(previous_corners)
            append_tracker_debug_row(
                tracker_debug_rows,
                frame=frame_index,
                accepted=False,
                reason="flow_failed",
                corners=previous_corners,
                point_count=len(current_points),
                mature_point_count=int(np.count_nonzero(point_ages >= reference_min_point_age)),
                valid_count=0,
                mature_valid_count=0,
                inlier_count=0,
                inlier_ratio=0.0,
                reprojection_error=float("inf"),
                coverage_x=0.0,
                coverage_y=0.0,
                rejected_updates=rejected_updates,
            )
            previous_gray = gray
            frame_index += 1
            continue

        previous_back, back_status, _ = cv2.calcOpticalFlowPyrLK(
            gray,
            previous_gray,
            next_points,
            None,
            winSize=(31, 31),
            maxLevel=3,
            criteria=(cv2.TERM_CRITERIA_EPS | cv2.TERM_CRITERIA_COUNT, 30, 0.01),
        )
        if previous_back is None or back_status is None:
            trajectory.append(previous_corners)
            append_tracker_debug_row(
                tracker_debug_rows,
                frame=frame_index,
                accepted=False,
                reason="backflow_failed",
                corners=previous_corners,
                point_count=len(current_points),
                mature_point_count=int(np.count_nonzero(point_ages >= reference_min_point_age)),
                valid_count=0,
                mature_valid_count=0,
                inlier_count=0,
                inlier_ratio=0.0,
                reprojection_error=float("inf"),
                coverage_x=0.0,
                coverage_y=0.0,
                rejected_updates=rejected_updates,
            )
            previous_gray = gray
            frame_index += 1
            continue

        forward_ok = status.reshape(-1).astype(bool)
        backward_ok = back_status.reshape(-1).astype(bool)
        round_trip_error = np.linalg.norm(
            current_points.reshape(-1, 2) - previous_back.reshape(-1, 2),
            axis=1,
        )
        valid = forward_ok & backward_ok & (round_trip_error < 2.0)
        mature = valid & (point_ages >= reference_min_point_age)
        reference_good = reference_points.reshape(-1, 2)[mature]
        current_good = next_points.reshape(-1, 2)[mature]
        valid_count = int(np.count_nonzero(valid))
        mature_valid_count = int(np.count_nonzero(mature))

        if len(reference_good) >= 20:
            current_to_reference, inlier_mask = cv2.findHomography(
                current_good,
                reference_good,
                cv2.RANSAC,
                3.0,
            )
        else:
            current_to_reference, inlier_mask = None, None

        accepted_transform = None
        if current_to_reference is not None and inlier_mask is not None:
            inlier_count = int(inlier_mask.sum())
            inlier_ratio = inlier_count / max(1, len(reference_good))
            reprojection_error = homography_median_reprojection_error(
                current_good,
                reference_good,
                current_to_reference,
                inlier_mask,
            )
            coverage_x, coverage_y = homography_inlier_screen_coverage(
                reference_good,
                inlier_mask,
                reference_corners,
            )
        else:
            inlier_count = 0
            inlier_ratio = 0.0
            reprojection_error = float("inf")
            coverage_x = 0.0
            coverage_y = 0.0

        if (
            current_to_reference is not None
            and inlier_mask is not None
            and inlier_count >= reference_min_inliers
            and inlier_ratio >= reference_min_inlier_ratio
            and reprojection_error <= reference_max_reprojection_error
            and coverage_x >= reference_min_coverage_x
            and coverage_y >= reference_min_coverage_y
        ):
            reject_reason = "accepted"
            reference_to_current = np.linalg.inv(current_to_reference)
            corners = cv2.perspectiveTransform(
                reference_corners.reshape(1, 4, 2),
                reference_to_current,
            ).reshape(4, 2)
            corners = order_corners(corners).astype(np.float32)
            if detected_corners_are_valid(corners, gray.shape) and geometry_update_is_reasonable(
                corners,
                previous_corners,
                max_scale_step=reference_max_scale_step,
                max_area_step=reference_max_area_step,
            ):
                previous_corners = corners
                accepted_transform = current_to_reference
            else:
                rejected_updates += 1
                reject_reason = "invalid_geometry"
        elif current_to_reference is not None:
            rejected_updates += 1
            reject_reason = reference_reject_reason(
                current_to_reference=current_to_reference,
                inlier_mask=inlier_mask,
                mature_valid_count=mature_valid_count,
                inlier_count=inlier_count,
                inlier_ratio=inlier_ratio,
                reprojection_error=reprojection_error,
                coverage_x=coverage_x,
                coverage_y=coverage_y,
                reference_min_inliers=reference_min_inliers,
                reference_min_inlier_ratio=reference_min_inlier_ratio,
                reference_max_reprojection_error=reference_max_reprojection_error,
                reference_min_coverage_x=reference_min_coverage_x,
                reference_min_coverage_y=reference_min_coverage_y,
            )
        else:
            reject_reason = reference_reject_reason(
                current_to_reference=current_to_reference,
                inlier_mask=inlier_mask,
                mature_valid_count=mature_valid_count,
                inlier_count=inlier_count,
                inlier_ratio=inlier_ratio,
                reprojection_error=reprojection_error,
                coverage_x=coverage_x,
                coverage_y=coverage_y,
                reference_min_inliers=reference_min_inliers,
                reference_min_inlier_ratio=reference_min_inlier_ratio,
                reference_max_reprojection_error=reference_max_reprojection_error,
                reference_min_coverage_x=reference_min_coverage_x,
                reference_min_coverage_y=reference_min_coverage_y,
            )
        trajectory.append(previous_corners)

        keep = valid
        if accepted_transform is not None:
            valid_indices = np.flatnonzero(valid)
            valid_current = next_points.reshape(-1, 2)[valid]
            valid_reference = reference_points.reshape(-1, 2)[valid]
            projected_reference = cv2.perspectiveTransform(
                valid_current.reshape(-1, 1, 2).astype(np.float32),
                accepted_transform,
            ).reshape(-1, 2)
            reprojection_errors = np.linalg.norm(projected_reference - valid_reference, axis=1)
            max_keep_error = max(3.0, reference_max_reprojection_error * 1.5)
            keep = np.zeros_like(valid)
            keep[valid_indices[reprojection_errors <= max_keep_error]] = True

        reference_points = reference_points[keep]
        current_points = next_points[keep].astype(np.float32)
        point_ages = point_ages[keep]
        if accepted_transform is not None:
            point_ages += 1
        if (
            len(current_points) < 140
            or frame_index % feature_refresh == 0
        ) and accepted_transform is not None:
            reference_points, current_points, point_ages = append_reference_points(
                gray,
                previous_corners,
                accepted_transform,
                reference_points,
                current_points,
                point_ages,
            )

        append_tracker_debug_row(
            tracker_debug_rows,
            frame=frame_index,
            accepted=accepted_transform is not None,
            reason=reject_reason,
            corners=previous_corners,
            point_count=len(current_points),
            mature_point_count=int(np.count_nonzero(point_ages >= reference_min_point_age)),
            valid_count=valid_count,
            mature_valid_count=mature_valid_count,
            inlier_count=inlier_count,
            inlier_ratio=inlier_ratio,
            reprojection_error=reprojection_error,
            coverage_x=coverage_x,
            coverage_y=coverage_y,
            rejected_updates=rejected_updates,
        )

        previous_gray = gray
        frame_index += 1
        if frame_count and (frame_index % 60 == 0 or frame_index == frame_count):
            print(
                f"reference-tracked corners {frame_index}/{frame_count} frames "
                f"with {len(current_points)} points "
                f"({int(np.count_nonzero(point_ages >= reference_min_point_age))} mature), "
                f"rejected {rejected_updates} updates",
                file=sys.stderr,
            )

    return trajectory


def estimate_corner_trajectory(
    capture: cv2.VideoCapture,
    fallback_corners: np.ndarray,
    auto_detect: bool,
    tracker: str,
    smooth: float,
    detect_correction: float,
    feature_refresh: int,
    reference_min_inliers: int,
    reference_min_inlier_ratio: float,
    reference_max_reprojection_error: float,
    reference_max_scale_step: float,
    reference_max_area_step: float,
    reference_min_point_age: int,
    reference_min_coverage_x: float,
    reference_min_coverage_y: float,
    tracker_debug_rows: list[dict[str, object]] | None,
) -> list[np.ndarray]:
    if tracker == "reference":
        return estimate_reference_corner_trajectory(
            capture=capture,
            fallback_corners=fallback_corners,
            auto_detect=auto_detect,
            feature_refresh=feature_refresh,
            reference_min_inliers=reference_min_inliers,
            reference_min_inlier_ratio=reference_min_inlier_ratio,
            reference_max_reprojection_error=reference_max_reprojection_error,
            reference_max_scale_step=reference_max_scale_step,
            reference_max_area_step=reference_max_area_step,
            reference_min_point_age=reference_min_point_age,
            reference_min_coverage_x=reference_min_coverage_x,
            reference_min_coverage_y=reference_min_coverage_y,
            tracker_debug_rows=tracker_debug_rows,
        )

    frame_count = int(capture.get(cv2.CAP_PROP_FRAME_COUNT) or 0)
    trajectory: list[np.ndarray] = []
    previous_gray: np.ndarray | None = None
    previous_points: np.ndarray | None = None
    previous_corners: np.ndarray | None = None
    frame_index = 0

    while True:
        ok, frame = capture.read()
        if not ok:
            break

        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        detected_corners = detect_screen_corners(frame) if auto_detect else fallback_corners
        predicted_corners = None
        tracked_points = None
        inliers = 0

        if tracker == "flow" and previous_gray is not None and previous_corners is not None:
            predicted_corners, tracked_points, inliers = flow_predict_corners(
                previous_gray,
                gray,
                previous_points,
                previous_corners,
            )

        if previous_corners is None:
            corners = detected_corners if detected_corners is not None else fallback_corners
        elif predicted_corners is not None:
            if detected_corners is not None:
                corners = (predicted_corners * (1.0 - detect_correction)) + (
                    detected_corners * detect_correction
                )
            else:
                corners = predicted_corners
        elif detected_corners is not None:
            corners = detected_corners
        else:
            corners = previous_corners

        if previous_corners is not None and smooth:
            corners = (previous_corners * smooth) + (corners * (1.0 - smooth))

        corners = order_corners(corners)
        trajectory.append(corners.astype(np.float32))

        previous_gray = gray
        previous_corners = corners.astype(np.float32)
        if tracker == "flow":
            should_refresh = (
                tracked_points is None
                or len(tracked_points) < 80
                or inliers < 60
                or frame_index % feature_refresh == 0
            )
            previous_points = select_tracking_points(gray, previous_corners) if should_refresh else tracked_points

        frame_index += 1
        if frame_count and (frame_index % 60 == 0 or frame_index == frame_count):
            print(f"estimated corners {frame_index}/{frame_count} frames", file=sys.stderr)

    return trajectory


def centered_window_filter(trajectory: np.ndarray, window: int, reducer: str) -> np.ndarray:
    if window <= 1 or len(trajectory) < 3:
        return trajectory

    radius = window // 2
    pad_width = [(radius, radius), *[(0, 0) for _ in range(trajectory.ndim - 1)]]
    padded = np.pad(trajectory, pad_width, mode="edge")
    filtered = np.empty_like(trajectory)
    for index in range(len(trajectory)):
        chunk = padded[index : index + window]
        if reducer == "median":
            filtered[index] = np.median(chunk, axis=0)
        elif reducer == "mean":
            filtered[index] = np.mean(chunk, axis=0)
        else:
            raise ValueError(f"unknown reducer: {reducer}")
    return filtered


def smooth_corner_trajectory(
    trajectory: list[np.ndarray],
    median_window: int,
    average_window: int,
) -> list[np.ndarray]:
    points = np.asarray(trajectory, dtype=np.float32)
    if len(points) == 0:
        return []
    points = centered_window_filter(points, median_window, "median")
    points = centered_window_filter(points, average_window, "mean")
    return [order_corners(corners).astype(np.float32) for corners in points]


def select_reference_points(gray: np.ndarray) -> np.ndarray | None:
    margin_x = max(20, gray.shape[1] // 50)
    margin_y = max(20, gray.shape[0] // 50)
    mask = np.zeros(gray.shape, dtype=np.uint8)
    mask[margin_y : gray.shape[0] - margin_y, margin_x : gray.shape[1] - margin_x] = 255
    points = cv2.goodFeaturesToTrack(
        gray,
        maxCorners=1200,
        qualityLevel=0.004,
        minDistance=9,
        mask=mask,
        blockSize=7,
    )
    if points is None or len(points) < 20:
        return None
    return points.astype(np.float32)


def transform_motion_components(transform: np.ndarray | None) -> dict[str, float]:
    if transform is None:
        return {
            "translation_x": float("nan"),
            "translation_y": float("nan"),
            "rotation_deg": float("nan"),
            "scale_x": float("nan"),
            "scale_y": float("nan"),
            "scale_avg": float("nan"),
            "perspective_x": float("nan"),
            "perspective_y": float("nan"),
        }

    matrix = transform.astype(np.float64)
    a = matrix[0, 0]
    b = matrix[0, 1]
    c = matrix[1, 0]
    d = matrix[1, 1]
    scale_x = float(np.hypot(a, c))
    scale_y = float(np.hypot(b, d))
    return {
        "translation_x": float(matrix[0, 2]),
        "translation_y": float(matrix[1, 2]),
        "rotation_deg": float(np.degrees(np.arctan2(c, a))),
        "scale_x": scale_x,
        "scale_y": scale_y,
        "scale_avg": float((scale_x + scale_y) * 0.5),
        "perspective_x": float(matrix[2, 0]),
        "perspective_y": float(matrix[2, 1]),
    }


def similarity_transform_from_components(
    translation_x: float,
    translation_y: float,
    rotation_deg: float,
    scale: float,
) -> np.ndarray:
    angle = np.radians(rotation_deg)
    cos_value = float(np.cos(angle) * scale)
    sin_value = float(np.sin(angle) * scale)
    return np.array(
        [
            [cos_value, -sin_value, translation_x],
            [sin_value, cos_value, translation_y],
            [0.0, 0.0, 1.0],
        ],
        dtype=np.float32,
    )


def step_limited_value(previous: float, target: float, max_step: float) -> float:
    if max_step <= 0:
        return target
    return previous + float(np.clip(target - previous, -max_step, max_step))


def smooth_residual_affine_transform(
    previous_transform: np.ndarray,
    measured_transform: np.ndarray,
    smooth: float,
    max_translation_step: float,
    max_rotation_step_deg: float,
    max_scale_step: float,
) -> np.ndarray:
    if (
        smooth <= 0
        and max_translation_step <= 0
        and max_rotation_step_deg <= 0
        and max_scale_step <= 0
    ):
        return measured_transform

    previous = transform_motion_components(previous_transform)
    measured = transform_motion_components(measured_transform)

    previous_scale = float(previous["scale_avg"])
    measured_scale = float(measured["scale_avg"])

    target_tx = float(previous["translation_x"]) * smooth + float(measured["translation_x"]) * (
        1.0 - smooth
    )
    target_ty = float(previous["translation_y"]) * smooth + float(measured["translation_y"]) * (
        1.0 - smooth
    )
    target_rotation = float(previous["rotation_deg"]) * smooth + float(
        measured["rotation_deg"]
    ) * (1.0 - smooth)
    target_scale = previous_scale * smooth + measured_scale * (1.0 - smooth)

    translation_x = step_limited_value(
        float(previous["translation_x"]),
        target_tx,
        max_translation_step,
    )
    translation_y = step_limited_value(
        float(previous["translation_y"]),
        target_ty,
        max_translation_step,
    )
    rotation_deg = step_limited_value(
        float(previous["rotation_deg"]),
        target_rotation,
        max_rotation_step_deg,
    )
    scale = step_limited_value(previous_scale, target_scale, max_scale_step)
    return similarity_transform_from_components(translation_x, translation_y, rotation_deg, scale)


def smooth_residual_affine_trajectory(
    transforms: list[np.ndarray],
    median_window: int,
    average_window: int,
) -> list[np.ndarray]:
    if not transforms:
        return []

    components = np.asarray(
        [
            [
                transform_motion_components(transform)["translation_x"],
                transform_motion_components(transform)["translation_y"],
                transform_motion_components(transform)["rotation_deg"],
                transform_motion_components(transform)["scale_avg"],
            ]
            for transform in transforms
        ],
        dtype=np.float32,
    )
    components = centered_window_filter(components, median_window, "median")
    components = centered_window_filter(components, average_window, "mean")
    return [
        similarity_transform_from_components(
            translation_x=float(row[0]),
            translation_y=float(row[1]),
            rotation_deg=float(row[2]),
            scale=float(row[3]),
        )
        for row in components
    ]


def add_applied_alignment_components(row: dict[str, object], transform: np.ndarray) -> None:
    components = transform_motion_components(transform)
    for key, value in components.items():
        row[f"applied_{key}"] = value


def alignment_inlier_coverage(
    reference_points: np.ndarray,
    inlier_mask: np.ndarray | None,
    width: int,
    height: int,
) -> tuple[float, float]:
    if inlier_mask is None:
        return 0.0, 0.0
    inliers = inlier_mask.reshape(-1).astype(bool)
    if int(inliers.sum()) < 2:
        return 0.0, 0.0

    points = reference_points.reshape(-1, 2)[inliers]
    lower = np.percentile(points, 5, axis=0)
    upper = np.percentile(points, 95, axis=0)
    coverage = np.maximum(upper - lower, 0.0)
    return float(coverage[0] / max(1, width)), float(coverage[1] / max(1, height))


def alignment_median_reprojection_error(
    current_points: np.ndarray,
    reference_points: np.ndarray,
    transform: np.ndarray,
    inlier_mask: np.ndarray,
) -> float:
    inliers = inlier_mask.reshape(-1).astype(bool)
    if not np.any(inliers):
        return float("inf")
    projected = cv2.perspectiveTransform(
        current_points[inliers].reshape(-1, 1, 2).astype(np.float32),
        transform.astype(np.float32),
    ).reshape(-1, 2)
    errors = np.linalg.norm(projected - reference_points[inliers], axis=1)
    return float(np.median(errors))


def empty_alignment_debug(
    reason: str,
    motion: str,
    reference_point_count: int,
    valid_count: int = 0,
) -> dict[str, object]:
    row: dict[str, object] = {
        "accepted": False,
        "reason": reason,
        "motion": motion,
        "reference_point_count": reference_point_count,
        "valid_count": valid_count,
        "inlier_count": 0,
        "inlier_ratio": 0.0,
        "coverage_x": 0.0,
        "coverage_y": 0.0,
        "reprojection_error": float("inf"),
    }
    row.update(transform_motion_components(None))
    return row


def estimate_reference_alignment(
    reference_gray: np.ndarray,
    gray: np.ndarray,
    reference_points: np.ndarray | None,
    motion: str,
    min_inliers: int,
    min_inlier_ratio: float,
    min_coverage_x: float,
    min_coverage_y: float,
    max_reprojection_error: float,
    max_translation: float,
    max_rotation_deg: float,
    max_scale_delta: float,
) -> tuple[np.ndarray | None, dict[str, object]]:
    if reference_points is None or len(reference_points) < 20:
        return None, empty_alignment_debug(
            reason="not_enough_reference_points",
            motion=motion,
            reference_point_count=0 if reference_points is None else len(reference_points),
        )

    current_points, status, _ = cv2.calcOpticalFlowPyrLK(
        reference_gray,
        gray,
        reference_points,
        None,
        winSize=(41, 41),
        maxLevel=4,
        criteria=(cv2.TERM_CRITERIA_EPS | cv2.TERM_CRITERIA_COUNT, 60, 0.001),
    )
    if current_points is None or status is None:
        return None, empty_alignment_debug(
            reason="flow_failed",
            motion=motion,
            reference_point_count=len(reference_points),
        )

    reference_back, back_status, _ = cv2.calcOpticalFlowPyrLK(
        gray,
        reference_gray,
        current_points,
        None,
        winSize=(41, 41),
        maxLevel=4,
        criteria=(cv2.TERM_CRITERIA_EPS | cv2.TERM_CRITERIA_COUNT, 60, 0.001),
    )
    if reference_back is None or back_status is None:
        return None, empty_alignment_debug(
            reason="backflow_failed",
            motion=motion,
            reference_point_count=len(reference_points),
        )

    forward_ok = status.reshape(-1).astype(bool)
    backward_ok = back_status.reshape(-1).astype(bool)
    round_trip_error = np.linalg.norm(
        reference_points.reshape(-1, 2) - reference_back.reshape(-1, 2),
        axis=1,
    )
    valid = forward_ok & backward_ok & (round_trip_error < 1.5)
    reference_good = reference_points.reshape(-1, 2)[valid]
    current_good = current_points.reshape(-1, 2)[valid]
    valid_count = len(reference_good)
    if len(reference_good) < 20:
        return None, empty_alignment_debug(
            reason="not_enough_valid_points",
            motion=motion,
            reference_point_count=len(reference_points),
            valid_count=valid_count,
        )

    if motion == "homography":
        transform, inlier_mask = cv2.findHomography(current_good, reference_good, cv2.RANSAC, 2.0)
        if transform is None or inlier_mask is None:
            return None, empty_alignment_debug(
                reason="homography_failed",
                motion=motion,
                reference_point_count=len(reference_points),
                valid_count=valid_count,
            )
        if int(inlier_mask.sum()) < 20:
            return None, empty_alignment_debug(
                reason="too_few_inliers",
                motion=motion,
                reference_point_count=len(reference_points),
                valid_count=valid_count,
            )
        transform = transform.astype(np.float32)
    else:
        affine, inlier_mask = cv2.estimateAffinePartial2D(
            current_good,
            reference_good,
            method=cv2.RANSAC,
            ransacReprojThreshold=2.0,
            maxIters=3000,
            confidence=0.995,
        )
        if affine is None or inlier_mask is None:
            return None, empty_alignment_debug(
                reason="affine_failed",
                motion=motion,
                reference_point_count=len(reference_points),
                valid_count=valid_count,
            )
        if int(inlier_mask.sum()) < 20:
            return None, empty_alignment_debug(
                reason="too_few_inliers",
                motion=motion,
                reference_point_count=len(reference_points),
                valid_count=valid_count,
            )
        transform = np.eye(3, dtype=np.float32)
        transform[:2] = affine.astype(np.float32)

    inlier_count = int(inlier_mask.sum())
    debug_row: dict[str, object] = {
        "accepted": True,
        "reason": "accepted",
        "motion": motion,
        "reference_point_count": len(reference_points),
        "valid_count": valid_count,
        "inlier_count": inlier_count,
        "inlier_ratio": inlier_count / max(1, valid_count),
        "reprojection_error": alignment_median_reprojection_error(
            current_good,
            reference_good,
            transform,
            inlier_mask,
        ),
    }
    coverage_x, coverage_y = alignment_inlier_coverage(
        reference_good,
        inlier_mask,
        width=gray.shape[1],
        height=gray.shape[0],
    )
    debug_row["coverage_x"] = coverage_x
    debug_row["coverage_y"] = coverage_y
    components = transform_motion_components(transform)
    debug_row.update(components)

    translation = float(
        np.hypot(
            float(components["translation_x"]),
            float(components["translation_y"]),
        )
    )
    scale_delta = abs(float(components["scale_avg"]) - 1.0)
    reject_reason = None
    if inlier_count < min_inliers:
        reject_reason = "too_few_inliers"
    elif float(debug_row["inlier_ratio"]) < min_inlier_ratio:
        reject_reason = "low_inlier_ratio"
    elif coverage_x < min_coverage_x:
        reject_reason = "low_coverage_x"
    elif coverage_y < min_coverage_y:
        reject_reason = "low_coverage_y"
    elif (
        max_reprojection_error > 0
        and float(debug_row["reprojection_error"]) > max_reprojection_error
    ):
        reject_reason = "high_reprojection_error"
    elif max_translation > 0 and translation > max_translation:
        reject_reason = "large_translation"
    elif max_rotation_deg > 0 and abs(float(components["rotation_deg"])) > max_rotation_deg:
        reject_reason = "large_rotation"
    elif max_scale_delta > 0 and scale_delta > max_scale_delta:
        reject_reason = "large_scale_delta"

    if reject_reason is not None:
        debug_row["accepted"] = False
        debug_row["reason"] = reject_reason
        return None, debug_row
    return transform, debug_row


def weighted_median(values: np.ndarray, weights: np.ndarray) -> float:
    if len(values) == 0:
        return float("nan")
    order = np.argsort(values)
    sorted_values = values[order]
    sorted_weights = weights[order]
    midpoint = sorted_weights.sum() * 0.5
    return float(sorted_values[np.searchsorted(np.cumsum(sorted_weights), midpoint)])


def line_roll_mask(
    shape: tuple[int, ...],
    top_fraction: float,
    right_fraction: float,
    bottom_fraction: float,
    ignore_top_fraction: float,
) -> np.ndarray:
    height, width = shape[:2]
    mask = np.zeros((height, width), dtype=np.uint8)
    if top_fraction:
        mask[: int(round(height * top_fraction)), :] = 255
    if right_fraction:
        mask[:, int(round(width * (1.0 - right_fraction))) :] = 255
    if bottom_fraction:
        mask[int(round(height * (1.0 - bottom_fraction))) :, :] = 255
    if ignore_top_fraction:
        mask[: int(round(height * ignore_top_fraction)), :] = 0
    return mask


def normalize_line_angle_degrees(angle: float) -> float:
    while angle <= -90.0:
        angle += 180.0
    while angle > 90.0:
        angle -= 180.0
    return angle


def hough_line_candidates(
    frame: np.ndarray,
    mask: np.ndarray,
    angle_limit: float,
) -> list[dict[str, object]]:
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    masked = cv2.bitwise_and(gray, gray, mask=mask)
    edges = cv2.Canny(masked, 60, 160)
    min_line_length = max(140, gray.shape[1] // 10)
    lines = cv2.HoughLinesP(
        edges,
        1,
        np.pi / 180.0,
        threshold=110,
        minLineLength=min_line_length,
        maxLineGap=18,
    )
    candidates: list[dict[str, object]] = []
    if lines is None:
        return candidates

    for x1, y1, x2, y2 in lines.reshape(-1, 4):
        length = float(np.hypot(x2 - x1, y2 - y1))
        if length < min_line_length:
            continue
        angle = normalize_line_angle_degrees(
            float(np.degrees(np.arctan2(y2 - y1, x2 - x1)))
        )
        if abs(angle) > angle_limit:
            continue
        candidates.append({"angle": angle, "length": length})
    return candidates


def contour_line_candidates(
    frame: np.ndarray,
    mask: np.ndarray,
    angle_limit: float,
    horizontal_kernel: int,
    max_thickness: int,
) -> list[dict[str, object]]:
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    masked = cv2.bitwise_and(gray, gray, mask=mask)
    blurred = cv2.GaussianBlur(masked, (3, 3), 0)
    edges = cv2.Canny(blurred, 60, 160)
    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (horizontal_kernel, 1))
    horizontal = cv2.morphologyEx(edges, cv2.MORPH_OPEN, kernel)
    contours, _ = cv2.findContours(horizontal, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    min_line_length = max(180, gray.shape[1] // 8)
    candidates: list[dict[str, object]] = []
    for contour in contours:
        if len(contour) < 2:
            continue
        (_, _), (rect_width, rect_height), rect_angle = cv2.minAreaRect(contour)
        long_side = float(max(rect_width, rect_height))
        short_side = float(min(rect_width, rect_height))
        if long_side < min_line_length or short_side > max_thickness:
            continue

        angle = float(rect_angle)
        if rect_width < rect_height:
            angle += 90.0
        angle = normalize_line_angle_degrees(angle)
        if abs(angle) > angle_limit:
            continue
        candidates.append({"angle": angle, "length": long_side})
    return candidates


def binary_foreground_mask(
    frame: np.ndarray,
    mask: np.ndarray,
    white_threshold: int,
    background_percentile: float,
    dark_margin: float,
    saturation_threshold: int,
) -> np.ndarray:
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
    masked_gray = gray[mask > 0]
    if masked_gray.size:
        background_level = min(
            float(white_threshold),
            float(np.percentile(masked_gray, background_percentile)),
        )
    else:
        background_level = float(np.percentile(gray, background_percentile))
    dark_threshold = max(0.0, background_level - dark_margin)
    color_threshold = max(0.0, background_level - (dark_margin * 0.5))
    foreground = np.where(
        (gray < dark_threshold)
        | ((hsv[:, :, 1] > saturation_threshold) & (gray < color_threshold)),
        255,
        0,
    ).astype(np.uint8)
    return cv2.bitwise_and(foreground, foreground, mask=mask)


def binary_horizontal_edge_mask(foreground: np.ndarray, horizontal_kernel: int) -> np.ndarray:
    boundary_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (3, 3))
    boundary = cv2.morphologyEx(foreground, cv2.MORPH_GRADIENT, boundary_kernel)
    close_width = max(3, horizontal_kernel // 4)
    close_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (close_width, 3))
    connected = cv2.morphologyEx(boundary, cv2.MORPH_CLOSE, close_kernel)
    line_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (horizontal_kernel, 3))
    return cv2.morphologyEx(connected, cv2.MORPH_OPEN, line_kernel)


def binary_contour_line_candidates(
    frame: np.ndarray,
    mask: np.ndarray,
    angle_limit: float,
    horizontal_kernel: int,
    max_thickness: int,
    white_threshold: int,
    background_percentile: float,
    dark_margin: float,
    saturation_threshold: int,
) -> list[dict[str, object]]:
    full_mask = np.full(mask.shape, 255, dtype=np.uint8)
    full_foreground = binary_foreground_mask(
        frame,
        full_mask,
        white_threshold=white_threshold,
        background_percentile=background_percentile,
        dark_margin=dark_margin,
        saturation_threshold=saturation_threshold,
    )
    candidates = binary_component_line_candidates(
        full_foreground,
        selection_mask=mask,
        angle_limit=angle_limit,
        min_line_length=max(180, frame.shape[1] // 8),
        min_area=frame.shape[0] * frame.shape[1] * 0.002,
        min_short_side=max(28.0, float(max_thickness)),
    )
    foreground = cv2.bitwise_and(full_foreground, full_foreground, mask=mask)
    horizontal = binary_horizontal_edge_mask(foreground, horizontal_kernel=horizontal_kernel)
    contours, _ = cv2.findContours(horizontal, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    min_line_length = max(180, frame.shape[1] // 8)
    for contour in contours:
        if len(contour) < 2:
            continue
        (_, _), (rect_width, rect_height), rect_angle = cv2.minAreaRect(contour)
        long_side = float(max(rect_width, rect_height))
        short_side = float(min(rect_width, rect_height))
        if long_side < min_line_length or short_side > max_thickness:
            continue

        angle = float(rect_angle)
        if rect_width < rect_height:
            angle += 90.0
        angle = normalize_line_angle_degrees(angle)
        if abs(angle) > angle_limit:
            continue
        candidates.append({"angle": angle, "length": long_side})
    return candidates


def binary_component_line_candidates(
    foreground: np.ndarray,
    selection_mask: np.ndarray,
    angle_limit: float,
    min_line_length: int,
    min_area: float,
    min_short_side: float,
) -> list[dict[str, object]]:
    contours, _ = cv2.findContours(foreground, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    height, width = foreground.shape[:2]
    candidates: list[dict[str, object]] = []
    for contour in contours:
        if len(contour) < 2:
            continue
        area = float(cv2.contourArea(contour))
        if area < min_area:
            continue

        x, y, box_width, box_height = cv2.boundingRect(contour)
        if np.count_nonzero(selection_mask[y : y + box_height, x : x + box_width]) == 0:
            continue
        touches_frame = (
            x <= 1
            or y <= 1
            or x + box_width >= width - 1
            or y + box_height >= height - 1
        )
        if touches_frame and (box_width > width * 0.90 or box_height > height * 0.90):
            continue

        (_, _), (rect_width, rect_height), rect_angle = cv2.minAreaRect(contour)
        long_side = float(max(rect_width, rect_height))
        short_side = float(min(rect_width, rect_height))
        if long_side < min_line_length or short_side < min_short_side:
            continue

        rect_area = max(float(rect_width * rect_height), 1.0)
        fill_ratio = area / rect_area
        aspect_ratio = long_side / max(short_side, 1.0)
        if fill_ratio < 0.35 or aspect_ratio < 1.2:
            continue

        angle = float(rect_angle)
        if rect_width < rect_height:
            angle += 90.0
        angle = normalize_line_angle_degrees(angle)
        if abs(angle) > angle_limit:
            continue
        candidates.append({"angle": angle, "length": long_side * min(fill_ratio, 1.0)})
    return candidates


def estimate_line_roll_angle(
    frame: np.ndarray,
    detector: str,
    full_mask: bool,
    top_fraction: float,
    right_fraction: float,
    bottom_fraction: float,
    ignore_top_fraction: float,
    min_segments: int,
    min_total_length: int,
    cluster_deg: float,
    horizontal_kernel: int,
    max_thickness: int,
    white_threshold: int,
    background_percentile: float,
    dark_margin: float,
    saturation_threshold: int,
) -> tuple[float | None, int, float]:
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    if full_mask:
        mask = np.full(gray.shape, 255, dtype=np.uint8)
        if ignore_top_fraction:
            mask[: int(round(gray.shape[0] * ignore_top_fraction)), :] = 0
    else:
        mask = line_roll_mask(
            gray.shape,
            top_fraction,
            right_fraction,
            bottom_fraction,
            ignore_top_fraction,
        )
    if detector == "binary-contour":
        candidates = binary_contour_line_candidates(
            frame,
            mask,
            angle_limit=3.0,
            horizontal_kernel=horizontal_kernel,
            max_thickness=max_thickness,
            white_threshold=white_threshold,
            background_percentile=background_percentile,
            dark_margin=dark_margin,
            saturation_threshold=saturation_threshold,
        )
    elif detector == "contour":
        candidates = contour_line_candidates(
            frame,
            mask,
            angle_limit=3.0,
            horizontal_kernel=horizontal_kernel,
            max_thickness=max_thickness,
        )
    else:
        candidates = hough_line_candidates(frame, mask, angle_limit=3.0)

    if len(candidates) < min_segments:
        total_length = sum(float(candidate["length"]) for candidate in candidates)
        return None, len(candidates), float(total_length)

    angle_values = np.asarray([candidate["angle"] for candidate in candidates], dtype=np.float32)
    weight_values = np.asarray([candidate["length"] for candidate in candidates], dtype=np.float32)
    dominant_angle = weighted_median(angle_values, weight_values)
    inlier_mask = np.abs(angle_values - dominant_angle) <= cluster_deg
    angle_values = angle_values[inlier_mask]
    weight_values = weight_values[inlier_mask]
    total_length = float(weight_values.sum())
    if len(angle_values) < min_segments:
        return None, int(len(angle_values)), total_length
    if total_length < min_total_length:
        return None, int(len(angle_values)), total_length

    return weighted_median(angle_values, weight_values), int(len(angle_values)), total_length


def update_line_roll_angle(
    previous_angle: float | None,
    measured_angle: float,
    max_correction: float,
    max_step: float,
    smooth: float,
) -> float:
    target = float(np.clip(measured_angle, -max_correction, max_correction))
    if previous_angle is None:
        return target

    smoothed = previous_angle * smooth + target * (1.0 - smooth)
    if max_step > 0:
        smoothed = previous_angle + float(np.clip(smoothed - previous_angle, -max_step, max_step))
    return float(np.clip(smoothed, -max_correction, max_correction))


def apply_roll_correction(frame: np.ndarray, angle: float) -> np.ndarray:
    height, width = frame.shape[:2]
    center = ((width - 1) / 2.0, (height - 1) / 2.0)
    transform = cv2.getRotationMatrix2D(center, angle, 1.0)
    return cv2.warpAffine(
        frame,
        transform,
        (width, height),
        flags=cv2.INTER_CUBIC,
        borderMode=cv2.BORDER_REPLICATE,
    )


def warp_screen_frame(
    frame: np.ndarray,
    frame_index: int,
    fallback_corners: np.ndarray,
    fallback_transform: np.ndarray,
    destination_corners: np.ndarray,
    corner_trajectory: list[np.ndarray] | None,
    last_corners: np.ndarray | None,
    width: int,
    height: int,
    smooth: float,
    auto_detect: bool,
    crop_left: float,
    crop_top: float,
    crop_right: float,
    crop_bottom: float,
) -> tuple[np.ndarray, np.ndarray | None]:
    if corner_trajectory is not None:
        source_corners = corner_trajectory[min(frame_index, len(corner_trajectory) - 1)]
        transform = cv2.getPerspectiveTransform(source_corners, destination_corners)
    elif auto_detect:
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
    return warped, last_corners


def reference_frame_alignment_debug(
    frame_index: int,
    reference_motion: str,
    reference_points: np.ndarray | None,
    width: int,
    height: int,
) -> dict[str, object]:
    point_count = 0 if reference_points is None else len(reference_points)
    debug_row: dict[str, object] = {
        "frame": frame_index,
        "accepted": True,
        "reason": "reference_frame",
        "motion": reference_motion,
        "reference_point_count": point_count,
        "valid_count": point_count,
        "inlier_count": point_count,
        "inlier_ratio": 1.0 if point_count else 0.0,
        "coverage_x": 0.0,
        "coverage_y": 0.0,
        "reprojection_error": 0.0,
    }
    if reference_points is not None:
        mask = np.ones((len(reference_points), 1), dtype=np.uint8)
        coverage_x, coverage_y = alignment_inlier_coverage(
            reference_points.reshape(-1, 2),
            mask,
            width=width,
            height=height,
        )
        debug_row["coverage_x"] = coverage_x
        debug_row["coverage_y"] = coverage_y
    debug_row.update(transform_motion_components(np.eye(3, dtype=np.float32)))
    return debug_row


def estimate_residual_alignment_trajectory(
    capture: cv2.VideoCapture,
    fallback_corners: np.ndarray,
    fallback_transform: np.ndarray,
    destination_corners: np.ndarray,
    corner_trajectory: list[np.ndarray] | None,
    width: int,
    height: int,
    smooth: float,
    auto_detect: bool,
    crop_left: float,
    crop_top: float,
    crop_right: float,
    crop_bottom: float,
    reference_motion: str,
    reference_align_min_inliers: int,
    reference_align_min_inlier_ratio: float,
    reference_align_min_coverage_x: float,
    reference_align_min_coverage_y: float,
    reference_align_max_reprojection_error: float,
    reference_align_max_translation: float,
    reference_align_max_rotation_deg: float,
    reference_align_max_scale_delta: float,
    median_window: int,
    average_window: int,
) -> tuple[list[np.ndarray], list[dict[str, object]], float]:
    frame_count = int(capture.get(cv2.CAP_PROP_FRAME_COUNT) or 0)
    reference_gray: np.ndarray | None = None
    reference_points: np.ndarray | None = None
    last_corners: np.ndarray | None = None
    measured_transforms: list[np.ndarray] = []
    debug_rows: list[dict[str, object]] = []
    previous_transform = np.eye(3, dtype=np.float32)
    processed = 0

    while True:
        ok, frame = capture.read()
        if not ok:
            break

        warped, last_corners = warp_screen_frame(
            frame=frame,
            frame_index=processed,
            fallback_corners=fallback_corners,
            fallback_transform=fallback_transform,
            destination_corners=destination_corners,
            corner_trajectory=corner_trajectory,
            last_corners=last_corners,
            width=width,
            height=height,
            smooth=smooth,
            auto_detect=auto_detect,
            crop_left=crop_left,
            crop_top=crop_top,
            crop_right=crop_right,
            crop_bottom=crop_bottom,
        )
        gray = cv2.cvtColor(warped, cv2.COLOR_BGR2GRAY)
        if reference_gray is None:
            reference_gray = gray
            reference_points = select_reference_points(reference_gray)
            measured_transform = np.eye(3, dtype=np.float32)
            debug_row = reference_frame_alignment_debug(
                frame_index=processed,
                reference_motion=reference_motion,
                reference_points=reference_points,
                width=gray.shape[1],
                height=gray.shape[0],
            )
        else:
            measured_transform, debug_row = estimate_reference_alignment(
                reference_gray,
                gray,
                reference_points,
                reference_motion,
                min_inliers=reference_align_min_inliers,
                min_inlier_ratio=reference_align_min_inlier_ratio,
                min_coverage_x=reference_align_min_coverage_x,
                min_coverage_y=reference_align_min_coverage_y,
                max_reprojection_error=reference_align_max_reprojection_error,
                max_translation=reference_align_max_translation,
                max_rotation_deg=reference_align_max_rotation_deg,
                max_scale_delta=reference_align_max_scale_delta,
            )
            debug_row = {"frame": processed, **debug_row}
            if measured_transform is None:
                measured_transform = previous_transform

        measured_transforms.append(measured_transform)
        previous_transform = measured_transform
        debug_rows.append(debug_row)
        processed += 1
        if frame_count and (processed % 60 == 0 or processed == frame_count):
            print(
                f"precomputed residual alignment {processed}/{frame_count} frames",
                file=sys.stderr,
            )

    filtered_transforms = smooth_residual_affine_trajectory(
        measured_transforms,
        median_window=median_window,
        average_window=average_window,
    )
    accepted_count = sum(1 for row in debug_rows if row["accepted"])
    accept_ratio = accepted_count / max(1, len(debug_rows))
    capture.set(cv2.CAP_PROP_POS_FRAMES, 0)
    return filtered_transforms, debug_rows, accept_ratio


def encode_warped_video(
    capture: cv2.VideoCapture,
    output: Path,
    fallback_corners: np.ndarray,
    corner_trajectory: list[np.ndarray] | None,
    width: int,
    height: int,
    fps: float,
    crf: int,
    preset: str,
    smooth: float,
    median_window: int,
    auto_detect: bool,
    crop_left: float,
    crop_top: float,
    crop_right: float,
    crop_bottom: float,
    reference_align: bool,
    reference_motion: str,
    reference_align_smooth: float,
    reference_align_max_translation_step: float,
    reference_align_max_rotation_step_deg: float,
    reference_align_max_scale_step: float,
    reference_align_filter_window: int,
    reference_align_min_inliers: int,
    reference_align_min_inlier_ratio: float,
    reference_align_min_coverage_x: float,
    reference_align_min_coverage_y: float,
    reference_align_max_reprojection_error: float,
    reference_align_max_translation: float,
    reference_align_max_rotation_deg: float,
    reference_align_max_scale_delta: float,
    reference_align_min_accept_ratio: float,
    line_roll_correction: bool,
    line_detector: str,
    line_full_mask: bool,
    line_mask_top: float,
    line_mask_right: float,
    line_mask_bottom: float,
    line_ignore_top: float,
    line_min_segments: int,
    line_min_total_length: int,
    line_cluster_deg: float,
    line_horizontal_kernel: int,
    line_max_thickness: int,
    line_white_threshold: int,
    line_background_percentile: float,
    line_dark_margin: float,
    line_saturation_threshold: int,
    line_max_correction_deg: float,
    line_max_step_deg: float,
    line_max_measurement_step_deg: float,
    line_smooth: float,
    align_debug_rows: list[dict[str, object]] | None,
) -> int:
    destination_corners = np.array(
        [[0, 0], [width - 1, 0], [width - 1, height - 1], [0, height - 1]],
        dtype=np.float32,
    )
    frame_count = int(capture.get(cv2.CAP_PROP_FRAME_COUNT) or 0)
    last_corners: np.ndarray | None = None
    fallback_transform = cv2.getPerspectiveTransform(fallback_corners, destination_corners)
    reference_gray: np.ndarray | None = None
    reference_points: np.ndarray | None = None
    residual_applied_transform = np.eye(3, dtype=np.float32)
    line_roll_angle: float | None = None
    line_roll_updates = 0
    line_roll_misses = 0
    residual_alignment_trajectory: list[np.ndarray] | None = None
    residual_alignment_globally_disabled = False

    if (
        reference_align
        and reference_motion == "affine"
        and (reference_align_filter_window > 1 or reference_align_min_accept_ratio > 0)
        and not line_roll_correction
    ):
        residual_median_window = median_window if reference_align_filter_window > 1 else 1
        (
            candidate_alignment_trajectory,
            candidate_align_debug_rows,
            residual_accept_ratio,
        ) = estimate_residual_alignment_trajectory(
            capture=capture,
            fallback_corners=fallback_corners,
            fallback_transform=fallback_transform,
            destination_corners=destination_corners,
            corner_trajectory=corner_trajectory,
            width=width,
            height=height,
            smooth=smooth,
            auto_detect=auto_detect,
            crop_left=crop_left,
            crop_top=crop_top,
            crop_right=crop_right,
            crop_bottom=crop_bottom,
            reference_motion=reference_motion,
            reference_align_min_inliers=reference_align_min_inliers,
            reference_align_min_inlier_ratio=reference_align_min_inlier_ratio,
            reference_align_min_coverage_x=reference_align_min_coverage_x,
            reference_align_min_coverage_y=reference_align_min_coverage_y,
            reference_align_max_reprojection_error=reference_align_max_reprojection_error,
            reference_align_max_translation=reference_align_max_translation,
            reference_align_max_rotation_deg=reference_align_max_rotation_deg,
            reference_align_max_scale_delta=reference_align_max_scale_delta,
            median_window=residual_median_window,
            average_window=reference_align_filter_window,
        )
        residual_alignment_enabled = (
            reference_align_min_accept_ratio <= 0
            or residual_accept_ratio >= reference_align_min_accept_ratio
        )
        residual_alignment_globally_disabled = not residual_alignment_enabled
        if residual_alignment_enabled:
            residual_alignment_trajectory = candidate_alignment_trajectory
        if align_debug_rows is not None:
            for row, transform in zip(
                candidate_align_debug_rows,
                candidate_alignment_trajectory,
                strict=True,
            ):
                row["global_accept_ratio"] = residual_accept_ratio
                row["global_enabled"] = residual_alignment_enabled
                if residual_alignment_enabled:
                    add_applied_alignment_components(row, transform)
                else:
                    add_applied_alignment_components(row, np.eye(3, dtype=np.float32))
                align_debug_rows.append(row)

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
            warped, last_corners = warp_screen_frame(
                frame=frame,
                frame_index=processed,
                fallback_corners=fallback_corners,
                fallback_transform=fallback_transform,
                destination_corners=destination_corners,
                corner_trajectory=corner_trajectory,
                last_corners=last_corners,
                width=width,
                height=height,
                smooth=smooth,
                auto_detect=auto_detect,
                crop_left=crop_left,
                crop_top=crop_top,
                crop_right=crop_right,
                crop_bottom=crop_bottom,
            )

            if line_roll_correction:
                measured_angle, segment_count, total_length = estimate_line_roll_angle(
                    warped,
                    detector=line_detector,
                    full_mask=line_full_mask,
                    top_fraction=line_mask_top,
                    right_fraction=line_mask_right,
                    bottom_fraction=line_mask_bottom,
                    ignore_top_fraction=line_ignore_top,
                    min_segments=line_min_segments,
                    min_total_length=line_min_total_length,
                    cluster_deg=line_cluster_deg,
                    horizontal_kernel=line_horizontal_kernel,
                    max_thickness=line_max_thickness,
                    white_threshold=line_white_threshold,
                    background_percentile=line_background_percentile,
                    dark_margin=line_dark_margin,
                    saturation_threshold=line_saturation_threshold,
                )
                if measured_angle is None:
                    line_roll_misses += 1
                    if line_roll_angle is not None:
                        warped = apply_roll_correction(warped, line_roll_angle)
                elif (
                    line_roll_angle is not None
                    and line_max_measurement_step_deg > 0
                    and abs(measured_angle - line_roll_angle) > line_max_measurement_step_deg
                ):
                    line_roll_misses += 1
                    warped = apply_roll_correction(warped, line_roll_angle)
                else:
                    line_roll_angle = update_line_roll_angle(
                        previous_angle=line_roll_angle,
                        measured_angle=measured_angle,
                        max_correction=line_max_correction_deg,
                        max_step=line_max_step_deg,
                        smooth=line_smooth,
                    )
                    warped = apply_roll_correction(warped, line_roll_angle)
                    line_roll_updates += 1

            if residual_alignment_trajectory is not None:
                residual_transform = residual_alignment_trajectory[
                    min(processed, len(residual_alignment_trajectory) - 1)
                ]
                warped = cv2.warpPerspective(
                    warped,
                    residual_transform,
                    (width, height),
                    flags=cv2.INTER_CUBIC,
                    borderMode=cv2.BORDER_REPLICATE,
                )
            elif reference_align and not residual_alignment_globally_disabled:
                gray = cv2.cvtColor(warped, cv2.COLOR_BGR2GRAY)
                if reference_gray is None:
                    reference_gray = gray
                    reference_points = select_reference_points(reference_gray)
                    if align_debug_rows is not None:
                        debug_row = reference_frame_alignment_debug(
                            frame_index=processed,
                            reference_motion=reference_motion,
                            reference_points=reference_points,
                            width=gray.shape[1],
                            height=gray.shape[0],
                        )
                        add_applied_alignment_components(
                            debug_row,
                            np.eye(3, dtype=np.float32),
                        )
                        align_debug_rows.append(debug_row)
                else:
                    residual_transform, align_debug = estimate_reference_alignment(
                        reference_gray,
                        gray,
                        reference_points,
                        reference_motion,
                        min_inliers=reference_align_min_inliers,
                        min_inlier_ratio=reference_align_min_inlier_ratio,
                        min_coverage_x=reference_align_min_coverage_x,
                        min_coverage_y=reference_align_min_coverage_y,
                        max_reprojection_error=reference_align_max_reprojection_error,
                        max_translation=reference_align_max_translation,
                        max_rotation_deg=reference_align_max_rotation_deg,
                        max_scale_delta=reference_align_max_scale_delta,
                    )
                    if residual_transform is not None:
                        if reference_motion == "affine":
                            residual_transform = smooth_residual_affine_transform(
                                previous_transform=residual_applied_transform,
                                measured_transform=residual_transform,
                                smooth=reference_align_smooth,
                                max_translation_step=reference_align_max_translation_step,
                                max_rotation_step_deg=reference_align_max_rotation_step_deg,
                                max_scale_step=reference_align_max_scale_step,
                            )
                        residual_applied_transform = residual_transform
                    if align_debug_rows is not None:
                        if residual_transform is not None:
                            add_applied_alignment_components(align_debug, residual_transform)
                        else:
                            add_applied_alignment_components(
                                align_debug,
                                np.eye(3, dtype=np.float32),
                            )
                        align_debug_rows.append({"frame": processed, **align_debug})
                    if residual_transform is not None:
                        warped = cv2.warpPerspective(
                            warped,
                            residual_transform,
                            (width, height),
                            flags=cv2.INTER_CUBIC,
                            borderMode=cv2.BORDER_REPLICATE,
                        )
            process.stdin.write(warped.tobytes())
            processed += 1
            if frame_count and (processed % 60 == 0 or processed == frame_count):
                if line_roll_correction:
                    angle_text = "none" if line_roll_angle is None else f"{line_roll_angle:.3f} deg"
                    print(
                        f"processed {processed}/{frame_count} frames, "
                        f"line roll {angle_text}, updates {line_roll_updates}, "
                        f"misses {line_roll_misses}",
                        file=sys.stderr,
                    )
                else:
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


def write_tracker_debug_csv(path: Path, rows: list[dict[str, object]]) -> None:
    fieldnames = [
        "frame",
        "accepted",
        "reason",
        "point_count",
        "mature_point_count",
        "valid_count",
        "mature_valid_count",
        "inlier_count",
        "inlier_ratio",
        "reprojection_error",
        "coverage_x",
        "coverage_y",
        "rejected_updates",
        "area",
        "center_x",
        "center_y",
        "top_edge",
        "right_edge",
        "bottom_edge",
        "left_edge",
        "tl_x",
        "tl_y",
        "tr_x",
        "tr_y",
        "br_x",
        "br_y",
        "bl_x",
        "bl_y",
    ]
    with path.open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def write_align_debug_csv(path: Path, rows: list[dict[str, object]]) -> None:
    fieldnames = [
        "frame",
        "accepted",
        "reason",
        "motion",
        "reference_point_count",
        "valid_count",
        "inlier_count",
        "inlier_ratio",
        "coverage_x",
        "coverage_y",
        "reprojection_error",
        "translation_x",
        "translation_y",
        "rotation_deg",
        "scale_x",
        "scale_y",
        "scale_avg",
        "perspective_x",
        "perspective_y",
        "applied_translation_x",
        "applied_translation_y",
        "applied_rotation_deg",
        "applied_scale_x",
        "applied_scale_y",
        "applied_scale_avg",
        "applied_perspective_x",
        "applied_perspective_y",
        "global_accept_ratio",
        "global_enabled",
    ]
    with path.open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def main() -> None:
    args = parse_args()
    apply_reference_profile(args)
    require_ffmpeg()

    source = args.input.resolve()
    capture = open_capture(source)
    output, run_dir = resolve_run_output(args, source)
    if source == output:
        raise SystemExit("input and output must be different files")

    fps = args.fps or float(capture.get(cv2.CAP_PROP_FPS) or 60.0)
    if fps <= 0:
        fps = 60.0

    fallback_corners = args.corners
    auto_detect = fallback_corners is None
    if fallback_corners is None:
        fallback_corners = parse_corners(DEFAULT_FALLBACK_CORNERS)

    with tempfile.TemporaryDirectory() as tmp:
        corner_trajectory = None
        tracker_debug_rows: list[dict[str, object]] | None = (
            [] if args.write_tracker_debug else None
        )
        align_debug_rows: list[dict[str, object]] | None = [] if args.write_align_debug else None
        if auto_detect:
            corner_trajectory = estimate_corner_trajectory(
                capture=capture,
                fallback_corners=fallback_corners,
                auto_detect=auto_detect,
                tracker=args.tracker,
                smooth=args.smooth,
                detect_correction=args.detect_correction,
                feature_refresh=args.feature_refresh,
                reference_min_inliers=args.reference_min_inliers,
                reference_min_inlier_ratio=args.reference_min_inlier_ratio,
                reference_max_reprojection_error=args.reference_max_reprojection_error,
                reference_max_scale_step=args.reference_max_scale_step,
                reference_max_area_step=args.reference_max_area_step,
                reference_min_point_age=args.reference_min_point_age,
                reference_min_coverage_x=args.reference_min_coverage_x,
                reference_min_coverage_y=args.reference_min_coverage_y,
                tracker_debug_rows=tracker_debug_rows,
            )
            capture.release()
            corner_trajectory = smooth_corner_trajectory(
                corner_trajectory,
                median_window=args.median_window,
                average_window=args.trajectory_window,
            )
            capture = open_capture(source)

        silent_video = Path(tmp) / "screen_normalized_silent.mp4"
        processed = encode_warped_video(
            capture=capture,
            output=silent_video,
            fallback_corners=fallback_corners,
            corner_trajectory=corner_trajectory,
            width=args.width,
            height=args.height,
            fps=fps,
            crf=args.crf,
            preset=args.preset,
            smooth=args.smooth,
            median_window=args.median_window,
            auto_detect=auto_detect,
            crop_left=args.crop_left,
            crop_top=args.crop_top,
            crop_right=args.crop_right,
            crop_bottom=args.crop_bottom,
            reference_align=args.reference_align,
            reference_motion=args.reference_motion,
            reference_align_smooth=args.reference_align_smooth,
            reference_align_max_translation_step=args.reference_align_max_translation_step,
            reference_align_max_rotation_step_deg=args.reference_align_max_rotation_step_deg,
            reference_align_max_scale_step=args.reference_align_max_scale_step,
            reference_align_filter_window=args.reference_align_filter_window,
            reference_align_min_inliers=args.reference_align_min_inliers,
            reference_align_min_inlier_ratio=args.reference_align_min_inlier_ratio,
            reference_align_min_coverage_x=args.reference_align_min_coverage_x,
            reference_align_min_coverage_y=args.reference_align_min_coverage_y,
            reference_align_max_reprojection_error=args.reference_align_max_reprojection_error,
            reference_align_max_translation=args.reference_align_max_translation,
            reference_align_max_rotation_deg=args.reference_align_max_rotation_deg,
            reference_align_max_scale_delta=args.reference_align_max_scale_delta,
            reference_align_min_accept_ratio=args.reference_align_min_accept_ratio,
            line_roll_correction=args.line_roll_correction,
            line_detector=args.line_detector,
            line_full_mask=args.line_full_mask,
            line_mask_top=args.line_mask_top,
            line_mask_right=args.line_mask_right,
            line_mask_bottom=args.line_mask_bottom,
            line_ignore_top=args.line_ignore_top,
            line_min_segments=args.line_min_segments,
            line_min_total_length=args.line_min_total_length,
            line_cluster_deg=args.line_cluster_deg,
            line_horizontal_kernel=args.line_horizontal_kernel,
            line_max_thickness=args.line_max_thickness,
            line_white_threshold=args.line_white_threshold,
            line_background_percentile=args.line_background_percentile,
            line_dark_margin=args.line_dark_margin,
            line_saturation_threshold=args.line_saturation_threshold,
            line_max_correction_deg=args.line_max_correction_deg,
            line_max_step_deg=args.line_max_step_deg,
            line_max_measurement_step_deg=args.line_max_measurement_step_deg,
            line_smooth=args.line_smooth,
            align_debug_rows=align_debug_rows,
        )
        mux_audio(silent_video, source, output)

    if tracker_debug_rows is not None:
        tracker_debug_output = run_dir / "tracker_debug.csv"
        write_tracker_debug_csv(tracker_debug_output, tracker_debug_rows)
        print(f"wrote {tracker_debug_output}")
    if align_debug_rows is not None:
        align_debug_output = run_dir / "align_debug.csv"
        write_align_debug_csv(align_debug_output, align_debug_rows)
        print(f"wrote {align_debug_output}")

    print(f"run directory: {run_dir}")
    print(f"wrote {output} from {processed} frames")


if __name__ == "__main__":
    main()
