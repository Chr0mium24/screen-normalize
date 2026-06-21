# 项目取舍决策：从几何 demo 到应用端前处理链路

整理时间：2026-06-22

## 当前判断

现有项目已经可以把一段真实拍屏视频做屏幕定位、透视归一化和时域稳定，也有同视频的初步消融数据。经过重新评估，项目不应再把“学习式特征匹配分支”作为 Final 必做核心。

更合理的主线是：

> 面向真实场景拍屏视频恢复，补全 video demoiréing 等后续恢复方法之前的屏幕捕获矫正、透视归一化和时域稳定前处理。

原因是：

- 现有拍屏去摩尔纹论文证明了屏幕图像/视频恢复是真实问题，但很多工作依赖受控采集、裁切或已对齐数据；
- 真实用户输入首先是一段完整手持拍摄视频，包含背景、屏幕边框、透视倾斜、手抖和动态屏幕内容；
- 去摩尔纹、颜色校正和细节恢复之前，需要把屏幕内容稳定到接近正面屏幕坐标系；
- 当前代码已经覆盖这条前置链路的核心几何模块，继续补实验和叙事比强行接入模型更稳。

完整应用链路叙事见 `doc/application-pipeline-story.md`。

## 主线方向

项目主线固定为 **传统几何前处理链路**：

```text
真实手持拍屏视频
  -> 首帧屏幕区域检测或手动四角点
  -> Homography 透视归一化
  -> LK 光流跟踪参考平面特征点
  -> RANSAC 估计当前帧屏幕平面 homography
  -> 几何门控拒绝异常更新
  -> 坏帧插值和轨迹平滑
  -> 可选残余仿射稳定
  -> 接近录屏视角的稳定屏幕视频
```

这个输出不是最终画质恢复结果，而是后续模块的稳定输入：

```text
本项目输出
  -> video demoiréing
  -> 颜色校正
  -> 细节恢复
  -> OCR / 归档 / 人工查看
```

## SuperPoint + LightGlue 的定位

`scripts/probe_learned_homography.py` 已经验证过 SuperPoint + LightGlue 可以在部分样例上估计屏幕平面 homography，但它不应作为当前主线必做项。

保留它的定位：

- 可选的 homography 匹配对照；
- future work；
- 用于说明学习式局部特征在拍屏几何估计中的可行性和局限；
- 不替代当前 LK + RANSAC 参考平面跟踪；
- 不承担屏幕边框检测、去摩尔纹或画质恢复任务。

不优先完整接入的原因：

- 它主要解决参考帧与当前帧之间的特征匹配，不直接解决真实场景下的屏幕边框定位；
- 它增加模型依赖、下载和运行不确定性，可能拖慢课程交付；
- 现有 probe 显示它在 `testmoire.mp4` 上接受率较低，说明学习式匹配不是万能解；
- 当前 LK reference tracker 在已有样例上重投影误差更低，已经足够支撑主方法。

因此，Final 中最稳的表述是：

> Our main system uses a classical LK-RANSAC homography tracker for screen-plane stabilization. We additionally probe SuperPoint and LightGlue as an optional learned feature matching baseline, but it is not required for the proposed application pipeline.

## 数据应该怎么补

不要只随便多拍几个视频。数据应该服务于“真实场景前处理链路是否可靠”这个问题。

### 1. 真实拍屏小数据集

建议选 3-6 段，每段 5-10 秒，覆盖不同失败模式：

| 编号 | 场景 | 目的 |
| --- | --- | --- |
| real_static | 静态网页或文件窗口 | 基础屏幕检测和透视归一化 |
| real_scroll | 页面滚动或鼠标移动 | 屏幕内部动态内容 |
| real_video | 屏幕内播放视频 | 大面积动态内容对跟踪的干扰 |
| real_glare | 轻微反光 | 高亮区域对特征点的影响 |
| real_occlusion | 手或边框轻微遮挡角点 | 屏幕边界不完整时的鲁棒性 |
| real_low_texture | 大面积白底或低纹理页面 | 特征不足问题 |

真实视频不要求 ground truth。它们用于主观对比、残余稳定性指标、失败案例和鲁棒性讨论。

### 2. 同视频消融

这是最重要的实验，因为它可以直接回答每个模块是否有贡献：

- `--tracker detect`：逐帧检测角点，展示角点误差导致的抖动；
- `--tracker flow`：普通光流跟踪，展示缺少参考平面门控时的漂移风险；
- `--tracker reference`：当前主方法；
- `--reference-align --reference-motion affine`：验证归一化后残余小运动是否能进一步降低；
- 不同 `--median-window` 和 `--trajectory-window`：分析轨迹平滑强度和延迟。

### 3. 可选合成或人工标注样例

如果时间允许，可以补一个小型合成/标注样例：

1. 取干净截图或录屏帧作为屏幕内容；
2. 采样已知四角点和 homography；
3. 贴到背景上，加入轻微模糊、压缩、反光遮罩和动态内容；
4. 保存每帧真实四角点；
5. 评价 corner RMSE、homography reprojection error 和 failure rate。

这可以增强量化说服力，但不是取代真实视频实验的主线。

## 最终方法结构

报告可以按下面方法线组织：

### Method A：逐帧检测 baseline

每帧独立检测屏幕四边形并透视矫正。作用是证明逐帧角点估计容易抖动。

