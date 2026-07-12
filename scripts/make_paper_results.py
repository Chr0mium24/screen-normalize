#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import html
import json
from pathlib import Path
from typing import Any

import matplotlib.pyplot as plt
import numpy as np

from screen_normalize.paper_style import (
    METHOD_COLORS,
    METHOD_LABELS,
    METHOD_LINES,
    METHOD_MARKERS,
    apply_paper_style,
    finish_axis,
)
from screen_normalize.run_io import METHOD_IDS, METRIC_IDS, read_json, write_csv


METRIC_SPECS = {
    "geometry": ("corner_rmse_px_mean", "Corner RMSE (px)", "lower"),
    "temporal": ("translation_px_mean", "Residual translation (px)", "lower"),
    "detail": ("edge_preservation_index_mean", "Edge preservation index", "higher"),
    "frequency": ("fft_orthogonality_error_deg_mean", "Orthogonality error (deg)", "lower"),
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
        flat: dict[str, Any] = {
            "category": clip_dir.parent.name,
            "clip_id": clip_dir.name,
            "method": method_dir.name,
            "metric": path.stem,
        }
        flatten("", read_json(path), flat)
        rows.append(flat)
    return rows


def metric_values(rows: list[dict[str, Any]], metric: str) -> list[tuple[str, list[float]]]:
    field = METRIC_SPECS[metric][0]
    values = {method: [] for method in METHOD_IDS}
    for row in rows:
        value = row.get(field)
        if row["metric"] == metric and row.get("status") == "ok" and isinstance(value, (int, float)):
            values[row["method"]].append(float(value))
    return [(method, values[method]) for method in METHOD_IDS if values[method]]


def distribution_panel(axis: Any, available: list[tuple[str, list[float]]], metric: str, panel: str) -> None:
    positions = np.arange(1, len(available) + 1)
    plot = axis.boxplot(
        [samples for _, samples in available],
        positions=positions,
        widths=0.52,
        patch_artist=True,
        showmeans=True,
        meanprops={"marker": "D", "markerfacecolor": "white", "markeredgecolor": "#222222", "markersize": 3.8},
        medianprops={"color": "#222222", "linewidth": 1.25},
        whiskerprops={"color": "#555555", "linewidth": 0.9},
        capprops={"color": "#555555", "linewidth": 0.9},
        flierprops={"marker": "o", "markersize": 2.5, "markerfacecolor": "none", "markeredgecolor": "#777777"},
    )
    for patch, (method, samples), position in zip(plot["boxes"], available, positions):
        patch.set_facecolor(METHOD_COLORS[method])
        patch.set_alpha(0.78)
        jitter = np.linspace(-0.085, 0.085, len(samples)) if len(samples) > 1 else np.asarray([0.0])
        axis.scatter(
            position + jitter,
            samples,
            s=14,
            marker=METHOD_MARKERS[method],
            color=METHOD_COLORS[method],
            edgecolor="white",
            linewidth=0.45,
            zorder=3,
        )
    axis.set_xticks(positions, [METHOD_LABELS[method] for method, _ in available])
    axis.tick_params(axis="x", rotation=10)
    finish_axis(axis, panel, metric.title(), METRIC_SPECS[metric][1])


def make_geometry_figure(rows: list[dict[str, Any]], output: Path) -> Path | None:
    available = metric_values(rows, "geometry")
    if not available:
        return None
    figure, axis = plt.subplots(figsize=(3.55, 2.85), constrained_layout=True)
    distribution_panel(axis, available, "geometry", "a")
    target = output / "figure_03_geometry_comparison.svg"
    figure.savefig(target, bbox_inches="tight")
    plt.close(figure)
    return target


def read_numeric_csv(path: Path) -> list[dict[str, float]]:
    result = []
    with path.open(newline="", encoding="utf-8") as handle:
        for row in csv.DictReader(handle):
            converted: dict[str, float] = {}
            try:
                for key in ("frame", "translation_px", "rotation_deg", "scale_delta"):
                    converted[key] = float(row[key])
            except (KeyError, TypeError, ValueError):
                continue
            result.append(converted)
    return result


def representative_temporal_clip(run_dir: Path) -> tuple[str, dict[str, list[dict[str, float]]]] | None:
    candidates = []
    category_priority = {"static": 0, "scrolling": 1, "screen_video": 2, "weak_border": 3, "hard": 4}
    for clip_dir in sorted(run_dir.glob("*/*")):
        series = {}
        for method in METHOD_IDS:
            path = clip_dir / method / "temporal_frames.csv"
            if path.exists():
                rows = read_numeric_csv(path)
                if rows:
                    series[method] = rows
        if len(series) == len(METHOD_IDS):
            candidates.append(
                (
                    category_priority.get(clip_dir.parent.name, 99),
                    -min(len(rows) for rows in series.values()),
                    f"{clip_dir.parent.name}/{clip_dir.name}",
                    series,
                )
            )
    if not candidates:
        return None
    _, _, name, series = min(candidates, key=lambda item: (item[0], item[1], item[2]))
    return name, series


def make_temporal_figure(run_dir: Path, output: Path) -> Path | None:
    selected = representative_temporal_clip(run_dir)
    if selected is None:
        return None
    clip_name, series = selected
    figure, axes = plt.subplots(1, 3, figsize=(7.2, 2.45), constrained_layout=True)
    specs = (
        ("translation_px", "Translation", "Translation (px)", 1.0),
        ("rotation_deg", "Rotation", "Rotation (deg)", 1.0),
        ("scale_delta", "Scale", "Scale change (%)", 100.0),
    )
    for panel_index, (field, title, ylabel, multiplier) in enumerate(specs):
        axis = axes[panel_index]
        pooled = []
        for method in METHOD_IDS:
            method_rows = series[method]
            frame = np.asarray([row["frame"] for row in method_rows])
            value = np.asarray([row[field] * multiplier for row in method_rows])
            pooled.extend(value.tolist())
            axis.plot(
                frame,
                value,
                color=METHOD_COLORS[method],
                linestyle=METHOD_LINES[method],
                linewidth=1.35 if method == "proposed" else 0.95,
                alpha=0.95,
                label=METHOD_LABELS[method],
            )
        pooled_values = np.asarray(pooled, dtype=float)
        if field == "translation_px":
            upper = max(1e-6, float(np.percentile(pooled_values, 99)))
            clipped = int(np.count_nonzero(pooled_values > upper))
            axis.set_ylim(0.0, upper * 1.08)
        else:
            bound = max(1e-6, float(np.percentile(np.abs(pooled_values), 99)))
            clipped = int(np.count_nonzero(np.abs(pooled_values) > bound))
            axis.set_ylim(-bound * 1.08, bound * 1.08)
        if clipped:
            axis.text(
                0.98,
                0.96,
                f"{clipped} point{'s' if clipped != 1 else ''} outside 99% range",
                transform=axis.transAxes,
                ha="right",
                va="top",
                fontsize=6.8,
                color="#6F7478",
            )
        axis.set_xlabel("Frame")
        finish_axis(axis, chr(97 + panel_index), title, ylabel)
    handles, labels = axes[0].get_legend_handles_labels()
    figure.legend(handles, labels, loc="upper center", ncol=3, bbox_to_anchor=(0.5, 1.08))
    figure.suptitle(f"Representative clip: {clip_name}", y=1.16, fontsize=8.5, color="#555555")
    target = output / "figure_04_temporal_stability.svg"
    figure.savefig(target, bbox_inches="tight")
    plt.close(figure)
    return target


def make_detail_frequency_figure(rows: list[dict[str, Any]], output: Path) -> Path | None:
    datasets = [(metric, metric_values(rows, metric)) for metric in ("detail", "frequency")]
    datasets = [(metric, values) for metric, values in datasets if values]
    if not datasets:
        return None
    figure, axes = plt.subplots(1, len(datasets), figsize=(3.55 * len(datasets), 2.85), constrained_layout=True, squeeze=False)
    for index, (metric, values) in enumerate(datasets):
        distribution_panel(axes.flat[index], values, metric, chr(97 + index))
    target = output / "figure_06_detail_frequency.svg"
    figure.savefig(target, bbox_inches="tight")
    plt.close(figure)
    return target


def make_ablation_figure(rows: list[dict[str, Any]], output: Path) -> Path | None:
    ablation = [row for row in rows if row.get("experiment") == "ablation"]
    if not ablation:
        return None
    available = metric_values(ablation, "temporal")
    if not available:
        return None
    figure, axis = plt.subplots(figsize=(3.55, 2.85), constrained_layout=True)
    distribution_panel(axis, available, "temporal", "a")
    target = output / "figure_07_ablation.svg"
    figure.savefig(target, bbox_inches="tight")
    plt.close(figure)
    return target


def aggregate_table(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    output = []
    for metric, (field, _, direction) in METRIC_SPECS.items():
        for method, samples in metric_values(rows, metric):
            values = np.asarray(samples, dtype=float)
            output.append(
                {
                    "metric": metric,
                    "direction": direction,
                    "method": method,
                    "n": len(values),
                    "median": float(np.median(values)),
                    "q1": float(np.percentile(values, 25)),
                    "q3": float(np.percentile(values, 75)),
                    "mean": float(np.mean(values)),
                    "std": float(np.std(values, ddof=1)) if len(values) > 1 else None,
                }
            )
    return output


def render_tables(summary: Path, aggregate: list[dict[str, Any]]) -> Path:
    arrows = {"lower": "&#8595;", "higher": "&#8593;"}
    groups = []
    for metric in METRIC_SPECS:
        records = [row for row in aggregate if row["metric"] == metric]
        if not records:
            continue
        body = []
        for row in records:
            spread = f"{row['median']:.3g} [{row['q1']:.3g}, {row['q3']:.3g}]"
            mean = f"{row['mean']:.3g} &#177; {row['std']:.3g}" if row["std"] is not None else f"{row['mean']:.3g}"
            body.append(f"<tr><td><span class='swatch' style='background:{METHOD_COLORS[row['method']]}'></span>{METHOD_LABELS[row['method']]}</td><td>{row['n']}</td><td>{spread}</td><td>{mean}</td></tr>")
        groups.append(
            f"<section><h2>{html.escape(metric.title())} {arrows[records[0]['direction']]}</h2>"
            "<table><thead><tr><th>Method</th><th>n</th><th>Median [Q1, Q3]</th><th>Mean &#177; SD</th></tr></thead><tbody>"
            + "".join(body)
            + "</tbody></table></section>"
        )
    target = summary / "tables.html"
    target.write_text(
        "<!doctype html><meta charset=utf-8><title>Paper tables</title><style>"
        "body{font:14px Arial,sans-serif;color:#242729;max-width:980px;margin:32px auto;padding:0 20px}"
        "h1{font-size:24px}h2{font-size:16px;margin:28px 0 8px}table{border-collapse:collapse;width:100%}"
        "th{background:#EEF1F2;border-top:2px solid #34383B;border-bottom:1px solid #767B7E;text-align:left}"
        "th,td{padding:9px 11px}td{border-bottom:1px solid #D9DDDF}.swatch{display:inline-block;width:10px;height:10px;margin-right:8px}"
        ".note{color:#62676A;font-size:12px}</style><h1>Paper result tables</h1>"
        "<p class='note'>Pilot output is shown for layout review only. No best values are automatically bolded.</p>"
        + "".join(groups),
        encoding="utf-8",
    )
    return target


def main() -> None:
    parser = argparse.ArgumentParser(description="Build publication-style paper tables and SVG figures from one run.")
    parser.add_argument("run_dir", type=Path)
    args = parser.parse_args()
    run_dir = args.run_dir.resolve()
    rows = collect(run_dir)
    if not rows:
        raise SystemExit(f"no metric JSON files found in {run_dir}")

    summary = run_dir / "summary"
    figures_dir = summary / "figures"
    figures_dir.mkdir(parents=True, exist_ok=True)
    for old in figures_dir.glob("*.svg"):
        old.unlink()
    write_csv(summary / "all_metrics.csv", rows)
    for metric in METRIC_IDS:
        write_csv(summary / f"{metric}_table.csv", [row for row in rows if row["metric"] == metric])
    ablation_rows = [row for row in rows if row.get("experiment") == "ablation"]
    write_csv(summary / "ablation_table.csv", ablation_rows)

    apply_paper_style()
    generated = {
        "figure_03": make_geometry_figure(rows, figures_dir),
        "figure_04": make_temporal_figure(run_dir, figures_dir),
        "figure_06": make_detail_frequency_figure(rows, figures_dir),
        "figure_07": make_ablation_figure(rows, figures_dir),
    }
    aggregate = aggregate_table(rows)
    write_csv(summary / "aggregate_metrics.csv", aggregate)
    tables = render_tables(summary, aggregate)
    manifest = {
        name: {"status": "generated" if path else "omitted_missing_data", "path": str(path) if path else None}
        for name, path in generated.items()
    }
    manifest.update(
        {
            "figure_01": {"status": "pending_intermediate_assets", "path": None},
            "figure_02": {"status": "pending_formal_dataset", "path": None},
            "figure_05": {"status": "pending_reviewed_frames", "path": None},
            "figure_08": {"status": "pending_failure_audit", "path": None},
            "figure_09": {"status": "optional_runtime_protocol_pending", "path": None},
        }
    )
    (summary / "figure_manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")

    figures = [path for path in generated.values() if path]
    body = "".join(
        f'<figure><img src="figures/{html.escape(path.name)}"><figcaption>{html.escape(path.stem.replace("_", " ").title())}</figcaption></figure>'
        for path in figures
    )
    missing = "".join(f"<li>{name}: {record['status']}</li>" for name, record in manifest.items() if record["status"] != "generated")
    (summary / "report.html").write_text(
        "<!doctype html><meta charset=utf-8><title>Paper results</title><style>"
        "body{font:14px Arial,sans-serif;color:#242729;max-width:1100px;margin:28px auto;padding:0 20px}"
        "header{border-bottom:2px solid #34383B;margin-bottom:24px}figure{margin:28px 0}img{width:100%;max-height:620px}"
        "figcaption{font-weight:600;margin-top:8px}a{color:#2F6F68}li{margin:5px 0}</style>"
        f"<header><h1>Paper results</h1><p>{len(rows)} method-metric records from this run.</p>"
        f"<p><a href='{tables.name}'>Review formatted tables</a></p></header>{body}<h2>Pending figure assets</h2><ul>{missing}</ul>",
        encoding="utf-8",
    )
    print(f"wrote {summary}")


if __name__ == "__main__":
    main()
