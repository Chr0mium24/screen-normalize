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

## Suggested edit order

1. Update `paper_status.md` for the new scrolling annotation status.
2. Update `paper_outline_zh.md` and `figure_plan.md` so they no longer promise border-guided estimation.
3. Rerun or regenerate summaries if the new annotations affect geometry metrics.
4. Rewrite the abstract with plain comparison language and fewer custom metric names.
5. Replace code-style category labels in manuscript prose, tables, and captions.
6. Rebuild PDFs after text and figures are consistent.

## Current abstract target

The revised abstract should follow this structure:

1. captured-screen videos need geometric normalization before downstream restoration;
2. the difficulty is separating physical screen motion from changing screen content;
3. the paper evaluates a reference-anchored screen-plane normalization pipeline;
4. the evaluation uses a 50-video collected benchmark with manual corner annotations;
5. results show smoother estimated trajectories but mixed annotated geometry;
6. the implication is a stability-accuracy trade-off and the need for stronger physical screen evidence.

Do not lead the abstract with internal method labels, code category names, or a list of project limitations.
