from __future__ import annotations

import cv2
import numpy as np


def weighted_median(values: np.ndarray, weights: np.ndarray) -> float:
    if len(values) == 0:
        return float("nan")
    order = np.argsort(values)
    sorted_values = values[order]
    sorted_weights = weights[order]
    midpoint = sorted_weights.sum() * 0.5
    return float(sorted_values[np.searchsorted(np.cumsum(sorted_weights), midpoint)])


def line_roll_mask(
    shape: tuple[int, ...],
    top_fraction: float,
    right_fraction: float,
    bottom_fraction: float,
    ignore_top_fraction: float,
) -> np.ndarray:
    height, width = shape[:2]
    mask = np.zeros((height, width), dtype=np.uint8)
    if top_fraction:
        mask[: int(round(height * top_fraction)), :] = 255
    if right_fraction:
        mask[:, int(round(width * (1.0 - right_fraction))) :] = 255
    if bottom_fraction:
        mask[int(round(height * (1.0 - bottom_fraction))) :, :] = 255
    if ignore_top_fraction:
        mask[: int(round(height * ignore_top_fraction)), :] = 0
    return mask


def normalize_line_angle_degrees(angle: float) -> float:
    while angle <= -90.0:
        angle += 180.0
    while angle > 90.0:
        angle -= 180.0
    return angle


def hough_line_candidates(
    frame: np.ndarray,
    mask: np.ndarray,
    angle_limit: float,
) -> list[dict[str, object]]:
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    masked = cv2.bitwise_and(gray, gray, mask=mask)
    edges = cv2.Canny(masked, 60, 160)
    min_line_length = max(140, gray.shape[1] // 10)
    lines = cv2.HoughLinesP(
        edges,
        1,
        np.pi / 180.0,
        threshold=110,
        minLineLength=min_line_length,
        maxLineGap=18,
    )
    candidates: list[dict[str, object]] = []
    if lines is None:
        return candidates

    for x1, y1, x2, y2 in lines.reshape(-1, 4):
        length = float(np.hypot(x2 - x1, y2 - y1))
        if length < min_line_length:
            continue
        angle = normalize_line_angle_degrees(
            float(np.degrees(np.arctan2(y2 - y1, x2 - x1)))
        )
        if abs(angle) > angle_limit:
            continue
        candidates.append({"angle": angle, "length": length})
    return candidates


def contour_line_candidates(
    frame: np.ndarray,
    mask: np.ndarray,
    angle_limit: float,
    horizontal_kernel: int,
    max_thickness: int,
) -> list[dict[str, object]]:
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    masked = cv2.bitwise_and(gray, gray, mask=mask)
    blurred = cv2.GaussianBlur(masked, (3, 3), 0)
    edges = cv2.Canny(blurred, 60, 160)
    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (horizontal_kernel, 1))
    horizontal = cv2.morphologyEx(edges, cv2.MORPH_OPEN, kernel)
    contours, _ = cv2.findContours(horizontal, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    min_line_length = max(180, gray.shape[1] // 8)
    candidates: list[dict[str, object]] = []
    for contour in contours:
        if len(contour) < 2:
            continue
        (_, _), (rect_width, rect_height), rect_angle = cv2.minAreaRect(contour)
        long_side = float(max(rect_width, rect_height))
        short_side = float(min(rect_width, rect_height))
        if long_side < min_line_length or short_side > max_thickness:
            continue

        angle = float(rect_angle)
        if rect_width < rect_height:
            angle += 90.0
        angle = normalize_line_angle_degrees(angle)
        if abs(angle) > angle_limit:
            continue
        candidates.append({"angle": angle, "length": long_side})
    return candidates


def binary_foreground_mask(
    frame: np.ndarray,
    mask: np.ndarray,
    white_threshold: int,
    background_percentile: float,
    dark_margin: float,
    saturation_threshold: int,
) -> np.ndarray:
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
    masked_gray = gray[mask > 0]
    if masked_gray.size:
        background_level = min(
            float(white_threshold),
            float(np.percentile(masked_gray, background_percentile)),
        )
    else:
        background_level = float(np.percentile(gray, background_percentile))
    dark_threshold = max(0.0, background_level - dark_margin)
    color_threshold = max(0.0, background_level - (dark_margin * 0.5))
    foreground = np.where(
        (gray < dark_threshold)
        | ((hsv[:, :, 1] > saturation_threshold) & (gray < color_threshold)),
        255,
        0,
    ).astype(np.uint8)
    return cv2.bitwise_and(foreground, foreground, mask=mask)


def binary_horizontal_edge_mask(foreground: np.ndarray, horizontal_kernel: int) -> np.ndarray:
    boundary_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (3, 3))
    boundary = cv2.morphologyEx(foreground, cv2.MORPH_GRADIENT, boundary_kernel)
    close_width = max(3, horizontal_kernel // 4)
    close_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (close_width, 3))
    connected = cv2.morphologyEx(boundary, cv2.MORPH_CLOSE, close_kernel)
    line_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (horizontal_kernel, 3))
    return cv2.morphologyEx(connected, cv2.MORPH_OPEN, line_kernel)


