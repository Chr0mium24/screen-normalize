# `paper_en_presentation(6).pptx` 6 分钟中英双语讲稿

> 适用版本：`D:\wechat\xwechat_files\wxid_ru5dlpvby1rc12_1472\msg\file\2026-07\paper_en_presentation(6).pptx`  
> 总时长：**6:00，包含第 7–9 页三段视频的完整播放时间**。  
> 使用方式：现场只朗读英文稿；中文是理解、背诵和临场提示用的对照译文。若中英文都逐句朗读，将明显超过 6 分钟。

## 一、总时间轴

| 页码 | 时间段 | 时长 | 操作重点 |
|---:|:---:|---:|---|
| 1 | 0:00–0:18 | 18 秒 | 开场、项目目标、核心结果 |
| 2 | 0:18–0:42 | 24 秒 | 问题背景与运动模型冲突 |
| 3 | 0:42–1:02 | 20 秒 | 三类证据来源 |
| 4 | 1:02–1:22 | 20 秒 | 旧流程及其问题 |
| 5 | 1:22–1:52 | 30 秒 | 新的边框引导流程 |
| 6 | 1:52–2:14 | 22 秒 | 数据与评价指标 |
| 7 | 2:14–2:23 | 9 秒 | 说一句 → 播放约 5.07 秒 → 点评 |
| 8 | 2:23–2:33 | 10 秒 | 说一句 → 播放约 5.07 秒 → 点评 |
| 9 | 2:33–2:43 | 10 秒 | 说一句 → 播放约 5.03 秒 → 点评 |
| 10 | 2:43–3:15 | 32 秒 | 总体定量结果 |
| 11 | 3:15–3:43 | 28 秒 | 分类结果 |
| 12 | 3:43–4:05 | 22 秒 | 单片段结果与非冻结说明 |
| 13 | 4:05–4:39 | 34 秒 | 消融实验 |
| 14 | 4:39–4:59 | 20 秒 | 定性结果 |
| 15 | 4:59–5:20 | 21 秒 | 信号诊断 |
| 16 | 5:20–5:50 | 30 秒 | 总结、局限与下一步 |
| 17 | 5:50–6:00 | 10 秒 | 文献、致谢、结束 |

## 二、正式双语讲稿

### 第 1 页｜0:00–0:18｜Border-Guided Screen-Plane Recovery

**English — speak this**

Good afternoon. We are Rongshuo Wen, Bihua Wen, and Mingrui Liu. Our project recovers a stable screen plane from handheld video. By prioritizing physical borders, we achieve 2.932-pixel corner RMSE, 0.996 IoU, and 0.752-pixel translation variation.

**中文对照**

大家下午好。我们是温荣硕、温碧华和刘明睿。我们的项目从手持视频中恢复稳定的屏幕平面。通过优先使用物理边框，我们取得了 2.932 像素角点 RMSE、0.996 IoU 和 0.752 像素平移变化。

### 第 2 页｜0:18–0:42｜Problem Context

**English — speak this**

Captured-screen video is useful, but the camera adds perspective and shake. Displayed content also moves independently from the monitor. Scrolling pages or videos can pull interior-feature trackers from the true boundary. We must locate the physical display, not follow its content.

**中文对照**

无法直接录屏时，拍屏视频很有用，但相机会引入透视和抖动。更重要的是，屏幕内容独立于物理显示器运动。滚动网页或视频会把内部特征跟踪器从真实边界拉走。我们必须定位物理显示器，而不是跟随其内容。

### 第 3 页｜0:42–1:02｜Evidence Sources

**English — speak this**

Frame-wise detection uses the current image and may jitter under weak borders. Optical flow tracks interior features and may drift with scrolling. Our method instead uses the four physical sides, directly matching the screen geometry we want to recover.

**中文对照**

我们比较三种证据来源。逐帧检测依赖当前图像，在弱边界下可能抖动。光流跟踪内部特征，可能随滚动内容漂移。我们则使用四条物理屏幕边，这种证据与需要恢复的屏幕几何直接一致。

### 第 4 页｜1:02–1:22｜Method Pipeline

**English — speak this**

Our previous pipeline initialized the plane, tracked LK features, and estimated homographies with RANSAC. It works only when interior features represent screen motion. On the right, content pulls the quadrilateral away from the monitor, motivating new primary evidence.

**中文对照**

旧流程先初始化平面，再跟踪 LK 特征并用 RANSAC 估计单应矩阵。它只有在内部特征能代表屏幕运动时才可靠。右侧例子显示，四边形会被内容拉离显示器，因此必须改变主要证据。

### 第 5 页｜1:22–1:52｜Border-Guided Estimation

**English — speak this**

