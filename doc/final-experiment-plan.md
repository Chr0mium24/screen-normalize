# Final 实验规划：屏幕捕获矫正与时域稳定

整理时间：2026-06-22

## 当前输入视频

当前 `inputs/` 中已经有足够启动下一阶段实验的材料：

| 文件 | 分辨率 | 帧率 | 时长 | 帧数 | 角色 |
| --- | ---: | ---: | ---: | ---: | --- |
| `静止网页.mp4` | 1920x1080 | 30 fps | 6.12 s | 184 | 基础成功样例，验证屏幕检测、透视矫正和低抖动输出 |
| `滚动网页.mp4` | 1920x1080 | 30 fps | 5.58 s | 168 | 动态 UI 样例，测试滚动和鼠标等内容运动是否干扰屏幕平面估计 |
| `运动视频.mp4` | 1920x1080 | 30.09 fps | 5.15 s | 155 | 屏幕内部大面积运动样例，测试视频播放内容是否拉动 homography |
| `testmoire.mp4` | 3840x2160 | 30 fps | 7.34 s | 221 | 4K/摩尔纹难例，连接 video demoiréing 前处理叙事 |
| `VID20260621024117.mp4` | 1920x1080 | 60 fps | 5.27 s | 317 | 已有稳定基准样例，用于延续 proposal 初步结果 |
| `VID20260621031719.mp4` | 1920x1080 | 60 fps | 9.64 s | 580 | 已有动态难例，用于验证 reference profile 和残余稳定策略 |

这组视频覆盖了 Final 需要的主要场景：静态、滚动、屏幕内运动、摩尔纹/高分辨率、已有基准和已有动态难例。下一步可以开始实验，但先不要急着批量跑；应先定义清楚每个实验回答什么问题。

## Final 要回答的问题

Final 报告不应只展示“跑出了几个视频”，而要回答下面几个问题：

1. **屏幕捕获矫正是否有效？**  
   原始拍屏视频中有背景、边框和透视倾斜；输出是否能稳定映射到固定 16:9 正面屏幕画布。

2. **参考平面跟踪是否优于逐帧检测和普通光流？**  
   在同一输入上比较 `detect`、`flow`、`reference`，用残余平移、旋转、尺度变化说明主方法是否降低抖动。

3. **动态屏幕内容是否会干扰屏幕平面估计？**  
   在 `滚动网页.mp4`、`运动视频.mp4`、`VID20260621031719.mp4` 上观察内容运动是否导致角点漂移、面积突变或残余晃动升高。

4. **当前系统的失败边界是什么？**  
   在 `testmoire.mp4` 和其他难例中分析摩尔纹、反光、低纹理、角点不可见或屏幕占比变化对检测和跟踪的影响。

5. **它为什么是 video demoiréing/OCR 的前处理？**  
   说明本项目不直接去摩尔纹，而是把真实拍摄视频变成更稳定、更接近屏幕坐标系的输入，为后续恢复模块提供对齐基础。

## 推荐实验矩阵

### 阶段 1：每个视频的主方法可行性

先对每个输入跑推荐主方法：

```bash
uv run scripts/normalize_screen.py inputs/<video>.mp4 \
  --tracker reference \
  --reference-profile low-latency \
  --write-tracker-debug \
  --write-trajectory-debug \
  --run-name main_<video_name>
```

如果屏幕内部运动很强，改用：

```bash
uv run scripts/normalize_screen.py inputs/<video>.mp4 \
  --tracker reference \
  --reference-profile dynamic \
  --write-tracker-debug \
  --write-trajectory-debug \
  --run-name main_dynamic_<video_name>
```

每个视频先判断：

- 自动角点是否成功；
- 是否需要手动 `--corners`；
- 输出是否仍有明显边框，需要 `--crop-*`；
- tracker debug 是否出现大段拒绝、内点骤降或覆盖不足。

### 阶段 2：同视频消融

至少选择 `静止网页.mp4`、`滚动网页.mp4`、`运动视频.mp4` 做消融：

| 方法 | 命令参数 | 目的 |
| --- | --- | --- |
| 逐帧检测 | `--tracker detect` | 展示逐帧角点检测误差导致的抖动 |
| 普通光流 | `--tracker flow` | 展示没有参考平面门控时的漂移风险 |
| 参考平面 | `--tracker reference` | 主方法 |
| 参考平面 + 残余对齐 | `--tracker reference --reference-align --reference-motion affine` | 验证归一化后小幅残余运动是否可进一步降低 |

每个输出都跑：

```bash
uv run scripts/analyze_stability.py runs/<run-name>/<normalized-video>.mp4 \
  --run-name analyze_<run-name>
```

### 阶段 3：难例和失败案例

重点看：

- `testmoire.mp4`：4K、摩尔纹、画面质量和特征匹配稳定性；
- `VID20260621031719.mp4`：屏幕内部动态内容强，验证 `reference-profile dynamic` 和残余对齐策略；
- 自动角点失败的视频：记录手动角点配置，说明系统边界。

难例不要求全部成功。Final 中应该明确写出失败原因，例如：

- 屏幕边框不完整或四角不可见；
- 屏幕内部大面积运动导致特征点集中在动态区域；
- 摩尔纹和压缩纹理影响角点/特征质量；
- 强反光导致局部特征缺失；
- 低纹理白底页面导致 LK 跟踪点不足。

## 要保存的结果

每个实验 run 至少保存：

- 归一化输出视频；
- `tracker_debug.csv`；
- `trajectory_debug.csv`；
- 稳定性分析的 `stability_metrics.csv`；
- 稳定性分析的 `stability_summary.json`；
- 原始帧、角点覆盖图、归一化帧、前后对比图。

报告中每一个数字都必须能追溯到：

```text
输入视频
运行命令
run 目录
分析目录
CSV/JSON 指标
```

## 最终报告结构

建议 Final 报告按下面结构写：

1. **Motivation**  
   真实拍屏视频进入 video demoiréing、OCR 或归档之前，需要先做屏幕捕获矫正和稳定。

2. **Problem Definition**  
   输入完整手持拍屏视频，输出固定比例、正面视角、时域稳定的屏幕内容视频。

3. **Method**  
   屏幕检测、homography 透视归一化、LK reference tracking、RANSAC、几何门控、插值和平滑、残余稳定。

4. **Dataset**  
   说明当前 6 个输入视频的场景、规格和用途。

5. **Experiments**  
   主方法结果、同视频消融、稳定性指标、关键帧对比。

6. **Failure Analysis**  
   摩尔纹、反光、边框不可见、低纹理、动态内容过强等失败原因。

7. **Discussion**  
   说明本项目是后续 video demoiréing/restoration 的前处理，不直接替代去摩尔纹网络。

8. **Conclusion**  
   总结参考平面跟踪和几何门控在真实拍屏视频前处理中的作用。

## 下一步执行目标

下一步不要直接全量批处理。建议按下面顺序推进：

1. 先从 `静止网页.mp4` 跑主方法，确认新输入的自动角点和输出目录没有问题。
2. 再跑 `滚动网页.mp4` 和 `运动视频.mp4`，观察动态内容是否导致 tracker debug 异常。
3. 只在前三个视频可解释后，再跑 `testmoire.mp4` 和两个旧样例。
4. 根据主方法结果，选择 2-3 个视频做完整消融。
5. 最后整理稳定性指标和关键帧，形成 Final report 的实验章节。
