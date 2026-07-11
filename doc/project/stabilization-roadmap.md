# Screen Stabilization Roadmap

## Goal

The goal is not to make the video "a bit smoother." The goal is to turn a filmed monitor into something that behaves like a screen recording.

That means separating two kinds of motion:

1. **Physical screen-plane motion**: camera shake, perspective drift, rolling rotation, and scale changes caused by filming the monitor. This must be removed.
2. **Content motion inside the screen**: video playback, subtitles, scrolling comments, cursor movement, and page changes. This must remain in the output and must not drive the screen-plane estimate.

The output should keep the browser chrome, page layout, player frame, and other screen-fixed UI stable. Moving content inside the player is allowed to move, but it must not pull the estimated homography.

## What Went Wrong

The early commits were aligned with the real objective:

- `055f234` through `603b6ad` built perspective correction, optical-flow tracking, and a reference-plane tracker.
- `8fa629c` added scale and area gating, which was a valid attempt to reject bad homography updates.

The middle phase lost focus:

- `d242a9b` introduced per-frame line-roll correction.
- `51eb962`, `6d63f4f`, and `afed38a` improved line diagnostics and line extraction, but this chased symptoms.
- The problem was not primarily "which line detector is best." The problem was that dynamic text, subtitles, and playback content were being allowed to influence camera/screen pose.

Per-frame line correction is especially risky. It can make the output look less like a recording because it rotates the entire screen based on changing image content. If line correction is needed, it should be global or very low frequency, not driven by frame-by-frame text edges.

The later commits moved back toward the right model:

- `60980a1` added reference-track coverage gating and offline smoothing.
- `6b72c02` made refreshed reference points mature before they can drive homography updates.

Those changes match the core principle: estimate the physical screen plane from stable evidence, not from arbitrary current-frame features.

## First Principles

The screen plane at frame `t` can be represented by a homography `H_t`.

A good `H_t` trajectory should satisfy:

- **Geometric validity**: corners remain ordered, screen area and side lengths change slowly, and aspect stays plausible.
- **Temporal continuity**: camera shake is low-frequency after normalization; sudden high-frequency perspective changes are usually tracker error.
- **Track consistency**: features used to estimate `H_t` should survive over time and remain consistent with the same reference plane.
- **Spatial support**: inliers should cover enough of the screen plane. A homography from points concentrated in one moving video region is not trustworthy.
- **Layer separation**: moving content inside the screen is not the camera motion and should not directly influence `H_t`.

The tracker should therefore prefer long-lived, reference-consistent points and reject short-lived dynamic features even if they have low immediate optical-flow error.

## Current Best Direction

Use `--tracker reference` without line-roll first for inputs that contain video playback or other dynamic content.

The current safe path for `VID20260621031719.mp4` is:

```bash
uv run scripts/normalize_screen.py inputs/VID20260621031719.mp4 --tracker reference --reference-align --reference-motion affine --crop-right 0.02 --crop-bottom 0.055
```

`--reference-align` now performs residual affine alignment only when a whole-video preflight says the residual track is globally reliable. It is allowed to improve difficult inputs, but it should disable itself when the residual track collapses on another input.

Line-roll should be treated as experimental. It should only be enabled after diagnostics show that the detected lines are stable screen-fixed structures, not text or playback content.

## Execution Plan

### 1. Build Repeatable Measurement

Before changing stabilization logic again, every candidate run must be measurable.

Implement and use a stability analysis tool that reports:

- per-frame residual affine translation, rotation, and scale between adjacent normalized frames;
- inlier count, inlier ratio, and inlier coverage;
- whole-video and last-N-seconds summaries;
- CSV and JSON outputs saved under `runs/`.

This metric is not perfect because moving content can still affect optical flow, but it provides a repeatable signal and exposes when a change makes the last seconds worse.

Implemented tool:

```bash
uv run scripts/analyze_stability.py <normalized-video> [<normalized-video> ...] --run-name <name>
```

It writes:

- `runs/<name>/stability_metrics.csv`
- `runs/<name>/stability_summary.json`

Current baseline run:

```text
runs/analyze_reference_stability_comparison/
```

