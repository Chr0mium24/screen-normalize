from __future__ import annotations

import cv2
import numpy as np


def weighted_median(values: np.ndarray, weights: np.ndarray) -> float:
    order = np.argsort(values)
    sorted_values = values[order]
    sorted_weights = weights[order]
    midpoint = sorted_weights.sum() * 0.5
    return float(sorted_values[np.searchsorted(np.cumsum(sorted_weights), midpoint)])


def line_roll_mask(
    shape: tuple[int, ...],
    top: float,
    right: float,
    bottom: float,
    ignore_top: float,
) -> np.ndarray:
    height, width = shape[:2]
    mask = np.zeros((height, width), dtype=np.uint8)
    if top:
        mask[: int(round(height * top)), :] = 255
    if right:
        mask[:, int(round(width * (1.0 - right))) :] = 255
    if bottom:
        mask[int(round(height * (1.0 - bottom))) :, :] = 255
    if ignore_top:
        mask[: int(round(height * ignore_top)), :] = 0
    return mask


def normalize_line_angle_degrees(angle: float) -> float:
    while angle <= -90.0:
        angle += 180.0
    while angle > 90.0:
        angle -= 180.0
    return angle


def group_line_candidates(
    candidates: list[dict[str, object]],
    cluster_deg: float,
    min_segments: int,
    min_total_length: int,
) -> dict[str, object]:
    if not candidates:
        return {
            "candidates": candidates,
            "inliers": [],
            "dominant_angle": None,
            "accepted_angle": None,
            "total_length": 0.0,
            "accepted": False,
        }

    angles = np.asarray([line["angle"] for line in candidates], dtype=np.float32)
    lengths = np.asarray([line["length"] for line in candidates], dtype=np.float32)
    dominant_angle = weighted_median(angles, lengths)
    inliers = [
        line for line in candidates if abs(float(line["angle"]) - dominant_angle) <= cluster_deg
    ]
    total_length = float(sum(float(line["length"]) for line in inliers))
    if inliers:
        inlier_angles = np.asarray([line["angle"] for line in inliers], dtype=np.float32)
        inlier_lengths = np.asarray([line["length"] for line in inliers], dtype=np.float32)
        accepted_angle = weighted_median(inlier_angles, inlier_lengths)
    else:
        accepted_angle = None

    accepted = (
        accepted_angle is not None
        and len(inliers) >= min_segments
        and total_length >= min_total_length
    )
    return {
        "candidates": candidates,
        "inliers": inliers,
        "dominant_angle": dominant_angle,
        "accepted_angle": accepted_angle if accepted else None,
        "total_length": total_length,
        "accepted": accepted,
    }


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

    candidates = []
    if lines is not None:
        for x1, y1, x2, y2 in lines.reshape(-1, 4):
            length = float(np.hypot(x2 - x1, y2 - y1))
            if length < min_line_length:
                continue
            angle = normalize_line_angle_degrees(
                float(np.degrees(np.arctan2(y2 - y1, x2 - x1)))
            )
            if abs(angle) > angle_limit:
                continue
            candidates.append(
                {
                    "p1": (int(x1), int(y1)),
                    "p2": (int(x2), int(y2)),
                    "angle": angle,
                    "length": length,
                }
            )

    return candidates


