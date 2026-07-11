#!/usr/bin/env python3
from __future__ import annotations

import argparse
import html
from pathlib import Path
from typing import Any

import matplotlib.pyplot as plt

from screen_normalize.run_io import METHOD_IDS, METRIC_IDS, read_json, write_csv


PRIMARY = {
    "geometry": "corner_rmse_px_mean",
    "temporal": "translation_px_mean",
    "detail": "edge_preservation_index_mean",
    "frequency": "fft_orthogonality_error_deg_mean",
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
    for metric, field in PRIMARY.items():
        values = {method: [] for method in METHOD_IDS}
        for row in rows:
            value = row.get(field)
            if row["metric"] == metric and row.get("status") == "ok" and isinstance(value, (int, float)):
                values.setdefault(row["method"], []).append(float(value))
        available = [(method, samples) for method, samples in values.items() if samples]
        if not available:
            continue
        figure, axis = plt.subplots(figsize=(6.4, 4.0))
        axis.boxplot([samples for _, samples in available], tick_labels=[method for method, _ in available])
        axis.set_title(f"{metric.title()} comparison")
        axis.set_ylabel(field)
        axis.grid(axis="y", alpha=0.25)
        figure.tight_layout()
        figure.savefig(output / f"{metric}_comparison.png", dpi=180)
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
    figures = sorted((summary / "figures").glob("*.png"))
    body = "".join(f'<figure><img src="figures/{html.escape(path.name)}" style="max-width:720px"><figcaption>{html.escape(path.stem)}</figcaption></figure>' for path in figures)
    (summary / "report.html").write_text(
        "<!doctype html><meta charset=utf-8><title>Paper results</title><style>body{font:14px system-ui;max-width:1100px;margin:24px auto}img{width:100%}figure{border:1px solid #ddd;padding:12px}</style>"
        f"<h1>Paper results</h1><p>{len(rows)} method-metric records. Tables are stored beside this report.</p>{body}",
        encoding="utf-8",
    )
    print(f"wrote {summary}")


if __name__ == "__main__":
    main()

