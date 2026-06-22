<h1>Screen Capture Rectification and Temporal Stabilization for Real-world Captured-screen Videos</h1>

<p class="meta"><strong>Group ID:</strong> TODO &nbsp; | &nbsp; <strong>Members:</strong> Rongshuo Wen (Leader, 124020369), Bihua Wen (124090670), Ruiming Liu (124090375)</p>

<div class="abstract">
  <strong>Problem.</strong> Existing screen demoiréing datasets validate the demand for captured-screen restoration, but their inputs are often controlled, cropped, paired, or spatially/temporally aligned. Real phone-captured screen videos still contain background regions, perspective distortion, hand-held camera shake, weak screen borders, and dynamic screen content. This project targets this missing pre-alignment stage.
</div>

<div class="grid">
<div class="card">

## Task and Goal

Input is a full camera video of a computer screen. Output is a fixed-ratio, front-facing, temporally stable screen video. The goal is to remove most non-screen background, rectify perspective distortion, reduce frame-to-frame jitter, and provide stable screen-coordinate input for downstream video demoiréing, OCR, or archival restoration.

</div>
<div class="card">

## Method

- Detect or manually specify the first-frame screen corners.
- Estimate a homography to rectify the screen to a 16:9 canvas.
- Track reference-plane features with Lucas-Kanade optical flow.
- Use RANSAC and geometric gates to reject unreliable updates.
- Interpolate/smooth the trajectory and evaluate residual motion.

</div>
<div class="card">

## Dataset Plan

The final evaluation will use a self-collected test set: **5 scenario classes x 10 clips x about 5 s**. The classes are static pages/documents, scrolling webpages, in-screen video playback, PPT or weak-border low-texture pages, and 4K/moiré/glare hard cases. Public demoiréing datasets are used as related-work evidence rather than direct benchmarks for this pre-alignment task.

</div>
<div class="card">

## Metrics

We estimate residual affine motion between adjacent normalized frames. Main metrics are residual translation p95, residual rotation p95, and residual scale-delta p95. Tracker accept ratio, RANSAC inliers, inlier ratio, and feature coverage are used to explain failure cases. Lower residual motion means a more stable normalized video.

</div>
<div class="card wide">

## Initial Experiment

One local 1920x1080 captured-screen video with 317 frames was used for an initial same-video ablation. The numbers below measure residual motion in the normalized output; they are not ground-truth reconstruction errors.

| Method | Last 2 s translation p95 | Last 2 s rotation p95 | Interpretation |
| --- | ---: | ---: | --- |
| Frame-wise corner detection | 1.927 px | 0.0425 deg | jittery baseline |
| Optical-flow tracking | 1.929 px | 0.0263 deg | lower rotation, still unstable |
| Reference-plane tracking | <span class="best">0.118 px</span> | <span class="best">0.0044 deg</span> | best residual stability |

</div>
<div class="card wide">

## Expected Result and Timeline

The expected result is a classical geometric preprocessing pipeline that converts realistic captured-screen videos into stable, rectified screen-coordinate videos. Proposal-stage work has fixed the application story, implemented the core normalization pipeline, and produced an initial ablation. Final-stage work will complete the 50-clip test set, run method ablations, visualize corners and tracking failures, and report both successful and unstable cases.

</div>
</div>

<p class="footer">Source files and evidence are stored under deliverables/proposal_20260622/. Current draft uses placeholder Group ID until the official group number is filled.</p>
