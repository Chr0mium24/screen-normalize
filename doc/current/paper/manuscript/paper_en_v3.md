---
title: "Border-Dominated Screen-Plane Normalization for Camera-Captured Screen Videos"
author:
  - "Rongshuo Wen (124020369)"
  - "Bihua Wen (124090670)"
  - "Mingrui Liu (124090375)"
date: "ECE4512 Course Project, 2026"
lang: en-US
geometry: margin=22mm
fontsize: 10pt
papersize: a4
---

# Abstract

Camera-captured screen videos preserve screen content when direct screen recording is unavailable, but the camera view also contains perspective distortion, handheld shake, background interference, weak monitor borders, and independently scrolling or playing content within the screen. This paper investigates geometric screen-plane normalization for such videos. We propose a border-dominated method that uses the physical screen boundary as the primary evidence for homography estimation. Local gradient profiles are sampled near predicted edges, four screen boundary lines are robustly fitted, and their intersections are used to recover the quadrilateral. Geometric gating, fallback strategies, and trajectory filtering are then applied to generate a front-facing screen canvas; LK/RANSAC is used only to assist in diagnosing conflicts caused by internal content motion. On an annotated evaluation subset covering five capture conditions, the method achieves a median corner RMSE of 3.87 px, a median quadrilateral IoU of 0.996, and a median trajectory translation variation of 2.45 px/frame. The results show that physical-border-dominated geometric estimation reduces content-driven drift in the evaluated clips, with the most substantial error reductions occurring in scrolling-page and weak-border clips.

**Keywords:** screen rectification; camera-captured screen video; homography; border detection; optical flow; video stabilization

# 1. Introduction

Camera-captured screen video is a practical alternative for recording classroom content, presentations, meetings, and device outputs. Unlike clean screen recordings, handheld camera videos contain perspective distortion, camera shake, exposure variation, glare, background regions, and partially missing monitor borders. To make downstream reading, recognition, or restoration more reliable, the physical display plane must first be estimated and normalized.

The central difficulty is that the displayed content and the physical screen do not follow the same motion model. Text, webpages, and videos can move within the screen, whereas motion of the monitor itself is caused only by the camera. A tracker that follows internal content may therefore produce a stable but incorrect screen plane. Independent frame-by-frame detection can avoid part of this content-driven drift, but it may introduce jitter and can also fail when borders are weak.

Our method uses the physical border, rather than texture inside the screen, as the primary evidence for screen-plane estimation. Starting from an initial four-corner annotation or detection result, the algorithm searches for boundaries near the predicted screen edges in each frame, fits four boundary lines, and constructs the current quadrilateral from their intersections. Sparse LK/RANSAC tracking is still computed, but its role is to diagnose conflicts between internal content motion and border estimation rather than to replace the border-dominated homography when valid boundary evidence is available.

## 1.1 Related Work

Planar document and screen rectification provide the basic geometric model adopted in this work. Camera-based document analysis commonly uses page boundaries, layout cues, and projective geometry to recover front-facing document views [1-3]. Screen-camera calibration likewise models the display using a planar homography, but controlled calibration patterns provide strong evidence that is unavailable in ordinary handheld video [4]. This work adopts the classical planar homography model. Its focus is not to reintroduce projective geometry, but to select more reliable evidence for the screen plane in uncontrolled camera-captured screen videos.

Feature-based planar tracking provides mature tools for propagating homographies through video. Lucas-Kanade registration and its pyramidal implementation support local feature tracking under moderate motion [5,6], Shi-Tomasi features provide trackable points [7], RANSAC-style estimators handle incorrect correspondences [8], and markerless tracking based on planar scene structure has shown that feature correspondences can support planar target tracking [9]. These methods assume that tracked features move consistently with the target plane. In camera-captured screen videos, however, webpage scrolling or video playback can create strong and stable internal motion, so internal texture cannot always represent the motion of the physical display.

Line-segment and boundary detection constitute another common approach to recovering screen quadrilaterals. LSD extracts line segments directly from images [10], while the Hough transform detects linear structures through voting in parameter space [11]. Both can provide candidate boundaries for rectangular or approximately rectangular objects. We do not claim originality for these detectors themselves. Instead, line and boundary detection are embedded in a local observation procedure constrained by the previous frame's screen geometry: responses consistent with the physical screen boundary are sought only near predicted edges, and gating is used to reject internal text, webpage lines, and background edges.

