# Proposal Border Ablation

Date: 2026-07-14

## Question

The current manuscript uses `proposal_border` as the Proposed method. This ablation checks the current method's added components on the representative `scrolling_01` clip, where internal page motion is the clearest stress case.

## Scope

Representative clip:

- `inputs/scrolling/scrolling_01.mp4`

Primary ablation run:

- `runs/20260714_proposal_border_ablation_scrolling_01`

Command:

```powershell
uv run python scripts\run_batch.py --videos inputs\scrolling\scrolling_01.mp4 --methods proposal_border proposal_border_lsd proposal_border_hough proposal_border_no_smoothing proposal_border_no_lk proposal_border_no_redetect proposal_border_loose_gates --metrics geometry temporal --run-dir runs\20260714_proposal_border_ablation_scrolling_01
```

Completion:

- Batch status: 1/1 clips `ok`
- Geometry JSON files: 7/7
- Temporal JSON files: 7/7

No-border diagnostic rows use the already completed run:

- `runs/20260714_small_sample_with_proposal_border`

## Results

| Variant | Corner RMSE p50 (px) ↓ | IoU p50 ↑ | Translation p50 (px/frame) ↓ | Runtime (s) | Held frames |
|---|---:|---:|---:|---:|---:|
| Proposed, profile border | 3.253 | 0.996038 | 0.752 | 57.83 | 0 |
| No trajectory filter | 2.932 | 0.996585 | 1.430 | 53.13 | 0 |
| No LK diagnostic | 3.253 | 0.996038 | 0.752 | 16.82 | 0 |
| No redetect fallback | 3.253 | 0.996038 | 0.752 | 55.09 | 0 |
| Loose edge gates | 3.253 | 0.996038 | 0.752 | 52.95 | 0 |
| LSD border detector | 3.604 | 0.995716 | 0.961 | 283.90 | 0 |
| Hough border detector | 27.335 | 0.974200 | 0.897 | 154.41 | 0 |
| No physical border: adjacent optical flow | 76.114 | 0.916022 | 2.205 | n/a | n/a |
| No physical border: reference LK/RANSAC | 643.949 | 0.520994 | 4.579 | n/a | n/a |

Reason counts for the rerun variants:

| Variant | Accepted frames | Held frames | Reason counts |
|---|---:|---:|---|
| Proposed, profile border | 299 | 0 | `initial=1`, `edge_accept=298` |
| No trajectory filter | 299 | 0 | `initial=1`, `edge_accept=298` |
| No LK diagnostic | 299 | 0 | `initial=1`, `edge_accept=298` |
| No redetect fallback | 299 | 0 | `initial=1`, `edge_accept=298` |
| Loose edge gates | 299 | 0 | `initial=1`, `edge_accept=298` |
| LSD border detector | 299 | 0 | `initial=1`, `edge_accept=298` |
| Hough border detector | 299 | 0 | `initial=1`, `edge_accept=296`, `edge_accept_lk_conflict=2` |

## Interpretation

The decisive ablation is the physical-border cue. Without physical border evidence, adjacent-frame optical flow has 76.114 px RMSE and the reference LK/RANSAC tracker has 643.949 px RMSE on `scrolling_01`. The full profile-border method is 3.253 px. This supports the current paper's central claim that screen-boundary evidence is necessary when internal page motion is coherent but not equal to physical screen motion.

The border-observation variants show why profile observations are the default. LSD is close geometrically but much slower. Hough is smoother than flow-only but much less accurate than profile or LSD.

The remaining module ablations are mostly inactive on this clip because the border evidence succeeds on every frame. Removing LK diagnostics, redetect fallback, or tightening/loosening gates does not change geometry. Removing the trajectory filter slightly lowers RMSE on annotated frames but increases translation variation, which supports keeping the filter for temporal stability.
