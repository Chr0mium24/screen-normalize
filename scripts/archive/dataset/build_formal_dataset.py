#!/usr/bin/env python3
"""Build the formal 5-second input clips from locally collected raw videos."""

from __future__ import annotations

import argparse
import csv
import shutil
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path


CLIP_SECONDS = 5.0
DATE_TAG = "2026-07-14"


@dataclass(frozen=True)
class SampleSpec:
    category: str
    clip_id: str
    source_name: str
    start_seconds: float


def build_sample_plan() -> list[SampleSpec]:
    samples: list[SampleSpec] = []

    for index in range(10):
        samples.append(
            SampleSpec(
                category="scrolling",
                clip_id=f"scrolling_{index + 1:02d}",
                source_name="VID20260712165829.mp4",
                start_seconds=index * CLIP_SECONDS,
            )
        )

    for source_index, source_name in enumerate(
        ("VID20260712170039.mp4", "VID20260712170115.mp4")
    ):
        for segment_index in range(5):
            samples.append(
                SampleSpec(
                    category="screen_video",
                    clip_id=f"screen_video_{source_index * 5 + segment_index + 1:02d}",
                    source_name=source_name,
                    start_seconds=segment_index * CLIP_SECONDS,
                )
            )

    static_single_sources = (
        "VID20260712170254.mp4",
        "VID20260712170303.mp4",
        "VID20260712170318.mp4",
        "VID20260712170428.mp4",
        "VID20260712170444.mp4",
    )
    for index, source_name in enumerate(static_single_sources):
        samples.append(
            SampleSpec(
                category="static",
                clip_id=f"static_{index + 1:02d}",
                source_name=source_name,
                start_seconds=0.0,
            )
        )

    for index in range(5):
        samples.append(
            SampleSpec(
                category="static",
                clip_id=f"static_{index + 6:02d}",
                source_name="VID20260712170211.mp4",
                start_seconds=index * CLIP_SECONDS,
            )
        )

    weak_border_sources = (
        "VID20260712170738.mp4",
        "VID20260712170803.mp4",
        "VID20260712170822.mp4",
        "VID20260712170854.mp4",
        "VID20260712170915.mp4",
    )
    for index, source_name in enumerate(weak_border_sources):
        samples.append(
            SampleSpec(
                category="weak_border",
                clip_id=f"weak_border_{index + 1:02d}",
                source_name=source_name,
                start_seconds=0.0,
            )
        )

    return samples


def run_command(command: list[str]) -> None:
    subprocess.run(command, check=True)


def probe_duration(video: Path) -> float:
    result = subprocess.run(
        [
            "ffprobe",
            "-v",
            "error",
            "-show_entries",
            "format=duration",
            "-of",
            "default=noprint_wrappers=1:nokey=1",
            str(video),
        ],
        capture_output=True,
        text=True,
        check=True,
    )
    return float(result.stdout.strip())


def ensure_tool(name: str) -> None:
    if shutil.which(name) is None:
        raise SystemExit(f"{name} must be available on PATH")


def ffmpeg_clip_command(
    source: Path,
    target: Path,
    start_seconds: float,
    mode: str,
) -> list[str]:
    command = [
        "ffmpeg",
        "-hide_banner",
        "-loglevel",
        "error",
        "-y",
        "-ss",
        f"{start_seconds:.3f}",
        "-i",
        str(source),
        "-t",
        f"{CLIP_SECONDS:.3f}",
        "-map",
        "0:v:0",
        "-an",
    ]
    if mode == "copy":
        command += ["-c", "copy", "-avoid_negative_ts", "make_zero"]
    elif mode == "reencode":
        command += [
            "-c:v",
            "libx264",
            "-preset",
            "veryfast",
            "-crf",
            "18",
            "-pix_fmt",
            "yuv420p",
            "-movflags",
            "+faststart",
        ]
    else:
        command += [
            "-c:v",
            "h264_nvenc",
            "-preset",
            "p4",
            "-cq:v",
            "18",
            "-b:v",
            "0",
            "-pix_fmt",
            "yuv420p",
            "-movflags",
            "+faststart",
        ]
    return command + [str(target)]


