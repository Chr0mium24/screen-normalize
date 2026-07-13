# Archived Scripts

这些脚本属于新实验流水线建立前的开发、诊断和试验入口，仅用于复查历史结果或提取实现逻辑：

- `analyze_stability.py`：旧版独立时域稳定性分析。
- `evaluate_screen_normalization.py`：旧版四类指标综合入口；其可复用计算位于 `screen_normalize/experiments/evaluation.py`。
- `make_comparison_strip.py`：旧版关键帧对比图生成器。
- `make_manual_demo_strip.py`：旧版人工理想矫正演示生成器。
- `probe_learned_homography.py`：SuperPoint + LightGlue 可行性探针。
- `visualize_line_roll.py`：line-roll 开发诊断入口。
- `dataset/build_formal_dataset.py`：旧版从原始素材切 5 秒正式 clip 的入口；当前四 clip pilot 不直接使用它。
- `annotation/select_corners.py`：旧版 Tk 单帧角点工具；当前标注统一使用浏览器入口。
- `annotation/annotate_corners.py`：旧版 Tk 单视频多帧标注工具。
- `annotation/batch_annotate.py`：旧版 Tk 批量标注工具，依赖旧 `segments/` 数据结构。
- `paper/build_data_requirements_report.py`：旧版数据/标注需求报告生成器，依赖已归档的旧论文计划文档。

它们不属于当前正式执行入口，也不应被新的批处理脚本调用。Git 历史中的 `make_mock_final_figures.py` 使用模拟结果，已删除，不能作为论文图表来源。

旧演示和 line-roll 可视化的配套模块位于 `screen_normalize/archive/`。
