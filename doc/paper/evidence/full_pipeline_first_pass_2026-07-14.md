# Full Pipeline First Pass Run Record

Date: 2026-07-14
Branch: `experiment/full-pipeline-first-pass`

## Goal

Run the current end-to-end experiment pipeline once over the active local dataset, without stopping to improve failed cases. Failures, missing metrics, and questionable outputs are recorded for later repair.

## Scope

- Dataset root: `inputs/`
- Active categories: `static`, `scrolling`, `screen_video`, `weak_border`, `hard`
- Expected local clips: 50 mp4 files, 10 per category
- Expected local annotations: 50 sidecar CSV files
- Main methods: `frame_wise`, `optical_flow`, `proposed`
- Metrics: `geometry`, `temporal`, `detail`, `frequency`

## Planned Commands

Smoke batch, one clip per category:

```bash
uv run scripts/run_batch.py --videos inputs/static/static_01.mp4 inputs/scrolling/scrolling_01.mp4 inputs/screen_video/screen_video_01.mp4 inputs/weak_border/weak_border_01.mp4 inputs/hard/hard_01.mp4 --methods frame_wise optical_flow proposed --metrics geometry temporal detail frequency --run-dir runs/20260714_full_pipeline_smoke
```

Full first pass:

```bash
uv run scripts/run_batch.py --input inputs --methods frame_wise optical_flow proposed --metrics geometry temporal detail frequency --run-dir runs/20260714_full_pipeline_first_pass
```

Paper result summary:

```bash
uv run scripts/paper/make_paper_results.py runs/20260714_full_pipeline_first_pass
```

## Results

## Stage 1: Smoke Batch

Command:

```bash
uv run scripts/run_batch.py --videos inputs/static/static_01.mp4 inputs/scrolling/scrolling_01.mp4 inputs/screen_video/screen_video_01.mp4 inputs/weak_border/weak_border_01.mp4 inputs/hard/hard_01.mp4 --methods frame_wise optical_flow proposed --metrics geometry temporal detail frequency --run-dir runs/20260714_full_pipeline_smoke
```

Run directory:

```text
runs/20260714_full_pipeline_smoke
```

Outcome:

- Batch status: 5/5 clips `ok`
- Method videos: 15 `normalized.mp4` files
- Metric JSON files: 60
- Failed method or metric JSON files: 0
- Run index: `runs/20260714_full_pipeline_smoke/index.html`
- Per-clip reports: 5 `report.html` files

Notes:

- The active direct-child dataset layout was accepted by `scripts/run_batch.py`.
- The smoke covered one clip from each active category.

## Stage 2: Full Main Experiment

Command:

```bash
uv run scripts/run_batch.py --input inputs --methods frame_wise optical_flow proposed --metrics geometry temporal detail frequency --run-dir runs/20260714_full_pipeline_first_pass
```

Run directory:

```text
runs/20260714_full_pipeline_first_pass
```

Outcome:

- Batch status: 50/50 clips `ok`
- Completed reports by category: `hard=10`, `screen_video=10`, `scrolling=10`, `static=10`, `weak_border=10`
- Method videos: 150 `normalized.mp4` files
- Metric JSON files: 600
- Failed method or metric JSON files: 0
- Run index: `runs/20260714_full_pipeline_first_pass/index.html`
- Logs: `runs/20260714_full_pipeline_first_pass.stdout.log`, `runs/20260714_full_pipeline_first_pass.stderr.log`

First-pass audit notes:

- This is a computational completion result, not a quality acceptance result.
- Several `hard` and `weak_border` clips showed very high reference-tracker rejection counts in stderr progress logs.
- Those clips should be manually reviewed in the generated HTML reports before writing final claims.

## Stage 3: Main Paper Summary

Command:

```bash
uv run scripts/paper/make_paper_results.py runs/20260714_full_pipeline_first_pass
```

Generated local summary:

```text
runs/20260714_full_pipeline_first_pass/summary
```

Committed summary evidence:

```text
doc/paper/results/full_pipeline_first_pass/
```

Outcome:

- `figure_03_geometry_comparison.svg`: generated
- `figure_06_detail_frequency.svg`: generated
- `figure_04_temporal_stability.svg`: omitted because the current summary script expects all `METHOD_IDS`, including `point_edge`, while this first pass ran only three main methods.
- `figure_07_ablation.svg`: omitted because this main run does not contain ablation methods.
- Metric status summary: `detail=150 ok`, `frequency=150 ok`, `temporal=150 ok`, `geometry=135 ok`, `geometry=15 skipped`
- Non-ok metric scope: `scrolling_06` through `scrolling_10`, all three methods, geometry only
- Non-ok reason: `no overlapping annotation and estimate frames`

Evidence files copied to `doc/paper/results/full_pipeline_first_pass/` include `batch.csv`, `aggregate_metrics.csv`, `all_metrics.csv`, per-metric tables, metric status tables, the figure manifest, and generated SVG figures.

## Stage 4: Full Ablation First Pass Plan

The main three-method run is kept separate from ablation outputs so that `make_paper_results.py` can read the main run without encountering ablation-only method IDs.

Planned ablation command:

```bash
uv run scripts/run_batch.py --input inputs --methods no_reliability_gates no_trajectory_smoothing no_offline_repair --metrics geometry temporal detail frequency --run-dir runs/20260714_full_ablation_first_pass
```

Planned run directory:

```text
runs/20260714_full_ablation_first_pass
```

The corresponding `proposed` outputs for ablation comparison will be read from `runs/20260714_full_pipeline_first_pass`. The first pass will record failures and missing metrics without changing the algorithm.

## Stage 4: Full Ablation First Pass Result

Command:

```bash
uv run scripts/run_batch.py --input inputs --methods no_reliability_gates no_trajectory_smoothing no_offline_repair --metrics geometry temporal detail frequency --run-dir runs/20260714_full_ablation_first_pass
```

Run directory:

```text
runs/20260714_full_ablation_first_pass
```

Outcome:

- Ablation batch status: 50/50 clips `ok`
- Completed reports by category: `hard=10`, `screen_video=10`, `scrolling=10`, `static=10`, `weak_border=10`
- Ablation method videos: 150 `normalized.mp4` files
- Ablation metric JSON files: 600
- Failed ablation method or metric JSON files: 0
- Logs: `runs/20260714_full_ablation_first_pass.stdout.log`, `runs/20260714_full_ablation_first_pass.stderr.log`

Committed summary evidence:

```text
doc/paper/results/full_ablation_first_pass/
```

Combined comparison summary:

- Compared methods: `proposed` from the main run plus the three ablation methods from the ablation run
- Combined method-metric records: 800
- Metric status summary: `detail=200 ok`, `frequency=200 ok`, `temporal=200 ok`, `geometry=180 ok`, `geometry=20 skipped`
- Non-ok metric scope: `scrolling_06` through `scrolling_10`, all four compared methods, geometry only
- Non-ok reason: `no overlapping annotation and estimate frames`

First-pass interpretation notes:

- This stage proves the ablation configurations can run across all 50 clips, but does not prove the module conclusions are valid.
- `hard` and `weak_border` still need manual HTML/video review because logs show high reference-tracker rejection in several clips.
- `no_offline_repair` matches `proposed` in the aggregate first-pass primary metrics, so this module remains potentially inconclusive until repair-triggering intervals are audited.
