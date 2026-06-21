from __future__ import annotations

import argparse
from datetime import datetime
from pathlib import Path
from tkinter import Tk

import cv2

from .common import create_run_directory, project_root
from .manual_demo_core import (
    build_demo_strip,
    choose_frames,
    load_annotations,
    read_metadata,
    save_annotations,
)
from .manual_demo_gui import ManualDemoPicker


def positive_int(value: str) -> int:
    parsed = int(value)
    if parsed <= 0:
        raise argparse.ArgumentTypeError("value must be positive")
    return parsed


def nonnegative_int(value: str) -> int:
    parsed = int(value)
    if parsed < 0:
        raise argparse.ArgumentTypeError("value must be >= 0")
    return parsed


def parse_frames(value: str) -> list[int]:
    frames: list[int] = []
    for raw in value.split(","):
        raw = raw.strip()
        if not raw:
            continue
        try:
            frame = int(raw)
        except ValueError as exc:
            raise argparse.ArgumentTypeError("frames must be comma-separated integers") from exc
        if frame < 0:
            raise argparse.ArgumentTypeError("frame indices must be >= 0")
        frames.append(frame)
    if not frames:
        raise argparse.ArgumentTypeError("at least one frame index is required")
    return frames


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Interactively annotate several video frames and render a manual "
            "target-effect demo strip."
        )
    )
    parser.add_argument("input", type=Path, help="Raw filmed-screen video.")
    parser.add_argument(
        "--frames",
        type=parse_frames,
        default=None,
        help="Comma-separated frame indices to annotate, for example 0,30,60,90.",
    )
    parser.add_argument(
        "--count",
        type=positive_int,
        default=8,
        help="Number of evenly spaced frames to annotate when --frames is omitted.",
    )
    parser.add_argument("--width", type=positive_int, default=1920)
    parser.add_argument("--height", type=positive_int, default=1080)
    parser.add_argument("--thumb-width", type=positive_int, default=320)
    parser.add_argument(
        "--label-height",
        type=nonnegative_int,
        default=28,
        help="Top label band height for each tile. Use 0 to disable frame labels.",
    )
    parser.add_argument("--max-display-width", type=positive_int, default=1100)
    parser.add_argument("--max-display-height", type=positive_int, default=760)
    parser.add_argument(
        "--point-radius",
        type=positive_int,
        default=4,
        help="Displayed control-point radius in pixels.",
    )
    parser.add_argument(
        "--hit-radius",
        type=positive_int,
        default=10,
        help="Drag-selection radius around existing points in pixels.",
    )
    parser.add_argument(
        "--label-font-size",
        type=positive_int,
        default=10,
        help="Displayed TL/TR/BR/BL label font size.",
    )
    parser.add_argument(
        "--annotations",
        type=Path,
        default=None,
        help="Reuse an existing manual_demo_annotations.json file instead of opening the GUI.",
    )
    parser.add_argument(
        "--runs-dir",
        type=Path,
        default=None,
        help="Directory that receives run folders. Defaults to ./runs.",
    )
    parser.add_argument(
        "--run-name",
        default=None,
        help="Override the generated run folder name.",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=None,
        help="Optional output PNG path. If omitted, writes inside runs/<run-name>/.",
    )
    return parser.parse_args()


def resolve_run_dir(args: argparse.Namespace) -> Path:
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        return args.output.parent.resolve()
    runs_dir = args.runs_dir.resolve() if args.runs_dir else project_root() / "runs"
    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    run_name = args.run_name or f"{timestamp}_manual_demo_strip"
    return create_run_directory(runs_dir, run_name).resolve()


def main() -> None:
    args = parse_args()
    input_path = args.input.resolve()
    metadata = read_metadata(input_path)
    run_dir = resolve_run_dir(args)
    output_path = args.output.resolve() if args.output else run_dir / f"{input_path.stem}_manual_demo_strip.png"
    annotation_path = run_dir / "manual_demo_annotations.json"

    output_size = (args.width, args.height)
    if args.annotations:
        loaded_output_size, annotations = load_annotations(args.annotations)
        if loaded_output_size is not None and (args.width, args.height) == (1920, 1080):
            output_size = loaded_output_size
    else:
        frames = args.frames or choose_frames(metadata, args.count)
        for frame in frames:
            if metadata.frame_count > 0 and frame >= metadata.frame_count:
                raise SystemExit(f"frame {frame} is outside video frame count {metadata.frame_count}")
        root = Tk()
        picker = ManualDemoPicker(
            root=root,
            input_path=input_path,
            metadata=metadata,
            frames=frames,
            output_size=output_size,
            max_display_size=(args.max_display_width, args.max_display_height),
            point_radius=args.point_radius,
            hit_radius=args.hit_radius,
            label_font_size=args.label_font_size,
        )
        root.mainloop()
        if picker.cancelled:
            raise SystemExit("manual annotation cancelled")
        annotations = picker.annotations
        save_annotations(annotation_path, input_path, output_size, annotations)
        print(f"wrote {annotation_path}")

    strip = build_demo_strip(
        input_path=input_path,
        annotations=annotations,
        output_size=output_size,
        thumb_width=args.thumb_width,
        label_height=args.label_height,
    )
    ok = cv2.imwrite(str(output_path), strip)
    if not ok:
        raise SystemExit(f"could not write {output_path}")
    print(f"wrote {output_path}")
