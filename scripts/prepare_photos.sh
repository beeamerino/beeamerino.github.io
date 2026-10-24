#!/bin/bash
# ---------------------------------------------------------------------------
# Standardize photos for the website gallery.
#   - converts any format (HEIC, DNG and other RAW, PNG, TIFF, JPG...) to JPEG
#   - applies the camera rotation, converts to sRGB, longest side 2000 px, quality 82
#   - REMOVES ALL METADATA (GPS location, camera, serial number...), keeping only
#     the color profile; then checks that no GPS data is left
#   - adds one row per new photo to data/gallery.csv (date taken is kept there).
#     The original file name is NOT stored: it may contain a locality. Rename the
#     output file if its name reveals where a threatened species grows.
#
# Usage (from projects/portfolio-web):
#   bash scripts/prepare_photos.sh                 # reads fotos_originales/
#   bash scripts/prepare_photos.sh ~/Pictures/x    # or any folder
#   bash scripts/prepare_photos.sh --force         # re-process everything
#
# Requirements on macOS: `sips` (built in) and exiftool  ->  brew install exiftool
# Originals are never modified. Output goes to fotos_procesadas/ (not published).
# ---------------------------------------------------------------------------
set -euo pipefail
cd "$(dirname "$0")/.."

FORCE=0; IN="fotos_originales"
for a in "$@"; do
  case "$a" in --force) FORCE=1 ;; *) IN="$a" ;; esac
done
OUT="fotos_procesadas"; CSV="data/gallery.csv"
MAX=2000; QUALITY=82
SRGB="/System/Library/ColorSync/Profiles/sRGB Profile.icc"

[ -d "$IN" ] || { echo "No existe la carpeta de entrada: $IN"; exit 1; }
mkdir -p "$OUT" data

HAS_SIPS=0; command -v sips >/dev/null && HAS_SIPS=1
HAS_EXIF=0; command -v exiftool >/dev/null && HAS_EXIF=1
IM=""; command -v magick >/dev/null && IM="magick"; [ -z "$IM" ] && command -v convert >/dev/null && IM="convert"
if [ $HAS_SIPS -eq 1 ] && [ $HAS_EXIF -eq 0 ]; then
  echo "Falta exiftool (necesario para borrar la ubicación). Instálalo con:  brew install exiftool"; exit 1
fi
if [ $HAS_SIPS -eq 0 ] && [ -z "$IM" ]; then
  echo "No encontré sips (macOS) ni ImageMagick."; exit 1
fi

[ -f "$CSV" ] || echo "file,date,caption,alt,location,comment,publish,source_id" > "$CSV"

slug() {  # "IMG 1234 (2).HEIC" -> "img-1234-2"
  echo "$1" | iconv -f utf-8 -t ascii//TRANSLIT 2>/dev/null | tr '[:upper:]' '[:lower:]' \
    | sed -E 's/\.[a-z0-9]+$//; s/[^a-z0-9]+/-/g; s/^-+|-+$//g'
}

n_new=0; n_skip=0; n_err=0
shopt -s nullglob nocaseglob
for f in "$IN"/*.{jpg,jpeg,heic,heif,dng,cr2,cr3,nef,arw,raf,orf,rw2,png,tif,tiff,webp}; do
  base="$(basename "$f")"; s="$(slug "$base")"; out="$OUT/$s.jpg"
  # source_id = fingerprint of the original (no name, no location): lets you rename outputs freely
  sid="$(shasum -a 1 "$f" 2>/dev/null || sha1sum "$f")"; sid="${sid:0:12}"
  if [ $FORCE -eq 0 ] && { [ -f "$out" ] || grep -q ",$sid" "$CSV"; }; then n_skip=$((n_skip+1)); continue; fi

  # date taken (kept in the CSV, never in the image)
  date=""
  if [ $HAS_EXIF -eq 1 ]; then
    date="$(exiftool -s3 -d '%Y-%m-%d' -DateTimeOriginal -CreateDate "$f" 2>/dev/null | head -1 || true)"
  elif [ -n "$IM" ]; then
    d="$(identify -format '%[EXIF:DateTimeOriginal]' "$f[0]" 2>/dev/null | head -c 10 || true)"
    date="${d//:/-}"
  fi

  if [ $HAS_SIPS -eq 1 ]; then
    tmp="$OUT/.tmp_$s.jpg"
    args=(-s format jpeg -s formatOptions $QUALITY -Z $MAX)
    [ -f "$SRGB" ] && args+=(--matchTo "$SRGB")
    if ! sips "${args[@]}" "$f" --out "$tmp" >/dev/null 2>&1; then
      echo "  ✗ no pude convertir: $base"; n_err=$((n_err+1)); rm -f "$tmp"; continue
    fi
    # bake the camera rotation into the pixels (stripping tags would otherwise lose it)
    o="$(exiftool -s3 -n -Orientation "$tmp" 2>/dev/null || echo 1)"
    case "$o" in 3) sips -r 180 "$tmp" >/dev/null ;; 6) sips -r 90 "$tmp" >/dev/null ;; 8) sips -r 270 "$tmp" >/dev/null ;; esac
    # remove EVERYTHING except the color profile
    exiftool -q -all= -tagsFromFile @ -ICC_Profile -overwrite_original "$tmp" >/dev/null
    mv "$tmp" "$out"
  else
    if ! $IM "$f" -auto-orient -resize "${MAX}x${MAX}>" -colorspace sRGB -quality $QUALITY -strip "$out" 2>/dev/null; then
      echo "  ✗ no pude convertir: $base"; n_err=$((n_err+1)); continue
    fi
  fi

  # safety check: no location data may remain
  if [ $HAS_EXIF -eq 1 ] && [ -n "$(exiftool -s3 -gps:all "$out" 2>/dev/null)" ]; then
    echo "  ✗ quedaron datos GPS en $out — lo borro por seguridad"; rm -f "$out"; n_err=$((n_err+1)); continue
  fi

  # add a CSV row if this photo is not listed yet
  python3 - "$CSV" "$out" "$date" "$sid" <<'PY'
import csv, sys
path, out, date, sid = sys.argv[1:5]
rows = list(csv.reader(open(path, encoding="utf-8")))
if not any(r and r[0] == out for r in rows[1:]):
    with open(path, "a", newline="", encoding="utf-8") as fh:
        csv.writer(fh, lineterminator="\n").writerow([out, date, "", "", "", "", "no", sid])
PY
  echo "  ✓ $base  →  $out"
  n_new=$((n_new+1))
done

echo
echo "Listo: $n_new nuevas, $n_skip ya estaban, $n_err con error. Revisa $OUT/ y $CSV"
echo "En el CSV: escribe la ubicación aproximada (solo región, nunca la localidad exacta"
echo "de especies amenazadas), tu comentario, y cambia publish a 'si' en las que quieras mostrar."
