# Kobo German dictionaries (German → English, German → Turkish)

Bigger custom dictionaries for Kobo e-readers (tested on a Kobo Sage, stock reader), built from Wiktionary.

| Dictionary | Entries | Words found in real novel text* |
|---|---|---|
| `dicthtml-de-en.zip`: German → English | 219,908 | **97.6%** |
| `dicthtml-de-tr.zip`: German → Turkish, with the English entry below | 219,908 | **83%** with a Turkish meaning, 97.6% with any meaning |

\* measured with `coverage.py` on ~240k words of quotes from 2010s–2020s German novels. Almost all remaining misses are names.

**Download:** grab both zips from the [latest release](../../releases/latest).

## Features

- **Inflected forms resolve to the base word**, with about 1.08 million forms: *ging* opens **gehen**, *Häusern* opens **Haus**, *eingereichten* opens **einreichen**.
- **Compounds** from German Wiktionary, e.g. *Ledersofa*: "leather couch, leather sofa".
- Grammar line with article, genitive and plural (*das Haus, plural Häuser*), numbered senses and short example sentences with translations.
- **de-tr** lists Turkish translations per sense (with a short German gloss), then the full English entry.
  - Turkish meanings marked **≈** were matched through English: the German and Turkish words share a sense in English Wiktionary's translation tables.
- Words with no translation in any source fall back to a German definition, marked *(Deutsch)*.

## Install on a Kobo (firmware 4.24+)

1. Connect the Kobo by USB to a computer, or to an Android phone over OTG and use its Files app.
2. Turn on hidden files. Copy the zips into `KOBOeReader/.kobo/custom-dict/`, creating that folder if it doesn't exist.
3. Keep the file names exactly as they are: `dicthtml-de-en.zip`, `dicthtml-de-tr.zip`.
4. Eject. In a German book, long-press a word, then tap the dictionary name in the popup to switch to **de-en** or **de-tr**.

Known limitation: with separable verbs (*fängt … an*), the Kobo looks up only *fängt*, so it shows *fangen*.

## Build it yourself

Requirements: Python 3 and [dictgen](https://pgaskin.net/dictutil/dictgen/) (`go install github.com/pgaskin/dictutil/cmd/dictgen@latest`).

```sh
./build.sh          # downloads ~8 GB of Wiktionary data on the first run, then builds out/*.zip
```

| File | Purpose |
|---|---|
| `fetch_data.sh` | downloads the [kaikki.org](https://kaikki.org) wiktextract dumps |
| `build.py` | turns them into dictfiles `de-en.df` and `de-tr.df` (about 2 minutes, ~5 GB RAM) |
| `coverage.py` | measures how many words of a German text the dictionary can look up |
| `legacy/` | the first, simpler version (English Wiktionary only) |

Data sources:
- English Wiktionary, German entries: main English definitions and inflection tables
- German Wiktionary: extra lemmas and compounds, English and Turkish translation tables, inflection pages
- Turkish Wiktionary: German entries with Turkish definitions
- English Wiktionary, English entries: translation groups that contain both a German and a Turkish word

## License

- Code: MIT (see `LICENSE`).
- Dictionary content in the release zips: derived from [Wiktionary](https://www.wiktionary.org/) and licensed under [CC BY-SA 4.0](https://creativecommons.org/licenses/by-sa/4.0/).
  - Extracted with [wiktextract](https://github.com/tatuylonen/wiktextract) via [kaikki.org](https://kaikki.org).
  - Packaged with [dictutil](https://github.com/pgaskin/dictutil).
