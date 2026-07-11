#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path

from screen_normalize.metrics.geometry import evaluate_geometry


def main() -> None:
    parser = argparse.ArgumentParser(description="Evaluate corner geometry for one clip and method.")
    parser.add_argument("original_video", type=Path)
    parser.add_argument("estimated_csv", type=Path)
    parser.add_argument("output_dir", type=Path)
    parser.add_argument("--annotations", type=Path)
    args = parser.parse_args()
    summary = evaluate_geometry(args.original_video, args.annotations, args.estimated_csv, args.output_dir)
    print(summary["status"])


if __name__ == "__main__":
    main()

