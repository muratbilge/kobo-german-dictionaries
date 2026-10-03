#!/bin/sh
# Download the Wiktionary extracts (kaikki.org / wiktextract) into data/  (~8 GB)
set -e
mkdir -p data && cd data
curl -fL -o en-German.jsonl  https://kaikki.org/dictionary/German/kaikki.org-dictionary-German.jsonl
curl -fL -o de-Deutsch.jsonl https://kaikki.org/dewiktionary/Deutsch/kaikki.org-dictionary-Deutsch.jsonl
curl -fL -o en-English.jsonl https://kaikki.org/dictionary/English/kaikki.org-dictionary-English.jsonl
curl -fL https://kaikki.org/dictionary/downloads/tr/tr-extract.jsonl.gz | gunzip > tr-extract.jsonl
