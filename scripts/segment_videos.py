"""Repackage category input videos into MP4 and split them into ~10s segments.

For each of the five category folders under ``inputs/`` (static, scrolling,
screen_video, weak_border, hard), every source video (e.g. ``.MOV``) is
stream-copied (no re-encode, lossless) into an MP4 container and cut into
segments of roughly the target length. Because stream copy can only cut at
keyframes, segment lengths are approximate and a trailing chunk shorter than
the target length is kept. Segments for one source land in
``inputs/<category>/segments/<source_stem>/`` so each source keeps its own
group.
"""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
from pathlib import Path

SEGMENT_SECONDS = 10
CATEGORIES = ("static", "scrolling", "screen_video", "weak_border", "hard")
SOURCE_SUFFIXES = {".mov", ".mp4", ".mkv", ".m4v", ".avi"}


def probe_duration(video: Path) -> float:
    result = subprocess.run(
        [
            "ffprobe",
            "-v",
            "error",
            "-show_entries",
            "format=duration",
            "-of",
            "json",
            str(video),
        ],
        capture_output=True,
        text=True,
        check=True,
    )
    data = json.loads(result.stdout)
    return float(data["format"]["duration"])


def segment_video(video: Path, out_dir: Path, seconds: int) -> list[Path]:
    stem = video.stem
    target_dir = out_dir / stem
    target_dir.mkdir(parents=True, exist_ok=True)
    pattern = str(target_dir / f"{stem}_%03d.mp4")
    subprocess.run(
        [
            "ffmpeg",
            "-hide_banner",
            "-loglevel",
            "error",
            "-y",
            "-i",
            str(video),
            "-c",
            "copy",
            "-map",
            "0:v:0",
            "-an",
            "-f",
            "segment",
            "-segment_time",
            str(seconds),
            "-reset_timestamps",
            "1",
            pattern,
        ],
        check=True,
    )
    return sorted(target_dir.glob(f"{stem}_*.mp4"))


def find_sources(category_dir: Path) -> list[Path]:
    return sorted(
        p
        for p in category_dir.iterdir()
        if p.is_file() and p.suffix.lower() in SOURCE_SUFFIXES
    )


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--input",
        type=Path,
        default=Path("inputs"),
        help="Directory holding the category folders.",
    )
    parser.add_argument(
        "--seconds",
        type=int,
        default=SEGMENT_SECONDS,
        help="Target segment length in seconds.",
    )
    args = parser.parse_args()

    if shutil.which("ffmpeg") is None or shutil.which("ffprobe") is None:
        raise SystemExit("ffmpeg and ffprobe must be on PATH.")

    total = 0
    for category in CATEGORIES:
        category_dir = args.input / category
        if not category_dir.is_dir():
            continue
        sources = find_sources(category_dir)
        if not sources:
            continue
        out_dir = category_dir / "segments"
        for video in sources:
            duration = probe_duration(video)
            segments = segment_video(video, out_dir, args.seconds)
            total += len(segments)
            rel = (out_dir / video.stem).relative_to(args.input)
            print(
                f"[{category}] {video.name}: {duration:.1f}s -> "
                f"{len(segments)} segment(s) in inputs/{rel}"
            )

    if total == 0:
        raise SystemExit("No source videos found in any category folder.")
    print(f"Done. {total} segment(s) total.")


if __name__ == "__main__":
    main()
