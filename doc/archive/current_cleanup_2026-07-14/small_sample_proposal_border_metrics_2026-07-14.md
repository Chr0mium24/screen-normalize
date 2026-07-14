# Small-Sample Metrics With Proposal Border

Date: 2026-07-14

## Scope

Reran the annotated two-per-category subset with geometry and temporal metrics only.

Clips:

- `static_01`, `static_02`
- `scrolling_01`, `scrolling_02`
- `screen_video_01`, `screen_video_02`
- `weak_border_01`, `weak_border_02`
- `hard_01`, `hard_02`

Methods:

- `frame_wise`
- `optical_flow`
- `proposed`
- `proposal_border`

Run directory:

- `runs/20260714_small_sample_with_proposal_border`

Command:

```powershell
uv run python scripts\run_batch.py --videos inputs\static\static_01.mp4 inputs\static\static_02.mp4 inputs\scrolling\scrolling_01.mp4 inputs\scrolling\scrolling_02.mp4 inputs\screen_video\screen_video_01.mp4 inputs\screen_video\screen_video_02.mp4 inputs\weak_border\weak_border_01.mp4 inputs\weak_border\weak_border_02.mp4 inputs\hard\hard_01.mp4 inputs\hard\hard_02.mp4 --methods frame_wise optical_flow proposed proposal_border --metrics geometry temporal --run-dir runs\20260714_small_sample_with_proposal_border
```

Completion:

- Batch status: 10/10 clips `ok`
- Geometry JSON files: 40/40
- Temporal JSON files: 40/40

## Overall Result

Values below are medians over the 10 clip-level p50 summaries.

| Method | Corner RMSE p50 median (px) | IoU p50 median | Translation p50 median (px/frame) |
|---|---:|---:|---:|
| `frame_wise` | 30.37 | 0.980 | 2.83 |
| `optical_flow` | 31.40 | 0.979 | 4.13 |
| `proposed` | 33.39 | 0.972 | 4.70 |
| `proposal_border` | 3.87 | 0.996 | 2.45 |

## Geometry by Category

Corner RMSE p50 median in pixels.

| Category | `frame_wise` | `optical_flow` | `proposed` | `proposal_border` |
|---|---:|---:|---:|---:|
| static | 33.13 | 33.49 | 2.44 | 3.60 |
| scrolling | 31.76 | 81.67 | 855.79 | 2.87 |
| screen_video | 30.08 | 29.46 | 2.90 | 3.75 |
| weak_border | 157.26 | 155.87 | 43.48 | 9.35 |
| hard | 9.62 | 24.90 | 41.78 | 10.70 |

## Temporal by Category

Translation p50 median in pixels/frame.

| Category | `frame_wise` | `optical_flow` | `proposed` | `proposal_border` |
|---|---:|---:|---:|---:|
| static | 3.08 | 3.22 | 3.22 | 3.26 |
| scrolling | 2.22 | 2.23 | 5.88 | 1.28 |
| screen_video | 3.72 | 3.36 | 3.21 | 3.25 |
| weak_border | 1.52 | 8.22 | 6.68 | 1.45 |
| hard | 5.19 | 8.56 | 6.53 | 3.74 |

## Proposal Border Per-Clip Check

| Clip | Corner RMSE p50 (px) | IoU p50 | Translation p50 (px/frame) |
|---|---:|---:|---:|
| `static/static_01` | 3.45 | 0.996 | 4.18 |
| `static/static_02` | 3.75 | 0.996 | 2.33 |
| `scrolling/scrolling_01` | 3.25 | 0.996 | 0.75 |
| `scrolling/scrolling_02` | 2.49 | 0.997 | 1.80 |
| `screen_video/screen_video_01` | 3.99 | 0.996 | 2.57 |
| `screen_video/screen_video_02` | 3.52 | 0.996 | 3.93 |
| `weak_border/weak_border_01` | 14.39 | 0.994 | 1.47 |
| `weak_border/weak_border_02` | 4.30 | 0.995 | 1.42 |
| `hard/hard_01` | 10.70 | 0.990 | 3.74 |
| `hard/hard_02` | 10.70 | 0.990 | 3.74 |

## Proposal Border Acceptance

`proposal_border` held 0 frames in all 10 clips.

| Clip | Accepted frames | Held frames | Reason counts |
|---|---:|---:|---|
| `static/static_01` | 300 | 0 | `initial=1`, `edge_accept=299` |
| `static/static_02` | 300 | 0 | `initial=1`, `edge_accept=299` |
| `scrolling/scrolling_01` | 299 | 0 | `initial=1`, `edge_accept=298` |
| `scrolling/scrolling_02` | 300 | 0 | `initial=1`, `edge_accept=299` |
| `screen_video/screen_video_01` | 300 | 0 | `initial=1`, `edge_accept=299` |
| `screen_video/screen_video_02` | 300 | 0 | `initial=1`, `edge_accept=299` |
| `weak_border/weak_border_01` | 300 | 0 | `initial=1`, `edge_accept=263`, `edge_accept_lk_conflict=36` |
| `weak_border/weak_border_02` | 300 | 0 | `initial=1`, `edge_accept=254`, `edge_accept_lk_conflict=45` |
| `hard/hard_01` | 300 | 0 | `initial=1`, `edge_accept=295`, `edge_accept_lk_conflict=4` |
| `hard/hard_02` | 300 | 0 | `initial=1`, `edge_accept=295`, `edge_accept_lk_conflict=4` |

## Interpretation

On this small annotated subset, `proposal_border` is now the strongest method for geometric accuracy and is also competitive or better in temporal translation. The biggest change is on scrolling clips, where the previous `proposed` method failed because interior reference features followed page motion; the border-guided method stays tied to the physical screen.

The result also changes the paper story. The old manuscript statement that the proposed method improves smoothness but not geometry applies to the old reference-anchored method, not to `proposal_border`. If the paper uses the new method as Proposed, the results and narrative should be regenerated around this run.

## Caveats

- This rerun covers the 10-clip annotated small subset, not all 50 active clips.
- Only geometry and temporal metrics were recomputed.
- `detail` and `frequency` were intentionally not rerun here.
