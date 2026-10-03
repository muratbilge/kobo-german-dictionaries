#!/usr/bin/env python3
"""German -> Turkish Kobo dictfile from the kaikki.org German-Wiktionary (de.wiktionary) extract.

Uses the "Übersetzungen" tables: each German sense (short German gloss) is listed
with its Turkish translations. Inflected forms become `&` variants.
"""
import html, json, re, sys
from collections import defaultdict

SRC, OUT = sys.argv[1], sys.argv[2]
esc = html.escape
POS_DE = {"noun": "Substantiv", "verb": "Verb", "adj": "Adjektiv", "adv": "Adverb",
          "name": "Eigenname", "prep": "Präposition", "conj": "Konjunktion",
          "pron": "Pronomen", "intj": "Interjektion", "num": "Numerale",
          "particle": "Partikel", "phrase": "Redewendung", "article": "Artikel"}
SKIP_FORM_TAGS = {"auxiliary", "table-tags", "inflection-template"}

entries = defaultdict(list)
variants = defaultdict(set)
stats = defaultdict(int)

def forms_of(d, word):
    out = set()
    for f in d.get("forms", []):
        form = f.get("form", "").strip()
        tags = set(f.get("tags", []))
        if not form or form == word or SKIP_FORM_TAGS & tags or form.endswith(("!", ".")):
            continue
        toks = form.split()
        if len(toks) == 1:
            out.add(form)
        elif len(toks) == 2 and toks[0] in ("ich", "du", "er", "sie", "es", "wir", "ihr"):
            out.add(toks[1])     # "du gehst" -> "gehst"
    return out

def article(d):
    for f in d.get("forms", []):
        if f.get("article") and "nominative" in f.get("tags", []) and "singular" in f.get("tags", []):
            return f["article"]
    return ""

with open(SRC, encoding="utf-8") as fh:
    for line in fh:
        if '"tr"' not in line:          # cheap prefilter: no Turkish anywhere
            continue
        d = json.loads(line)
        word = d.get("word", "").strip()
        if not word or d.get("lang_code") != "de":
            continue
        tr = [t for t in d.get("translations", []) if t.get("lang_code") == "tr" and t.get("word")]
        if not tr:
            continue
        # group Turkish words by sense
        glosses = {}
        for s in d.get("senses", []):
            if s.get("sense_index") and s.get("glosses"):
                glosses[s["sense_index"]] = s["glosses"][-1]
        groups = {}
        for t in tr:
            key = t.get("sense_index") or ""
            label = glosses.get(key) or t.get("sense") or ""
            g = groups.setdefault(key, [label, []])
            if t["word"] not in g[1]:
                g[1].append(t["word"])
        def sortkey(k):
            try:
                return [int(x) for x in k.replace("a", ".1").split(".") if x]
            except ValueError:
                return [999]
        items = []
        for k in sorted(groups, key=sortkey):
            label, words = groups[k]
            tw = "<b>" + esc(", ".join(words)) + "</b>"
            items.append(f'<li>{tw}<br/><i>{esc(label)}</i></li>' if label else f"<li>{tw}</li>")
        pos = POS_DE.get(d.get("pos", ""), d.get("pos", ""))
        art = article(d) if d.get("pos") == "noun" else ""
        head = f"<i>{esc(pos)}</i>" + (f" · <b>{esc(art)}</b> {esc(word)}" if art else "")
        entries[word].append(f"<p>{head}</p><ol>{''.join(items)}</ol>")
        variants[word] |= forms_of(d, word)
        stats["records"] += 1
        stats["translations"] += len(tr)

with open(OUT, "w", encoding="utf-8") as out:
    for w in sorted(entries):
        out.write(f"@ {w}\n")
        for v in sorted(variants[w]):
            if v.lower() != w.lower() and re.fullmatch(r"[\w\'’-]+", v):
                out.write(f"& {v}\n")
        out.write("<html>" + "".join(entries[w]).replace("\r", "").replace("\n", "<br/>") + "\n")
print(f"{stats['records']} records, {len(entries)} headwords, {stats['translations']} TR translations, "
      f"{sum(len(v) for v in variants.values())} variants", file=sys.stderr)
