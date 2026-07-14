from __future__ import annotations

import argparse
import csv
from pathlib import Path
from statistics import median
from typing import Any

from screen_normalize.experiments.annotations import load_annotations
from screen_normalize.experiments.evaluation import read_frames, video_metadata, warp_to_screen
from screen_normalize.metrics.frequency_preservation import (
    FrequencyPreservationConfig,
    evaluate_frequency_preservation_pair,
)


ROOT = Path(__file__).resolve().parents[2]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Demo reference-based frequency preservation metrics.")
    parser.add_argument("--original", type=Path, default=ROOT / "inputs" / "scrolling" / "scrolling_01.mp4")
    parser.add_argument("--annotations", type=Path, default=None)
    parser.add_argument(
        "--run-dir",
        type=Path,
        default=ROOT / "runs" / "20260714_small_sample_with_proposal_border" / "scrolling" / "scrolling_01",
    )
    parser.add_argument(
        "--methods",
        nargs="+",
        default=["frame_wise", "optical_flow", "proposal_border"],
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=ROOT / "runs" / "20260714_frequency_preservation_demo_scrolling_01",
    )
    parser.add_argument(
        "--markdown",
        type=Path,
        default=ROOT / "doc" / "current" / "paper" / "frequency_preservation_demo_2026-07-14.md",
    )
    return parser.parse_args()


def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    fields: list[str] = []
    for row in rows:
        fields.extend(key for key in row if key not in fields)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def summarize(rows: list[dict[str, Any]], methods: list[str]) -> list[dict[str, Any]]:
    metric_fields = [
        "log_fft_magnitude_similarity",
        "high_frequency_energy_ratio",
        "high_frequency_log_ratio_abs",
        "orientation_histogram_intersection",
        "band_energy_ratio",
        "band_log_ratio_abs",
    ]
    summaries: list[dict[str, Any]] = []
    for method in methods:
        method_rows = [row for row in rows if row["method"] == method]
        summary: dict[str, Any] = {"method": method, "frames": len(method_rows)}
        for field in metric_fields:
            values = [float(row[field]) for row in method_rows if row.get(field) is not None]
            summary[f"{field}_median"] = median(values) if values else None
        summaries.append(summary)
    return summaries


def markdown_table(rows: list[dict[str, Any]]) -> str:
    headers = [
        "Method",
        "Frames",
        "FFT sim ↑",
        "HF ratio ≈1",
        "Abs log HF ratio ↓",
        "Orient hist ↑",
        "Band ratio ≈1",
        "Abs log band ratio ↓",
    ]
    lines = ["| " + " | ".join(headers) + " |", "|---|---:|---:|---:|---:|---:|---:|---:|"]
    for row in rows:
        lines.append(
            "| {method} | {frames} | {fft:.3f} | {hf:.3f} | {hf_log:.3f} | "
            "{orient:.3f} | {band:.3f} | {band_log:.3f} |".format(
                method=row["method"],
                frames=row["frames"],
                fft=row["log_fft_magnitude_similarity_median"],
                hf=row["high_frequency_energy_ratio_median"],
                hf_log=row["high_frequency_log_ratio_abs_median"],
                orient=row["orientation_histogram_intersection_median"],
                band=row["band_energy_ratio_median"],
                band_log=row["band_log_ratio_abs_median"],
            )
        )
    return "\n".join(lines)


def write_markdown(
    path: Path,
    original: Path,
    annotations: Path,
    run_dir: Path,
    frames: list[int],
    rows: list[dict[str, Any]],
    summaries: list[dict[str, Any]],
) -> None:
    body = f"""# Frequency Preservation Demo

Date: 2026-07-14

## Question

The input videos already contain camera-screen interference and high-frequency texture. This demo checks whether reference-based frequency diagnostics can measure preservation of that captured signal after geometric normalization. It does not measure moire removal.

## Setup

- Original video: `{original.relative_to(ROOT)}`
- Annotation CSV: `{annotations.relative_to(ROOT)}`
- Normalized outputs: `{run_dir.relative_to(ROOT)}`
- Evaluated frames: `{', '.join(str(frame) for frame in frames)}`
- Per-frame CSV: `runs/20260714_frequency_preservation_demo_scrolling_01/frequency_preservation_rows.csv`
- Summary CSV: `runs/20260714_frequency_preservation_demo_scrolling_01/frequency_preservation_summary.csv`

Each annotated original frame is warped with the human screen-corner annotation to form the reference. The metric then compares each method's normalized output against that annotation-warped reference.

## Metrics

- `FFT sim`: cosine similarity between log FFT magnitudes outside the DC region.
- `HF ratio`: high-frequency energy ratio, where 1 means the output preserves the reference high-frequency energy.
- `|log HF ratio|`: symmetric distance from a perfect high-frequency energy ratio.
- `Orient hist`: histogram-intersection similarity between high-frequency orientation spectra.
- `Band ratio`: energy ratio in a broad high-frequency band used as a moire/high-frequency proxy, not a labeled moire mask.

## Results

{markdown_table(summaries)}

## Readout

The demo is feasible as a reference-based preservation diagnostic. The useful quantities are the similarity scores and the ratio distances, not raw frequency direction regularity. This should be framed as signal preservation after geometric normalization, not as moire removal or perceptual restoration quality.

"""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(body, encoding="utf-8")


def main() -> int:
    args = parse_args()
    original = args.original.resolve()
    annotations_path = (args.annotations or original.with_suffix(".csv")).resolve()
    run_dir = args.run_dir.resolve()
    output_dir = args.output_dir.resolve()

    metadata = video_metadata(original)
    annotations = load_annotations(annotations_path, metadata.width, metadata.height)
    frames = [frame for frame in sorted(annotations) if frame > 0]
    original_frames = read_frames(original, frames)

    rows: list[dict[str, Any]] = []
    config = FrequencyPreservationConfig()
    for method in args.methods:
        normalized_video = run_dir / method / "normalized.mp4"
        normalized_meta = video_metadata(normalized_video)
        normalized_frames = read_frames(normalized_video, frames)
        for frame in frames:
            original_frame = original_frames.get(frame)
            normalized_frame = normalized_frames.get(frame)
            if original_frame is None or normalized_frame is None:
                continue
            reference = warp_to_screen(
                original_frame,
                annotations[frame],
                normalized_meta.width,
                normalized_meta.height,
            )
            metric_row = evaluate_frequency_preservation_pair(reference, normalized_frame, config)
            rows.append({"method": method, "frame": frame, **metric_row})

    summaries = summarize(rows, args.methods)
    write_csv(output_dir / "frequency_preservation_rows.csv", rows)
    write_csv(output_dir / "frequency_preservation_summary.csv", summaries)
    write_markdown(args.markdown.resolve(), original, annotations_path, run_dir, frames, rows, summaries)
    print(f"Wrote {args.markdown}")
    print(f"Wrote {output_dir / 'frequency_preservation_summary.csv'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
