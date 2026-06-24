# Proposal Presentation Script (3 min) — Bilingual / 中英对照

- **Deck:** `ECE4512_Proposal_Presentation.pptx` (7 slides, English)
- **Slot:** 3 min talk + 2 min QA, 2026/06/24
- **Method framing (authoritative = deck/proposal):** border-guided reference-plane tracking — the homography is anchored to the physical screen border; inner Lucas–Kanade points are only a consistency check.
- **Spoken length:** ~475 English words including team roles. ≈3:55–4:00 at ~120 wpm. If long, shorten Slides 5–6 first; never cut the core Slide 4.

> Note: the spoken language is English (the deck is English). Chinese lines are a parallel translation + delivery notes, not meant to be read aloud.

---

## Before Slide 1 — Team Roles (~8s)

**EN (spoken):**
> For team roles, Rongshuo Wen handles the code and stabilization pipeline, Bihua Wen works on data collection and annotation, and Mingrui Liu covers the slides and report writing.

**中文对照：**
> 分工方面，温镕硕负责代码和稳定化流水线，温璧华负责数据采集和标注，刘明睿负责 PPT 和报告撰写。

**走位 / Delivery:** 一句话带过即可。

---

## Slide 1 — Title & Motivation (~30s)

**EN (spoken):**
> Good morning. Our project is *Screen Capture Rectification and Temporal Stabilization for Real-world Captured-screen Videos*.
> When you can't screen-record directly, you film the monitor with a phone. Research on screen demoiréing shows this captured-screen content is worth restoring — but those methods almost always start *after* the screen is already cropped and aligned. Real handheld footage is messier: background, perspective tilt, shake, weak borders, glare, moiré, and content moving on the screen. We fill that **missing geometric preprocessing step** — turning a raw clip into a clean, front-facing screen video that downstream demoiréing or OCR can actually use.

**中文对照：**
> 早上好。我们的项目是《面向真实场景拍屏视频的屏幕捕获矫正与时域稳定化》。
> 当无法直接录屏时，人们会用手机拍屏幕。去摩尔纹研究说明拍屏内容值得恢复，但这些方法几乎都是从"屏幕已经裁切、对齐之后"开始的。真实手持视频要乱得多：背景、透视倾斜、手抖、弱边框、反光、摩尔纹，以及屏幕里在动的内容。我们补的就是这一步**缺失的几何前处理**——把原始片段变成干净、正视角的屏幕视频，让后续去摩尔纹或 OCR 真正能用。

**走位 / Delivery:** 开场放慢；手指右侧 "handheld → rectified" 对比图；落点重读 "missing preprocessing step"（全篇定位）。

---

## Slide 2 — Problem & Goal (~22s)

**EN (spoken):**
> The gap: downstream restoration assumes a cropped, aligned screen. Real handheld video has background, perspective, and jitter. Our goal: estimate the screen plane every frame and render it front-facing — removing background and perspective, reducing shake, but keeping on-screen content moving — at a fixed output size.

**中文对照：**
> 缺口在于：下游恢复默认屏幕已裁切、已对齐，而真实手持视频有背景、透视和抖动。我们的目标：逐帧估计屏幕平面并渲染成正视角——去掉背景和透视、压低抖动，但保留屏幕内的内容运动——并按固定尺寸输出。

**走位 / Delivery:** gap 两句快速带过；重音落在 goal，尤其"保留内容运动"。

---

## Slide 3 — Method · Geometric Pipeline (~28s)

**EN (spoken):**
> Our method is a classical, interpretable geometry pipeline. We initialize the screen plane at the first frame by finding its four corners. We track features with Lucas–Kanade, estimate the screen-plane homography with RANSAC, then gate, interpolate, and smooth that trajectory. The output is a stable 16:9 video.

**中文对照：**
> 我们的方法是一条经典、可解释的几何流水线。先在首帧通过找到四个角点初始化屏幕平面；再用 Lucas–Kanade 跟踪特征、用 RANSAC 估计屏幕平面单应，然后对轨迹做门控、插值和平滑。输出是稳定的 16:9 视频，供后续恢复使用。

**走位 / Delivery:** 顺着 INPUT→STAGE 1–4→OUTPUT 六个卡片从左扫到右，每个动词对一个卡片。

---

## Slide 4 — Screen Motion vs. Content Motion (~35s, core / 核心)

