# Proposal for CIE6032 Final Project 2026

**Names & IDs:** Rongshuo Wen (Leader, 124020369), Bihua Wen (124090670), Ruiming Liu (124090375)

**Title:** Screen Capture Rectification and Temporal Stabilization for Real-world Captured-screen Videos

**Description:** Existing screen demoiréing and screen-image restoration studies show that captured-screen content is a meaningful image processing problem. However, many public datasets are collected in controlled settings, where the screen region is already cropped, aligned, or paired with a clean reference. In real phone-captured videos, the input usually contains background regions, perspective distortion, hand-held camera shake, weak or missing screen borders, moiré patterns, glare, and dynamic screen content. This project focuses on this missing preprocessing stage: converting a full captured-screen video into a rectified and temporally stable screen-coordinate video before downstream demoiréing, OCR, or archival restoration.

**Task and goal:** The input is a hand-held video of a computer screen. The output is a fixed-ratio, front-facing, temporally stable video of the screen content. The goal is to remove most non-screen background, correct perspective distortion, reduce frame-to-frame jitter, and provide a reliable normalized input for later restoration tasks.

**Method:** The proposed pipeline first obtains the first-frame screen quadrilateral by automatic detection or manual annotation. A homography is then used to rectify the screen plane to a 16:9 output canvas. To avoid the jitter caused by independent frame-wise corner detection, reference-plane feature points are tracked using Lucas-Kanade optical flow, and a robust homography is estimated with RANSAC. Unreliable updates are rejected by geometric constraints, while missing or unstable trajectory segments are interpolated and smoothed before rendering the normalized video.

**Dataset and experiment:** The final evaluation will use a self-collected test set with 5 scenario classes, 10 clips per class, and about 5 seconds per clip. The classes are static webpages/documents, scrolling webpages, in-screen video playback, PPT or weak-border low-texture pages, and 4K/moiré/glare hard cases. Public demoiréing datasets will be discussed as related-work evidence because they mostly evaluate restoration after alignment, while this project evaluates the preceding video rectification and stabilization step.

**Evaluation metrics:** The main quantitative metrics are residual adjacent-frame translation p95, rotation p95, and scale-delta p95 measured in the normalized output video. Tracker accept ratio, RANSAC inlier count, inlier ratio, and feature coverage will be used to explain failure cases. In an initial 317-frame local test video, reference-plane tracking reduced the last-two-second residual motion to 0.118 px translation p95 and 0.0044 deg rotation p95, compared with 1.927 px and 0.0425 deg for frame-wise detection.

**Expected results:** The expected result is a classical image-processing and geometric-vision pipeline that produces stable, rectified screen videos from realistic captured-screen inputs. The final report will compare frame-wise detection, ordinary optical-flow tracking, and reference-plane tracking; summarize successful and failed cases; and discuss when this preprocessing is sufficient for downstream screen video restoration.

**Tentative timeline/to-do list:** Jun. 22--24: finalize proposal and presentation. Jun. 25--30: complete the 50-clip self-collected test set. Jul. 1--7: run method ablations and metric evaluation. Jul. 8--12: prepare visual comparisons, failure analysis, and final report. Jul. 13--15: finalize code, sample data, and presentation.
