# Final Experiment Run Manifest

Generated on 2026-06-22. All commands were executed with `uv run` from the repository root on branch `final-experiments`.

以下命令按执行时的原始路径保留，不能当作当前流水线命令。2026-07-12 整理后，输入视频位于 `inputs/archive/pilot/`，结果位于 `runs/archive/pre_pipeline/`，旧稳定性脚本位于 `scripts/archive/analyze_stability.py`。

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

## 2026-07-13 Current Ablation Run

Current scope uses one representative clip from each included category and excludes `weak_border`: `static_02_000`, `scrolling_03_000`, `screen_video_03_000`, and `hard_01`.

Three new variants were run. Historical `proposed` outputs were reused and only their metrics were recomputed with the current evaluator so geometry consistently excludes the initialization frame.

```bash
uv run python scripts/run_batch.py --videos inputs/static/segments/static_02/static_02_000.mp4 inputs/scrolling/segments/scrolling_03/scrolling_03_000.mp4 inputs/screen_video/segments/screen_video_03/screen_video_03_000.mp4 inputs/hard/hard_01.mp4 --methods no_reliability_gates no_trajectory_smoothing no_offline_repair --metrics geometry temporal detail frequency --run-dir runs/20260713_ablation
uv run python scripts/paper/ablation/stage_ablation_full.py
uv run python scripts/run_batch.py --videos inputs/static/segments/static_02/static_02_000.mp4 inputs/scrolling/segments/scrolling_03/scrolling_03_000.mp4 inputs/screen_video/segments/screen_video_03/screen_video_03_000.mp4 inputs/hard/hard_01.mp4 --methods proposed --metrics geometry temporal detail frequency --run-dir runs/20260713_ablation --reuse-outputs
uv run python scripts/paper/ablation/summarize_ablation.py runs/20260713_ablation --output-dir doc/paper/results/ablation --paper-dir doc/paper
```

Evidence is stored under `doc/paper/results/ablation/`, including the clip metrics, summary table, quality report, video-integrity table, and HTML report.

Result boundary: 16/16 method outputs and 64/64 metric JSON files are complete, but this is a four-clip descriptive pilot. The offline-repair path was not exercised by an interior rejected interval, so that module's contribution is inconclusive.
