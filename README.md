# screen-normalize

把手持拍摄的电脑屏幕视频转换成接近正常录屏的视频，并作为后续拍屏去摩尔纹、颜色校正和细节恢复的前置几何链路。

这是一个数字图像处理课程大作业项目。当前方向确定为：

**面向真实场景拍屏视频恢复的屏幕捕获矫正与时域稳定化。**

当前可运行实现以传统几何方法为主，重点补足现有拍屏恢复论文在真实应用端常常默认或简化的前处理部分：

```text
真实手持拍屏视频
  -> 屏幕区域检测
  -> 透视矫正
  -> 屏幕平面跟踪
  -> 时域稳定
  -> 接近录屏视角的屏幕视频
  -> 后续可接视频去摩尔纹 / 颜色校正 / 细节恢复
```

也就是说，本项目不直接做去摩尔纹或画质恢复，而是先把真实拍摄场景中的屏幕内容定位、拉正并稳定。完整叙事见 `doc/application-pipeline-story.md`，项目取舍见 `doc/project-upgrade-decision.md`。SuperPoint + LightGlue 等学习式特征匹配只作为可选探针或对照实验，不再作为主线必做项。

## 项目目标

输入是一段手机或相机拍摄的电脑屏幕视频，画面中通常包含墙面、桌面、屏幕边框、透视变形和轻微手抖。

目标输出是只保留屏幕内容、几何上稳定的屏幕视频：

- 去掉屏幕外的墙面、桌面和边框；
- 把倾斜拍摄的屏幕透视校正成正面视角；
- 保持输出长宽比固定，默认输出 `1920x1080`；
- 减少由于手持拍摄和逐帧角点误差造成的画面晃动；
- 保留屏幕内部真实内容变化，例如播放视频、滚动页面、鼠标移动和字幕。

从应用链路看，这个输出可以作为后续 video demoiréing、OCR、归档或人工查看的更稳定输入。

## 方法路线

### 1. 屏幕区域检测

使用传统视觉方法从输入视频中定位屏幕平面：

1. 在首帧上自动检测候选屏幕区域。
2. 根据四边形形状、面积、长宽比和边界位置筛选屏幕轮廓。
3. 将四个角点排序为 `TL,TR,BR,BL`。
4. 如果自动检测失败，可以手动指定四个角点作为兜底。

### 2. 透视归一化

屏幕可以近似看作一个平面，因此用单应变换把拍摄画面中的屏幕映射到固定矩形画布：

```text
原始视频帧
  -> 屏幕四角点
  -> Homography
  -> 固定尺寸正面屏幕画面
```

输出分辨率默认是 `1920x1080`，也可以通过 `--width` 和 `--height` 指定。

### 3. 参考平面跟踪

逐帧重新检测角点容易抖动，所以推荐使用 `reference` 跟踪模式：

1. 用首帧屏幕作为参考平面。
2. 用 Lucas-Kanade 光流跟踪屏幕内部特征点。
3. 用 RANSAC 估计参考平面到当前帧的单应性矩阵。
4. 用几何门控过滤异常更新，例如点数不足、内点比例过低、覆盖范围不足、重投影误差过大、面积或边长突变。
5. 对面积或边长突变的角点观测做离线二次门控。
6. 对被门控拒绝的坏帧用前后可靠帧插值，再对整段角点轨迹做时域平滑，减少逐帧检测噪声。

这个流程的原则是：**屏幕平面运动应该稳定，屏幕内部内容变化不应该拉动屏幕姿态估计。**

### 4. 残余稳定化

透视归一化后仍可能有小幅残余晃动。当前脚本支持可选的参考帧残余对齐：

```bash
uv run scripts/normalize_screen.py inputs/my_screen_video.mp4 \
  --tracker reference \
  --reference-align \
  --reference-motion affine
```

残余对齐只在整段视频的预检结果可靠时启用，避免把播放内容、字幕或动态页面误当成相机运动。

### 5. 频域轨迹分析

本项目的频域部分用于稳定化分析，而不是图像恢复：

- 把角点、平移量、旋转角或尺度变化看作时间序列；
- 分析轨迹中的高频成分，判断哪些是逐帧估计噪声；
- 用低通思想解释为什么稳定化应该保留低频手持运动趋势、抑制高频抖动；
- 在报告中比较稳定前后残余运动的统计指标。

