#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
from pathlib import Path

from screen_normalize.experiments.pipeline import analyze_clip
from screen_normalize.experiments.reporting import render_run_index
from screen_normalize.experiments.run_io import (
    METHOD_IDS,
    METRIC_IDS,
    RUNNABLE_METHOD_IDS,
    create_analysis_run,
    write_csv,
)


VIDEO_SUFFIXES = {".mp4", ".mov", ".mkv"}


def select_videos(input_dir: Path, videos: list[Path] | None, categories: list[str] | None, limit: int) -> list[Path]:
    if videos:
        selected = [path.resolve() for path in videos]
    else:
        roots = [input_dir / category for category in categories] if categories else [path for path in input_dir.iterdir() if path.is_dir() and path.name != "archive"]
        selected = sorted(path.resolve() for root in roots if root.exists() for path in root.iterdir() if path.suffix.lower() in VIDEO_SUFFIXES)
    if categories:
        allowed = set(categories)
        selected = [path for path in selected if path.parent.name in allowed]
    return selected[:limit] if limit > 0 else selected


def main() -> None:
    parser = argparse.ArgumentParser(description="Run the experiment pipeline over selected videos.")
    parser.add_argument("--input", type=Path, default=Path("inputs"))
    parser.add_argument("--videos", nargs="+", type=Path)
    parser.add_argument("--categories", nargs="+")
    parser.add_argument(
        "--methods", nargs="+", choices=RUNNABLE_METHOD_IDS, default=list(METHOD_IDS)
    )
    parser.add_argument("--metrics", nargs="+", choices=METRIC_IDS, default=list(METRIC_IDS))
    parser.add_argument("--limit", type=int, default=0)
    parser.add_argument("--run-dir", type=Path)
    parser.add_argument("--reuse-outputs", action="store_true")
    parser.add_argument("--skip-existing", action="store_true")
    args = parser.parse_args()
    run_dir = args.run_dir.resolve() if args.run_dir else create_analysis_run()
    selected = select_videos(args.input.resolve(), args.videos, args.categories, args.limit)
    if not selected:
        raise SystemExit("no input videos selected")
    records = []
    for video in selected:
        try:
            record = analyze_clip(video, run_dir, args.methods, args.metrics, reuse_outputs=args.reuse_outputs, skip_existing=args.skip_existing)
        except Exception as exc:
            record = {"category": video.parent.name, "clip_id": video.stem, "status": "failed", "reason": f"{type(exc).__name__}: {exc}"}
        records.append(record)
        print(f"[{record['status']}] {record['category']}/{record['clip_id']}")
    batch_path = run_dir / "batch.csv"
    if batch_path.exists():
        with batch_path.open(newline="", encoding="utf-8") as handle:
            existing = list(csv.DictReader(handle))
        current_keys = {(record["category"], record["clip_id"]) for record in records}
        records = [record for record in existing if (record["category"], record["clip_id"]) not in current_keys] + records
    write_csv(batch_path, records)
    index = render_run_index(run_dir, records)
    print(f"run directory: {run_dir}\nindex: {index}")


if __name__ == "__main__":
    main()
