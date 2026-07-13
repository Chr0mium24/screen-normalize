#!/usr/bin/env python3
from __future__ import annotations

import argparse
import shutil
from pathlib import Path


ITEMS = [
    {"category": "static", "old": "IMG_0957", "new": "static_01", "extension": ".MOV", "source_subdir": ""},
    {"category": "static", "old": "IMG_0974", "new": "static_02", "extension": ".MOV", "source_subdir": ""},
    {
        "category": "static",
        "old": "VID20260712170254",
        "new": "static_03",
        "extension": ".mp4",
        "source_subdir": "",
    },
    {"category": "scrolling", "old": "IMG_0958", "new": "scrolling_01", "extension": ".MOV", "source_subdir": ""},
    {"category": "scrolling", "old": "IMG_0959", "new": "scrolling_02", "extension": ".MOV", "source_subdir": ""},
    {
        "category": "scrolling",
        "old": "VID20260712165829",
        "new": "scrolling_03",
        "extension": ".mp4",
        "source_subdir": "",
    },
    {
        "category": "screen_video",
        "old": "IMG_0963 (1)",
        "new": "screen_video_01",
        "extension": ".MOV",
        "source_subdir": "",
    },
    {
        "category": "screen_video",
        "old": "IMG_0968",
        "new": "screen_video_02",
        "extension": ".MOV",
        "source_subdir": "",
    },
    {
        "category": "screen_video",
        "old": "VID20260712170039",
        "new": "screen_video_03",
        "extension": ".mp4",
        "source_subdir": "",
    },
    {
        "category": "weak_border",
        "old": "IMG_0964",
        "new": "weak_border_01",
        "extension": ".MOV",
        "source_subdir": "",
    },
    {
        "category": "hard",
        "old": "VID20260712170803",
        "new": "hard_01",
        "extension": ".mp4",
        "source_subdir": "moire",
    },
]


def assert_within(path: Path, root: Path) -> Path:
    resolved = path.resolve()
    root_resolved = root.resolve()
    if resolved == root_resolved or root_resolved in resolved.parents:
        return resolved
    raise ValueError(f"refusing path outside inputs: {resolved}")


def move_checked(source: Path, destination: Path, inputs_root: Path) -> None:
    source_path = assert_within(source, inputs_root)
    destination_path = assert_within(destination, inputs_root)
    if not source_path.exists():
        if destination_path.exists():
            return
        raise FileNotFoundError(f"missing source: {source_path}")
    if destination_path.exists():
        raise FileExistsError(f"destination already exists: {destination_path}")
    destination_path.parent.mkdir(parents=True, exist_ok=True)
    shutil.move(str(source_path), str(destination_path))


def replace_in_html(root: Path, replacements: dict[str, str]) -> int:
    runs_root = root / "runs"
    if not runs_root.exists():
        return 0
    updated = 0
    for path in runs_root.rglob("*.html"):
        text = path.read_text(encoding="utf-8")
        new_text = text
        for old, new in replacements.items():
            new_text = new_text.replace(old, new)
        if new_text != text:
            path.write_text(new_text, encoding="utf-8")
            updated += 1
    return updated


def rename_collected_dataset(repo_root: Path, update_historical_html: bool = True) -> tuple[int, int]:
    inputs_root = repo_root / "inputs"
    replacements: dict[str, str] = {}

    for item in ITEMS:
        category_root = inputs_root / item["category"]
        source_root = category_root / item["source_subdir"] if item["source_subdir"] else category_root
        old_source = source_root / f"{item['old']}{item['extension']}"
        new_source = category_root / f"{item['new']}{item['extension']}"
        move_checked(old_source, new_source, inputs_root)

        old_csv = source_root / f"{item['old']}.csv"
        new_csv = category_root / f"{item['new']}.csv"
        if old_csv.exists() or new_csv.exists():
            move_checked(old_csv, new_csv, inputs_root)

        old_segment_dir = category_root / "segments" / item["old"]
        new_segment_dir = category_root / "segments" / item["new"]
        if old_segment_dir.exists():
            for child in old_segment_dir.iterdir():
                if child.is_file() and child.stem.lower().startswith(item["old"].lower()):
                    suffix = child.stem[len(item["old"]) :]
                    move_checked(child, old_segment_dir / f"{item['new']}{suffix}{child.suffix}", inputs_root)
            move_checked(old_segment_dir, new_segment_dir, inputs_root)

        old_category_path = f"inputs/{item['category']}/"
        if item["source_subdir"]:
            old_category_path += f"{item['source_subdir']}/"
        replacements[f"{old_category_path}{item['old']}{item['extension']}"] = (
            f"inputs/{item['category']}/{item['new']}{item['extension']}"
        )
        replacements[f"inputs/{item['category']}/segments/{item['old']}/"] = (
            f"inputs/{item['category']}/segments/{item['new']}/"
        )
        replacements[item["old"]] = item["new"]

    html_updates = replace_in_html(repo_root, replacements) if update_historical_html else 0
    return len(ITEMS), html_updates


def main() -> None:
    parser = argparse.ArgumentParser(description="Rename collected source clips into paper dataset IDs.")
    parser.add_argument("--repo-root", type=Path, default=Path(__file__).resolve().parents[2])
    parser.add_argument(
        "--no-update-historical-html",
        action="store_true",
        help="Do not rewrite historical run HTML references.",
    )
    args = parser.parse_args()

    renamed, html_updates = rename_collected_dataset(
        args.repo_root.resolve(), update_historical_html=not args.no_update_historical_html
    )
    print(f"renamed {renamed} collected source clips; updated {html_updates} historical HTML files")


if __name__ == "__main__":
    main()
