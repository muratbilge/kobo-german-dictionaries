#!/usr/bin/env python3
"""German -> English and German -> Turkish(+English) Kobo dictfiles.

Sources (kaikki.org wiktextract dumps in data/):
  en-German.jsonl   English Wiktionary, German entries   -> main English definitions + forms
  de-Deutsch.jsonl  German Wiktionary, German entries    -> extra lemmas (compounds), EN/TR translation
                                                            tables, German glosses, inflection forms
  tr-extract.jsonl  Turkish Wiktionary                   -> German entries with Turkish definitions
  en-English.jsonl  English Wiktionary, English entries  -> translation groups containing both a German
                                                            and a Turkish word = German->Turkish pairs
Output: de-en.df (English, German gloss fallback) and de-tr.df (Turkish first, English below).
"""
import html, json, re, sys
from collections import defaultdict

D = "data/"
esc = html.escape
MAX_SENSES, MAX_EX_LEN = 12, 160
POS_EN = {"noun": "noun", "verb": "verb", "adj": "adjective", "adv": "adverb", "name": "proper noun",
          "prep": "preposition", "conj": "conjunction", "pron": "pronoun", "intj": "interjection",
          "num": "numeral", "particle": "particle", "det": "determiner", "article": "article",
          "phrase": "phrase", "prefix": "prefix", "suffix": "suffix", "contraction": "contraction",
          "abbrev": "abbreviation"}
GENDER = {"m": "der", "f": "die", "n": "das"}
DROP_TAGS = {"form-of", "alt-of", "error-unknown-tag", "strong", "weak", "irregular",
             "neuter", "masculine", "feminine", "proper-noun"}
BAD_FORM_TAGS = {"auxiliary", "diminutive", "alternative", "obsolete", "table-tags",
                 "inflection-template", "class"}
PRONOUNS = {"ich", "du", "er", "sie", "es", "wir", "ihr", "man"}
VALID = re.compile(r"[\w'’-]+")
ADJ_END = ("e", "em", "en", "er", "es")

def log(*a):
    print(*a, file=sys.stderr, flush=True)

def is_form_of(s):
    return "form_of" in s or "alt_of" in s or "form-of" in s.get("tags", [])

def rows(path):
    with open(path, encoding="utf-8") as fh:
        for line in fh:
            yield json.loads(line)

# ---------------------------------------------------------------- lemma store
en_blocks = defaultdict(list)    # lemma -> English-Wiktionary HTML blocks
de_info = {}                     # lemma -> (pos, article, [(gloss, [en], [tr])])  from de.wiktionary
tr_wikt = defaultdict(list)      # lemma -> Turkish definitions from tr.wiktionary
tr_pivot = defaultdict(dict)     # lemma -> {turkish word: english word}
forms = defaultdict(set)         # lemma -> inflected forms
form_of = defaultdict(set)       # form -> lemmas (from explicit form-of entries)
adj_like = set()                 # lemmas/forms that take adjective endings

def add_forms(lemma, d, strip_pronoun=False):
    for f in d.get("forms", []):
        form = f.get("form", "").strip()
        tags = set(f.get("tags", []))
        if not form or form == lemma or BAD_FORM_TAGS & tags or form.endswith(("!", ".")):
            continue
        toks = form.split()
        if strip_pronoun and len(toks) == 2 and toks[0] in PRONOUNS:
            toks = toks[1:]
        if len(toks) == 1:
            forms[lemma].add(toks[0])
            if "participle" in tags:
                adj_like.add(toks[0])

# ---- 1. English Wiktionary (German entries)
def head_line(d):
    for t in d.get("head_templates", []):
        exp = t.get("expansion", "")
        if exp:
            exp = re.sub(r",? ?diminutive .*?(?=\)$)", "", exp)
            exp = re.sub(r",? ?(feminine|masculine) .*?(?=\)$)", "", exp)
            return exp[:200]
    return d["word"]

def en_article(d):
    for t in d.get("head_templates", []):
        g = str(t.get("args", {}).get("1", ""))[:1]
        if t.get("name") == "de-noun" and g in GENDER:
            return GENDER[g]
    return ""

def sense_html(s):
    glosses = s.get("glosses") or s.get("raw_glosses")
    if not glosses:
        return None
    g = glosses[-1]
    tags = [t for t in s.get("raw_tags", []) + s.get("tags", [])
            if t not in DROP_TAGS and not t.startswith("class-")]
    out = f"<i>({esc(', '.join(dict.fromkeys(tags)))})</i> " if tags else ""
    out += esc(g)
    for ex in s.get("examples", []):
        txt, eng = ex.get("text", ""), ex.get("english") or ex.get("translation", "")
        if txt and len(txt) <= MAX_EX_LEN and ex.get("type") != "quotation":
            out += f"<br/><i>{esc(txt)}</i>" + (f" — {esc(eng)}" if eng else "")
            break
    return out

