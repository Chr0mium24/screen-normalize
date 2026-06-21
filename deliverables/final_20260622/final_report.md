# Screen Capture Rectification and Temporal Stabilization for Real-World Filmed Display Videos

## Abstract

Real-world filmed screen videos are often not ready for screen restoration models. A handheld camera recording of a monitor contains background regions, perspective distortion, small hand shake, rolling screen content, moire patterns, and dynamic foreground motion inside the display. Many video demoireing and restoration papers focus on already cropped or controlled recaptured screen content, while an application pipeline still needs to first locate, rectify, and stabilize the screen plane. This project implements a classical image processing pipeline for that missing front-end stage. The system detects or manually initializes the screen quadrilateral, warps each frame to a fixed 16:9 screen coordinate system using a homography, tracks a reference screen plane with Lucas-Kanade optical flow, estimates frame homographies with RANSAC, rejects unreliable updates with geometric gates, interpolates missing observations, smooths the corner trajectory, and optionally applies residual affine stabilization after rectification. Experiments on six local filmed-screen videos show that reference-plane tracking greatly improves clean static cases, remains useful under screen-internal video motion, and exposes clear failure boundaries on a 4K moire-heavy hard case. The best static sample reduces last-two-second residual translation p95 from 1.423 px with per-frame detection to 0.078 px with reference tracking. Dynamic content cases show that residual motion metrics must be interpreted carefully because scrolling pages and played videos are real screen content, not only camera shake. The final system is therefore best understood as a practical preprocessing chain for video demoireing, OCR, archiving, and visual inspection, rather than as a complete restoration model.

## 1. Introduction

Filming a computer screen with a mobile phone is common in real usage: users record online lectures, dashboards, code, videos, chat windows, or error states when direct screen recording is not available. The captured video is usually geometrically degraded before any image restoration problem begins. The camera sees not only the screen content, but also the surrounding desk or wall. The screen is tilted, the four corners are not aligned to the image axes, and handheld motion introduces small frame-to-frame translation, rotation, scale, and perspective changes.

This project addresses the application-side preprocessing problem:

```text
handheld filmed screen video
  -> screen region detection
  -> perspective rectification
  -> reference-plane tracking
  -> temporal stabilization
  -> screen-coordinate video for restoration/OCR/archive
```

The project does not directly remove moire patterns, enhance colors, or recover lost detail. Instead, it normalizes the geometry so that later video demoireing or recognition modules can operate on a stable screen-coordinate input. This positioning also explains why the project uses classical geometry and tracking methods instead of training a deep restoration network.

## 2. Related Work

Video stabilization commonly estimates camera motion, smooths motion trajectories, and warps frames to remove high-frequency shake. Classical pipelines use feature detection, KLT tracking, robust motion estimation, and trajectory smoothing. The reference final report in the course material follows this general structure for video stabilization, but its target is unconstrained natural video. Our task is narrower: the dominant object is a planar display, so a homography is an appropriate geometric model.

The implementation is also motivated by homography-based stabilization work such as Cinematic-L1 video stabilization with a log-homography model. That paper supports the idea that homography trajectories can be optimized or smoothed over time for visually stable video. In our project, the optimization is simpler and more practical for a course project: we track a reference screen plane, reject bad homography updates, interpolate missing corner observations, and apply moving-window smoothing.

Recent video demoireing papers, including relation-based temporal consistency methods, direction-aware temporal-guided methods, and recaptured raw screen image/video demoireing, show the importance of temporal consistency for screen restoration. However, those restoration pipelines often assume the screen content is already captured or aligned in a controlled way. This project fills the earlier application step: turning a real camera video of a physical monitor into a rectified and stabilized screen-content video.

## 3. Problem Definition

The input is a video of a monitor captured by a phone or camera. The output is a fixed-resolution screen video, by default 1920x1080, where screen content is mapped to a frontal 16:9 canvas.

The pipeline should:

- remove most off-screen background;
- correct perspective distortion with a planar homography;
- keep the screen boundary and static UI structure stable over time;
- preserve real screen content changes, including scrolling, mouse movement, playback, and subtitles;
- avoid letting dynamic screen content dominate the estimated screen plane.

