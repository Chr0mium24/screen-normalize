---
title: "Screen Capture Rectification and Temporal Stabilization for Real-World Captured-Screen Videos"
author:
  - "Rongshuo Wen (124020369)"
  - "Bihua Wen (124090670)"
  - "Mingrui Liu (124090375)"
date: "ECE4512 Final Project, 2026"
lang: en-US
geometry: margin=22mm
fontsize: 10pt
papersize: a4
header-includes:
  - |
    ```{=latex}
    \usepackage{booktabs}
    \usepackage{microtype}
    ```
---

# Abstract

Videos of computer displays are commonly captured with handheld phones when direct screen recording is unavailable or inappropriate. The resulting footage contains background clutter, projective distortion, camera shake, weak screen boundaries, and screen content that may scroll or play independently of the camera. These effects must be separated before downstream tasks such as screen-content restoration or demoiréing can operate on a stable screen-coordinate signal. This paper presents a classical computer-vision pipeline that detects or initializes a screen quadrilateral, tracks the screen plane against a fixed reference using pyramidal Lucas--Kanade features and a RANSAC homography, rejects geometrically unreliable updates, repairs and smooths the corner trajectory, and renders a frontal video with optional residual alignment. The evaluation protocol compares frame-wise detection, adjacent-frame optical flow, and the proposed reference-anchored pipeline on a planned 50-clip dataset spanning five real-world scenarios. Geometry, temporal stability, detail preservation, and frequency-domain behavior are evaluated separately so that improved stability is not conflated with sharpness or moiré removal. On the completed formal dataset, the proposed method achieves **[TBD-GEOMETRY]** corner error, **[TBD-TEMPORAL]** residual translation, and **[TBD-DETAIL]** edge preservation, compared with **[TBD-BASELINES]** for the two baselines. These results will determine whether the additional robustness stages improve screen-plane stability without unacceptable geometric or resampling cost.

**Keywords:** screen rectification; video stabilization; homography; optical flow; captured-screen video; projective geometry

# 1. Introduction

Recording a physical display with a handheld camera is a simple way to preserve a presentation, demonstrate software, or document content on a device that cannot be directly recorded. Unlike a native screen recording, however, a camera observation includes the display's surroundings and is affected by viewpoint, lens sampling, hand motion, glare, partial occlusion, and exposure changes. The output is therefore neither a conventional scene video nor a clean screen capture. A useful front end must first identify the screen plane, remove its perspective distortion, and produce a temporally stable coordinate system.

Captured-screen restoration and demoiréing research establishes the importance of recovering content degraded by the interaction between a display and a camera. Such restoration is easier to define once the screen region is cropped or aligned. In an uncontrolled user video, that assumption is itself a substantial preprocessing problem: the visible content may scroll, animate, or play a video while the physical display moves only because of the camera. A tracker that follows all interior texture can confuse content motion with screen motion. Conversely, detecting the screen independently in every frame can convert small detection errors into visible jitter.

This work studies the missing geometric front end. We model the display as a planar quadrilateral and estimate a screen-to-image homography over time. The implemented pipeline anchors tracked features to a fixed reference screen plane rather than accumulating only adjacent-frame motion. Forward--backward flow, RANSAC support, reprojection error, spatial coverage, and quadrilateral-change gates determine whether an update is usable. Rejected observations do not immediately alter the output trajectory: the system holds the last accepted geometry online, then applies offline interpolation and robust temporal filtering before rendering. A bounded residual-alignment stage compensates for small motion that remains after the main warp.

The contributions of the project are:

1. a reproducible end-to-end workflow from full-scene video and sparse four-corner annotations to rectified video, structured metrics, and per-clip audit reports;
2. a reference-anchored screen-plane tracker with explicit acceptance diagnostics, failure holding, trajectory repair, and temporal smoothing;
3. a controlled comparison with frame-wise detection and adjacent-frame optical-flow baselines across five planned scene categories; and
4. an evaluation protocol that separates geometric accuracy, temporal variation, aligned detail preservation, and frequency diagnostics.

The current implementation should not be interpreted as a demoiréing system. It performs geometric normalization and resampling, and its Fourier analysis reports directional regularity and high-frequency changes only. It also differs from the original proposal in one important respect: physical border lines do not yet provide the primary per-frame motion estimate. This boundary is retained throughout the paper so that experimental claims remain consistent with executable code.

