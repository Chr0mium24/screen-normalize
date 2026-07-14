# Manuscript Restructure Notes, 2026-07-14

## Skill Route

- Writing route: `research-paper-writing` + `nature-writing`
- Figure route: `nature-figure`
- Detected paper type: algorithmic / methods-style computer-vision system
- Language handling: Chinese author notes with English and Chinese manuscript outputs
- Journal stance: generic, Nature-leaning structure without claiming Nature submission compliance
- Figure backend: Python / matplotlib, using PNG previews plus SVG/PDF editable exports

## One-Sentence Argument

In real captured-screen videos, we show that a reference-anchored screen-plane
normalization pipeline can strongly reduce trajectory-derived variation, but the
first-pass benchmark reveals a reliability-gate trade-off: conservative gates
create smooth outputs by holding stale geometry under dynamic content, weak
borders, and hard viewpoints.

## Terminology Ledger

| Canonical term | First-use definition | Variants avoided | Decision |
|---|---|---|---|
| Captured-screen video | Handheld camera video of a physical display | screen capture video, phone-recorded screen | Use captured-screen video in English; use 拍屏视频 in Chinese |
| Screen-plane normalization | Recovering a frontal screen-coordinate video from a full-scene recording | rectification, stabilization, correction | Use for the whole front-end task |
| Proposed | Reference-anchored pipeline with gates, repair, smoothing, and residual alignment | our method, dynamic method | Use `Proposed` in metrics/tables; define once in Method |
| Frame-wise | Per-frame independent quadrilateral estimation baseline | detector baseline | Use `Frame-wise` |
| Optical flow | Adjacent-frame propagation baseline | LK baseline, flow baseline | Use `Optical flow` |
| Reliability gates | Explicit checks that accept or reject candidate quadrilateral updates | filters, thresholds | Use `reliability gates` |
| Trajectory-derived variation | Motion diagnostic computed from estimated quadrilateral changes | temporal stability score | Use diagnostic wording to avoid overclaiming physical stability |
| Edge-preservation index | Local edge-consistency diagnostic | edge F1, detail score | Use full term in prose and F1 label in figures |

## Revised Section Architecture

1. Abstract: lead with the benchmarked trade-off, not a full experiment log.
2. Introduction: task relevance -> motion ambiguity -> benchmark contribution -> explicit boundary.
3. Method: task formulation -> reference-anchored pipeline -> compared methods.
4. Dataset and metrics: preserve protocol, annotation exclusions, and diagnostic metric caveats.
5. Results: run completion -> core trade-off -> category stress -> qualitative/detail evidence -> ablation -> failure/tuning smoke.
6. Discussion: interpret why gates help and fail, then name the physical-border evidence gap.
7. Conclusion: bounded contribution and next benchmark step.

## Figure Contract

Core conclusion: the implemented system exposes a stability-accuracy trade-off,
with reliability gates as the main engineering lever.

Figure archetype: asymmetric mixed-modality figure set.

Target output: manuscript PNG for Markdown/PDF rendering, plus SVG/PDF exports
for editable figure files.

Panel map:

- Figure 1: pipeline schematic plus real input/output evidence.
- Figure 2: dataset scale and representative categories.
- Figure 3: hero trade-off plot plus aggregate metric panels.
- Figure 4: category stress matrix connecting geometry, trajectory variation, and accepted updates.
- Figure 5: qualitative method comparison across representative clips.
- Figure 6: local detail and FFT diagnostics.
- Figure 7: ablation trade-off showing reliability gates as the main lever.
- Figure 8: failure modes plus tuning smoke acceptance signal.

Reviewer risk:

- Risk: readers may interpret low temporal variation as true stabilization.
- Fix: manuscript now states that temporal variation is trajectory-derived and must be read with geometry and edge metrics.
- Risk: tuning smoke test may be mistaken for a full rerun.
- Fix: manuscript labels it as diagnostic and excludes it from formal aggregate claims.
- Risk: Proposed appears worse on aggregate geometry.
- Fix: manuscript frames the contribution as auditable benchmark and failure analysis, not overall superiority.

## Claim-Evidence Map

| Claim | Evidence | Status |
|---|---|---|
| The first-pass pipeline runs end to end on the full dataset | 50/50 clips completed; 150 videos, 600 metric JSON files, 50 reports | supported |
| Proposed strongly reduces trajectory-derived variation | Median translation variation 0.254 px/frame vs 4.886 and 12.311 | supported |
| Proposed is not overall geometrically superior | Median corner RMSE 191.83 px vs 32.56 and 34.88; edge F1 lower | supported |
| Conservative gates drive the trade-off | No-gates ablation improves RMSE to 35.63 and IoU to 0.968 but raises temporal variation to 6.165 | supported |
| Softer gates reduce over-freezing on selected examples | Smoke rerun acceptance and RMSE improvements on `hard_01` and `weak_border_10` | supported as diagnostic only |
| Scrolling needs physical-border evidence | `scrolling_05` worsens after tuning despite more accepted updates | inferred from diagnostic evidence |

## Self-Review

- Contribution: pass as a benchmarked engineering front end and failure analysis; not framed as SOTA restoration.
- Writing clarity: improved by separating task, method, results, ablation, and limitations.
- Experimental strength: enough for a course first-pass evaluation, not enough for broad generalization.
- Evaluation completeness: includes baselines, metrics, ablation, failure cases, and tuning smoke; lacks full tuned rerun.
- Method soundness: main weakness is still the missing physical-border evidence module.