Last-two-second metrics on `VID20260621031719.mp4` outputs:

| Output | Translation p95 | Rotation p95 | Scale delta p95 |
| --- | ---: | ---: | ---: |
| `run_other_input_no_line_roll` | 2.897 px | 0.0699 deg | 0.002494 |
| `run_other_input_reference_smoothed_line_roll_gated` | 1.294 px | 0.0381 deg | 0.000757 |
| `run_other_input_reference_mature_no_line` | 0.970 px | 0.0191 deg | 0.000517 |
| `run_other_input_reference_mature_line_roll` | 1.143 px | 0.0442 deg | 0.000477 |

Current decision: `run_other_input_reference_mature_no_line` is the best baseline for the dynamic-video input. Line-roll improves neither the visual model nor the last-two-second residual rotation for this case.

### 2. Log Tracker Internals

Add an optional tracker-debug output to `normalize_screen.py`:

- accepted/rejected update per frame;
- corner coordinates;
- area and side lengths;
- inlier count, ratio, reprojection error, and coverage;
- mature point count;
- reason for rejection.

This makes it possible to diagnose the actual homography source instead of inspecting only the final video.

Implemented option:

```bash
uv run scripts/normalize_screen.py <input-video> --tracker reference --write-tracker-debug
```

It writes:

- `runs/<run-name>/tracker_debug.csv`

Current debug run:

```text
runs/debug_tracker_reference_mature/
```

Observed on `VID20260621031719.mp4`:

- rows: 580
- accepted frames: 580
- reasons: `initial_reference` for frame 0, `accepted` for the rest
- mature point count median: 701
- inlier count median: 669
- inlier ratio median: 0.986
- coverage median: x 0.752, y 0.934
- reprojection error median: 0.374 px

Interpretation: the current mature-point tracker is not failing through obvious rejected frames or low coverage. The remaining shake should be investigated in the trajectory model and offline optimization, not by adding more website-specific masks or per-frame line correction.

### 3. Add Residual Alignment, But Gate It Globally

Residual affine alignment after perspective correction is useful on the difficult dynamic-video input, but it is not safe as a blind per-frame correction.

Implemented options:

```bash
uv run scripts/normalize_screen.py <input-video> --tracker reference --reference-align --reference-motion affine --write-align-debug
```

It writes:

- `runs/<run-name>/align_debug.csv`

The debug file records measured and applied residual translation, rotation, scale, inlier counts, coverage, per-frame rejection reason, whole-video accept ratio, and whether residual alignment was globally enabled.

Experiments on `VID20260621031719.mp4`:

| Output | Translation p95 | Rotation p95 | Scale delta p95 | Decision |
| --- | ---: | ---: | ---: | --- |
| reference mature, no residual | 0.970 px | 0.0191 deg | 0.000517 | baseline |
| raw residual affine | 0.650 px | 0.0193 deg | 0.000436 | best metric, unsafe alone |
| online residual smooth 0.85 | 0.790 px | 0.0191 deg | 0.000423 | smoother correction, worse output |
| online residual smooth 0.50 | 0.691 px | 0.0213 deg | 0.000487 | acceptable, still worse than raw |
| residual step-limit only | 0.740 px | 0.0231 deg | 0.000461 | worse than raw |
| offline residual filter 5 | 0.782 px | 0.0216 deg | 0.000452 | centered filtering still under-corrects |
| global-gated residual affine | 0.728 px | 0.0232 deg | 0.000479 | safe default improvement |

Interpretation:

- The residual affine estimate is real signal on this input; smoothing it too much leaves camera motion uncorrected.
- Per-frame or short-window smoothing is not the right fix for this case.
- Raw residual affine can be the most aggressive diagnostic run, but it should not be the default without whole-video reliability checks.

Cross-input validation:

| Input/run | Result |
| --- | --- |
| `VID20260621031719.mp4` global-gated residual | accepted ratio 0.991, globally enabled |
| `VID20260621024117.mp4` global-gated residual | accepted ratio 0.057, globally disabled |
| `VID20260621024117.mp4` same-command no residual vs global-disabled residual | identical metrics |

