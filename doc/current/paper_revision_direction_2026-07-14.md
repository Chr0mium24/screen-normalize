# Paper Revision Direction - 2026-07-14

## Core decision

The manuscript should read like a paper, not like a project progress report. It should describe what the current work does, what evidence supports it, and where the evaluated scope ends. It should not volunteer project-internal gaps, abandoned proposal elements, code-style labels, or internal method names in high-level sections.

## Problems to fix

### 1. Do not write project non-deliverables as paper claims

Current risk:

- The manuscript says or implies that the project did not complete some originally planned component.
- Phrases such as "not a completed demoireing method" or "falls short of the original proposal" sound like a progress report.

Revision direction:

- State the positive scope instead: this paper evaluates geometric screen-plane normalization for captured-screen videos.
- Put exclusions only as scope boundaries, not confessions.
- In Discussion, write that content restoration or demoireing is outside the evaluated scope, rather than saying the project failed to build it.

Preferred framing:

> This work focuses on geometric screen-plane normalization as a preprocessing step for captured-screen video restoration.

Avoid:

> This is not a completed demoireing method.

### 2. Do not put internal baseline names in the abstract

Current risk:

- Names such as `Frame-wise`, `Optical flow`, and `Proposed` appear too early.
- They are experiment labels, not concepts a reader understands before the paper defines them.

Revision direction:

- The abstract should describe comparison classes in plain language.
- Formal method labels should first appear in the Experiments or Compared Methods section.

Preferred abstract language:

> Compared with frame-level detection and adjacent-frame tracking alternatives, the reference-anchored pipeline produced smoother estimated trajectories, but this did not consistently translate into better annotated screen geometry.

Avoid:

> Proposed outperforms Frame-wise and Optical flow on translation variation.

### 3. Reduce unexplained custom metrics in the abstract

Current risk:

- The abstract currently exposes too many project-defined metrics, such as trajectory-derived translation variation, edge preservation index, and FFT orthogonality.
- These are valid diagnostics only after the evaluation protocol explains them.

Revision direction:

- In the abstract, keep only the two central result dimensions:
  1. estimated trajectory smoothness / temporal stability;
  2. annotated screen geometry.
- Move detail, edge, and FFT diagnostics to Evaluation and Results.
- If a number is used in the abstract, pair it with a plain-language interpretation.

### 4. Replace code-style category names in paper prose

Current risk:

- Category labels such as `screen_video`, `weak_border`, and `hard` are code or directory names.
- They make the manuscript sound like a repository report.

Revision direction:

- Use reader-facing labels in prose, tables, and figures.
- Keep raw directory names only in reproducibility notes if needed.

Mapping:

| Code label | Paper label |
| --- | --- |
| `static` | static pages / static-screen videos |
| `scrolling` | scrolling pages |
| `screen_video` | videos playing on the screen |
| `weak_border` | weak-border scenes |
| `hard` | challenging scenes |

### 5. Update scrolling annotation status

Current risk:

- Current status and manuscript text say five scrolling clips have only frame-0 annotations and their geometry metrics are skipped.
- The user reports that scrolling annotations have now been completed.

Revision direction:

- Update `doc/current/paper_status.md` to reflect the new annotation state.
- Recompute or regenerate the metric summaries before changing manuscript numbers.
- If annotations are updated but metrics have not been rerun, write that clearly as "annotations updated; metrics pending rerun."
- After rerun, update:
  - Dataset annotation counts;
  - number of clips with geometry metrics;
  - aggregate geometry tables;
  - category-level scrolling geometry results;
  - any figure generated from geometry metrics.

### 6. Keep the actual method story: reference-anchored LK + RANSAC + gates

Current risk:

- `paper_outline_zh.md` and `figure_plan.md` still describe a border-guided homography method.
- The implemented and current manuscript method is reference-anchored sparse LK tracking, RANSAC homography estimation, and reliability gating.

Revision direction:

