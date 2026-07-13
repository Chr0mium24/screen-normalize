# Code Organization Cleanup

Date: 2026-07-14

## Goal

Keep the post-refactor package layout intact while reducing noise in the top-level `scripts/` directory. The package modules under `screen_normalize/` remain organized by responsibility; this cleanup only moves command scripts into function-specific folders.

## Script Layout

- `scripts/`: daily project entrypoints such as normalization, annotation, segmentation, single-video analysis, and batch analysis.
- `scripts/diagnostics/`: exploratory diagnostics for reference points and screen-edge observations.
- `scripts/dataset/`: one-off dataset naming and migration utilities.
- `scripts/paper/`: paper figures, PDFs, result summaries, and report artifacts.
- `scripts/paper/ablation/`: ablation staging, summarization, and report generation.
- `scripts/archive/`: old pre-pipeline entrypoints kept only for traceability.

## Result

No algorithm behavior changes are intended. README, evidence manifests, and tests should reference the new paths. Python commands should be run through `uv run`.