### Method B：普通光流跟踪 baseline

用前后帧光流传播角点。作用是展示没有参考平面约束和几何门控时，动态内容和局部漂移会影响稳定性。

### Method C：参考平面 LK + RANSAC 主方法

```text
首帧角点
  -> 参考平面特征点
  -> LK 光流跟踪
  -> RANSAC homography
  -> 几何门控
  -> 坏帧插值和轨迹平滑
  -> 固定比例输出
```

### Method D：可选残余仿射稳定

在透视归一化后估计相对参考帧的小幅残余仿射运动，只在全视频预检可靠时启用。

### Optional：学习式特征匹配探针

SuperPoint + LightGlue 可以保留为 `probe` 级实验，用来说明它在部分拍屏样例上能估计 homography，但目前不作为主方法，也不要求接入完整视频处理流程。

## 实验设计

### 实验 1：同一真实视频消融

使用现有 `inputs/VID20260621024117.mp4`，比较：

- 逐帧检测；
- 普通光流跟踪；
- 参考平面 LK + RANSAC；
- 参考平面 LK + RANSAC + 轨迹几何门控；
- 可选残余仿射稳定。

评价残余平移、旋转、尺度变化，以及输出视频观感。

### 实验 2：真实小数据集泛化

对 3-6 段真实视频跑推荐配置，报告：

- 是否自动检测成功；
- 是否需要手动角点；
- 稳定性指标；
- 关键帧对比；
- 失败原因。

### 实验 3：应用链路说明

把本项目输出解释为后续 video demoiréing 的前处理输入，而不是直接与去摩尔纹网络比较画质指标。重点展示：

- 原始完整拍摄画面；
- 屏幕四角点；
- 透视归一化结果；
- 稳定前后残余运动指标；
- 为什么这种对齐输入对后续恢复/OCR更有价值。

## 代码改造优先级

当前优先级：

1. 固定真实视频实验集和运行配置；
2. 保存每个实验的命令、输出目录、debug CSV 和关键帧；
3. 整理同视频消融结果；
4. 更新 proposal/final 文档，把项目定位为应用端前处理链路；
5. 如果时间允许，再做小型合成/人工标注样例。

暂不优先：

- 不优先实现 `--tracker learned`；
- 不优先训练或接入去摩尔纹网络；
- 不优先做复杂 GUI 或独立应用；
- 不把 SuperPoint/LightGlue 包装成核心创新。

## 参考文献对应

### 几何和稳定主线

- `screen_to_camera_homography_estimation_iccv2003.pdf`：支撑屏幕到相机的 homography 建模。
- `whiteboard_scanning_image_enhancement_2007.pdf`：支撑平面区域定位、裁切、矩形化和增强的扫描流程。
- `mobile_document_perspective_rectification_vanishing_point_2007.pdf`：支撑手机拍摄平面内容的透视校正背景。
- `lucas_kanade_iterative_image_registration_1981.pdf`：支撑 LK 跟踪。
- `shi_tomasi_good_features_to_track_1994.pdf`：支撑传统特征点选择。
- `mlesac_robust_estimator_image_geometry_2000.pdf`：支撑 RANSAC/MLESAC 鲁棒估计。
- `motion_smoothing_strategies_video_stabilization_ipol2017.pdf`：支撑轨迹平滑。
- `l1_optimal_camera_paths_cvpr2011.pdf` 和 `cinematic_l1_log_homography_wacv2021.pdf`：支撑视频稳定化路径优化和 homography 轨迹表述。

### 应用链路和后续恢复背景

- Video Demoiréing with Relation-Based Temporal Consistency, CVPR 2022.
  用于说明拍屏视频去摩尔纹是真实研究问题，同时其数据对齐依赖 homography 和 optical flow。

- Direction-aware Video Demoiréing with Temporal-guided Bilateral Learning, AAAI 2024.
  用于说明后续恢复模块会处理去摩尔纹、颜色校正、细节恢复和时间一致性。

- Recaptured Raw Screen Image and Video Demoiréing via Channel and Spatial Modulations, NeurIPS 2023.
  用于说明拍屏图像/视频恢复中存在可控采集和时序对齐设置。

### 可选学习式匹配参考

- SuperPoint: Self-Supervised Interest Point Detection and Description, CVPRW 2018.
- LightGlue: Local Feature Matching at Light Speed, ICCV 2023.
- LoFTR: Detector-Free Local Feature Matching with Transformers, CVPR 2021.
- HPatches: A Benchmark and Evaluation of Handcrafted and Learned Local Descriptors, CVPR 2017.

这些只用于 optional probe 或 future work，不是当前主方法的必要引用。

## 最终建议

Final 阶段最稳的目标不是继续扩大模型范围，而是把当前传统几何链路做完整、讲清楚、可复现：

> 本项目补全真实拍屏视频恢复的前置链路：从完整手持拍摄画面中检测屏幕平面，透视归一化到固定画布，并通过 LK + RANSAC 和轨迹平滑获得时域稳定的屏幕视频，为后续 video demoiréing、OCR 和归档提供更可靠的输入。

这样项目有三个清晰层次：

1. 应用意义：真实拍屏恢复不能默认已有裁切和对齐输入；
2. 图像处理方法：边缘、角点、homography、光流、RANSAC、轨迹平滑；
3. 实验证据：同视频消融 + 真实小数据集 + 失败案例。
