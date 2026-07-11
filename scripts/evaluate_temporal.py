#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path

from screen_normalize.metrics.temporal import evaluate_temporal


def main() -> None:
    parser = argparse.ArgumentParser(description="Evaluate corner-trajectory stability for one method.")
    parser.add_argument("estimated_csv", type=Path)
    parser.add_argument("output_dir", type=Path)
    args = parser.parse_args()
    print(evaluate_temporal(args.estimated_csv, args.output_dir)["status"])


if __name__ == "__main__":
    main()

