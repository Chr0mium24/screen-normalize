# Retained Local Runs

`runs/` 是本地实验产物目录，不进入 Git。为保证论文数字可追溯，流水线重构前的最小证据集保留在 `runs/archive/pre_pipeline/`。

## Main Methods

- `archive/pre_pipeline/main_static_page`
- `archive/pre_pipeline/main_dynamic_scroll_page`
- `archive/pre_pipeline/main_dynamic_screen_video`
- `archive/pre_pipeline/main_dynamic_testmoire`
- `archive/pre_pipeline/main_vid_024117`
- `archive/pre_pipeline/main_dynamic_vid_031719`

## Ablations

- `archive/pre_pipeline/ablation_static_{detect,flow,reference_align}`
- `archive/pre_pipeline/ablation_scroll_{detect,flow,reference_align}`
- `archive/pre_pipeline/ablation_screenvideo_{detect,flow,reference_align}`

## Analysis and Visual Evidence

- `archive/pre_pipeline/` 下上述 main 和 ablation run 对应的 `analyze_*` 目录
- `archive/pre_pipeline/final_visuals`
- `archive/pre_pipeline/eval_smoke_static`
- `archive/pre_pipeline/eval_smoke_self_consistency`

完整命令见 `run_manifest.md`，已汇总数字见 `experiment_summary.csv`。其他早期 `debug_*`、`verify_*`、`inspect_*` 和未被报告引用的试验性 run 已删除。

## Current Four-Clip Ablation

- Run：`runs/20260713_ablation`
- 范围：static、scrolling、screen_video、hard 各一个代表 clip；weak_border 排除。
- 新运行：`no_reliability_gates`、`no_trajectory_smoothing`、`no_offline_repair`。
- 复用：历史 `proposed` 视频与角点轨迹；指标按当前代码重算并排除初始化帧。
- 汇总：`doc/paper/results/ablation/`。
- 限制：仅描述性 n=4；offline repair 未被当前四个 clip 有效触发。

## Current Full First-Pass Archives

- Main run：`runs/20260714_full_pipeline_first_pass`
- Ablation run：`runs/20260714_full_ablation_first_pass`
- 汇总表、论文图和证据说明已展开保存在 `doc/paper/results/`、`doc/paper/evidence/` 和 `doc/paper/manuscript/figures/`。
- 轻量 raw metrics archive：`doc/paper/results/raw_run_archives/first_pass_text_metrics_20260714.zip`。
- Archive 包含两个完整 run 的 CSV、JSON、MD 和 SVG 文件，并附带 `MANIFEST.csv` 记录每个成员文件的大小和 SHA-256。
- Archive 明确排除 MP4、JPG、PNG 和 HTML 本地报告；两次完整 run 的未压缩媒体产物约 3.7 GB，仍保留在本地 `runs/`。
