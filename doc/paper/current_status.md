# Current Paper Status

Date: 2026-07-14

This file is the current status entry for the paper workspace. Older plans, generated reports, placeholder figures, and one-off operation records were moved to `doc/archive/paper_workspace_cleanup_2026-07-14/`.

## Current Scope

The current data scope is a local 50-clip, five-category video collection with matching local annotation CSV files. The current evaluated-result scope is now a computational first pass over all 50 active clips for the three main methods and three ablation methods. These outputs are not yet manually reviewed final evidence.

| Area | Current fact | Paper implication |
| --- | --- | --- |
| Active video categories | `static`, `scrolling`, `screen_video`, `weak_border`, `hard` | Dataset section can describe the 50 collected and annotated clips. |
| Evaluated result categories | all five active categories in the 2026-07-14 first-pass runs | Results can be described as first-pass computational outputs, not final reviewed claims. |
| Dataset scale claim | 50 local 5-second mp4 clips; 50 active annotation CSV files found in the current filesystem check | The dataset can be described as locally annotated and processed once. |
| Main first-pass scope | 50 clips x 3 methods x 4 metrics | `geometry` has 15 skipped records from five scrolling clips; other metrics completed. |
| Ablation first-pass scope | 50 clips x 4 compared methods x 4 metrics, with `proposed` read from the main run | `geometry` has 20 skipped records from five scrolling clips; offline repair remains potentially inconclusive. |
| Manuscript figures | Fig. 3 and Fig. 6 first-pass SVGs generated; Fig. 4 and Fig. 7 omitted by current summary limitations | Generate/rebuild real final figures before final PDF. |

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

Committed first-pass evidence:

- `doc/paper/evidence/full_pipeline_first_pass_2026-07-14.md`
- `doc/paper/results/full_pipeline_first_pass/`
- `doc/paper/results/full_ablation_first_pass/`

Older pilot evidence that should be treated as historical unless explicitly cited:

- `doc/paper/results/ablation/ablation_table.csv`
- `doc/paper/results/ablation/ablation_clip_metrics.csv`
- `doc/paper/results/ablation/ablation_quality.json`
- `doc/paper/results/ablation/video_integrity.csv`
- `doc/paper/evidence/experiment_summary.csv`
- `doc/paper/evidence/run_manifest.md`
- `doc/paper/evidence/retained_runs.md`

Known limitations:

- The first-pass outputs have not been manually reviewed clip by clip.
- `scrolling_06` through `scrolling_10` have geometry status `skipped` because annotation frames and estimate frames do not overlap.
- `no_offline_repair` matches `proposed` in aggregate first-pass primary metrics; treat that ablation as potentially inconclusive until repair-triggering intervals are audited.
- The summary script omitted Fig. 4 because it expects `point_edge` alongside the three main methods; this is a reporting-script limitation, not missing temporal metric JSON.
- Fig. 7 still needs a formal plotting path for the full ablation first-pass summary.
- The current manuscript still needs real figures and claim cleanup before submission.

## Done

- [x] Package and script entrypoints were reorganized by responsibility.
- [x] Ablation-capable runner and summary scripts exist.
- [x] Four-clip ablation summaries are committed.
- [x] Formal 5-second active video dataset is organized locally: 50 mp4 clips across five categories.
- [x] Active dataset has matching local annotation CSV files for all 50 clips.
- [x] 50-clip three-method first pass completed: 50/50 batch `ok`, 150 method videos, 600 metric JSON files.
- [x] 50-clip three-ablation first pass completed: 50/50 batch `ok`, 150 ablation method videos, 600 ablation metric JSON files.
- [x] First-pass summary evidence committed under `doc/paper/results/full_pipeline_first_pass/` and `doc/paper/results/full_ablation_first_pass/`.
- [x] Non-current paper plans, operation records, generated reports, PDFs, and placeholder figures were archived.
- [x] Current paper workspace now has a single status entry.

## Next Missing Work

1. Manually review the generated HTML/video reports, especially `hard`, `weak_border`, and scrolling clips with high rejection counts.
2. Fix or explicitly explain the `scrolling_06` through `scrolling_10` geometry skip caused by non-overlapping annotation and estimate frames.
3. Decide how to handle `no_offline_repair`: find repair-triggering intervals or mark the ablation inconclusive.
4. Update the paper summary/plotting path so Fig. 4 can use the three-method temporal outputs and Fig. 7 can use the full ablation first-pass summary.
5. Generate final real figures from reviewed outputs; do not use archived placeholder SVGs as evidence.
6. Rewrite `paper_zh.md` and `paper_en.md` around the first-pass/reviewed scope and replace every TBD.
7. Add failure-case evidence for at least scrolling drift and hard/weak-border tracker freeze.
8. Rebuild PDFs only after the manuscript points to real figures and all numbers trace to committed CSV/JSON or retained runs.
