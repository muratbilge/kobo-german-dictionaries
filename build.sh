#!/bin/sh
# Build out/dicthtml-de-en.zip and out/dicthtml-de-tr.zip
# needs: python3, dictgen (go install github.com/pgaskin/dictutil/cmd/dictgen@latest)
set -e
[ -f data/en-German.jsonl ] || ./fetch_data.sh
python3 build.py
mkdir -p out
dictgen -o out/dicthtml-de-en.zip de-en.df
dictgen -o out/dicthtml-de-tr.zip de-tr.df
ls -l out
