#!/usr/bin/env python3
# /// script
# dependencies = [
#   "numpy>=2.2.0",
#   "opencv-python-headless>=4.12.0.88",
# ]
# ///

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from screen_normalize.common import clean_path_component, create_run_directory, project_root
from screen_normalize.experiments.evaluation import (
    FrequencyConfig,
    MotionConfig,
    SignalConfig,
    analyze_temporal_stability,
    as_jsonable,
    evaluate_geometry_accuracy,
    evaluate_signal_preservation,
    evaluate_spectral_regularity,
    flatten_summary,
    read_corner_map,
    video_metadata,
    write_dict_csv,
)


def positive_int(value: str) -> int:
    parsed = int(value)
    if parsed <= 0:
        raise argparse.ArgumentTypeError("value must be positive")
    return parsed


def nonnegative_float(value: str) -> float:
    parsed = float(value)
    if parsed < 0:
        raise argparse.ArgumentTypeError("value must be >= 0")
    return parsed


def fraction(value: str) -> float:
    parsed = float(value)
    if not 0.0 <= parsed <= 1.0:
        raise argparse.ArgumentTypeError("value must be between 0 and 1")
    return parsed


def percentile(value: str) -> float:
    parsed = float(value)
    if not 0.0 <= parsed <= 100.0:
        raise argparse.ArgumentTypeError("value must be between 0 and 100")
    return parsed


def byte_int(value: str) -> int:
    parsed = int(value)
    if not 0 <= parsed <= 255:
        raise argparse.ArgumentTypeError("value must be between 0 and 255")
    return parsed


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Evaluate normalized captured-screen videos across temporal, "
            "geometry, signal, and spectral dimensions."
        )
    )
    parser.add_argument(
        "--normalized",
        required=True,
        type=Path,
        help="Normalized output video to evaluate.",
    )
    parser.add_argument(
        "--original",
        type=Path,
        default=None,
        help="Original captured-screen video. Required for signal preservation against GT warps.",
    )
    parser.add_argument(
        "--annotations",
        type=Path,
        default=None,
        help=(
            "Manual source-corner annotations as CSV or JSON. CSV columns: "
            "frame,tl_x,tl_y,tr_x,tr_y,br_x,br_y,bl_x,bl_y."
        ),
    )
    parser.add_argument(
        "--estimated-corners",
        type=Path,
        default=None,
        help=(
            "Estimated source corners from tracker_debug.csv, trajectory_debug.csv, "
            "or a matching annotation CSV/JSON."
        ),
    )
    parser.add_argument(
        "--estimated-prefix",
        default="auto",
        help=(
            "Corner column prefix for --estimated-corners. Use auto, raw_, "
            "interpolated_, smoothed_, or empty string."
        ),
    )
    parser.add_argument("--runs-dir", type=Path, default=None)
    parser.add_argument("--run-name", default=None)
    parser.add_argument(
        "--last-seconds",
        type=nonnegative_float,
        default=2.0,
        help="Also summarize temporal stability on the last N seconds.",
    )
    parser.add_argument("--max-corners", type=positive_int, default=800)
    parser.add_argument("--quality-level", type=fraction, default=0.01)
    parser.add_argument("--min-distance", type=positive_int, default=10)
    parser.add_argument("--min-points", type=positive_int, default=30)
    parser.add_argument("--ransac-threshold", type=nonnegative_float, default=2.0)
    parser.add_argument(
        "--sample-stride",
        type=positive_int,
        default=30,
        help="Default frame stride for signal and FFT sampling.",
    )
    parser.add_argument("--max-signal-frames", type=positive_int, default=120)
    parser.add_argument("--max-frequency-frames", type=positive_int, default=120)
    parser.add_argument("--canny-low", type=byte_int, default=80)
    parser.add_argument("--canny-high", type=byte_int, default=160)
    parser.add_argument("--fft-max-side", type=positive_int, default=720)
    parser.add_argument("--fft-dc-radius", type=fraction, default=0.05)
    parser.add_argument("--fft-peak-percentile", type=percentile, default=99.5)
    parser.add_argument("--fft-min-peak-points", type=positive_int, default=20)
    return parser.parse_args()


def resolve_run_dir(args: argparse.Namespace) -> Path:
    runs_dir = args.runs_dir.resolve() if args.runs_dir else project_root() / "runs"
    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    run_name = args.run_name or f"{timestamp}_{Path(__file__).stem}"
    return create_run_directory(runs_dir, clean_path_component(run_name)).resolve()


