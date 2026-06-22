# Proposal Presentation Image and Content Checklist

This checklist matches `proposal_presentation.tex`. The main presentation is designed for 6 slides and about 3 minutes, with 2 backup slides for QA.

## Compile Command

Recommended command:

```bash
cd deliverables/proposal_20260622
latexmk -pdf proposal_presentation.tex
```

Fallback command:

```bash
cd deliverables/proposal_20260622
pdflatex proposal_presentation.tex
pdflatex proposal_presentation.tex
```

The template uses missing-image placeholders, so it can compile before all final images are ready.

## Images Needed

| Slide | File path in LaTeX | Status | What you should provide |
| --- | --- | --- | --- |
| 1. Title and Topic | `assets/comparison_1s.jpg` | Existing local candidate | A clean before/after image: raw phone-captured screen on the left, rectified screen-coordinate output on the right. Use a real project frame if possible. |
| 2. Motivation and Gap | `assets/screen_corners_overlay_4s.jpg` | Existing local candidate | A raw frame with the detected or annotated screen quadrilateral drawn on top. It should clearly show background, perspective tilt, and the physical screen boundary. |
| 4. Core Idea and Method | `assets/tracking_visualization.png` | Missing in this exact format | A compact visualization showing screen-border tracking and inner content motion separately. You can export/convert the existing `assets/tracking_visualization.svg` to PNG, or replace the LaTeX path with a PDF/PNG version. |

## Optional Images To Improve The Deck

| Suggested file name | Use | Content |
| --- | --- | --- |
| `assets/problem_examples_montage.png` | Replace or supplement slide 2 | A 2x2 montage: weak border/PPT, scrolling page, glare or reflection, moire hard case. Each tile should have a short label. |
| `assets/self_collected_dataset_plan.png` | Supplement slide 5 | Visual summary of the 5 planned scenario classes and 10 clips per class. You can convert the existing SVG if you want an image instead of the native LaTeX text. |
| `assets/proposal_timeline.png` | Supplement slide 6 | A short timeline from Jun. 22 to Jul. 15. The current slide already has a table, so this is optional. |

## Text Content To Confirm

| Item | Current draft | What to confirm |
| --- | --- | --- |
| Title | `Screen Capture Rectification and Temporal Stabilization for Real-world Captured-screen Videos` | Confirm this is the exact title you want on the slide and proposal. |
| Names | Rongshuo Wen, Bihua Wen, Ruiming Liu | Add student IDs on the title slide if required by the instructor. |
| Dataset plan | 5 classes, 10 clips per class, about 5 seconds per clip | Confirm whether you will actually collect all 50 clips or present this as the planned dataset. |
| Scenario classes | static pages; scrolling pages; in-screen video playback; PPT or weak-border pages; glare/moire/partial-loss hard cases | Confirm whether PPT/weak-border should be one class and hard cases another class, matching the proposal. |
| Metrics | corner error, quad IoU, aspect-ratio error; residual translation/rotation/scale; gradient magnitude; edge preservation; 2D FFT direction check | Confirm that all metrics are feasible for the implementation stage. If not, remove the weaker ones before presenting. |
| Baselines | frame-wise detection, content optical flow, proposed border-guided tracking | Confirm these are the three methods you want to compare in the final report. |

## 3-Minute Speaking Content

Use this pacing if the deck stays at 6 main slides:

| Slide | Time | Message |
| --- | ---: | --- |
| 1 | 15s | We solve geometric preprocessing for real captured-screen videos. |
| 2 | 30s | Existing restoration setups often start after alignment, while real phone videos contain background, tilt, shake, weak borders, glare, moire, and dynamic content. |
| 3 | 25s | Input is a full hand-held video; output is a stable front-facing screen video that preserves aspect ratio and real content motion. |
| 4 | 55s | The method estimates the physical screen plane using borders, with LK points only as consistency checks. Conflicting inner motion is rejected as content motion. |
| 5 | 60s | We evaluate on 50 planned self-collected clips using geometry, stability, signal preservation, and FFT-based grid/moire measures. |
| 6 | 35s | Expected result is a classical geometric preprocessing pipeline, with ablations and failure analysis completed by Jul. 15. |

## 2-Minute QA Content

Prepare short answers for these questions:

1. Why not directly train a demoireing model?

   This project targets the earlier geometric stage. Downstream restoration still needs stable, cropped, front-facing screen input in real applications.

2. How do you avoid confusing scrolling content with camera shake?

   The homography is estimated mainly from physical screen borders. Inner LK features are only consistency evidence, and RANSAC rejects motion that conflicts with the border motion.

3. What if the screen border is weak or missing?

   The system re-detects borders when confidence is low. If recovery fails, it freezes the last valid homography and marks invalid regions for robustness analysis.

4. What makes the evaluation quantitative?

   Annotated corners measure geometry, residual affine motion measures temporal stability, and gradient/edge/FFT metrics measure signal preservation after rectification.
