#!/usr/bin/env python3
"""Batch multi-frame corner annotation across all category segments.

Walks every ``inputs/<category>/segments/**/*.mp4`` clip in order and opens the
existing single-frame :class:`CornerPicker` for a fixed number of evenly spaced
keyframes per clip. Annotations are written to a CSV beside each video (same
stem), so filenames stay aligned with the source clips.

Conveniences:
- Each clip contributes a fixed number of keyframes (default 5), spread evenly
  from the first frame to the second-to-last frame.
- ``--videos`` restricts annotation to specific clips (by path or filename
  substring); otherwise every clip in the selected categories is visited.
- Per-clip frame progress and overall clip progress are shown in the window
  title and the terminal.
- Already-annotated keyframes are reused; a fully annotated clip is skipped.
- ``Enter`` saves the current frame, ``Esc`` skips the current frame, ``n``
  abandons the rest of the current clip, and ``b`` returns to the clip picker.
"""

from __future__ import annotations

import argparse
from pathlib import Path
from tkinter import (
    BOTH,
    END,
    EXTENDED,
    LEFT,
    RIGHT,
    Y,
    Button,
    Frame,
    Label,
    Listbox,
    Scrollbar,
    Tk,
)

import cv2
import numpy as np

from screen_normalize.experiments.annotations import load_annotations, save_annotations
from scripts.select_corners import CornerPicker, read_frame, scale_for_display

CATEGORIES = ("static", "scrolling", "screen_video", "weak_border", "hard")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, default=Path("inputs"))
    parser.add_argument(
        "--categories",
        nargs="*",
        default=list(CATEGORIES),
        help="Subset of category folders to visit.",
    )
    parser.add_argument(
        "--videos",
        nargs="*",
        default=None,
        help=(
            "Only annotate clips matching these values. Each value may be a clip "
            "path or a filename substring (e.g. IMG_0974 or IMG_0974_000)."
        ),
    )
    parser.add_argument(
        "--all",
        action="store_true",
        help="Skip the GUI clip picker and annotate every collected clip.",
    )
    parser.add_argument(
        "--frames-per-clip",
        type=int,
        default=5,
        help="Number of evenly spaced keyframes to annotate per clip.",
    )
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


def collect_clips(input_dir: Path, categories: list[str]) -> list[Path]:
    clips: list[Path] = []
    for category in categories:
        segments = input_dir / category / "segments"
        if not segments.is_dir():
            continue
        clips.extend(sorted(segments.rglob("*.mp4")))
    return clips


def filter_clips(clips: list[Path], selectors: list[str]) -> list[Path]:
    resolved = {Path(s).resolve() for s in selectors}
    selected: list[Path] = []
    for clip in clips:
        if clip.resolve() in resolved:
            selected.append(clip)
            continue
        if any(s in clip.name or s in str(clip) for s in selectors):
            selected.append(clip)
    return selected


def progress_bar(done: int, total: int, width: int = 20) -> str:
    total = max(total, 1)
    filled = round(width * done / total)
    return f"[{'#' * filled}{'-' * (width - filled)}] {done}/{total}"


def clip_status(video: Path, frames_per_clip: int) -> tuple[int, int]:
    width, height, frame_count = video_shape(video)
    keyframes = select_keyframes(frame_count, frames_per_clip)
    total = len(keyframes)
    try:
        annotations = load_annotations(video.with_suffix(".csv"), width, height)
    except Exception:
        return 0, total
    done = sum(1 for frame in keyframes if frame in annotations)
    return done, total


