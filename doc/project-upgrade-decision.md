# 项目升级决策：从几何 demo 变成可实验项目

检索与整理时间：2026-06-22

## 当前问题

现有项目已经可以把一段拍屏视频做屏幕定位、透视归一化和稳定化，也有同视频的初步消融数据。但如果继续只写“传统视觉流程”，Final 报告会偏薄，原因不是功能少，而是缺少一个清晰的研究变量：

- 数据只有一个主要样例，缺少可控评价；
- 真实视频没有 ground truth，只能用残余稳定性指标间接评价；
- 方法主要是工程组合，缺少一个可以和传统方法对比的现代模块；
- 继续加去反光、去摩尔纹、画质增强会把问题从几何归一化带偏。

项目应该从“跑通一个视频”升级为：

> 面向拍屏视频的平面几何归一化任务，构造真实样例和可控合成 benchmark，对比传统 LK 跟踪与学习式特征匹配在动态屏幕内容下的单应估计稳定性。

## 推荐方向

推荐做 **混合几何方案**，不是换题：

1. 保留现在的传统方法作为 baseline：首帧屏幕角点、homography、Shi-Tomasi/LK、RANSAC、轨迹门控和平滑。
2. 新增一个模型分支：用学习式局部特征匹配估计参考屏幕平面到当前帧的 homography。
3. 新增一个合成拍屏 benchmark：由干净屏幕画面生成带已知 homography 的拍屏视频，用 ground truth 评价角点误差、homography 误差和稳定性。

这样 Final 就不是“做了一个裁切脚本”，而是一个完整实验：

```text
真实拍屏视频 + 合成有真值视频
        |
        v
传统 LK + RANSAC baseline
        vs
学习式特征匹配 + RANSAC
        |
        v
几何误差、稳定性、失败案例分析
```

## 为什么模型应加在特征匹配环节

拍屏视频的核心难点不是画质恢复，而是 **屏幕平面姿态估计**。因此模型应该服务于 homography 估计，而不是做图像增强。

学习式特征匹配适合这个项目，因为：

- 它和现有代码接口一致：输入参考帧和当前帧，输出匹配点，再用 RANSAC 求 homography；
- 不需要训练自己的大模型，可以直接用公开 pretrained 模型；
- 可以和传统 Shi-Tomasi + LK 做公平对比；
- 动态内容、低纹理、重复纹理、反光区域会影响特征匹配，正好能形成实验分析；
- 仍然属于图像配准、特征点、单应性和视频稳定化问题，和课程主题一致。

推荐优先顺序：

| 方案 | 决策 | 原因 |
| --- | --- | --- |
| SuperPoint + LightGlue | 推荐作为主模型分支 | 稀疏特征匹配，适合接 RANSAC homography，公开代码和模型成熟 |
| LoFTR | 可作为备选或补充 | 半稠密匹配，对低纹理更友好，但推理更重，可能引入动态内容误匹配 |
| YOLO 屏幕检测 | 可选，不作为主创新 | 主要解决首帧检测，不能直接解决视频抖动；可作为自动初始化增强 |
| 文档去弯曲模型 | 不推荐 | 纸张去弯曲关注非平面形变，和电脑屏幕平面 homography 不匹配 |
| 去反光/去摩尔纹/画质恢复模型 | 不推荐 | 会把项目带到图像恢复，实验成本高，也不直接解决“像录屏”的几何问题 |
| 通用深度视频稳定模型 | 不推荐作为主线 | 多数不保证固定屏幕比例和屏幕平面几何一致性，解释难度高 |

## 数据应该怎么补

不要只随便多拍几个视频。数据应该分成两类：

### 1. 真实拍屏小数据集

目标是展示实际效果和失败场景。建议 6 段左右，每段 5-10 秒即可：

| 编号 | 场景 | 目的 |
| --- | --- | --- |
| real_static | 静态网页或文件窗口 | 基础几何归一化 |
| real_scroll | 页面滚动或鼠标移动 | 屏幕内部动态内容 |
| real_video | 屏幕内播放视频 | 大面积动态内容干扰 |
| real_glare | 轻微反光 | 高亮区域对特征的影响 |
| real_occlusion | 手或边框轻微遮挡角点 | 角点不可见时的稳定性 |
| real_low_texture | 大面积白底或低纹理页面 | 特征不足问题 |

真实视频不要求 ground truth。它们用于主观对比、残余稳定性指标、失败案例和鲁棒性讨论。

### 2. 合成拍屏 benchmark

目标是提供可量化真值。生成方式：

1. 取干净屏幕截图或录屏帧作为“真实屏幕内容”；
2. 采样一个 16:9 屏幕矩形；
3. 对每帧施加已知平移、旋转、尺度和透视扰动；
4. 把屏幕贴到背景图上；
5. 加入轻微模糊、噪声、压缩、反光遮罩、角点遮挡、屏幕内部视频变化；
6. 保存每帧真实四角点和 homography。

这样可以直接评价：

- 四角点平均误差；
- homography 重投影误差；
- 稳定后相邻帧残余运动；
- 失败帧比例；
- 不同扰动强度下的性能变化。