# 2. Related Work

## 2.1 Captured-screen restoration

Recent video demoiréing work treats camera-captured displays as a restoration problem. Dai *et al.* construct spatially and temporally aligned captured/clean videos and learn relation-based temporal consistency [16]. Xu *et al.* combine direction-aware frequency processing, alignment, color correction, and detail refinement [17]. Yue *et al.* study raw-domain screen recapture and build aligned raw image and video data [18]. These methods address moiré removal and content restoration after controlled acquisition and alignment. Our task is complementary: it starts from a full handheld scene and produces the frontal screen-coordinate video that a restoration model could consume. The distinction also explains why the present FFT measurements are diagnostics rather than demoiréing scores.

## 2.2 Planar document and screen rectification

A planar surface observed by a perspective camera is related to a frontal coordinate system by a homography. Camera-based document analysis has consequently used page boundaries, layout cues, text structure, and vanishing points to recover frontal document views [1--4]. Jagannathan and Jawahar organize perspective correction around the available geometric evidence, while Yin *et al.* combine line information and vanishing-point detection for mobile document images [1,2]. Williem *et al.* emphasize computationally efficient boundary extraction and robust rectification on smartphones [3]. Screen--camera calibration likewise treats the screen as a planar projective surface, although controlled projected patterns provide evidence unavailable in ordinary handheld recordings [4].

These methods support the geometric model used here, but most address a single image or a controlled calibration sequence. Applying independent image rectification to video does not guarantee that the estimated quadrilateral varies smoothly. The present task therefore adds tracking, rejection, and temporal trajectory processing to planar rectification.

## 2.3 Line and vanishing-point evidence

Physical display borders and interface lines are useful because a frontal rectangular screen contains two approximately orthogonal direction families. The Line Segment Detector (LSD) provides a parameter-controlled method for extracting line segments [5], while vanishing-point methods group line evidence to infer scene directions [6]. Such evidence motivates the border-guided design in the project proposal. The current system uses contour-based initialization and line-based residual roll correction; full border-dominant motion estimation remains future implementation work. We therefore do not attribute current results to an LSD/Hough border tracker.

## 2.4 Feature tracking and robust homography estimation

Lucas and Kanade formulate image registration as an iterative alignment problem [7]. The pyramidal implementation extends the usable displacement range by solving from coarse to fine resolution [8]. Shi and Tomasi show that points with well-conditioned local gradients are more reliable for tracking [9]. These ideas underlie OpenCV's pyramidal LK tracker and good-features-to-track detector used in this project.

A homography estimated from tracked points is sensitive to incorrect correspondences. RANSAC-type estimators seek a model supported by an inlier subset; robust alternatives such as MLESAC further formalize model scoring [10]. Our implementation uses RANSAC and supplements it with minimum inlier count, inlier ratio, median reprojection error, screen-plane coverage, and quadrilateral geometry checks. This combination is intended to prevent a compact group of moving content features from controlling the entire screen transform, although formal evaluation on dynamic content is still required.

## 2.5 Video stabilization

Classical video stabilization estimates a camera-motion path, smooths that path, and renders compensated frames. Grundmann *et al.* use robust L1 optimization to encourage simple camera motions [11]. Sánchez compares parametric motion-smoothing strategies and demonstrates that the choice of motion model and temporal filter affects both stability and distortion [12]. Bradley *et al.* formulate stabilization in log-homography space to retain projective motion while imposing cinematic path priors [13]. Evaluation frameworks consequently separate motion stability from cropping and geometric distortion [14].

Our objective is narrower: only the physical screen plane is stabilized, and the target canvas is the screen rectangle itself. This removes the usual background crop trade-off but introduces a different ambiguity between camera motion and dynamic screen content. The present method uses a fixed reference plane and conservative update gates instead of optimizing a general camera path.

# 3. Proposed Processing Pipeline

## 3.1 Overview and notation

Let frame $I_t$ contain an observed screen quadrilateral

$$
Q_t = \{\mathbf{q}_{t,1},\mathbf{q}_{t,2},\mathbf{q}_{t,3},\mathbf{q}_{t,4}\},
$$

ordered as top-left, top-right, bottom-right, and bottom-left. The output rectangle is

