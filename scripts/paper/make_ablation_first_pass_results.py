#!/usr/bin/env python3
from __future__ import annotations

import argparse
import shutil
from pathlib import Path
from typing import Any

import matplotlib.pyplot as plt
import numpy as np

from screen_normalize.experiments.paper_style import apply_paper_style, finish_axis
from screen_normalize.experiments.run_io import read_json, write_csv


METHOD_SOURCES = (
    ("proposed", "main"),
    ("no_reliability_gates", "ablation"),
    ("no_trajectory_smoothing", "ablation"),
    ("no_offline_repair", "ablation"),
)
METHOD_LABELS = {
    "proposed": "Full",
    "no_reliability_gates": "w/o gates",
    "no_trajectory_smoothing": "w/o smoothing",
    "no_offline_repair": "w/o repair",
}
METHOD_COLORS = {
    "proposed": "#2F7F73",
    "no_reliability_gates": "#C58B3A",
    "no_trajectory_smoothing": "#526D82",
    "no_offline_repair": "#806491",
}
METRIC_FIELDS = {
    "geometry": {
        "corner_rmse_px": "corner_rmse_px_mean",
        "quad_iou": "quad_iou_mean",
        "aspect_relative_error": "aspect_relative_error_mean",
    },
    "temporal": {
        "translation_px": "translation_px_mean",
        "rotation_abs_deg": "rotation_abs_deg_mean",
        "scale_abs_delta": "scale_abs_delta_mean",
    },
    "detail": {
        "edge_preservation_index": "edge_preservation_index_mean",
        "gradient_magnitude_ratio": "gradient_magnitude_ratio_mean",
    },
    "frequency": {
        "fft_orthogonality_error_deg": "fft_orthogonality_error_deg_mean",
    },
}
AGGREGATE_SPECS = (
    ("geometry", "corner_rmse_px", "Corner RMSE (px)", "lower"),
    ("geometry", "quad_iou", "Quad IoU", "higher"),
    ("temporal", "translation_px", "Translation (px)", "lower"),
    ("detail", "edge_preservation_index", "Edge preservation", "higher"),
)


def scalar(value: Any) -> float | None:
    if isinstance(value, int | float) and np.isfinite(value):
        return float(value)
    return None


def clip_dirs(run_dir: Path) -> list[Path]:
    return sorted(
        path
        for category in run_dir.iterdir()
        if category.is_dir()
        for path in category.iterdir()
        if path.is_dir()
    )


def method_dir(main_run: Path, ablation_run: Path, category: str, clip_id: str, method: str) -> Path:
    source = main_run if method == "proposed" else ablation_run
    return source / category / clip_id / method


def collect(main_run: Path, ablation_run: Path) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    clip_rows: list[dict[str, Any]] = []
    metric_status: list[dict[str, Any]] = []
    for clip_dir in clip_dirs(ablation_run):
        category = clip_dir.parent.name
        clip_id = clip_dir.name
        for method, _ in METHOD_SOURCES:
            directory = method_dir(main_run, ablation_run, category, clip_id, method)
            method_json = directory / "method.json"
            if method_json.exists():
                method_payload = read_json(method_json)
                row: dict[str, Any] = {
                    "category": category,
                    "clip_id": clip_id,
                    "method": method,
                    "method_status": method_payload.get("status"),
                    "processed_frames": method_payload.get("processed_frames"),
                    "elapsed_seconds": method_payload.get("elapsed_seconds"),
                }
            else:
                row = {
                    "category": category,
                    "clip_id": clip_id,
                    "method": method,
                    "method_status": "missing",
                    "processed_frames": None,
                    "elapsed_seconds": None,
                }
            for metric, fields in METRIC_FIELDS.items():
                metric_file = directory / f"{metric}.json"
                if metric_file.exists():
                    payload = read_json(metric_file)
                    status = payload.get("status")
                    reason = payload.get("reason")
                    for output_name, source_name in fields.items():
                        row[output_name] = payload.get(source_name)
                else:
                    status = "missing"
                    reason = "missing metric json"
                row[f"{metric}_status"] = status
                row[f"{metric}_reason"] = reason
                metric_status.append(
                    {
                        "metric": metric,
                        "category": category,
                        "clip_id": clip_id,
                        "method": method,
                        "status": status,
                        "reason": reason,
                    }
                )
            clip_rows.append(row)
    return clip_rows, metric_status


