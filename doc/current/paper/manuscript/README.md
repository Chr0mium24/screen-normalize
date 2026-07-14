# Bilingual Manuscript Workspace

- `paper_en.md`: English manuscript source.
- `paper_zh.md`: Chinese manuscript source.
- `paper.css`: shared print/PDF styling.

Generated PDFs can be rebuilt from the repository root after the manuscript source changes:

```bash
scripts/paper/build_paper_pdfs.sh
```

Old PDFs, layout SVGs, and writing scaffold notes were archived under `doc/archive/paper_workspace_cleanup_2026-07-14/`. The 2026-07-14 manuscript restructure note is archived under `doc/archive/paper_results/2026-07-14-first-pass/`.

Current manuscript state:

- The Markdown drafts contain the first-pass results archived under `doc/archive/paper_results/2026-07-14-first-pass/`.
- Manuscript figures are generated under `doc/current/paper/manuscript/figures`.
- The text keeps temporal-stability claims tied to trajectory-derived diagnostics and does not claim demoireing quality.