**EN (spoken):**
> This is the key idea: **separate screen motion from content motion**. We anchor the homography to the **physical screen border**, not to texture inside the screen. Inner Lucas–Kanade points are only a **consistency check** — if their motion conflicts with the border under RANSAC, we label them screen-content motion and drop them from the estimate. And there's a robust fallback: if border confidence drops or the quadrilateral becomes invalid, we re-detect; if that fails, we freeze the last valid homography. The result — content keeps moving inside the screen, but the frame itself stays locked and rectified.

**中文对照：**
> 这是核心思想：**把屏幕运动和内容运动分开**。我们把单应**锚定到物理屏幕边框**，而不是屏幕内部的纹理。内部 Lucas–Kanade 点只作**一致性校验**——若它们的运动在 RANSAC 下与边框冲突，就判为屏幕内容运动、从估计中剔除。还有稳健兜底：边框置信度下降或四边形非法时重新检测；若仍失败，则冻结上一帧有效单应。结果就是——屏幕内的内容继续动，而画面本身保持锁定、矫正。

**走位 / Delivery:** 全篇语速最慢的一页；讲到 result 时指底部 time-strip（内容在变、画面不动）。

---

## Slide 5 — Dataset & Experiment (~20s)

**EN (spoken):**
> To evaluate, we will build a 50-clip set — five scenario classes, ten clips each: static pages, scrolling pages, in-screen video, weak-border slides, and hard 4K-moiré-glare cases. A few pilot clips are already captured; full collection and key-frame corner annotation are scheduled for next week, so we can measure accuracy without any downstream model.

**中文对照：**
> 为评估，我们将构建一个 50 段的数据集——5 类场景、每类 10 段：静态页、滚动页、屏内视频、弱边框幻灯片，以及困难的 4K/摩尔纹/反光样例。目前已采集少量先导片段；完整采集与关键帧角点标注计划在下周完成，这样不依赖任何下游模型也能量化精度。

**走位 / Delivery:** 五类卡片一句话扫过；手停在红色 Class 5（难例，衔接 future work）。**口头一定说成"计划/在建"**，避免 Slide 5 的 "50 clips" 被误读成已采完。

---

## Slide 6 — Evaluation Metrics (~18s)

**EN (spoken):**
> We measure three things. Geometric accuracy — corner error, IoU, and aspect-ratio error. Temporal stability — residual translation, rotation, and scale between frames, as p95. And signal preservation — gradient and edge metrics, plus 2D-FFT grid orthogonality for moiré. No downstream model is needed.

**中文对照：**
> 我们衡量三件事。几何精度——角点误差、IoU 和长宽比误差。时域稳定性——相邻帧的残余平移、旋转和尺度，按 p95。信号保持——梯度与边缘指标，以及摩尔纹的 2D-FFT 网格正交性。全程不需要下游模型。

**走位 / Delivery:** 三个数字徽章 1-2-3 点一下即可，别逐条念 bullet。

---

## Slide 7 — Initial Results & Timeline (~27s, strong close / 强收尾)

**EN (spoken):**
> Here is an initial result. On the same video, per-frame detection and optical-flow tracking both leave about 1.9 pixels of residual jitter. Our border-guided tracking cuts that to 0.118 — about sixteen times steadier. The final report will compare all three on the full dataset. The proposal is done today; the next three weeks cover the dataset, ablations, and the report. Thank you.

**中文对照：**
> 这是一个初步结果。在同一段视频上，逐帧检测和普通光流都残留约 1.9 像素的抖动；我们以边框为引导的跟踪把它降到 0.118——大约稳 16 倍。最终报告会在完整数据集上比较这三种。proposal 今天完成，接下来三周覆盖数据集、消融和报告。谢谢。

**走位 / Delivery:** 报数字时指柱状图最右那根矮柱；"16×" 和 "0.118 px" 是全场记忆点，说重一点。

---

## Delivery Notes / 交付说明

- **Pace / 语速:** ~475 words ≈ 3:55–4:00 at ~120 wpm. 若偏慢/超时，先把 Slide 5、6 各压成一句；核心 Slide 4 不要砍。
- **QA consistency / 口径一致:** deck 中 "border-guided" 与 "reference-plane tracking" 指同一方法（都锚定到首帧屏幕平面/边框）。
- **Terminology / 术语:** homography=单应；rectify=矫正；residual jitter=残余抖动；p95=95 分位；inlier=内点；RANSAC=随机抽样一致。
- **Key memory hooks / 记忆点:** "missing preprocessing step"（定位）、"separate screen motion from content motion"（方法）、"0.118 px / ~16×"（结果）。

---

## QA / 答辩问题记录

### Q1. Why is this problem worth solving? / 为什么这个问题值得做？