def aggregate(clip_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for method, _ in METHOD_SOURCES:
        method_rows = [row for row in clip_rows if row["method"] == method]
        for metric, fields in METRIC_FIELDS.items():
            for field in fields:
                values = [scalar(row.get(field)) for row in method_rows]
                numeric = np.asarray([value for value in values if value is not None], dtype=float)
                rows.append(
                    {
                        "metric": metric,
                        "field": field,
                        "direction": next(
                            (direction for spec_metric, spec_field, _, direction in AGGREGATE_SPECS if spec_metric == metric and spec_field == field),
                            "diagnostic",
                        ),
                        "method": method,
                        "n": int(numeric.size),
                        "median": float(np.median(numeric)) if numeric.size else None,
                        "q1": float(np.percentile(numeric, 25)) if numeric.size else None,
                        "q3": float(np.percentile(numeric, 75)) if numeric.size else None,
                        "mean": float(np.mean(numeric)) if numeric.size else None,
                        "std": float(np.std(numeric, ddof=1)) if numeric.size > 1 else None,
                    }
                )
    return rows


def build_figure(aggregate_rows: list[dict[str, Any]], output_dir: Path) -> Path:
    figures = output_dir / "figures"
    figures.mkdir(parents=True, exist_ok=True)
    apply_paper_style()
    figure, axes = plt.subplots(1, len(AGGREGATE_SPECS), figsize=(9.2, 2.75), constrained_layout=True)
    methods = [method for method, _ in METHOD_SOURCES]
    positions = np.arange(len(methods))
    for index, (metric, field, title, _) in enumerate(AGGREGATE_SPECS):
        axis = axes[index]
        by_method = {row["method"]: row for row in aggregate_rows if row["metric"] == metric and row["field"] == field}
        medians = [by_method[method]["median"] for method in methods]
        q1 = [by_method[method]["q1"] for method in methods]
        q3 = [by_method[method]["q3"] for method in methods]
        lower = [median - low if median is not None and low is not None else 0.0 for median, low in zip(medians, q1)]
        upper = [high - median if median is not None and high is not None else 0.0 for median, high in zip(medians, q3)]
        axis.bar(
            positions,
            [value if value is not None else 0.0 for value in medians],
            color=[METHOD_COLORS[method] for method in methods],
            alpha=0.85,
            width=0.68,
        )
        axis.errorbar(
            positions,
            [value if value is not None else 0.0 for value in medians],
            yerr=np.asarray([lower, upper], dtype=float),
            fmt="none",
            ecolor="#242729",
            elinewidth=0.8,
            capsize=2.5,
        )
        axis.set_xticks(positions, [METHOD_LABELS[method] for method in methods])
        axis.tick_params(axis="x", rotation=18)
        finish_axis(axis, chr(97 + index), title, "Median [IQR]")
    target = figures / "figure_07_ablation_first_pass.svg"
    figure.savefig(target, bbox_inches="tight")
    plt.close(figure)
    return target


def main() -> None:
    parser = argparse.ArgumentParser(description="Build full first-pass ablation tables and Figure 7.")
    parser.add_argument("main_run", type=Path)
    parser.add_argument("ablation_run", type=Path)
    parser.add_argument("--output-dir", type=Path, default=Path("doc/paper/results/full_ablation_first_pass"))
    args = parser.parse_args()

    output_dir = args.output_dir.resolve()
    output_dir.mkdir(parents=True, exist_ok=True)
    clip_rows, metric_status = collect(args.main_run.resolve(), args.ablation_run.resolve())
    aggregate_rows = aggregate(clip_rows)
    write_csv(output_dir / "ablation_clip_metrics.csv", clip_rows)
    write_csv(output_dir / "metric_status.csv", metric_status)
    write_csv(output_dir / "non_ok_metrics.csv", [row for row in metric_status if row["status"] != "ok"])
    write_csv(output_dir / "ablation_aggregate_metrics.csv", aggregate_rows)
    batch = args.ablation_run / "batch.csv"
    if batch.exists():
        shutil.copy2(batch, output_dir / "batch.csv")
    figure = build_figure(aggregate_rows, output_dir)
    print(f"wrote {output_dir}")
    print(f"figure: {figure}")


if __name__ == "__main__":
    main()