The hard cases are:

- screen corners or borders are weak, missing, or reflective;
- low-texture white pages produce too few reliable feature points;
- scrolling or played video creates many moving features inside the screen;
- 4K capture and moire patterns damage local texture consistency;
- residual stabilization may confuse real screen content motion with camera shake.

## 4. Method

### 4.1 Screen Initialization

The first frame is used to initialize the screen quadrilateral. The automatic detector searches for a plausible large quadrilateral using color/edge/contour cues and rejects candidates whose area, aspect ratio, or position is unreasonable. If the automatic detector fails, the command-line interface supports manual corner input in TL, TR, BR, BL order:

```bash
uv run scripts/normalize_screen.py inputs/my_video.mp4 \
  --corners "x1,y1:x2,y2:x3,y3:x4,y4"
```

### 4.2 Perspective Rectification

For each frame, the four screen corners define a homography from camera coordinates to the target screen canvas. Warping the frame by this homography removes perspective tilt and most surrounding background:

```text
source screen quadrilateral -> fixed rectangular screen canvas
```

This stage is the geometric foundation for the entire project. Without it, downstream demoireing or OCR would receive a moving, tilted, and background-contaminated input.

### 4.3 Reference-Plane Tracking

The recommended tracker is `reference`. It locks the screen plane to the first frame and updates the plane over time:

1. Detect stable feature points on the reference screen plane.
2. Track points with Lucas-Kanade optical flow.
3. Estimate a homography with RANSAC.
4. Reject the update if inliers, inlier ratio, reprojection error, feature coverage, side-length change, or area change are unreliable.
5. Refresh features when needed.

This is different from plain optical flow. Plain flow only propagates corners frame to frame and can drift with dynamic content. The reference tracker keeps all frames tied to a common reference plane and uses gates to prevent bad updates from entering the corner trajectory.

### 4.4 Trajectory Interpolation and Smoothing

After tracking, the system performs offline trajectory refinement. Observations with sudden side-length or area jumps are treated as unreliable. Rejected frames are interpolated between reliable neighbors when possible, then the corner trajectory is smoothed with a temporal window. Conceptually, this suppresses high-frequency estimation noise while preserving the low-frequency camera/screen motion trend.

### 4.5 Optional Residual Alignment

After perspective rectification, the pipeline can estimate a small residual affine motion relative to the first rectified frame:

```bash
uv run scripts/normalize_screen.py inputs/my_video.mp4 \
  --tracker reference \
  --reference-align \
  --reference-motion affine
```

This stage is guarded by a whole-video accept-ratio check. If too few residual alignments are reliable, it is disabled to avoid over-correcting real screen content motion. In the experiments, residual alignment helps less than expected on dynamic samples, which is an important negative result.

## 5. Dataset

The experiments use six local input videos in `inputs/`:

| Video | Resolution | FPS | Duration | Role |
| --- | ---: | ---: | ---: | --- |
| `静止网页.mp4` | 1920x1080 | 30 | 6.12 s | Clean static page; main success case |
| `滚动网页.mp4` | 1920x1080 | 30 | 5.58 s | Scrolling page; dynamic UI content |
| `运动视频.mp4` | 1920x1080 | 30.09 | 5.15 s | Large screen-internal video motion |
| `testmoire.mp4` | 3840x2160 | 30 | 7.34 s | 4K moire hard case |
| `VID20260621024117.mp4` | 1920x1080 | 60 | 5.27 s | Existing stable 60fps baseline |
| `VID20260621031719.mp4` | 1920x1080 | 60 | 9.64 s | Existing dynamic hard case |

The set covers static, scrolling, internal motion, high-resolution moire, and 60fps samples. The videos are local and ignored by git; every experiment is traceable through the run names and CSV/JSON outputs in `runs/`.

## 6. Experiments

### 6.1 Evaluation Protocol

Each normalized output is analyzed with adjacent-frame affine motion estimation:

```bash
uv run scripts/analyze_stability.py runs/<normalize-run>/<output-video>.mp4 \
  --run-name analyze_<normalize-run>
```

The main reported metrics are:

- last-two-second residual translation p95 in pixels;
- last-two-second residual absolute rotation p95 in degrees;
- last-two-second residual absolute scale-delta p95;
- tracker rejected frame count;
- median tracker inliers and inlier ratio for reference-tracking runs.

These metrics are useful but not perfect. When the screen content itself scrolls or plays a video, adjacent-frame image motion includes real content motion. Therefore, the numbers must be interpreted together with tracker debug logs and visual inspection.

### 6.2 Ablation on Three Core Videos

| Scenario | Method | Run | Last-2s trans. p95 | Rot. p95 | Scale p95 | Rejected frames | Median inliers | Median inlier ratio |
| --- | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |
| Static page | detect | `ablation_static_detect` | 1.423 | 0.0073 | 0.001251 | n/a | n/a | n/a |
| Static page | flow | `ablation_static_flow` | 1.068 | 0.0133 | 0.000510 | n/a | n/a | n/a |
| Static page | reference | `main_static_page` | 0.078 | 0.0015 | 0.000079 | 0 | 1000 | 1.000 |
| Static page | reference+align | `ablation_static_reference_align` | 0.155 | 0.0047 | 0.000102 | 0 | 1000 | 1.000 |
| Scrolling page | detect | `ablation_scroll_detect` | 1.528 | 0.0298 | 0.000698 | n/a | n/a | n/a |
| Scrolling page | flow | `ablation_scroll_flow` | 4.484 | 0.0171 | 0.000884 | n/a | n/a | n/a |
| Scrolling page | reference | `main_dynamic_scroll_page` | 1.593 | 0.0082 | 0.000777 | 132 | 0 | 0.000 |
| Scrolling page | reference+align | `ablation_scroll_reference_align` | 1.593 | 0.0082 | 0.000777 | 132 | 0 | 0.000 |
| Screen video | detect | `ablation_screenvideo_detect` | 4.543 | 0.0110 | 0.000941 | n/a | n/a | n/a |
| Screen video | flow | `ablation_screenvideo_flow` | 3.257 | 0.0113 | 0.000777 | n/a | n/a | n/a |
| Screen video | reference | `main_dynamic_screen_video` | 3.252 | 0.0066 | 0.000748 | 0 | 817 | 0.995 |
| Screen video | reference+align | `ablation_screenvideo_reference_align` | 3.252 | 0.0066 | 0.000748 | 0 | 817 | 0.995 |

On the static page, reference tracking is clearly best: translation p95 drops from 1.423 px with per-frame detection to 0.078 px. This supports the main design choice that the screen should be tracked as a reference plane rather than redetected independently every frame.

On the scrolling page, plain flow has the worst translation p95 because it follows moving page content. Reference tracking rejects many updates and keeps rotation lower than detection. This is a mixed result: the geometry gate prevents unsafe updates, but the residual translation metric is still influenced by real scrolling motion.

On the screen-video sample, reference tracking reduces residual rotation and keeps a strong inlier set. The translation metric remains high because the video content itself is moving. This confirms the need to separate camera/screen-plane motion from screen-internal content motion in both the algorithm and the evaluation.

### 6.3 Main Results on Additional Cases

| Scenario | Method | Run | Last-2s trans. p95 | Rot. p95 | Scale p95 | Rejected frames | Median inliers | Median inlier ratio |
| --- | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |
| 4K moire hard case | reference | `main_dynamic_testmoire` | 3.409 | 0.0480 | 0.001885 | 220 | 0 | 0.000 |
| 60fps baseline | reference | `main_vid_024117` | 0.118 | 0.0044 | 0.000118 | 0 | 813 | 0.999 |
| 60fps dynamic hard case | reference | `main_dynamic_vid_031719` | 0.919 | 0.0194 | 0.000424 | 0 | 669 | 0.986 |

The 60fps baseline is a strong positive case, with translation p95 of 0.118 px and a median inlier ratio of 0.999. The 60fps dynamic hard case is less stable but still trackable, with median inlier ratio of 0.986.

The 4K moire case is the main failure case. The tracker rejects almost all updates and the median inlier count is zero. This does not mean the application direction is invalid; it means the current classical feature tracker is not robust enough for this condition. A better final system would need stronger screen-border detection, moire-aware feature selection, manual corner refinement, or a learned correspondence module.

