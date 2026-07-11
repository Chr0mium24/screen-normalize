from pathlib import Path

from screen_normalize.reporting import render_clip_report, render_run_index
from screen_normalize.run_io import write_json


def test_reports_reference_existing_local_files(tmp_path: Path) -> None:
    video = tmp_path / "inputs" / "static" / "static_01.mp4"
    video.parent.mkdir(parents=True)
    video.touch()
    clip = tmp_path / "runs" / "run" / "static" / "static_01"
    method = clip / "proposed"
    method.mkdir(parents=True)
    (method / "normalized.mp4").touch()
    write_json(method / "geometry.json", {"status": "ok", "corner_rmse_px_mean": 1.0})
    report = render_clip_report(clip, video, "static", "static_01", ["proposed"])
    content = report.read_text()
    assert "normalized.mp4" in content and "static_01.mp4" in content

    index = render_run_index(tmp_path / "runs" / "run", [{"category": "static", "clip_id": "static_01", "status": "ok", "reason": ""}])
    assert "static/static_01/report.html" in index.read_text()
