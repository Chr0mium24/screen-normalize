#!/usr/bin/env python3
from __future__ import annotations

import argparse
import html
from pathlib import Path
from typing import Any

import matplotlib.pyplot as plt
import numpy as np

from screen_normalize.run_io import METHOD_IDS, METRIC_IDS, read_json, write_csv


PRIMARY = {
    "geometry": "corner_rmse_px_mean",
    "temporal": "translation_px_mean",
    "detail": "edge_preservation_index_mean",
    "frequency": "fft_orthogonality_error_deg_mean",
}

METHOD_LABELS = {
    "frame_wise": "Frame-wise",
    "optical_flow": "Optical flow",
    "proposed": "Proposed",
}
COLORS = {
    "frame_wise": "#4C78A8",
    "optical_flow": "#F58518",
    "proposed": "#2A9D6F",
}


def flatten(prefix: str, value: Any, output: dict[str, Any]) -> None:
    if isinstance(value, dict):
        for key, item in value.items():
            flatten(f"{prefix}.{key}" if prefix else key, item, output)
    elif isinstance(value, (str, int, float, bool)) or value is None:
        output[prefix] = value


def collect(run_dir: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for path in sorted(run_dir.glob("*/*/*/*.json")):
        if path.stem not in METRIC_IDS:
            continue
        method_dir = path.parent
        clip_dir = method_dir.parent
        flat: dict[str, Any] = {"category": clip_dir.parent.name, "clip_id": clip_dir.name, "method": method_dir.name, "metric": path.stem}
        flatten("", read_json(path), flat)
        rows.append(flat)
    return rows


def make_figures(rows: list[dict[str, Any]], output: Path) -> None:
    output.mkdir(parents=True, exist_ok=True)
    plt.rcParams.update(
        {
            "font.family": "DejaVu Sans",
            "font.size": 8.5,
            "axes.titlesize": 9,
            "axes.labelsize": 8.5,
            "legend.fontsize": 8,
            "svg.fonttype": "none",
        }
    )
    labels = {
        "geometry": "Corner RMSE (px)",
        "temporal": "Residual translation (px)",
        "detail": "Edge preservation index",
        "frequency": "Orthogonality error (deg)",
    }
    datasets = []
    for metric, field in PRIMARY.items():
        values = {method: [] for method in METHOD_IDS}
        for row in rows:
            value = row.get(field)
            if row["metric"] == metric and row.get("status") == "ok" and isinstance(value, (int, float)):
                values.setdefault(row["method"], []).append(float(value))
        available = [(method, samples) for method, samples in values.items() if samples]
        if available:
            datasets.append((metric, available))
    if not datasets:
        return
    columns = 2 if len(datasets) > 1 else 1
    rows_count = (len(datasets) + columns - 1) // columns
    figure, axes = plt.subplots(
        rows_count,
        columns,
        figsize=(7.2, 2.9 * rows_count),
        constrained_layout=True,
        squeeze=False,
    )
    for panel_index, (metric, available) in enumerate(datasets):
        axis = axes.flat[panel_index]
        positions = np.arange(1, len(available) + 1)
        plot = axis.boxplot(
            [samples for _, samples in available],
            positions=positions,
            widths=0.55,
            patch_artist=True,
            showmeans=True,
            meanprops={"marker": "D", "markerfacecolor": "white", "markeredgecolor": "#222222", "markersize": 3.5},
            medianprops={"color": "#222222", "linewidth": 1.2},
            whiskerprops={"color": "#555555"},
            capprops={"color": "#555555"},
            flierprops={"marker": "o", "markersize": 2.5, "markerfacecolor": "none", "markeredgecolor": "#777777"},
        )
        for patch, (method, samples), position in zip(plot["boxes"], available, positions):
            patch.set_facecolor(COLORS[method])
            patch.set_alpha(0.78)
            jitter = np.linspace(-0.09, 0.09, len(samples)) if len(samples) > 1 else np.asarray([0.0])
            axis.scatter(position + jitter, samples, s=10, color=COLORS[method], edgecolor="white", linewidth=0.35, zorder=3)
        axis.set_xticks(positions, [METHOD_LABELS[method] for method, _ in available])
        axis.set_ylabel(labels[metric])
        axis.set_title(f"({chr(97 + panel_index)}) {metric.title()}", loc="left", fontweight="bold")
        axis.grid(axis="y", color="#D9D9D9", linewidth=0.6, alpha=0.75)
        axis.spines[["top", "right"]].set_visible(False)
        axis.tick_params(axis="x", rotation=12)
    for axis in axes.flat[len(datasets) :]:
        axis.set_axis_off()
    figure.savefig(output / "main_method_comparison.svg", bbox_inches="tight")
    plt.close(figure)


def main() -> None:
    parser = argparse.ArgumentParser(description="Build paper tables and figures from one completed run.")
    parser.add_argument("run_dir", type=Path)
    args = parser.parse_args()
    run_dir = args.run_dir.resolve()
    rows = collect(run_dir)
    if not rows:
        raise SystemExit(f"no metric JSON files found in {run_dir}")
    summary = run_dir / "summary"
    summary.mkdir(exist_ok=True)
    write_csv(summary / "all_metrics.csv", rows)
    for metric in METRIC_IDS:
        write_csv(summary / f"{metric}_table.csv", [row for row in rows if row["metric"] == metric])
    write_csv(summary / "ablation_table.csv", [row for row in rows if row.get("experiment") == "ablation"])
    make_figures(rows, summary / "figures")
    figures = sorted((summary / "figures").glob("*.svg"))
    body = "".join(f'<figure><img src="figures/{html.escape(path.name)}" style="max-width:720px"><figcaption>{html.escape(path.stem)}</figcaption></figure>' for path in figures)
    (summary / "report.html").write_text(
        "<!doctype html><meta charset=utf-8><title>Paper results</title><style>body{font:14px system-ui;max-width:1100px;margin:24px auto}img{width:100%}figure{border:1px solid #ddd;padding:12px}</style>"
        f"<h1>Paper results</h1><p>{len(rows)} method-metric records. Tables are stored beside this report.</p>{body}",
        encoding="utf-8",
    )
    print(f"wrote {summary}")


if __name__ == "__main__":
    main()