$$
R = \{(0,0),(W-1,0),(W-1,H-1),(0,H-1)\}.
$$

The rectifying homography $H_t$ satisfies $\tilde{\mathbf r}_i \sim H_t\tilde{\mathbf q}_{t,i}$ in homogeneous coordinates. The processing sequence is initialization, method-specific trajectory estimation, reliability filtering, temporal repair and smoothing, projective warping, optional residual alignment, and video encoding. **[FIGURE 1 ABOUT HERE]**

## 3.2 Screen initialization

The first screen quadrilateral is supplied manually or detected automatically. Automatic initialization converts the frame to HSV, thresholds a configurable color range, applies morphological closing and opening, selects the largest sufficiently large contour, and searches polygonal approximations for a valid convex quadrilateral. The result is ordered and checked for image bounds, convexity, area, and plausible geometry. This detector is deliberately lightweight and is not expected to cover every display appearance. A validated manual initialization remains available for difficult clips.

The formal annotation tool is separate from initialization. It records sparse ground-truth corners in a CSV file with columns `frame, tl_x, tl_y, ..., bl_y`; these labels are used for evaluation and are not silently injected into automatic runs.

## 3.3 Baseline trajectories

**Frame-wise detection** applies screen detection independently at each frame and does not use cross-frame smoothing. It measures how much temporal inconsistency is introduced when every frame is treated as an unrelated image.

**Optical-flow tracking** propagates screen geometry from the preceding frame using interior features. When a new detection is available, a small correction can be blended with the flow prediction. Because this baseline follows adjacent content, scrolling or video playback may bias the transform and accumulate drift.

Both baselines use the same output resolution, warping implementation, encoding settings, and metric code as the proposed method.

## 3.4 Reference-anchored tracking

The proposed implementation detects Shi--Tomasi features inside an eroded screen mask and stores their positions in a reference frame. For each subsequent frame, pyramidal LK flow predicts new positions. A backward flow from the current frame to the preceding frame yields the round-trip error

$$
e_i^{\mathrm{fb}} = \left\|\mathbf p_{t-1,i}-\hat{\mathbf p}_{t-1,i}\right\|_2.
$$

Only points with successful forward and backward status and $e_i^{\mathrm{fb}}<\tau_{\mathrm{fb}}$ remain candidates. Points must also survive a minimum age before contributing to the homography. This prevents newly inserted points from immediately changing the screen plane.

The current-to-reference homography $G_t$ is estimated with RANSAC from mature correspondences. A candidate is accepted only if it satisfies thresholds on inlier count, inlier ratio, median reprojection error, and horizontal and vertical inlier coverage. The inverse transform maps the reference quadrilateral into the current frame:

$$
Q_t = G_t^{-1} Q_0.
$$

Finally, the quadrilateral must remain convex, inside the frame, and within maximum scale and area changes relative to the last accepted state. Accepted transforms are also used to reject high-reprojection-error tracks and to add fresh points while retaining their reference coordinates.

## 3.5 Failure handling and trajectory repair

If flow fails, too few mature tracks remain, RANSAC fails, support is spatially concentrated, reprojection error is excessive, or the predicted quadrilateral is implausible, the online tracker appends the last accepted corners. This hold behavior avoids a sudden warp generated from an unsupported estimate. Every frame records its acceptance state and rejection reason in `debug.csv`.

After the full trajectory is available, a second geometry gate checks scale and area changes between reliable observations. Rejected positions are replaced by linear interpolation between reliable corner coordinates. Endpoint gaps use the nearest reliable state. This repair converts isolated failures into a continuous trajectory but cannot reconstruct motion across a long unobserved interval; such intervals must be inspected as failure cases.

## 3.6 Temporal smoothing and residual alignment

The repaired corner trajectory is filtered first by a centered median window and then by a centered moving average:

$$
\bar{Q}_t = \frac{1}{2k+1}\sum_{j=-k}^{k} Q'_{t+j},
$$

with endpoint replication. The median stage limits isolated corner jumps; the average suppresses remaining high-frequency variation. The formal experiment must report the chosen windows and include a no-smoothing ablation because a temporal metric derived from the same trajectory can otherwise favor smoothing by construction.