The new pipeline starts from first-frame corners or a detector fallback. Near each predicted side, we sample gradient profiles and fit four lines. Their intersections give the corners. Convexity and step-size checks reject invalid quadrilaterals; we redetect when needed, then warp to a fixed canvas. Borders define geometry, while interior texture only checks consistency.

**中文对照**

新流程从首帧角点或检测器回退开始，在每条预测边附近采样梯度剖面并拟合四条直线，交点给出屏幕角点。我们用凸性和步长检查拒绝非法四边形，必要时重新检测，再映射到固定画布。现在由边框决定几何，内部纹理只检查一致性。

### 第 6 页｜1:52–2:14｜Evaluation Setup

**English — speak this**

We collected fifty clips covering static pages, scrolling pages, screen videos, weak borders, and challenging scenes. All methods share the input, initialization, output canvas, and metric code. We evaluate corner RMSE, quadrilateral IoU, and translation variation. Reference-based metrics only assess signal preservation.

**中文对照**

我们在静态页面、滚动页面、屏幕视频、弱边界和挑战场景中共采集 50 个片段。所有方法使用相同输入、初始化、输出画布和评价代码。主指标是角点 RMSE、四边形 IoU 和帧间平移变化；参考图像指标只评估信号保真度。

### 第 7 页｜2:14–2:23｜Video 1: Static Page

**English — speak this**

First, a static page.

**[Click to play the video. Stay silent for approximately 5.07 seconds.]**

Our recovered screen remains steady.

**中文对照**

首先看一个静态页面。

**[点击播放视频，保持安静约 5.07 秒。]**

我们恢复出的屏幕范围保持稳定。

### 第 8 页｜2:23–2:33｜Video 2: Scrolling Page

**English — speak this**

Now the page scrolls.

**[Click to play the video. Stay silent for approximately 5.07 seconds.]**

Optical flow drifts; ours stays fixed.

**中文对照**

现在网页开始滚动。

**[点击播放视频，保持安静约 5.07 秒。]**

光流发生漂移，而我们的屏幕范围保持固定。

### 第 9 页｜2:33–2:43｜Video 3: Screen Video

**English — speak this**

Finally, displayed content moves rapidly.

**[Click to play the video. Stay silent for approximately 5.03 seconds.]**

It remains inside our recovered screen.

**中文对照**

最后，屏幕内容快速运动。

**[点击播放视频，保持安静约 5.03 秒。]**

它始终位于我们恢复出的屏幕范围内。

### 第 10 页｜2:43–3:15｜Overall Results

**English — speak this**

Here, our method cuts RMSE from about thirty pixels for both baselines to 3.87 and reaches the highest IoU, 0.996. Translation variation is 2.45 pixels per frame, versus 2.83 for frame-wise detection and 4.13 for optical flow. It is both closer to the annotation and more stable.

**中文对照**

本页总体比较中，两个基线的 RMSE 约为 30 像素，我们将其降至 3.87，并取得最高的 0.996 IoU。平移变化为每帧 2.45 像素，逐帧为 2.83，光流为 4.13。因此，我们的结果既更接近标注，也更稳定。

### 第 11 页｜3:15–3:43｜Category Results

**English — speak this**

The category breakdown shows where gains occur. On scrolling pages, our RMSE is 2.87, while optical flow reaches 81.7. With weak borders, ours is 9.35, versus over 155 for both baselines. In hard clips, frame-wise error is slightly lower, but our trajectory is more stable. The method is most useful under strong content motion or difficult borders.

**中文对照**

分类结果显示提升来自哪里。滚动页面中，我们的 RMSE 为 2.87，光流达到 81.7；弱边界场景中，我们为 9.35，两个基线都超过 155。挑战片段里，逐帧误差略低，但我们的轨迹更稳定。因此，本方法最适合内容运动强烈或边界困难的情况。

### 第 12 页｜3:43–4:05｜Clip-Level Results

**English — speak this**

Seven clips have median RMSE below five pixels, and every clip stays below fifteen. The system held zero frames, so low variation does not come from freezing an old homography. With a visible boundary, the estimate keeps updating with the physical screen.

**中文对照**

7 个片段的 RMSE 中位数低于 5 像素，所有已评估片段都低于 15。系统也没有保持旧帧。因此，低变化并非来自冻结旧单应矩阵；只要边界可见，估计就会继续随物理屏幕更新。

### 第 13 页｜4:05–4:39｜Ablation Study

**English — speak this**

The ablation identifies the decisive component. The full chain gives 2.932 RMSE, 0.996 IoU, and 0.752 translation variation. Removing the trajectory filter worsens RMSE and variation. Disabling the LK diagnostic changes little, confirming its auxiliary role. Without physical borders, RMSE jumps to 76.114 and IoU falls to 0.916. LSD remains competitive, while Hough lines are less accurate. Reliable borders, not interior tracking, drive the improvement.

