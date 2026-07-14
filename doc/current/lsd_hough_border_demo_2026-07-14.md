# LSD and Hough Border Demo Check

Date: 2026-07-14

## Question

Does using LSD or Hough line segments improve the proposal-style border demo?

## Change

The proposal demo now supports three edge observation modes:

- `profile`: the existing normal-gradient edge sampler around each predicted screen edge.
- `hough`: Canny + probabilistic Hough line segments filtered near each predicted edge.
- `lsd`: OpenCV Line Segment Detector segments filtered near each predicted edge.

Command form:

```powershell
uv run python scripts\demo_proposal_method.py inputs\scrolling\scrolling_01.mp4 --edge-detector hough --run-name proposal_demo_scrolling_01_hough --width 960 --height 540 --no-overlay
uv run python scripts\demo_proposal_method.py inputs\scrolling\scrolling_01.mp4 --edge-detector lsd --run-name proposal_demo_scrolling_01_lsd --width 960 --height 540 --no-overlay
```

The default remains `profile`.

## Result on `scrolling_01`

| Detector | Corner RMSE p50 (px) | IoU p50 | Translation p50 (px/frame) | Accepted updates | Held frames |
|---|---:|---:|---:|---:|---:|
| `profile` | 3.25 | 0.9960 | 0.75 | 298 | 0 |
| `hough` | 27.33 | 0.9742 | 0.90 | 298 | 0 |
| `lsd` | 3.60 | 0.9957 | 0.96 | 298 | 0 |

Debug reason counts:

- `profile`: `initial` = 1, `edge_accept` = 298.
- `hough`: `initial` = 1, `edge_accept` = 296, `edge_accept_lk_conflict` = 2.
- `lsd`: `initial` = 1, `edge_accept` = 298.

Runtime observation:

- Hough was much slower than `profile` on the full 299-frame 4K clip.
- LSD was slower again, taking close to five minutes on this single clip.

## Interpretation

LSD works and produces geometry close to the current `profile` detector on this scrolling clip, but it is slower and not better. Hough is stable enough to accept every update, but its line fit is less accurate here, with median corner RMSE increasing from 3.25 px to 27.33 px.

For now, `profile` should remain the default detector for `proposal_border`. LSD is useful as a diagnostic or fallback candidate. Hough is not a better default without additional tuning.

## Verification

```powershell
uv run pytest
```

Result: 27 passed.