def binary_contour_line_candidates(
    frame: np.ndarray,
    mask: np.ndarray,
    angle_limit: float,
    horizontal_kernel: int,
    max_thickness: int,
    white_threshold: int,
    background_percentile: float,
    dark_margin: float,
    saturation_threshold: int,
) -> list[dict[str, object]]:
    full_mask = np.full(mask.shape, 255, dtype=np.uint8)
    full_foreground = binary_foreground_mask(
        frame,
        full_mask,
        white_threshold=white_threshold,
        background_percentile=background_percentile,
        dark_margin=dark_margin,
        saturation_threshold=saturation_threshold,
    )
    candidates = binary_component_line_candidates(
        full_foreground,
        selection_mask=mask,
        angle_limit=angle_limit,
        min_line_length=max(180, frame.shape[1] // 8),
        min_area=frame.shape[0] * frame.shape[1] * 0.002,
        min_short_side=max(28.0, float(max_thickness)),
    )
    foreground = cv2.bitwise_and(full_foreground, full_foreground, mask=mask)
    horizontal = binary_horizontal_edge_mask(foreground, horizontal_kernel=horizontal_kernel)
    contours, _ = cv2.findContours(horizontal, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    min_line_length = max(180, frame.shape[1] // 8)
    for contour in contours:
        if len(contour) < 2:
            continue
        (_, _), (rect_width, rect_height), rect_angle = cv2.minAreaRect(contour)
        long_side = float(max(rect_width, rect_height))
        short_side = float(min(rect_width, rect_height))
        if long_side < min_line_length or short_side > max_thickness:
            continue

        angle = float(rect_angle)
        if rect_width < rect_height:
            angle += 90.0
        angle = normalize_line_angle_degrees(angle)
        if abs(angle) > angle_limit:
            continue
        candidates.append({"angle": angle, "length": long_side})
    return candidates


def binary_component_line_candidates(
    foreground: np.ndarray,
    selection_mask: np.ndarray,
    angle_limit: float,
    min_line_length: int,
    min_area: float,
    min_short_side: float,
) -> list[dict[str, object]]:
    contours, _ = cv2.findContours(foreground, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    height, width = foreground.shape[:2]
    candidates: list[dict[str, object]] = []
    for contour in contours:
        if len(contour) < 2:
            continue
        area = float(cv2.contourArea(contour))
        if area < min_area:
            continue

        x, y, box_width, box_height = cv2.boundingRect(contour)
        if np.count_nonzero(selection_mask[y : y + box_height, x : x + box_width]) == 0:
            continue
        touches_frame = (
            x <= 1
            or y <= 1
            or x + box_width >= width - 1
            or y + box_height >= height - 1
        )
        if touches_frame and (box_width > width * 0.90 or box_height > height * 0.90):
            continue

        (_, _), (rect_width, rect_height), rect_angle = cv2.minAreaRect(contour)
        long_side = float(max(rect_width, rect_height))
        short_side = float(min(rect_width, rect_height))
        if long_side < min_line_length or short_side < min_short_side:
            continue

        rect_area = max(float(rect_width * rect_height), 1.0)
        fill_ratio = area / rect_area
        aspect_ratio = long_side / max(short_side, 1.0)
        if fill_ratio < 0.35 or aspect_ratio < 1.2:
            continue

        angle = float(rect_angle)
        if rect_width < rect_height:
            angle += 90.0
        angle = normalize_line_angle_degrees(angle)
        if abs(angle) > angle_limit:
            continue
        candidates.append({"angle": angle, "length": long_side * min(fill_ratio, 1.0)})
    return candidates


def estimate_line_roll_angle(
    frame: np.ndarray,
    detector: str,
    full_mask: bool,
    top_fraction: float,
    right_fraction: float,
    bottom_fraction: float,
    ignore_top_fraction: float,
    min_segments: int,
    min_total_length: int,
    cluster_deg: float,
    horizontal_kernel: int,
    max_thickness: int,
    white_threshold: int,
    background_percentile: float,
    dark_margin: float,
    saturation_threshold: int,
) -> tuple[float | None, int, float]:
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    if full_mask:
        mask = np.full(gray.shape, 255, dtype=np.uint8)
        if ignore_top_fraction:
            mask[: int(round(gray.shape[0] * ignore_top_fraction)), :] = 0
    else:
        mask = line_roll_mask(
            gray.shape,
            top_fraction,
            right_fraction,
            bottom_fraction,
            ignore_top_fraction,
        )
    if detector == "binary-contour":
        candidates = binary_contour_line_candidates(
            frame,
            mask,
            angle_limit=3.0,
            horizontal_kernel=horizontal_kernel,
            max_thickness=max_thickness,
            white_threshold=white_threshold,
            background_percentile=background_percentile,
            dark_margin=dark_margin,
            saturation_threshold=saturation_threshold,
        )
    elif detector == "contour":
        candidates = contour_line_candidates(
            frame,
            mask,
            angle_limit=3.0,
            horizontal_kernel=horizontal_kernel,
            max_thickness=max_thickness,
        )
    else:
        candidates = hough_line_candidates(frame, mask, angle_limit=3.0)

    if len(candidates) < min_segments:
        total_length = sum(float(candidate["length"]) for candidate in candidates)
        return None, len(candidates), float(total_length)

    angle_values = np.asarray([candidate["angle"] for candidate in candidates], dtype=np.float32)
    weight_values = np.asarray([candidate["length"] for candidate in candidates], dtype=np.float32)
    dominant_angle = weighted_median(angle_values, weight_values)
    inlier_mask = np.abs(angle_values - dominant_angle) <= cluster_deg
    angle_values = angle_values[inlier_mask]
    weight_values = weight_values[inlier_mask]
    total_length = float(weight_values.sum())
    if len(angle_values) < min_segments:
        return None, int(len(angle_values)), total_length
    if total_length < min_total_length:
        return None, int(len(angle_values)), total_length

    return weighted_median(angle_values, weight_values), int(len(angle_values)), total_length


def update_line_roll_angle(
    previous_angle: float | None,
    measured_angle: float,
    max_correction: float,
    max_step: float,
    smooth: float,
) -> float:
    target = float(np.clip(measured_angle, -max_correction, max_correction))
    if previous_angle is None:
        return target

    smoothed = previous_angle * smooth + target * (1.0 - smooth)
    if max_step > 0:
        smoothed = previous_angle + float(np.clip(smoothed - previous_angle, -max_step, max_step))
    return float(np.clip(smoothed, -max_correction, max_correction))


def apply_roll_correction(frame: np.ndarray, angle: float) -> np.ndarray:
    height, width = frame.shape[:2]
    center = ((width - 1) / 2.0, (height - 1) / 2.0)
    transform = cv2.getRotationMatrix2D(center, angle, 1.0)
    return cv2.warpAffine(
        frame,
        transform,
        (width, height),
        flags=cv2.INTER_CUBIC,
        borderMode=cv2.BORDER_REPLICATE,
    )