After the main projective warp, an optional residual stage tracks features in the normalized frame against a reference normalized image. Only small translation, rotation, and scale corrections passing support, coverage, and reprojection gates are retained. Corrections are step-limited and smoothed; the entire residual stage is disabled when its whole-video acceptance ratio is below a threshold. Stable horizontal interface lines may additionally estimate a bounded roll correction. These secondary corrections are diagnostic and conservative rather than substitutes for correct screen-plane tracking.

## 3.7 Rendering

Each smoothed quadrilateral is mapped to a fixed $W\times H$ canvas with a perspective transform. Optional fractional crops remove unreliable boundary pixels. Frames are encoded with H.264 settings shared by all methods, and the source audio is muxed into the final video. The pipeline writes `normalized.mp4`, `estimated_corners.csv`, `debug.csv`, `method.json`, metric JSON/CSV files, visual diagnostics, and a static audit report for every clip.

# 4. Dataset and Annotation Protocol

## 4.1 Planned data collection

The formal dataset is designed to contain 50 approximately five-second handheld videos, organized into five categories with ten clips each:

1. **Static:** webpages, PDF pages, or other fixed content;
2. **Scrolling:** vertically or horizontally moving pages;
3. **Screen video:** independently moving video content inside the display;
4. **Weak border:** slides or low-contrast scenes in which the physical boundary is difficult to distinguish; and
5. **Hard:** glare, high-frequency interference, partial screen loss, or other severe conditions.

Category is determined by the containing directory and the filename is the clip identifier. Resolution, frame rate, duration, device, illumination, and difficulty labels are not manually curated dataset metadata. Video properties may be read during decoding only as operational values. At the time of this pre-results draft, formal collection is **[TBD-DATASET-STATUS]** complete. **[FIGURE 2 ABOUT HERE]**

## 4.2 Corner annotations

Selected keyframes are annotated with the four visible screen corners in TL/TR/BR/BL order. The annotation tool loads existing CSV files, supports correction and deletion, validates coordinate bounds and convex non-degenerate geometry, and writes atomically. The final report must state the sampling interval, total number of annotated frames, number of annotators, and any repeated-annotation quality check: **[TBD-ANNOTATION-PROTOCOL]**.

Annotations are used for geometry evaluation and for constructing a same-coordinate, same-scale reference in detail evaluation. No manually defined texture region of interest is required; the normalized image boundary is excluded automatically.

# 5. Experimental Design

## 5.1 Compared methods

The three compared configurations are fixed before the formal run:

- **Frame-wise:** independent detection; no cross-frame trajectory smoothing.
- **Optical flow:** adjacent-frame feature propagation without reference anchoring, offline recovery, or residual alignment.
- **Proposed:** reference-anchored tracking, reliability gates, hold/interpolation recovery, median-plus-average trajectory smoothing, and bounded residual alignment.

All methods process the same clips and use the same canvas, encoder, annotated frames, and evaluation functions. Formal parameter values are inserted from `method.json`: **[TBD-PARAMETER-TABLE]**.

## 5.2 Geometry

For a matched annotated frame with predicted corners $\hat{\mathbf q}_i$ and ground truth $\mathbf q_i$, corner RMSE is

$$
E_c = \sqrt{\frac{1}{4}\sum_{i=1}^{4}\left\|\hat{\mathbf q}_i-\mathbf q_i\right\|_2^2}.
$$

Quadrilateral intersection over union is $\mathrm{IoU}=|P\cap G|/|P\cup G|$. Aspect ratio is computed from the mean top/bottom width divided by the mean left/right height; absolute and relative errors are reported. Results are aggregated over matched keyframes, by category and overall.

## 5.3 Temporal stability

The implemented metric decomposes the frame-to-frame projective change of the estimated screen quadrilateral into translation magnitude, rotation, and scale change. Per-frame series and mean, median, 95th percentile, and maximum absolute values are stored. This avoids measuring optical flow directly on dynamic screen pixels, but it is not independent of each method's estimated trajectory. Therefore, the main temporal claim must be corroborated by annotated geometry over time, a fixed physical screen structure, or an external residual measure before final submission. The report will use **[TBD-FINAL-TEMPORAL-DEFINITION]** as the primary definition and retain trajectory variation as a diagnostic if independence cannot be established.

## 5.4 Detail preservation

