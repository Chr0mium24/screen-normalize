# Proposal Deliverable - 2026-06-22

本文件夹是课程大作业 Proposal 交付草稿，方向为：**面向真实场景拍屏视频恢复的屏幕捕获矫正与时域稳定化**。

## 文件

- `proposal_content.md`：当前主稿。先审这个文件，再决定是否导出 PPT/Word。
- `Proposal_ID_en.md` / `Proposal_ID_en.pdf`：英文一页 proposal 试版，`ID` 需替换为正式 group number。
- `Proposal_ID_zh.md` / `Proposal_ID_zh.pdf`：中文一页 proposal 试版，`ID` 需替换为正式 group number。
- `proposal_pdf_style.css`：中英文一页 proposal PDF 共用样式。
- `proposal_presentation.pptx`：早期生成稿，暂不作为当前主稿。
- `proposal_report.docx`：早期生成稿，暂不作为当前主稿。
- `proposal_report.md`：早期报告源文本。
- `proposal_presentation_outline.md`：早期 PPT 结构源文本。
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

## 定位

当前先固定 Proposal 内容，不直接继续改 PPT/Word。`proposal_content.md` 已按参考示例重写为三页 Proposal 逻辑：动机、目标方法、数据与初步结果。当前叙事把项目定位为真实拍屏视频恢复的前置几何链路：先做屏幕捕获矫正、透视归一化和时域稳定，后续可接 video demoiréing、OCR 或归档。主稿已加入 LCDMoire、UHDM、Video Demoiréing 和 RawVDemoiré 等公开数据集作为背景论据，强调它们多服务于受控、裁剪、配对或已对齐的恢复任务，而本项目补的是完整拍屏视频进入恢复模型之前的几何归一化环节。主稿也写明 Final 阶段计划整理 5 类自采拍屏短视频、每类 10 段、每段约 5 秒，并补充 residual translation、rotation、scale delta、tracker accept ratio、RANSAC inliers 和 feature coverage 等评价指标。数据部分只使用能追溯到具体运行目录的同视频消融，不用不清楚的数字，也不把尚未完成的 50 段测试集写成已完成结果。

新增 SVG 资产统一使用 1600x900 画布、warm white 背景、Georgia 标题、深灰正文、绿色主强调和细线表格/卡片风格，方便直接放入 proposal PPT。