def resolve_raw_root(raw_root: Path, archive_root: Path) -> Path:
    if raw_root.exists():
        return raw_root
    if archive_root.exists():
        return archive_root
    raise SystemExit(f"raw video directory not found: {raw_root}")


def validate_sources(samples: list[SampleSpec], raw_root: Path) -> None:
    missing = sorted({spec.source_name for spec in samples if not (raw_root / spec.source_name).is_file()})
    if missing:
        joined = "\n".join(f"- {name}" for name in missing)
        raise SystemExit(f"missing source video(s):\n{joined}")


def validate_targets(samples: list[SampleSpec], output_root: Path, force: bool) -> None:
    existing = [
        output_root / spec.category / f"{spec.clip_id}.mp4"
        for spec in samples
        if (output_root / spec.category / f"{spec.clip_id}.mp4").exists()
    ]
    if existing and not force:
        joined = "\n".join(f"- {path}" for path in existing)
        raise SystemExit(f"target video(s) already exist; rerun with --force to overwrite:\n{joined}")


def write_manifest(rows: list[dict[str, str]], manifest_path: Path | None) -> None:
    if manifest_path is None:
        return
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = [
        "category",
        "clip_id",
        "source_name",
        "start_seconds",
        "duration_seconds",
        "target_path",
    ]
    with manifest_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def archive_raw_directory(raw_root: Path, archive_root: Path) -> None:
    if raw_root.resolve() == archive_root.resolve():
        return
    if archive_root.exists():
        raise SystemExit(f"archive target already exists: {archive_root}")
    archive_root.parent.mkdir(parents=True, exist_ok=True)
    shutil.move(str(raw_root), str(archive_root))


def find_repo_root(start: Path) -> Path:
    for candidate in (start, *start.parents):
        if (candidate / "pyproject.toml").is_file() and (candidate / "screen_normalize").is_dir():
            return candidate
    raise SystemExit(f"could not find repository root from {start}")


def parse_args() -> argparse.Namespace:
    repo_root = find_repo_root(Path(__file__).resolve())
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--raw-root", type=Path, default=repo_root.parent / "premodify")
    parser.add_argument("--output-root", type=Path, default=repo_root / "inputs")
    parser.add_argument(
        "--archive-root",
        type=Path,
        default=repo_root / "inputs" / "archive" / f"raw_premodify_{DATE_TAG}",
    )
    parser.add_argument("--manifest", type=Path)
    parser.add_argument("--mode", choices=("copy", "reencode", "nvenc"), default="copy")
    parser.add_argument("--duration-tolerance", type=float, default=0.35)
    parser.add_argument("--archive-raw", action="store_true")
    parser.add_argument("--force", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    ensure_tool("ffmpeg")
    ensure_tool("ffprobe")

    samples = build_sample_plan()
    raw_root = resolve_raw_root(args.raw_root, args.archive_root)
    output_root = args.output_root

    validate_sources(samples, raw_root)
    validate_targets(samples, output_root, args.force)

    rows: list[dict[str, str]] = []
    for spec in samples:
        source = raw_root / spec.source_name
        target = output_root / spec.category / f"{spec.clip_id}.mp4"
        target.parent.mkdir(parents=True, exist_ok=True)
        run_command(ffmpeg_clip_command(source, target, spec.start_seconds, args.mode))
        duration = probe_duration(target)
        if abs(duration - CLIP_SECONDS) > args.duration_tolerance:
            raise SystemExit(
                f"{target} duration {duration:.3f}s is outside tolerance "
                f"for {CLIP_SECONDS:.3f}s"
            )
        row = {
            "category": spec.category,
            "clip_id": spec.clip_id,
            "source_name": spec.source_name,
            "start_seconds": f"{spec.start_seconds:.3f}",
            "duration_seconds": f"{duration:.3f}",
            "target_path": target.relative_to(output_root.parent).as_posix(),
        }
        rows.append(row)
        print(
            f"[{spec.category}] {spec.clip_id}: {spec.source_name} "
            f"@ {spec.start_seconds:.1f}s -> {duration:.3f}s"
        )

    write_manifest(rows, args.manifest)
    if args.archive_raw:
        archive_raw_directory(raw_root, args.archive_root)
        print(f"archived raw videos: {args.archive_root}")
    print(f"generated {len(rows)} clip(s)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