**中文对照**

消融实验识别了决定性组件。完整流程取得 2.932 RMSE、0.996 IoU 和 0.752 平移变化。移除轨迹滤波会同时恶化 RMSE 和稳定性；关闭 LK 诊断影响很小，证明它只是辅助模块。但没有物理边框时，RMSE 激增至 76.114，IoU 降至 0.916。LSD 仍有竞争力，Hough 则明显较差。因此，提升来自可靠边框观测，而不是内部跟踪。

### 第 14 页｜4:39–4:59｜Qualitative Results

**English — speak this**

These examples show the same pattern visually. Focus on the outer screen extent, not the content. Baseline outputs can shift or crop the screen, especially with scrolling and weak borders. Our output aligns the browser frame and monitor boundary more consistently. Earlier metrics provide quantitative evidence.

**中文对照**

这些样例从视觉上呈现相同规律。请关注屏幕外部范围，而不是内容。逐帧和光流可能移动或裁切屏幕，特别是在滚动和弱边界下。我们的输出能更一致地对齐浏览器外框和显示器边界，前面的指标则给出定量证据。

### 第 15 页｜4:59–5:20｜Signal Diagnostics

**English — speak this**

Signal diagnostics support the geometric results. Our output reaches 0.890 SSIM, 0.930 gradient similarity, and 0.952 edge F1, while preserving frequency structure. Better alignment retains useful signal. However, these diagnostics neither evaluate demoireing nor replace the main geometric metrics.

**中文对照**

信号诊断支持几何结果。我们的输出达到 0.890 SSIM、0.930 梯度相似度和 0.952 边缘 F1，同时保留频率结构。更好的对齐能保留有用信号；但这些诊断不评价去摩尔纹，也不能取代主要几何指标。

### 第 16 页｜5:20–5:50｜Conclusion

**English — speak this**

To conclude, physical borders prevent content-driven homography drift. Our annotated evaluation reaches 2.932-pixel RMSE and 0.996 IoU, with the largest gains on scrolling and weak borders. Reflections, occlusion, and low contrast remain limitations. Stronger boundary models and denser annotations come next. This geometric front end can support OCR, reading restoration, and demoireing.

**中文对照**

总结来说，物理边框能避免内容驱动的单应矩阵漂移。标注评估达到 2.932 像素 RMSE 和 0.996 IoU，在滚动和弱边界场景中提升最大。反光、遮挡和低对比度仍是局限。下一步是更强的边界模型和更密集的标注。这个几何前端可支持 OCR、阅读恢复和视频去摩尔纹。

### 第 17 页｜5:50–6:00｜References

**English — speak this**

Our work builds on perspective correction, tracking, robust estimation, stabilization, and demoireing. The references are listed here. Thank you, and we welcome your questions.

**中文对照**

本项目基于透视校正、跟踪、鲁棒估计、视频稳定和去摩尔纹研究，参考文献列在这里。谢谢大家，欢迎提问。

## 三、上台操作提示

1. 第 7–9 页每页只说一小句再播放；播放期间停顿，不要解释画面，否则会同时争夺听众注意力。
2. 三段视频的实际时长分别约为 **5.07、5.07、5.03 秒**。若 PowerPoint 设置为自动播放，到达该页后不要再次点击画面，以免暂停。
3. 第 7 页重点看静态页面的稳定范围；第 8 页重点看滚动时光流漂移；第 9 页重点看快速视频内容是否影响外部屏幕几何。
4. 第 14 页不要逐格解释，只需让听众看四周边界和裁切范围。
5. 正常语速控制在约 125–130 英文词/分钟；遇到数字稍微放慢，但不要在图表页逐项念完所有数值。

## 四、最新版 PPT 的数据一致性提醒（不上台朗读）

1. 第 1、13、16 页采用 **2.932 px RMSE / 0.996 IoU / 0.752 px translation variation**；第 10 页仍显示 **3.87 px / 0.996 / 2.45 px/frame**。本稿分别称为“annotated evaluation / ablation setting”和“overall comparison on this slide”，没有把两组数字说成同一统计口径。正式答辩前最好根据实验记录统一，或明确写出各自的数据子集与聚合方式。
2. 第 13 页右侧说明仍写着“smoothing trades a slightly lower RMSE for worse stability”，但更新后的表格显示：完整方法 RMSE 为 2.932，去掉滤波后为 3.253，同时平移变化从 0.752 升至 1.430。也就是说，按当前表格，滤波同时改善 RMSE 和稳定性；本稿以表格数值为准。
3. 第 6 页写有五类、每类 10 个 collection clips，共 50 个；几何标注结果页展示的是较小的 annotated/evaluated 集合。若被问到样本规模，应区分“采集集”和“有详细几何标注的评价集”。