Video stabilization research emphasizes trajectory smoothing and visual stability, but a smooth camera path does not necessarily imply correct screen geometry [12,13]. Camera-captured screen restoration and video demoiréing methods generally operate after a usable screen region has already been obtained [14-16]; this work addresses the geometric front end that precedes them. Therefore, the novelty of this paper does not lie in the classical components themselves, such as LK, RANSAC, LSD, Hough, or homography estimation, but in their organization under physical-border dominance: border observations determine the quadrilateral, geometric gating and trajectory filtering constrain temporal continuity, and internal feature motion is used only for conflict diagnosis without overriding valid border results.

## 1.2 Main Contributions

This paper makes three contributions. First, it presents a geometric normalization pipeline for camera-captured screen videos in which screen-boundary evidence dominates the screen-plane trajectory, while internal texture provides only auxiliary consistency information. Second, under unified initialization, output-canvas, and evaluation-code settings, it compares frame-by-frame detection, adjacent-frame optical flow, and the border-dominated method in terms of four-corner geometric error, quadrilateral overlap, and trajectory variation. Third, experiments show that the proposed method improves geometric accuracy on the annotated evaluation subset and achieves the largest error reductions in scrolling-page and weak-border clips.

# 2. Proposed Method

## 2.1 Algorithm Overview

The input is a video containing a single planar display, and the output is a video mapped to a fixed front-facing canvas. In each frame, the screen is represented by four corners ordered as top-left, top-right, bottom-right, and bottom-left. The target boundary is the visible active area of the display panel rather than the browser window, internal content edges, or the monitor enclosure. In the current experiments, the four manually annotated corners in frame 0 are used for initialization whenever available, and the automatic detector is called only when they are missing. Because frame 0 is already provided as algorithm input, it is excluded from evaluation. The main evaluation therefore measures continuous screen-plane recovery given an initial quadrilateral.

As shown in Figure 1, the algorithm uses the quadrilateral from the previous frame to predict the four current edges, extracts local border evidence near those predicted edges, fits boundary lines, and intersects them to form a candidate quadrilateral. The trajectory is updated after the candidate passes geometric gating. If it fails, the system successively falls back to redetection and then to the previous-frame result. The complete trajectory is temporally filtered before being mapped to the fixed canvas. Internal LK/RANSAC motion is used only to determine whether screen content motion conflicts with physical-border motion and does not replace a valid border result.

![Figure 1. Border-dominated screen-plane normalization pipeline. Physical-border evidence dominates homography estimation; LK/RANSAC serves only as a consistency diagnostic for internal content-motion conflicts. Missing border evidence triggers redetection or reuse of the previous valid quadrilateral.](figures/figure_01_pipeline.png)

## 2.2 Local Border Observation and Quadrilateral Recovery

The core of the proposed method is to use the previous frame's geometric prior to restrict the border search range. For each predicted edge, the algorithm uniformly selects 50 sampling centers over 4% to 96% of the edge length, avoiding unstable corner regions, and samples grayscale profiles along the normal pointing toward the screen interior. Search radii of 20, 60, and 120 px are used successively, allowing normal jitter to be handled first within a narrow band while still permitting recovery from larger displacement over a wider range. Each profile is obtained by linear resampling, smoothed with a one-dimensional Gaussian filter, and differentiated along the normal direction. For a sampling center $\mathbf p_{i,j}$ on a predicted edge, a unit normal $\mathbf n_i$, and a search radius $r$, the candidate offset is summarized as

$$
s_{i,j}^{*}=\arg\max_{|s|\le r}
\left|g_{i,j}(s)\right|w_d(|s|),
\qquad
\mathbf c_{i,j}=\mathbf p_{i,j}+s_{i,j}^{*}\mathbf n_i,
$$

where $g_{i,j}(s)$ is the one-dimensional gradient of the smoothed profile and $w_d$ is a weight that decreases with distance from the prediction. After the first frame, responses consistent with the recorded border polarity are also prioritized. Unlike searching for arbitrary strong lines across the entire image, this design uses temporal priors to suppress stronger but irrelevant structures such as desk edges, webpage separators, and internal text.

