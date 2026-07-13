from pathlib import Path

import pytest

from screen_normalize.experiments.run_io import (
    ABLATION_METHOD_IDS,
    clip_directory,
    create_analysis_run,
    method_directory,
    read_json,
    write_json,
)


def test_run_paths_and_json(tmp_path: Path) -> None:
    run = create_analysis_run(tmp_path)
    clip = clip_directory(run, "static", "static_01")
    method = method_directory(run, "static", "static_01", "proposed")
    assert method == clip / "proposed"
    write_json(method / "metric.json", {"value": 1})
    assert read_json(method / "metric.json") == {"value": 1}


def test_unknown_method_is_rejected(tmp_path: Path) -> None:
    with pytest.raises(ValueError):
        method_directory(tmp_path, "static", "clip", "unknown")


def test_ablation_method_directories_are_supported(tmp_path: Path) -> None:
    for method in ABLATION_METHOD_IDS:
        path = method_directory(tmp_path, "static", "static_01", method)
        assert path == tmp_path / "static" / "static_01" / method
