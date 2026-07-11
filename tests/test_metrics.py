from pathlib import Path

from screen_normalize.metrics.geometry import evaluate_geometry
from screen_normalize.metrics.temporal import evaluate_temporal


def test_geometry_skips_without_annotations(tmp_path: Path) -> None:
    estimate = tmp_path / "estimate.csv"
    estimate.write_text("frame,tl_x,tl_y,tr_x,tr_y,br_x,br_y,bl_x,bl_y\n")
    summary = evaluate_geometry(tmp_path / "missing.mp4", None, estimate, tmp_path)
    assert summary["status"] == "skipped"


def test_temporal_marks_bad_input_failed(tmp_path: Path) -> None:
    estimate = tmp_path / "estimate.csv"
    estimate.write_text("bad\n")
    summary = evaluate_temporal(estimate, tmp_path)
    assert summary["status"] == "failed"
