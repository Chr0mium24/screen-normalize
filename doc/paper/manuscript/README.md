# Bilingual Manuscript Workspace

- `paper_en.md`: polished English pre-results manuscript.
- `paper_zh.md`: claim-equivalent Chinese manuscript.
- `paper_en.pdf` and `paper_zh.pdf`: PDF exports generated from the Markdown sources.
- `comparison_and_qa.md`: comparison with the teacher paper and course report examples, plus the writing QA record.
- `00_scope.md` through `05_style_guide.md`: evidence and writing contracts used to prevent unsupported claims.

Regenerate both PDFs from the repository root:

```bash
scripts/paper/build_paper_pdfs.sh
```

Formal figures and measurements are intentionally absent; clearly marked layout placeholders are included. Replace result placeholders only from one reviewed formal run.

Generate the eight SVG layout placeholders with:

```bash
uv run scripts/paper/build_placeholder_figures.py
```

Placeholder charts use identical values of `1.0` and carry a red warning. They establish layout only and must never be cited as results.
