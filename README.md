# beeamerino.github.io

Personal portfolio of **Beatriz M. Meriño**, built with [Quarto](https://quarto.org) and hosted on GitHub Pages at <https://beeamerino.github.io>.

## Languages

Spanish is the main language (files at the root); English lives in `en/` with the same file names.
The **ES · EN** button in the navbar jumps to the same page in the other language.
Edit the Spanish pages first; translate them into `en/` at the end.

## Edit and preview

```bash
quarto preview                  # Spanish, live preview; reloads on every save
quarto preview --profile en     # English
bash scripts/build_site.sh      # full bilingual build into _site/ (what GitHub publishes)
python3 -m http.server -d _site 8000   # then open http://localhost:8000 to test the ES/EN button
```

## Where things live

| What | File |
|---|---|
| Home | `index.qmd` |
| Research | `research.qmd` |
| Publications | `data/publications.bib` → auto-built into `_publications_es.md` / `_publications_en.md` by `scripts/build_publications.py` (runs on every render) |
| Software & tutorials | `software.qmd` |
| Experience | `experience.qmd` |
| Teaching, talks & outreach | `teaching-outreach.qmd` |
| CV page | `cv.qmd` + PDFs in `assets/cv/` |
| Profile photo | `assets/img/profile.jpg` (shown automatically when present; otherwise an ASCII cactus) |
| Link-preview image | `assets/img/social-card.png` |
| Colors & layout | `assets/css/custom.scss` (light) and `assets/css/dark.scss` (dark) |

## Publications: automatic from ORCID

Every day at 13:30 (Chile) GitHub Actions runs `scripts/sync_orcid.py`: it reads your public ORCID record,
and any work with a DOI that is not yet in `data/publications.bib` is downloaded as BibTeX (from doi.org),
appended to the .bib, committed and published. Existing entries are never modified, so your manual
fixes stay. To keep it working, keep ORCID complete: in ORCID enable *Crossref auto-update* so new papers
with your ORCID iD are added automatically. DOIs you don't want on the site go in `data/orcid_ignore.txt`.

Embargoed papers: add `embargo = {YYYY-MM-DD}` and the entry stays hidden until that date (but note the
.bib itself is public on GitHub, so keep embargoed titles out of the repo — see
`personal/literature/publications_forthcoming.bib`).

## Adding a publication by hand

1. Google Scholar → your profile → tick the paper → **Export → BibTeX**, copy the text.
2. Paste it into `data/publications.bib`.
3. Optional fields: `featured = {true}` (★), `status = {in preparation}` / `{submitted}`, `pdf = {assets/pdf/file.pdf}`. Write species names as `\emph{Eriosyce}`.

## Photos for the gallery

1. Put your photos (HEIC, DNG/RAW, JPG, PNG, TIFF…) in `fotos_originales/` (never published).
2. `brew install exiftool` (once), then `bash scripts/prepare_photos.sh`.
3. Standardized JPGs without any metadata (no GPS) land in `fotos_procesadas/`, and one row per
   photo is added to `data/gallery.csv` (columns: caption, alt, location, comment, publish).
4. Fill the CSV (Numbers/Excel are fine; keep it as CSV). Location: region only, never the exact
   locality of threatened species. Set `publish` to `si` for the photos to show.

## Profile photo

```bash
bash scripts/prepare_photo.sh ~/Desktop/my_photo.jpg
```

## Publish

Every push to `main` renders and deploys through `.github/workflows/publish.yml` (branch `gh-pages`).

## Before going public

- [ ] Photo in `assets/img/profile.jpg`
- [ ] `assets/cv/CV_Beatriz_Merino_EN.pdf` and `assets/cv/CV_Beatriz_Merino_ES.pdf` (career-agent)
- [ ] LinkedIn URL in the navbar and home buttons

Never add: RUT, phone number, referees' emails, unpublished results, private repositories.
