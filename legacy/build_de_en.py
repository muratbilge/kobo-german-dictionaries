#!/usr/bin/env python3
"""German -> English Kobo dictfile from the kaikki.org English-Wiktionary German extract.

One entry per headword (all parts of speech merged). Every inflected form from
the Wiktionary tables is added as a `&` variant so "ging", "Häuser", "schönsten"
etc. resolve to their lemma. Pure "form of" entries are dropped when their word
is already a variant of a real lemma.
"""
import html, json, re, sys
from collections import defaultdict

SRC, OUT = sys.argv[1], sys.argv[2]
MAX_SENSES, MAX_EX_LEN = 12, 160
POS_NAMES = {"noun": "noun", "verb": "verb", "adj": "adjective", "adv": "adverb",
             "name": "proper noun", "prep": "preposition", "conj": "conjunction",
             "pron": "pronoun", "intj": "interjection", "num": "numeral",
             "particle": "particle", "det": "determiner", "article": "article",
             "phrase": "phrase", "prefix": "prefix", "suffix": "suffix",
             "contraction": "contraction", "abbrev": "abbreviation"}
SKIP_FORM_TAGS = {"table-tags", "inflection-template", "class"}
GENDER = {"m": "der", "f": "die", "n": "das"}

esc = html.escape
entries = defaultdict(list)      # word -> [html block per POS]
variants = defaultdict(set)      # word -> {forms}
formof_only = {}                 # word -> html block (only used if not covered)

def is_form_of(sense):
    return "form_of" in sense or "alt_of" in sense or "form-of" in sense.get("tags", [])

def head_line(d):
    for t in d.get("head_templates", []):
        exp = t.get("expansion", "")
        if exp:
            exp = re.sub(r",? ?diminutive .*?(?=\)$)", "", exp)   # drop long diminutive lists
            exp = re.sub(r",? ?(feminine|masculine) .*?(?=\)$)", "", exp)
            return exp[:200]
    return d["word"]

def article(d):
    for t in d.get("head_templates", []):
        g = str(t.get("args", {}).get("1", ""))[:1]
        if t.get("name") == "de-noun" and g in GENDER:
            return GENDER[g]
    return ""

def forms_of(d, word):
    out = set()
    for f in d.get("forms", []):
        if SKIP_FORM_TAGS & set(f.get("tags", [])) or f.get("source") == "declension" and not f.get("form"):
            continue
        form = f.get("form", "").strip()
        if not form or form == word or form in ("-", "—") or "strong" == form:
            continue
        if " " not in form and not {"auxiliary", "diminutive", "alternative", "obsolete"} & set(f.get("tags", [])):
            out.add(form)
    return out

def sense_html(s):
    glosses = s.get("glosses") or s.get("raw_glosses")
    if not glosses:
        return None
    g = glosses[-1] if len(glosses) > 1 else glosses[0]
    tags = [t for t in s.get("raw_tags", []) + s.get("tags", [])
            if t not in ("form-of", "alt-of", "error-unknown-tag", "strong", "weak", "irregular",
                          "neuter", "masculine", "feminine", "proper-noun")
            and not t.startswith("class-")]
    out = ""
    if tags:
        out += f"<i>({esc(', '.join(dict.fromkeys(tags)))})</i> "
    out += esc(g)
    for ex in s.get("examples", []):
        txt, eng = ex.get("text", ""), ex.get("english") or ex.get("translation", "")
        if txt and len(txt) <= MAX_EX_LEN and ex.get("type") != "quotation":
            out += f'<br/><i>{esc(txt)}</i>'
            if eng:
                out += f' — {esc(eng)}'
            break
    return out

n = 0
with open(SRC, encoding="utf-8") as fh:
    for line in fh:
        d = json.loads(line)
        word = d.get("word", "").strip()
        if not word or d.get("lang_code") != "de":
            continue
        senses = d.get("senses", [])
        real = [s for s in senses if not is_form_of(s)]
        items = [h for h in (sense_html(s) for s in (real or senses)[:MAX_SENSES]) if h]
        if not items:
            continue
        pos = POS_NAMES.get(d.get("pos", ""), d.get("pos", ""))
        art = article(d)
        head = esc(head_line(d))
        if art:
            head = f"<b>{art}</b> {head}"
        block = (f'<p><i>{esc(pos)}</i> · {head}</p><ol>'
                 + "".join(f"<li>{i}</li>" for i in items) + "</ol>")
        if real:
            entries[word].append(block)
            variants[word] |= forms_of(d, word)
        else:
            formof_only.setdefault(word, "")
            formof_only[word] += block
        n += 1

covered = set().union(*variants.values()) if variants else set()
kept_formof = 0
for w, b in formof_only.items():
    if w not in covered or w in entries:
        entries[w].append(b)
        kept_formof += 1

with open(OUT, "w", encoding="utf-8") as out:
    for w in sorted(entries):
        out.write(f"@ {w}\n")
        for v in sorted(variants.get(w, ())):
            if v.lower() != w.lower() and re.fullmatch(r"[\w\'’-]+", v):
                out.write(f"& {v}\n")
        out.write("<html>" + "".join(entries[w]).replace("\r", "").replace("\n", "<br/>") + "\n")
print(f"read {n} senses-bearing records; {len(entries)} headwords; "
      f"{sum(len(v) for v in variants.values())} variants; kept {kept_formof} form-of-only", file=sys.stderr)
