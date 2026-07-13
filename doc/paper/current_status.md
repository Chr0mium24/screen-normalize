# Current Paper Status

Date: 2026-07-14

This file is the current status entry for the paper workspace. Older plans, generated reports, placeholder figures, and one-off operation records were moved to `doc/archive/paper_workspace_cleanup_2026-07-14/`.

## Current Scope

The current data scope is a local 36-clip, five-category video collection. The current evaluated-result scope is still a four-clip ablation pilot, because the newly organized 36 clips do not yet have committed annotation CSV files or completed full experiment results.

| Area | Current fact | Paper implication |
| --- | --- | --- |
| Active video categories | `static`, `scrolling`, `screen_video`, `weak_border`, `hard` | Dataset section can describe the 36 collected clips. |
| Evaluated result categories | `static`, `scrolling`, `screen_video`, `hard` from the existing ablation summaries | Results must remain pilot/descriptive until the 36 clips are annotated and rerun. |
| Dataset scale claim | 36 local 5-second mp4 clips; 0 active annotation CSV files found in the current filesystem check | Do not claim a fully annotated benchmark yet. |
| Ablation scope | 4 clips x 4 variants in committed CSV/JSON summaries | Descriptive only; no significance claims. |
| Manuscript figures | Old placeholder SVGs are archived | Generate real figures before final PDF. |

## Dataset State

`inputs/README.md` records the active video layout. `doc/paper/data_renaming_manifest.csv` remains a historical naming record for the earlier representative-clip workflow.

Current filesystem check:

- `inputs/static/`: 10 mp4 clips.
- `inputs/scrolling/`: 10 mp4 clips.
- `inputs/screen_video/`: 10 mp4 clips.
- `inputs/weak_border/`: 5 mp4 clips.
- `inputs/hard/`: 1 mp4 clip.
- Active annotation CSV files found: 0.
- Raw source videos are archived locally under `inputs/archive/raw_premodify_2026-07-14/`.
- Older unannotated backups remain under `inputs/archive/removed_unannotated_2026-07-14/`.

Current active video count:

| Category | Active mp4 clips | Active annotation CSV |
| --- | ---: | ---: |
| `static` | 10 | 0 |
| `scrolling` | 10 | 0 |
| `screen_video` | 10 | 0 |
| `weak_border` | 5 | 0 |
| `hard` | 1 | 0 |
| Total | 36 | 0 |

## Current Evidence

Committed evidence that can be cited only within the pilot scope:

- `doc/paper/results/ablation/ablation_table.csv`
- `doc/paper/results/ablation/ablation_clip_metrics.csv`
- `doc/paper/results/ablation/ablation_quality.json`
- `doc/paper/results/ablation/video_integrity.csv`
- `doc/paper/evidence/experiment_summary.csv`
- `doc/paper/evidence/run_manifest.md`
- `doc/paper/evidence/retained_runs.md`

Known limitations:

- The 36 active videos are not yet annotated in the current active layout.
- `no_offline_repair` was not meaningfully exercised; treat that ablation as inconclusive.
- `n=4` supports descriptive comparison only.
- The current manuscript still needs real figures and claim cleanup before submission.

## Done

- [x] Package and script entrypoints were reorganized by responsibility.
- [x] Ablation-capable runner and summary scripts exist.
- [x] Four-clip ablation summaries are committed.
- [x] Formal 5-second active video dataset is organized locally: 36 mp4 clips across five categories.
- [x] Non-current paper plans, operation records, generated reports, PDFs, and placeholder figures were archived.
- [x] Current paper workspace now has a single status entry.

## Next Missing Work

1. Annotate the active 36 clips, or explicitly choose a smaller labeled subset and record that scope.
2. Update the runner/report path so it skips clips without CSV labels and reports missing-label counts clearly.
3. Rerun main experiments and ablations on the chosen annotated scope.
4. Generate real figures from reviewed outputs; do not use archived placeholder SVGs as evidence.
5. Rewrite `paper_zh.md` and `paper_en.md` around the actual evaluated scope.
6. Remove all TBDs, placeholder figure references, and unsupported 50-video/full-benchmark claims.
7. Add failure-case evidence for at least scrolling drift and hard tracker freeze.
8. Rebuild PDFs only after the manuscript points to real figures and all numbers trace to committed CSV/JSON or retained runs.
