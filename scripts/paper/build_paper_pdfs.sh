#!/bin/sh
set -eu

root=$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)
manuscript="$root/doc/current/paper/manuscript"
chrome="/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
temporary=$(mktemp -d)
trap 'rm -rf "$temporary"' EXIT

pandoc "$manuscript/paper_en.md" \
  --from markdown+tex_math_dollars \
  --resource-path="$manuscript" \
  --pdf-engine=xelatex \
  --output "$manuscript/paper_en.pdf"

pandoc "$manuscript/paper_zh.md" \
  --from markdown+tex_math_dollars \
  --resource-path="$manuscript" \
  --to html5 \
  --standalone \
  --mathml \
  --embed-resources \
  --css "$manuscript/paper.css" \
  --output "$temporary/paper_zh.html"

"$chrome" \
  --headless \
  --disable-gpu \
  --no-pdf-header-footer \
  --print-to-pdf="$manuscript/paper_zh.pdf" \
  "file://$temporary/paper_zh.html" >/dev/null 2>&1