log("1/4 English Wiktionary German entries")
en_formof_blocks = {}
for d in rows(D + "en-German.jsonl"):
    w = d.get("word", "").strip()
    if not w or d.get("lang_code") != "de":
        continue
    senses = d.get("senses", [])
    real = [s for s in senses if not is_form_of(s)]
    items = [h for h in (sense_html(s) for s in (real or senses)[:MAX_SENSES]) if h]
    if not items:
        continue
    pos = POS_EN.get(d.get("pos", ""), d.get("pos", ""))
    art = en_article(d)
    head = (f"<b>{art}</b> " if art else "") + esc(head_line(d))
    block = f"<p><i>{esc(pos)}</i> · {head}</p><ol>" + "".join(f"<li>{i}</li>" for i in items) + "</ol>"
    if real:
        en_blocks[w].append(block)
        add_forms(w, d)
        if d.get("pos") == "adj":
            adj_like.add(w)
    else:
        en_formof_blocks[w] = en_formof_blocks.get(w, "") + block
        for s in senses:
            for fo in s.get("form_of", []):
                if fo.get("word"):
                    form_of[w].add(fo["word"])
log(f"   {len(en_blocks)} lemmas")

# ---- 2. German Wiktionary
log("2/4 German Wiktionary")
POS_DE = {"noun": "Substantiv", "verb": "Verb", "adj": "Adjektiv", "adv": "Adverb", "name": "Eigenname",
          "prep": "Präposition", "conj": "Konjunktion", "pron": "Pronomen", "intj": "Interjektion",
          "num": "Numerale", "particle": "Partikel", "phrase": "Redewendung", "article": "Artikel",
          "abbrev": "Abkürzung"}

def sense_key(k):
    try:
        return [int(x) for x in re.sub(r"[a-z]", "", k).split(".") if x]
    except ValueError:
        return [999]

for d in rows(D + "de-Deutsch.jsonl"):
    w = d.get("word", "").strip()
    if not w or d.get("lang_code") != "de":
        continue
    senses = [s for s in d.get("senses", []) if s.get("glosses")]
    if not senses:
        continue
    fo = [s for s in senses if is_form_of(s)]
    if fo:
        for s in fo:
            for t in s.get("form_of", []):
                if t.get("word"):
                    form_of[w].add(t["word"])
                    if d.get("pos") in ("adj", "verb") and "participle" in s.get("tags", []):
                        adj_like.add(w)
        continue
    add_forms(w, d, strip_pronoun=True)
    if d.get("pos") == "adj":
        adj_like.add(w)
    gl = {}
    for s in senses:
        gl[s.get("sense_index", "")] = [s["glosses"][-1], [], []]
    for t in d.get("translations", []):
        lc, tw = t.get("lang_code"), t.get("word")
        if lc not in ("en", "tr") or not tw:
            continue
        k = t.get("sense_index", "")
        g = gl.setdefault(k, [t.get("sense", ""), [], []])
        lst = g[1] if lc == "en" else g[2]
        if tw not in lst:
            lst.append(tw)
    art = ""
    if d.get("pos") == "noun":
        for f in d.get("forms", []):
            if f.get("article") and {"nominative", "singular"} <= set(f.get("tags", [])):
                art = f["article"]
                break
    pos = POS_DE.get(d.get("pos", ""), d.get("pos", ""))
    entry = (pos, art, [gl[k] for k in sorted(gl, key=sense_key)])
    if w in de_info:      # several POS for one word: concatenate
        p0, a0, s0 = de_info[w]
        entry = (p0, a0 or art, s0 + [[f"({pos})", [], []]] + entry[2])
    de_info[w] = entry
log(f"   {len(de_info)} lemmas")

# ---- 3. Turkish Wiktionary
log("3/4 Turkish Wiktionary")
JUNK = ("sözcüğünün", "eyleminin", "Vikisözlük", "çekimi", "mastarı", "tanımisteniyor", "çoğulu")
for d in rows(D + "tr-extract.jsonl"):
    w = d.get("word", "").strip()
    if not w or d.get("lang_code") != "de":
        continue
    for s in d.get("senses", []):
        if is_form_of(s) or not s.get("glosses"):
            continue
        g = s["glosses"][-1].strip()
        if g and not any(j in g for j in JUNK) and g != w and g not in tr_wikt[w]:
            tr_wikt[w].append(g)
log(f"   {len(tr_wikt)} lemmas")

