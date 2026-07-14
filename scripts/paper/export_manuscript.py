"""Export manuscript Markdown files to HTML and PDF.

The project environment on Windows may not have Pandoc in PATH. This script
keeps the export path reproducible with only Python's standard library and a
local Chromium-family browser for PDF printing.
"""

from __future__ import annotations

import html
import os
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
MANUSCRIPT_DIR = ROOT / "doc" / "current" / "paper" / "manuscript"
SOURCES = ("paper_zh.md", "paper_en.md")


def parse_front_matter(text: str) -> tuple[dict[str, object], str]:
    if not text.startswith("---\n"):
        return {}, text
    end = text.find("\n---\n", 4)
    if end == -1:
        return {}, text
    raw = text[4:end].splitlines()
    body = text[end + 5 :]
    meta: dict[str, object] = {}
    i = 0
    while i < len(raw):
        line = raw[i]
        if not line.strip():
            i += 1
            continue
        if ":" not in line:
            i += 1
            continue
        key, value = line.split(":", 1)
        key = key.strip()
        value = value.strip().strip('"')
        if value:
            meta[key] = value
            i += 1
            continue
        items: list[str] = []
        i += 1
        while i < len(raw) and raw[i].startswith("  - "):
            items.append(raw[i][4:].strip().strip('"'))
            i += 1
        meta[key] = items
    return meta, body


def inline_markup(text: str) -> str:
    escaped = html.escape(text)
    code_chunks: list[str] = []

    def stash_code(match: re.Match[str]) -> str:
        code_chunks.append(f"<code>{match.group(1)}</code>")
        return f"\u0000{len(code_chunks) - 1}\u0000"

    escaped = re.sub(r"`([^`]+)`", stash_code, escaped)
    escaped = re.sub(r"\*\*([^*]+)\*\*", r"<strong>\1</strong>", escaped)
    escaped = re.sub(r"(?<!\*)\*([^*\n]+)\*(?!\*)", r"<em>\1</em>", escaped)
    for index, chunk in enumerate(code_chunks):
        escaped = escaped.replace(f"\u0000{index}\u0000", chunk)
    return escaped


def is_table_start(lines: list[str], index: int) -> bool:
    if index + 1 >= len(lines):
        return False
    return lines[index].lstrip().startswith("|") and re.match(
        r"^\s*\|?\s*:?-{3,}:?\s*(\|\s*:?-{3,}:?\s*)+\|?\s*$",
        lines[index + 1],
    ) is not None


def split_table_row(line: str) -> list[str]:
    line = line.strip()
    if line.startswith("|"):
        line = line[1:]
    if line.endswith("|"):
        line = line[:-1]
    return [cell.strip() for cell in line.split("|")]


def render_table(lines: list[str]) -> str:
    headers = split_table_row(lines[0])
    rows = [split_table_row(line) for line in lines[2:]]
    out = ["<table>", "<thead><tr>"]
    out.extend(f"<th>{inline_markup(cell)}</th>" for cell in headers)
    out.append("</tr></thead>")
    out.append("<tbody>")
    for row in rows:
        out.append("<tr>")
        out.extend(f"<td>{inline_markup(cell)}</td>" for cell in row)
        out.append("</tr>")
    out.append("</tbody></table>")
    return "\n".join(out)


def render_markdown(body: str) -> str:
    lines = body.splitlines()
    blocks: list[str] = []
    i = 0
    while i < len(lines):
        line = lines[i]
        stripped = line.strip()
        if not stripped:
            i += 1
            continue
        if stripped.startswith("!["):
            match = re.match(r"!\[(.*)\]\((.*)\)", stripped)
            if match:
                caption, src = match.groups()
                blocks.append(
                    "<figure>"
                    f'<img src="{html.escape(src)}" alt="{html.escape(caption)}">'
                    f"<figcaption>{inline_markup(caption)}</figcaption>"
                    "</figure>"
                )
                i += 1
                continue
        if is_table_start(lines, i):
            table_lines = [lines[i], lines[i + 1]]
            i += 2
            while i < len(lines) and lines[i].lstrip().startswith("|"):
                table_lines.append(lines[i])
                i += 1
            blocks.append(render_table(table_lines))
            continue
        heading = re.match(r"^(#{1,6})\s+(.*)$", stripped)
        if heading:
            level = len(heading.group(1))
            blocks.append(f"<h{level}>{inline_markup(heading.group(2))}</h{level}>")
            i += 1
            continue
        if re.match(r"^\d+\.\s+", stripped):
            items: list[str] = []
            while i < len(lines) and re.match(r"^\d+\.\s+", lines[i].strip()):
                item = re.sub(r"^\d+\.\s+", "", lines[i].strip())
                items.append(f"<li>{inline_markup(item)}</li>")
                i += 1
            blocks.append("<ol>\n" + "\n".join(items) + "\n</ol>")
            continue
        if stripped.startswith("- "):
            items = []
            while i < len(lines) and lines[i].strip().startswith("- "):
                items.append(f"<li>{inline_markup(lines[i].strip()[2:])}</li>")
                i += 1
            blocks.append("<ul>\n" + "\n".join(items) + "\n</ul>")
            continue

        paragraph = [stripped]
        i += 1
        while i < len(lines):
            nxt = lines[i].strip()
            if (
                not nxt
                or nxt.startswith("#")
                or nxt.startswith("![")
                or nxt.startswith("|")
                or re.match(r"^\d+\.\s+", nxt)
                or nxt.startswith("- ")
            ):
                break
            paragraph.append(nxt)
            i += 1
        blocks.append(f"<p>{inline_markup(' '.join(paragraph))}</p>")
    return "\n".join(blocks)


