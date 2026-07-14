# Annotated Two-Per-Category Geometry/Temporal Rerun

Date: 2026-07-14

This archive records a lightweight rerun after the active dataset annotation CSV files were completed. The run uses two clips from each active category and recomputes only geometry and temporal metrics.

## Scope

| Category | Clips |
| --- | --- |
| static | `static_01`, `static_02` |
| scrolling | `scrolling_01`, `scrolling_02` |
| screen_video | `screen_video_01`, `screen_video_02` |
| weak_border | `weak_border_01`, `weak_border_02` |
| hard | `hard_01`, `hard_02` |

## Methods

- Main comparison: `frame_wise`, `optical_flow`, `proposed`
- Ablation comparison: `proposed`, `no_reliability_gates`, `no_trajectory_smoothing`, `no_offline_repair`

## Metrics

- Recomputed in this archive: `geometry`, `temporal`
- Intentionally not recomputed: `detail`, `frequency`

The `detail` and `frequency` metrics are video-reading quality diagnostics and were skipped to keep this CPU rerun short. Do not interpret missing `detail` or `frequency` rows in this archive as run failures.

## Result Locations

- Main geometry/temporal summary: `results/main_geometry_temporal/`
- Ablation geometry/temporal summary: `results/ablation_geometry_temporal/`

For the ablation output, use `metric_status_geometry_temporal.csv`, `non_ok_geometry_temporal.csv`, and `ablation_aggregate_geometry_temporal.csv` when reading this archive. The unfiltered script outputs also list missing `detail` and `frequency` records because those metrics were intentionally omitted.

## Completion

- Main subset batch: 10/10 clips `ok`
- Ablation subset batch: 10/10 clips `ok`
- Main geometry records: 30 method-clip rows
- Main temporal records: 30 method-clip rows
- Ablation geometry/temporal status rows: 80 method-clip-metric rows
- Geometry/temporal non-ok rows: 0