- Update the outline and figure plan to match the implemented method.
- Do not rewrite the manuscript method toward the old border-guided plan unless that module is implemented and the benchmark is rerun.

Correct method framing:

> The method initializes a screen quadrilateral, tracks sparse reference-plane features with pyramidal Lucas-Kanade optical flow, estimates a RANSAC homography, applies reliability gates, repairs and smooths the corner trajectory, and warps frames to a frontal screen coordinate system.

### 7. Do not expose raw configuration flags in the main text

Current risk:

- The manuscript directly lists implementation flags such as `smooth=0.85`, `median_window=5`, `trajectory_window=9`, `interpolate=true`, `geometry_gate=true`, `reference_align=true`, and `reference_reliability_gates=true`.
- This reads like a command-line configuration dump, not a methods description.

Revision direction:

- In the main Methods section, describe the roles of smoothing, interpolation, geometry gating, reference alignment, and reliability gating in prose.
- Put exact parameter values in a compact implementation-details table, appendix, or reproducibility note only if needed.
- Explain why a parameter family exists before listing any value.

Preferred framing:

> The final configuration combines reliability-gated reference tracking with short-window trajectory repair and temporal smoothing. Exact implementation parameters are reported with the reproducibility materials.

Avoid:

> The formal Proposed configuration is `smooth=0.85`, `median_window=5`, ...

### 8. Replace low-information dataset figures

Current risk:

- The current dataset figure mainly shows category distribution and representative frames.
- A figure that only proves "we have five folders of videos" has low scientific value.

Revision direction:

- The dataset figure should teach the reader what makes the benchmark difficult.
- Prefer examples with visible annotation overlays, motion/content-change cues, weak-border cases, and failure-relevant variation.
- If possible, include a compact panel that links category difficulty to evaluation coverage, such as number of annotated frames per category or representative corner annotations.
- Avoid making a dataset figure that is only a visual inventory.

Better figure purpose:

> Show the visual conditions and annotation targets that make screen-plane normalization difficult.

### 9. Tighten the paper structure around one argument

Current risk:

- The current manuscript can feel like a sequence of completed project tasks: pipeline, dataset, metrics, generated reports, ablation, smoke test, limitations.
- The reader should instead feel one continuous argument: dynamic screen content makes stable geometry hard; reference anchoring improves smoothness but can freeze incorrect geometry; evaluation exposes the trade-off.

Revision direction:

- Reorder Results so every subsection serves the trade-off argument.
- Remove subsections that only report execution completion.
- Use Results sections for evidence, not project management.

Suggested Results structure:

1. Benchmark and evaluation setup in one compact subsection.
2. Main trade-off: smoother estimated trajectories versus mixed annotated geometry.
3. Category analysis: where the trade-off appears.
4. Ablation: reliability gates are the main lever.
5. Failure analysis: stale geometry and content-motion contamination.

### 10. Remove production-count bookkeeping from the manuscript

Current risk:

- Sentences such as "the three methods produced 150 rectified videos, 600 metric JSON files, and 50 HTML audit reports" are repository bookkeeping.
- They prove the pipeline ran, but they do not advance the scientific or engineering argument.

Revision direction:

- Move these facts to reproducibility documentation, run records, or appendix.
- In the manuscript, report only what affects trust in the results: dataset size, annotation coverage, compared methods, evaluation metrics, and success/failure rates if relevant.

Preferred manuscript language:

> All 50 clips were processed successfully for the compared methods, allowing aggregate comparison across the five scene types.

Avoid:

> The three methods produced 150 rectified videos, 600 metric JSON files, and 50 HTML audit reports.

### 11. Exclude engineering work unrelated to the paper objective

Current risk:

- Project documents may include implementation cleanup, report generation, HTML audit tooling, archive organization, or other engineering work.
- These are useful for the repository but distract from the paper's claim if they enter the manuscript.

Revision direction:

- Keep engineering-management details in `doc/current/paper_status.md`, run records, or repository documentation.
- Manuscript content should be limited to:
  - problem motivation;
  - evaluated method;
  - dataset and annotation protocol;
  - metrics and comparisons;
  - results, ablation, and failure analysis;
  - limitations relevant to the claims.
- Delete or move anything whose only purpose is "we organized/generated/built a tool."

Decision rule:

> If a sentence would not help a reader judge the method, evidence, or limitation, it should not be in the paper body.

### 12. Results must interpret figures, not list numbers

Current risk:

- Several Results paragraphs read as metric dumps.
- Figures are inserted, but the text does not guide the reader through what the figure shows, why it matters, or how it changes the paper's argument.
- The reader sees many numbers and method names but not a coherent finding.

Problem example:

> Detail metrics provide an independent check on this interpretation (Figure 6). Proposed's gradient-magnitude ratio is close to the baselines; its edge-preservation index is lower; FFT orthogonality is lower than Frame-wise; this is not demoireing.

Why this fails:

- It mixes three different diagnostics without a single paragraph-level claim.
- It does not say what panel or visual evidence the reader should look at.
- It reports medians before explaining the visual phenomenon.
- It introduces frequency diagnostics even though they are not central to the main argument.
- It ends by negating a claim rather than advancing the result.

Revision direction:

- Each Results paragraph should start with the point the figure supports.
- Then describe the visual pattern in the figure.
- Then give only the necessary numbers.
- Then state the implication for the method or failure mode.
- If a metric does not change the argument, move it to a table, appendix, or omit it from the main text.

Preferred paragraph pattern:

1. Claim: what the reader should learn.
2. Figure readout: where that pattern appears in the figure.
3. Evidence: one or two numbers, only if needed.
4. Interpretation: what this means for the method.

Possible rewrite direction for the Figure 6 paragraph:

> Figure 6 shows that smoother trajectories do not necessarily preserve screen content better after warping. In examples where the estimated quadrilateral is stale or shifted, local edges become less aligned even though the trajectory curve is smooth. This pattern appears in the edge-preservation scores: the reference-anchored method is lower than the two simpler alternatives, while the gradient-magnitude ratio remains similar. The failure is therefore not primarily a loss of raw texture contrast; it is a geometry-alignment problem caused by stale holds, incorrect warps, or repeated resampling. Frequency-direction measurements are kept as a diagnostic of rectification regularity, but they should not be used as evidence of demoireing.

Use this structure across Results:

- Do not write "Metric A is x, Metric B is y, Metric C is z" unless the paragraph first says why those metrics belong together.
- Do not mention every plotted value in the text.
- Do not explain a figure by repeating its axis labels.
- Do not include a figure unless the text extracts a concrete claim from it.

### 13. Every figure needs a reason to exist

Current risk:

- Some figures may be included because they were generated, not because they sharpen the argument.
- This weakens continuity and makes the paper feel like a project artifact collection.

Revision direction:

- Before keeping any figure, answer:
  1. What single claim does this figure support?
  2. Which panel is the reader supposed to inspect first?
  3. What would be lost if this figure were removed?
  4. Does the text interpret the figure, or merely cite it?
- If the answer is weak, merge the figure into another figure, move it to supplementary material, or remove it.

Figure role targets:

| Figure | Required role |
| --- | --- |
| Pipeline | Explain the evaluated method, not the old proposal. |
| Dataset | Show task difficulty and annotation target, not just categories. |
| Main trade-off | Carry the central result. |
| Category stress | Explain where the main trade-off comes from. |
| Qualitative examples | Make the failure mode visible. |
| Detail/frequency | Only stay if it clarifies alignment/resampling failure beyond geometry metrics. |
| Ablation | Identify the mechanism behind the trade-off. |
| Failures | Connect representative failures to the next method improvement. |

Specific Figure 8 issue:

