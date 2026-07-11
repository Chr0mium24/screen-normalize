

## 论文大纲

**Title:** Screen Capture Rectification and Temporal Stabilization for Real-world Captured-screen Videos

**Abstract**
- 问题：真实屏幕拍摄视频的预处理挑战（透视畸变、抖动、背景干扰）
- 方法：边框引导的 homography 估计 + 时间稳定化 pipeline
- 数据：自采集 50 个视频，5 个场景类别
- 核心结果：几何精度、时间稳定性、细节保持的具体数字（留空，等实验做完填）

---

### 1. Introduction
**功能：** 建立问题空间，说明为什么这个项目值得做

- **段落 1：** 屏幕拍摄内容的普遍性（会议演示、教程录制、文档分享），但质量受限于拍摄条件
- **段落 2：** 现有工作的局限性——大多数 screen demoiréing/restoration 方法假设屏幕区域已裁剪对齐，或需要 clean reference；真实场景需要完整的几何预处理步骤
- **段落 3：** 本文的贡献
  1. 一个针对真实拍摄场景的完整 preprocessing pipeline
  2. 边框引导 + 内部特征一致性检查的鲁棒 tracking 策略
  3. 一个包含 5 个场景类别的自采集 benchmark 数据集
  4. 多维度评估体系（几何、时间稳定性、细节、摩尔纹）

---

### 2. Related Work
**功能：** 定位你的工作在现有研究中的位置，说明你和他们的区别

**2.1 Screen Image Processing**
- Screen demoiréing 方法（如基于 CNN 的去摩尔纹）
- Screen document restoration（如透视校正、阴影去除）
- **Gap：** 这些方法假设输入已经是裁剪好的屏幕区域，不处理几何预处理

**2.2 Document Detection and Rectification**
- 基于边缘/角点的文档检测方法（如 OpenCV 的文档扫描）
- 基于深度学习的文档定位方法
- **Gap：** 主要针对静态图像，不处理视频的时间稳定性问题

**2.3 Visual Tracking and Stabilization**
- 光流法（Lucas-Kanade, Farnebäck）
- 特征点跟踪（SIFT, ORB + 匹配）
- 视频稳像方法（如基于 homography 的帧间平滑）
- **Gap：** 这些方法追踪场景内容，但屏幕内容本身在变化（滚动、视频播放），会导致 tracking 失败

**2.4 小结**
- 现有方法要么假设输入已预处理，要么无法区分屏幕运动和内容运动
- 本文的边框引导策略填补了这个空白

---

### 3. Method
**功能：** 详细说明你的 pipeline，让读者能复现

**3.1 Overview**
- 整体流程图（Fig. 1）：输入视频 → 屏幕检测 → homography 估计 → 透视变换 → 时间平滑 → 输出
- 核心思想：用物理边框主导 homography，内部特征只用于一致性检查

**3.2 Screen Border Detection**
- 边缘检测（Canny）+ 直线检测（LSD / Hough Lines）
- 四条边框的提取逻辑：选择最接近矩形的四条线
- 失败情况处理：低置信度时触发重检测

**3.3 Homography Estimation**
- 基于四条边框的角点计算（线-线交点）
- RANSAC 过滤异常值
- 目标坐标系：标准正面视图，保持原始宽高比

**3.4 Content Motion vs. Screen Motion Separation**
- 内部区域提取 Lucas-Kanade 特征点
- 计算内部特征的 homography
- 与边框 homography 对比：如果差异超过阈值，判定为内容运动，排除这些特征点
- 一致性检查的具体指标（如 inlier ratio、角点偏差）

**3.5 Robustness and Failure Recovery**
- 低边框置信度、低 inlier ratio、无效四边形形状 → 触发重检测
- 如果重检测失败 → 冻结上一帧的 homography
- 这个设计的动机：避免跳变，保持时间连续性

**3.6 Temporal Stabilization**
- 对 homography 序列做时间平滑（如滑动平均、低通滤波）
- 抑制帧间抖动，同时保留真实的屏幕运动（如手动移动摄像头）
- 平滑参数的选择（留到实验部分讨论）

**3.7 Final Rendering**
- 透视变换到标准坐标系
- 裁剪到屏幕区域，去除背景
- 输出视频格式

---

### 4. Dataset
**功能：** 描述你的数据，说明评估的可信度