**EN:**
> Many restoration methods assume the screen is already cropped and aligned. Our project solves the missing preprocessing step from raw handheld video to a stable frontal screen video.

**中文：**
> 很多恢复方法默认屏幕已经裁好、对齐了。我们解决的是从真实手持拍摄视频到稳定正视屏幕视频的前处理缺口。

### Q2. What is the main contribution of the proposal? / 这个 proposal 的主要贡献是什么？

**EN:**
> The contribution is a practical geometry pipeline: screen detection, homography rectification, temporal stabilization, and evaluation metrics for filmed-screen videos.

**中文：**
> 主要贡献是一条实用的几何流水线：屏幕检测、单应矫正、时域稳定，以及针对拍屏视频的评估指标。

### Q3. How does the current code find the screen border? / 当前代码怎么找到屏幕边框？

**EN:**
> We convert the frame to HSV, threshold the screen-like color range, clean the mask with morphology, and take the largest external contour as the screen region.

**中文：**
> 我们转 HSV，用屏幕颜色阈值得到 mask，再用形态学去噪，最后取最大的外轮廓作为屏幕区域。

### Q4. How does the code get the four screen corners? / 代码怎么得到四个屏幕角点？

**EN:**
> We approximate the largest contour with `cv2.approxPolyDP`. If it becomes a valid quadrilateral, we order the four vertices as TL, TR, BR, BL.

**中文：**
> 对最大轮廓用 `cv2.approxPolyDP` 做多边形近似。如果得到合理四边形，就排序成左上、右上、右下、左下。

### Q5. How do you separate screen motion from content motion? / 怎么区分屏幕运动和屏幕内容运动？

**EN:**
> We anchor the homography to the physical screen plane. Points whose motion disagrees with the border or RANSAC homography are treated as content motion and rejected.

**中文：**
> 我们把单应锚定到物理屏幕平面。和边框或 RANSAC 单应不一致的点，会被当作屏幕内容运动剔除。

### Q6. How are corners tracked in later frames? / 后续帧怎么跟踪角点？

**EN:**
> We track screen-region feature points with Lucas-Kanade optical flow, estimate a homography with RANSAC, and project the reference corners to the current frame.

**中文：**
> 我们在屏幕区域内用 Lucas-Kanade 光流跟踪特征点，再用 RANSAC 估计单应，把参考四角投影到当前帧。

### Q7. What happens if the border is weak, occluded, or affected by glare? / 如果边框弱、被遮挡或有反光怎么办？

**EN:**
> The tracker uses inlier count, reprojection error, coverage, and geometry checks. If an update is unreliable, we reject it and reuse or interpolate nearby valid corners.

**中文：**
> 跟踪器会检查内点数、重投影误差、覆盖范围和几何变化。不可靠更新会被拒绝，并沿用或插值有效角点。

### Q8. Why not use a deep learning method directly? / 为什么不直接用深度学习方法？

**EN:**
> Our proposal focuses on an interpretable DIP pipeline with limited data. Deep features like SuperPoint or LightGlue can be future baselines, but they are not required for the core system.

**中文：**
> 我们重点是数据需求低、可解释的 DIP 流水线。SuperPoint 或 LightGlue 可以作为后续对照，但不是主系统必需。

### Q9. What DIP-related methods or tools are used? / 用到了哪些 DIP 课程相关方法或工具？

**EN:**
> We use HSV thresholding, binary masks, morphology, contours, polygon approximation, perspective transform, homography, optical flow, RANSAC, smoothing, and FFT analysis.

**中文：**
> 用到了 HSV 阈值、二值 mask、形态学、轮廓、多边形近似、透视变换、单应矩阵、光流、RANSAC、平滑和 FFT 分析。

### Q10. How will you evaluate the final result? / 最终怎么评价效果？

**EN:**
> We evaluate geometry with corner error, IoU, and aspect ratio; stability with residual frame-to-frame motion; and signal preservation with edge, gradient, and FFT-based metrics.

**中文：**
> 几何上看角点误差、IoU 和长宽比；稳定性看相邻帧残余运动；信号保持看边缘、梯度和 FFT 相关指标。

### Q11. How is this different from normal video stabilization? / 我们项目和普通视频增稳有什么不同？

**EN:**
> Normal stabilization usually makes the whole camera view smoother. Our task locks a specific screen plane, removes perspective and background, and keeps the content inside the screen moving normally.

**中文：**
> 普通增稳通常让整个相机画面更平滑。我们是锁定特定的屏幕平面，去掉透视和背景，同时保留屏幕内部内容的正常运动。
