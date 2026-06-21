# 项目目标与实验计划

## 题目

**基于传统图像处理的拍屏视频几何归一化与稳定化**

本项目面向数字图像处理课程大作业。目标不是训练一个图像恢复模型，也不是追求通用的视频增强，而是用传统图像处理和几何视觉方法，把手持拍摄电脑屏幕的视频转换成接近正常录屏观感的视频。

## 问题定义

手机或相机拍摄电脑屏幕时，原始视频通常包含以下问题：

- 屏幕外的墙面、桌面、边框和其他背景；
- 斜拍造成的透视畸变；
- 手持拍摄造成的轻微平移、旋转、尺度和透视晃动；
- 逐帧角点检测误差造成的高频抖动；
- 屏幕内部内容变化，例如播放视频、页面滚动、鼠标移动、字幕和弹窗；
- 强反光、遮挡或低纹理区域造成的局部特征缺失。

本项目把屏幕视为一个近似平面目标。每一帧中，屏幕平面到相机图像之间可以用单应变换描述。核心问题是：**如何在屏幕内部内容可能变化的情况下，稳定估计屏幕平面的几何变换，并抑制逐帧估计误差造成的画面抖动。**

## 输入输出

### 输入

输入是一段拍摄电脑屏幕的视频，放在 `inputs/` 目录下，例如：

```text
inputs/my_screen_video.mp4
```

视频可以包含轻微手抖和屏幕内部内容变化。当前系统允许自动检测失败时手动指定首帧四角点。

### 输出

输出写入 `runs/<时间>_<脚本名>/` 或指定的 `--run-name` 目录，包括：

- 透视归一化后的视频，例如 `my_screen_video_normalized.mp4`；
- 可选的 `tracker_debug.csv`，记录每帧跟踪和门控状态；
- 可选的 `align_debug.csv`，记录残余对齐状态；
- 稳定性分析结果 `stability_metrics.csv` 和 `stability_summary.json`。

输出视频应满足：

- 只保留屏幕内容或尽量减少屏幕外背景；
- 固定输出比例和分辨率，默认 `1920x1080`；
- 屏幕边框、浏览器 UI、页面布局等屏幕固定结构在时间上稳定；
- 屏幕内部真实内容变化被保留，不反向拉动整个屏幕平面。

## 方法流程

当前方法路线固定为纯传统视觉流程：

```text
输入拍屏视频
  -> 首帧屏幕区域检测或手动四角点
  -> 四角点排序
  -> 单应变换透视归一化
  -> LK 光流跟踪参考平面特征点
  -> RANSAC 估计当前帧单应性
  -> 几何门控拒绝异常更新
  -> 角点轨迹时域平滑
  -> 可选残余仿射稳定
  -> 固定尺寸输出视频
  -> 稳定性指标和消融对比
```

各模块职责如下：

1. **屏幕检测**  
   在首帧寻找屏幕候选四边形，结合面积、长宽比、位置和边界合理性筛选。自动检测不可靠时使用 `--corners` 手动兜底。

2. **透视归一化**  
   根据四个屏幕角点估计 homography，把斜拍屏幕映射到固定矩形画布。

3. **参考平面跟踪**  
   使用 Lucas-Kanade 光流跟踪参考帧上的稳定特征点，用 RANSAC 估计参考平面到当前帧的单应性。

4. **异常帧门控**  
   根据内点数量、内点比例、重投影误差、特征覆盖范围、面积变化和边长变化拒绝不可信更新。

5. **轨迹平滑**  
   对角点或运动参数序列做时域平滑，降低高频估计噪声。报告中可以把这部分解释为运动轨迹低通滤波。

6. **残余稳定化**  
   在透视归一化后，可选地估计相对参考帧的小幅残余仿射运动。该模块只在整段视频预检可靠时启用，避免动态内容误导稳定化。

7. **评估与可视化**  
   用 `scripts/analyze_stability.py` 统计相邻帧残余平移、旋转和尺度变化，并结合截图、视频对比和 debug CSV 分析结果。

## 不做什么

为避免项目发散，以下内容不作为本项目目标：

- 不训练深度学习模型；
- 不使用分割模型或画质恢复模型；
- 不做屏幕内容画质恢复；
- 不做屏幕内容语义理解；
- 不恢复被反光、遮挡或过曝区域破坏的真实内容；
- 不追求任意复杂场景下完全自动和完全鲁棒；
- 不让文字、字幕、播放器画面等动态内容逐帧决定屏幕姿态；
- 不把逐帧线段检测得到的旋转直接作为主稳定信号。

反光只作为几何估计中的干扰因素处理。可选策略是检测高亮饱和区域并避免其参与特征点选择或跟踪，但不尝试视觉修复反光区域。

## 成功标准

最终结果用主观视觉效果和量化指标共同判断。

### 视觉标准

