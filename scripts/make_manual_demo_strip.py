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
import json
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from tkinter import BOTH, LEFT, RIGHT, Button, Canvas, Frame, Label, PhotoImage, Tk

import cv2
import numpy as np


POINT_LABELS = ("TL", "TR", "BR", "BL")


@dataclass(frozen=True)
class VideoMetadata:
    path: Path
    width: int
    height: int
    fps: float
    frame_count: int


@dataclass
class FrameAnnotation:
    frame: int
    time_seconds: float
    corners: list[tuple[float, float]]


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


def project_root() -> Path:
    script_path = Path(__file__).resolve()
    for path in (script_path.parent, *script_path.parents):
        if (path / ".git").exists():
            return path
    if script_path.parent.name == "scripts":
        return script_path.parent.parent
    return Path.cwd()


def clean_path_component(value: str) -> str:
    cleaned = "".join(
        character if character.isalnum() or character in ("-", "_", ".") else "_"
        for character in value
    ).strip("._-")
    return cleaned or "run"


def create_run_directory(runs_dir: Path, run_name: str) -> Path:
    runs_dir.mkdir(parents=True, exist_ok=True)
    clean_name = clean_path_component(run_name)
    for index in range(1000):
        suffix = "" if index == 0 else f"_{index:02d}"
        candidate = runs_dir / f"{clean_name}{suffix}"
        try:
            candidate.mkdir()
        except FileExistsError:
            continue
        return candidate
    raise RuntimeError(f"could not create unique run directory under {runs_dir}")


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


def read_metadata(path: Path) -> VideoMetadata:
    capture = cv2.VideoCapture(str(path))
    if not capture.isOpened():
        raise SystemExit(f"could not open video: {path}")
    fps = float(capture.get(cv2.CAP_PROP_FPS) or 0.0)
    frame_count = int(capture.get(cv2.CAP_PROP_FRAME_COUNT) or 0)
    width = int(capture.get(cv2.CAP_PROP_FRAME_WIDTH) or 0)
    height = int(capture.get(cv2.CAP_PROP_FRAME_HEIGHT) or 0)
    capture.release()
    if fps <= 0 or width <= 0 or height <= 0:
        raise SystemExit(f"could not read video metadata: {path}")
    return VideoMetadata(path=path, width=width, height=height, fps=fps, frame_count=frame_count)


def read_frame(path: Path, index: int) -> np.ndarray:
    capture = cv2.VideoCapture(str(path))
    if not capture.isOpened():
        raise SystemExit(f"could not open video: {path}")
    capture.set(cv2.CAP_PROP_POS_FRAMES, index)
    ok, frame = capture.read()
    capture.release()
    if not ok:
        raise SystemExit(f"could not read frame {index} from {path}")
    return frame


def choose_frames(metadata: VideoMetadata, count: int) -> list[int]:
    if metadata.frame_count <= 0:
        raise SystemExit(f"video does not report frame count: {metadata.path}")
    if count == 1:
        return [0]
    raw = np.linspace(0, metadata.frame_count - 1, count)
    return [int(round(value)) for value in raw]


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


def warp_frame(frame: np.ndarray, corners: list[tuple[float, float]], output_size: tuple[int, int]) -> np.ndarray:
    source = np.asarray(corners, dtype=np.float32)
    width, height = output_size
    destination = np.asarray(
        [[0, 0], [width - 1, 0], [width - 1, height - 1], [0, height - 1]],
        dtype=np.float32,
    )
    transform = cv2.getPerspectiveTransform(source, destination)
    return cv2.warpPerspective(frame, transform, (width, height))


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


def draw_points(
    image: np.ndarray,
    source_size: tuple[int, int],
    points: list[tuple[float, float]],
) -> None:
    source_width, source_height = source_size
    scale_x = image.shape[1] / source_width
    scale_y = image.shape[0] / source_height
    scaled = [(int(round(x * scale_x)), int(round(y * scale_y))) for x, y in points]

    polygon = np.asarray(scaled, dtype=np.int32).reshape((-1, 1, 2))
    cv2.polylines(image, [polygon], isClosed=True, color=(0, 255, 96), thickness=2)
    for index, point in enumerate(scaled, start=1):
        cv2.circle(image, point, 5, (40, 40, 255), -1)
        cv2.circle(image, point, 6, (255, 255, 255), 1)
        cv2.putText(
            image,
            str(index),
            (point[0] + 8, point[1] - 8),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.45,
            (255, 255, 255),
            2,
            cv2.LINE_AA,
        )


