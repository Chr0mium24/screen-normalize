from pathlib import Path

import numpy as np
import pytest

from screen_normalize.experiments.annotations import AnnotationError, load_annotations, save_annotations


VALID = np.asarray([[10, 10], [90, 12], [88, 80], [12, 82]], dtype=np.float32)


def test_annotation_round_trip_and_overwrite(tmp_path: Path) -> None:
    path = tmp_path / "clip.csv"
    save_annotations(path, {30: VALID, 0: VALID + 1}, 100, 100)
    loaded = load_annotations(path, 100, 100)
    assert list(loaded) == [0, 30]
    np.testing.assert_allclose(loaded[30], VALID)

    save_annotations(path, {0: VALID + 2}, 100, 100)
    assert list(load_annotations(path, 100, 100)) == [0]


def test_annotation_rejects_invalid_quad(tmp_path: Path) -> None:
    invalid = VALID[[0, 2, 1, 3]]
    with pytest.raises(AnnotationError):
        save_annotations(tmp_path / "clip.csv", {0: invalid}, 100, 100)