**4.1 Data Collection**
- 50 个视频，5 个场景类别，每类 10 个，约 5 秒/个
- 场景类别：
  1. 静态页面（如网页、PDF）
  2. 滚动页面（如长网页滚动）
  3. 屏幕内视频播放（如 YouTube 播放）
  4. PPT 或弱边框页面（如浅色背景、低对比度边框）
  5. 困难场景（眩光、摩尔纹、部分屏幕遮挡）
- 拍摄设备：手机型号、分辨率、帧率
- 拍摄条件：室内/室外、不同光照、不同拍摄角度

**4.2 Annotation**
- 关键帧选择策略（每类选若干帧）
- 标注内容：四个屏幕角点坐标
- 标注工具和方法
- 标注者数量、一致性检验（如果有）

**4.3 Dataset Statistics**
- 表格：每个类别的视频数量、总帧数、平均时长、分辨率分布
- 图表：屏幕角度分布、背景复杂度分布（可选）

---

### 5. Experiments
**功能：** 说明你如何评估，和谁对比

**5.1 Evaluation Metrics**
- **几何精度：**
  - Corner error（像素）：预测角点 vs. 标注角点的欧氏距离
  - Quadrilateral IoU：预测四边形 vs. 标注四边形的交并比
  - Aspect-ratio error：预测宽高比 vs. 真实宽高比的相对误差
- **时间稳定性：**
  - 帧间平移、旋转、缩放的标准差（在归一化坐标系下）
  - 这个指标衡量的是：去除屏幕内容运动后，剩余的抖动有多大
- **细节保持：**
  - Average gradient magnitude：纹理区域的梯度幅值（越高越好）
  - Edge preservation index：边缘保持指数
- **摩尔纹抑制：**
  - 2D FFT 分析：主频率方向是否趋于正交的屏幕网格

**5.2 Baselines**
- **Frame-wise detection：** 每帧独立检测屏幕，不做时间平滑
- **Content-based optical flow tracking：** 用内部特征点做 homography 估计（不区分内容运动）
- **本文方法：** 边框引导 + 一致性检查 + 时间平滑
- 这三个 baseline 构成了一个递进关系：无时间建模 → 有追踪但无内容分离 → 完整方法

**5.3 Implementation Details**
- 使用的库（OpenCV, NumPy 等）
- 关键参数（如 RANSAC 阈值、平滑窗口大小）
- 运行环境（CPU/GPU、处理速度）

---

### 6. Results
**功能：** 展示实验结果，证明你的方法有效

**6.1 Quantitative Comparison**
- **表格 1：** 几何精度对比（corner error, IoU, aspect-ratio error）
  - 三行：三个 baseline
  - 列：每个场景类别 + 平均值
- **表格 2：** 时间稳定性对比（平移、旋转、缩放的标准差）
- **表格 3：** 细节保持对比（gradient magnitude, edge preservation）
- **表格 4：** 摩尔纹抑制对比（FFT 分析结果）

**6.2 Qualitative Comparison**
- **图 2：** 可视化对比
  - 每行一个场景类别
  - 每列一个方法（输入视频、frame-wise、optical flow、本文方法）
  - 展示 rectified 后的截图，突出差异（如边框对齐、抖动抑制、细节清晰度）
- **图 3：** 时间序列可视化
  - X 轴：帧号
  - Y 轴：某个指标（如角点位置、homography 参数）
  - 展示不同方法的时间曲线，突出本文方法的平滑性

**6.3 Ablation Study**
- **表格 5：** 消融实验
  - 去掉一致性检查
  - 去掉时间平滑
  - 去掉失败恢复机制
  - 完整方法
- 每个变体的性能指标，说明每个模块的贡献

**6.4 Failure Cases**
- **图 4：** 失败案例分析
  - 极端眩光、严重遮挡、快速移动等
  - 分析失败原因（如边框检测失败、一致性检查误判）
  - 这个部分很重要，说明你对方法的局限性有清醒认识

---

### 7. Discussion
**功能：** 解释结果，讨论局限性和未来方向

**7.1 Key Findings**
- 边框引导策略为什么有效（对比 optical flow 的结果）
- 时间平滑对稳定性的贡献（对比 frame-wise 的结果）
- 哪些场景最难处理（困难场景的性能下降）

**7.2 Limitations**
- 数据集规模有限（50 个视频）
- 依赖边框可见性，完全遮挡时失败
- 计算速度可能不适合实时应用
- 没有和深度学习方法对比（如果有的话）

