from __future__ import annotations

import numpy as np

from .geometry import geometry_update_is_reasonable, order_corners


def centered_window_filter(trajectory: np.ndarray, window: int, reducer: str) -> np.ndarray:
    if window <= 1 or len(trajectory) < 3:
        return trajectory

    radius = window // 2
    pad_width = [(radius, radius), *[(0, 0) for _ in range(trajectory.ndim - 1)]]
    padded = np.pad(trajectory, pad_width, mode="edge")
    filtered = np.empty_like(trajectory)
    for index in range(len(trajectory)):
        chunk = padded[index : index + window]
        if reducer == "median":
            filtered[index] = np.median(chunk, axis=0)
        elif reducer == "mean":
            filtered[index] = np.mean(chunk, axis=0)
        else:
            raise ValueError(f"unknown reducer: {reducer}")
    return filtered


def smooth_corner_trajectory(
    trajectory: list[np.ndarray],
    median_window: int,
    average_window: int,
) -> list[np.ndarray]:
    points = np.asarray(trajectory, dtype=np.float32)
    if len(points) == 0:
        return []
    points = centered_window_filter(points, median_window, "median")
    points = centered_window_filter(points, average_window, "mean")
    return [order_corners(corners).astype(np.float32) for corners in points]


def reliable_mask_from_tracker_rows(
    rows: list[dict[str, object]] | None,
    length: int,
) -> np.ndarray:
    if length <= 0:
        return np.zeros((0,), dtype=bool)
    if rows is None:
        return np.ones((length,), dtype=bool)

    reliable = np.ones((length,), dtype=bool)
    seen = np.zeros((length,), dtype=bool)
    for row in rows:
        try:
            index = int(row["frame"])
        except (KeyError, TypeError, ValueError):
            continue
        if not 0 <= index < length:
            continue
        seen[index] = True
        reliable[index] = bool(row.get("accepted", False))
    reliable[~seen] = True
    if length:
        reliable[0] = True
    return reliable


def interpolate_corner_trajectory(
    trajectory: list[np.ndarray],
    reliable: np.ndarray,
) -> list[np.ndarray]:
    points = np.asarray(trajectory, dtype=np.float32)
    if len(points) == 0:
        return []
    if len(reliable) != len(points):
        reliable = np.ones((len(points),), dtype=bool)
    if int(np.count_nonzero(reliable)) == 0:
        return [order_corners(corners).astype(np.float32) for corners in points]
    if bool(np.all(reliable)):
        return [order_corners(corners).astype(np.float32) for corners in points]

    frame_indices = np.arange(len(points), dtype=np.float32)
    reliable_indices = frame_indices[reliable]
    interpolated = points.copy()
    for corner_index in range(points.shape[1]):
        for axis in range(points.shape[2]):
            values = points[:, corner_index, axis]
            interpolated[:, corner_index, axis] = np.interp(
                frame_indices,
                reliable_indices,
                values[reliable],
            )
    return [order_corners(corners).astype(np.float32) for corners in interpolated]


def apply_offline_geometry_gate(
    trajectory: list[np.ndarray],
    reliable: np.ndarray,
    max_scale_step: float,
    max_area_step: float,
) -> np.ndarray:
    if len(trajectory) == 0:
        return reliable
    if len(reliable) != len(trajectory):
        reliable = np.ones((len(trajectory),), dtype=bool)
    gated = reliable.copy()
    previous_reliable: np.ndarray | None = None
    for index, corners in enumerate(trajectory):
        if not gated[index]:
            continue
        ordered = order_corners(corners).astype(np.float32)
        if previous_reliable is None:
            previous_reliable = ordered
            continue
        if geometry_update_is_reasonable(
            ordered,
            previous_reliable,
            max_scale_step=max_scale_step,
            max_area_step=max_area_step,
        ):
            previous_reliable = ordered
        else:
            gated[index] = False
    if len(gated):
        gated[0] = True
    return gated


def build_trajectory_debug_rows(
    raw_trajectory: list[np.ndarray],
    reliable: np.ndarray,
    interpolated_trajectory: list[np.ndarray],
    smoothed_trajectory: list[np.ndarray],
) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    length = max(len(raw_trajectory), len(interpolated_trajectory), len(smoothed_trajectory))
    for frame in range(length):
        row: dict[str, object] = {
            "frame": frame,
            "reliable": bool(reliable[frame]) if frame < len(reliable) else True,
        }
        for prefix, trajectory in (
            ("raw", raw_trajectory),
            ("interpolated", interpolated_trajectory),
            ("smoothed", smoothed_trajectory),
        ):
            if frame >= len(trajectory):
                continue
            corners = trajectory[frame]
            for index, label in enumerate(("tl", "tr", "br", "bl")):
                row[f"{prefix}_{label}_x"] = float(corners[index, 0])
                row[f"{prefix}_{label}_y"] = float(corners[index, 1])
        rows.append(row)
    return rows
