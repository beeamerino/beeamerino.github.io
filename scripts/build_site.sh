#!/bin/bash
# Build both languages into _site/ (Spanish at the root, English in _site/en/).
set -euo pipefail
cd "$(dirname "$0")/.."
python3 scripts/build_publications.py
python3 scripts/build_gallery.py
quarto render                      # Spanish  -> _site/
quarto render --profile en         # English  -> _site_en/en/
mkdir -p _site/en
cp -R _site_en/en/. _site/en/
cp -R _site_en/site_libs/. _site/site_libs/   # identical theme files; ensures nothing is missing
echo "Site ready in _site/  (open with: python3 -m http.server -d _site 8000)"
