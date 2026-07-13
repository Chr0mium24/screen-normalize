#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import shutil
from pathlib import Path


HISTORICAL_FULL_RUNS = [
    {
        "category": "static",
        "clip": "static_02_000",
        "source": "runs/20260712-172512_analysis/IMG_0974/IMG_0974_000/proposed",
    },
    {
        "category": "scrolling",
        "clip": "scrolling_03_000",
        "source": "runs/20260712-scrolling-segments-rerun/VID20260712165829/VID20260712165829_000/proposed",
    },
    {
        "category": "screen_video",
        "clip": "screen_video_03_000",
        "source": "runs/20260713-screen-video-segments-VID20260712170039/VID20260712170039/VID20260712170039_000/proposed",
    },
    {
        "category": "hard",
        "clip": "hard_01",
        "source": "runs/20260712-181406_analysis/moire/VID20260712170803/proposed",
    },
]


def link_or_copy(source: Path, target: Path) -> None:
    if target.exists():
        return
    try:
        os.link(source, target)
    except OSError:
        shutil.copy2(source, target)


def stage_full_outputs(repo_root: Path, run_dir: Path) -> None:
    target_root = repo_root / run_dir
    for item in HISTORICAL_FULL_RUNS:
        source_dir = repo_root / item["source"]
        if not source_dir.exists():
            raise FileNotFoundError(f"missing historical proposed output: {source_dir}")

        target_dir = target_root / item["category"] / item["clip"] / "proposed"
        target_dir.mkdir(parents=True, exist_ok=True)

        for name in ("estimated_corners.csv", "debug.csv", "align_debug.csv", "method.json"):
            source_file = source_dir / name
            if source_file.exists():
                shutil.copy2(source_file, target_dir / name)

        normalized_video = source_dir / "normalized.mp4"
        if not normalized_video.exists():
            raise FileNotFoundError(f"missing historical normalized video: {normalized_video}")
        link_or_copy(normalized_video, target_dir / "normalized.mp4")

        reuse = {
            "status": "reused",
            "method": "proposed",
            "source_method_dir": item["source"],
            "output_reused": ["normalized.mp4", "estimated_corners.csv"],
            "metrics_recomputed": True,
            "metric_policy": "current code; initialization frame excluded",
        }
        (target_dir / "reuse.json").write_text(
            json.dumps(reuse, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
        )


def main() -> None:
    parser = argparse.ArgumentParser(description="Stage historical full-method outputs for ablation.")
    parser.add_argument("--run-dir", type=Path, default=Path("runs/20260713_ablation"))
    parser.add_argument("--repo-root", type=Path, default=Path(__file__).resolve().parents[3])
    args = parser.parse_args()

    stage_full_outputs(args.repo_root.resolve(), args.run_dir)
    print(f"staged historical full proposed outputs in {args.run_dir}")


if __name__ == "__main__":
    main()