## 当前结论

当前传统主流程已经可以作为课程项目的核心方法：

- 有完整可运行脚本 `scripts/normalize_screen.py`；
- 支持自动角点检测，也支持手动角点覆盖；
- 支持 `detect`、`flow`、`reference` 三种角点轨迹来源；
- 推荐的 `reference` 模式用光流、RANSAC 和门控把屏幕平面锁定到参考帧；
- 支持输出 tracker debug CSV，便于解释每帧为什么接受或拒绝更新；
- 支持稳定性分析脚本 `scripts/analyze_stability.py`；
- 每次运行自动写入 `runs/<时间>_<脚本名>/`，便于复现实验和写报告。

为了让 Final 不只是工程 demo，后续重点应该补齐应用链路和实验可信度：

- 多个真实输入视频的场景覆盖，而不是简单堆数量；
- 同一输入上的消融实验：逐帧检测、普通光流、参考平面跟踪、残余对齐、轨迹平滑；
- 屏幕四角点、透视矫正前后、稳定前后的关键帧可视化；
- 可选的合成或人工标注样例，用来提供角点和 homography 的近似真值评价；
- 失败案例分析，例如强反光、屏幕边缘遮挡、画面内容大幅运动。

`scripts/probe_learned_homography.py` 中的 SuperPoint + LightGlue 探针可以保留为可选对照或 future work，用来说明现代特征匹配在拍屏 homography 估计上的可行性和局限；主方法仍然是当前的 LK + RANSAC 参考平面跟踪。

## Final 实验材料

Final 阶段的实验规划、报告和提交材料已整理到：

- `doc/final-experiment-plan.md`：实验问题、输入视频、消融矩阵和报告结构；
- `deliverables/final_20260622/final_report.md`：英文 final report 初稿；
- `deliverables/final_20260622/experiment_summary.csv`：可追溯的实验指标表；
- `deliverables/final_20260622/run_manifest.md`：每个 run 对应的执行命令；
- `deliverables/final_20260622/final_presentation_outline.md`：final presentation 结构。

本机还生成了 `runs/final_visuals/`，包含报告/PPT 可用的 input/output 关键帧截图。`runs/` 和视频文件默认不进 git，但 run 名已写入 manifest，便于复现。

## 环境

本项目使用 `uv` 管理 Python 运行环境。脚本顶部已经写了依赖声明，直接用 `uv run` 执行即可。

```bash
uv run scripts/normalize_screen.py --help
```

还需要本机安装 `ffmpeg`，用于把处理后的帧重新编码成视频。

## 快速开始

把输入视频放到 `inputs/` 目录，例如：

```text
inputs/my_screen_video.mp4
```

推荐先用静态屏幕配置运行：

```bash
uv run scripts/normalize_screen.py inputs/my_screen_video.mp4 \
  --tracker reference \
  --reference-profile low-latency
```

输出文件会写到：

```text
runs/<时间>_normalize_screen/my_screen_video_normalized.mp4
```

如果希望固定输出目录名，使用 `--run-name`：

```bash
uv run scripts/normalize_screen.py inputs/my_screen_video.mp4 \
  --tracker reference \
  --reference-profile low-latency \
  --run-name geometry_test
```

## 常用运行方式

自动检测屏幕并透视矫正：

```bash
uv run scripts/normalize_screen.py inputs/my_screen_video.mp4 \
  --tracker reference \
  --reference-profile low-latency
```

如果自动角点不准，手动指定第一帧四个角点，顺序是左上、右上、右下、左下：

```bash
uv run scripts/normalize_screen.py inputs/my_screen_video.mp4 \
  --tracker reference \
  --reference-profile low-latency \
  --corners "124,116:1488,132:1516,850:145,934"
```

如果输出中还留有边框或播放器边缘，可以在透视矫正后裁切：

```bash
uv run scripts/normalize_screen.py inputs/my_screen_video.mp4 \
  --tracker reference \
  --reference-profile low-latency \
  --crop-right 0.02 \
  --crop-bottom 0.04
```

如果需要分析跟踪过程：

```bash
uv run scripts/normalize_screen.py inputs/my_screen_video.mp4 \
  --tracker reference \
  --reference-profile low-latency \
  --write-tracker-debug \
  --run-name debug_tracker
```

这会生成：

```text
runs/debug_tracker/tracker_debug.csv
```

