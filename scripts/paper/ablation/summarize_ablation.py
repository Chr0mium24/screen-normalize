#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import re
from pathlib import Path
from statistics import median


METHODS = (
    "proposed",
    "no_reliability_gates",
    "no_trajectory_smoothing",
    "no_offline_repair",
)
PRIMARY_METRICS = {
    "corner_rmse_px": ("geometry", "corner_rmse_px_mean", "lower"),
    "quad_iou": ("geometry", "quad_iou_mean", "higher"),
    "translation_px": ("temporal", "translation_px_mean", "lower"),
    "edge_preservation_index": ("detail", "edge_preservation_index_mean", "higher"),
}
AUDIT_METRICS = {
    **PRIMARY_METRICS,
    "aspect_relative_error": ("geometry", "aspect_relative_error_mean", "lower"),
    "rotation_abs_deg": ("temporal", "rotation_abs_deg_mean", "lower"),
    "scale_abs_delta": ("temporal", "scale_abs_delta_mean", "lower"),
    "gradient_magnitude_ratio": ("detail", "gradient_magnitude_ratio_mean", "target_one"),
    "fft_orthogonality_error_deg": (
        "frequency",
        "fft_orthogonality_error_deg_mean",
        "lower",
    ),
}


def read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def write_csv(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fields = list(rows[0]) if rows else []
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        if fields:
            writer.writeheader()
            writer.writerows(rows)


def percentile(values: list[float], fraction: float) -> float | None:
    if not values:
        return None
    ordered = sorted(values)
    position = (len(ordered) - 1) * fraction
    lower = math.floor(position)
    upper = math.ceil(position)
    if lower == upper:
        return ordered[lower]
    weight = position - lower
    return ordered[lower] * (1.0 - weight) + ordered[upper] * weight


def degradation(value: float, full: float, direction: str) -> float:
    if direction == "lower":
        return value - full
    if direction == "higher":
        return full - value
    return abs(value - 1.0) - abs(full - 1.0)


def collect(run_dir: Path) -> tuple[list[dict], list[dict]]:
    rows: list[dict] = []
    issues: list[dict] = []
    clip_dirs = sorted(
        path
        for category in run_dir.iterdir()
        if category.is_dir()
        for path in category.iterdir()
        if path.is_dir()
    )
    for clip_dir in clip_dirs:
        category, clip_id = clip_dir.parent.name, clip_dir.name
        for method in METHODS:
            method_dir = clip_dir / method
            method_file = method_dir / "method.json"
            if not method_file.exists():
                issues.append(
                    {
                        "severity": "high",
                        "category": category,
                        "clip_id": clip_id,
                        "method": method,
                        "check": "method_output",
                        "message": "missing method.json",
                    }
                )
                continue
            method_json = read_json(method_file)
            if method_json.get("status") != "ok":
                issues.append(
                    {
                        "severity": "critical",
                        "category": category,
                        "clip_id": clip_id,
                        "method": method,
                        "check": "method_status",
                        "message": str(method_json.get("reason") or method_json.get("status")),
                    }
                )
            row = {
                "category": category,
                "clip_id": clip_id,
                "method": method,
                "processed_frames": method_json.get("processed_frames"),
                "elapsed_seconds": method_json.get("elapsed_seconds"),
            }
            debug_file = method_dir / "debug.csv"
            if debug_file.exists():
                with debug_file.open(newline="", encoding="utf-8") as handle:
                    debug_rows = list(csv.DictReader(handle))
                accepted_indices = [
                    index
                    for index, item in enumerate(debug_rows)
                    if str(item.get("accepted", "")).lower() in {"true", "1"}
                ]
                interior_rejected = 0
                if len(accepted_indices) >= 2:
                    first, last = accepted_indices[0], accepted_indices[-1]
                    interior_rejected = sum(
                        str(debug_rows[index].get("accepted", "")).lower() in {"false", "0"}
                        for index in range(first + 1, last)
                    )
                row["tracker_rows"] = len(debug_rows)
                row["tracker_accepted"] = len(accepted_indices)
                row["tracker_accept_ratio"] = (
                    len(accepted_indices) / len(debug_rows) if debug_rows else None
                )
                row["interior_rejected_frames"] = interior_rejected
            corners_file = method_dir / "estimated_corners.csv"
            if corners_file.exists():
                row["estimated_corners_sha256"] = hashlib.sha256(
                    corners_file.read_bytes()
                ).hexdigest()
            loaded: dict[str, dict] = {}
            for metric_id in {item[0] for item in AUDIT_METRICS.values()}:
                metric_file = method_dir / f"{metric_id}.json"
                if not metric_file.exists():
                    issues.append(
                        {
                            "severity": "high",
                            "category": category,
                            "clip_id": clip_id,
                            "method": method,
                            "check": f"{metric_id}_output",
                            "message": f"missing {metric_id}.json",
                        }
                    )
                    continue
                payload = read_json(metric_file)
                loaded[metric_id] = payload
                if payload.get("status") != "ok":
                    issues.append(
                        {
                            "severity": "high",
                            "category": category,
                            "clip_id": clip_id,
                            "method": method,
                            "check": f"{metric_id}_status",
                            "message": str(payload.get("reason") or payload.get("status")),
                        }
                    )
            geometry = loaded.get("geometry", {})
            if geometry and geometry.get("initialization_frame_excluded") is not True:
                issues.append(
                    {
                        "severity": "high",
                        "category": category,
                        "clip_id": clip_id,
                        "method": method,
                        "check": "initialization_frame_policy",
                        "message": "geometry metric did not record initialization-frame exclusion",
                    }
                )
            for output_name, (metric_id, field, _) in AUDIT_METRICS.items():
                value = loaded.get(metric_id, {}).get(field)
                row[output_name] = value
                if value is None or not isinstance(value, (int, float)) or not math.isfinite(value):
                    issues.append(
                        {
                            "severity": "high",
                            "category": category,
                            "clip_id": clip_id,
                            "method": method,
                            "check": field,
                            "message": "metric is missing or non-finite",
                        }
                    )
            rows.append(row)
    return rows, issues


def experimental_validity_issues(rows: list[dict]) -> list[dict]:
    issues: list[dict] = []
    full_rows = [row for row in rows if row["method"] == "proposed"]
    for row in full_rows:
        if float(row.get("corner_rmse_px") or 0.0) > 100.0 or float(row.get("quad_iou") or 1.0) < 0.8:
            issues.append(
                {
                    "severity": "high",
                    "category": row["category"],
                    "clip_id": row["clip_id"],
                    "method": "proposed",
                    "check": "geometry_failure",
                    "message": (
                        f"full geometry is poor: RMSE={float(row['corner_rmse_px']):.3f}px, "
                        f"IoU={float(row['quad_iou']):.3f}"
                    ),
                }
            )
        if float(row.get("tracker_accept_ratio") or 0.0) < 0.1:
            issues.append(
                {
                    "severity": "high",
                    "category": row["category"],
                    "clip_id": row["clip_id"],
                    "method": "proposed",
                    "check": "tracker_freeze",
                    "message": (
                        f"only {row.get('tracker_accepted', 0)}/{row.get('tracker_rows', 0)} "
                        "tracker rows were accepted"
                    ),
                }
            )

    repairable_frames = sum(int(row.get("interior_rejected_frames") or 0) for row in full_rows)
    if repairable_frames == 0:
        issues.append(
            {
                "severity": "high",
                "category": "all",
                "clip_id": "four-clip ablation subset",
                "method": "no_offline_repair",
                "check": "module_not_exercised",
                "message": (
                    "no full-method clip contains rejected frames bracketed by later accepted frames; "
                    "offline interpolation has no repairable interval"
                ),
            }
        )

    by_key = {(row["clip_id"], row["method"]): row for row in rows}
    for full in full_rows:
        without_repair = by_key.get((full["clip_id"], "no_offline_repair"))
        if (
            without_repair
            and int(full.get("interior_rejected_frames") or 0) == 0
            and full.get("estimated_corners_sha256") != without_repair.get("estimated_corners_sha256")
        ):
            issues.append(
                {
                    "severity": "medium",
                    "category": full["category"],
                    "clip_id": full["clip_id"],
                    "method": "proposed vs no_offline_repair",
                    "check": "cross_run_nondeterminism",
                    "message": (
                        "the historical full and current no-repair trajectory hashes differ even though "
                        "the repair path had no eligible interval; small differences are not attributable to repair"
                    ),
                }
            )
    issues.append(
        {
            "severity": "medium",
            "category": "all",
            "clip_id": "four paired clips",
            "method": "all",
            "check": "sample_size",
            "message": "n=4 supports descriptive paired results only, not strong inferential claims",
        }
    )
    return issues


def aggregate(rows: list[dict]) -> list[dict]:
    full_by_clip = {
        row["clip_id"]: row for row in rows if row["method"] == "proposed"
    }
    output: list[dict] = []
    for method in METHODS:
        method_rows = [row for row in rows if row["method"] == method]
        summary: dict[str, object] = {"method": method, "n_clips": len(method_rows)}
        for output_name, (_, _, direction) in PRIMARY_METRICS.items():
            values = [float(row[output_name]) for row in method_rows if row.get(output_name) is not None]
            summary[f"{output_name}_median"] = median(values) if values else None
            q1, q3 = percentile(values, 0.25), percentile(values, 0.75)
            summary[f"{output_name}_iqr"] = (q3 - q1) if q1 is not None and q3 is not None else None
            degradations = [
                degradation(float(row[output_name]), float(full_by_clip[row["clip_id"]][output_name]), direction)
                for row in method_rows
                if row["clip_id"] in full_by_clip
                and row.get(output_name) is not None
                and full_by_clip[row["clip_id"]].get(output_name) is not None
            ]
            summary[f"{output_name}_degradation_median"] = (
                median(degradations) if degradations else None
            )
        output.append(summary)
    return output


def manuscript_gaps(paper_dir: Path) -> dict:
    manuscripts = [paper_dir / "manuscript" / "paper_zh.md", paper_dir / "manuscript" / "paper_en.md"]
    placeholder_dir = paper_dir / "manuscript" / "figures" / "placeholders"
    result = {"manuscripts": {}, "placeholder_figures": len(list(placeholder_dir.glob("*.svg")))}
    for path in manuscripts:
        text = path.read_text(encoding="utf-8")
        result["manuscripts"][path.name] = {
            "tbd_tokens": len(re.findall(r"\[TBD[^\]]*\]", text)),
            "placeholder_figure_references": len(re.findall(r"figures/placeholders/", text)),
        }
    return result


def main() -> None:
    parser = argparse.ArgumentParser(description="Summarize a four-variant ablation run.")
    parser.add_argument("run_dir", type=Path)
    parser.add_argument("--output-dir", type=Path, default=Path("doc/paper/results/ablation"))
    parser.add_argument("--paper-dir", type=Path, default=Path("doc/paper"))
    args = parser.parse_args()

    rows, issues = collect(args.run_dir.resolve())
    issues.extend(experimental_validity_issues(rows))
    summary = aggregate(rows)
    output_dir = args.output_dir.resolve()
    write_csv(output_dir / "ablation_clip_metrics.csv", rows)
    write_csv(output_dir / "ablation_table.csv", summary)
    quality = {
        "run_dir": str(args.run_dir),
        "expected_method_outputs": 16,
        "observed_method_outputs": len(rows),
        "expected_metric_outputs": 64,
        "observed_metric_outputs": sum(
            1
            for row in rows
            for metric_id in {item[0] for item in AUDIT_METRICS.values()}
            if (args.run_dir / row["category"] / row["clip_id"] / row["method"] / f"{metric_id}.json").exists()
        ),
        "issues": issues,
        "manuscript_gaps": manuscript_gaps(args.paper_dir.resolve()),
        "statistical_scope": "descriptive pilot; four paired clips are insufficient for strong inferential claims",
    }
    (output_dir / "ablation_quality.json").write_text(
        json.dumps(quality, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    print(
        f"wrote {len(rows)} clip-method rows, {len(summary)} summary rows, "
        f"and {len(issues)} quality issues to {output_dir}"
    )


if __name__ == "__main__":
    main()
