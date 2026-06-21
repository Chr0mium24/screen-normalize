# Proposal Deliverable - 2026-06-22

本文件夹是课程大作业 Proposal 交付草稿，方向为：**基于传统图像处理的拍屏视频几何归一化与稳定化**。

## 文件

- `proposal_presentation.pptx`：按 Example Proposal 结构整理的 6 页 PPT。
- `proposal_report.docx`：按 Proposal 报告模板字段整理的中文报告。
- `proposal_report.md`：报告源文本，便于继续修改。
- `proposal_presentation_outline.md`：PPT 结构源文本。
- `assets/`：原始帧、归一化帧和左右对比图。
- `evidence/best_result_normalized.mp4`：当前最新最好输出视频。
- `evidence/stability_summary.json`：稳定性分析摘要。
- `evidence/stability_metrics.csv`：逐帧稳定性指标。
- `evidence/trajectory_debug.csv`：角点轨迹调试数据。

## 当前最好结果

- 运行目录：`runs/proposal_best_geometry_gate/`
- 输出视频：`runs/proposal_best_geometry_gate/VID20260621024117_normalized.mp4`
- 已复制到：`evidence/best_result_normalized.mp4`
- 最后 2 秒稳定性：translation p95 = 0.118 px，rotation p95 = 0.0044 deg，scale delta p95 = 0.000118

## 定位

这套材料适合作为 Proposal：问题边界明确、传统视觉方法路线明确、已有初步结果和可复现实验命令。作为 Final PRO+ 还偏薄，后续需要补足多视频实验、消融对比、失败案例和更完整的结果讨论。
