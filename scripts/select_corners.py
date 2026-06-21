#!/usr/bin/env python3
# /// script
# dependencies = [
#   "numpy>=2.2.0",
#   "opencv-python-headless>=4.12.0.88",
# ]
# ///

from __future__ import annotations

import argparse
import base64
import shlex
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from tkinter import BOTH, LEFT, RIGHT, Button, Canvas, Frame, Label, PhotoImage, Tk

import cv2
import numpy as np


POINT_LABELS = ("TL", "TR", "BR", "BL")


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


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Open a first-frame corner picker and print a --corners string in "
            "TL,TR,BR,BL order."
        )
    )
    parser.add_argument("input", type=Path)
    parser.add_argument("--frame", type=nonnegative_int, default=0)
    parser.add_argument("--width", type=positive_int, default=1920)
    parser.add_argument("--height", type=positive_int, default=1080)
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
        "--run-preview",
        action="store_true",
        help="After accepting points, run normalize_screen.py with the selected corners.",
    )
    parser.add_argument("--preview-run-name", default="manual_corner_preview")
    parser.add_argument(
        "--extra-normalize-args",
        default="--tracker reference --reference-profile low-latency",
        help="Extra arguments used only with --run-preview.",
    )
    return parser.parse_args()


def read_frame(video: Path, frame_index: int) -> np.ndarray:
    capture = cv2.VideoCapture(str(video))
    if not capture.isOpened():
        raise SystemExit(f"could not open video: {video}")
    if frame_index:
        capture.set(cv2.CAP_PROP_POS_FRAMES, frame_index)
    ok, frame = capture.read()
    capture.release()
    if not ok:
        raise SystemExit(f"could not read frame {frame_index} from {video}")
    return frame


def bgr_to_photo(image: np.ndarray) -> PhotoImage:
    ok, encoded = cv2.imencode(".png", image)
    if not ok:
        raise RuntimeError("could not encode preview image")
    data = base64.b64encode(encoded.tobytes()).decode("ascii")
    return PhotoImage(data=data)


def scale_for_display(width: int, height: int, max_width: int, max_height: int) -> float:
    return min(max_width / width, max_height / height, 1.0)


def format_corners(points: list[tuple[float, float]]) -> str:
    return ":".join(f"{round(x)},{round(y)}" for x, y in points)


def split_extra_args(value: str) -> list[str]:
    tokens = shlex.split(value)
    merged: list[str] = []
    index = 0
    while index < len(tokens):
        token = tokens[index]
        if token.endswith("-") and index + 1 < len(tokens):
            merged.append(token + tokens[index + 1])
            index += 2
            continue
        merged.append(token)
        index += 1
    return merged


