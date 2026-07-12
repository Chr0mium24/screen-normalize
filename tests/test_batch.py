from pathlib import Path

from scripts.make_paper_results import aggregate_table, collect
from scripts.run_batch import select_videos
from screen_normalize.run_io import write_json


def test_video_selection_and_limit(tmp_path: Path) -> None:
    for category in ("static", "hard"):
        directory = tmp_path / category
        directory.mkdir()
        (directory / f"{category}_01.mp4").touch()
    assert len(select_videos(tmp_path, None, ["static"], 0)) == 1
    assert len(select_videos(tmp_path, None, None, 1)) == 1


def test_summary_collects_only_metric_json(tmp_path: Path) -> None:
    method = tmp_path / "static" / "static_01" / "proposed"
    write_json(method / "geometry.json", {"status": "ok", "corner_rmse_px_mean": 2.0})
    write_json(method / "method.json", {"status": "ok"})
    rows = collect(tmp_path)
    assert len(rows) == 1 and rows[0]["clip_id"] == "static_01"
    aggregate = aggregate_table(rows)
    assert aggregate[0]["n"] == 1
    assert aggregate[0]["median"] == 2.0
