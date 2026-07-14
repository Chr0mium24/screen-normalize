# Scrolling Proposal Demo Comparison

Date: 2026-07-14

## Question

Does the small proposal-method demo perform better than the current reference-anchored `proposed` method on scrolling videos?

## Scope

This is a narrow check on the two scrolling clips used by the current annotated paper subset:

- `inputs/scrolling/scrolling_01.mp4`
- `inputs/scrolling/scrolling_02.mp4`

The comparison uses the existing current-method results from:

- `runs/20260714_annotated_two_per_category_main/scrolling/scrolling_01/proposed`
- `runs/20260714_annotated_two_per_category_main/scrolling/scrolling_02/proposed`

The proposal demo was run with:

```powershell
uv run python scripts\demo_proposal_method.py inputs\scrolling\scrolling_01.mp4 --run-name proposal_demo_scrolling_01 --width 960 --height 540 --no-overlay
uv run python scripts\demo_proposal_method.py inputs\scrolling\scrolling_02.mp4 --run-name proposal_demo_scrolling_02 --width 960 --height 540 --no-overlay
```

Metrics were computed with the existing geometry and temporal evaluators:

```powershell
uv run python scripts\evaluate_geometry.py inputs\scrolling\scrolling_01.mp4 runs\proposal_demo_scrolling_01\smoothed_corners.csv runs\proposal_demo_scrolling_01\geometry_eval --annotations inputs\scrolling\scrolling_01.csv
uv run python scripts\evaluate_temporal.py runs\proposal_demo_scrolling_01\smoothed_corners.csv runs\proposal_demo_scrolling_01\temporal_eval
uv run python scripts\evaluate_geometry.py inputs\scrolling\scrolling_02.mp4 runs\proposal_demo_scrolling_02\smoothed_corners.csv runs\proposal_demo_scrolling_02\geometry_eval --annotations inputs\scrolling\scrolling_02.csv
uv run python scripts\evaluate_temporal.py runs\proposal_demo_scrolling_02\smoothed_corners.csv runs\proposal_demo_scrolling_02\temporal_eval
```

## Result

| Clip | Method | Corner RMSE p50 (px) | IoU p50 | Translation p50 (px/frame) | Demo held frames |
|---|---:|---:|---:|---:|---:|
| `scrolling_01` | Current `proposed` | 635.53 | 0.522 | 3.47 | n/a |
| `scrolling_01` | Proposal demo | 3.25 | 0.996 | 0.75 | 0 |
| `scrolling_02` | Current `proposed` | 918.17 | 0.389 | 5.28 | n/a |
| `scrolling_02` | Proposal demo | 2.49 | 0.997 | 1.80 | 0 |

Demo update summaries:

- `scrolling_01`: 299 frames, 298 accepted updates after initialization, 0 held frames.
- `scrolling_02`: 300 frames, 299 accepted updates after initialization, 0 held frames.

## Interpretation

On these two scrolling clips, the proposal demo is clearly better than the current `proposed` method in both annotated geometry and estimated temporal stability. The improvement is consistent with the method difference: the current method estimates the screen plane from interior reference features, which can be contaminated by scrolling page content, while the demo estimates the quadrilateral from physical screen-border evidence and only uses LK/RANSAC as a consistency check.

This result should not yet be generalized to the whole project. It only covers the scrolling subset. The proposal demo still needs the same checks on static, screen-video, weak-border, and hard scenes before replacing the current method in the paper.
