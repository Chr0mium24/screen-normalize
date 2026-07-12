from __future__ import annotations

import csv
import json
from datetime import datetime
from pathlib import Path
from typing import Any, Iterable

from ..common import clean_path_component, create_run_directory, project_root
from .evaluation import as_jsonable


METHOD_IDS = ("frame_wise", "optical_flow", "proposed")
METRIC_IDS = ("geometry", "temporal", "detail", "frequency")


def create_analysis_run(runs_dir: Path | None = None, name: str = "analysis") -> Path:
    root = (runs_dir or project_root() / "runs").resolve()
    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    return create_run_directory(root, f"{timestamp}_{clean_path_component(name)}").resolve()


def clip_directory(run_dir: Path, category: str, clip_id: str) -> Path:
    path = run_dir / clean_path_component(category) / clean_path_component(clip_id)
    path.mkdir(parents=True, exist_ok=True)
    return path


def method_directory(run_dir: Path, category: str, clip_id: str, method: str) -> Path:
    if method not in METHOD_IDS:
        raise ValueError(f"unsupported method: {method}")
    path = clip_directory(run_dir, category, clip_id) / method
    path.mkdir(parents=True, exist_ok=True)
    return path


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(as_jsonable(payload), indent=2, ensure_ascii=True) + "\n")


def read_json(path: Path) -> Any:
    return json.loads(path.read_text())


def write_csv(path: Path, rows: Iterable[dict[str, Any]]) -> None:
    materialized = list(rows)
    fields: list[str] = []
    for row in materialized:
        fields.extend(key for key in row if key not in fields)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        if fields:
            writer.writeheader()
            writer.writerows(materialized)
