#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path

from screen_normalize.experiments.pipeline import analyze_clip
from screen_normalize.experiments.run_io import METHOD_IDS, METRIC_IDS, create_analysis_run


def main() -> None:
    parser = argparse.ArgumentParser(description="Run methods, metrics, and an HTML report for one video.")
    parser.add_argument("video", type=Path)
    parser.add_argument("--methods", nargs="+", choices=METHOD_IDS, default=list(METHOD_IDS))
    parser.add_argument("--metrics", nargs="+", choices=METRIC_IDS, default=list(METRIC_IDS))
    parser.add_argument("--run-dir", type=Path)
    parser.add_argument("--reuse-outputs", action="store_true")
    parser.add_argument("--skip-existing", action="store_true")
    args = parser.parse_args()
    run_dir = args.run_dir.resolve() if args.run_dir else create_analysis_run()
    result = analyze_clip(args.video, run_dir, args.methods, args.metrics, reuse_outputs=args.reuse_outputs, skip_existing=args.skip_existing)
    print(f"{result['status']}: {result['report']}")


if __name__ == "__main__":
    main()
