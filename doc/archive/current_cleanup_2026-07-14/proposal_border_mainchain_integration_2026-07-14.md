# Proposal Border Main-Chain Integration

Date: 2026-07-14

## Change

The proposal-method demo is now integrated into the main experiment pipeline as a runnable method:

- Method id: `proposal_border`
- Main entry point: `scripts/run_batch.py --methods proposal_border`
- Output layout: the same per-method directory structure as `frame_wise`, `optical_flow`, `proposed`, and `point_edge`

The existing `proposed` method is unchanged. It remains the reference-anchored LK/RANSAC/gate method. The new `proposal_border` method is the border-guided proposal-style path.

## Implementation

Updated files:

- `screen_normalize/experiments/run_io.py`: adds `proposal_border` to `METHOD_IDS`.
- `screen_normalize/experiments/runner.py`: routes `proposal_border` through `estimate_proposal_border_trajectory`.
- `screen_normalize/experiments/paper_style.py`: adds labels, color, marker, and line style for reports/figures.
- `tests/test_runner.py`: checks the new method configuration.

The method uses the demo algorithm from:

- `screen_normalize/algorithms/proposal_demo.py`

## Smoke Run

Command:

```powershell
uv run python scripts\run_batch.py --videos inputs\scrolling\scrolling_01.mp4 --methods proposal_border --metrics geometry temporal --run-dir runs\proposal_border_mainchain_smoke
```

Status: `ok`

Standard method outputs:

- `runs/proposal_border_mainchain_smoke/scrolling/scrolling_01/proposal_border/normalized.mp4`
- `runs/proposal_border_mainchain_smoke/scrolling/scrolling_01/proposal_border/estimated_corners.csv`
- `runs/proposal_border_mainchain_smoke/scrolling/scrolling_01/proposal_border/debug.csv`
- `runs/proposal_border_mainchain_smoke/scrolling/scrolling_01/proposal_border/geometry.json`
- `runs/proposal_border_mainchain_smoke/scrolling/scrolling_01/proposal_border/temporal.json`
- `runs/proposal_border_mainchain_smoke/index.html`

Smoke metrics on `scrolling_01`:

- Geometry status: `ok`
- Corner RMSE p50: 3.25 px
- IoU p50: 0.996
- Temporal status: `ok`
- Translation p50: 0.75 px/frame
- Debug reasons: `initial` = 1, `edge_accept` = 298

## Verification

```powershell
uv run pytest
```

Result: 26 passed.

## Notes

`proposal_border` is now part of the main runnable method set. It should be treated as a new method until the full five-category benchmark is rerun. Only after that should the paper decide whether to rename it as the final proposed method or keep it as a separate comparison.
