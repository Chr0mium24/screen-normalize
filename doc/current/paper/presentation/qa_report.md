# PPTX QA Report

- PPTX: `paper_zh_presentation.pptx`
- Source PDF: `doc/current/paper/manuscript/paper_zh.pdf`
- Slide count: 13
- Figures inserted: 6 manuscript figures
- Figure asset handling: copied full manuscript PNGs; no panel crop was applied, so axes/legends/panel labels remain with the original figure canvas.
- Speaker notes: generated as `speaker_notes_cn.md` because python-pptx does not provide stable native speaker-note authoring.
- Layout review: slide rhythm alternates cover, concept, workflow, evaluation table, evidence figures, ablation table, qualitative figure, synthesis.
- Text density review: on-slide text kept to short bullets, metric callouts, captions, and source labels; detailed explanation moved to speaker notes sidecar.
- Known limitation: rendered slide preview was not produced; verification uses package reopening, asset contact sheet, shape-bound checks, and the bundled PPTX XML audit.

## Self-review defects

- high: none identified in generation self-check.
- medium: native speaker notes are not embedded in PPTX; sidecar notes file generated instead.
- low: dense qualitative figure is shown as a full source figure; it is intended for trend-level visual comparison rather than reading every small label.

## Audit

The bundled XML audit is run after generation and writes `pptx_audit.md`.
Final audit summary for the generated deck: high=0, medium=0; remaining findings are low-severity near-miss alignment hints.