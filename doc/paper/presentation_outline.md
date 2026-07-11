# Final Presentation Outline

Target length: 8-10 slides, about 5 minutes.

## 1. Title

**Screen Capture Rectification and Temporal Stabilization for Real-World Filmed Display Videos**

One-sentence pitch: before video demoireing or OCR can work on real filmed-screen videos, the screen must first be detected, rectified, and stabilized.

## 2. Motivation

- Real users film screens with phones when direct screen recording is unavailable.
- The captured video includes background, perspective distortion, hand shake, scrolling, screen-internal motion, and moire.
- Existing demoireing/restoration papers often start after the screen has already been captured or aligned.

Suggested visual: raw input frame next to normalized output frame.

## 3. Problem Definition

Input: full camera video of a physical monitor.

Output: fixed 16:9 screen-coordinate video, stable over time.

Key constraint: preserve real screen content motion while stabilizing the screen plane.

## 4. Method Overview

Pipeline:

```text
screen detection -> homography rectification -> LK reference tracking
-> RANSAC and gates -> interpolation/smoothing -> optional residual affine alignment
```

Emphasize that this is a classical, interpretable geometry pipeline.

## 5. Why Reference Tracking

Compare three choices:

- `detect`: independent frame detection; jitter from corner noise.
- `flow`: frame-to-frame propagation; can drift with dynamic content.
- `reference`: all frames tied to the first screen plane; bad updates rejected.

## 6. Dataset

Show the six local videos:

- static page;
- scrolling page;
- screen-internal video;
- 4K moire hard case;
- stable 60fps baseline;
- dynamic 60fps hard case.

## 7. Main Quantitative Results

Use the core ablation table:

- Static page: detection 1.423 px vs reference 0.078 px translation p95.
- Scrolling page: flow drifts to 4.484 px; reference lowers rotation but rejects many updates.
- Screen video: reference lowers rotation and keeps median inlier ratio 0.995.

## 8. Failure Case

4K moire hard case:

- 220 rejected tracker frames;
- median inlier count 0;
- last-2s rotation p95 0.0480 deg.

Message: the current classical tracker has a clear boundary; future work should add stronger border detection or learned matching.

## 9. Application Chain

This project is not a full demoireing model.

It is the preprocessing chain:

```text
real filmed screen scene -> stable screen video -> demoireing/OCR/archive
```

This makes the project complementary to video demoireing papers.

## 10. Conclusion

- Homography rectification converts filmed screens into screen coordinates.
- Reference-plane tracking is better than per-frame detection on clean cases.
- Dynamic content requires gating and careful evaluation.
- Moire-heavy 4K input motivates future learned matching or border-aware refinement.