def make_tile(frame: np.ndarray, thumb_width: int, label_height: int, label: str) -> np.ndarray:
    source_height, source_width = frame.shape[:2]
    scale = thumb_width / source_width
    thumb_height = max(1, int(round(source_height * scale)))
    tile = cv2.resize(frame, (thumb_width, thumb_height), interpolation=cv2.INTER_AREA)
    if label_height <= 0:
        return tile
    labeled = cv2.copyMakeBorder(
        tile,
        label_height,
        0,
        0,
        0,
        cv2.BORDER_CONSTANT,
        value=(20, 20, 20),
    )
    cv2.putText(
        labeled,
        label,
        (8, max(18, label_height - 8)),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.48,
        (240, 240, 240),
        1,
        cv2.LINE_AA,
    )
    return labeled


def make_row_label(height: int, width: int, text: str) -> np.ndarray:
    label = np.full((height, width, 3), 245, dtype=np.uint8)
    cv2.rectangle(label, (0, 0), (width - 1, height - 1), (210, 210, 210), 1)
    cv2.putText(
        label,
        text,
        (10, max(24, height // 2)),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.58,
        (20, 20, 20),
        2,
        cv2.LINE_AA,
    )
    return label


def pad_to_height(image: np.ndarray, height: int) -> np.ndarray:
    missing = height - image.shape[0]
    if missing <= 0:
        return image
    return cv2.copyMakeBorder(
        image,
        0,
        missing,
        0,
        0,
        cv2.BORDER_CONSTANT,
        value=(255, 255, 255),
    )


def build_demo_strip(
    input_path: Path,
    annotations: list[FrameAnnotation],
    output_size: tuple[int, int],
    thumb_width: int,
    label_height: int,
) -> np.ndarray:
    original_tiles: list[np.ndarray] = []
    target_tiles: list[np.ndarray] = []
    for annotation in annotations:
        frame = read_frame(input_path, annotation.frame)
        original = frame.copy()
        frame_height, frame_width = frame.shape[:2]
        draw_points(original, (frame_width, frame_height), annotation.corners)

        label = f"f{annotation.frame}  {annotation.time_seconds:.2f}s"
        original_tiles.append(make_tile(original, thumb_width, label_height, label))
        warped = warp_frame(frame, annotation.corners, output_size)
        target_tiles.append(make_tile(warped, thumb_width, label_height, label))

    original_row = np.hstack(original_tiles)
    target_row = np.hstack(target_tiles)
    row_height = max(original_row.shape[0], target_row.shape[0])
    original_row = pad_to_height(original_row, row_height)
    target_row = pad_to_height(target_row, row_height)

    label_width = 160
    original_row = np.hstack([make_row_label(row_height, label_width, "marked input"), original_row])
    target_row = np.hstack([make_row_label(row_height, label_width, "manual target"), target_row])
    separator = np.full((12, original_row.shape[1], 3), 255, dtype=np.uint8)
    return np.vstack([original_row, separator, target_row])


def save_annotations(
    path: Path,
    input_path: Path,
    output_size: tuple[int, int],
    annotations: list[FrameAnnotation],
) -> None:
    payload = {
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "video": str(input_path),
        "output_size": {"width": output_size[0], "height": output_size[1]},
        "frames": [
            {
                "frame": annotation.frame,
                "time_seconds": annotation.time_seconds,
                "corners": [[x, y] for x, y in annotation.corners],
            }
            for annotation in annotations
        ],
    }
    with path.open("w") as handle:
        json.dump(payload, handle, indent=2)
        handle.write("\n")


def load_annotations(path: Path) -> tuple[tuple[int, int] | None, list[FrameAnnotation]]:
    with path.open() as handle:
        payload = json.load(handle)

    output_size = None
    raw_output_size = payload.get("output_size")
    if isinstance(raw_output_size, dict):
        width = raw_output_size.get("width")
        height = raw_output_size.get("height")
        if isinstance(width, int) and isinstance(height, int):
            output_size = (width, height)

    annotations = []
    for raw_frame in payload.get("frames", []):
        corners = [(float(x), float(y)) for x, y in raw_frame["corners"]]
        if len(corners) != 4:
            raise SystemExit(f"annotation frame {raw_frame.get('frame')} does not have 4 corners")
        annotations.append(
            FrameAnnotation(
                frame=int(raw_frame["frame"]),
                time_seconds=float(raw_frame["time_seconds"]),
                corners=corners,
            )
        )
    if not annotations:
        raise SystemExit(f"no annotations found in {path}")
    return output_size, annotations


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


if __name__ == "__main__":
    main()
