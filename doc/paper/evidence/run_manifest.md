# Final Experiment Run Manifest

Generated on 2026-06-22. All commands were executed with `uv run` from the repository root on branch `final-experiments`.

## Main Runs

```bash
uv run scripts/normalize_screen.py inputs/静止网页.mp4 --tracker reference --reference-profile low-latency --write-tracker-debug --write-trajectory-debug --run-name main_static_page
uv run scripts/analyze_stability.py runs/main_static_page/静止网页_normalized.mp4 --run-name analyze_main_static_page

uv run scripts/normalize_screen.py inputs/滚动网页.mp4 --tracker reference --reference-profile dynamic --write-tracker-debug --write-trajectory-debug --run-name main_dynamic_scroll_page
uv run scripts/analyze_stability.py runs/main_dynamic_scroll_page/滚动网页_normalized.mp4 --run-name analyze_main_dynamic_scroll_page

uv run scripts/normalize_screen.py inputs/运动视频.mp4 --tracker reference --reference-profile dynamic --write-tracker-debug --write-trajectory-debug --run-name main_dynamic_screen_video
uv run scripts/analyze_stability.py runs/main_dynamic_screen_video/运动视频_normalized.mp4 --run-name analyze_main_dynamic_screen_video

uv run scripts/normalize_screen.py inputs/testmoire.mp4 --tracker reference --reference-profile dynamic --write-tracker-debug --write-trajectory-debug --run-name main_dynamic_testmoire
uv run scripts/analyze_stability.py runs/main_dynamic_testmoire/testmoire_normalized.mp4 --run-name analyze_main_dynamic_testmoire

uv run scripts/normalize_screen.py inputs/VID20260621024117.mp4 --tracker reference --reference-profile low-latency --write-tracker-debug --write-trajectory-debug --run-name main_vid_024117
uv run scripts/analyze_stability.py runs/main_vid_024117/VID20260621024117_normalized.mp4 --run-name analyze_main_vid_024117

uv run scripts/normalize_screen.py inputs/VID20260621031719.mp4 --tracker reference --reference-profile dynamic --write-tracker-debug --write-trajectory-debug --run-name main_dynamic_vid_031719
uv run scripts/analyze_stability.py runs/main_dynamic_vid_031719/VID20260621031719_normalized.mp4 --run-name analyze_main_dynamic_vid_031719
```

## Ablation Runs

```bash
uv run scripts/normalize_screen.py inputs/静止网页.mp4 --tracker detect --write-tracker-debug --write-trajectory-debug --run-name ablation_static_detect
uv run scripts/analyze_stability.py runs/ablation_static_detect/静止网页_normalized.mp4 --run-name analyze_ablation_static_detect

uv run scripts/normalize_screen.py inputs/静止网页.mp4 --tracker flow --write-tracker-debug --write-trajectory-debug --run-name ablation_static_flow
uv run scripts/analyze_stability.py runs/ablation_static_flow/静止网页_normalized.mp4 --run-name analyze_ablation_static_flow

uv run scripts/normalize_screen.py inputs/静止网页.mp4 --tracker reference --reference-profile low-latency --reference-align --reference-motion affine --write-tracker-debug --write-trajectory-debug --write-align-debug --run-name ablation_static_reference_align
uv run scripts/analyze_stability.py runs/ablation_static_reference_align/静止网页_normalized.mp4 --run-name analyze_ablation_static_reference_align

uv run scripts/normalize_screen.py inputs/滚动网页.mp4 --tracker detect --write-tracker-debug --write-trajectory-debug --run-name ablation_scroll_detect
uv run scripts/analyze_stability.py runs/ablation_scroll_detect/滚动网页_normalized.mp4 --run-name analyze_ablation_scroll_detect

uv run scripts/normalize_screen.py inputs/滚动网页.mp4 --tracker flow --write-tracker-debug --write-trajectory-debug --run-name ablation_scroll_flow
uv run scripts/analyze_stability.py runs/ablation_scroll_flow/滚动网页_normalized.mp4 --run-name analyze_ablation_scroll_flow

uv run scripts/normalize_screen.py inputs/滚动网页.mp4 --tracker reference --reference-profile dynamic --reference-align --reference-motion affine --write-tracker-debug --write-trajectory-debug --write-align-debug --run-name ablation_scroll_reference_align
uv run scripts/analyze_stability.py runs/ablation_scroll_reference_align/滚动网页_normalized.mp4 --run-name analyze_ablation_scroll_reference_align

uv run scripts/normalize_screen.py inputs/运动视频.mp4 --tracker detect --write-tracker-debug --write-trajectory-debug --run-name ablation_screenvideo_detect
uv run scripts/analyze_stability.py runs/ablation_screenvideo_detect/运动视频_normalized.mp4 --run-name analyze_ablation_screenvideo_detect

uv run scripts/normalize_screen.py inputs/运动视频.mp4 --tracker flow --write-tracker-debug --write-trajectory-debug --run-name ablation_screenvideo_flow
uv run scripts/analyze_stability.py runs/ablation_screenvideo_flow/运动视频_normalized.mp4 --run-name analyze_ablation_screenvideo_flow

uv run scripts/normalize_screen.py inputs/运动视频.mp4 --tracker reference --reference-profile dynamic --reference-align --reference-motion affine --write-tracker-debug --write-trajectory-debug --write-align-debug --run-name ablation_screenvideo_reference_align
uv run scripts/analyze_stability.py runs/ablation_screenvideo_reference_align/运动视频_normalized.mp4 --run-name analyze_ablation_screenvideo_reference_align
```

## Evidence Files

Each normalization run contains:

- `<input>_normalized.mp4`
- `tracker_debug.csv`
- `trajectory_debug.csv`
- `align_debug.csv` for residual-alignment ablations

Each analysis run contains:

- `stability_metrics.csv`
- `stability_summary.json`

The committed summary table is `experiment_summary.csv`.
