# Proposed Tuning Notes, 2026-07-14

## Goal

Reduce over-freezing in the Proposed reference tracker while preserving the
reference-anchored RANSAC tracker, reliability gates, offline repair, and
trajectory smoothing.

## Observed Issue

The first-pass Proposed run was visually stable, but tracker diagnostics showed
many clips accepting only 1--3 frames out of about 300. The dominant rejection
reasons were `low_coverage_x`, `low_coverage_y`, and a smaller number of
`invalid_geometry` cases. This made the temporal metric very low, but it also
allowed stale geometry to persist for long spans.

## Tracking-Only Sweep

To avoid repeatedly encoding videos, the sweep recomputed corner trajectories
and geometry/temporal metrics only. The sample focused on difficult clips:

- `hard_01`, `hard_10`
- `screen_video_07`, `screen_video_10`
- `scrolling_05`, `scrolling_10`
- `static_08`, `static_10`
- `weak_border_03`, `weak_border_10`

| Config | Median corner RMSE (px) | Median translation variation (px/frame) | Median tracker accept ratio |
|---|---:|---:|---:|
| current | 191.83 | 0.018 | 0.008 |
| balanced | 180.85 | 0.132 | 0.017 |
| balanced_y_loose | 242.43 | 4.986 | 0.528 |
| low_age | 104.78 | 4.993 | 0.554 |
| permissive_smoothed | 147.15 | 6.097 | 0.898 |

The `low_age` setting gave the best sampled geometry tradeoff without disabling
the tracker gates entirely. Its temporal value is higher because it follows more
estimated screen motion instead of freezing for most frames.

## Applied Change

The `dynamic` reference profile now uses softer gates:

- `reference_min_inliers = 24`
- `reference_min_inlier_ratio = 0.15`
- `reference_max_reprojection_error = 4.5`
- `reference_max_scale_step = 0.08`
- `reference_max_area_step = 0.18`
- `reference_min_point_age = 1`
- `reference_min_coverage_x = 0.08`
- `reference_min_coverage_y = 0.05`

Unchanged Proposed modules:

- fixed-reference LK tracking
- RANSAC homography estimation
- reliability gates
- offline geometry gate
- interpolation
- median and moving-average trajectory smoothing
- residual alignment

## Validation

- `uv run pytest`: 25 passed

## Next Evaluation

Run a full Proposed-only first pass with the tuned profile, then compare against
the existing Frame-wise and Optical-flow baselines. If full-run metrics match the
sample trend, refresh the paper results and manuscript figures.
