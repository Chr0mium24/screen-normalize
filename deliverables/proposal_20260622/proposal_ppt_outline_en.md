# Week 4 Proposal Presentation Outline

Requirement: one-page proposal submitted on 2026/06/22, 3-minute presentation plus 2-minute QA on 2026/06/24.

Recommended length: 6 slides. Keep each slide visually simple, with one main message and one figure or table.

## 1. Title and Topic

**Screen Capture Rectification and Temporal Stabilization for Real-world Captured-screen Videos**

Time: 15 seconds.

Content:

- Team members and student IDs.
- Topic: geometric preprocessing for real phone-captured screen videos.
- One-sentence pitch: before screen restoration, demoireing, OCR, or archiving, the screen must first be located, rectified, and stabilized.

Suggested visual: a raw phone-captured screen frame next to a clean front-facing screen-coordinate output.

## 2. Motivation and Gap

Time: 30 seconds.

Main message: existing screen restoration datasets often start after cropping or alignment, but real phone videos are less controlled.

Content:

- Real inputs include background, perspective distortion, hand-held shake, weak borders, glare, moire patterns, and dynamic screen content.
- This project focuses on the missing preprocessing step before downstream restoration.
- The goal is not to build a full demoireing model, but to prepare better geometric input for later tasks.

Suggested visual: problem examples labeled with background, tilt, shake, weak border, and moire.

## 3. Task and Goal

Time: 25 seconds.

Main message: convert a full captured-screen video into a stable screen-coordinate video.

Content:

- Input: hand-held video of a computer screen.
- Output: front-facing video of the screen content, with the original screen aspect ratio preserved.
- Desired effects: suppress non-screen background, perspective distortion, and frame-to-frame jitter.
- Key constraint: preserve real screen content motion such as scrolling or in-screen video playback.

Suggested visual: simple input-to-output pipeline diagram.

## 4. Core Idea and Method

Time: 55 seconds.

Main message: estimate the physical screen plane, not the moving inner content.

Pipeline:

```text
screen quadrilateral initialization
-> border-based homography estimation
-> LK feature consistency check
-> RANSAC conflict filtering
-> re-detection or freeze on failure
-> aspect-ratio rectification and temporal smoothing
```

Content:

- Use automatic detection or manual annotation to initialize the screen quadrilateral.
- Use edge filtering and LSD/Hough line detection to locate the four physical borders.
- Use inner Lucas-Kanade feature points only as consistency evidence.
- If inner motion conflicts with border motion under RANSAC, treat it as screen-content motion and exclude it from homography estimation.
- Smooth the corner trajectory to reduce high-frequency jitter.

Suggested visual: method pipeline with the screen border highlighted separately from inner moving content.

## 5. Experiments and Evaluation

Time: 60 seconds.

Main message: evaluate geometry correctness, temporal stability, and signal preservation on self-collected videos.

Dataset plan:

- 5 scenario classes, 10 clips per class, about 5 seconds per clip.
- Static pages, scrolling pages, in-screen video playback, PPT or weak-border pages, and hard cases with glare, moire, or partial screen loss.
- Selected key frames will be manually annotated with four screen corners.

Metrics:

- Geometry: corner error, quadrilateral IoU, aspect-ratio error.
- Temporal stability: residual adjacent-frame translation, rotation, and scale variation after normalization.
- Signal preservation: average gradient magnitude and edge preservation index on texture-rich regions.
- Moire or regular-grid hard cases: 2D FFT to check whether dominant frequency directions become closer to an orthogonal screen grid.

Comparison methods:

- Frame-wise screen detection.
- Content-based optical-flow tracking.
- Proposed border-guided tracking strategy.

Suggested visual: compact table with dataset classes, metrics, and baselines.

## 6. Expected Results, Timeline, and QA Setup

Time: 35 seconds.

Main message: the expected deliverable is a classical geometric preprocessing pipeline with clear success cases and failure analysis.

Expected results:

- Stable front-facing screen videos from realistic captured-screen inputs.
- Better separation between screen-plane motion and screen-content motion.
- Clear analysis of when detection, optical flow, and border-guided tracking succeed or fail.

Timeline:

- Jun. 22-24: finalize proposal and presentation.
- Jun. 25-26: collect 50 self-captured clips.
- Jun. 27-30: organize data and annotate selected key frames.
- Jul. 1-7: run ablations and metric evaluation.
- Jul. 8-10: prepare visual comparisons and report analysis.
- Jul. 11-15: finalize report, code, sample data, and presentation.

Suggested visual: short timeline bar.

## 2-Minute QA Preparation

Likely question 1: Why not directly train a demoireing model?

Answer: the project targets the earlier geometric stage. A restoration model still needs stable, cropped, front-facing screen input in real applications.

Likely question 2: How do you avoid confusing scrolling content with camera shake?

Answer: the homography is estimated from physical screen borders, while inner LK features are used only as a consistency check. Conflicting inner motion is rejected by RANSAC and treated as content motion.

Likely question 3: What if the screen border is weak or missing?

Answer: the system re-detects borders when confidence is low. If recovery fails, it freezes the last valid homography and marks invalid regions; these cases are included in robustness analysis.

Likely question 4: What makes the evaluation quantitative?

Answer: annotated corners measure geometric correctness; residual affine motion measures temporal stability; gradient, edge, and FFT metrics measure whether rectification preserves useful screen signal.