Each edge requires at least eight valid candidate points. The implementation uses the Huber distance in OpenCV `fitLine` to fit a line and iteratively updates inliers for at most four iterations based on the median and MAD of point-to-line distances. The fraction of sampled points classified as inliers is used as edge confidence. Intersections of adjacent fitted lines form the candidate quadrilateral. The estimate is rejected if any edge is missing, adjacent lines are nearly parallel, an intersection is invalid, or the quadrilateral is non-convex. The LSD and Hough ablations replace only the source of candidate line segments; the remaining position, orientation, overlap filtering, and line-fitting procedures are unchanged.

## 2.3 Geometric Gating, Temporal Filtering, and Motion Diagnosis

A candidate quadrilateral first undergoes absolute shape checks: its area must occupy 20% to 85% of the full frame, its aspect ratio must lie between 1.25 and 2.35, and it must remain convex. Relative changes from the previous frame are then checked, requiring each edge-length change to remain below 10% and the area change below 20%. A border candidate is accepted directly if it passes these checks; otherwise, automatic redetection is invoked. Redetection must still satisfy the shape constraints, but the edge-length and area-change thresholds are relaxed to 15% and 30%, respectively. If both procedures fail, the current frame reuses the previous-frame quadrilateral and records that no update was accepted. The current configuration does not apply additional interpolation to these frames. Instead, the full trajectory is processed uniformly by a centered 5-frame median filter followed by a centered 9-frame mean filter to suppress isolated jumps and framewise edge noise.

The fusion of LK/RANSAC and border detection follows a "border decision, LK diagnosis" order rather than a weighted average of two quadrilaterals. Specifically, the system first predicts the current search bands using the previous-frame quadrilateral and generates a candidate quadrilateral from local border observations. Only after the candidate passes edge-confidence, shape, and inter-frame geometric-change gating does it enter the LK consistency check. LK/RANSAC then estimates only the motion of features inside the screen. This mechanism explicitly separates internal content motion from physical screen motion, preventing internal feature motion from being incorrectly interpreted as screen-plane motion.

To diagnose internal content motion, the system selects Shi-Tomasi features inside the previous-frame screen and estimates an internal-motion homography $H_t^{\mathrm{LK}}$ using pyramidal LK and RANSAC. After projecting the previous-frame corners into the current frame, the mean discrepancy from the border-based candidate corners is computed as

$$
D_t=\frac{1}{4}\sum_{k=1}^{4}
\left\|\mathbf q_{t,k}^{\mathrm{border}}-
\pi\!\left(H_t^{\mathrm{LK}}\mathbf q_{t-1,k}\right)\right\|_2,
$$

where $\pi(\cdot)$ denotes homogeneous-coordinate normalization. When RANSAC has at least 24 inliers, an inlier ratio of at least 0.25, and $D_t\le24$ px, the two motions are recorded as consistent; otherwise, the frame is marked as `content_conflict`. This marker does not override a border result that has already passed gating. Thus, LK/RANSAC provides auxiliary evidence for explaining content-motion conflicts rather than serving as the screen-geometry estimator.

# 3. Implementation Details

The final quadrilateral is mapped to a 1920 × 1080 canvas using a standard homography. All methods use `INTER_CUBIC` interpolation, `BORDER_REPLICATE` padding, and H.264 encoding. The frame-by-frame detection baseline independently estimates the screen in each frame using color thresholding, morphological processing, the largest contour, and quadrilateral approximation. The adjacent-frame optical-flow baseline propagates the previous-frame corners using forward-backward LK tracking and a RANSAC homography, falling back to a detection result or the previous frame when tracking fails. The Proposed method and both baselines share the same initialization, canvas, encoding, and evaluation code. Their main difference is that the Proposed quadrilateral is determined by local physical borders rather than internal texture motion.

| Implementation Item | Setting |
|---|---|
| Profile sampling | 50 points per edge, covering 4%–96% of the edge length; search radii of 20/60/120 px |
| Boundary-line recovery | Huber `fitLine` + MAD inlier updates, up to 4 iterations; at least 8 valid points and confidence no lower than 0.35 |
| Geometric gating | Area ratio 20%–85%, aspect ratio 1.25–2.35; online edge-length/area-change limits of 10%/20% |
| Redetection gating | Edge-length/area-change limits relaxed to 15%/30% |
| LK/RANSAC | LK window 31 × 31, 3 pyramid levels, RANSAC threshold 3 px; consistency thresholds of 24 inliers, 0.25 inlier ratio, and 24 px discrepancy |
| Trajectory and output | 5-frame median + 9-frame mean; 1920 × 1080, `INTER_CUBIC`, `BORDER_REPLICATE` |