- 输出画面基本没有墙面、桌面和屏幕外背景；
- 屏幕被拉正为固定比例，整体接近录屏视角；
- 屏幕固定结构不出现明显高频抖动；
- 画面没有由于逐帧角点误差造成的抽搐、缩放或透视变形；
- 屏幕内部播放视频、滚动页面、鼠标移动等内容可以自然变化。

### 量化标准

对不同方法输出运行稳定性分析，比较：

- 相邻帧残余平移量；
- 相邻帧残余旋转角；
- 相邻帧尺度变化；
- 最后若干秒的稳定性统计；
- RANSAC 内点数量和内点比例；
- 跟踪点覆盖范围和异常帧拒绝原因。

期望结果是：相较于逐帧检测或直接光流跟踪，参考平面跟踪和轨迹平滑能降低残余运动指标，并让视频观感更接近录屏。

## 实验设计

### 数据集

选取 3-5 个本地拍屏视频作为实验样例，覆盖不同情况：

- 静态桌面或文件浏览器；
- 页面滚动或鼠标移动；
- 屏幕内部播放视频；
- 轻微反光或边缘遮挡；
- 自动角点检测成功和失败的样例。

输入视频放在 `inputs/`，实验输出统一保存在 `runs/`。

### 主实验

对每个输入视频运行推荐配置：

```bash
uv run scripts/normalize_screen.py inputs/my_screen_video.mp4 \
  --tracker reference \
  --reference-profile low-latency \
  --write-tracker-debug \
  --run-name main_my_screen_video
```

对于屏幕内部动态内容更强的视频，可使用：

```bash
uv run scripts/normalize_screen.py inputs/my_screen_video.mp4 \
  --tracker reference \
  --reference-profile dynamic \
  --write-tracker-debug \
  --run-name main_dynamic_my_screen_video
```

如果自动角点不可靠，加入 `--corners` 手动指定首帧四角点。

### 消融实验

至少比较以下方法：

1. **逐帧检测**：`--tracker detect`  
   用来展示逐帧角点估计容易抖动。

2. **普通光流跟踪**：`--tracker flow`  
   用来展示没有参考平面门控时的漂移风险。

3. **参考平面跟踪**：`--tracker reference`  
   作为主方法。

4. **不同轨迹平滑窗口**：调整 `--median-window` 和 `--trajectory-window`  
   用来分析平滑强度和延迟之间的权衡。

5. **残余仿射稳定**：加入 `--reference-align --reference-motion affine`  
   用来验证归一化后的残余小运动是否可以进一步降低。

6. **手动角点兜底**：加入 `--corners`  
   用来说明自动检测失败时系统仍可完成几何归一化。

### 评估命令

对每个输出运行：

```bash
uv run scripts/analyze_stability.py runs/<run-name>/<video> \
  --run-name analyze_<run-name>
```

报告中展示：

- 原视频和输出视频关键帧对比；
- 不同方法输出视频的同帧截图；
- 稳定性指标表格；
- tracker debug 中的接受/拒绝帧统计；
- 失败案例和原因分析。

## 参考文献如何对应方法

参考文献集中在 `doc/traditional-geometry-stabilization-references/`。

| 项目模块 | 对应参考文献 |
| --- | --- |
| 屏幕平面和 homography 建模 | `screen_to_camera_homography_estimation_iccv2003.pdf` |
| 白板/文档透视矫正类比 | `whiteboard_scanning_image_enhancement_2007.pdf`, `mobile_document_perspective_rectification_vanishing_point_2007.pdf`, `perspective_correction_camera_document_analysis_2005.pdf` |
| LK 光流和特征跟踪 | `lucas_kanade_iterative_image_registration_1981.pdf`, `shi_tomasi_good_features_to_track_1994.pdf`, `bouguet_pyramidal_lk_feature_tracker.pdf` |
| 鲁棒几何估计 | `mlesac_robust_estimator_image_geometry_2000.pdf` |
| 线段和消失点辅助分析 | `lsd_line_segment_detector_ipol2012.pdf`, `vanishing_point_detection_point_alignments_ipol2017.pdf`, `vanishing_points_correct_camera_rotation_crv2005.pdf` |
| 视频稳定化和轨迹平滑 | `motion_smoothing_strategies_video_stabilization_ipol2017.pdf`, `l1_optimal_camera_paths_cvpr2011.pdf`, `cinematic_l1_log_homography_wacv2021.pdf` |
| 稳定性评价 | `video_stabilization_evaluation_framework_euvip2018.pdf` |
| 频域残余配准 | `fft_registration_reddy_chatterji_1996.pdf` |

## 下一步执行顺序

1. 固定实验视频列表，确定每个视频的自动角点或手动角点配置。
2. 为每个视频跑主方法输出，并保存 tracker debug。
3. 跑消融实验，至少覆盖逐帧检测、普通光流、参考平面跟踪和残余对齐。
4. 用稳定性分析脚本生成 CSV 和 JSON 指标。
5. 从每组视频截取关键帧，整理到报告和展示材料。
6. 根据结果只做必要的算法修正，不再更改项目主线。