At annotated frames, the original image is warped using ground-truth corners to the exact output coordinate system. The normalized method output and this reference are compared at equal dimensions after excluding the outer boundary. Average Sobel gradient magnitude measures retained local contrast. Canny edge maps are dilated by one pixel to tolerate small registration errors; precision and recall are combined as an edge-preservation F1 score. Frames without a valid aligned reference are skipped rather than compared at inconsistent scale.

## 5.5 Frequency diagnostics

Sampled normalized frames are mean-centered, multiplied by a Hann window, and transformed with a two-dimensional FFT. After suppressing the direct-current neighborhood, high-magnitude frequency points vote in a 180-bin angular histogram. The primary direction and the strongest direction near its orthogonal complement define orthogonality and axis-alignment errors. These values characterize direction regularity after resampling. They do not quantify moiré removal and are interpreted alongside spectra and image crops rather than as a quality score with a universal optimum.

## 5.6 Runtime, subsets, and statistical reporting

Temporal evaluation and method success rate use all formal clips. Geometry uses every annotated keyframe. Any texture-rich detail subset, high-frequency subset, qualitative examples, or ablation subset is fixed before inspecting final results and listed in **[TBD-SUBSET-DEFINITION]**. For each metric, the paper reports sample count, mean and standard deviation or median and interquartile range according to distribution, plus per-clip points. Paired comparisons are used because all methods process the same clips. Statistical tests and confidence intervals, if used, are specified after checking distributional assumptions and are not added solely to decorate small pilot samples.

The formal environment is **[TBD-HARDWARE]**, with Python **[TBD]**, OpenCV **[TBD]**, NumPy **[TBD]**, and FFmpeg **[TBD]**. Processing time excludes manual annotation and includes **[TBD-RUNTIME-BOUNDARY]**.

# 6. Results

> This section is structurally complete but intentionally contains no invented formal result. Replace every bracketed item from one reviewed formal run.

## 6.1 Run completeness and success rate

The formal run processed **[TBD-N-CLIPS]** clips and **[TBD-N-FRAMES]** frames. Frame-wise, Optical flow, and Proposed completed **[TBD-SUCCESS-FW]**, **[TBD-SUCCESS-OF]**, and **[TBD-SUCCESS-PR]** clips, respectively. Failures were defined before aggregation as **[TBD-SUCCESS-CRITERION]**. The distribution across the five categories is shown in **[TABLE/FIGURE TBD]**.

## 6.2 Geometry accuracy

Across **[TBD-N-ANNOTATED]** annotated keyframes, the Proposed method obtained a corner RMSE of **[TBD] px**, quadrilateral IoU of **[TBD]**, and relative aspect-ratio error of **[TBD]%**. The corresponding Frame-wise values were **[TBD]**, **[TBD]**, and **[TBD]**, while Optical flow obtained **[TBD]**, **[TBD]**, and **[TBD]**. The category-level results indicate **[TBD-DIRECTIONAL-FINDING]**. Any claim of improvement will be stated with paired uncertainty and the number of matched frames, not only the aggregate mean. **[FIGURE 3 AND TABLE 1 ABOUT HERE]**

## 6.3 Temporal stability

Under the final independent temporal definition, residual translation, rotation, and scale variation were **[TBD]**, **[TBD]**, and **[TBD]** for Proposed, compared with **[TBD]** for Frame-wise and **[TBD]** for Optical flow. Per-frame curves show **[TBD-CURVE-OBSERVATION]**. The largest method difference occurred in **[TBD-CATEGORY]**, whereas **[TBD-CATEGORY]** remained difficult because **[TBD-CAUSE]**. Trajectory-derived values are reported separately to avoid presenting smoothing of the estimator as independent evidence of physical stabilization. **[FIGURE 4 AND TABLE 2 ABOUT HERE]**

## 6.4 Detail and frequency behavior

On **[TBD-N-DETAIL]** aligned frames, average gradient ratio and edge-preservation index were **[TBD]** and **[TBD]** for Proposed. Relative to the baselines, this represents **[TBD-NEUTRAL-COMPARISON]**. Local crops show whether the measured difference reflects preserved glyph edges, interpolation blur, or small alignment error. **[FIGURE 6A--B AND TABLE 3 ABOUT HERE]**