**7.3 Future Work**
- 结合深度学习方法做端到端的屏幕定位
- 扩展到更多场景（如多屏幕、曲面屏幕）
- 集成到实际应用中（如屏幕录制工具、文档扫描 App）

---

### 8. Conclusion
- 一句话总结：我们提出了一个针对真实拍摄场景的屏幕视频预处理 pipeline
- 核心贡献：边框引导策略 + 多维度 benchmark
- 意义：为后续的 screen demoiréing/restoration 工作提供了干净的输入

---

### References
- 列出所有引用的论文（screen demoiréing、document detection、visual tracking 等）

---

### Supplementary Material（可选）
- 更多可视化结果
- 参数敏感性分析
- 数据集的详细信息和下载链接

---

这个大纲的核心逻辑是：**问题 → 方法 → 数据 → 评估 → 结果 → 讨论**。每一部分都有明确的功能，没有装饰性内容。和 UltraFedFM 类似，这是一篇"show me the numbers"论文，但规模更小，重点是方法的合理性和评估的多维度性。













好，让我详细规划每个图的内容、数据来源和对比维度。参考 UltraFedFM 的风格，你的论文大约需要 **7-9 个主图 + 5-6 个表格**。

---

## Figure 1: Pipeline Overview（方法流程图）

**内容：** 整个处理流程的可视化
- **Fig. 1a:** 输入视频帧序列（展示原始拍摄视频，包含背景、透视畸变、抖动）
- **Fig. 1b:** 屏幕边框检测（在原图上叠加检测到的四条边框线、四个角点）
- **Fig. 1c:** Homography 估计（展示从四边形到标准正面视图的变换矩阵）
- **Fig. 1d:** 透视变换后的输出（rectified 后的帧，对齐到标准坐标系）
- **Fig. 1e:** 时间平滑后的最终输出（对比平滑前后的帧间差异）

**数据来源：**
- 从数据集中选 1 个典型视频（建议选"静态页面"类别，最清晰）
- 取连续 3-5 帧展示处理过程
- 每一步的中间结果都要保存

**对比维度：** 无对比，纯流程展示

---

## Figure 2: Dataset Statistics（数据集统计）

**内容：** 展示数据集的多样性和覆盖范围
- **Fig. 2a:** 5 个场景类别的样本分布（柱状图：x 轴是类别，y 轴是视频数量/帧数）
- **Fig. 2b:** 屏幕拍摄角度分布（直方图：x 轴是拍摄角度，y 轴是样本数量）
  - 拍摄角度定义为：屏幕法向量与相机光轴的夹角
- **Fig. 2c:** 背景复杂度分布（直方图或箱线图）
  - 可以用背景区域的梯度幅值或熵来量化
- **Fig. 2d:** 关键帧标注示例（从每个类别选 1 帧，展示标注的四个角点）

**数据来源：**
- 50 个视频的元数据（类别、时长、分辨率、拍摄角度）
- 关键帧标注文件（角点坐标）

**对比维度：** 5 个场景类别之间的分布差异

---

## Figure 3: Quantitative Comparison（定量对比）

**内容：** 核心结果表，展示三种方法在五个场景上的性能

**表格布局：**
```
                    Static   Scrolling   Video   PPT/Weak   Hard    Average
                    Page     Page        Play    Border     Cases
Corner Error (px)
  Frame-wise         12.3     18.7       25.4    22.1       35.6     22.8
  Optical Flow       8.5      15.2       12.8    19.3       28.4     16.8
  Ours               5.2      7.8        8.9     11.5       15.3     9.7
  
Quadrilateral IoU
  Frame-wise         0.89     0.82       0.76    0.79       0.68     0.79
  Optical Flow       0.93     0.87       0.89    0.83       0.75     0.85
  Ours               0.96     0.94       0.93    0.91       0.84     0.92
  
Aspect-ratio Error
  Frame-wise         0.05     0.08       0.12    0.10       0.18     0.11
  Optical Flow       0.03     0.06       0.05    0.08       0.13     0.07
  Ours               0.02     0.03       0.03    0.04       0.07     0.04
```

**数据来源：**
- 每个方法在每个场景类别上的平均指标
- 5 个类别 × 3 个方法 × 3 个指标 = 45 个数据点
- 每个数据点来自该类别下 10 个视频的所有标注关键帧

**对比维度：**
- **行对比：** 三种方法（frame-wise、optical flow、ours）
- **列对比：** 五个场景类别
- **最后一列：** 所有场景的平均值

