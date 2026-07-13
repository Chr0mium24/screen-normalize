# Current Paper Status

Date: 2026-07-14

This file is the current status entry for the paper workspace. Older plans, generated reports, placeholder figures, and one-off operation records were moved to `doc/archive/paper_workspace_cleanup_2026-07-14/`.

## Current Scope

The current data scope is a local 50-clip, five-category video collection with matching local annotation CSV files. The current evaluated-result scope is still a four-clip ablation pilot, because the 50 active clips have not yet been processed through a reviewed full experiment run.

| Area | Current fact | Paper implication |
| --- | --- | --- |
| Active video categories | `static`, `scrolling`, `screen_video`, `weak_border`, `hard` | Dataset section can describe the 50 collected and annotated clips. |
| Evaluated result categories | `static`, `scrolling`, `screen_video`, `hard` from the existing ablation summaries | Results must remain pilot/descriptive until the 50 clips are rerun and reviewed. |
| Dataset scale claim | 50 local 5-second mp4 clips; 50 active annotation CSV files found in the current filesystem check | The dataset can be described as locally annotated, but not yet as fully evaluated. |
| Ablation scope | 4 clips x 4 variants in committed CSV/JSON summaries | Descriptive only; no significance claims. |
| Manuscript figures | Old placeholder SVGs are archived | Generate real figures before final PDF. |

## Dataset State

`inputs/README.md` records the active video layout. `doc/paper/data_renaming_manifest.csv` remains a historical naming record for the earlier representative-clip workflow.

Current filesystem check:

- `inputs/static/`: 10 mp4 clips.
- `inputs/scrolling/`: 10 mp4 clips.
- `inputs/screen_video/`: 10 mp4 clips.
- `inputs/weak_border/`: 10 mp4 clips.
- `inputs/hard/`: 10 mp4 clips.
- Active annotation CSV files found: 50.
- Raw source videos are archived locally under `inputs/archive/raw_premodify_2026-07-14/`.
- Older unannotated backups remain under `inputs/archive/removed_unannotated_2026-07-14/`.

Current active video count:

| Category | Active mp4 clips | Active annotation CSV |
| --- | ---: | ---: |
| `static` | 10 | 10 |
| `scrolling` | 10 | 10 |
| `screen_video` | 10 | 10 |
| `weak_border` | 10 | 10 |
| `hard` | 10 | 10 |
| Total | 50 | 50 |

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

- The 50 active videos have local annotation CSV files, but they have not yet been processed through a reviewed full three-method experiment run.
- `no_offline_repair` was not meaningfully exercised; treat that ablation as inconclusive.
- `n=4` supports descriptive comparison only.
- The current manuscript still needs real figures and claim cleanup before submission.

## Done

- [x] Package and script entrypoints were reorganized by responsibility.
- [x] Ablation-capable runner and summary scripts exist.
- [x] Four-clip ablation summaries are committed.
- [x] Formal 5-second active video dataset is organized locally: 50 mp4 clips across five categories.
- [x] Active dataset has matching local annotation CSV files for all 50 clips.
- [x] Non-current paper plans, operation records, generated reports, PDFs, and placeholder figures were archived.
- [x] Current paper workspace now has a single status entry.

## Next Missing Work

1. Run a small smoke batch on the active annotated layout to confirm the runner reads the 50 direct child clips and CSV files correctly.
2. Run the full 50-clip three-method experiment: `frame_wise`, `optical_flow`, and `proposed` with geometry, temporal, detail, and frequency metrics.
3. Review the generated HTML reports and record any failed clips, frozen trackers, drift, or unusable metrics before aggregating.
4. Rerun or extend ablations on the evaluated scope; the current four-clip ablation remains descriptive, and `no_offline_repair` is inconclusive.
5. Generate real figures from reviewed outputs; do not use archived placeholder SVGs as evidence.
6. Rewrite `paper_zh.md` and `paper_en.md` around the actual evaluated scope and replace every TBD.
7. Add failure-case evidence for at least scrolling drift and hard tracker freeze.
8. Rebuild PDFs only after the manuscript points to real figures and all numbers trace to committed CSV/JSON or retained runs.