For the predefined frequency subset, the post-rectification direction and orthogonality statistics were **[TBD]**. Spectrum examples show **[TBD-DIAGNOSTIC-OBSERVATION]**. These measurements are reported as consequences of geometric normalization and resampling; they are not evidence of moiré suppression. **[FIGURE 6C AND TABLE 4 ABOUT HERE]**

## 6.5 Ablation and failure cases

Removing consistency/reliability gates changed **[TBD-METRIC]** from **[TBD]** to **[TBD]**; removing trajectory smoothing changed it to **[TBD]**; removing failure recovery changed it to **[TBD]**. Because the current implementation does not contain the proposal's explicit border-versus-content consistency module, the final ablation name must match the code actually run. **[FIGURE 7 AND TABLE 5 ABOUT HERE]**

Manual audit identified **[TBD-N-FAILURES]** representative failure modes: **[TBD-FAILURE-1]**, **[TBD-FAILURE-2]**, and **[TBD-FAILURE-3]**. Each case is linked to tracker rejection diagnostics and a visible output defect. **[FIGURE 8 ABOUT HERE]**

# 7. Discussion

## 7.1 Interpretation framework

The central question is not whether the corner trajectory can be made numerically smooth; a sufficiently strong filter can always reduce its high-frequency variation. The useful question is whether the stabilized output remains geometrically correct while dynamic screen content, weak evidence, and temporary tracking failures are present. Geometry and detail results therefore constrain the interpretation of temporal gains. A method is preferable only when reduced residual motion does not arise from freezing an incorrect quadrilateral or over-smoothing genuine camera movement.

If the formal results show an advantage over frame-wise detection, the likely mechanism is the use of a persistent reference plane and rejection of isolated detections. If the advantage is primarily over adjacent optical flow in scrolling and screen-video categories, that pattern would support the hypothesis that reference anchoring and mature-track gates reduce contamination by newly appearing content. These mechanisms should be claimed only when category-level results and ablations agree.

Frequency results require a different interpretation. A smaller axis-alignment error can be an expected consequence of rectifying a rectangular display, while high-frequency energy may increase or decrease according to interpolation, scale, and the original sampling pattern. Neither direction alone defines better visual quality. Any visible moiré change belongs in a descriptive failure or diagnostic analysis unless paired clean-screen references and a dedicated restoration metric are introduced.

## 7.2 Limitations

First, the planned dataset is small and collected by the project team. It can test controlled engineering hypotheses but cannot establish broad device or display generalization. Second, automatic initialization is based on a simple appearance-specific contour detector; invisible borders, severe glare, occlusion, and partial screen loss can produce a wrong first plane. Third, current reference tracking still uses interior image features. Dynamic content is mitigated by reference anchoring, point age, RANSAC, and coverage gates, but it is not explicitly separated using independently tracked physical borders as proposed originally.

Fourth, online failure handling holds the last accepted geometry and offline interpolation assumes that neighboring reliable states are informative. Long failures or rapid camera motion violate that assumption. Fifth, the residual-alignment stage can compensate for small errors but may also follow content if its gates are insufficient. Sixth, the present trajectory-based temporal metric shares information with the algorithm being evaluated and must not be the sole evidence of stabilization. Finally, every warp resamples the screen image; stability and frontal geometry may be gained at the cost of blur, ringing, or altered high-frequency patterns.

## 7.3 Future work

The most direct extension is to complete the proposal-level border-guided tracker: detect physical borders with LSD/Hough evidence, estimate their intersections and confidence, and use interior features only to test consistency. A learned screen detector could improve initialization while preserving the transparent geometric tracker. Longer occlusions could be handled by an explicit state model rather than linear interpolation. Evaluation should expand across devices, display technologies, viewing distances, and multiple screens, with a held-out protocol and repeated annotations. Finally, this geometric front end can be connected to a dedicated video demoiréing or restoration model, but the two stages should retain separate metrics.

# 8. Conclusion

This project develops a complete engineering path from a handheld full-scene screen video to a frontal, temporally processed screen-coordinate video. The current implementation combines screen-plane initialization, reference-anchored LK tracking, robust homography gates, failure holding, offline repair, temporal filtering, projective rendering, and auditable experiment outputs. It is evaluated against frame-wise detection and adjacent optical flow using separate geometry, temporal, detail, and frequency protocols. Final claims of superiority are deliberately deferred until the planned dataset, annotations, independent temporal measure, and ablations are complete. The resulting system is best understood as a geometric preprocessing front end for later screen-content restoration, not as a demoiréing method itself.