# 4. Experiments

## 4.1 Dataset and Evaluation Metrics

The project dataset contains 50 camera-captured screen videos with a total of 14,985 frames. It covers five capture conditions: static pages, scrolling pages, video playback within the screen, weak-border scenes, and challenging scenes with difficult viewpoints or backgrounds. The final quantitative evaluation uses annotated clips.
Manual annotation follows the target definition in Section 2.1 and records the four corners of the visible active area of the display panel. Geometric accuracy is calculated only on annotated non-initialization frames so that frame 0, which is already supplied to the algorithm, is not counted toward accuracy. Metrics are first aggregated over annotated frames within each clip, after which medians and interquartile ranges are reported across clips. Category-level results are used to identify scene differences in the current data and are not treated as statistical estimates of the overall distribution of each category.

Geometric accuracy is evaluated using the corner RMSE, mean error, and maximum error between the estimated corners and manual annotations. The IoU and aspect-ratio error between the predicted and annotated quadrilaterals are also calculated. Corner error reflects local localization deviation, while IoU measures overlap of the overall screen region. All metrics are computed only on non-initialization frames that contain both manual annotations and valid estimates.

Temporal stability is evaluated by the projective change between adjacent estimated quadrilaterals, including translation, rotation, and scale changes. The main text primarily reports translation variation in px/frame. This metric reflects frame-to-frame fluctuation in the estimated trajectory and is considered jointly with RMSE and IoU to evaluate the geometric accuracy and temporal continuity of screen-plane recovery. All metrics are first aggregated over frames within each clip and then summarized across clips using medians and interquartile ranges, reducing the influence of a small number of outlier frames.

To further evaluate how normalization affects camera-captured screen signals, we design a frequency-domain diagnostic based on three inputs. For frame $t$, the diagnostic input is written as

$$
\mathcal X_t=\left(R_t^{\mathrm{raw}}, R_t^{\mathrm{track}}, T_t\right),
$$

where $R_t^{\mathrm{raw}}$ is the corresponding target region in the original frame, $R_t^{\mathrm{track}}$ is the output region produced by the actual tracking pipeline, and $T_t$ is the geometric transformation between them. The diagnostic uses $T_t$ to predict the theoretical location of a moiré-spectrum peak in the tracked output, and then compares the dominant frequency, orientation, energy, peak width, and occurrence of new peaks. It is intended to determine whether cropping, scaling, rotation, perspective rectification, and stabilization in the actual pipeline alter the structure of camera-captured moiré patterns.

## 4.2 Geometric Recovery Results

**Overall results.**

The border-dominated method achieves the best overall geometric accuracy while also reducing trajectory variation (Figure 2 and Table 2). Its median corner RMSE is 3.87 px, compared with 30.37 px for frame-by-frame detection and 31.40 px for adjacent-frame optical flow. It also achieves the highest median IoU of 0.996 and the lowest median translation variation of 2.45 px/frame.

![Figure 2. Overall comparison of geometric accuracy and trajectory variation. Bars show medians of clip-level summaries, and error bars show interquartile ranges.](figures/figure_02_overall_results.png)

| Metric | Frame-by-Frame Detection | Adjacent-Frame Optical Flow | Proposed |
|---|---:|---:|---:|
| Corner RMSE, px ↓ | 30.37 [14.59, 33.22] | 31.40 [28.37, 65.52] | 3.87 [3.47, 9.10] |
| Quadrilateral IoU ↑ | 0.980 [0.979, 0.988] | 0.979 [0.932, 0.980] | 0.996 [0.995, 0.996] |
| Translation variation, px/frame ↓ | 2.83 [2.37, 4.22] | 4.13 [2.35, 8.37] | 2.45 [1.55, 3.74] |

These results support the central design choice of this work: on the current evaluation clips, when the homography is dominated by screen borders rather than internal content, the estimated plane is closer to the manual annotation and exhibits less drift than adjacent-frame optical flow in scenes with content motion.

**Category-level and clip-level results.**

