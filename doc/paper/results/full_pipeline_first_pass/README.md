# Full Pipeline First Pass Results

Date: 2026-07-14
Source run: `runs/20260714_full_pipeline_first_pass`

This directory contains committed summary evidence from the first full main-method pass over the active local dataset. Large generated videos, per-frame images, HTML reports, and run logs remain local under `runs/`.

## Scope

- Clips processed: 50/50
- Categories: `hard`, `screen_video`, `scrolling`, `static`, `weak_border`
- Methods: `frame_wise`, `optical_flow`, `proposed`
- Metrics requested: `geometry`, `temporal`, `detail`, `frequency`

## Completion

- `batch.csv`: 50/50 clips completed with batch status `ok`
- Method outputs: 150 local `normalized.mp4` files
- Metric JSON files: 600 local files
- Failed method or metric JSON files: 0
- Non-ok metrics: 15 geometry records with status `skipped`

## Known First-Pass Issues

- `scrolling_06` through `scrolling_10` have no overlapping annotation and estimate frames for geometry evaluation, so geometry aggregates use 45 clips per method rather than 50.
- `figure_04` was omitted by the current paper summary script because it expects every `METHOD_IDS` method, including `point_edge`, while this first pass intentionally ran only the three main methods.
- `figure_07` was omitted because this run does not include ablation methods.
- Several `hard` and `weak_border` clips showed high reference-tracker rejection counts in stderr progress logs; these require manual HTML/video review before final claims.

## Files

- `aggregate_metrics.csv`: method-level metric aggregates used for first-pass result reading.
- `all_metrics.csv`: flattened metric JSON records.
- `*_table.csv`: per-metric flattened tables.
- `metric_status.csv`: status of every method-metric JSON.
- `non_ok_metrics.csv`: non-ok metric records requiring follow-up.
- `figure_manifest.json`: generated/omitted figure status from `make_paper_results.py`.
- `figures/`: generated SVG figures from the first-pass summary.
