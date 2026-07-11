# Retained Local Runs

`runs/` 是本地实验产物目录，不进入 Git。为保证论文数字可追溯，当前仅保留以下结果。

## Main Methods

- `main_static_page`
- `main_dynamic_scroll_page`
- `main_dynamic_screen_video`
- `main_dynamic_testmoire`
- `main_vid_024117`
- `main_dynamic_vid_031719`

## Ablations

- `ablation_static_{detect,flow,reference_align}`
- `ablation_scroll_{detect,flow,reference_align}`
- `ablation_screenvideo_{detect,flow,reference_align}`

## Analysis and Visual Evidence

- 上述 main 和 ablation run 对应的 `analyze_*` 目录
- `final_visuals`
- `eval_smoke_static`
- `eval_smoke_self_consistency`

完整命令见 `run_manifest.md`，已汇总数字见 `experiment_summary.csv`。其他早期 `debug_*`、`verify_*`、`inspect_*` 和未被报告引用的试验性 run 已删除。
