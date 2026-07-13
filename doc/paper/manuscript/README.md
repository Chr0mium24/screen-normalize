# Bilingual Manuscript Workspace

- `paper_en.md`: English manuscript source.
- `paper_zh.md`: Chinese manuscript source.
- `paper.css`: shared print/PDF styling.

Generated PDFs are not kept in the active manuscript directory. Rebuild them from the repository root only after real figures and final numbers are in place:

```bash
scripts/paper/build_paper_pdfs.sh
```

Old PDFs, layout placeholder SVGs, and writing scaffold notes were archived under `doc/archive/paper_workspace_cleanup_2026-07-14/`.

Current manuscript state:

- The Markdown drafts still need claim cleanup for the actual evaluated scope.
- Placeholder figure references must be replaced by real figure paths before final PDF export.
- Any regenerated local placeholders are layout-only artifacts and must not be cited as results.
