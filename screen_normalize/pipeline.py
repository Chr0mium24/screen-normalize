from __future__ import annotations

from pathlib import Path
from typing import Any

from .metrics import evaluate_detail, evaluate_frequency, evaluate_geometry, evaluate_temporal
from .reporting import render_clip_report
from .run_io import METHOD_IDS, METRIC_IDS, clip_directory, method_directory, write_json
from .runner import run_method


def analyze_clip(
    video: Path,
    run_dir: Path,
    methods: list[str] | tuple[str, ...] = METHOD_IDS,
    metrics: list[str] | tuple[str, ...] = METRIC_IDS,
    *,
    reuse_outputs: bool = False,
    skip_existing: bool = False,
) -> dict[str, Any]:
    video = video.resolve()
    category, clip_id = video.parent.name, video.stem
    annotation = video.with_suffix(".csv")
    clip_dir = clip_directory(run_dir, category, clip_id)
    failures: list[str] = []
    for method in methods:
        output_dir = method_directory(run_dir, category, clip_id, method)
        normalized = output_dir / "normalized.mp4"
        estimates = output_dir / "estimated_corners.csv"
        if not (reuse_outputs and normalized.exists() and estimates.exists()):
            try:
                run_method(video, output_dir, method)
            except Exception as exc:
                reason = f"{type(exc).__name__}: {exc}"
                write_json(output_dir / "method.json", {"status": "failed", "method": method, "reason": reason})
                failures.append(f"{method}: {reason}")
                continue
        for metric in metrics:
            target = output_dir / f"{metric}.json"
            if skip_existing and target.exists():
                continue
            if metric == "geometry":
                summary = evaluate_geometry(video, annotation if annotation.exists() else None, estimates, output_dir)
            elif metric == "temporal":
                summary = evaluate_temporal(estimates, output_dir)
            elif metric == "detail":
                summary = evaluate_detail(normalized, video, annotation if annotation.exists() else None, output_dir)
            elif metric == "frequency":
                summary = evaluate_frequency(normalized, output_dir)
            else:
                raise ValueError(f"unsupported metric: {metric}")
            if summary["status"] == "failed":
                failures.append(f"{method}/{metric}: {summary.get('reason')}")
    report_methods = [method for method in METHOD_IDS if (clip_dir / method / "method.json").exists()]
    report = render_clip_report(clip_dir, video, category, clip_id, report_methods)
    return {
        "category": category,
        "clip_id": clip_id,
        "status": "failed" if failures else "ok",
        "reason": "; ".join(failures),
        "report": str(report),
    }