# Data Availability

The formal dataset is being collected for this course project and is not yet released. The final version will state which clips, annotations, representative frames, and derived metrics can be shared, together with any privacy restrictions. Pilot videos are development material and are not part of the formal evidence.

# Code Availability

The implementation is organized as reusable Python modules and `uv`-managed scripts. A formal run produces method outputs, per-frame CSV files, metric JSON files, visual diagnostics, and static HTML audit reports. The final version will provide the repository location, commit identifier, and the reviewed run used for every reported table and figure: **[TBD-CODE-RELEASE]**.

# Author Contributions

Project conception, implementation, data collection, annotation, experiment execution, analysis, visualization, and writing contributions will be recorded here after team review: **[TBD-AUTHOR-CONTRIBUTIONS]**.

# References

1. L. Jagannathan and C. V. Jawahar, “Perspective Correction Methods for Camera-Based Document Analysis,” 2005.
2. X.-C. Yin, J. Sun, S. Naoi, Y. Fujii, and K. Fujimoto, “Perspective Rectification for Mobile Phone Camera-Based Documents Using a Hybrid Approach to Vanishing Point Detection,” 2007.
3. Williem, C. Simon, S. Cho, and I. K. Park, “Fast and Robust Perspective Rectification of Document Images on a Smartphone,” *CVPR Workshops*, 2014.
4. T. Okatani and K. Deguchi, “Autocalibration of a Projector-Screen-Camera System: Theory and Algorithm for Screen-to-Camera Homography Estimation,” *ICCV*, 2003.
5. R. Grompone von Gioi, J. Jakubowicz, J.-M. Morel, and G. Randall, “LSD: A Line Segment Detector,” *Image Processing On Line*, 2012.
6. J. Lezama, G. Randall, and R. Grompone von Gioi, “Vanishing Point Detection in Urban Scenes Using Point Alignments,” *Image Processing On Line*, 2017.
7. B. D. Lucas and T. Kanade, “An Iterative Image Registration Technique with an Application to Stereo Vision,” 1981.
8. J.-Y. Bouguet, “Pyramidal Implementation of the Lucas Kanade Feature Tracker,” Intel Corporation, 2000.
9. J. Shi and C. Tomasi, “Good Features to Track,” *CVPR*, 1994.
10. P. H. S. Torr and A. Zisserman, “MLESAC: A New Robust Estimator with Application to Estimating Image Geometry,” *Computer Vision and Image Understanding*, 2000.
11. M. Grundmann, V. Kwatra, and I. Essa, “Auto-Directed Video Stabilization with Robust L1 Optimal Camera Paths,” *CVPR*, 2011.
12. J. Sánchez, “Comparison of Motion Smoothing Strategies for Video Stabilization Using Parametric Models,” *Image Processing On Line*, 2017.
13. A. Bradley, J. Klivington, J. Triscari, and R. van der Merwe, “Cinematic-L1 Video Stabilization with a Log-Homography Model,” *WACV*, 2021.
14. W. Guilluy, A. Beghdadi, and L. Oudre, “A Performance Evaluation Framework for Video Stabilization Methods,” *EUVIP*, 2018.
15. B. S. Reddy and B. N. Chatterji, “An FFT-Based Technique for Translation, Rotation, and Scale-Invariant Image Registration,” *IEEE Transactions on Image Processing*, vol. 5, no. 8, 1996.
16. P. Dai, X. Yu, L. Ma, B. Zhang, J. Li, W. Li, J. Shen, and X. Qi, “Video Demoireing with Relation-Based Temporal Consistency,” *CVPR*, 2022.
17. S. Xu, B. Song, X. Chen, and J. Zhou, “Direction-Aware Video Demoireing with Temporal-Guided Bilateral Learning,” *AAAI*, 2024.
18. H. Yue, Y. Cheng, X. Liu, and J. Yang, “Recaptured Raw Screen Image and Video Demoiréing via Channel and Spatial Modulations,” *NeurIPS*, 2023.
