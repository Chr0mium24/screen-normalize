# Current Figure and Table Plan

本文档定义当前重写稿实际使用的图表。它不再保留旧版 7-9 张主图计划；没有信息量或没有进入正文论证的诊断图应留在归档记录中。

统一字体、配色、表格规则和缺失数据处理见 [`visual_style.md`](visual_style.md)。图表中的方法名应使用读者可理解的描述：Frame-level detection、Adjacent-frame tracking、Reference-anchored method；不要在论文主图中暴露代码式方法名或目录名。

## Figure 1: Method Pipeline

**目的：** 说明当前实际实现的参考帧锚定几何归一化流程。

**内容：**
- 输入拍屏帧和初始化四边形。
- 参考平面特征跟踪。
- RANSAC 单应矩阵估计。
- 可靠性门控、保持、修复和平滑。
- 输出正面屏幕画布。

**当前文件：** `doc/current/paper/manuscript/figures/figure_01_pipeline.png`

## Figure 2: Dataset Examples and Annotations

**目的：** 展示五种拍摄条件和人工四角标注目标。

**内容：**
- 静态页面。
- 滚动页面。
- 屏幕内播放视频。
- 弱边框场景。
- 挑战场景。

**当前文件：** `doc/current/paper/manuscript/figures/figure_02_dataset.png`

**使用边界：** 图注只说明样例和标注目标，不把数据集图片包装成主要实验贡献。

## Figure 3: Geometry and Temporal Comparison

**目的：** 支撑主结论：参考帧锚定更平滑，但标注几何更差。

**数据来源：** `doc/archive/paper_results/2026-07-14-annotated-two-per-category/results/main_geometry_temporal/`

**当前文件：** `doc/current/paper/manuscript/figures/figure_03_geometry_comparison.svg`

**必须同时配套的文字解释：**
- 平移变化下降只说明估计轨迹更平滑。
- 角点 RMSE 和 IoU 显示几何正确性没有提升。
- 不能把平滑性解释成屏幕平面正确。

## Figure 4: Category-Level Stress

**目的：** 解释主取舍在哪些场景出现。

**数据来源：** `doc/archive/paper_results/2026-07-14-annotated-two-per-category/results/main_geometry_temporal/`

**当前文件：** `doc/current/paper/manuscript/figures/figure_04_temporal_stability.svg`

**必须同时配套的文字解释：**
- 静态页面和屏幕内播放视频中，参考平面证据较可靠。
- 滚动页面会让内部内容运动污染参考平面估计。
- 弱边框和挑战场景中的低变化可能来自长期保持，而不是成功跟踪。

## Figure 5: Qualitative Examples

**目的：** 用可见输出解释“稳定但错误”的失败模式。

**当前文件：** `doc/current/paper/manuscript/figures/figure_05_qualitative.png`

**使用边界：**
- 只保留能说明偏移、裁切或稳定错误几何的样例。
- 如果样例不清楚，应替换，而不是靠图注解释。
- 不把定性图写成额外性能证明。

## Tables

### Table 1: Dataset Scope

**内容：** 五种拍摄条件、完整数据集 clip 数、正文子集 clip 数、完整数据集帧数。

### Table 2: Main Metrics

**数据来源：** annotated two-per-category main rerun.

**指标：**
- Corner RMSE, px.
- Quadrilateral IoU.
- Translation variation, px/frame.

**报告格式：** median [Q1, Q3].

### Table 3: Ablation Metrics

**数据来源：** annotated two-per-category ablation rerun.

**变体：**
- Full reference-anchored method.
- Without reliability gates.
- Without trajectory smoothing.
- Without offline repair.

**指标：**
- Corner RMSE, px.
- IoU.
- Translation variation, px/frame.

## Excluded From Main Text

- Detail/frequency diagnostic figure.
- Failure/tuning timeline figure.
- Processing speed figure.
- Counts of generated videos, JSON files, or HTML reports.
- Raw parameter lists.
- Tuning smoke-test results.

These can remain in archived engineering documentation, but they should not drive the current manuscript narrative.
