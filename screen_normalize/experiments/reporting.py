from __future__ import annotations

import csv
import html
import os
from pathlib import Path
from typing import Any

from .run_io import METHOD_IDS, METRIC_IDS, read_json


STYLE = """
body{font:14px system-ui,sans-serif;margin:0;color:#202124;background:#f6f7f8}main{max-width:1180px;margin:auto;padding:24px}
h1,h2{letter-spacing:0}a{color:#0759a5}table{border-collapse:collapse;width:100%;background:white}th,td{border:1px solid #d8dce0;padding:7px;text-align:left;vertical-align:top}th{background:#eef1f3}
.videos{display:grid;grid-template-columns:repeat(auto-fit,minmax(280px,1fr));gap:12px}.panel{background:white;border:1px solid #d8dce0;border-radius:6px;padding:12px;margin:12px 0}video{width:100%;background:#111}.ok{color:#176b3a}.failed{color:#a1261d}.skipped{color:#765900}code{white-space:pre-wrap}
"""


def _relative(target: Path, document: Path) -> str:
    return Path(os.path.relpath(target.resolve(), document.parent.resolve())).as_posix()


def _summary_value(summary: dict[str, Any]) -> str:
    preferred = (
        "corner_rmse_px_mean",
        "quad_iou_mean",
        "translation_px_mean",
        "rotation_abs_deg_mean",
        "edge_preservation_index_mean",
        "fft_orthogonality_error_deg_mean",
    )
    values = []
    for key in preferred:
        if key in summary and summary[key] is not None:
            values.append(f"{key}: {summary[key]:.4g}" if isinstance(summary[key], float) else f"{key}: {summary[key]}")
    return "<br>".join(html.escape(value) for value in values) or html.escape(str(summary.get("reason") or "-"))


def render_clip_report(
    clip_dir: Path,
    original_video: Path,
    category: str,
    clip_id: str,
    methods: list[str],
) -> Path:
    output = clip_dir / "report.html"
    videos = [f'<div><h3>Original</h3><video controls preload="metadata" src="{html.escape(_relative(original_video, output))}"></video></div>']
    rows = []
    for method in methods:
        method_dir = clip_dir / method
        normalized = method_dir / "normalized.mp4"
        if normalized.exists():
            videos.append(f'<div><h3>{html.escape(method)}</h3><video controls preload="metadata" src="{html.escape(_relative(normalized, output))}"></video></div>')
        cells = [f"<th>{html.escape(method)}</th>"]
        for metric in METRIC_IDS:
            path = method_dir / f"{metric}.json"
            summary = read_json(path) if path.exists() else {"status": "skipped", "reason": "not selected"}
            status = html.escape(str(summary.get("status", "unknown")))
            cells.append(f'<td><span class="{status}">{status}</span><br>{_summary_value(summary)}</td>')
        rows.append("<tr>" + "".join(cells) + "</tr>")
    tracker_rows = []
    for method in methods:
        debug = clip_dir / method / "debug.csv"
        if not debug.exists():
            continue
        with debug.open(newline="") as handle:
            records = list(csv.DictReader(handle))
        rejected = sum(1 for row in records if row.get("accepted", "").lower() in ("false", "0"))
        tracker_rows.append(f"<li>{html.escape(method)}: {len(records)} rows, {rejected} rejected</li>")
    artifacts = []
    for method in methods:
        for path in sorted((clip_dir / method).glob("*.png")) + sorted((clip_dir / method).glob("*.jpg")):
            artifacts.append(f'<figure><img src="{html.escape(_relative(path, output))}" style="max-width:100%"><figcaption>{html.escape(method + ": " + path.stem)}</figcaption></figure>')
    output.write_text(
        "<!doctype html><meta charset=utf-8><title>" + html.escape(clip_id) + "</title><style>" + STYLE + "</style><main>"
        f"<h1>{html.escape(clip_id)}</h1><p>Category: {html.escape(category)}</p>"
        '<section class="panel"><h2>Videos</h2><div class="videos">' + "".join(videos) + "</div></section>"
        '<section class="panel"><h2>Metrics</h2><table><tr><th>Method</th>' + "".join(f"<th>{name}</th>" for name in METRIC_IDS) + "</tr>" + "".join(rows) + "</table></section>"
        '<section class="panel"><h2>Tracker diagnostics</h2><ul>' + "".join(tracker_rows) + "</ul></section>"
        '<section class="panel"><h2>Visual diagnostics</h2>' + ("".join(artifacts) or "<p>No visual artifacts were requested.</p>") + "</section>"
        '<section class="panel"><h2>Review notes</h2><p>Record manual conclusions in <code>notes.md</code>.</p></section></main>',
        encoding="utf-8",
    )
    notes = clip_dir / "notes.md"
    if not notes.exists():
        notes.write_text(f"# {clip_id} review\n\n- Status: pending\n- Notes:\n", encoding="utf-8")
    return output


def render_run_index(run_dir: Path, records: list[dict[str, str]]) -> Path:
    output = run_dir / "index.html"
    rows = []
    for record in records:
        report = run_dir / record["category"] / record["clip_id"] / "report.html"
        link = html.escape(_relative(report, output)) if report.exists() else "#"
        status = html.escape(record["status"])
        rows.append(f'<tr><td>{html.escape(record["category"])}</td><td><a href="{link}">{html.escape(record["clip_id"])}</a></td><td class="{status}">{status}</td><td>{html.escape(record.get("reason", ""))}</td></tr>')
    output.write_text(
        "<!doctype html><meta charset=utf-8><title>Experiment run</title><style>" + STYLE + "</style><main><h1>Experiment run</h1>"
        "<table><tr><th>Category</th><th>Clip</th><th>Status</th><th>Reason</th></tr>" + "".join(rows) + "</table></main>",
        encoding="utf-8",
    )
    return output
