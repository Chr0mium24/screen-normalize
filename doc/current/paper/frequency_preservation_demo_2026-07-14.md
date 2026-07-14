# Frequency Preservation Demo

Date: 2026-07-14

## Question

The input videos already contain camera-screen interference and high-frequency texture. This demo checks whether reference-based frequency diagnostics can measure preservation of that captured signal after geometric normalization. It does not measure moire removal.

## Setup

- Original video: `inputs\scrolling\scrolling_01.mp4`
- Annotation CSV: `inputs\scrolling\scrolling_01.csv`
- Normalized outputs: `runs\20260714_small_sample_with_proposal_border\scrolling\scrolling_01`
- Evaluated frames: `74, 148, 223, 297`
- Per-frame CSV: `runs/20260714_frequency_preservation_demo_scrolling_01/frequency_preservation_rows.csv`
- Summary CSV: `runs/20260714_frequency_preservation_demo_scrolling_01/frequency_preservation_summary.csv`

Each annotated original frame is warped with the human screen-corner annotation to form the reference. The metric then compares each method's normalized output against that annotation-warped reference.

## Metrics

- `FFT sim`: cosine similarity between log FFT magnitudes outside the DC region.
- `HF ratio`: high-frequency energy ratio, where 1 means the output preserves the reference high-frequency energy.
- `|log HF ratio|`: symmetric distance from a perfect high-frequency energy ratio.
- `Orient hist`: histogram-intersection similarity between high-frequency orientation spectra.
- `Band ratio`: energy ratio in a broad high-frequency band used as a moire/high-frequency proxy, not a labeled moire mask.

## Results

| Method | Frames | FFT sim ↑ | HF ratio ≈1 | Abs log HF ratio ↓ | Orient hist ↑ | Band ratio ≈1 | Abs log band ratio ↓ |
|---|---:|---:|---:|---:|---:|---:|---:|
| frame_wise | 4 | 0.964 | 1.003 | 0.027 | 0.992 | 0.980 | 0.020 |
| optical_flow | 4 | 0.963 | 0.982 | 0.033 | 0.992 | 0.958 | 0.043 |
| proposal_border | 4 | 0.990 | 1.001 | 0.027 | 0.997 | 1.000 | 0.012 |

## Readout

The demo is feasible as a reference-based preservation diagnostic. The useful quantities are the similarity scores and the ratio distances, not raw frequency direction regularity. This should be framed as signal preservation after geometric normalization, not as moire removal or perceptual restoration quality.