In the current category-level evaluation, the largest error reductions occur in clips with strong content motion or weak boundaries (Figure 3 and Table 3). On scrolling pages, the median RMSE of Proposed is 2.87 px, compared with 31.76 px for frame-by-frame detection and 81.67 px for adjacent-frame optical flow. On weak-border clips, Proposed reduces the median RMSE to 9.35 px, whereas both alternative methods exceed 155 px. The weak-border result does not imply that this category is easier for the proposed method; its absolute error remains higher than that of scrolling pages. The relative advantage arises because local prediction-guided search narrows the range of edge candidates, allowing the method to exploit the previous frame's geometric prior even when global boundary evidence is weak.

![Figure 3. Geometric accuracy and trajectory variation by capture condition. Values are clip-level medians within each capture condition of the annotated evaluation subset.](figures/figure_03_category_results.png)

| Capture Condition | Frame-by-Frame RMSE | Optical-Flow RMSE | Proposed RMSE | Proposed Translation Variation |
|---|---:|---:|---:|---:|
| Static page | 33.13 | 33.49 | 3.60 | 3.26 |
| Scrolling page | 31.76 | 81.67 | 2.87 | 1.28 |
| Video playback within screen | 30.08 | 29.46 | 3.75 | 3.25 |
| Weak-border scene | 157.26 | 155.87 | 9.35 | 1.45 |
| Challenging scene | 9.62 | 24.90 | 10.70 | 3.74 |

Challenging scenes are the only category in which frame-by-frame detection has a slightly lower RMSE than Proposed. The absolute difference is small, while Proposed produces a more stable trajectory in this category: its translation variation is 3.74 px/frame, compared with 5.19 px/frame for frame-by-frame detection and 8.56 px/frame for adjacent-frame optical flow.

Proposed achieves low clip-level median errors on the evaluated clips (Figure 4), with all clips remaining below 15 px. The higher-error clips consist of one weak-border video and two challenging videos, all of which have less visible boundaries. Together with the trajectory-variation results, this indicates that the low-error clips were not obtained by sacrificing geometric accuracy merely to produce a smoother appearance.

![Figure 4. Clip-level results of Proposed. The dashed line indicates a corner RMSE of 10 px; all evaluated clips remain below 15 px.](figures/figure_04_proposed_clip_results.png)

When the physical border moves, the trajectory updates accordingly. LK/RANSAC inconsistency only records conflicts between internal content motion and the boundary estimate and does not directly replace valid border geometry. Conflict markers are concentrated mainly in weak-border and challenging scenes, indicating that disagreements between internal feature motion and border estimation do occur in more difficult clips.

**Qualitative results.**

The qualitative outputs are consistent with the quantitative results (Figure 5). In scrolling and weak-border examples, Proposed better preserves the screen extent, whereas content-driven tracking or frame-by-frame detection may produce cropping offsets. In static-page and in-screen-video examples, all three methods produce readable outputs, but Proposed maintains more stable alignment with the physical border.

![Figure 5. Representative input frames and normalized outputs. Each row corresponds to one capture condition; the four columns show the input annotation, frame-by-frame output, adjacent-frame optical-flow output, and Proposed output, respectively.](figures/figure_05_qualitative.png)

## 4.4 Ablation and Mechanism Analysis

To avoid incorporating historical diagnostic items used during the early debugging stage into the formal experiments, the ablation study retains only the modules that are directly related to the core design claims of the current method and can be independently disabled or replaced. These modules include trajectory filtering, LK/RANSAC consistency diagnostics, physical border evidence, and the border observation strategy. All variants are evaluated on the same experimental video clips using identical initialization, output canvas, perspective transformation settings, and metric computation code, thereby minimizing the influence of differences in data, parameters, and post-processing. The results are presented in Table 4.

| Variant | Module Setting | Corner RMSE, px ↓ | IoU ↑ | Translation Variation, px/frame ↓ |
|---|---|---:|---:|---:|
| Proposed, profile border | Complete current pipeline: profile border observation + LK diagnosis | 3.253 | 0.996038 | 0.752 |
| Without trajectory filtering | Median/trajectory window set to 1 | 2.932 | 0.996585 | 1.430 |
| Without LK consistency diagnosis | Border still determines quadrilateral; internal-motion check disabled | 3.253 | 0.994323 | 0.972 |
| Without physical-border evidence | Previous quadrilateral propagated using only adjacent-frame optical flow | 76.114 | 0.916022 | 2.205 |
| LSD border observation | Profile observation replaced by LSD line-segment detection | 3.604 | 0.995716 | 0.961 |
| Hough border observation | Profile observation replaced by Hough line detection | 27.335 | 0.974200 | 0.897 |

