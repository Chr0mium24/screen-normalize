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

- The Markdown drafts use the annotated two-per-category geometry/temporal rerun archived under `doc/archive/paper_results/2026-07-14-annotated-two-per-category/`.
- Manuscript figures are generated under `doc/current/paper/manuscript/figures`.
- The text keeps temporal-stability claims tied to trajectory-derived diagnostics, separates smoothness from annotated geometry, and does not claim demoireing quality.
