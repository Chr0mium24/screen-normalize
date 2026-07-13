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

Pending. This file will be updated after each stage.
