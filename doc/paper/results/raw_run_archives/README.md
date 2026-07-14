# Raw Run Archives

This folder stores compact, Git-tracked evidence archives for paper results.

## `first_pass_text_metrics_20260714.zip`

Contents:

- `runs/20260714_full_pipeline_first_pass/**/*.csv`
- `runs/20260714_full_pipeline_first_pass/**/*.json`
- `runs/20260714_full_pipeline_first_pass/**/*.md`
- `runs/20260714_full_pipeline_first_pass/**/*.svg`
- `runs/20260714_full_ablation_first_pass/**/*.csv`
- `runs/20260714_full_ablation_first_pass/**/*.json`
- `runs/20260714_full_ablation_first_pass/**/*.md`
- `runs/20260714_full_ablation_first_pass/**/*.svg`
- `MANIFEST.csv` with archive path, byte size, and SHA-256 for each member

Excluded intentionally:

- MP4 rectified videos
- JPG/PNG sampled frames and dense visual dumps
- HTML reports with local media links

The excluded media remains local under `runs/` because the two complete runs are
approximately 3.7 GB. The manuscript figures and aggregate CSV/JSON summaries are
tracked separately under `doc/paper/manuscript/figures` and `doc/paper/results`.
