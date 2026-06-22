# Proposal for ECE4512 Final Project 2026

**Names & IDs:** Rongshuo Wen (124020369), Bihua Wen (124090670), Mingrui Liu (124090375)

**Title:** Screen Capture Rectification and Temporal Stabilization for Real-world Captured-screen Videos

**Description:** Screen demoiréing and restoration studies show that captured-screen content is an important image-processing problem. However, many datasets assume that the screen region is already cropped, aligned, or paired with a clean reference. Real phone-captured videos are less controlled: they include background regions, perspective distortion, hand-held shake, weak borders, glare, moiré patterns, and dynamic screen content. This project studies the missing geometric preprocessing step that converts full captured-screen videos into rectified and temporally stable screen-coordinate videos.

**Task and goal:** Given a hand-held video of a computer screen, the task is to estimate the screen plane over time and render the content as a front-facing video. The output should suppress background, perspective distortion, and frame-to-frame jitter while preserving the screen aspect ratio.

**Method:** The method separates screen motion from content motion. It obtains the screen quadrilateral by automatic detection or manual annotation, then estimates the homography mainly from physical screen borders. Edge filtering and LSD/Hough line detection locate the four borders, while inner Lucas-Kanade features are used only for consistency checking. If inner motion conflicts with border motion under RANSAC, it is treated as screen-content motion and excluded. Low border confidence, low inlier ratio, or invalid quadrilateral shape triggers border re-detection; if recovery fails, the last valid homography is frozen. The final video is rectified to the estimated native aspect ratio and temporally smoothed.

**Dataset and experiment:** The evaluation will use a self-collected real-video set with 5 scenario classes, 10 clips per class, and about 5 seconds per clip. The scenarios cover static pages, scrolling pages, in-screen video playback, PPT or weak-border pages, and hard cases with glare, moiré patterns, or partial screen loss. Selected key frames from each class will be manually annotated with four screen corners.

**Evaluation metrics:** Geometry will be evaluated on annotated key frames using corner error, quadrilateral IoU, and aspect-ratio error. Temporal stability will be measured by residual adjacent-frame translation, rotation, and scale variation in the normalized video. To check whether rectification preserves detail, texture-rich patches will be compared with average gradient magnitude and an edge preservation index at the same screen-coordinate scale. For moiré or regular-grid cases, 2D FFT will be used to test whether dominant horizontal and vertical frequency directions become closer to an orthogonal screen grid.

**Expected results:** The expected outcome is a classical image-processing and geometric-vision preprocessing pipeline that converts real captured-screen videos into stable, front-facing screen videos. The final report will compare frame-wise detection, content-based optical-flow tracking, and the proposed border-guided tracking strategy.

**Tentative timeline/to-do list:** Jun. 22--24: finalize proposal and presentation. Jun. 25--26: collect 50 videos. Jun. 27--30: organize data and annotate key frames. Jul. 1--7: run ablations and metrics. Jul. 8--10: prepare visual comparisons and analysis. Jul. 11--15: finalize report, code, sample data, and presentation.
