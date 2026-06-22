# Proposal Presentation 图片与内容清单

这份清单对应 `proposal_presentation.tex`。主讲部分设计为 6 页，约 3 分钟；另外有 2 页 QA 备用页。

## 编译命令

推荐命令：

```bash
cd deliverables/proposal_20260622
latexmk -pdf proposal_presentation.tex
```

备用命令：

```bash
cd deliverables/proposal_20260622
pdflatex proposal_presentation.tex
pdflatex proposal_presentation.tex
```

模板内置了缺图占位框，所以即使最终图片还没准备齐，也可以先编译检查版式。

## 必须准备的图片

| 页码 | LaTeX 中的文件路径 | 当前状态 | 需要提供或确认的内容 |
| --- | --- | --- | --- |
| 1. Title and Topic | `assets/comparison_1s.jpg` | 已有本地候选图 | 一张清晰的 before/after 对比图：左侧是手机原始拍屏画面，右侧是拉正后的屏幕坐标输出。优先使用项目真实帧。 |
| 2. Motivation and Gap | `assets/screen_corners_overlay_4s.jpg` | 已有本地候选图 | 一张带屏幕四边形标注的原始帧。画面最好能明显看到屏幕外背景、透视倾斜和物理屏幕边界。 |
| 4. Core Idea and Method | `assets/tracking_visualization.png` | 当前缺少这个精确格式 | 一张紧凑的方法示意图，区分“屏幕边框跟踪”和“屏幕内部内容运动”。可以把已有的 `assets/tracking_visualization.svg` 导出成 PNG，也可以把 LaTeX 路径改成 PDF/PNG 版本。 |

## 可选增强图片

| 建议文件名 | 用途 | 内容要求 |
| --- | --- | --- |
| `assets/problem_examples_montage.png` | 替换或补充第 2 页 | 2x2 问题样例拼图：弱边框/PPT、滚动页面、反光或眩光、摩尔纹难例。每个小图加一个短标签。 |
| `assets/self_collected_dataset_plan.png` | 补充第 5 页 | 展示 5 类计划场景、每类 10 段视频的数据集设计。已有 SVG 可转换成图片；当前 LaTeX 里也已有文字版说明。 |
| `assets/proposal_timeline.png` | 补充第 6 页 | 从 6 月 22 日到 7 月 15 日的简短时间轴。当前第 6 页已有表格，所以这张图不是必须。 |

## 需要确认的文字内容

| 项目 | 当前草稿 | 需要确认 |
| --- | --- | --- |
| 标题 | `Screen Capture Rectification and Temporal Stabilization for Real-world Captured-screen Videos` | 是否就是最终放在 slide 和 proposal 里的英文标题。 |
| 姓名 | Rongshuo Wen, Bihua Wen, Ruiming Liu | 如果老师要求，是否需要在 title slide 上加入学号。 |
| 数据集计划 | 5 类场景，每类 10 段，每段约 5 秒 | 确认这是“计划采集”的数据集，还是 presentation 时已经能说“已采集”。 |
| 场景类别 | 静态页面、滚动页面、屏幕内视频播放、PPT 或弱边框页面、反光/摩尔纹/部分出画难例 | 确认 PPT/弱边框作为一类，hard cases 作为另一类，和 proposal 保持一致。 |
| 评价指标 | 角点误差、四边形 IoU、长宽比误差；残余平移/旋转/尺度变化；平均梯度幅度；边缘保持指数；2D FFT 主频方向检查 | 确认这些指标都能在后续实现中完成。如果有不稳妥的指标，presentation 前建议删掉或弱化。 |
| 对比方法 | 逐帧检测、内容光流、边框引导跟踪 | 确认 final report 也会围绕这三种方法做对比。 |

## 3 分钟讲稿节奏

如果保持 6 页主讲 slide，可以按下面节奏讲：

| 页码 | 时间 | 核心信息 |
| --- | ---: | --- |
| 1 | 15 秒 | 我们解决真实拍屏视频进入恢复任务前的几何前处理问题。 |
| 2 | 30 秒 | 现有恢复任务常常从已对齐屏幕开始，但真实手机视频包含背景、倾斜、抖动、弱边框、反光、摩尔纹和动态内容。 |
| 3 | 25 秒 | 输入是完整手持拍屏视频；输出是稳定、正视角、保持长宽比且保留真实内容运动的屏幕视频。 |
| 4 | 55 秒 | 方法核心是用物理边框估计屏幕平面，LK 点只做一致性检查；与边框冲突的内部运动视为内容运动并排除。 |
| 5 | 60 秒 | 实验计划使用 50 段自采视频，从几何准确性、时域稳定性、信号保持性和 FFT 网格/摩尔纹指标评价。 |
| 6 | 35 秒 | 预期结果是一套经典几何前处理流程，并在 7 月 15 日前完成消融、失败分析和最终交付。 |

## 2 分钟 QA 准备

准备下面几个短回答：

1. 为什么不直接训练去摩尔纹模型？

   本项目解决的是更前面的几何阶段。真实应用中，下游恢复模型仍然需要稳定、裁剪、正视角的屏幕输入。

2. 如何避免把滚动内容误认为相机抖动？

   单应矩阵主要根据物理屏幕边框估计。内部 LK 特征只作为一致性证据，RANSAC 会排除与边框运动冲突的内部运动。

3. 如果屏幕边框很弱或缺失怎么办？

   边框置信度低时系统会重新检测；如果仍然无法恢复，就冻结上一帧有效单应矩阵，并把这些帧作为鲁棒性分析的一部分。

4. 评价如何做到定量？

   人工角点标注衡量几何准确性；残余仿射运动衡量时域稳定性；梯度、边缘和 FFT 指标衡量矫正后的信号保持情况。
