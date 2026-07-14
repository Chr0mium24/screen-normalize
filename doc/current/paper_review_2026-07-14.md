# Paper Review - 2026-07-14

## Review setup

- Input scope: current Chinese and English manuscript sources in `doc/current/paper/manuscript/`, current status notes, figure plan, and archived first-pass result summaries.
- Assessment boundary: this is a manuscript-readiness review based on local files only. It does not verify every reference externally and does not manually inspect all generated videos frame by frame.
- Shared manuscript claim summary: the paper now claims a bounded engineering result: reference-anchored screen-plane normalization gives smoother estimated trajectories, but the first-pass run exposes a stability-accuracy trade-off rather than an overall win.
- Visible evidence base: 50 clips, 14985 frames, 179 non-initialization geometry annotations, 50-clip main run, 50-clip ablation run, generated figures, and archived CSV/Markdown evidence.
- Missing materials affecting confidence: clip-by-clip manual video review, added non-initialization annotations for `scrolling_06` through `scrolling_10`, externally verified reference metadata, and a formal rerun of any tuned Proposed configuration.

## Reviewer 1

- Overall assessment: the manuscript is substantially more honest and defensible than a success-only project report, but it is not yet final-submission ready.
- Who would be interested in the results, and why: readers working on screen capture preprocessing, geometric rectification, and course-project reproducibility would care because the paper exposes a practical failure mode in reference tracking.
- Major strengths: the paper clearly separates geometry, temporal stability, detail preservation, and frequency diagnostics; it also avoids claiming demoireing performance.
- Major concerns: the implemented method differs from the original border-guided plan, while the outline and figure plan still contain older promises about physical border dominance. This creates a mismatch between intended contribution and actual evidence.
- Technical failings that need to be addressed before the case is established: the strongest result is negative/mixed, but the visual audit is not complete; several geometry records are skipped in scrolling; `no_offline_repair` is probably inconclusive; and the tuned-gate smoke test is too small to support aggregate claims.
- Assessment against Nature-style criteria: originality is modest but credible as an engineering benchmark; technical soundness is partial because evidence is first-pass and sparse; broad significance is limited; readability is good for the current project scope.
- Recommendation posture: revise before final submission.

## Reviewer 2

- Overall assessment: the current story is coherent if framed as a failure-aware benchmark, not as a completed method paper.
- Who would be interested in the results, and why: project evaluators and applied computer-vision readers would value the reproducible pipeline and explicit failure analysis.
- Major strengths: the abstract and conclusion now correctly state that Proposed loses on overall annotated geometry and edge preservation; this prevents the central overclaim.
- Major concerns: novelty is under pressure. Reference-anchored LK plus RANSAC plus smoothing is classical, and the missing physical-border evidence means the paper's distinctive method is weaker than the problem framing suggests.
- Technical failings that need to be addressed before the case is established: the manuscript needs a sharper explanation of why Frame-wise is so poor on `static` yet strong overall, and why Proposed has a very low RMSE quartile but a poor median. These distributional effects are important and currently under-explained.
- Assessment against Nature-style criteria: scientific importance is field-local; originality comes mainly from the dataset/evaluation packaging and transparent negative result, not from a new algorithm.
- Recommendation posture: acceptable for a course final report after tightening claims; weak for a formal research submission.

## Reviewer 3

- Overall assessment: the paper is readable and organized, but some presentation assets and documentation still lag behind the current manuscript story.
- Who would be interested in the results, and why: readers outside the immediate implementation can follow the trade-off, especially because the paper defines what the metrics do not prove.
- Major strengths: limitation statements are unusually clear, especially around trajectory-derived temporal metrics and non-demoireing frequency diagnostics.
- Major concerns: the figure plan and visual style notes still mention pending assets and older border-guided figures, while the manuscript already uses eight generated figures. This can confuse final package review.
- Technical failings that need to be addressed before the case is established: figure captions are mostly descriptive but do not always state data inclusion/exclusion rules; annotation protocol lacks annotator consistency or quality-control detail; Data Availability says raw videos need team review, which may be fine for coursework but weak for reproducibility.
- Assessment against Nature-style criteria: readability is good, but broad readership interest is limited unless the paper foregrounds the general lesson: smooth estimated trajectories can be stale and wrong.
- Recommendation posture: revise presentation and reproducibility details before treating the PDF as final.

## Cross-review synthesis

- Consensus strengths: the current manuscript has a clear bounded claim, real first-pass data, real ablation data, and a candid negative result.
- Consensus technical risks: incomplete manual audit, sparse/uneven annotations, skipped scrolling geometry records, inconclusive offline-repair ablation, and method-story mismatch around physical-border evidence.
- Where emphasis differs across reviewers: Reviewer 1 emphasizes evidence validity, Reviewer 2 emphasizes novelty and contribution framing, and Reviewer 3 emphasizes reader-facing packaging.
- Broad-interest / significance readout: the paper is currently strongest as a transparent engineering report. It is not yet a strong method paper because the proposed method does not win overall and the intended border-guided mechanism is not implemented.
- Most important issues to resolve before a strong case is established:
  1. Align the manuscript, outline, and figure plan around the implemented reference-anchored method, or implement the physical-border module and rerun.
  2. Manually review generated HTML/video reports and record which qualitative examples are accepted.
  3. Add or explicitly justify missing non-initialization annotations for the five skipped scrolling clips.
  4. Mark `no_offline_repair` as inconclusive unless repair-triggering intervals are audited.
  5. Keep the tuned-gate smoke test as diagnostic only, unless a formal tuned subset/full run is added.

## Risk / unsupported claims

- The current paper should not claim a complete demoireing method.
- The current paper should not claim overall superiority of Proposed.
- The current paper should not imply physical display borders dominate the actual per-frame estimate.
- The current paper should not use the smoke test as a formal replacement result.
- The current paper should not treat trajectory-derived stability as independent proof of correct physical stabilization.