This ablation supports three conclusions. First, trajectory filtering mainly improves temporal stability rather than the median single-frame geometry. After filtering is disabled, RMSE decreases from 3.253 px to 2.932 px, but inter-frame translation variation increases from 0.752 px/frame to 1.430 px/frame. Second, LK/RANSAC is not the primary geometric driver in the current method. Disabling LK diagnosis slightly improves the result, indicating that LK diagnosis provides an optimization benefit in some cases of rapid camera motion. Third, physical-border cues are the decisive component. After border evidence is removed, adjacent-frame optical flow follows coherently scrolling content and corner RMSE rises to 76.114 px. Replacing the border-observation method further shows that profile sampling is the more reliable default: LSD performs similarly but slightly worse, whereas Hough produces substantial geometric degradation on this clip.

Because the profile-based border observations remained valid throughout the clip, the unchanged geometric results after disabling the LK diagnostic only demonstrate that LK does not dominate the homography estimation for this clip. Instead, the results emphasize the ability of the border-based method to stably follow the screen during camera motion. The gating, re-detection, and hold-last-valid fallback mechanisms help maintain experimental accuracy while improving robustness under complex real-world acquisition conditions.


## 4.5 Frequency-Domain Signal-Preservation Experiment

The signal-preservation diagnostic examines whether the actual tracking pipeline changes the frequency-domain structure of camera-captured moiré patterns, but it does not replace the preceding analyses of geometric accuracy, motion effects, and mechanism behavior. For frame $t$, the diagnostic input is

$$
\mathcal X_t=\left(R_t^{\mathrm{raw}}, R_t^{\mathrm{track}}, T_t\right),
\qquad
R_t^{\mathrm{raw}}=\operatorname{crop}(I_t, Q_t),
$$

where $I_t$ is the original video frame, $Q_t$ is the target region in the original frame, $R_t^{\mathrm{track}}$ is the tracking output after target cropping, scaling, rotation, perspective rectification, and stabilization, and $T_t$ denotes the affine or perspective transformation from $R_t^{\mathrm{raw}}$ to $R_t^{\mathrm{track}}$. This definition retains all geometric operations in the actual pipeline and avoids underestimating their effect on moiré structure through an oversimplified experiment.

The algorithm computes the spectra of the two regions as

$$
F_t^{\mathrm{raw}}=\left|\mathcal F(R_t^{\mathrm{raw}})\right|,
\qquad
F_t^{\mathrm{track}}=\left|\mathcal F(R_t^{\mathrm{track}})\right|,
$$

and uses $T_t$ to derive rotation and scale compensation in frequency coordinates. If $\mathbf f_t^{\mathrm{raw}}$ is the dominant moiré peak in the original spectrum, its theoretical location in the tracked output is denoted by

$$
\widehat{\mathbf f}_t^{\mathrm{track}}
=\Phi(T_t,\mathbf f_t^{\mathrm{raw}}).
$$

Finally, the position, orientation, energy, and width of $\widehat{\mathbf f}_t^{\mathrm{track}}$ are compared with the actual peak in the tracked spectrum, and the appearance of additional significant peaks is recorded. The diagnostic is currently presented as an algorithmic validation design. During implementation, corresponding results are generated from clips with clearly visible moiré patterns under static capture, translation, rotation, distance changes, slight shake, and perspective changes.

![Figure 6. Design of the signal-preservation diagnostic. Each frame provides the original target region, tracking output, and geometric-transformation parameters. The algorithm uses the geometric transformation to compensate for rotation and scale changes of spectral peaks, and then compares dominant frequency, orientation, energy, peak width, and new peaks. This diagnostic measures the influence of the tracking pipeline on camera-captured moiré structure rather than demoiréing performance.](figures/figure_06b_moire_roi_preservation.png)

