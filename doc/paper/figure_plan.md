# Final Figure and Table Plan

本文档定义最终论文需要交付的图表、数据来源和对比维度。所有 `TBD-*` 结果位均必须由真实实验填充。

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

## Figure 2: Dataset Examples and Annotations（数据集示例与标注）

**内容：** 直接展示五类输入和人工四角标注，不制作视频属性统计图表。
- **Fig. 2a:** 每个类别选 1 个代表帧，按 static、scrolling、screen video、weak border、hard 排列。
- **Fig. 2b:** 对同一组或另一组代表帧叠加 TL/TR/BR/BL 四角标注。
- 图注说明数据集共 50 个视频，每类固定 10 个。

**数据来源：** 五类目录中的代表视频帧和同名角点 CSV。类别直接由目录名确定；不建立其他数据集元数据。

**对比维度：** 5 个场景类别之间的分布差异

---

## Figure 3: Quantitative Comparison（定量对比）

**内容：** 核心结果表，展示三种方法在五个场景上的性能

**表格布局：**
```
                    Static   Scrolling   Video   PPT/Weak   Hard    Average
                    Page     Page        Play    Border     Cases
Corner Error (px)
  Frame-wise         TBD-GEO-01 ...                              TBD-GEO-06
  Optical Flow       TBD-GEO-07 ...                              TBD-GEO-12
  Ours               TBD-GEO-13 ...                              TBD-GEO-18
  
Quadrilateral IoU
  Frame-wise         TBD-GEO-19 ...                              TBD-GEO-24
  Optical Flow       TBD-GEO-25 ...                              TBD-GEO-30
  Ours               TBD-GEO-31 ...                              TBD-GEO-36
  
Aspect-ratio Error
  Frame-wise         TBD-GEO-37 ...                              TBD-GEO-42
  Optical Flow       TBD-GEO-43 ...                              TBD-GEO-48
  Ours               TBD-GEO-49 ...                              TBD-GEO-54
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
Frame-wise          TBD-TEMP-01   TBD-TEMP-02   TBD-TEMP-03
Optical Flow        TBD-TEMP-04   TBD-TEMP-05   TBD-TEMP-06
Ours                TBD-TEMP-07   TBD-TEMP-08   TBD-TEMP-09
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

## Figure 6: Detail Preservation and Frequency Diagnostics（细节保持与频域诊断）

**内容：** 展示 rectification 后是否保留细节，并分析几何归一化和重采样带来的频域变化；不评价或宣称摩尔纹抑制能力。

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

**Fig. 6c: 2D FFT 频域诊断**
- 选 2 个包含规则网格或明显高频伪影的帧（来自 `hard` 类别）
- 每行展示：
  - 原始帧的局部放大
  - 原始帧的 2D FFT 频谱
  - Rectified 后的帧
  - Rectified 后的 2D FFT 频谱
- 用箭头标注主频率方向，说明频谱方向是否随几何归一化趋于坐标轴对齐
- 结合频谱能量变化检查重采样是否放大或削弱高频伪影，但不将变化解释为去摩尔纹

**数据来源：**
- 从 `hard` 类别中选有规则网格或高频伪影的视频
- 提取纹理区域，计算梯度幅值和边缘保持指数
- 对代表帧做 2D FFT，分析主频率方向和频谱能量变化

**对比维度：**
- **三种方法的细节保持能力**
- **几何归一化前后的频谱方向与高频能量变化**

---

## Figure 7: Ablation Study（消融实验）

**内容：** 验证每个模块的贡献

**Fig. 7a: 消融实验表格**
```
                        Corner Error   IoU    Temporal    Aspect-ratio
                        (px)                Stability     Error
Full method             TBD-ABL-01     TBD-ABL-02  TBD-ABL-03  TBD-ABL-04
w/o Consistency Check   TBD-ABL-05     TBD-ABL-06  TBD-ABL-07  TBD-ABL-08
w/o Temporal Smoothing  TBD-ABL-09     TBD-ABL-10  TBD-ABL-11  TBD-ABL-12
w/o Failure Recovery    TBD-ABL-13     TBD-ABL-14  TBD-ABL-15  TBD-ABL-16
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
| Fig. 2 | 数据集示例与标注 | 5 类代表帧和角点 CSV | 5 个场景类别的直观展示 |
| Fig. 3 | 定量对比      | 3 方法 × 5 场景 × 3 指标 | 表格 + 柱状图       |
| Fig. 4 | 时间稳定性    | 3 方法 × 50 视频的帧序列 | 折线图 + 汇总表     |
| Fig. 5 | 定性可视化    | 3 方法 × 5 场景 × 3 帧   | 5×4 网格            |
| Fig. 6 | 细节与频域诊断 | 3 方法 × 纹理区域 + FFT | 局部放大 + 频谱变化 |
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

5. **频域诊断帧：**
   - 原始帧和 rectified 帧
   - 2D FFT 频谱