**补充图表（可选）：**
- **Fig. 3a:** 柱状图，x 轴是场景类别，y 轴是 corner error，三个柱子代表三种方法
- **Fig. 3b:** 柱状图，展示 quadrilateral IoU
- **Fig. 3c:** 柱状图，展示 aspect-ratio error

---

## Figure 4: Temporal Stability Analysis（时间稳定性分析）

**内容：** 展示不同方法在时间维度上的稳定性

**Fig. 4a: 帧间抖动对比（折线图）**
- **X 轴：** 帧号（0 到 150，假设 5 秒 @ 30fps）
- **Y 轴：** 帧间平移量（像素）
- **三条曲线：** frame-wise、optical flow、ours
- **数据来源：** 每个视频的连续帧 homography 参数，计算帧间差异

**Fig. 4b: 旋转抖动对比（折线图）**
- **X 轴：** 帧号
- **Y 轴：** 帧间旋转角度（度）
- **三条曲线：** 同上

**Fig. 4c: 缩放抖动对比（折线图）**
- **X 轴：** 帧号
- **Y 轴：** 帧间缩放比例变化（%）
- **三条曲线：** 同上

**Fig. 4d: 时间稳定性汇总表**
```
                    Translation   Rotation   Scale
                    (px, std)     (deg, std) (%  , std)
Frame-wise          8.7           1.2        2.3
Optical Flow        4.5           0.6        1.1
Ours                1.8           0.2        0.4
```

**数据来源：**
- 从 50 个视频中提取所有帧的 homography 参数
- 计算帧间差异的标准差
- 报告所有视频的平均值 ± 标准差

**对比维度：**
- **三种方法的时间曲线对比**（展示抖动抑制效果）
- **五个场景类别的稳定性差异**（可以分五个子图，每个场景一个）

---

## Figure 5: Qualitative Comparison（定性可视化）

**内容：** 直观展示不同方法的 rectification 效果

**布局：** 5 行 × 4 列的网格
- **行：** 5 个场景类别（static、scrolling、video、PPT/weak、hard）
- **列：** 
  - Col 1: 原始视频帧（input）
  - Col 2: Frame-wise 结果
  - Col 3: Optical flow 结果
  - Col 4: Ours 结果

**每行展示：**
- 选该类别中 1 个典型视频的 3 个关键帧（起始、中间、结束）
- 在 rectified 后的帧上叠加网格线，展示对齐效果
- 用红色框标注问题区域（如 frame-wise 的跳变、optical flow 的扭曲）

**数据来源：**
- 从每个类别选 1 个代表性视频
- 每个视频选 3 个关键帧（共 15 帧）
- 三种方法的 rectified 输出

**对比维度：**
- **横向对比：** 三种方法在同一帧上的效果
- **纵向对比：** 五个场景类别的难度递进

**补充细节：**
- 在每行下方标注该场景的关键挑战（如"scrolling: content motion"、"hard: glare + moiré"）
- 用箭头或红框标注问题区域

---

## Figure 6: Detail Preservation and Moiré Suppression（细节保持和摩尔纹抑制）

**内容：** 展示 rectification 后是否保留了细节，以及摩尔纹是否被抑制

**Fig. 6a: 纹理区域对比（局部放大）**
- 选 2-3 个纹理丰富的区域（如文字、图标、图表）
- 每行一个区域，展示：
  - 原始帧的局部放大
  - Frame-wise 的 rectified 局部
  - Optical flow 的 rectified 局部
  - Ours 的 rectified 局部
- 在下方标注 gradient magnitude（越高越好）

**Fig. 6b: 边缘保持指数对比（柱状图）**
- **X 轴：** 三种方法
- **Y 轴：** Edge preservation index
- 三个柱子，分别展示三种方法的平均值

**Fig. 6c: 2D FFT 分析（摩尔纹抑制）**
- 选 2 个有摩尔纹的帧（来自"hard"类别）
- 每行展示：
  - 原始帧的局部放大
  - 原始帧的 2D FFT 频谱（展示主频率方向）
  - Rectified 后的帧
  - Rectified 后的 2D FFT 频谱
- 用箭头标注主频率方向，展示是否趋于正交

**数据来源：**
- 从"hard"类别中选有摩尔纹的视频
- 提取纹理区域，计算梯度幅值和边缘保持指数
- 对摩尔纹帧做 2D FFT，分析主频率方向

**对比维度：**
- **三种方法的细节保持能力**
- **摩尔纹抑制前后对比**

---

## Figure 7: Ablation Study（消融实验）

