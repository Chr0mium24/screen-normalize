# Proposal Deliverable - 2026-06-22

本文件夹是课程大作业 Proposal 交付草稿，方向为：**面向真实场景拍屏视频恢复的屏幕捕获矫正与时域稳定化**。

## 文件

- `Proposal_ID_en.md` / `Proposal_ID_en.docx` / `Proposal_ID_en.pdf`：英文一页 proposal 正式草稿，`ID` 需替换为正式 group number。
- `Proposal_ID_zh.md` / `Proposal_ID_zh.docx` / `Proposal_ID_zh.pdf`：中文一页 proposal 对照稿，`ID` 需替换为正式 group number。
- `proposal_pdf_style.css`：仅用于导出 PDF 的 A4 打印样式。当前为白底、黑字、单栏正文，不使用卡片、配色块或网页式排版。
- `assets/`：原始帧、角点覆盖图、归一化帧、左右对比图和方法对比图。
- `assets/*.svg`：统一 academic 风格的 proposal 图，包括应用链路、数据集 gap、自采数据计划、before/after 时间条、失败案例、跟踪示意、指标定义和消融表。
- `evidence/best_result_normalized.mp4`：当前最新最好输出视频。
- `evidence/stability_summary.json`：稳定性分析摘要。
- `evidence/stability_metrics.csv`：逐帧稳定性指标。
- `evidence/trajectory_debug.csv`：角点轨迹调试数据。
- `evidence/proposal_ablation_summary.csv`：同一输入视频上的三种方法对比表。

## 当前最好结果

- 运行目录：`runs/proposal_best_geometry_gate/`
- 输出视频：`runs/proposal_best_geometry_gate/VID20260621024117_normalized.mp4`
- 已复制到：`evidence/best_result_normalized.mp4`
- 最后 2 秒稳定性：translation p95 = 0.118 px，rotation p95 = 0.0044 deg，scale delta p95 = 0.000118

## 当前提交稿定位

当前一页 proposal 已按课程模板压缩为正式 Word 文档结构：Names & IDs、Title、Description、Task and goal、Method、Dataset and experiment、Evaluation metrics、Expected results 和 Timeline。PDF 是 A4 一页，白底、黑字、单栏正文，不放装饰性图片或卡片。

项目叙事定位为真实拍屏视频恢复的前置几何链路：先做屏幕捕获矫正、透视归一化和时域稳定，后续可接 video demoiréing、OCR 或归档。公开 demoiréing 数据集只作为相关工作背景，因为它们多服务于受控、裁剪、配对或已对齐的恢复任务；本项目补的是完整拍屏视频进入恢复模型之前的几何归一化环节。提交前还需要把文件名和正文中的 `ID` 替换成正式 group number。

SVG 资产仅保留给后续 proposal PPT 选用，不插入一页 proposal PDF。
