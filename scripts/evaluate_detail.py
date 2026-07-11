#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path

from screen_normalize.metrics.detail import evaluate_detail


def main() -> None:
    parser = argparse.ArgumentParser(description="Evaluate aligned detail preservation for one method.")
    parser.add_argument("normalized_video", type=Path)
    parser.add_argument("original_video", type=Path)
    parser.add_argument("output_dir", type=Path)
    parser.add_argument("--annotations", type=Path)
    args = parser.parse_args()
    print(evaluate_detail(args.normalized_video, args.original_video, args.annotations, args.output_dir)["status"])


if __name__ == "__main__":
    main()

