# screen-normalize

把手持拍摄的电脑屏幕视频转换成接近正常录屏的视频。

这是一个数字图像处理课程大作业项目。当前方向确定为：

**基于传统图像处理的拍屏视频几何归一化与稳定化。**

项目不依赖深度学习模型，核心问题也不再放在图像恢复上，而是处理拍屏幕视频里最主要的几何退化：屏幕外背景、透视畸变、手持抖动和逐帧检测误差。

## 项目目标

输入是一段手机或相机拍摄的电脑屏幕视频，画面中通常包含墙面、桌面、屏幕边框、透视变形和轻微手抖。

目标输出是只保留屏幕内容的正常视频：

- 去掉屏幕外的墙面、桌面和边框；
- 把倾斜拍摄的屏幕透视校正成正面视角；
- 保持输出长宽比固定，默认输出 `1920x1080`；
- 减少由于手持拍摄和逐帧角点误差造成的画面晃动；
- 保留屏幕内部真实内容变化，例如播放视频、滚动页面、鼠标移动和字幕。

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
5. 对角点轨迹做时域平滑，减少逐帧检测噪声。

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

当前主流程已经可以作为课程项目的核心实现：

- 有完整可运行脚本 `scripts/normalize_screen.py`；
- 支持自动角点检测，也支持手动角点覆盖；
- 支持 `detect`、`flow`、`reference` 三种角点轨迹来源；
- 推荐的 `reference` 模式用光流、RANSAC 和门控把屏幕平面锁定到参考帧；
- 支持输出 tracker debug CSV，便于解释每帧为什么接受或拒绝更新；
- 支持稳定性分析脚本 `scripts/analyze_stability.py`；
- 每次运行自动写入 `runs/<时间>_<脚本名>/`，便于复现实验和写报告。

还需要在 final 阶段补充：

- 多个输入视频的对比实验；
- 自动角点和手动角点的对比；
- 是否使用参考跟踪、残余对齐、轨迹平滑的消融实验；
- 失败案例分析，例如强反光、屏幕边缘遮挡、画面内容大幅运动。

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
| `--corners "x,y:x,y:x,y:x,y"` | 手动指定四个屏幕角点，覆盖自动检测。 |
| `--crop-left/top/right/bottom` | 透视矫正后按比例裁切输出画面。 |
| `--width`, `--height` | 设置输出分辨率，默认 `1920x1080`。 |
| `--run-name` | 固定本次运行的输出目录名。 |
| `--write-tracker-debug` | 输出每帧跟踪诊断信息。 |

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
- `doc/traditional-geometry-stabilization-references/`：本项目当前传统视觉方向的论文 PDF 和中文索引。
- `doc/stabilization-roadmap.md`：从稳定化目标、失败原因、实验结果到后续路线的详细分析。

## 后续工作

下一步建议按课程交付顺序做：

1. 固定实验集，选择 3-5 个拍屏幕视频作为样例。
2. 对每个样例保存原视频、归一化输出、debug CSV 和稳定性指标。
3. 截图展示自动角点、手动角点、透视矫正前后对比。
4. 做消融实验：逐帧检测、光流跟踪、参考平面跟踪、残余对齐、不同平滑窗口。
5. 在 final report 中把项目完整表述为传统图像处理的几何校正与稳定化流程。
