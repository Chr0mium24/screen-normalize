# screen-normalize

Normalize a hand-filmed static monitor into a screen-recording-like video.

The target case is a mostly static screen: documents, slides, dashboards, web pages, forms, code editors, or paused video frames. The tool estimates the monitor plane, warps it to a fixed 16:9 output canvas, and writes every result into a run directory.

Moving content inside the screen is not the primary target. If large parts of the screen are playing video, scrolling, or changing rapidly, pause the content or expect lower stability.

## Quick Start

Put the input video in `inputs/`, then run:

```bash
uv run scripts/normalize_screen.py inputs/my_static_screen.mp4 --tracker reference --reference-profile low-latency
```

The output is written to:

```text
runs/<run-name>/<input_stem>_normalized.mp4
```

For repeatable folders, pass `--run-name`:

```bash
uv run scripts/normalize_screen.py inputs/my_static_screen.mp4 --tracker reference --reference-profile low-latency --run-name static_test
```

## Recommended Static Workflow

1. Start with automatic detection:

```bash
uv run scripts/normalize_screen.py inputs/my_static_screen.mp4 --tracker reference --reference-profile low-latency
```

2. If the frame includes a border or unwanted edge, crop after warping:

```bash
uv run scripts/normalize_screen.py inputs/my_static_screen.mp4 --tracker reference --reference-profile low-latency --crop-right 0.02 --crop-bottom 0.04
```

3. If automatic corner detection starts from the wrong screen outline, pass manual corners from the first frame in `TL,TR,BR,BL` order:

```bash
uv run scripts/normalize_screen.py inputs/my_static_screen.mp4 --tracker reference --reference-profile low-latency --corners "124,116:1488,132:1516,850:145,934"
```

4. If there is still small residual drift, inspect tracker diagnostics before changing stabilization settings:

```bash
uv run scripts/normalize_screen.py inputs/my_static_screen.mp4 --tracker reference --reference-profile low-latency --write-tracker-debug --run-name debug_static
```

This writes `runs/debug_static/tracker_debug.csv`.

## Static Defaults

The recommended static mode is:

```bash
--tracker reference --reference-profile low-latency
```

`--tracker reference` tracks screen features with Lucas-Kanade optical flow, estimates a RANSAC homography back to the first detected screen plane, and rejects weak geometric updates.

`--reference-profile low-latency` is tuned for static content:

- refreshed points can affect the estimate immediately;
- median and moving-average trajectory smoothing are disabled;
- camera motion is corrected with less lag;
- moving screen content is not aggressively filtered out.

Use this profile when the visible screen content is stable enough to act as the reference plane.

## Key Options

| Option | Purpose |
| --- | --- |
| `--tracker reference` | Lock the output to the first detected screen plane. |
| `--reference-profile low-latency` | Static-screen profile with minimal smoothing lag. |
| `--corners "x,y:x,y:x,y:x,y"` | Override automatic first-frame screen corners. |
| `--crop-left/top/right/bottom` | Crop the normalized output by a fraction after warping. |
| `--width`, `--height` | Output canvas size. Defaults to `1920x1080`. |
| `--run-name` | Use a deterministic folder under `runs/`. |
| `--write-tracker-debug` | Save per-frame reference tracker diagnostics. |

## Measuring Stability

Use the analysis script to compare normalized outputs:

```bash
uv run scripts/analyze_stability.py runs/static_test/my_static_screen_normalized.mp4 --run-name analyze_static_test
```

It writes:

- `runs/analyze_static_test/stability_metrics.csv`
- `runs/analyze_static_test/stability_summary.json`

The most useful summary fields are last-window residual translation, rotation, and scale delta. Lower values usually mean the output feels more like a recording.

## Project Layout

- `scripts/` - runnable processing and analysis scripts.
- `inputs/` - local input videos. Files in this directory are ignored by git.
- `runs/` - generated outputs. Every script run writes to a subdirectory.
- `doc/` - reference papers and implementation notes.

The repository root should only contain folders, `.gitignore`, and this `README.md`.

## Development Notes

Use `uv` for Python execution and dependency resolution:

```bash
uv run scripts/normalize_screen.py --help
```

Generated videos, CSVs, and debug artifacts belong under `runs/` and should stay out of git.
