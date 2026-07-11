# Bilingual Manuscript Workspace

- `paper_en.md`: polished English pre-results manuscript.
- `paper_zh.md`: claim-equivalent Chinese manuscript.
- `paper_en.pdf` and `paper_zh.pdf`: PDF exports generated from the Markdown sources.
- `comparison_and_qa.md`: comparison with the teacher paper and course report examples, plus the writing QA record.
- `00_scope.md` through `05_style_guide.md`: evidence and writing contracts used to prevent unsupported claims.

Regenerate both PDFs from the repository root:

```bash
scripts/build_paper_pdfs.sh
```

Figures and formal measurements are intentionally absent. Replace result placeholders only from one reviewed formal run.
