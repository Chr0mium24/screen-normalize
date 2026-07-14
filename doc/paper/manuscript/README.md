# Bilingual Manuscript Workspace

- `paper_en.md`: English manuscript source.
- `paper_zh.md`: Chinese manuscript source.
- `paper.css`: shared print/PDF styling.

Generated PDFs can be rebuilt from the repository root after the manuscript source changes:

```bash
scripts/paper/build_paper_pdfs.sh
```

Old PDFs, layout SVGs, and writing scaffold notes were archived under `doc/archive/paper_workspace_cleanup_2026-07-14/`.

Current manuscript state:

- The Markdown drafts contain the first-pass results from `runs/20260714_full_pipeline_first_pass`.
- Manuscript figures are generated from reviewed experiment artifacts under `doc/paper/manuscript/figures`.
- The text keeps temporal-stability claims tied to trajectory-derived diagnostics and does not claim demoireing quality.
