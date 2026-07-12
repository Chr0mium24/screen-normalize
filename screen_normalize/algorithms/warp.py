from __future__ import annotations

import cv2
import numpy as np

from .detection import detect_screen_corners
from .geometry import order_corners


def warp_screen_frame(
    frame: np.ndarray,
    frame_index: int,
    fallback_corners: np.ndarray,
    fallback_transform: np.ndarray,
    destination_corners: np.ndarray,
    corner_trajectory: list[np.ndarray] | None,
    last_corners: np.ndarray | None,
    width: int,
    height: int,
    smooth: float,
    auto_detect: bool,
    crop_left: float,
    crop_top: float,
    crop_right: float,
    crop_bottom: float,
) -> tuple[np.ndarray, np.ndarray | None]:
    if corner_trajectory is not None:
        source_corners = corner_trajectory[min(frame_index, len(corner_trajectory) - 1)]
        transform = cv2.getPerspectiveTransform(source_corners, destination_corners)
    elif auto_detect:
        detected_corners = detect_screen_corners(frame)
        if detected_corners is None:
            source_corners = last_corners if last_corners is not None else fallback_corners
        elif last_corners is None:
            source_corners = detected_corners
        else:
            source_corners = (last_corners * smooth) + (detected_corners * (1.0 - smooth))
        last_corners = source_corners
        transform = cv2.getPerspectiveTransform(source_corners, destination_corners)
    else:
        transform = fallback_transform

    warped = cv2.warpPerspective(
        frame,
        transform,
        (width, height),
        flags=cv2.INTER_CUBIC,
        borderMode=cv2.BORDER_REPLICATE,
    )
    if crop_left or crop_top or crop_right or crop_bottom:
        x1 = int(round(width * crop_left))
        y1 = int(round(height * crop_top))
        x2 = int(round(width * (1.0 - crop_right)))
        y2 = int(round(height * (1.0 - crop_bottom)))
        if x1 >= x2 or y1 >= y2:
            raise SystemExit("crop values leave no output area")
        warped = cv2.resize(
            warped[y1:y2, x1:x2],
            (width, height),
            interpolation=cv2.INTER_CUBIC,
        )
    return warped, last_corners
