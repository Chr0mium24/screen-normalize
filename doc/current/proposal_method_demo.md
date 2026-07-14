# Proposal Method Demo

Date: 2026-07-14

## Purpose

This demo implements a small, runnable version of the method described in the original proposal:

- estimate the screen quadrilateral mainly from physical screen borders;
- use inner Lucas-Kanade optical-flow features only as a consistency check;
- re-detect the border when edge evidence fails;
- freeze the last valid quadrilateral when neither border tracking nor re-detection recovers;
- warp the video into a fixed front-facing screen canvas.

This is a demonstration path, not the formal method used by the current paper experiments.

## Implementation

Files:

- `screen_normalize/algorithms/proposal_demo.py`
- `scripts/demo_proposal_method.py`
- `tests/test_proposal_demo.py`

Main flow:

1. Initialize the first-frame screen quadrilateral from `--corners`, frame-0 annotation CSV, or automatic detection.
2. For each later frame, sample normal gradients around the predicted four screen edges.
3. Fit four physical edge lines and intersect them into a border-derived quadrilateral.
4. Accept the border quadrilateral if edge confidence, quadrilateral validity, and geometry-step gates pass.
5. Independently run pyramidal LK and RANSAC on inner screen features only to label agreement or content-motion conflict.
6. If border evidence fails, try automatic screen re-detection.
7. If recovery fails, hold the last valid quadrilateral.
8. Smooth the accepted/held trajectory and render the normalized video.

## Smoke Run

Command:

```powershell
uv run python scripts\demo_proposal_method.py inputs\static\static_01.mp4 --max-frames 120 --run-name proposal_demo_static_01 --width 960 --height 540
```

Outputs:

- `runs/proposal_demo_static_01/static_01_normalized.mp4`
- `runs/proposal_demo_static_01/proposal_overlay.mp4`
- `runs/proposal_demo_static_01/proposal_debug.csv`
- `runs/proposal_demo_static_01/raw_corners.csv`
- `runs/proposal_demo_static_01/smoothed_corners.csv`
- `runs/proposal_demo_static_01/summary.json`

Summary:

- Frames processed: 120
- Accepted frames: 120
- Accepted updates after initialization: 119
- Held frames: 0
- Reasons: `initial` = 1, `edge_accept` = 119

Interpretation:

The demo runs end-to-end on a real static-page clip and shows that border evidence can drive every update in this easy case. This is only a smoke result. It does not establish that the border-guided proposal method outperforms the current reference-anchored method, and it should not be reported as a formal experimental result without rerunning the annotated benchmark.

## Verification

```powershell
uv run pytest tests/test_boundary.py tests/test_proposal_demo.py
```

Result: 4 passed.
