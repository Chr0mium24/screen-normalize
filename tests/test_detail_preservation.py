import cv2
import numpy as np

from screen_normalize.metrics.detail_preservation import evaluate_detail_preservation_pair


def test_detail_preservation_identical_images_are_near_perfect() -> None:
    image = np.zeros((96, 128, 3), dtype=np.uint8)
    image[:, 20:24] = 255
    image[40:44, :] = 180

    summary = evaluate_detail_preservation_pair(image, image)

    assert summary["ssim"] > 0.999
    assert summary["gradient_magnitude_similarity"] > 0.999
    assert abs(summary["gradient_magnitude_ratio"] - 1.0) < 1e-9
    assert summary["edge_f1"] > 0.999
    assert abs(summary["laplacian_energy_ratio"] - 1.0) < 1e-9


def test_detail_preservation_detects_blur_detail_loss() -> None:
    reference = np.zeros((96, 128, 3), dtype=np.uint8)
    reference[:, ::4] = 255
    blurred = cv2.GaussianBlur(reference, (9, 9), 2.0)

    summary = evaluate_detail_preservation_pair(reference, blurred)

    assert summary["ssim"] < 1.0
    assert summary["gradient_magnitude_ratio"] < 1.0
    assert summary["laplacian_energy_ratio"] < 1.0
