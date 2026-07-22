# 4.5 频域信号保持 Demo 图数据缺口

日期：2026-07-22

## 结论

现在可以先做一版“一半 demo”的计算图，但只能画 **全局 FFT 保持指标**，还不能画完整的 **Peak Set / MSPS** 图。

现有可用数据在：

```text
runs/20260714_frequency_preservation_demo_scrolling_01/
```

包含：

```text
frequency_preservation_rows.csv
frequency_preservation_summary.csv
```

这两张表已经能支持一版 demo 图：

1. 三种方法的 `log_fft_magnitude_similarity` 条形图。
2. 三种方法的 `high_frequency_energy_ratio` 或 `band_energy_ratio` 接近 1 的对比图。
3. 三种方法的 `orientation_histogram_intersection` 条形图。
4. 4 个采样帧上的逐帧折线或散点图。

这版图可以叫：

```text
Reference-based FFT preservation demo
```

但不能叫完整 MSPS，因为它没有检测、匹配和可视化摩尔纹峰。

## 当前已有 demo 数值

| Method | Frames | FFT sim ↑ | HF ratio ≈1 | Orient hist ↑ | Band ratio ≈1 |
|---|---:|---:|---:|---:|---:|
| frame_wise | 4 | 0.964 | 1.003 | 0.992 | 0.980 |
| optical_flow | 4 | 0.963 | 0.982 | 0.992 | 0.958 |
| proposal_border | 4 | 0.990 | 1.001 | 0.997 | 1.000 |

如果只需要“半 demo”，可以直接用这些数值画一版图，结论写成：

```text
在 scrolling_01 的 4 个标注帧上，proposal_border 相比 frame_wise 和 optical_flow 有更高的 log-FFT 相似度和方向直方图相似度，同时高频能量比与宽频带能量比更接近 1。这说明该方法在几何归一化后更好地保持了已有拍屏频域结构。
```

边界必须写清楚：

```text
该 demo 仍是全局频谱统计，不是 Peak Set/MSPS；它不能证明每一个摩尔纹峰都被逐一保持。
```

## 如果要画 Peak Set / MSPS Demo 图，现在差什么数据

### 1. 差 reference 与 track 的同帧图像对

MSPS 图需要每个采样帧同时有：

```text
reference_warped_frame.png
tracked_output_frame.png
```

当前 CSV 只保存了计算后的指标，没有保存用于画峰检测的中间图像。因此现在不能回画：

```text
reference FFT + detected peaks
tracked FFT + matched peaks
```

虽然原始视频和 normalized video 还在，但需要重新抽帧并保存中间结果。

### 2. 差每帧 transform / homography

Peak Set 图如果要解释“峰为什么移动”，需要知道原始区域到追踪输出的几何变换：

```text
homography_raw_to_track
raw_region_corners
tracked_size
```

没有这个数据，只能比较两个 FFT 峰的位置，不能做旋转、尺度、透视补偿。这样会重新落入“峰轻微移动导致误判”的问题。

### 3. 差峰检测结果表

需要新增一张逐帧峰表：

```text
moire_peaks.csv
```

字段建议：

```text
method,frame,source,peak_id,x,y,radius,angle_deg,energy,width_px,prominence
```

其中 `source` 取：

```text
reference
tracked
```

这张表是画峰点、峰宽圆圈、峰能量大小的基础。

### 4. 差峰匹配结果表

需要新增：

```text
moire_peak_matches.csv
```

字段建议：

```text
method,frame,ref_peak_id,track_peak_id,position_error_px,angle_error_deg,energy_delta_db,width_relative_error,match_cost
```

还要有：

```text
new_peak_count
missing_peak_count
msps
```

否则只能画“检测到哪些峰”，不能画“哪些峰被保持、哪些峰新增或丢失”。

## 最小补数据方案

如果只为了画一版 MSPS demo 图，不需要重新做完整实验。最小方案是：

| 数据 | 最小数量 |
|---|---:|
| clip | 1 个，继续用 `scrolling_01` |
| frames | 4 帧，继续用 `74, 148, 223, 297` |
| methods | 先只画 `proposal_border`，对比可选加 `frame_wise` |
| 每帧图像 | `reference_warped_frame.png` + `tracked_output_frame.png` |
| 每帧变换 | `transform.json`，至少包含 corners 和 output size |
| 输出表 | `moire_peaks.csv` + `moire_peak_matches.csv` + `moire_msps_summary.csv` |

这就是“一半 demo”的下一步：不扩数据集，只在已有 4 个采样帧上补中间图像、峰检测和峰匹配。

## Demo 图建议版式

建议先画 2 行 3 列：

| 面板 | 内容 |
|---|---|
| A | 原始 frame / reference warped crop |
| B | tracked output |
| C | reference FFT，标出 peaks |
| D | tracked FFT，标出 matched peaks 和 new peaks |
| E | 每帧 MSPS 柱状或散点 |
| F | position error、energy delta、width error 三个小指标 |

如果现在不补数据，只用已有 CSV，则图改成 1 行 3 列：

| 面板 | 内容 |
|---|---|
| A | `log_fft_magnitude_similarity` |
| B | `high_frequency_energy_ratio` 与 `band_energy_ratio` |
| C | `orientation_histogram_intersection` |

这版可以立即画，但论文口径只能说是 preliminary FFT preservation demo。

