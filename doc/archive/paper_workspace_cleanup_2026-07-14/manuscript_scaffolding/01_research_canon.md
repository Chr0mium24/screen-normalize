# Research Canon

## Fixed facts

- The task is to convert a handheld full-scene recording of a display into a frontal, screen-coordinate video.
- The planned formal dataset contains five categories with ten clips per category. Formal collection and annotation are incomplete.
- The only manual annotation is TL/TR/BR/BL screen corners on selected keyframes.
- Baselines are `frame_wise`, `optical_flow`, and `proposed`.
- Current `proposed` implementation initializes a screen quadrilateral, tracks interior Shi-Tomasi/LK features against a reference frame, estimates a homography with RANSAC, rejects weak or implausible updates, holds the last accepted quadrilateral on online failure, repairs the trajectory offline, smooths it, warps the screen, and optionally estimates residual alignment.
- Current implementation does not yet use LSD/Hough border motion as the primary per-frame estimate and does not implement the proposal's explicit border-versus-content consistency test.
- Frequency analysis is diagnostic. It does not establish demoireing performance.
- Pilot results validate the software path only and are not formal paper evidence.

## Unresolved facts

- Final dataset count, annotation count, device conditions, and annotation consistency.
- Final geometry, temporal, detail, frequency, runtime, ablation, and failure-case results.
- Whether the method will be extended to the proposal-complete border-guided design before final experiments.
- Hardware and software versions used for the formal run.

## Terminology

- **Rectification:** projective mapping from the observed screen quadrilateral to a frontal rectangle.
- **Screen-plane trajectory:** the per-frame four-corner or homography sequence.
- **Reference-anchored tracking:** estimating each frame relative to a fixed reference screen plane.
- **Residual alignment:** a bounded secondary alignment estimated after geometric rectification.
- **Frequency diagnostics:** FFT-derived direction and axis-regularity measurements, not moire removal.

