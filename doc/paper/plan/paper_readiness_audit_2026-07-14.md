# Paper Readiness Audit

Date: 2026-07-14

## Scope

This audit answers three questions against `doc/paper/outline_zh.md` and `doc/paper/figure_plan.md`:

1. What does the paper need in total?
2. What does the project already have?
3. What is still missing before the manuscript can be submitted honestly?

The current project has enough material for a limited, descriptive paper draft, but not enough for the original full 50-video benchmark claim. If the original outline is kept unchanged, the missing work is still large. If the scope is revised to a four-category representative pilot, the next work is mostly manuscript refill, real figures, failure evidence, and explicit limitations.

## Executive Summary

| Area | Original outline requires | Current project has | Status |
| --- | --- | --- | --- |
| Method claim | Border-guided homography, content/screen motion separation, failure recovery, temporal smoothing | Reference-anchored LK/RANSAC tracker with reliability gates, trajectory smoothing/repair, residual alignment; boundary/point-edge code exists but is not the frozen main result path | Partially ready; wording must match code |
| Dataset | 50 videos, 5 categories, 10 per category | 11 collected sources across 5 categories; current evaluated scope is 4 included categories and 4 representative clips; weak_border excluded | Not ready for 50-video claim |
| Annotation | Keyframe corner annotations, protocol, quality check/relabeling | Representative annotations exist for static, scrolling, screen_video, hard; no full 50-video protocol or repeated annotation QA | Partially ready |
| Main experiment | 3 methods over full dataset, 4 metric families, category and aggregate tables | Historical complete HTML reports for 4 representative clips; old pilot summary exists but is not formal main evidence | Pilot only |
| Ablation | Full + three module removals with valid module triggering | 4 clips x 4 variants complete; no_offline_repair not effectively triggered; n=4 only descriptive | Numerically complete, inferentially weak |
| Figures | Real Fig. 1-8 from reviewed runs | 8 placeholder SVGs; ablation HTML/table exists; no final manuscript figures | Not ready |
| Manuscript | No TBDs, real captions, synced zh/en claims | Chinese draft has 59 TBD tokens, English draft has 58; both cite 8 placeholder figures | Not ready |
| Reproducibility | Commit, environment, parameters, runtime, success criteria | Run manifest exists; method JSONs exist; formal hardware/software/runtime boundary still missing | Partially ready |

## What The Paper Needs In Total

### Section-Level Requirements

| Paper section | Required content | Required evidence |
| --- | --- | --- |
| Abstract | Problem, implemented method, dataset scope, strongest numeric results | Final geometry, temporal, detail, and success-rate numbers |
| Introduction | Motivation and contributions | Contributions must match implemented code and real dataset scope |
| Related Work | Screen processing, document rectification, visual tracking/stabilization | References and positioning; mostly prose-ready |
| Method | Pipeline overview, detection/tracking, homography, reliability checks, recovery, smoothing, rendering | Code-backed description, parameters, failure handling, method diagrams |
| Dataset | Categories, collection, annotation, examples | Dataset counts, clip IDs, annotation protocol, representative frames |
| Experiments | Metrics, baselines, implementation details | Exact formulas, method configs, environment, run manifest |
| Results | Quantitative, qualitative, temporal, detail/frequency, ablation, failures | Reviewed CSV/JSON results, real figures, failure screenshots/debug evidence |
| Discussion | Findings, limitations, future work | Must stay within evidence; no 50-video or demoiré claims unless supported |
| Conclusion | Summary of demonstrated contribution | Tied to actual completed scope |
| References/Supplement | Full citations and optional extra results | Bibliography, extra tables/figures if needed |

### Figure And Table Requirements

| Output | Original requirement | Current status | Missing |
| --- | --- | --- | --- |
| Fig. 1 Pipeline | Real frames showing input, evidence, homography, rectification, smoothing | Placeholder only | Extract real panels from one reviewed clip |
| Fig. 2 Dataset | Five categories, representative frames and corner annotations | Placeholder only; weak_border collected but excluded from current results | Decide whether Fig. 2 shows 5 collected classes or 4 evaluated classes; generate real panels |
| Fig. 3 Geometry | 3 methods x categories x corner RMSE/IoU/aspect error | Current pilot has 4 representative clips, not full table | Generate final geometry figure/table for chosen scope |
| Fig. 4 Temporal | Translation/rotation/scale curves and summary | Current metrics are trajectory diagnostics, not independent temporal truth | Either add independent temporal evidence or label as diagnostic |
| Fig. 5 Qualitative | Input + 3 methods across categories | Placeholder only | Select fixed frames and export real outputs |
| Fig. 6 Detail/Frequency | Crops, edge/gradient metrics, FFT diagnostics | Metric code and pilot outputs exist; no final figure | Fix subset and generate real panels |
| Fig. 7 Ablation | Full and 3 variants | CSV/HTML exists for 4 clips | Make final figure; mark offline repair inconclusive or replace clip |
| Fig. 8 Failure Cases | Three failures with diagnosis | Candidate failures: scrolling drift, hard tracker freeze | Capture screenshots/debug rows and write failure analysis |
| Optional Fig. 9 Speed | Runtime breakdown | Not currently required | Only include if runtime data is collected |
| Tables 1-4 | Geometry, temporal, detail, frequency by method/category | No formal full tables yet | Generate from reviewed run or revise to pilot tables |
| Table 5 | Ablation table | `doc/paper/results/ablation/ablation_table.csv` exists | Needs interpretation boundary |

## What The Project Already Has

### Data And Organization

- `doc/paper/data_renaming_manifest.csv` records 11 collected sources:
  - static: 3 sources, representative `static_02`
  - scrolling: 3 sources, representative `scrolling_03`
  - screen_video: 3 sources, representative `screen_video_03`
  - weak_border: 1 source, excluded from current evaluated scope
  - hard: 1 source, representative `hard_01`