合成数据比“多拍几个视频”更有价值，因为它能回答方法到底准不准。

## 建议的最终方法结构

最终报告可以写成三条方法线：

### Method A：逐帧检测 baseline

每帧独立检测屏幕四边形并透视矫正。作用是证明逐帧角点不稳定。

### Method B：传统参考平面跟踪

当前已有主方法：

```text
首帧角点
  -> 参考平面特征点
  -> LK 光流跟踪
  -> RANSAC homography
  -> 几何门控
  -> 轨迹平滑
  -> 固定比例输出
```

### Method C：学习式特征匹配跟踪

新增模型分支：

```text
首帧角点
  -> 参考屏幕平面图像
  -> SuperPoint/LightGlue 或 LoFTR 匹配当前帧
  -> RANSAC homography
  -> 同样的几何门控和平滑
  -> 固定比例输出
```

关键是 Method B 和 Method C 共享后处理和评价，只替换“匹配点来源”。这样对比才干净。

## 实验设计

### 实验 1：同一真实视频消融

使用现有 `inputs/VID20260621024117.mp4`：

- 逐帧检测；
- LK 跟踪；
- 参考平面 LK + RANSAC；
- 学习式特征匹配 + RANSAC。

评价残余平移、旋转、尺度变化，以及输出视频观感。

### 实验 2：合成 benchmark 准确率

在合成数据上比较：

- corner RMSE；
- homography reprojection error；
- tracking failure rate；
- 不同动态内容比例下的误差变化；
- 不同反光/遮挡强度下的误差变化。

这是 Final 报告最重要的量化实验。

### 实验 3：真实小数据集泛化

对 6 段真实视频跑推荐配置，报告：

- 成功/失败；
- 是否需要手动角点；
- 稳定性指标；
- 关键帧对比；
- 失败原因。

这部分不用追求大规模，关键是覆盖场景。

## 代码改造计划

建议按下面顺序做，避免再发散：

1. 新增 `scripts/generate_synthetic_screen_dataset.py`  
   生成合成拍屏视频、每帧四角点和 metadata。

2. 新增 `scripts/evaluate_homography.py`  
   读取合成数据真值和运行输出，计算 corner RMSE、reprojection error、失败帧比例。

3. 给 `scripts/normalize_screen.py` 增加一个 tracker：`--tracker learned`  
   第一版用 SuperPoint + LightGlue；如果依赖或显存不合适，再换 LoFTR。

4. 新增 `scripts/run_benchmark.py`  
   批量跑 detect、reference、learned 三种方法，并把结果写到同一个 `runs/<timestamp>_benchmark/`。

5. 更新报告内容  
   把题目从“纯传统视觉”改为“传统几何与学习式特征匹配结合的拍屏视频几何归一化与稳定化”。

## 参考文献和数据源对应

### 已有本地参考

- `screen_to_camera_homography_estimation_iccv2003.pdf`：支撑屏幕到相机的 homography 建模。
- `lucas_kanade_iterative_image_registration_1981.pdf`：支撑 LK 跟踪。
- `shi_tomasi_good_features_to_track_1994.pdf`：支撑传统特征点选择。
- `mlesac_robust_estimator_image_geometry_2000.pdf`：支撑 RANSAC/MLESAC 鲁棒估计。
- `motion_smoothing_strategies_video_stabilization_ipol2017.pdf`：支撑轨迹平滑。
- `l1_optimal_camera_paths_cvpr2011.pdf` 和 `cinematic_l1_log_homography_wacv2021.pdf`：支撑稳定化路径优化和 homography 轨迹表述。

### 建议补充引用

- SuperPoint: Self-Supervised Interest Point Detection and Description, CVPRW 2018.  
  用于说明学习式兴趣点和描述子。

- LightGlue: Local Feature Matching at Light Speed, ICCV 2023.  
  用于说明学习式局部特征匹配。

- LoFTR: Detector-Free Local Feature Matching with Transformers, CVPR 2021.  
  用于说明无检测器的半稠密匹配备选方案。

- Deep Homography Estimation for Dynamic Scenes, CVPR 2020.  
  用于说明动态内容下 homography 估计可以用合成数据训练/评价。

- HPatches: A Benchmark and Evaluation of Handcrafted and Learned Local Descriptors, CVPR 2017.  
  用于说明局部特征和 homography benchmark 的评价思路。

- Screen Detection YOLOv8 dataset, Mendeley Data.  
  仅作为可选屏幕检测数据源，不作为主实验依赖。

## 最终建议

最合适的升级不是加去反光或去摩尔纹，而是：

> 建立“传统 LK vs 学习式特征匹配”的 homography 估计对比，并用合成拍屏 benchmark 提供真值评价，再用少量真实拍屏视频展示实际效果。

这样项目有三个层次：

1. 图像处理基础：边缘、角点、homography、光流、RANSAC、轨迹平滑；
2. 现代模型扩展：SuperPoint/LightGlue 或 LoFTR；
3. 实验完整性：合成真值 benchmark + 真实视频案例 + 消融评价。

这比继续堆零散功能更适合课程大作业，也更容易写成完整报告。
