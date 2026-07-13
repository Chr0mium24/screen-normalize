# Full Ablation First Pass Results

Date: 2026-07-14

This directory contains committed summary evidence from the first full ablation pass. The ablation methods were run in a separate local run directory so the main three-method paper summary remains clean.

## Source Runs

- Main/proposed source: `runs/20260714_full_pipeline_first_pass`
- Ablation source: `runs/20260714_full_ablation_first_pass`

## Scope

- Clips processed by ablation run: 50/50
- Ablation methods: `no_reliability_gates`, `no_trajectory_smoothing`, `no_offline_repair`
- Comparison method: `proposed`, read from the main first-pass run
- Metrics: `geometry`, `temporal`, `detail`, `frequency`

## Completion

- Ablation batch status: 50/50 clips `ok`
- Ablation method videos: 150 local `normalized.mp4` files
- Ablation metric JSON files: 600 local files
- Failed ablation method or metric JSON files: 0
- Combined comparison metric records: 800 method-metric records across 4 methods
- Non-ok combined metrics: 20 geometry records with status `skipped`
- Figure output: `figures/figure_07_ablation_first_pass.svg`

## Known First-Pass Issues

- `scrolling_06` through `scrolling_10` only have frame-0 annotations. Geometry evaluation excludes frame 0 because it is used for initialization, so those geometry rows are intentionally skipped across all four comparison methods.
- Geometry aggregates use 45 clips per method; temporal, detail, and frequency aggregates use 50 clips per method.
- This is a computational first pass. The ablation interpretation still needs manual review, especially high rejection behavior in `hard` and `weak_border`.
- `no_offline_repair` currently matches `proposed` in the aggregate first-pass primary metrics, so this module may still be weakly exercised or non-informative in the current dataset.

## Files

- `batch.csv`: ablation run batch status.
- `metric_status.csv`: status of every combined method-metric record.
- `non_ok_metrics.csv`: non-ok method-metric records requiring follow-up.
- `ablation_clip_metrics.csv`: one row per clip and comparison method with key metrics.
- `ablation_aggregate_metrics.csv`: aggregate first-pass metrics for proposed and the three ablation methods.
- `figures/figure_07_ablation_first_pass.svg`: first-pass ablation figure generated from `ablation_aggregate_metrics.csv`.