def write_optional_csv(path: Path, rows: list[dict[str, object]]) -> str | None:
    if not rows:
        return None
    write_dict_csv(path, rows)
    return str(path)


def main() -> None:
    args = parse_args()
    run_dir = resolve_run_dir(args)

    normalized = args.normalized.resolve()
    original = args.original.resolve() if args.original else None
    annotations = (
        read_corner_map(args.annotations.resolve()) if args.annotations is not None else None
    )
    estimates = (
        read_corner_map(args.estimated_corners.resolve(), prefix=args.estimated_prefix)
        if args.estimated_corners is not None
        else None
    )

    motion_config = MotionConfig(
        max_corners=args.max_corners,
        quality_level=args.quality_level,
        min_distance=args.min_distance,
        min_points=args.min_points,
        ransac_threshold=args.ransac_threshold,
    )
    signal_config = SignalConfig(
        sample_stride=args.sample_stride,
        max_frames=args.max_signal_frames,
        canny_low=args.canny_low,
        canny_high=args.canny_high,
    )
    frequency_config = FrequencyConfig(
        sample_stride=args.sample_stride,
        max_frames=args.max_frequency_frames,
        max_side=args.fft_max_side,
        dc_radius_fraction=args.fft_dc_radius,
        peak_percentile=args.fft_peak_percentile,
        min_peak_points=args.fft_min_peak_points,
    )

    artifacts: dict[str, str | None] = {}
    dimensions: dict[str, dict[str, object]] = {}

    temporal_rows, temporal_summary = analyze_temporal_stability(
        normalized,
        motion_config,
        args.last_seconds,
    )
    dimensions["temporal_stability"] = temporal_summary
    artifacts["temporal_metrics_csv"] = write_optional_csv(
        run_dir / "temporal_metrics.csv",
        temporal_rows,
    )

    if annotations is not None and estimates is not None:
        geometry_meta = video_metadata(original) if original is not None else video_metadata(normalized)
        geometry_rows, geometry_summary = evaluate_geometry_accuracy(
            annotations,
            estimates,
            width=geometry_meta.width,
            height=geometry_meta.height,
        )
    else:
        missing = []
        if annotations is None:
            missing.append("--annotations")
        if estimates is None:
            missing.append("--estimated-corners")
        geometry_rows = []
        geometry_summary = {
            "status": "skipped",
            "reason": f"missing {' and '.join(missing)}",
        }
    dimensions["geometry_accuracy"] = geometry_summary
    artifacts["geometry_metrics_csv"] = write_optional_csv(
        run_dir / "geometry_metrics.csv",
        geometry_rows,
    )

    signal_rows, signal_summary = evaluate_signal_preservation(
        normalized,
        original,
        annotations,
        signal_config,
    )
    dimensions["signal_preservation"] = signal_summary
    artifacts["signal_metrics_csv"] = write_optional_csv(
        run_dir / "signal_metrics.csv",
        signal_rows,
    )

    spectral_rows, spectral_summary = evaluate_spectral_regularity(
        normalized,
        frequency_config,
    )
    dimensions["spectral_regularity"] = spectral_summary
    artifacts["spectral_metrics_csv"] = write_optional_csv(
        run_dir / "spectral_metrics.csv",
        spectral_rows,
    )

    summary_csv = run_dir / "evaluation_summary.csv"
    summary_json = run_dir / "evaluation_summary.json"
    write_dict_csv(summary_csv, flatten_summary(dimensions))
    artifacts["evaluation_summary_csv"] = str(summary_csv)
    artifacts["evaluation_summary_json"] = str(summary_json)

    with summary_json.open("w") as handle:
        json.dump(
            as_jsonable(
                {
                    "generated_at": datetime.now().isoformat(timespec="seconds"),
                    "inputs": {
                        "normalized": str(normalized),
                        "original": str(original) if original is not None else None,
                        "annotations": (
                            str(args.annotations.resolve()) if args.annotations is not None else None
                        ),
                        "estimated_corners": (
                            str(args.estimated_corners.resolve())
                            if args.estimated_corners is not None
                            else None
                        ),
                    },
                    "artifacts": artifacts,
                    "dimensions": dimensions,
                }
            ),
            handle,
            indent=2,
        )
        handle.write("\n")

    print(f"run directory: {run_dir}")
    for label, path in artifacts.items():
        if path is not None:
            print(f"wrote {label}: {path}")
    for dimension, summary in dimensions.items():
        status = summary.get("status")
        reason = summary.get("reason")
        detail = f" ({reason})" if reason else ""
        print(f"{dimension}: {status}{detail}")


if __name__ == "__main__":
    main()