# ---- 4. English Wiktionary translation groups: German + Turkish in the same sense
log("4/4 English->(German,Turkish) pivot")
npairs = 0
try:
    for d in rows(D + "en-English.jsonl"):
        if d.get("lang_code") != "en":
            continue
        tr = d.get("translations", []) + [t for s in d.get("senses", []) for t in s.get("translations", [])]
        if not tr:
            continue
        groups = defaultdict(lambda: ([], []))
        for t in tr:
            lc = t.get("lang_code") or t.get("code")
            if lc in ("de", "tr") and t.get("word"):
                groups[t.get("sense", "")][0 if lc == "de" else 1].append(t["word"])
        for de_ws, tr_ws in groups.values():
            if de_ws and tr_ws:
                for dw in de_ws:
                    for tw in tr_ws[:4]:
                        tr_pivot[dw].setdefault(tw, d["word"])
                        npairs += 1
except FileNotFoundError:
    log("   en-English.jsonl missing, skipping pivot")
log(f"   {npairs} pairs, {len(tr_pivot)} German words")

# ---------------------------------------------------------------- assemble
lemmas = set(en_blocks) | set(de_info)
for w, b in en_formof_blocks.items():          # form-of-only words with nothing better
    if w not in lemmas and not (form_of[w] & lemmas):
        en_blocks[w].append(b)
        lemmas.add(w)

variants = defaultdict(set)
for lemma in lemmas:
    variants[lemma] |= forms.get(lemma, set())
for f, ls in form_of.items():
    for l in ls:
        if l in lemmas and f != l:
            variants[l].add(f)
# adjective endings for adjectives and participles: schön -> schönen, eingereicht -> eingereichten
for lemma in lemmas:
    cands = [lemma] if lemma in adj_like else []
    cands += [v for v in variants[lemma] if v in adj_like or re.fullmatch(r"(\w*ge\w+[tn]|\w+end)", v)
              and lemma[:1].islower()]
    for base in cands:
        if base[:1].isupper() or len(base) < 3:
            continue
        stem = base[:-1] if base.endswith("e") else base
        for e in ADJ_END:
            variants[lemma].add(stem + e)

def de_en_html(w):
    if en_blocks.get(w):
        return "".join(en_blocks[w])
    pos, art, senses = de_info[w]
    head = f"<i>{esc(pos)}</i>" + (f" · <b>{esc(art)}</b> {esc(w)}" if art else "")
    items, german_only = [], True
    for gloss, en, _ in senses:
        if en:
            german_only = False
            items.append(f"<li><b>{esc(', '.join(en))}</b>" + (f"<br/><i>{esc(gloss)}</i>" if gloss else "") + "</li>")
        elif gloss:
            items.append(f"<li>{esc(gloss)}</li>")
    note = " <small>(Deutsch)</small>" if german_only else ""
    return f"<p>{head}{note}</p><ol>{''.join(items[:MAX_SENSES])}</ol>"

def de_tr_html(w):
    parts = []
    info = de_info.get(w)
    direct = [(g, t) for g, _, t in (info[2] if info else []) if t]
    if direct:
        parts.append("<ol>" + "".join(
            f"<li><b>{esc(', '.join(t))}</b>" + (f"<br/><i>{esc(g)}</i>" if g else "") + "</li>"
            for g, t in direct) + "</ol>")
    if tr_wikt.get(w):
        parts.append("<ul>" + "".join(f"<li>{esc(g)}</li>" for g in tr_wikt[w][:8]) + "</ul>")
    have = {x for _, t in direct for x in t}
    piv = [(t, e) for t, e in tr_pivot.get(w, {}).items() if t not in have]
    if piv and not direct:
        parts.append("<p>≈ " + "; ".join(f"<b>{esc(t)}</b> <small>({esc(e)})</small>" for t, e in piv[:8]) + "</p>")
    tr = ""
    if parts:
        tr = "<p><b>Türkçe</b></p>" + "".join(parts) + "<hr/><p><b>English</b></p>"
    return tr + de_en_html(w), bool(parts)

def write(path, render):
    n = withtr = 0
    with open(path, "w", encoding="utf-8") as out:
        for w in sorted(lemmas):
            body = render(w)
            if isinstance(body, tuple):
                body, t = body
                withtr += t
            out.write(f"@ {w}\n")
            for v in sorted(variants[w]):
                if v.lower() != w.lower() and VALID.fullmatch(v):
                    out.write(f"& {v}\n")
            out.write("<html>" + body.replace("\r", "").replace("\n", "<br/>") + "\n")
            n += 1
    log(f"{path}: {n} entries" + (f", {withtr} with Turkish" if withtr else ""))

write("de-en.df", de_en_html)
write("de-tr.df", de_tr_html)
log(f"variants: {sum(len(v) for v in variants.values())}")
