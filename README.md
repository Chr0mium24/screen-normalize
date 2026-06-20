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

## Current Recommended Mode

The most stable mode for filmed screens is:

```bash
uv run scripts/normalize_screen.py inputs/VID20260621024117.mp4 --tracker reference --crop-right 0.02 --crop-bottom 0.055
```

`--tracker reference` locks the video to the first detected screen plane, tracks screen features with Lucas-Kanade optical flow, estimates a RANSAC homography, and rejects updates with weak inliers or abnormal scale/area changes.

If the normalized screen still has a small residual tilt and the page has stable browser or UI lines, add line-based roll correction:

```bash
uv run scripts/normalize_screen.py inputs/VID20260621031719.mp4 --tracker reference --line-roll-correction --crop-right 0.02 --crop-bottom 0.055
```

`--line-roll-correction` estimates long horizontal lines only in stable mask regions, by default the top browser/page area and right-side UI. It then applies a small smoothed rotation; it does not recompute screen corners or use moving video content as geometry.

To inspect which lines are being used, render a diagnostic overlay:

```bash
uv run scripts/visualize_line_roll.py runs/run_other_input_no_line_roll/VID20260621031719_normalized.mp4 --run-name debug_line_roll_no_line_input
```

The debug video draws same-direction inlier lines in green, other horizontal candidates in orange, and writes per-frame measurements to a CSV next to the video.