def make_html(meta: dict[str, object], body_html: str, css: str) -> str:
    title = str(meta.get("title", "Manuscript"))
    authors = meta.get("author", [])
    if isinstance(authors, str):
        authors = [authors]
    date = str(meta.get("date", ""))
    lang = str(meta.get("lang", "en"))
    author_html = "\n".join(f'<div class="author">{html.escape(a)}</div>' for a in authors)
    return f"""<!doctype html>
<html lang="{html.escape(lang)}">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{html.escape(title)}</title>
  <style>
{css}
figure {{
  break-inside: avoid;
  margin: 4mm auto 5mm;
}}
figure img {{
  display: block;
  max-height: 185mm;
  max-width: 100%;
  object-fit: contain;
  width: auto;
  margin: 0 auto;
}}
figcaption {{
  color: #333;
  font-size: 8.5pt;
  margin-top: 1.5mm;
  text-align: left;
}}
.paper-title {{
  font-family: "Heiti SC", "Microsoft YaHei", sans-serif;
  font-size: 19pt;
  line-height: 1.25;
  margin: 0 0 7mm;
  text-align: center;
}}
  </style>
</head>
<body>
  <h1 class="paper-title">{html.escape(title)}</h1>
  {author_html}
  <div class="date">{html.escape(date)}</div>
  {body_html}
</body>
</html>
"""


def find_browser() -> Path | None:
    env_browser = os.environ.get("BROWSER")
    candidates = [
        env_browser,
        shutil.which("msedge"),
        shutil.which("chrome"),
        shutil.which("chromium"),
        r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
        r"C:\Program Files\Microsoft\Edge\Application\msedge.exe",
        r"C:\Program Files\Google\Chrome\Application\chrome.exe",
        r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
    ]
    for candidate in candidates:
        if candidate and Path(candidate).exists():
            return Path(candidate)
    return None


def print_pdf(browser: Path, html_path: Path, pdf_path: Path) -> None:
    with tempfile.TemporaryDirectory(prefix="paper-browser-") as user_data_dir:
        command = [
            str(browser),
            "--headless=new",
            "--disable-gpu",
            "--allow-file-access-from-files",
            f"--user-data-dir={user_data_dir}",
            "--no-pdf-header-footer",
            f"--print-to-pdf={pdf_path}",
            html_path.resolve().as_uri(),
        ]
        result = subprocess.run(command, cwd=MANUSCRIPT_DIR, text=True, capture_output=True)
    if result.returncode != 0:
        raise RuntimeError(result.stderr.strip() or result.stdout.strip())
    if not pdf_path.exists() or pdf_path.stat().st_size == 0:
        raise RuntimeError(f"PDF was not created: {pdf_path}")


def main() -> int:
    css = (MANUSCRIPT_DIR / "paper.css").read_text(encoding="utf-8")
    browser = find_browser()
    if browser is None:
        print("No Chrome or Edge executable found; HTML files will still be written.", file=sys.stderr)

    for source_name in SOURCES:
        source = MANUSCRIPT_DIR / source_name
        meta, body = parse_front_matter(source.read_text(encoding="utf-8"))
        html_path = source.with_suffix(".html")
        pdf_path = source.with_suffix(".pdf")
        html_path.write_text(make_html(meta, render_markdown(body), css), encoding="utf-8")
        print(f"Wrote {html_path.relative_to(ROOT)}")
        if browser is not None:
            print_pdf(browser, html_path, pdf_path)
            print(f"Wrote {pdf_path.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
