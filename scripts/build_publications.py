#!/usr/bin/env python3
"""Build _publications_es.md and _publications_en.md from data/publications.bib (no dependencies).

Runs automatically before every `quarto render` / `quarto preview`
(see `pre-render` in _quarto.yml). Edit the .bib, never the .md.
"""
import re
from datetime import datetime, timedelta, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
BIB = ROOT / "data" / "publications.bib"
LABELS = {
    "es": {"prep": "En preparación", "arts": "Artículos con revisión de pares", "soft": "Software",
           "status": {"in preparation": "En preparación", "submitted": "Enviado", "in review": "En revisión", "accepted": "Aceptado"},
           "code": "Código", "link": "Enlace", "featured": "Destacado", "authors": "autores", "prefix": ""},
    "en": {"prep": "In preparation", "arts": "Peer-reviewed articles", "soft": "Software",
           "status": {}, "code": "Code", "link": "Link", "featured": "Featured", "authors": "authors", "prefix": "../"},
}
L = LABELS["es"]
ME = ("Meriño", "Vergara-Meriño", "Merino")  # name variants to highlight


def parse_bib(text):
    entries, i = [], 0
    text = "\n".join(l for l in text.splitlines() if not l.lstrip().startswith("%"))
    while (m := re.compile(r"@(\w+)\s*\{\s*([^,\s]+)\s*,").search(text, i)):
        etype, key, j, depth = m.group(1).lower(), m.group(2), m.end(), 1
        k = j
        while depth and k < len(text):
            depth += {"{": 1, "}": -1}.get(text[k], 0)
            k += 1
        body, fields, p = text[j:k - 1], {}, 0
        while (fm := re.compile(r"\s*(\w+)\s*=\s*").match(body, p)):
            p = fm.end()
            if body[p] == "{":
                d, q = 1, p + 1
                while d:
                    d += {"{": 1, "}": -1}.get(body[q], 0)
                    q += 1
                val, p = body[p + 1:q - 1], q
            else:
                q = body.find(",", p)
                q = len(body) if q == -1 else q
                val, p = body[p:q].strip().strip('"'), q
            fields[fm.group(1).lower()] = " ".join(val.split())
            p = body.find(",", p) + 1 if "," in body[p:] else len(body)
        entries.append({"type": etype, "key": key, **fields})
        i = k
    return entries


def tex(s):
    s = re.sub(r"\\(?:emph|textit)\{([^{}]*)\}", r"*\1*", s)
    s = re.sub(r"\\textbf\{([^{}]*)\}", r"**\1**", s)
    return s.replace("{", "").replace("}", "").replace("--", "–").replace("\\&", "&")


def author(a):
    a = tex(a.strip())
    if a == "others":
        return "*et al.*"
    last, _, first = a.partition(",")
    initials = " ".join(p[0] + "." for p in re.split(r"[\s.]+", first.strip()) if p)
    name = f"{last.strip()}, {initials}".strip(", ")
    return f"**{name}**" if any(v in last for v in ME) else name


def authors(s):
    names = [author(a) for a in s.split(" and ")]
    if len(names) > 10:  # long consortium lists: first three, me, last
        me = [i for i, n in enumerate(names) if n.startswith("**")]
        keep = sorted(set([0, 1, 2, len(names) - 1] + me))
        short, prev = [], -1
        for i in keep:
            if i - prev > 1:
                short.append("…")
            short.append(names[i])
            prev = i
        return ", ".join(short[:-1]) + " & " + short[-1] + f" ({len(names)} {L['authors']})"
    if len(names) > 1 and names[-1] != "*et al.*":
        return ", ".join(names[:-1]) + " & " + names[-1]
    return " ".join(names) if names[-1] == "*et al.*" else names[0]


def names_end_dot(e):
    return e.get('author', '').strip().endswith('others')


def fmt(e):
    star = f'<span class="pub-star" title="{L["featured"]}">★</span> ' if e.get("featured") == "true" else ""
    when = "" if e.get("status") else f" ({e.get('year', 'n.d.')})."
    when = when
    out = f"{star}{authors(e.get('author', ''))}{when}{'' if when or names_end_dot(e) else '.'} {tex(e.get('title', ''))}."
    note = e.get("note_en") if L is LABELS["en"] and e.get("note_en") else e.get("note")
    venue = e.get("journal") or e.get("booktitle") or e.get("publisher") or note
    if venue:
        out += f" *{tex(venue)}*"
        if e.get("volume"):
            out += f", {e['volume']}"
            if e.get("number"):
                out += f"({e['number']})"
        if e.get("pages"):
            out += f", {tex(e['pages'])}"
        out += "."
    links = []
    if e.get("doi"):
        links.append(f'[DOI](https://doi.org/{e["doi"]}){{.pub-link}}')
    if e.get("url"):
        links.append(f'[{L["code"]}]({e["url"]}){{.pub-link}}' if e["type"] == "software" else f'[{L["link"]}]({e["url"]}){{.pub-link}}')
    if e.get("pdf"):
        links.append(f'[PDF]({L["prefix"]}{e["pdf"]}){{.pub-link}}')
    if links:
        out += " " + " ".join(links)
    return out


def embargoed(e):
    """Hide entries whose `embargo = {YYYY-MM-DD}` date has not arrived (Chile time)."""
    if not e.get("embargo"):
        return False
    today = (datetime.now(timezone.utc) - timedelta(hours=3)).date().isoformat()
    return e["embargo"] > today


def build(entries, lang):
    global L
    L = LABELS[lang]
    pending = [e for e in entries if e.get("status")]
    software = [e for e in entries if e["type"] == "software" and not e.get("status")]
    papers = sorted((e for e in entries if e not in pending and e not in software),
                    key=lambda e: (-int(e.get("year", 0)), e["key"]))
    md = ["<!-- AUTO-GENERATED by scripts/build_publications.py from data/publications.bib. Do not edit. -->", ""]
    if pending:
        md += [f"## {L['prep']}", ""]
        for e in pending:
            st = L["status"].get(e["status"].lower(), e["status"].capitalize())
            md += [f"::: {{.pub}}\n{fmt(e)} [{st}]{{.pub-status}}\n:::\n"]
    md += [f"## {L['arts']} [{len(papers)}]{{.pub-count}}", ""]
    year = None
    for e in papers:
        if e.get("year") != year:
            year = e.get("year")
            md += [f"### {year} {{#y{year} .pub-year}}", ""]
        md += [f"::: {{.pub}}\n{fmt(e)}\n:::\n"]
    if software:
        md += [f"## {L['soft']}", ""]
        md += [f"::: {{.pub}}\n{fmt(e)}\n:::\n" for e in software]
    (ROOT / f"_publications_{lang}.md").write_text("\n".join(md), encoding="utf-8")
    return len(papers), len(pending), len(software)


def main():
    entries = [e for e in parse_bib(BIB.read_text(encoding="utf-8")) if not embargoed(e)]
    for lang in ("es", "en"):
        n = build(entries, lang)
    print(f"build_publications: {n[0]} articles, {n[1]} in preparation, {n[2]} software (es + en)")


if __name__ == "__main__":
    main()
