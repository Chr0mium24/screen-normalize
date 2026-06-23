# Proposal Presentation Script (3 min) — Bilingual / 中英对照

- **Deck:** `ECE4512_Proposal_Presentation.pptx` (7 slides, English)
- **Slot:** 3 min talk + 2 min QA, 2026/06/24
- **Method framing (authoritative = deck/proposal):** border-guided reference-plane tracking — the homography is anchored to the physical screen border; inner Lucas–Kanade points are only a consistency check.
- **Spoken length:** ~407 English words (Slides 2–7 trimmed from ~496; Slide 1 kept at full length). ≈3:10–3:20 at ~120 wpm. If long, shorten Slides 5–6 first; never cut the core Slide 4.

> Note: the spoken language is English (the deck is English). Chinese lines are a parallel translation + delivery notes, not meant to be read aloud.

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
> Our method is a classical, interpretable geometry pipeline. We initialize the screen plane at the first frame by finding its four corners. We track features with Lucas–Kanade, estimate the screen-plane homography with RANSAC, then gate, interpolate, and smooth that trajectory. The output is a stable 16:9 video, ready for later restoration.

**中文对照：**
> 我们的方法是一条经典、可解释的几何流水线。先在首帧通过找到四个角点初始化屏幕平面；再用 Lucas–Kanade 跟踪特征、用 RANSAC 估计屏幕平面单应，然后对轨迹做门控、插值和平滑。输出是稳定的 16:9 视频，供后续恢复使用。

**走位 / Delivery:** 顺着 INPUT→STAGE 1–4→OUTPUT 六个卡片从左扫到右，每个动词对一个卡片。

---

## Slide 4 — Screen Motion vs. Content Motion (~32s, core / 核心)

**EN (spoken):**
> This is the key idea: separate screen motion from content motion. We anchor the homography to the screen border, not to content inside the screen. Inner feature points are only a consistency check — if their motion conflicts with the border, we drop them as content motion. If the border is lost, we freeze the last valid homography. So content keeps moving, but the frame stays locked and rectified.

**中文对照：**
> 核心思想：把屏幕运动和内容运动分开。我们把单应锚定到屏幕边框，而不是屏幕内部的内容。内部特征点只作一致性校验——若其运动与边框冲突，就当作内容运动剔除。若边框丢失，则冻结上一帧有效单应。于是内容继续动，而画面保持锁定、矫正。

**走位 / Delivery:** 全篇语速最慢的一页；讲到最后一句时指底部 time-strip（内容在变、画面不动）。

---

## Slide 5 — Dataset & Experiment (~18s)

**EN (spoken):**
> To evaluate, we are collecting fifty real clips — five scenario classes, ten clips each: static pages, scrolling pages, in-screen video, weak-border slides, and hard 4K-moiré-glare cases. On key frames, we manually label the four screen corners, so we can measure accuracy without any downstream model.

**中文对照：**
> 为评估，我们正在采集 50 段真实视频——5 类场景、每类 10 段：静态页、滚动页、屏内视频、弱边框幻灯片，以及困难的 4K/摩尔纹/反光样例。我们在关键帧上人工标注四个屏幕角点，这样不依赖任何下游模型也能量化精度。

**走位 / Delivery:** 五类卡片一句话扫过；手停在红色 Class 5（难例，衔接 future work）。

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
> Here is an initial result. On the same video, per-frame detection and optical-flow tracking both leave about 1.9 pixels of residual jitter. Our border-guided tracking cuts that to 0.118 — about sixteen times steadier. The final report compares all three on the full dataset. The proposal is done today; the next three weeks cover the dataset, ablations, and the report. Thank you.

**中文对照：**
> 这是一个初步结果。在同一段视频上，逐帧检测和普通光流都残留约 1.9 像素的抖动；我们以边框为引导的跟踪把它降到 0.118——大约稳 16 倍。最终报告会在完整数据集上比较这三种。proposal 今天完成，接下来三周覆盖数据集、消融和报告。谢谢。

**走位 / Delivery:** 报数字时指柱状图最右那根矮柱；"16×" 和 "0.118 px" 是全场记忆点，说重一点。

---

## Delivery Notes / 交付说明

- **Pace / 语速:** ~407 words ≈ 3:10–3:20 at ~120 wpm. 若偏慢/超时，先把 Slide 5、6 各压成一句；核心 Slide 4 不要砍。
- **QA consistency / 口径一致:** deck 中 "border-guided" 与 "reference-plane tracking" 指同一方法（都锚定到首帧屏幕平面/边框）。
- **Terminology / 术语:** homography=单应；rectify=矫正；residual jitter=残余抖动；p95=95 分位；inlier=内点；RANSAC=随机抽样一致。
- **Key memory hooks / 记忆点:** "missing preprocessing step"（定位）、"separate screen motion from content motion"（方法）、"0.118 px / ~16×"（结果）。
