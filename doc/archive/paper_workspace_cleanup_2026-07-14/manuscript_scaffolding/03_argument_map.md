# Argument Map

## Tension

Screen restoration methods often operate on already isolated or aligned screen content, whereas real handheld input contains background, perspective distortion, camera motion, weak boundaries, and independently moving screen content.

## Research question

Can a lightweight classical vision pipeline produce a stable frontal screen-coordinate video from uncontrolled handheld recordings without treating all visible content motion as camera motion?

## Current thesis

A reference-anchored planar tracker with robust acceptance gates, failure holding, offline trajectory repair, smoothing, and residual alignment provides a reproducible front-end for screen-video rectification. Its advantage over frame-wise detection and unconstrained optical flow must be established by the formal experiment.

## Supporting chain

1. The display is approximately planar, so four corners define the rectifying homography.
2. A fixed reference plane reduces drift relative to purely adjacent-frame tracking.
3. Forward-backward checks, RANSAC support, coverage, reprojection, and quadrilateral gates reject unreliable updates.
4. Holding, interpolation, and temporal filters prevent rejected observations from becoming abrupt output motion.
5. Geometry, temporal, detail, and frequency measurements expose complementary benefits and costs.

## Counterarguments and limits

- Interior features may still follow changing screen content.
- Strong smoothing can improve the chosen temporal metric by construction.
- A screen with invisible boundaries or severe occlusion can defeat initialization.
- Rectification resampling can alter detail and high-frequency artifacts.
- The current code does not fully realize proposal-level border guidance.

