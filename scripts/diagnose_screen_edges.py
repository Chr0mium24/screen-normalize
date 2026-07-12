#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path

import cv2
import numpy as np

from screen_normalize.algorithms.boundary import corners_from_lines, observe_quad_edges
from screen_normalize.algorithms.geometry import detected_corners_are_valid, geometry_update_is_reasonable
from screen_normalize.experiments.annotations import CORNER_NAMES, load_annotations


COLORS = ((0, 220, 255), (0, 255, 0), (255, 180, 0), (255, 0, 255))


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Diagnose dense normal-profile observations on four screen edges.")
    parser.add_argument("input", type=Path)
    parser.add_argument("annotations", type=Path)
    parser.add_argument("output_dir", type=Path)
    parser.add_argument("--samples-per-edge", type=int, default=50)
    parser.add_argument("--search-radii", default="20,60,120")
    parser.add_argument("--display-width", type=int, default=1920)
    return parser.parse_args()


def corner_error(estimate: np.ndarray, truth: np.ndarray) -> tuple[float, float]:
    errors = np.linalg.norm(estimate - truth, axis=1)
    return float(np.sqrt(np.mean(errors**2))), float(np.mean(errors))


def draw_label(frame: np.ndarray, lines: list[str]) -> None:
    y = 38
    for text in lines:
        cv2.putText(frame, text, (18, y), cv2.FONT_HERSHEY_SIMPLEX, 0.75, (0, 0, 0), 5, cv2.LINE_AA)
        cv2.putText(frame, text, (18, y), cv2.FONT_HERSHEY_SIMPLEX, 0.75, (255, 255, 255), 2, cv2.LINE_AA)
        y += 32


def serialize_corners(row: dict[str, object], corners: np.ndarray) -> None:
    for name, point in zip(CORNER_NAMES, corners, strict=True):
        row[f"{name}_x"] = float(point[0])
        row[f"{name}_y"] = float(point[1])


