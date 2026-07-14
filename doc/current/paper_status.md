# Current Paper Status

Date: 2026-07-14

This file is the current status entry for the manuscript. One-off experiment outputs remain archived; the manuscript should only cite the evidence batches listed here.

## Current Scope

The project has a local 50-clip captured-screen video collection with matching corner-annotation CSV files. The active annotations now include non-initialization labels for all 50 clips, giving 248 annotated frames in total and 199 scored non-initialization frames.

The current manuscript describes the dataset as the 50-clip collection. The reported numerical tables use the archived geometry/temporal rerun after annotation completion. Earlier full first-pass outputs remain archived as engineering evidence, but they are not the main source for the rewritten numerical claims.

| Area | Current fact | Manuscript implication |
| --- | --- | --- |
| Dataset | 50 clips, 14985 frames, five capture conditions | Describe the full collection as the dataset. |
| Annotations | 248 annotated frames, 199 scored non-initialization frames | State that all active clips now have non-initialization geometry labels. |
| Main reported comparison | Current geometry/temporal rerun | Use for the main results tables and figures. |
| Reported ablation | Current geometry/temporal rerun | Use to explain the reliability-gate trade-off. |
| Earlier full first pass | 50 clips, archived | Use only as supporting provenance, not as the current main result. |
| Tuning smoke test | Archived diagnostic only | Do not cite in the main manuscript. |
| Manuscript | English and Chinese Markdown, HTML, and PDF regenerated around the current evidence | Rebuild exports after any later source edits. |

## Current Document Paths

- Current entry: `doc/current/README.md`
- Current status: `doc/current/paper_status.md`
- Current outline: `doc/current/paper_outline_zh.md`
- Current figure plan: `doc/current/figure_plan.md`
- Current manuscript: `doc/current/paper/manuscript/`
- Current references: `doc/current/paper/references/`
- Current proposal: `doc/current/paper/source/proposal.pdf`

## Archived Evidence In Use

- Primary reported rerun: `doc/archive/paper_results/2026-07-14-annotated-two-per-category/`
- Main comparison metrics: `doc/archive/paper_results/2026-07-14-annotated-two-per-category/results/main_geometry_temporal/`
- Ablation metrics: `doc/archive/paper_results/2026-07-14-annotated-two-per-category/results/ablation_geometry_temporal/`
- Earlier full first pass, supporting only: `doc/archive/paper_results/2026-07-14-first-pass/`

## Dataset State

| Capture condition | Active mp4 clips | Active annotation CSV |
| --- | ---: | ---: |
| Static pages | 10 | 10 |
| Scrolling pages | 10 | 10 |
| Videos playing on the screen | 10 | 10 |
| Weak-border scenes | 10 | 10 |
| Challenging scenes | 10 | 10 |
| Total | 50 | 50 |

`inputs/README.md` records the active video layout. Raw source videos and older backups remain under local `inputs/archive/` paths and are not part of the tracked manuscript evidence.

## Current Manuscript Claim

The paper should make a bounded claim: reference-frame anchoring reduces estimated trajectory variation in the current annotated evaluation, but it does not improve annotated screen geometry. The main mechanism is the reliability gate: it suppresses short-term jitter while also freezing stale geometry when screen-plane evidence is weak or misleading.

The paper should not claim demoireing quality, full content restoration, overall superiority, or successful completion of the original border-dominant design.

## Current Figures and Tables

- Figure 1: Method pipeline.
- Figure 2: Dataset examples and corner annotations.
- Figure 3: Geometry and temporal comparison in the current annotated rerun.
- Figure 4: Category-level geometry and temporal stress.
- Figure 5: Qualitative examples.
- Table 1: Dataset scope.
- Table 2: Main geometry and temporal metrics.
- Table 3: Ablation metrics.

Detail/frequency diagnostics, failure timelines, tuning smoke-test plots, processing-output counts, and runtime bookkeeping are not main-text evidence in the rewritten manuscript.

## Known Limitations

- The manuscript describes the dataset as the full 50-clip collection. Exact run scope for the current geometry/temporal evidence remains in the archive records.
- Geometry labels are sparse keyframes rather than dense frame-level ground truth.
- The temporal metric is derived from the estimated quadrilateral and should not be interpreted as independent physical stabilization ground truth.
- The qualitative examples still need a final manual review pass if the figures are used for a polished submission.
- The current system still relies on reference-plane feature evidence and does not yet use physical screen borders as the dominant per-frame signal.

## Done

- [x] Active video and annotation inventory checked: 50 active clips and 50 active annotation CSV files.
- [x] Scrolling annotations added to the active evidence state.
- [x] Annotated geometry/temporal rerun completed and archived.
- [x] English and Chinese manuscript Markdown rewritten around the current evidence.
- [x] English and Chinese HTML/PDF exports regenerated from the rewritten Markdown.
- [x] Current manuscript avoids raw parameter flags, code-style category labels, smoke-test claims, and project-output bookkeeping in the main argument.

## Next Missing Work

1. Manually review Figure 5 qualitative selections and replace any weak examples.
2. If time permits, rerun the full 50-clip geometry/temporal comparison under the completed annotation state.
3. Rebuild figures from source scripts with final reader-facing method labels instead of patching labels in exported SVGs.
