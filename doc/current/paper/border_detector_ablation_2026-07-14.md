# Border Detector Ablation

Date: 2026-07-14

## Question

The rewritten paper uses the border-guided method as Proposed. This ablation tests whether the default profile-based border observation is the right detector choice, compared with LSD and Hough line-segment detectors in the same main experiment pipeline.

## Final Scope

Use `scrolling_01` as the representative ablation clip. This clip is the most relevant stress case because internal page motion can corrupt content-driven geometry, while the proposed method should stay tied to the physical display boundary.

Methods:

- `proposal_border`: default profile edge observations
- `proposal_border_lsd`: LSD line-segment edge observations
- `proposal_border_hough`: Hough line-segment edge observations

Metrics:

- geometry
- temporal

Run directory:

- `runs/20260714_border_detector_ablation_scrolling_01`

Command:

```powershell
uv run python scripts\run_batch.py --videos inputs\scrolling\scrolling_01.mp4 --methods proposal_border proposal_border_lsd proposal_border_hough --metrics geometry temporal --run-dir runs\20260714_border_detector_ablation_scrolling_01
```

Completion:

- Batch status: 1/1 clips `ok`
- Geometry JSON files: 3/3
- Temporal JSON files: 3/3

## Results

| Border observation | Corner RMSE p50 (px) ↓ | IoU p50 ↑ | Translation p50 (px/frame) ↓ | Runtime (s) | Held frames |
|---|---:|---:|---:|---:|---:|
| Profile/default | 3.253 | 0.996038 | 0.752 | 59.21 | 0 |
| LSD segments | 3.604 | 0.995716 | 0.961 | 285.49 | 0 |
| Hough segments | 27.335 | 0.974200 | 0.897 | 159.25 | 0 |

Reason counts:

| Border observation | Accepted frames | Held frames | Reason counts |
|---|---:|---:|---|
| Profile/default | 299 | 0 | `initial=1`, `edge_accept=298` |
| LSD segments | 299 | 0 | `initial=1`, `edge_accept=298` |
| Hough segments | 299 | 0 | `initial=1`, `edge_accept=296`, `edge_accept_lk_conflict=2` |

## Interpretation

The default profile detector is the best choice for the current Proposed method on the representative scrolling clip. LSD is geometrically close but costs about 4.8x more runtime on this clip. Hough is faster than LSD but substantially worse geometrically, suggesting that its line segments are too sparse or unstable for precise screen-edge localization under this capture condition.

This ablation supports keeping profile-based border observations as the manuscript Proposed configuration. It should be reported as a targeted detector ablation, not as a replacement for the ten-clip main result.
