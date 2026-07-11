from __future__ import annotations

import base64
from pathlib import Path
from tkinter import BOTH, LEFT, RIGHT, Button, Canvas, Frame, Label, PhotoImage, Tk

import cv2
import numpy as np

from .manual_demo_core import (
    POINT_LABELS,
    FrameAnnotation,
    VideoMetadata,
    format_corners,
    read_frame,
    warp_frame,
)


def bgr_to_photo(image: np.ndarray) -> PhotoImage:
    ok, encoded = cv2.imencode(".png", image)
    if not ok:
        raise RuntimeError("could not encode preview image")
    data = base64.b64encode(encoded.tobytes()).decode("ascii")
    return PhotoImage(data=data)


def scale_for_display(width: int, height: int, max_width: int, max_height: int) -> float:
    return min(max_width / width, max_height / height, 1.0)


class ManualDemoPicker:
    def __init__(
        self,
        root: Tk,
        input_path: Path,
        metadata: VideoMetadata,
        frames: list[int],
        output_size: tuple[int, int],
        max_display_size: tuple[int, int],
        point_radius: int,
        hit_radius: int,
        label_font_size: int,
    ) -> None:
        self.root = root
        self.input_path = input_path
        self.metadata = metadata
        self.frames = frames
        self.output_size = output_size
        self.max_display_size = max_display_size
        self.point_radius = point_radius
        self.hit_radius = hit_radius
        self.label_font_size = label_font_size

        self.index = 0
        self.annotations: list[FrameAnnotation] = [
            FrameAnnotation(
                frame=frame,
                time_seconds=frame / metadata.fps,
                corners=[],
            )
            for frame in frames
        ]
        self.drag_index: int | None = None
        self.cancelled = False

        self.frame_bgr = read_frame(self.input_path, self.frames[self.index])
        frame_height, frame_width = self.frame_bgr.shape[:2]
        self.scale = scale_for_display(
            frame_width,
            frame_height,
            self.max_display_size[0],
            self.max_display_size[1],
        )
        display_size = (round(frame_width * self.scale), round(frame_height * self.scale))

        self.root.title("Manual target demo corners: TL, TR, BR, BL")
        self.root.bind("<Return>", lambda _event: self.accept_current())
        self.root.bind("<Escape>", lambda _event: self.cancel())
        self.root.bind("u", lambda _event: self.undo())
        self.root.bind("r", lambda _event: self.reset())
        self.root.bind("b", lambda _event: self.previous_frame())

        outer = Frame(self.root)
        outer.pack(fill=BOTH, expand=True)

        left = Frame(outer)
        left.pack(side=LEFT, fill=BOTH, expand=True)
        right = Frame(outer)
        right.pack(side=RIGHT, fill=BOTH, expand=False)

        self.status = Label(left, text="", anchor="w")
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
        Button(buttons, text="Back", command=self.previous_frame).pack(side=LEFT)
        Button(buttons, text="Undo", command=self.undo).pack(side=LEFT)
        Button(buttons, text="Reset", command=self.reset).pack(side=LEFT)
        Button(buttons, text="Accept/Next", command=self.accept_current).pack(side=LEFT)

        self.base_photo: PhotoImage | None = None
        self.preview_photo: PhotoImage | None = None
        self.draw()

    @property
    def points(self) -> list[tuple[float, float]]:
        return self.annotations[self.index].corners

    def load_current_frame(self) -> None:
        self.frame_bgr = read_frame(self.input_path, self.frames[self.index])

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

    def previous_frame(self) -> None:
        if self.index <= 0:
            return
        self.index -= 1
        self.load_current_frame()
        self.draw()

    def accept_current(self) -> None:
        if len(self.points) != 4:
            self.status.config(text="Need exactly 4 points: TL, TR, BR, BL.")
            return
        print(f"frame {self.frames[self.index]}: {format_corners(self.points)}")
        if self.index == len(self.frames) - 1:
            self.root.destroy()
            return
        self.index += 1
        self.load_current_frame()
        self.draw()

    def cancel(self) -> None:
        self.cancelled = True
        self.root.destroy()

    def draw(self) -> None:
        frame_height, frame_width = self.frame_bgr.shape[:2]
        display_size = (round(frame_width * self.scale), round(frame_height * self.scale))
        display_bgr = cv2.resize(self.frame_bgr, display_size, interpolation=cv2.INTER_AREA)
        self.base_photo = bgr_to_photo(display_bgr)

        self.canvas.delete("all")
        self.canvas.create_image(0, 0, image=self.base_photo, anchor="nw")

        canvas_points = [self.to_canvas_point(point) for point in self.points]
        if len(canvas_points) >= 2:
            line_points = canvas_points + ([canvas_points[0]] if len(canvas_points) == 4 else [])
            for first, second in zip(line_points, line_points[1:]):
                self.canvas.create_line(*first, *second, fill="#00ff66", width=2)

        for point_index, (x, y) in enumerate(canvas_points):
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
                text=POINT_LABELS[point_index],
                fill="white",
                font=("Helvetica", self.label_font_size, "bold"),
            )

        annotation = self.annotations[self.index]
        prefix = (
            f"Frame {self.index + 1}/{len(self.frames)}: "
            f"f{annotation.frame}  {annotation.time_seconds:.2f}s. "
        )
        if len(self.points) < 4:
            self.status.config(text=f"{prefix}Select {POINT_LABELS[len(self.points)]}.")
            self.preview_canvas.delete("all")
            self.preview_photo = None
        else:
            self.status.config(
                text=(
                    f"{prefix}Press Enter or Accept/Next. "
                    f"Corners: {format_corners(self.points)}"
                )
            )
            self.update_preview()

    def update_preview(self) -> None:
        warped = warp_frame(self.frame_bgr, self.points, self.output_size)
        preview = cv2.resize(warped, (480, 270), interpolation=cv2.INTER_AREA)
        self.preview_photo = bgr_to_photo(preview)
        self.preview_canvas.delete("all")
        self.preview_canvas.create_image(0, 0, image=self.preview_photo, anchor="nw")
