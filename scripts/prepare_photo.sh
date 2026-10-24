#!/bin/bash
# Prepare a profile photo for the website (macOS, uses the built-in `sips`).
# Usage (from the repo root):   bash scripts/prepare_photo.sh ~/Desktop/my_photo.jpg
# Result: assets/img/profile.jpg — longest side 1000 px, JPEG quality 82 (~150–300 KB).
# The site crops it to a circle with CSS, so no manual cropping is needed;
# just make sure your face is in the upper-middle part of the photo.
set -euo pipefail
in="${1:?Give the path to your photo}"
out="assets/img/profile.jpg"
mkdir -p assets/img
sips -s format jpeg -s formatOptions 82 -Z 1000 "$in" --out "$out" >/dev/null
echo "Saved $out ($(du -h "$out" | cut -f1)), $(sips -g pixelWidth -g pixelHeight "$out" | awk '/pixel/{printf "%s ", $2}')px"
