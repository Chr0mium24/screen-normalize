from __future__ import annotations

import argparse
import csv
from pathlib import Path
from statistics import median
from typing import Any

from screen_normalize.experiments.annotations import load_annotations
from screen_normalize.experiments.evaluation import read_frames, video_metadata, warp_to_screen
from screen_normalize.metrics.detail_preservation import (
    DetailPreservationConfig,
    evaluate_detail_preservation_pair,
)


ROOT = Path(__file__).resolve().parents[2]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Demo reference-based detail preservation metrics.")
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
        default=ROOT / "runs" / "20260714_detail_preservation_demo_scrolling_01",
    )
    parser.add_argument(
        "--markdown",
        type=Path,
        default=ROOT / "doc" / "current" / "paper" / "detail_preservation_demo_2026-07-14.md",
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
        "ssim",
        "gradient_magnitude_similarity",
        "gradient_magnitude_ratio",
        "gradient_log_ratio_abs",
        "edge_f1",
        "laplacian_energy_ratio",
        "laplacian_log_ratio_abs",
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
        "SSIM ↑",
        "Grad sim ↑",
        "Grad ratio ≈1",
        "Edge F1 ↑",
        "Lap ratio ≈1",
        "Abs log Lap ratio ↓",
    ]
    lines = ["| " + " | ".join(headers) + " |", "|---|---:|---:|---:|---:|---:|---:|---:|"]
    for row in rows:
        lines.append(
            "| {method} | {frames} | {ssim:.3f} | {grad_sim:.3f} | {grad:.3f} | "
            "{edge:.3f} | {lap:.3f} | {lap_log:.3f} |".format(
                method=row["method"],
                frames=row["frames"],
                ssim=row["ssim_median"],
                grad_sim=row["gradient_magnitude_similarity_median"],
                grad=row["gradient_magnitude_ratio_median"],
                edge=row["edge_f1_median"],
                lap=row["laplacian_energy_ratio_median"],
                lap_log=row["laplacian_log_ratio_abs_median"],
            )
        )
    return "\n".join(lines)


def write_markdown(
    path: Path,
    original: Path,
    annotations: Path,
    run_dir: Path,
    frames: list[int],
    summaries: list[dict[str, Any]],
) -> None:
    body = f"""# Detail Preservation Demo

Date: 2026-07-14

## Question

This demo checks whether reference-based detail diagnostics can measure preservation of local structure after geometric normalization. It does not measure perceptual restoration quality or moire removal.

## Setup

- Original video: `{original.relative_to(ROOT)}`
- Annotation CSV: `{annotations.relative_to(ROOT)}`
- Normalized outputs: `{run_dir.relative_to(ROOT)}`
- Evaluated frames: `{', '.join(str(frame) for frame in frames)}`
- Per-frame CSV: `runs/20260714_detail_preservation_demo_scrolling_01/detail_preservation_rows.csv`
- Summary CSV: `runs/20260714_detail_preservation_demo_scrolling_01/detail_preservation_summary.csv`

Each annotated original frame is warped with the human screen-corner annotation to form the reference. The metric then compares each method's normalized output against that annotation-warped reference.

## Metrics

- `SSIM`: grayscale structural similarity to the annotation-warped reference.
- `Grad sim`: cosine similarity between Sobel gradient-magnitude maps.
- `Grad ratio`: mean gradient-magnitude ratio, where 1 means matching edge strength.
- `Edge F1`: Canny edge overlap with a one-pixel tolerance.
- `Lap ratio`: Laplacian detail-energy ratio, where 1 means matching local high-frequency detail energy.

## Results

{markdown_table(summaries)}

## Readout

The demo is feasible as a detail-preservation diagnostic. It should be used as supporting evidence that geometric normalization preserves captured local structure, not as a standalone ranking metric for visual restoration.

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
    config = DetailPreservationConfig()
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
            metric_row = evaluate_detail_preservation_pair(reference, normalized_frame, config)
            rows.append({"method": method, "frame": frame, **metric_row})

    summaries = summarize(rows, args.methods)
    write_csv(output_dir / "detail_preservation_rows.csv", rows)
    write_csv(output_dir / "detail_preservation_summary.csv", summaries)
    write_markdown(args.markdown.resolve(), original, annotations_path, run_dir, frames, summaries)
    print(f"Wrote {args.markdown}")
    print(f"Wrote {output_dir / 'detail_preservation_summary.csv'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
