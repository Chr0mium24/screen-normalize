# 最终论文大纲

> 本大纲是最终论文的验收规格，不是当前完成状态的摘要。当前完成状态、证据边界和下一步缺口见 `current_status.md`。详细图表规格见 `figure_plan.md`。

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
  4. 多维度评估体系（几何、时间稳定性、细节、频域诊断）

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
- 类别由目录名确定，文件名作为 clip ID，不整理其他数据集元数据

**4.2 Annotation**
- 关键帧选择策略（每类选若干帧）
- 标注内容：四个屏幕角点坐标
- 标注工具和方法
- 标注者数量、一致性检验（如果有）

**4.3 Dataset Examples**
- 说明 5 类各 10 个视频
- 图表：每类代表帧和四角标注示例

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
- **频域诊断：**
  - 2D FFT 主方向与坐标轴对齐程度
  - 重采样前后的高频能量变化
  - 不将这些变化解释为摩尔纹抑制能力

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
- **表格 4：** 频域诊断对比（FFT 方向和高频变化）

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
