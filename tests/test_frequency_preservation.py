import numpy as np

from screen_normalize.metrics.frequency_preservation import evaluate_frequency_preservation_pair


def test_frequency_preservation_identical_images_are_near_perfect() -> None:
    image = np.zeros((96, 128, 3), dtype=np.uint8)
    image[:, 20:24] = 255
    image[40:44, :] = 180

    summary = evaluate_frequency_preservation_pair(image, image)

    assert summary["log_fft_magnitude_similarity"] > 0.999
    assert abs(summary["high_frequency_energy_ratio"] - 1.0) < 1e-9
    assert summary["orientation_histogram_intersection"] > 0.999
    assert abs(summary["band_energy_ratio"] - 1.0) < 1e-9


def test_frequency_preservation_detects_blur_energy_loss() -> None:
    reference = np.zeros((96, 128, 3), dtype=np.uint8)
    reference[:, ::4] = 255
    blurred = reference.copy()
    blurred[:, ::4] = 80

    summary = evaluate_frequency_preservation_pair(reference, blurred)

    assert summary["high_frequency_energy_ratio"] < 1.0
    assert summary["band_energy_ratio"] < 1.0
