from __future__ import annotations

import json
import mimetypes
from dataclasses import dataclass
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, quote, urlparse

import cv2
import numpy as np

from .experiments.annotations import AnnotationError, load_annotations, save_annotations, validate_corners


CATEGORIES = ("static", "scrolling", "screen_video", "weak_border", "hard")
VIDEO_EXTENSIONS = {".mp4"}
IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png"}
MEDIA_EXTENSIONS = VIDEO_EXTENSIONS | IMAGE_EXTENSIONS


def select_keyframes(frame_count: int, frames_per_clip: int) -> list[int]:
    if frame_count <= 0:
        return []
    picks = np.linspace(0, max(0, frame_count - 2), max(1, frames_per_clip))
    return sorted({int(round(value)) for value in picks if 0 <= round(value) < frame_count})


def video_shape(path: Path) -> tuple[int, int, int]:
    capture = cv2.VideoCapture(str(path))
    if not capture.isOpened():
        raise ValueError(f"无法打开视频：{path.name}")
    width = int(capture.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(capture.get(cv2.CAP_PROP_FRAME_HEIGHT))
    count = int(capture.get(cv2.CAP_PROP_FRAME_COUNT))
    capture.release()
    if width <= 0 or height <= 0 or count <= 0:
        raise ValueError(f"视频信息无效：{path.name}")
    return width, height, count


def image_shape(path: Path) -> tuple[int, int, int]:
    image = cv2.imread(str(path), cv2.IMREAD_COLOR)
    if image is None:
        raise ValueError(f"无法打开图片：{path.name}")
    height, width = image.shape[:2]
    if width <= 0 or height <= 0:
        raise ValueError(f"图片信息无效：{path.name}")
    return width, height, 1


def media_shape(path: Path) -> tuple[int, int, int]:
    if path.suffix.lower() in IMAGE_EXTENSIONS:
        return image_shape(path)
    return video_shape(path)


def media_keyframes(path: Path, frame_count: int, frames_per_clip: int) -> list[int]:
    if path.suffix.lower() in IMAGE_EXTENSIONS:
        return [0]
    return select_keyframes(frame_count, frames_per_clip)


def read_media_frame(path: Path, frame_index: int) -> np.ndarray:
    if path.suffix.lower() in IMAGE_EXTENSIONS:
        if frame_index != 0:
            raise ValueError("图片只有第 0 帧")
        image = cv2.imread(str(path), cv2.IMREAD_COLOR)
        if image is None:
            raise ValueError(f"无法读取图片：{path.name}")
        return image

    capture = cv2.VideoCapture(str(path))
    capture.set(cv2.CAP_PROP_POS_FRAMES, frame_index)
    ok, frame = capture.read()
    capture.release()
    if not ok:
        raise ValueError(f"无法读取第 {frame_index} 帧")
    return frame


@dataclass(frozen=True)
class AnnotationStore:
    input_dir: Path
    frames_per_clip: int = 5

    def __post_init__(self) -> None:
        object.__setattr__(self, "input_dir", self.input_dir.resolve())

    def media_paths(self, category: str) -> list[Path]:
        category_dir = self.input_dir / category
        if not category_dir.is_dir():
            return []

        paths = [path for path in category_dir.iterdir() if path.suffix.lower() in MEDIA_EXTENSIONS]
        segments_dir = category_dir / "segments"
        if segments_dir.is_dir():
            paths.extend(path for path in segments_dir.rglob("*") if path.suffix.lower() in MEDIA_EXTENSIONS)

        return sorted(set(paths), key=lambda path: path.relative_to(self.input_dir).as_posix())

    def video_item(self, path: Path, category: str) -> dict[str, object]:
        item: dict[str, object] = {
            "id": path.relative_to(self.input_dir).as_posix(),
            "name": path.name,
            "category": category,
            "mediaType": "image" if path.suffix.lower() in IMAGE_EXTENSIONS else "video",
        }
        try:
            width, height, count = media_shape(path)
            keyframes = media_keyframes(path, count, self.frames_per_clip)
            annotations = load_annotations(path.with_suffix(".csv"), width, height)
            done = sum(frame in annotations for frame in keyframes)
            item.update(
                width=width,
                height=height,
                frameCount=count,
                keyframes=keyframes,
                done=done,
                total=len(keyframes),
                status=(
                    "complete"
                    if keyframes and done == len(keyframes)
                    else ("started" if done else "pending")
                ),
            )
        except (ValueError, AnnotationError) as exc:
            item.update(done=0, total=0, status="error", error=str(exc))
        return item

    def videos(self) -> list[dict[str, object]]:
        result: list[dict[str, object]] = []
        for category in CATEGORIES:
            for path in self.media_paths(category):
                result.append(self.video_item(path, category))
        return result

    def resolve_video(self, video_id: str) -> Path:
        candidate = (self.input_dir / video_id).resolve()
        try:
            candidate.relative_to(self.input_dir)
        except ValueError as exc:
            raise ValueError("视频路径超出输入目录") from exc
        if candidate.suffix.lower() not in MEDIA_EXTENSIONS or not candidate.is_file():
            raise FileNotFoundError("媒体不存在")
        return candidate

    def annotations(self, video_id: str) -> tuple[Path, int, int, dict[int, np.ndarray]]:
        video = self.resolve_video(video_id)
        width, height, _ = media_shape(video)
        return video, width, height, load_annotations(video.with_suffix(".csv"), width, height)

    def frame_jpeg(self, video_id: str, frame_index: int) -> bytes:
        video = self.resolve_video(video_id)
        _, _, count = media_shape(video)
        if not 0 <= frame_index < count:
            raise ValueError("帧号超出视频范围")
        frame = read_media_frame(video, frame_index)
        encoded, data = cv2.imencode(".jpg", frame, [cv2.IMWRITE_JPEG_QUALITY, 92])
        if not encoded:
            raise ValueError("无法编码媒体帧")
        return data.tobytes()

    def save(self, video_id: str, frame: int, corners: object) -> dict[str, object]:
        video, width, height, annotations = self.annotations(video_id)
        _, _, count = media_shape(video)
        if not 0 <= frame < count:
            raise AnnotationError("帧号超出视频范围")
        annotations[frame] = validate_corners(np.asarray(corners, dtype=np.float32), width, height)
        save_annotations(video.with_suffix(".csv"), annotations, width, height)
        return {"ok": True, "frame": frame}

    def delete(self, video_id: str, frame: int) -> dict[str, object]:
        video, width, height, annotations = self.annotations(video_id)
        existed = annotations.pop(frame, None) is not None
        save_annotations(video.with_suffix(".csv"), annotations, width, height)
        return {"ok": True, "deleted": existed}

    def preview_jpeg(self, video_id: str, frame: int, corners: object) -> bytes:
        video = self.resolve_video(video_id)
        width, height, count = media_shape(video)
        if not 0 <= frame < count:
            raise ValueError("帧号超出视频范围")
        points = validate_corners(np.asarray(corners, dtype=np.float32), width, height)
        image = read_media_frame(video, frame)
        destination = np.asarray([[0, 0], [1919, 0], [1919, 1079], [0, 1079]], np.float32)
        warped = cv2.warpPerspective(image, cv2.getPerspectiveTransform(points, destination), (1920, 1080))
        preview = cv2.resize(warped, (480, 270), interpolation=cv2.INTER_AREA)
        encoded, data = cv2.imencode(".jpg", preview, [cv2.IMWRITE_JPEG_QUALITY, 88])
        if not encoded:
            raise ValueError("无法编码透视预览")
        return data.tobytes()


def make_handler(store: AnnotationStore, static_dir: Path) -> type[BaseHTTPRequestHandler]:
    class Handler(BaseHTTPRequestHandler):
        def log_message(self, fmt: str, *args: object) -> None:
            print(f"[annotation-web] {self.address_string()} {fmt % args}")

        def send_bytes(self, data: bytes, content_type: str, status: int = 200) -> None:
            self.send_response(status)
            self.send_header("Content-Type", content_type)
            self.send_header("Content-Length", str(len(data)))
            self.send_header("Cache-Control", "no-store")
            self.end_headers()
            self.wfile.write(data)

        def send_json(self, value: object, status: int = 200) -> None:
            self.send_bytes(json.dumps(value, ensure_ascii=False).encode(), "application/json; charset=utf-8", status)

        def body(self) -> dict[str, object]:
            length = int(self.headers.get("Content-Length", "0"))
            return json.loads(self.rfile.read(length) or b"{}")

        def query(self) -> dict[str, str]:
            return {key: values[0] for key, values in parse_qs(urlparse(self.path).query).items()}

        def handle_error(self, exc: Exception) -> None:
            status = HTTPStatus.NOT_FOUND if isinstance(exc, FileNotFoundError) else HTTPStatus.BAD_REQUEST
            self.send_json({"error": str(exc)}, status)

        def do_GET(self) -> None:
            try:
                path = urlparse(self.path).path
                if path == "/api/videos":
                    self.send_json({"videos": store.videos(), "framesPerClip": store.frames_per_clip})
                elif path == "/api/annotations":
                    _, _, _, values = store.annotations(self.query()["video"])
                    self.send_json({"annotations": {str(k): v.tolist() for k, v in values.items()}})
                elif path == "/api/frame":
                    query = self.query()
                    self.send_bytes(store.frame_jpeg(query["video"], int(query["frame"])), "image/jpeg")
                elif path == "/" or path == "/index.html":
                    self.send_bytes((static_dir / "annotation.html").read_bytes(), "text/html; charset=utf-8")
                else:
                    file = (static_dir / path.lstrip("/")).resolve()
                    if static_dir.resolve() not in file.parents or not file.is_file():
                        raise FileNotFoundError("页面资源不存在")
                    self.send_bytes(file.read_bytes(), mimetypes.guess_type(file.name)[0] or "application/octet-stream")
            except (Exception, KeyError) as exc:
                self.handle_error(exc)

        def do_POST(self) -> None:
            try:
                path = urlparse(self.path).path
                data = self.body()
                if path == "/api/annotations":
                    self.send_json(store.save(str(data["video"]), int(data["frame"]), data["corners"]))
                elif path == "/api/preview":
                    self.send_bytes(store.preview_jpeg(str(data["video"]), int(data["frame"]), data["corners"]), "image/jpeg")
                else:
                    raise FileNotFoundError("接口不存在")
            except (Exception, KeyError, TypeError) as exc:
                self.handle_error(exc)

        def do_DELETE(self) -> None:
            try:
                query = self.query()
                self.send_json(store.delete(query["video"], int(query["frame"])))
            except (Exception, KeyError) as exc:
                self.handle_error(exc)

    return Handler


def serve(input_dir: Path, host: str, port: int, frames_per_clip: int) -> ThreadingHTTPServer:
    store = AnnotationStore(input_dir, frames_per_clip)
    static_dir = Path(__file__).with_name("web")
    return ThreadingHTTPServer((host, port), make_handler(store, static_dir))


def browser_url(host: str, port: int) -> str:
    return f"http://{'127.0.0.1' if host in ('0.0.0.0', '::') else host}:{port}/"
