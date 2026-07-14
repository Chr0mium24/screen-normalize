# Bilingual Manuscript Workspace

- `paper_en.md`: English manuscript source.
- `paper_zh.md`: Chinese manuscript source.
- `paper.css`: shared print/PDF styling.

Generated HTML/PDF exports can be rebuilt from the repository root after the manuscript source changes:

```bash
uv run python scripts/paper/export_manuscript.py
```

Old PDFs, layout SVGs, and writing scaffold notes were archived under `doc/archive/paper_workspace_cleanup_2026-07-14/`. The 2026-07-14 manuscript restructure note is archived under `doc/archive/paper_results/2026-07-14-first-pass/`.

Current manuscript state:

- The Markdown drafts use `runs/20260714_small_sample_with_proposal_border`, with `proposal_border` reported as the manuscript Proposed method.
- Manuscript figures are generated under `doc/current/paper/manuscript/figures`.
- The text reports geometric screen-plane normalization only, with physical-border evidence as the main method cue and LK/RANSAC as a consistency diagnostic.
