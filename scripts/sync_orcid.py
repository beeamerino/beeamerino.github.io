#!/usr/bin/env python3
"""Add new publications from ORCID to a curated .bib file (stdlib only).

ORCID is the source of *which* papers exist; the .bib stays the curated
source of *how* they look. The script only APPENDS works whose DOI (or
title) is not already in the .bib — it never edits or deletes your entries,
so manual fixes (italics, accents, `featured`, `status`) are preserved.

Usage:
  python3 scripts/sync_orcid.py                                  # website bib
  python3 scripts/sync_orcid.py --bib ../../personal/literature/publications.bib
  python3 scripts/sync_orcid.py --dry-run                        # only report

DOIs listed in data/orcid_ignore.txt (one per line) are skipped, e.g. preprints
or datasets you do not want on the site.
"""
import argparse
import datetime as dt
import json
import re
import sys
import unicodedata
import urllib.request
from pathlib import Path

ORCID_ID = "0000-0002-9518-2331"
ROOT = Path(__file__).resolve().parent.parent
UA = "beeamerino.github.io publication sync (mailto:beeatriz.merino@gmail.com)"


def get(url, accept):
    req = urllib.request.Request(url, headers={"Accept": accept, "User-Agent": UA})
    with urllib.request.urlopen(req, timeout=30) as r:
        return r.read().decode("utf-8")


def norm_title(t):
    t = unicodedata.normalize("NFKD", re.sub(r"\\\w+\{|[{}]", "", t)).encode("ascii", "ignore").decode()
    return re.sub(r"[^a-z0-9]", "", t.lower())


def orcid_works(orcid):
    data = json.loads(get(f"https://pub.orcid.org/v3.0/{orcid}/works", "application/json"))
    works = []
    for g in data.get("group", []):
        s = g["work-summary"][0]
        dois = [x["external-id-value"].lower().strip() for x in
                (s.get("external-ids") or {}).get("external-id", []) if x["external-id-type"] == "doi"]
        works.append({"title": s["title"]["title"]["value"], "type": s.get("type", ""),
                      "doi": dois[0] if dois else None})
    return works


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--bib", default=str(ROOT / "data" / "publications.bib"))
    ap.add_argument("--orcid", default=ORCID_ID)
    ap.add_argument("--dry-run", action="store_true")
    a = ap.parse_args()

    bib_path = Path(a.bib)
    bib = bib_path.read_text(encoding="utf-8")
    have_dois = {d.lower() for d in re.findall(r"doi\s*=\s*[{\"]([^}\"]+)", bib, flags=re.I)}
    have_titles = {norm_title(t) for t in re.findall(r"\btitle\s*=\s*\{((?:[^{}]|\{[^{}]*\})*)\}", bib, flags=re.I)}
    ignore_file = ROOT / "data" / "orcid_ignore.txt"
    ignore = {l.strip().lower() for l in ignore_file.read_text().splitlines()
              if l.strip() and not l.startswith("#")} if ignore_file.exists() else set()

    try:
        works = orcid_works(a.orcid)
    except Exception as e:  # network problems must never break the site build
        print(f"sync_orcid: could not reach ORCID ({e}); bib left unchanged.")
        return 0

    added = []
    for w in works:
        if not w["doi"]:
            print(f"sync_orcid: skipped (no DOI on ORCID): {w['title'][:80]}")
            continue
        if w["doi"] in have_dois or w["doi"] in ignore:
            continue
        if norm_title(w["title"]) in have_titles:
            print(f"sync_orcid: title already in bib without this DOI, add `doi = {{{w['doi']}}}` by hand: {w['title'][:70]}")
            continue
        try:
            entry = get(f"https://doi.org/{w['doi']}", "application/x-bibtex; charset=utf-8").strip()
        except Exception as e:
            print(f"sync_orcid: DOI {w['doi']} not resolvable yet ({e}); will retry next run.")
            continue
        entry = re.sub(r",\s*(?=\w+\s*=)", ",\n  ", entry, count=0)  # one field per line
        added.append(f"% Added automatically from ORCID on {dt.date.today()} — check accents/italics.\n{entry}\n")
        have_dois.add(w["doi"])
        print(f"sync_orcid: NEW {w['doi']}  {w['title'][:80]}")

    if added and not a.dry_run:
        with bib_path.open("a", encoding="utf-8") as f:
            f.write("\n" + "\n".join(added))
    print(f"sync_orcid: {len(works)} works on ORCID, {len(added)} new{' (dry run)' if a.dry_run else ''}.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