@dataclass
class CornerPicker:
    root: Tk
    input_path: Path
    frame_bgr: np.ndarray
    output_size: tuple[int, int]
    scale: float
    run_preview: bool
    preview_run_name: str
    extra_normalize_args: str
    point_radius: int
    hit_radius: int
    label_font_size: int

    def __post_init__(self) -> None:
        self.points: list[tuple[float, float]] = []
        self.drag_index: int | None = None
        self.accepted = False

        frame_height, frame_width = self.frame_bgr.shape[:2]
        display_size = (round(frame_width * self.scale), round(frame_height * self.scale))
        self.display_bgr = cv2.resize(self.frame_bgr, display_size, interpolation=cv2.INTER_AREA)

        self.root.title("Select screen/content corners: TL, TR, BR, BL")
        self.root.bind("<Return>", lambda _event: self.accept())
        self.root.bind("<Escape>", lambda _event: self.cancel())
        self.root.bind("u", lambda _event: self.undo())
        self.root.bind("r", lambda _event: self.reset())

        outer = Frame(self.root)
        outer.pack(fill=BOTH, expand=True)

        left = Frame(outer)
        left.pack(side=LEFT, fill=BOTH, expand=True)
        right = Frame(outer)
        right.pack(side=RIGHT, fill=BOTH, expand=False)

        self.status = Label(
            left,
            text=(
                "Click points in order: TL, TR, BR, BL. Drag a point to adjust. "
                "Enter accepts, u undoes, r resets."
            ),
            anchor="w",
        )
        self.status.pack(fill=BOTH)

        self.canvas = Canvas(left, width=display_size[0], height=display_size[1])
        self.canvas.pack(fill=BOTH, expand=True)
        self.canvas.bind("<Button-1>", self.on_click)
        self.canvas.bind("<B1-Motion>", self.on_drag)
        self.canvas.bind("<ButtonRelease-1>", self.on_release)

        self.preview_label = Label(right, text="Warp preview appears after 4 points")
        self.preview_label.pack(fill=BOTH)
        self.preview_canvas = Canvas(right, width=480, height=270)
        self.preview_canvas.pack(fill=BOTH, expand=False)

        buttons = Frame(right)
        buttons.pack(fill=BOTH)
        Button(buttons, text="Undo", command=self.undo).pack(side=LEFT)
        Button(buttons, text="Reset", command=self.reset).pack(side=LEFT)
        Button(buttons, text="Accept", command=self.accept).pack(side=LEFT)

        self.base_photo = bgr_to_photo(self.display_bgr)
        self.canvas_image = None
        self.preview_photo: PhotoImage | None = None
        self.draw()

    def to_frame_point(self, x: float, y: float) -> tuple[float, float]:
        return x / self.scale, y / self.scale

    def to_canvas_point(self, point: tuple[float, float]) -> tuple[float, float]:
        return point[0] * self.scale, point[1] * self.scale

    def nearest_point(self, x: float, y: float) -> int | None:
        if not self.points:
            return None
        canvas_points = [self.to_canvas_point(point) for point in self.points]
        distances = [np.hypot(px - x, py - y) for px, py in canvas_points]
        nearest = int(np.argmin(distances))
        return nearest if distances[nearest] <= self.hit_radius else None

    def on_click(self, event: object) -> None:
        x = float(getattr(event, "x"))
        y = float(getattr(event, "y"))
        nearest = self.nearest_point(x, y)
        if nearest is not None:
            self.drag_index = nearest
            return
        if len(self.points) >= 4:
            return
        self.points.append(self.to_frame_point(x, y))
        self.drag_index = len(self.points) - 1
        self.draw()

    def on_drag(self, event: object) -> None:
        if self.drag_index is None:
            return
        x = float(getattr(event, "x"))
        y = float(getattr(event, "y"))
        frame_height, frame_width = self.frame_bgr.shape[:2]
        frame_x, frame_y = self.to_frame_point(x, y)
        frame_x = min(max(frame_x, 0.0), float(frame_width - 1))
        frame_y = min(max(frame_y, 0.0), float(frame_height - 1))
        self.points[self.drag_index] = (frame_x, frame_y)
        self.draw()

    def on_release(self, _event: object) -> None:
        self.drag_index = None

    def undo(self) -> None:
        if self.points:
            self.points.pop()
        self.draw()

    def reset(self) -> None:
        self.points.clear()
        self.draw()

    def draw(self) -> None:
        self.canvas.delete("all")
        self.canvas_image = self.canvas.create_image(0, 0, image=self.base_photo, anchor="nw")
        canvas_points = [self.to_canvas_point(point) for point in self.points]
        if len(canvas_points) >= 2:
            line_points = canvas_points + ([canvas_points[0]] if len(canvas_points) == 4 else [])
            for first, second in zip(line_points, line_points[1:]):
                self.canvas.create_line(*first, *second, fill="#00ff66", width=2)
        for index, (x, y) in enumerate(canvas_points):
            radius = self.point_radius
            self.canvas.create_oval(
                x - radius,
                y - radius,
                x + radius,
                y + radius,
                fill="#ff3355",
                outline="white",
            )
            self.canvas.create_text(
                x + 18,
                y - 16,
                text=POINT_LABELS[index],
                fill="white",
                font=("Helvetica", self.label_font_size, "bold"),
            )

        if len(self.points) < 4:
            next_label = POINT_LABELS[len(self.points)]
            self.status.config(text=f"Select {next_label}. Current points: {format_corners(self.points)}")
        else:
            corners = format_corners(self.points)
            self.status.config(text=f"Ready. Press Enter or Accept. --corners \"{corners}\"")
            self.update_preview()

    def update_preview(self) -> None:
        source = np.asarray(self.points, dtype=np.float32)
        width, height = self.output_size
        destination = np.asarray(
            [[0, 0], [width - 1, 0], [width - 1, height - 1], [0, height - 1]],
            dtype=np.float32,
        )
        transform = cv2.getPerspectiveTransform(source, destination)
        warped = cv2.warpPerspective(self.frame_bgr, transform, (width, height))
        preview = cv2.resize(warped, (480, 270), interpolation=cv2.INTER_AREA)
        self.preview_photo = bgr_to_photo(preview)
        self.preview_canvas.delete("all")
        self.preview_canvas.create_image(0, 0, image=self.preview_photo, anchor="nw")

    def accept(self) -> None:
        if len(self.points) != 4:
            self.status.config(text="Need exactly 4 points: TL, TR, BR, BL.")
            return
        corners = format_corners(self.points)
        command = (
            f'uv run scripts/normalize_screen.py "{self.input_path}" '
            f'--corners "{corners}" {" ".join(split_extra_args(self.extra_normalize_args))}'
        )
        print(corners)
        print(command)
        try:
            self.root.clipboard_clear()
            self.root.clipboard_append(corners)
        except Exception:
            pass
        self.accepted = True
        self.root.destroy()

        if self.run_preview:
            self.run_normalize_preview(corners)

    def run_normalize_preview(self, corners: str) -> None:
        command = [
            "uv",
            "run",
            "scripts/normalize_screen.py",
            str(self.input_path),
            "--corners",
            corners,
            "--run-name",
            self.preview_run_name,
            *split_extra_args(self.extra_normalize_args),
        ]
        print("running:", " ".join(command), file=sys.stderr)
        completed = subprocess.run(command, check=False)
        if completed.returncode:
            print(
                f"preview command failed with exit code {completed.returncode}",
                file=sys.stderr,
            )

    def cancel(self) -> None:
        self.root.destroy()


def main() -> None:
    args = parse_args()
    frame = read_frame(args.input, args.frame)
    frame_height, frame_width = frame.shape[:2]
    scale = scale_for_display(
        frame_width,
        frame_height,
        args.max_display_width,
        args.max_display_height,
    )
    root = Tk()
    CornerPicker(
        root=root,
        input_path=args.input,
        frame_bgr=frame,
        output_size=(args.width, args.height),
        scale=scale,
        run_preview=args.run_preview,
        preview_run_name=args.preview_run_name,
        extra_normalize_args=args.extra_normalize_args,
        point_radius=args.point_radius,
        hit_radius=args.hit_radius,
        label_font_size=args.label_font_size,
    )
    root.mainloop()


if __name__ == "__main__":
    main()
