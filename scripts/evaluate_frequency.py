#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path

from screen_normalize.metrics.frequency import evaluate_frequency


def main() -> None:
    parser = argparse.ArgumentParser(description="Evaluate frequency regularity for one normalized video.")
    parser.add_argument("normalized_video", type=Path)
    parser.add_argument("output_dir", type=Path)
    args = parser.parse_args()
    print(evaluate_frequency(args.normalized_video, args.output_dir)["status"])


if __name__ == "__main__":
    main()

