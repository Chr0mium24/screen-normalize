# Current Paper Status

Date: 2026-07-14

This file is the current status entry for the paper. Stable, one-off experiment outputs are archived under `../archive/paper_results/2026-07-14-first-pass/`; this file points to that evidence but stays short and current.

## Current Scope

The current data scope is a local 50-clip, five-category captured-screen video collection with matching local annotation CSV files. The active CSV set now includes non-initialization annotations for the previously incomplete scrolling clips. The current result scope includes the original computational first pass over all 50 active clips and a newer two-clips-per-category geometry/temporal rerun after annotation completion. These outputs are usable for drafting but are not manually reviewed final evidence.

| Area | Current fact | Paper implication |
| --- | --- | --- |
| Active video categories | `static`, `scrolling`, `screen_video`, `weak_border`, `hard` | Dataset section can describe a 50-clip, five-category benchmark. |
| Main first pass | 50 clips x 3 methods x 4 metrics | Results can discuss a stability-accuracy trade-off, with first-pass caveats. |
| Ablation first pass | 50 clips x 4 compared variants x 4 metrics | Reliability gates and smoothing can be discussed; offline repair remains inconclusive. |
| Annotated subset rerun | 10 clips x main/ablation methods x geometry/temporal | Use this as the current lightweight evidence that every included category has non-initialization geometry labels. |
| Proposed tuning | 1-2 smoke clips per category | Shows softened gates can help over-freezing cases, but this is not a full replacement run. |
| Manuscript | Current Chinese and English Markdown, HTML, and PDF exist | The paper is complete enough to review, not ready for final submission claims. |
| Figures | Eight main figures exist in PNG/SVG/PDF form | Figures are current manuscript assets; raw result figures remain archived. |

## Current Document Paths

- Current entry: `doc/current/README.md`
- Current status: `doc/current/paper_status.md`
- Current outline: `doc/current/paper_outline_zh.md`
- Current figure plan: `doc/current/figure_plan.md`
- Current manuscript: `doc/current/paper/manuscript/`
- Current references: `doc/current/paper/references/`
- Current proposal: `doc/current/paper/source/proposal.pdf`

## Archived Evidence In Use

- Main first pass: `doc/archive/paper_results/2026-07-14-first-pass/results/full_pipeline_first_pass/`
- Full ablation first pass: `doc/archive/paper_results/2026-07-14-first-pass/results/full_ablation_first_pass/`
- Annotated two-per-category geometry/temporal rerun: `doc/archive/paper_results/2026-07-14-annotated-two-per-category/`
- Older four-clip pilot ablation: `doc/archive/paper_results/2026-07-14-first-pass/results/ablation/`
- Proposed tuning smoke: `doc/archive/paper_results/2026-07-14-first-pass/results/proposed_tuning_2026-07-14.md`
- Tuning smoke table: `doc/archive/paper_results/2026-07-14-first-pass/results/proposed_tuning_smoke.csv`
- Run evidence notes: `doc/archive/paper_results/2026-07-14-first-pass/evidence/`
- Dataset naming record: `doc/archive/paper_results/2026-07-14-first-pass/data_renaming_manifest.csv`

## Dataset State

| Category | Active mp4 clips | Active annotation CSV |
| --- | ---: | ---: |
| `static` | 10 | 10 |
| `scrolling` | 10 | 10 |
| `screen_video` | 10 | 10 |
| `weak_border` | 10 | 10 |
| `hard` | 10 | 10 |
| Total | 50 | 50 |

`inputs/README.md` records the active video layout. Raw source videos and older unannotated backups remain under local `inputs/archive/` paths and are not part of the tracked paper evidence.

## Known Limitations

- The first-pass outputs have not been manually reviewed clip by clip.
- The original full first-pass summaries were produced before the current completed annotation state; use the annotated two-per-category rerun for updated geometry/temporal wording.
- Proposed is visually and trajectory stable, but the first-pass geometry and detail metrics are not universally better.
- The softened-gate tuning smoke improves several over-freezing hard/weak-border cases, but scrolling still needs stronger physical-border evidence.
- `no_offline_repair` is still potentially inconclusive because the archived first pass did not isolate clear repair-triggering intervals.

## Done

- [x] Code package and script entrypoints are organized by responsibility.
- [x] 50-clip three-method first pass completed: 50/50 batch `ok`, 150 method videos, 600 metric JSON files.
- [x] 50-clip three-ablation first pass completed: 50/50 batch `ok`, 150 ablation method videos, 600 ablation metric JSON files.
- [x] First-pass result tables, figures, raw text metric archive, and evidence notes are archived under `doc/archive/paper_results/2026-07-14-first-pass/`.
- [x] Annotated two-per-category geometry/temporal rerun completed and archived.
- [x] Current manuscript assets are under `doc/current/paper/manuscript/`.
- [x] Current documents and archived result records are separated into different paths.

## Next Missing Work

1. Manually review the generated HTML/video reports, especially `hard`, `weak_border`, and scrolling clips with high rejection counts.
2. Decide whether to replace manuscript tables with the annotated subset rerun now, or wait for a full 50-clip geometry/temporal rerun.
3. Decide whether `no_offline_repair` should stay in the paper or be marked inconclusive.
4. If time permits, run a small formal tuned-Proposed subset and update only the evidence batch that the manuscript cites.
5. Re-check paper claims after manual review so the text does not imply Proposed is an overall winner when the data support a trade-off.