## 关键参数

| 参数 | 作用 |
| --- | --- |
| `--tracker reference` | 推荐模式。把屏幕平面锁定到首帧参考平面，再用光流和 RANSAC 跟踪。 |
| `--reference-profile low-latency` | 适合静态或近静态屏幕内容，减少平滑滞后。 |
| `--reference-profile dynamic` | 适合内部内容变化更大的实验输入。 |
| `--reference-align` | 在透视归一化后做可选残余对齐。 |
| `--reference-motion affine` | 残余对齐使用仿射模型，通常比再次估计单应更稳。 |
| `--trajectory-geometry-gate` | 默认开启。离线拒绝面积或边长突变的角点观测，避免局部错角点导致突然缩放。 |
| `--trajectory-interpolate` | 默认开启。对被门控拒绝的角点观测做前后可靠帧插值，再进入轨迹平滑。 |
| `--corners "x,y:x,y:x,y:x,y"` | 手动指定四个屏幕角点，覆盖自动检测。 |
| `--crop-left/top/right/bottom` | 透视矫正后按比例裁切输出画面。 |
| `--width`, `--height` | 设置输出分辨率，默认 `1920x1080`。 |
| `--run-name` | 固定本次运行的输出目录名。 |
| `--write-tracker-debug` | 输出每帧跟踪诊断信息。 |
| `--write-trajectory-debug` | 输出原始、插值后、平滑后的角点轨迹，便于分析坏帧和插值效果。 |

## 稳定性评估

用 `scripts/analyze_stability.py` 分析输出视频中相邻帧的残余运动：

```bash
uv run scripts/analyze_stability.py \
  runs/geometry_test/my_screen_video_normalized.mp4 \
  --run-name analyze_geometry_test
```

它会生成：

```text
runs/analyze_geometry_test/stability_metrics.csv
runs/analyze_geometry_test/stability_summary.json
```

报告里可以重点使用这些指标：

- 残余平移量；
- 残余旋转角；
- 残余尺度变化；
- RANSAC 内点数量和内点比例；
- 最后几秒的稳定性统计。

这些指标不能完全代替主观视觉效果，但可以支持方法对比和消融实验。

## 目录结构

```text
.
├── README.md
├── doc/          # 论文、路线分析和方法笔记
├── inputs/       # 本地输入视频，默认不提交到 git
├── reference/    # 课程 proposal/final 模板和示例
├── runs/         # 每次运行生成的结果，默认不提交到 git
├── scripts/      # 视频处理和分析脚本
└── test/         # 预留测试目录
```

根目录只保留文件夹、`.gitignore` 和 `README.md`。输入视频和实验结果不要散落在根目录。

## 参考材料

- `reference/`：课程 proposal、cover letter、final report 和 presentation 示例。
- `doc/`：当前阅读和保存的相关论文，包括视频稳定、单应性估计、线段检测、消失点和相机路径平滑等方向。
- `doc/project-goal.md`：当前项目题目、边界、成功标准和实验计划。
- `doc/application-pipeline-story.md`：把本项目定位为拍屏视频恢复前置链路的说明，包含与 video demoiréing 论文和 log-homography 视频稳定论文的关系。
- `doc/final-experiment-plan.md`：Final 阶段实验规划，说明当前输入视频、测试矩阵、失败案例和报告结构。
- `doc/project-upgrade-decision.md`：关于主线取舍、实验补强和可选模型探针的决策文档。
- `doc/learned-homography-probe.md`：SuperPoint + LightGlue 作为可选 homography 匹配对照的初步探针结果。
- `doc/traditional-geometry-stabilization-references/`：本项目当前传统视觉方向的论文 PDF 和中文索引。
- `doc/stabilization-roadmap.md`：从稳定化目标、失败原因、实验结果到后续路线的详细分析。

## 后续工作

下一步建议按课程交付顺序做：

1. 固定实验集，选择 3-5 个拍屏幕视频作为样例。
2. 对每个样例保存原视频、归一化输出、debug CSV 和稳定性指标。
3. 截图展示自动角点、手动角点、透视矫正前后对比。
4. 做消融实验：逐帧检测、光流跟踪、参考平面跟踪、残余对齐、不同平滑窗口。
5. 在 final report 中把项目完整表述为真实拍屏视频恢复的前置屏幕捕获矫正与时域稳定链路。
