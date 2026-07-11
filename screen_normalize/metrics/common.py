from __future__ import annotations

from pathlib import Path
from typing import Any, Callable

from ..run_io import write_csv, write_json


MetricPayload = tuple[list[dict[str, Any]], dict[str, Any]]


def persist_metric(output_dir: Path, name: str, payload: MetricPayload) -> dict[str, Any]:
    rows, summary = payload
    write_csv(output_dir / f"{name}_frames.csv", rows)
    write_json(output_dir / f"{name}.json", summary)
    return summary


def run_guarded(output_dir: Path, name: str, function: Callable[[], MetricPayload]) -> dict[str, Any]:
    try:
        return persist_metric(output_dir, name, function())
    except (Exception, SystemExit) as exc:
        summary = {"status": "failed", "reason": f"{type(exc).__name__}: {exc}"}
        write_csv(output_dir / f"{name}_frames.csv", [])
        write_json(output_dir / f"{name}.json", summary)
        return summary