def main() -> None:
    args = parse_args()
    radii = tuple(int(value) for value in args.search_radii.split(","))
    if not radii or min(radii) <= 0:
        raise SystemExit("search radii must be positive")
    args.output_dir.mkdir(parents=True, exist_ok=True)

    capture = cv2.VideoCapture(str(args.input))
    if not capture.isOpened():
        raise SystemExit(f"cannot open {args.input}")
    width = int(capture.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(capture.get(cv2.CAP_PROP_FRAME_HEIGHT))
    fps = float(capture.get(cv2.CAP_PROP_FPS) or 30.0)
    annotations = load_annotations(args.annotations, width, height)
    if 0 not in annotations:
        raise SystemExit("frame 0 annotation is required")

    display_scale = min(1.0, args.display_width / width)
    display_size = (round(width * display_scale), round(height * display_scale))
    output_video = args.output_dir / "edge_observations.mp4"
    writer = cv2.VideoWriter(str(output_video), cv2.VideoWriter_fourcc(*"mp4v"), fps, display_size)
    if not writer.isOpened():
        raise SystemExit(f"cannot create {output_video}")

    predicted = annotations[0].copy()
    polarities: np.ndarray | None = None
    rows: list[dict[str, object]] = []
    frame_index = 0
    while True:
        ok, frame = capture.read()
        if not ok:
            break
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        accepted = False
        used_radius = radii[-1]
        chosen_observations = None
        candidate = None
        measured_polarities = np.zeros(4, dtype=np.float32)
        for radius in radii:
            observations, measured = observe_quad_edges(
                gray, predicted, args.samples_per_edge, radius, polarities
            )
            proposed = corners_from_lines([item.line for item in observations])
            confidences = np.asarray([item.confidence for item in observations])
            chosen_observations = observations
            measured_polarities = measured
            used_radius = radius
            if (
                proposed is not None
                and float(confidences.min()) >= 0.35
                and detected_corners_are_valid(proposed, frame.shape)
                and geometry_update_is_reasonable(proposed, predicted, 0.08, 0.15)
            ):
                candidate = proposed
                accepted = True
                break

        if frame_index == 0:
            candidate = annotations[0].copy()
            accepted = True
        if accepted and candidate is not None:
            predicted = candidate
            nonzero = measured_polarities != 0
            if polarities is None:
                polarities = measured_polarities
            else:
                polarities[nonzero] = measured_polarities[nonzero]

        canvas = frame.copy()
        if chosen_observations is not None:
            for edge, observation in enumerate(chosen_observations):
                color = COLORS[edge]
                for point, is_inlier in zip(observation.points, observation.inliers, strict=True):
                    cv2.circle(canvas, tuple(np.round(point).astype(int)), 5 if is_inlier else 3, color if is_inlier else (0, 0, 255), -1, cv2.LINE_AA)
                if observation.line is not None:
                    a, b, c = observation.line
                    if abs(b) > abs(a):
                        endpoints = [(0, round(-c / b)), (width - 1, round(-(a * (width - 1) + c) / b))]
                    else:
                        endpoints = [(round(-c / a), 0), (round(-(b * (height - 1) + c) / a), height - 1)]
                    cv2.line(canvas, endpoints[0], endpoints[1], color, 3, cv2.LINE_AA)
        cv2.polylines(canvas, [np.round(predicted).astype(np.int32)], True, (255, 255, 255), 4, cv2.LINE_AA)

        confidences = [item.confidence for item in chosen_observations] if chosen_observations else [0.0] * 4
        row: dict[str, object] = {
            "frame": frame_index,
            "accepted": accepted,
            "search_radius": used_radius,
            **{f"edge_{index}_confidence": value for index, value in enumerate(confidences)},
        }
        serialize_corners(row, predicted)
        rmse = float("nan")
        if frame_index in annotations:
            rmse, mean_error = corner_error(predicted, annotations[frame_index])
            row["corner_rmse"] = rmse
            row["corner_mean_error"] = mean_error
            cv2.polylines(canvas, [np.round(annotations[frame_index]).astype(np.int32)], True, (0, 255, 0), 4, cv2.LINE_AA)
        rows.append(row)
        draw_label(canvas, [
            f"frame={frame_index} edge_quad={'accepted' if accepted else 'held'} radius={used_radius}",
            "edge confidence=" + ", ".join(f"{value:.2f}" for value in confidences),
            f"annotation RMSE={rmse:.2f}px" if np.isfinite(rmse) else "white=edge estimate; green=annotation",
        ])
        writer.write(cv2.resize(canvas, display_size, interpolation=cv2.INTER_AREA))
        frame_index += 1

    capture.release()
    writer.release()
    csv_path = args.output_dir / "edge_observations.csv"
    fields = list(rows[0])
    for optional in ("corner_rmse", "corner_mean_error"):
        if optional not in fields:
            fields.append(optional)
    with csv_path.open("w", newline="", encoding="utf-8") as handle:
        csv_writer = csv.DictWriter(handle, fieldnames=fields)
        csv_writer.writeheader()
        csv_writer.writerows(rows)
    annotated = [row for row in rows if "corner_rmse" in row]
    summary = {
        "input": str(args.input.resolve()),
        "frames": len(rows),
        "accepted_frames": sum(bool(row["accepted"]) for row in rows),
        "accept_ratio": sum(bool(row["accepted"]) for row in rows) / max(1, len(rows)),
        "annotated_frame_rmse": {str(row["frame"]): row["corner_rmse"] for row in annotated},
        "annotated_noninitial_rmse_mean": float(np.mean([row["corner_rmse"] for row in annotated if row["frame"] != 0])) if len(annotated) > 1 else None,
        "search_radii": radii,
        "samples_per_edge": args.samples_per_edge,
    }
    (args.output_dir / "edge_observations_summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