def choose_clips(clips: list[Path], frames_per_clip: int) -> list[Path]:
    statuses = [clip_status(clip, frames_per_clip) for clip in clips]
    selection: list[Path] = []

    root = Tk()
    root.title("Select clips to annotate")
    Label(
        root,
        text=(
            "Select one or more clips (Ctrl/Shift-click for multiple), then "
            "Annotate Selected. Numbers show annotated/total keyframes."
        ),
        anchor="w",
        justify="left",
    ).pack(fill=BOTH, padx=8, pady=6)

    body = Frame(root)
    body.pack(fill=BOTH, expand=True, padx=8)
    scrollbar = Scrollbar(body)
    scrollbar.pack(side=RIGHT, fill=Y)
    listbox = Listbox(
        body,
        selectmode=EXTENDED,
        width=80,
        height=min(24, max(6, len(clips))),
        yscrollcommand=scrollbar.set,
    )
    listbox.pack(side=LEFT, fill=BOTH, expand=True)
    scrollbar.config(command=listbox.yview)

    for clip, (done, total) in zip(clips, statuses):
        mark = "OK " if total and done >= total else "   "
        rel = clip.relative_to(clip.parents[3]) if len(clip.parents) >= 4 else clip
        listbox.insert(END, f"{mark}[{done}/{total}] {rel}")

    for index, (done, total) in enumerate(statuses):
        if not (total and done >= total):
            listbox.selection_set(index)
            listbox.see(index)
            break

    def annotate_selected() -> None:
        for index in listbox.curselection():
            selection.append(clips[index])
        root.destroy()

    def annotate_pending() -> None:
        for clip, (done, total) in zip(clips, statuses):
            if not (total and done >= total):
                selection.append(clip)
        root.destroy()

    def select_all() -> None:
        listbox.selection_set(0, END)

    buttons = Frame(root)
    buttons.pack(fill=BOTH, padx=8, pady=8)
    Button(buttons, text="Annotate Selected", command=annotate_selected).pack(side=LEFT)
    Button(buttons, text="Annotate All Pending", command=annotate_pending).pack(side=LEFT)
    Button(buttons, text="Select All", command=select_all).pack(side=LEFT)
    Button(buttons, text="Cancel", command=root.destroy).pack(side=RIGHT)

    root.mainloop()
    return selection


def select_keyframes(frame_count: int, frames_per_clip: int) -> list[int]:
    if frame_count <= 0:
        return []
    last = max(0, frame_count - 2)
    count = max(1, frames_per_clip)
    picks = np.linspace(0, last, count)
    ordered = sorted({int(round(value)) for value in picks})
    return [frame for frame in ordered if 0 <= frame < frame_count]


def annotate_clip(
    video: Path,
    args: argparse.Namespace,
    clip_index: int,
    clip_total: int,
) -> str:
    output = video.with_suffix(".csv")
    width, height, frame_count = video_shape(video)
    annotations = load_annotations(output, width, height)
    keyframes = select_keyframes(frame_count, args.frames_per_clip)
    total_frames = len(keyframes)

    pending = [frame for frame in keyframes if frame not in annotations]
    if not pending:
        print(f"skip (complete): {video}  {progress_bar(total_frames, total_frames)}")
        return "continue"

    done = total_frames - len(pending)
    print(f"annotating {video}")

    for frame_index in keyframes:
        if frame_index in annotations:
            continue

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
        picker.skip_clip = False
        picker.back_to_menu = False
        root.bind("n", lambda _event, p=picker: _skip_clip(p))
        root.bind("b", lambda _event, p=picker: _back_to_menu(p))
        root.title(
            f"clip {clip_index}/{clip_total}  frames {progress_bar(done, total_frames)}  "
            f"| {video.name} frame {frame_index}  "
            "| Enter:save  Esc:skip  n:skip clip  b:menu  f:fit  X:quit"
        )
        root.mainloop()

        if getattr(picker, "quit_all", False):
            print("window closed: stopping all annotation")
            return "quit"
        if getattr(picker, "back_to_menu", False):
            print("returning to clip selection")
            return "menu"
        if getattr(picker, "skip_clip", False):
            print(f"skipped rest of clip: {video}")
            return "continue"
        if picker.accepted and len(picker.points) == 4:
            annotations[frame_index] = picker.points
            save_annotations(output, annotations, width, height)
            done += 1
            print(f"  {video.name}  {progress_bar(done, total_frames)}")

    print(f"wrote {len(annotations)} annotated frames to {output}")
    return "continue"


def _skip_clip(picker: CornerPicker) -> None:
    picker.skip_clip = True
    picker.root.destroy()


def _back_to_menu(picker: CornerPicker) -> None:
    picker.back_to_menu = True
    picker.root.destroy()


def run_batch(clips: list[Path], args: argparse.Namespace) -> str:
    total = len(clips)
    for index, video in enumerate(clips, start=1):
        print(f"[{index}/{total}] {video}")
        result = annotate_clip(video, args, index, total)
        if result in ("quit", "menu"):
            return result
    return "done"


def main() -> None:
    args = parse_args()
    clips = collect_clips(args.input, args.categories)
    if args.videos:
        clips = filter_clips(clips, args.videos)
        if not clips:
            raise SystemExit(f"no clips matched --videos {args.videos}")
    if not clips:
        raise SystemExit(f"no clips found under {args.input}/<category>/segments/")

    print(f"found {len(clips)} clip(s)")

    if args.videos or args.all:
        run_batch(clips, args)
        return

    while True:
        selected = choose_clips(clips, args.frames_per_clip)
        if not selected:
            print("no clips selected")
            return
        result = run_batch(selected, args)
        if result == "quit":
            return
        if result == "done":
            print("batch complete; reopening clip selection")


if __name__ == "__main__":
    main()