- A figure described as "failure modes and tuning signal" has low value if it only shows old/new gate acceptance ratios or internal timelines.
- Acceptance ratio is an internal diagnostic. It does not by itself show the reader what failed visually, how the geometry was wrong, or why the failure matters.
- The current Figure 8 should either be replaced, redesigned, moved to supplementary material, or removed.

Figure 8 should only stay if it does at least two of the following:

1. shows original input frames with the true/estimated quadrilateral overlaid;
2. shows the resulting warped screen output so the failure is visible;
3. links each failure to one mechanism, such as stale geometry, content-motion tracking, weak screen boundary, or viewpoint distortion;
4. reports one reader-facing consequence, such as large corner error, lost screen area, or visible crop/shift;
5. supports a specific future-method decision, such as needing stronger physical screen evidence.

If the only message is "tuned gates increased acceptance," do not keep it as a main-text figure. Put the tuning table in a short diagnostic note or omit it.

### 14. Reduce secondary diagnostics in the main narrative

Current risk:

- Detail and frequency metrics are secondary diagnostics, but the current writing gives them nearly the same narrative weight as geometry and temporal stability.
- This makes the paper feel unfocused and "not knowing what it is talking about."

Revision direction:

- Main narrative should revolve around geometry correctness and temporal stability.
- Detail preservation can be one supporting check if it explains a visible alignment/resampling failure.
- FFT/frequency diagnostics should be shortened, moved later, or moved to supplementary material unless they directly support a necessary claim.
- Avoid introducing diagnostics whose interpretation requires long disclaimers.

Decision rule:

> If a metric needs two sentences to explain what it does not mean, it probably should not lead a main Results paragraph.

### 15. Keep references only when they are cited and useful

Current risk:

- The reference folder contains many papers, and the manuscript reference list can become a bibliography dump.
- Extra uncited or weakly related references make the paper look less focused.

Revision direction:

- Keep only references that are actually cited in the manuscript body.
- Each cited reference must serve one clear function:
  - establish the screen/captured-video restoration context;
  - support planar homography or rectification background;
  - support LK feature tracking / RANSAC / robust model fitting;
  - support video stabilization or temporal smoothing evaluation;
  - support a comparison or limitation discussed in the text.
- Delete references that are merely stored in `doc/current/paper/references/` but not used in the argument.
- Do not cite papers just because they are in the local reference folder.

Reference-list rule:

> The final bibliography should be the set of works cited in the text, not the set of PDFs collected during the project.

Practical cleanup:

1. Scan manuscript citation markers and build the used-reference set.
2. Remove bibliography entries not cited in the body.
3. If a citation is only decorative, remove the citation and the entry.
4. If a claim needs support but has no citation, add one targeted citation rather than several broad ones.

## Suggested edit order

1. Update `paper_status.md` for the new scrolling annotation status.
2. Update `paper_outline_zh.md` and `figure_plan.md` so they no longer promise border-guided estimation.
3. Rerun or regenerate summaries if the new annotations affect geometry metrics.
4. Rewrite the abstract with plain comparison language and fewer custom metric names.
5. Replace code-style category labels in manuscript prose, tables, and captions.
6. Remove raw parameter dumps and production-count bookkeeping from the paper body.
7. Replace low-information dataset figures with evidence-bearing visual examples.
8. Rewrite Results paragraphs so each one interprets a figure and advances one claim.
9. Remove, merge, or demote figures and metrics that do not serve the central argument.
10. Trim references to body-cited, argument-serving works only.
11. Rebuild PDFs after text and figures are consistent.

## Current abstract target

The revised abstract should follow this structure:

1. captured-screen videos need geometric normalization before downstream restoration;
2. the difficulty is separating physical screen motion from changing screen content;
3. the paper evaluates a reference-anchored screen-plane normalization pipeline;
4. the evaluation uses a 50-video collected benchmark with manual corner annotations;
5. results show smoother estimated trajectories but mixed annotated geometry;
6. the implication is a stability-accuracy trade-off and the need for stronger physical screen evidence.

Do not lead the abstract with internal method labels, code category names, or a list of project limitations.
