# Detail Preservation Demo

Date: 2026-07-14

## Question

This demo checks whether reference-based detail diagnostics can measure preservation of local structure after geometric normalization. It does not measure perceptual restoration quality or moire removal.

## Setup

- Original video: `inputs\scrolling\scrolling_01.mp4`
- Annotation CSV: `inputs\scrolling\scrolling_01.csv`
- Normalized outputs: `runs\20260714_small_sample_with_proposal_border\scrolling\scrolling_01`
- Evaluated frames: `74, 148, 223, 297`
- Per-frame CSV: `runs/20260714_detail_preservation_demo_scrolling_01/detail_preservation_rows.csv`
- Summary CSV: `runs/20260714_detail_preservation_demo_scrolling_01/detail_preservation_summary.csv`

Each annotated original frame is warped with the human screen-corner annotation to form the reference. The metric then compares each method's normalized output against that annotation-warped reference.

## Metrics

- `SSIM`: grayscale structural similarity to the annotation-warped reference.
- `Grad sim`: cosine similarity between Sobel gradient-magnitude maps.
- `Grad ratio`: mean gradient-magnitude ratio, where 1 means matching edge strength.
- `Edge F1`: Canny edge overlap with a one-pixel tolerance.
- `Lap ratio`: Laplacian detail-energy ratio, where 1 means matching local high-frequency detail energy.

## Results

| Method | Frames | SSIM ↑ | Grad sim ↑ | Grad ratio ≈1 | Edge F1 ↑ | Lap ratio ≈1 | Abs log Lap ratio ↓ |
|---|---:|---:|---:|---:|---:|---:|---:|
| frame_wise | 4 | 0.434 | 0.475 | 1.002 | 0.617 | 0.989 | 0.011 |
| optical_flow | 4 | 0.314 | 0.337 | 1.046 | 0.452 | 1.033 | 0.041 |
| proposal_border | 4 | 0.890 | 0.930 | 1.006 | 0.952 | 1.047 | 0.045 |

## Readout

The demo is feasible as a detail-preservation diagnostic. It should be used as supporting evidence that geometric normalization preserves captured local structure, not as a standalone ranking metric for visual restoration.

