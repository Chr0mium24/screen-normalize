from __future__ import annotations

import cv2
import numpy as np

from .geometry import detected_corners_are_valid, order_corners


def detect_screen_corners(frame: np.ndarray) -> np.ndarray | None:
    hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
    mask = cv2.inRange(hsv, (85, 20, 50), (130, 255, 255))
    mask = cv2.morphologyEx(
        mask,
        cv2.MORPH_CLOSE,
        cv2.getStructuringElement(cv2.MORPH_RECT, (25, 25)),
        iterations=2,
    )
    mask = cv2.morphologyEx(
        mask,
        cv2.MORPH_OPEN,
        cv2.getStructuringElement(cv2.MORPH_RECT, (5, 5)),
        iterations=1,
    )

    contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    if not contours:
        return None

    contour = max(contours, key=cv2.contourArea)
    frame_area = frame.shape[0] * frame.shape[1]
    if cv2.contourArea(contour) < frame_area * 0.20:
        return None

    perimeter = cv2.arcLength(contour, True)
    for epsilon_fraction in (0.010, 0.012, 0.015, 0.018, 0.020, 0.025, 0.030, 0.040):
        approximate = cv2.approxPolyDP(contour, epsilon_fraction * perimeter, True)
        if len(approximate) != 4:
            continue

        corners = order_corners(approximate.reshape(-1, 2))
        if detected_corners_are_valid(corners, frame.shape):
            return corners

    return None


def corner_mask(shape: tuple[int, ...], corners: np.ndarray, inset_pixels: int = 12) -> np.ndarray:
    mask = np.zeros(shape[:2], dtype=np.uint8)
    cv2.fillConvexPoly(mask, corners.astype(np.int32), 255)
    if inset_pixels > 0:
        kernel = cv2.getStructuringElement(
            cv2.MORPH_ELLIPSE,
            (inset_pixels * 2 + 1, inset_pixels * 2 + 1),
        )
        mask = cv2.erode(mask, kernel, iterations=1)
    return mask


def select_tracking_points(gray: np.ndarray, corners: np.ndarray) -> np.ndarray | None:
    points = cv2.goodFeaturesToTrack(
        gray,
        maxCorners=900,
        qualityLevel=0.005,
        minDistance=8,
        mask=corner_mask(gray.shape, corners),
        blockSize=7,
    )
    if points is None or len(points) < 12:
        return None
    return points.astype(np.float32)