Important caveat: the archived old-input output `runs/20260621-033412_normalize_screen/VID20260621024117_normalized.mp4` still measures much better than the current code's no-residual reference path. That is a separate regression target. The new residual gate prevents this change from making it worse, but it does not recover the archived old-input quality by itself.

### 4. Split Reference Tracker Latency Profiles

The old input and the dynamic-video input need different reference tracker latency.

On `VID20260621024117.mp4`, the archived reference-track outputs are very stable:

| Output | Translation p95 | Rotation p95 | Scale delta p95 |
| --- | ---: | ---: | ---: |
| archived `screen_recording_reference_track` | 0.072 px | 0.0042 deg | 0.000092 |
| archived `screen_recording_reference_gated_tight` | 0.050 px | 0.0025 deg | 0.000049 |
| current reference default | 2.181 px | 0.0068 deg | 0.000400 |
| current `--trajectory-window 1` | 0.347 px | 0.0151 deg | 0.000269 |
| current no median/no average | 0.234 px | 0.0156 deg | 0.000314 |
| current `--reference-min-point-age 1 --median-window 1 --trajectory-window 1` | 0.118 px | 0.0044 deg | 0.000118 |

Interpretation: the current mature-point plus long-window smoothing path adds too much latency for the old input. The low-latency reference path recovers most of the archived quality.

The same low-latency profile is unsafe for `VID20260621031719.mp4`:

| Output | Translation p95 | Rotation p95 | Scale delta p95 |
| --- | ---: | ---: | ---: |
| mature reference, no residual | 0.970 px | 0.0191 deg | 0.000517 |
| global-gated residual affine | 0.728 px | 0.0232 deg | 0.000479 |
| low-latency reference | 4.093 px | 0.0834 deg | 0.003074 |
| low-latency reference plus residual | 6.074 px | 0.1545 deg | 0.003276 |

Implemented profile option:

```bash
uv run scripts/normalize_screen.py <input-video> --tracker reference --reference-profile low-latency
uv run scripts/normalize_screen.py <input-video> --tracker reference --reference-profile dynamic
```

Use `low-latency` only when the screen content is mostly stable and the main error is smoothing lag. Use `dynamic` for moving playback or changing page content.

### 5. Strengthen Stable-Track Selection

Extend the mature-point idea into track-level scoring:

- keep feature identity and age;
- track survival length;
- count how often each point agrees with the accepted reference homography;
- downweight or discard points that repeatedly disagree;
- avoid letting newly refreshed points immediately influence `H_t`.

The point is not to hardcode screen regions. The point is to let temporal consistency identify the stable screen layer.

### 6. Replace Greedy Per-Frame Pose With Offline Trajectory Optimization

Do not directly trust each frame's best homography.

Collect candidate observations and solve a robust low-frequency trajectory:

- use median filtering for outlier rejection;
- use moving average or spline smoothing for low-frequency camera motion;
- use Huber-style penalties so bad frames are held or interpolated;
- keep area, side length, and corner acceleration bounded.

This should become the main stabilizer for difficult hand-shot inputs.

### 7. Rework Line-Roll Into Global or Low-Frequency Bias

Line-roll should not rotate the output frame by frame.

If needed:

- estimate a constant roll bias from many frames;
- or estimate a very low-frequency curve after robust temporal filtering;
- reject text-like or dynamic line observations;
- never allow a single frame's line detection to rotate the screen.

For moving-video inputs, default to no line-roll unless the diagnostics prove it helps.

### 8. Validate Against Both Inputs

Every stabilization change should be tested on both known inputs:

- the first input where the existing reference output is already good;
- the second input with playback motion and late-frame shake.

A change only counts as an improvement if it preserves the good input and improves the difficult input by the same metrics and visual inspection.

## Decision Rules

- If a change improves line metrics but worsens residual screen motion, reject it.
- If a method depends on a website-specific region, keep it out of the default path.
- If a dynamic video region can dominate the estimate, the method is not separating layers correctly.
- If the output is only "slower shake," the root problem is still unsolved.
- Prefer fewer moving parts with clear diagnostics over more detectors without a measurable win.