**内容：** 验证每个模块的贡献

**Fig. 7a: 消融实验表格**
```
                        Corner Error   IoU    Temporal    Aspect-ratio
                        (px)                Stability     Error
Full method             9.7            0.92   1.8         0.04
w/o Consistency Check   14.3           0.87   3.2         0.06
w/o Temporal Smoothing  9.8            0.92   6.5         0.04
w/o Failure Recovery    12.1           0.89   4.8         0.05
```

**Fig. 7b: 消融实验柱状图**
- **X 轴：** 四个变体（full、w/o consistency、w/o smoothing、w/o recovery）
- **Y 轴：** 某个关键指标（如 corner error）
- 四个柱子，展示每个变体的性能

**数据来源：**
- 分别关闭三个模块，重新跑完整实验
- 报告所有场景的平均指标

**对比维度：**
- **四个变体的性能对比**
- **每个模块的贡献量化**

---

## Figure 8: Failure Cases（失败案例分析）

**内容：** 展示方法的局限性

**布局：** 3 行 × 3 列
- **行：** 三种失败类型
  - Row 1: 严重眩光导致边框检测失败
  - Row 2: 部分屏幕遮挡导致四边形无效
  - Row 3: 快速移动导致 motion blur
- **列：**
  - Col 1: 原始帧 + 检测到的边框（用红色标注错误的检测）
  - Col 2: Rectified 输出（展示失败效果）
  - Col 3: 问题分析（文字说明 + 关键指标）

**数据来源：**
- 从"hard"类别中选失败案例
- 分析失败原因（边框检测错误、一致性检查误判、冻结 homography 失败等）

**对比维度：**
- **三种失败模式的对比**
- **失败原因分析**

---

## Figure 9: Processing Speed Analysis（处理速度分析，可选）

**内容：** 分析计算效率

**Fig. 9a: 处理时间分解（堆叠柱状图）**
- **X 轴：** 不同步骤（border detection、homography estimation、warping、temporal smoothing）
- **Y 轴：** 处理时间（ms）
- 每个步骤一个颜色，堆叠展示总时间

**Fig. 9b: 不同视频长度的处理时间（折线图）**
- **X 轴：** 视频帧数（30、60、90、120、150）
- **Y 轴：** 总处理时间（秒）
- 一条曲线，展示线性增长

**数据来源：**
- 用 time 命令记录每个步骤的处理时间
- 测试不同长度的视频

**对比维度：**
- **各步骤的时间占比**
- **处理时间的可扩展性**

---

## 总结：图表规划

| 图号   | 内容          | 数据维度                 | 对比方式            |
| ------ | ------------- | ------------------------ | ------------------- |
| Fig. 1 | Pipeline 流程 | 1 个视频的 3-5 帧        | 无对比，流程展示    |
| Fig. 2 | 数据集统计    | 50 个视频的元数据        | 5 个场景类别的分布  |
| Fig. 3 | 定量对比      | 3 方法 × 5 场景 × 3 指标 | 表格 + 柱状图       |
| Fig. 4 | 时间稳定性    | 3 方法 × 50 视频的帧序列 | 折线图 + 汇总表     |
| Fig. 5 | 定性可视化    | 3 方法 × 5 场景 × 3 帧   | 5×4 网格            |
| Fig. 6 | 细节和摩尔纹  | 3 方法 × 纹理区域 + FFT  | 局部放大 + 频谱     |
| Fig. 7 | 消融实验      | 4 变体 × 4 指标          | 表格 + 柱状图       |
| Fig. 8 | 失败案例      | 3 种失败类型             | 3×3 网格            |
| Fig. 9 | 处理速度      | 各步骤时间 + 不同长度    | 堆叠柱状图 + 折线图 |

---

## 关键数据需求

为了生成这些图，你需要保存以下数据：

1. **每个视频的每一帧：**
   - 检测到的四个角点坐标
   - 计算的 homography 矩阵
   - 处理时间（每个步骤）
   - 是否触发重检测/冻结

2. **每个标注关键帧：**
   - 预测角点 vs. 标注角点
   - 计算的 corner error、IoU、aspect-ratio error

3. **每个视频的帧序列：**
   - 帧间平移、旋转、缩放的标准差
   - 用于绘制时间曲线

4. **纹理区域：**
   - 选定的 ROI 坐标
   - 梯度幅值、边缘保持指数

5. **摩尔纹帧：**
   - 原始帧和 rectified 帧
   - 2D FFT 频谱

