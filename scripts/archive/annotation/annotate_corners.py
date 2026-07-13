#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path
from tkinter import Tk

import cv2

from screen_normalize.experiments.annotations import load_annotations, save_annotations
from scripts.select_corners import CornerPicker, read_frame, scale_for_display


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Create or edit multi-frame screen-corner annotations.")
    parser.add_argument("input", type=Path)
    parser.add_argument("--output", type=Path, help="Defaults to a CSV beside the video.")
    parser.add_argument("--frames", type=int, nargs="*", help="Explicit frame indexes to visit.")
    parser.add_argument("--stride", type=int, default=30)
    parser.add_argument("--max-frames", type=int, default=0, help="0 visits all selected frames.")
    parser.add_argument("--max-display-width", type=int, default=1100)
    parser.add_argument("--max-display-height", type=int, default=760)
    return parser.parse_args()


def video_shape(path: Path) -> tuple[int, int, int]:
    capture = cv2.VideoCapture(str(path))
    if not capture.isOpened():
        raise SystemExit(f"could not open video: {path}")
    width = int(capture.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(capture.get(cv2.CAP_PROP_FRAME_HEIGHT))
    count = int(capture.get(cv2.CAP_PROP_FRAME_COUNT))
    capture.release()
    return width, height, count


def main() -> None:
    args = parse_args()
    video = args.input.resolve()
    output = (args.output or video.with_suffix(".csv")).resolve()
    width, height, frame_count = video_shape(video)
    annotations = load_annotations(output, width, height)
    selected = sorted(set(args.frames)) if args.frames else list(range(0, frame_count, max(1, args.stride)))
    selected = [frame for frame in selected if 0 <= frame < frame_count]
    if args.max_frames > 0:
        selected = selected[: args.max_frames]

    for frame_index in selected:
        frame = read_frame(video, frame_index)
        root = Tk()
        scale = scale_for_display(width, height, args.max_display_width, args.max_display_height)
        picker = CornerPicker(
            root=root,
            input_path=video,
            frame_bgr=frame,
            output_size=(1920, 1080),
            scale=scale,
            run_preview=False,
            preview_run_name="annotation_preview",
            extra_normalize_args="",
            point_radius=4,
            hit_radius=10,
            label_font_size=10,
        )
        if frame_index in annotations:
            picker.points = [tuple(map(float, point)) for point in annotations[frame_index]]
            picker.draw()
        root.title(f"{video.name} - frame {frame_index} - accept to save, escape to skip")
        root.mainloop()
        if picker.accepted and len(picker.points) == 4:
            annotations[frame_index] = picker.points
            save_annotations(output, annotations, width, height)

    print(f"wrote {len(annotations)} annotated frames to {output}")


if __name__ == "__main__":
    main()