The experimental results show that the proposed method preserves the local frequency structure of moiré patterns well after geometric rectification and temporal stabilization. It achieves a local FFT similarity of 0.878, an orientation-histogram similarity of 0.948, and a dominant-peak radius change of only 0.015. Its overall performance is better than pure optical-flow propagation, indicating that border constraints reduce spectral misalignment caused by scrolling content. Compared with the frame-by-frame method, the proposed method performs slightly worse in the peak-width metric but is more balanced in dominant-peak orientation, energy, and overall spectral consistency, showing that the tracked output remains suitable for subsequent moiré analysis and processing.


# 5. Conclusion

This paper presents a border-dominated method for geometric normalization of camera-captured screen videos. By using physical screen edges as the primary geometric cues and restricting LK/RANSAC to auxiliary consistency diagnosis, the method reduces content-driven homography drift in clips with scrolling content. On the annotated evaluation subset, it achieves a median corner RMSE of 3.87 px, a median IoU of 0.996, and a median trajectory translation variation of 2.45 px/frame, outperforming the frame-by-frame detection and adjacent-frame optical-flow baselines overall. The current results support the design choice that physical borders should dominate screen geometry.

# Supplementary Notes

**Data availability.** The project contains a local collection of camera-captured screen videos, including an annotated evaluation subset with four-corner annotations used for the quantitative experiments in the main text. The raw videos are course-project data, and the team must confirm privacy and authorization boundaries before public release. The aggregated metrics and evidence records used in this paper have been archived in the repository documentation.

**Code availability.** The code is provided with the project repository and is executed through Python scripts managed by `uv`. The repository contains the paper source, figure-generation scripts, evaluation scripts, and archived metrics, allowing the tables in the main text to be reproduced from the available local data.

**Author contributions.** All three authors jointly contributed to project conception, data collection, annotation, implementation, experiment execution, and paper writing.

# References

1. L. Jagannathan and C. V. Jawahar, "Perspective Correction Methods for Camera-Based Document Analysis," 2005.
2. X.-C. Yin, J. Sun, S. Naoi, Y. Fujii, and K. Fujimoto, "Perspective Rectification for Mobile Phone Camera-Based Documents Using a Hybrid Approach to Vanishing Point Detection," 2007.
3. Williem, C. Simon, S. Cho, and I. K. Park, "Fast and Robust Perspective Rectification of Document Images on a Smartphone," *CVPR Workshops*, 2014.
4. T. Okatani and K. Deguchi, "Autocalibration of a Projector-Screen-Camera System: Theory and Algorithm for Screen-to-Camera Homography Estimation," *ICCV*, 2003.
5. B. D. Lucas and T. Kanade, "An Iterative Image Registration Technique with an Application to Stereo Vision," 1981.
6. J.-Y. Bouguet, "Pyramidal Implementation of the Lucas Kanade Feature Tracker," Intel Corporation, 2000.
7. J. Shi and C. Tomasi, "Good Features to Track," *CVPR*, 1994.
8. P. H. S. Torr and A. Zisserman, "MLESAC: A New Robust Estimator with Application to Estimating Image Geometry," *Computer Vision and Image Understanding*, 2000.
9. G. Simon, A. W. Fitzgibbon, and A. Zisserman, "Markerless Tracking using Planar Structures in the Scene," *ISAR*, 2000.
10. R. Grompone von Gioi, J. Jakubowicz, J.-M. Morel, and G. Randall, "LSD: A Line Segment Detector," *Image Processing On Line*, 2012.
11. R. O. Duda and P. E. Hart, "Use of the Hough Transformation to Detect Lines and Curves in Pictures," *Communications of the ACM*, 1972.
12. M. Grundmann, V. Kwatra, and I. Essa, "Auto-Directed Video Stabilization with Robust L1 Optimal Camera Paths," *CVPR*, 2011.
13. W. Guilluy, A. Beghdadi, and L. Oudre, "A Performance Evaluation Framework for Video Stabilization Methods," *EUVIP*, 2018.
14. P. Dai, X. Yu, L. Ma, B. Zhang, J. Li, W. Li, J. Shen, and X. Qi, "Video Demoireing with Relation-Based Temporal Consistency," *CVPR*, 2022.
15. S. Xu, B. Song, X. Chen, and J. Zhou, "Direction-Aware Video Demoireing with Temporal-Guided Bilateral Learning," *AAAI*, 2024.
16. H. Yue, Y. Cheng, X. Liu, and J. Yang, "Recaptured Raw Screen Image and Video Demoireing via Channel and Spatial Modulations," *NeurIPS*, 2023.