def contour_line_candidates(
    frame: np.ndarray,
    mask: np.ndarray,
    angle_limit: float,
    horizontal_kernel: int,
    max_line_thickness: int,
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
        rect = cv2.minAreaRect(contour)
        (cx, cy), (rect_width, rect_height), rect_angle = rect
        long_side = float(max(rect_width, rect_height))
        short_side = float(min(rect_width, rect_height))
        if long_side < min_line_length or short_side > max_line_thickness:
            continue

        angle = float(rect_angle)
        if rect_width < rect_height:
            angle += 90.0
        angle = normalize_line_angle_degrees(angle)
        if abs(angle) > angle_limit:
            continue

        theta = np.deg2rad(angle)
        dx = np.cos(theta) * long_side * 0.5
        dy = np.sin(theta) * long_side * 0.5
        p1 = (int(round(cx - dx)), int(round(cy - dy)))
        p2 = (int(round(cx + dx)), int(round(cy + dy)))
        candidates.append(
            {
                "p1": p1,
                "p2": p2,
                "angle": angle,
                "length": long_side,
            }
        )

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
    max_line_thickness: int,
    white_threshold: int,
    background_percentile: float,
    dark_margin: float,
    saturation_threshold: int,
) -> tuple[list[dict[str, object]], np.ndarray, np.ndarray]:
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
        min_short_side=max(28.0, float(max_line_thickness)),
    )
    foreground = cv2.bitwise_and(full_foreground, full_foreground, mask=mask)
    horizontal = binary_horizontal_edge_mask(foreground, horizontal_kernel=horizontal_kernel)
    contours, _ = cv2.findContours(horizontal, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    min_line_length = max(180, frame.shape[1] // 8)
    for contour in contours:
        if len(contour) < 2:
            continue
        rect = cv2.minAreaRect(contour)
        (cx, cy), (rect_width, rect_height), rect_angle = rect
        long_side = float(max(rect_width, rect_height))
        short_side = float(min(rect_width, rect_height))
        if long_side < min_line_length or short_side > max_line_thickness:
            continue

        angle = float(rect_angle)
        if rect_width < rect_height:
            angle += 90.0
        angle = normalize_line_angle_degrees(angle)
        if abs(angle) > angle_limit:
            continue

        theta = np.deg2rad(angle)
        dx = np.cos(theta) * long_side * 0.5
        dy = np.sin(theta) * long_side * 0.5
        p1 = (int(round(cx - dx)), int(round(cy - dy)))
        p2 = (int(round(cx + dx)), int(round(cy + dy)))
        candidates.append(
            {
                "p1": p1,
                "p2": p2,
                "angle": angle,
                "length": long_side,
            }
        )

    return candidates, foreground, horizontal


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

        rect = cv2.minAreaRect(contour)
        (cx, cy), (rect_width, rect_height), rect_angle = rect
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

        p1, p2 = selected_component_edge(
            rect,
            selection_mask=selection_mask,
            angle_limit=angle_limit,
        )
        candidates.append(
            {
                "p1": p1,
                "p2": p2,
                "angle": angle,
                "length": long_side * min(fill_ratio, 1.0),
            }
        )
    return candidates


def selected_component_edge(
    rect: tuple[tuple[float, float], tuple[float, float], float],
    selection_mask: np.ndarray,
    angle_limit: float,
) -> tuple[tuple[int, int], tuple[int, int]]:
    box = cv2.boxPoints(rect)
    height, width = selection_mask.shape[:2]
    edges = []
    for index in range(4):
        p1 = box[index]
        p2 = box[(index + 1) % 4]
        length = float(np.hypot(*(p2 - p1)))
        if length <= 0:
            continue
        angle = normalize_line_angle_degrees(
            float(np.degrees(np.arctan2(p2[1] - p1[1], p2[0] - p1[0])))
        )
        if abs(angle) > angle_limit:
            continue
        midpoint = (p1 + p2) * 0.5
        mx = int(np.clip(round(float(midpoint[0])), 0, width - 1))
        my = int(np.clip(round(float(midpoint[1])), 0, height - 1))
        inside_mask = selection_mask[my, mx] > 0
        edges.append((inside_mask, length, p1, p2))
    if not edges:
        center, (rect_width, rect_height), rect_angle = rect
        angle = float(rect_angle)
        if rect_width < rect_height:
            angle += 90.0
        angle = normalize_line_angle_degrees(angle)
        theta = np.deg2rad(angle)
        long_side = max(rect_width, rect_height)
        dx = np.cos(theta) * long_side * 0.5
        dy = np.sin(theta) * long_side * 0.5
        cx, cy = center
        return (
            (int(round(cx - dx)), int(round(cy - dy))),
            (int(round(cx + dx)), int(round(cy + dy))),
        )

    _, _, start, end = max(edges, key=lambda item: (item[0], item[1]))
    return (
        (int(round(float(start[0]))), int(round(float(start[1])))),
        (int(round(float(end[0]))), int(round(float(end[1])))),
    )


def detect_lines(
    frame: np.ndarray,
    mask: np.ndarray,
    detector: str,
    angle_limit: float,
    cluster_deg: float,
    min_segments: int,
    min_total_length: int,
    horizontal_kernel: int,
    max_line_thickness: int,
    white_threshold: int,
    background_percentile: float,
    dark_margin: float,
    saturation_threshold: int,
) -> dict[str, object]:
    foreground = None
    horizontal = None
    if detector == "binary-contour":
        candidates, foreground, horizontal = binary_contour_line_candidates(
            frame,
            mask,
            angle_limit=angle_limit,
            horizontal_kernel=horizontal_kernel,
            max_line_thickness=max_line_thickness,
            white_threshold=white_threshold,
            background_percentile=background_percentile,
            dark_margin=dark_margin,
            saturation_threshold=saturation_threshold,
        )
    elif detector == "contour":
        candidates = contour_line_candidates(
            frame,
            mask,
            angle_limit=angle_limit,
            horizontal_kernel=horizontal_kernel,
            max_line_thickness=max_line_thickness,
        )
    else:
        candidates = hough_line_candidates(
            frame,
            mask,
            angle_limit=angle_limit,
        )

    detection = group_line_candidates(
        candidates,
        cluster_deg=cluster_deg,
        min_segments=min_segments,
        min_total_length=min_total_length,
    )
    detection["foreground_mask"] = foreground
    detection["horizontal_mask"] = horizontal
    return detection


def draw_overlay(
    frame: np.ndarray,
    mask: np.ndarray,
    detection: dict[str, object],
    frame_index: int,
    detector: str,
    view: str,
) -> np.ndarray:
    if view == "binary" and detection["foreground_mask"] is not None:
        output = cv2.cvtColor(cv2.bitwise_not(detection["foreground_mask"]), cv2.COLOR_GRAY2BGR)
    elif view == "horizontal" and detection["horizontal_mask"] is not None:
        output = cv2.cvtColor(detection["horizontal_mask"], cv2.COLOR_GRAY2BGR)
    else:
        output = frame.copy()
        mask_overlay = np.zeros_like(output)
        mask_overlay[mask > 0] = (255, 120, 0)
        output = cv2.addWeighted(output, 1.0, mask_overlay, 0.16, 0.0)

    inlier_ids = {id(line) for line in detection["inliers"]}
    for line in detection["candidates"]:
        color = (0, 220, 0) if id(line) in inlier_ids else (0, 165, 255)
        thickness = 2 if id(line) in inlier_ids else 1
        cv2.line(output, line["p1"], line["p2"], color, thickness, cv2.LINE_AA)

    accepted_angle = detection["accepted_angle"]
    dominant_angle = detection["dominant_angle"]
    status = "accepted" if detection["accepted"] else "rejected"
    text_lines = [
        f"frame {frame_index}",
        f"detector: {detector}",
        f"view: {view}",
        f"raw horizontal candidates: {len(detection['candidates'])}",
        f"same-direction inliers: {len(detection['inliers'])}",
        f"dominant angle: {dominant_angle:.3f} deg" if dominant_angle is not None else "dominant angle: none",
        f"accepted angle: {accepted_angle:.3f} deg" if accepted_angle is not None else "accepted angle: none",
        f"total inlier length: {float(detection['total_length']):.0f}px",
        f"status: {status}",
    ]
    x, y = 24, 36
    for text in text_lines:
        cv2.putText(output, text, (x, y), cv2.FONT_HERSHEY_SIMPLEX, 0.72, (0, 0, 0), 4)
        cv2.putText(output, text, (x, y), cv2.FONT_HERSHEY_SIMPLEX, 0.72, (255, 255, 255), 2)
        y += 30
    return output
