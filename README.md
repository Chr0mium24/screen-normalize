# screen-normalize

Turn a filmed monitor into a screen-recording-like video by estimating the screen plane and warping it to a fixed output canvas.

## Layout

- `scripts/` - runnable processing scripts.
- `inputs/` - local input videos. Files in this directory are ignored by git.
- `runs/` - generated outputs. Every script run writes to a timestamped subdirectory.
- `doc/` - reference papers and notes.

The repository root should only contain folders, `.gitignore`, and this `README.md`.

## Usage

Use `uv` to run the script dependencies:

```bash
uv run scripts/normalize_screen.py inputs/VID20260621024117.mp4 --tracker reference --crop-right 0.02 --crop-bottom 0.055
```

By default, outputs are written to:

```text
runs/<YYYYMMDD-HHMMSS>_normalize_screen/<input_stem>_normalized.mp4
```

You can provide an output filename, but it is still placed inside the generated run directory:

```bash
uv run scripts/normalize_screen.py inputs/VID20260621024117.mp4 screen.mp4 --tracker reference
```

Use `--run-name` for a deterministic run folder name:

```bash
uv run scripts/normalize_screen.py inputs/VID20260621024117.mp4 --run-name test_reference_gate --tracker reference
```

## Current Recommended Modes

For screens with moving playback, subtitles, scrolling content, or other dynamic regions, use the mature reference profile and gated residual affine alignment:

```bash
uv run scripts/normalize_screen.py inputs/VID20260621031719.mp4 --tracker reference --reference-profile dynamic --reference-align --reference-motion affine --crop-right 0.02 --crop-bottom 0.055
```

For mostly stable screen content where the main problem is smoothing lag, use the low-latency reference profile:

```bash
uv run scripts/normalize_screen.py inputs/VID20260621024117.mp4 --tracker reference --reference-profile low-latency
```

`--tracker reference` locks the video to the first detected screen plane, tracks screen features with Lucas-Kanade optical flow, estimates a RANSAC homography, and rejects updates with weak inliers, poor inlier screen coverage, or abnormal scale/area changes. The `dynamic` profile waits for refreshed points to survive before they can drive homography estimation and applies offline trajectory smoothing. The `low-latency` profile uses immediate points and disables trajectory smoothing; it can recover sharper camera motion, but it is unsafe when moving screen content can take over the estimate.

`--reference-align` runs a residual affine alignment after perspective correction. It now performs a whole-video reliability preflight and disables itself when the residual track is not globally reliable.

If the normalized screen still has a small residual tilt and the page has stable structural edges, add binary-contour roll correction with a restricted mask:

```bash
uv run scripts/normalize_screen.py inputs/VID20260621031719.mp4 --tracker reference --line-roll-correction --line-detector binary-contour --no-line-full-mask --line-mask-top 0 --line-mask-right 0.33 --line-mask-bottom 0.30 --line-ignore-top 0.22 --crop-right 0.02 --crop-bottom 0.055
```

`--line-roll-correction` defaults to `--line-detector binary-contour`: it estimates the light page background per frame, thresholds darker or saturated content into a binary foreground mask, extracts large rectangular contours and horizontal edges, clusters same-direction structural lines, and applies a small smoothed rotation. Missed or temporally inconsistent measurements reuse the previous accepted roll angle instead of dropping the correction to zero. This does not recompute screen corners.

Keep the mask away from browser chrome and text-heavy top UI. For the current Bilibili input, the right-side recommendation column plus lower player region is more stable than full-frame detection.

For inputs where the screen itself contains a moving video, run the reference tracker without line-roll first. Per-frame line-roll can reintroduce small motion if the detected lines come from dynamic text or video content.

To inspect which lines are being used, render a diagnostic overlay:

```bash
uv run scripts/visualize_line_roll.py runs/run_other_input_no_line_roll/VID20260621031719_normalized.mp4 --detector binary-contour --mask-top 0 --mask-right 0.33 --mask-bottom 0.30 --ignore-top 0.22 --run-name debug_binary_component_selected_edges
```

The debug video draws same-direction inlier lines in green, other horizontal candidates in orange, and writes per-frame measurements to a CSV next to the video. Add `--view binary` to see the inverse threshold mask directly, or `--view horizontal` to see the final horizontal edge mask.
