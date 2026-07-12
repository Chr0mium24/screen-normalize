from __future__ import annotations

import csv
from pathlib import Path


def write_tracker_debug_csv(path: Path, rows: list[dict[str, object]]) -> None:
    fieldnames = [
        "frame",
        "accepted",
        "reason",
        "point_count",
        "mature_point_count",
        "valid_count",
        "mature_valid_count",
        "inlier_count",
        "inlier_ratio",
        "reprojection_error",
        "coverage_x",
        "coverage_y",
        "rejected_updates",
        "area",
        "center_x",
        "center_y",
        "top_edge",
        "right_edge",
        "bottom_edge",
        "left_edge",
        "tl_x",
        "tl_y",
        "tr_x",
        "tr_y",
        "br_x",
        "br_y",
        "bl_x",
        "bl_y",
    ]
    with path.open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def write_trajectory_debug_csv(path: Path, rows: list[dict[str, object]]) -> None:
    labels = ("tl", "tr", "br", "bl")
    prefixes = ("raw", "interpolated", "smoothed")
    fieldnames = ["frame", "reliable"]
    for prefix in prefixes:
        for label in labels:
            fieldnames.extend([f"{prefix}_{label}_x", f"{prefix}_{label}_y"])
    with path.open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def write_align_debug_csv(path: Path, rows: list[dict[str, object]]) -> None:
    fieldnames = [
        "frame",
        "accepted",
        "reason",
        "motion",
        "reference_point_count",
        "valid_count",
        "inlier_count",
        "inlier_ratio",
        "coverage_x",
        "coverage_y",
        "reprojection_error",
        "translation_x",
        "translation_y",
        "rotation_deg",
        "scale_x",
        "scale_y",
        "scale_avg",
        "perspective_x",
        "perspective_y",
        "applied_translation_x",
        "applied_translation_y",
        "applied_rotation_deg",
        "applied_scale_x",
        "applied_scale_y",
        "applied_scale_avg",
        "applied_perspective_x",
        "applied_perspective_y",
        "global_accept_ratio",
        "global_enabled",
    ]
    with path.open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)