- Current evidence scope is four included categories: static, scrolling, screen_video, hard.
- Historical HTML links were repaired to the renamed dataset paths.
- `inputs/README.md` documents the current input layout.

### Code And Experiment Pipeline

- Main package is organized under:
  - `screen_normalize/algorithms/`
  - `screen_normalize/experiments/`
  - `screen_normalize/metrics/`
- Script entrypoints are grouped under:
  - `scripts/diagnostics/`
  - `scripts/dataset/`
  - `scripts/paper/`
  - `scripts/paper/ablation/`
- The runner supports:
  - `frame_wise`
  - `optical_flow`
  - `proposed`
  - `point_edge`
  - `no_reliability_gates`
  - `no_trajectory_smoothing`
  - `no_offline_repair`
- Metric families exist for geometry, temporal, detail, and frequency.

### Existing Results

- Four-clip ablation run: `runs/20260713_ablation`
- Committed summary files:
  - `doc/paper/results/ablation/ablation_clip_metrics.csv`
  - `doc/paper/results/ablation/ablation_table.csv`
  - `doc/paper/results/ablation/ablation_quality.json`
  - `doc/paper/results/ablation/video_integrity.csv`
  - `doc/paper/results/ablation/ablation_report.html`
- Completion:
  - 16/16 method outputs observed
  - 64/64 metric JSON files observed
  - 4 clips x 4 variants summarized
- Important limitations already recorded:
  - n=4 supports descriptive pilot results only
  - hard/proposed has poor geometry and tracker freeze
  - scrolling/proposed has poor geometry
  - no_offline_repair was not meaningfully exercised

### Manuscript Assets

- Chinese and English manuscript drafts exist.
- Eight placeholder figures exist under `doc/paper/manuscript/figures/placeholders/`.
- Current gaps from `ablation_quality.json`:
  - `paper_zh.md`: 59 TBD tokens, 8 placeholder figure references
  - `paper_en.md`: 58 TBD tokens, 8 placeholder figure references

## What Is Missing

### Critical Missing Items Before Submission

1. Decide final paper scope.
   - Option A: original full paper: 50 videos, 5 categories, full formal evaluation.
   - Option B: honest current paper: four-category representative pilot, explicitly descriptive, no broad benchmark claim.

2. Align method claims with implemented code.
   - Do not claim the main result is a fully border-guided screen-motion/content-motion separator unless that exact path becomes the evaluated method.
   - Current safe wording: reference-anchored feature tracking with geometric reliability gates, trajectory repair/smoothing, and rectified rendering.

3. Replace all placeholder figures.
   - Fig. 1-8 are currently placeholders.
   - Figure 7 has numeric data but still needs final manuscript figure generation.

4. Refill manuscript TBD fields.
   - Dataset status, annotation protocol, parameter table, temporal definition, subset definition, hardware/software, success criteria, quantitative results, failure cases, code release, author contributions.

5. Add failure evidence.
   - Capture visual/debug evidence for at least:
     - scrolling drift / geometry failure
     - hard tracker freeze
     - one additional visible failure or limitation

6. Add reproducibility metadata.
   - Git commit
   - Python/OpenCV/NumPy/FFmpeg versions
   - hardware/OS
   - runtime boundary
   - success/failure criteria

### Missing If Keeping The Original 50-Video Outline

- Collect or formalize 50 videos: 10 per category.
- Include weak_border in evaluation.
- Complete keyframe annotation for all 50 clips.
- Run 50 clips x 3 main methods.
- Run valid ablations across a representative subset or all clips.
- Create independent temporal validation, not only method self-trajectory diagnostics.
- Produce category-level and aggregate statistics with paired uncertainty.
- Generate all final figures and tables from the reviewed formal run.

### Missing If Writing The Current Four-Clip Paper

- Revise Abstract, Dataset, Experiments, Results, and Discussion to avoid the 50-video benchmark claim.
- State that the current results are a four-clip descriptive pilot.
- Use four categories as evaluated scope; mention weak_border as collected but excluded.
- Replace Fig. 3-7 with pilot figures/tables and make sample sizes explicit.
- Either remove the offline-repair ablation conclusion or label it inconclusive.
- Do not report statistical significance.
- Keep temporal metrics as diagnostics unless independent temporal evidence is added.

## Recommended Next Sequence

1. Freeze scope in writing.
   - Recommended for speed: write a four-category representative pilot paper.
   - If the instructor requires the original benchmark, restart from the 50-video requirements.

2. Generate real manuscript figures in this order:
   - Fig. 7 ablation from existing CSV
   - Fig. 2 dataset examples from collected frames/annotations
   - Fig. 5 qualitative comparison from existing representative reports
   - Fig. 8 failure cases from scrolling and hard debug evidence
   - Fig. 3/Fig. 4/Fig. 6 from reviewed current metrics, with diagnostic labels where needed
   - Fig. 1 pipeline panels from one stable static clip

3. Fill reproducibility metadata.

4. Rewrite the Results section around evidence that actually exists.

5. Sync `paper_zh.md` and `paper_en.md`.

6. Build PDF and run final QA:
   - no TBD tokens
   - no placeholder figures
   - no unsupported 50-video claim
   - all numbers trace to committed CSV/JSON or retained run evidence

## Bottom Line

The project currently has a usable experimental core and enough evidence for a limited pilot-style paper. It does not yet satisfy the original outline as a 50-video, five-category benchmark paper. The main missing work is not more code architecture; it is scope decision, real figure generation, manuscript refill, failure evidence, and strict wording so the paper does not overclaim beyond the four representative clips.
