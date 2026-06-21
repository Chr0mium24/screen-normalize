from __future__ import annotations

import argparse
import sys
from pathlib import Path

from .common import (
    byte_int,
    crop_fraction,
    nonnegative_fraction,
    odd_positive_int,
    parse_corners,
    percentile_float,
    positive_int,
    smoothing_weight,
)


ADVANCED_OPTIONS = {
    "--smooth",
    "--trajectory-window",
    "--median-window",
    "--detect-correction",
    "--feature-refresh",
    "--reference-min-inliers",
    "--reference-min-inlier-ratio",
    "--reference-max-reprojection-error",
    "--reference-max-scale-step",
    "--reference-max-area-step",
    "--reference-min-point-age",
    "--reference-min-coverage-x",
    "--reference-min-coverage-y",
    "--reference-align-smooth",
    "--reference-align-max-translation-step",
    "--reference-align-max-rotation-step-deg",
    "--reference-align-max-scale-step",
    "--reference-align-filter-window",
    "--reference-align-min-inliers",
    "--reference-align-min-inlier-ratio",
    "--reference-align-min-coverage-x",
    "--reference-align-min-coverage-y",
    "--reference-align-max-reprojection-error",
    "--reference-align-max-translation",
    "--reference-align-max-rotation-deg",
    "--reference-align-max-scale-delta",
    "--reference-align-min-accept-ratio",
    "--trajectory-interpolate",
    "--no-trajectory-interpolate",
    "--trajectory-geometry-gate",
    "--no-trajectory-geometry-gate",
    "--line-detector",
    "--line-full-mask",
    "--no-line-full-mask",
    "--line-mask-top",
    "--line-mask-right",
    "--line-mask-bottom",
    "--line-ignore-top",
    "--line-min-segments",
    "--line-min-total-length",
    "--line-cluster-deg",
    "--line-horizontal-kernel",
    "--line-max-thickness",
    "--line-white-threshold",
    "--line-background-percentile",
    "--line-dark-margin",
    "--line-saturation-threshold",
    "--line-max-correction-deg",
    "--line-max-step-deg",
    "--line-max-measurement-step-deg",
    "--line-smooth",
}


def hide_advanced_options(parser: argparse.ArgumentParser) -> None:
    for action in parser._actions:
        if any(option in ADVANCED_OPTIONS for option in action.option_strings):
            action.help = argparse.SUPPRESS


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    raw_args = sys.argv[1:] if argv is None else list(argv)
    show_advanced = "--advanced-help" in raw_args
    if show_advanced:
        raw_args = ["--help" if item == "--advanced-help" else item for item in raw_args]

    parser = argparse.ArgumentParser(
        description="Perspective-correct a filmed monitor into a screen-recording-like video."
    )
    parser.add_argument(
        "--advanced-help",
        action="store_true",
        help="Show internal tracker, alignment, and line-roll tuning options.",
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
        "--write-trajectory-debug",
        action="store_true",
        help="Write raw/interpolated/smoothed corner trajectory diagnostics to trajectory_debug.csv.",
    )
    parser.add_argument(
        "--trajectory-interpolate",
        action=argparse.BooleanOptionalAction,
        default=True,
        help="Interpolate rejected corner observations before trajectory smoothing.",
    )
    parser.add_argument(
        "--trajectory-geometry-gate",
        action=argparse.BooleanOptionalAction,
        default=True,
        help="Reject offline corner observations with sudden area or side-length jumps.",
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
    if not show_advanced:
        hide_advanced_options(parser)
    return parser.parse_args(raw_args)


def apply_reference_profile(args: argparse.Namespace) -> None:
    if args.reference_profile == "dynamic":
        args.reference_min_point_age = 15
        args.median_window = 5
        args.trajectory_window = 31
    elif args.reference_profile == "low-latency":
        args.reference_min_point_age = 1
        args.median_window = 1
        args.trajectory_window = 1
