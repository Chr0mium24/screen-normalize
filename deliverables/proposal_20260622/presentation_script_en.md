# Proposal Presentation Script (3 min) — Bilingual / 中英对照

- **Deck:** `ECE4512_Proposal_Presentation.pptx` (7 slides, English)
- **Slot:** 3 min talk + 2 min QA, 2026/06/24
- **Method framing (authoritative = deck/proposal):** border-guided reference-plane tracking — the homography is anchored to the physical screen border; inner Lucas–Kanade points are only a consistency check.
- **Total length:** ~3:00–3:15. If overrunning, compress Slides 5–6 first; never cut the core Slide 4.

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

## Slide 2 — Problem & Goal (~25s)

**EN (spoken):**
> Here's the gap. Downstream restoration assumes a cropped, aligned screen. Real video has off-screen background, perspective, and frame-to-frame jitter — and weak borders, glare, and moiré make a naive per-frame detector unstable.
> Our goal: continuously estimate the screen plane and render it front-facing — removing background and perspective, reducing hand-held jitter while **keeping real on-screen content moving**, and preserving aspect ratio at a fixed output.

**中文对照：**
> 这就是缺口。下游恢复默认屏幕已裁切、已对齐；而真实视频有屏幕外背景、透视和逐帧抖动，弱边框、反光和摩尔纹又会让逐帧检测器不稳。
> 我们的目标：持续估计屏幕平面并渲染成正视角——去掉背景和透视、压低手抖，同时**保留屏幕内真实的内容运动**，并按固定 1920×1080 输出、保持长宽比。

**走位 / Delivery:** 三条 gap 快速带过；重音落在 goal 的三个 bullet，尤其"保留内容运动"。

---

## Slide 3 — Method · Geometric Pipeline (~35s)

**EN (spoken):**
> The method is a classical, interpretable geometry pipeline. From the full scene, we first **initialize** the screen plane — detecting or setting the four corners at the first frame. We then **track** features with Lucas–Kanade across frames, **estimate** the per-frame screen-plane homography with RANSAC, and **filter** that trajectory — gating bad updates, interpolating, and smoothing over time. The output is a stable 16:9 screen video, ready for demoiréing, OCR, or archival.

**中文对照：**
> 方法是一条经典、可解释的几何流水线。从完整画面出发，先**初始化**屏幕平面——在首帧检测或设定四个角点；再用 Lucas–Kanade 光流逐帧**跟踪**特征点，用 RANSAC **估计**每帧的屏幕平面单应，并对这条轨迹做**滤波**——门控异常更新、插值、时域平滑。输出是稳定的 16:9 屏幕视频，可直接接去摩尔纹、OCR 或归档。

**走位 / Delivery:** 顺着 INPUT→STAGE 1–4→OUTPUT 六个卡片从左扫到右，每个动词 init/track/estimate/filter 对一个卡片。

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
> To evaluate, we're collecting **fifty real clips** — five scenario classes, ten clips each, about five seconds: static pages, scrolling pages, in-screen video, weak-border slides, and the hard 4K-moiré-glare cases. For each class we manually annotate the four screen corners on selected key frames, so we can measure accuracy **without any downstream model**.

**中文对照：**
> 为评估，我们正在采集 **50 段真实视频**——5 类场景、每类 10 段、约 5 秒：静态页、滚动页、屏内视频、弱边框幻灯片，以及困难的 4K/摩尔纹/反光样例。每一类都在选定关键帧上人工标注四个屏幕角点，这样**不依赖任何下游模型**也能量化精度。

**走位 / Delivery:** 五类卡片一句话扫过；手停在红色 Class 5（难例，衔接 future work）。

---

## Slide 6 — Evaluation Metrics (~20s)

**EN (spoken):**
> We measure three things: **geometric accuracy** — corner error, quadrilateral IoU, aspect-ratio error; **temporal stability** — residual translation, rotation, and scale between frames, reported as p95; and **signal preservation** — gradient and edge metrics, plus 2D-FFT grid orthogonality for moiré. Together: correctness, stability, and detail — with no dependence on a restoration model.

**中文对照：**
> 我们衡量三件事：**几何精度**——角点误差、四边形 IoU、长宽比误差；**时域稳定性**——相邻帧的残余平移、旋转和尺度变化，按 p95 报告；**信号保持**——梯度与边缘指标，以及摩尔纹场景下的 2D-FFT 网格正交性。三者合起来覆盖正确性、稳定性和细节——且不依赖任何恢复模型。

**走位 / Delivery:** 三个数字徽章 1-2-3 点一下即可，别逐条念 bullet。

---

## Slide 7 — Initial Results & Timeline (~30s, strong close / 强收尾)

**EN (spoken):**
> And we already have an initial result. On the same input, per-frame detection and optical-flow tracking both leave about **1.9 pixels** of residual jitter; our **border-guided** reference-plane tracking cuts that to **0.118** — roughly **sixteen times steadier**. The final report will compare all three strategies on the full dataset. The proposal is done today; over the next three weeks we build the dataset, run the ablations, and prepare the final report. Thank you.

**中文对照：**
> 我们已经有了初步结果。在同一段输入上，逐帧检测和普通光流跟踪都残留约 **1.9 像素**的抖动；而我们**以边框为引导**的参考平面跟踪把它降到 **0.118**——大约**稳 16 倍**。最终报告会在完整数据集上比较这三种策略。proposal 今天完成，接下来三周我们采集数据集、跑消融与指标、准备最终报告。谢谢。

**走位 / Delivery:** 报数字时指柱状图最右那根矮柱；"16×" 和 "0.118 px" 是全场记忆点，说重一点。

---

## Delivery Notes / 交付说明

- **Timing / 时长:** ~3:00–3:15。超时先压 Slide 5、6；核心 Slide 4 不要砍。
- **QA consistency / 口径一致:** deck 中 "border-guided" 与 "reference-plane tracking" 指同一方法（都锚定到首帧屏幕平面/边框）。被问到时统一口径，别让评委以为是两个东西。
- **Terminology / 术语:** homography=单应；rectify=矫正；residual jitter=残余抖动；p95=95 分位；inlier=内点；RANSAC=随机抽样一致。中文追问时能立刻对上。
- **Key memory hooks / 记忆点:** "missing preprocessing step"（定位）、"separate screen motion from content motion"（方法）、"0.118 px / ~16×"（结果）。