## 7. Failure Analysis

The experiments show four important limitations.

First, dynamic screen content can dominate residual motion metrics. A scrolling web page and a playing video contain legitimate motion inside the screen. Adjacent-frame affine analysis can count this as residual motion even when the screen plane is geometrically stable. This is why debug evidence such as tracker inliers, rejection reasons, and visual inspection must accompany the metric table.

Second, the current automatic detector and reference tracker depend on usable screen texture and borders. The 4K moire sample leaves too few reliable feature correspondences, causing the tracker to reject almost all updates. This is the clearest boundary of the current method.

Third, residual alignment is not automatically beneficial. It improves only when the rectified screen has stable shared features across time. For scrolling and played-video samples, the global accept-ratio gate correctly prevents most residual corrections. Applying residual alignment blindly would risk stabilizing the content motion instead of the camera motion.

Fourth, this project does not remove moire or restore damaged image content. Even a geometrically stable output may still contain moire, blur, exposure problems, and compression artifacts. Those belong to the downstream restoration stage.

## 8. Discussion

The strongest story for this project is not "we built a full screen restoration app." The stronger and more defensible story is:

> Existing screen demoireing and short-video restoration methods often study controlled or already aligned screen content. In real usage, a phone first captures a whole physical scene. This project implements the missing preprocessing chain: screen localization, perspective normalization, reference-plane tracking, and temporal stabilization.

This also explains the relationship between this project and the cited video demoireing work. Demoireing models can remove interference patterns after the screen content is already well framed. Our system prepares that input by reducing geometric variation. The two stages are complementary.

The results also justify keeping SuperPoint + LightGlue as optional future work rather than the main contribution. The current classical method is interpretable, fast enough for short experiments, and produces useful debug evidence. Learned matching may help the 4K moire failure case, but it would need its own evaluation and is not required to prove the core application chain.

## 9. Conclusion

This project implements and evaluates a practical preprocessing pipeline for filmed screen videos. The system converts a handheld camera view of a monitor into a rectified and temporally stabilized screen-coordinate video using homography rectification, LK reference tracking, RANSAC, geometric gating, interpolation, and smoothing.

The experiments support three conclusions:

1. Reference-plane tracking is clearly better than per-frame detection on clean static screen videos.
2. Dynamic screen content requires gated reference tracking; plain flow can drift with the content.
3. 4K moire-heavy videos expose the current method's feature-tracking boundary and motivate future learned matching or border-aware refinement.

The final output is a credible application-side front end for video demoireing, OCR, archiving, or human inspection. It completes the preprocessing part of a realistic filmed-screen restoration chain.

## Reproducibility

The main commands used in the final experiments are documented in `run_manifest.md`. Raw input videos and generated videos are local artifacts under `inputs/` and `runs/` and are intentionally not committed to git. The committed summary table is `experiment_summary.csv`; every row lists the normalization run and the stability-analysis run that produced the reported metrics.

## References

1. Lucas, B. D., and Kanade, T. "An Iterative Image Registration Technique with an Application to Stereo Vision." 1981.
2. Shi, J., and Tomasi, C. "Good Features to Track." 1994.
3. Bouguet, J.-Y. "Pyramidal Implementation of the Lucas Kanade Feature Tracker."
4. Torr, P. H. S., and Zisserman, A. "MLESAC: A New Robust Estimator with Application to Estimating Image Geometry." 2000.
5. Grundmann, M., Kwatra, V., and Essa, I. "Auto-Directed Video Stabilization with Robust L1 Optimal Camera Paths." CVPR 2011.
6. Goldstein, A., and Fattal, R. "Video Stabilization using Epipolar Geometry." and related homography-based stabilization literature.
7. "Cinematic-L1 Video Stabilization with a Log-Homography Model." WACV 2021.
8. "Video Demoireing with Relation-Based Temporal Consistency." CVPR 2022.
9. "Direction-aware Video Demoireing with Temporal-guided Bilateral Learning." AAAI 2024.
10. "Recaptured Raw Screen Image and Video Demoireing via Channel and Spatial Modulations." NeurIPS 2023.
