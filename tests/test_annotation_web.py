from pathlib import Path

import cv2
import numpy as np

from screen_normalize.annotation_web import AnnotationStore, select_keyframes


def make_video(path: Path, frames: int = 8) -> None:
    path.parent.mkdir(parents=True)
    writer = cv2.VideoWriter(str(path), cv2.VideoWriter_fourcc(*"mp4v"), 5, (100, 80))
    assert writer.isOpened()
    for index in range(frames):
        writer.write(np.full((80, 100, 3), index * 10, dtype=np.uint8))
    writer.release()


def test_select_keyframes_matches_batch_policy() -> None:
    assert select_keyframes(1, 5) == [0]
    assert select_keyframes(10, 5) == [0, 2, 4, 6, 8]
    assert select_keyframes(0, 5) == []


def test_store_discovers_saves_and_deletes_annotations(tmp_path: Path) -> None:
    video = tmp_path / "static" / "segments" / "clip.mp4"
    make_video(video)
    store = AnnotationStore(tmp_path, frames_per_clip=3)

    [item] = store.videos()
    assert item["id"] == "static/segments/clip.mp4"
    assert item["keyframes"] == [0, 3, 6]
    assert item["status"] == "pending"
    assert store.frame_jpeg(item["id"], 3).startswith(b"\xff\xd8")

    corners = [[10, 10], [90, 10], [90, 70], [10, 70]]
    store.save(item["id"], 0, corners)
    assert store.videos()[0]["done"] == 1
    assert store.annotations(item["id"])[3][0].shape == (4, 2)
    assert store.preview_jpeg(item["id"], 0, corners).startswith(b"\xff\xd8")

    assert store.delete(item["id"], 0)["deleted"] is True
    assert store.annotations(item["id"])[3] == {}


def test_store_saves_and_deletes_moire_rois(tmp_path: Path) -> None:
    video = tmp_path / "scrolling" / "clip.mp4"
    make_video(video)
    store = AnnotationStore(tmp_path, frames_per_clip=3)
    [item] = store.videos()

    rois = [
        {"x1": 10, "y1": 12, "x2": 42, "y2": 48, "label": "moire", "notes": "white area"},
        {"x1": 50, "y1": 20, "x2": 80, "y2": 55, "label": "moire", "notes": ""},
    ]
    assert store.save_rois(item["id"], 3, rois) == {"ok": True, "frame": 3, "rois": 2}

    _, _, _, saved = store.moire_rois(item["id"])
    assert len(saved[3]) == 2
    assert saved[3][0]["roi_id"] == "roi_01"
    assert saved[3][0]["x1"] == 10.0
    assert (video.parent / "clip_moire_rois.csv").exists()

    assert store.delete_rois(item["id"], 3)["deleted"] is True
    assert store.moire_rois(item["id"])[3] == {}


def test_store_rejects_path_escape(tmp_path: Path) -> None:
    store = AnnotationStore(tmp_path)
    try:
        store.resolve_video("../outside.mp4")
    except ValueError as exc:
        assert "超出" in str(exc)
    else:
        raise AssertionError("path escape should be rejected")
