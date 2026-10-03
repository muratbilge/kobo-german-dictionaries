#!/usr/bin/env python3
"""Coverage test: share of words in a German text that a dictfile can look up.
Usage: coverage.py DICT.df TEXT.txt [MARKER] [N_TOP_MISSES]   (MARKER: count only entries containing it, e.g. Türkçe)"""
import re,sys,collections
def keys(df, need=None):
    k=set(); cur=[]
    for l in open(df,encoding='utf-8'):
        if l.startswith(('@ ','& ')): cur.append(l[2:].strip().lower())
        else:
            if need is None or need in l: k.update(cur)
            cur=[]
    return k
K=keys(sys.argv[1], sys.argv[3] if len(sys.argv)>3 and sys.argv[3] else None)
toks=[t for t in re.findall(r"[A-Za-zÄÖÜäöüß]+",open(sys.argv[2],encoding='utf-8').read()) if len(t)>1]
names=set(t.lower() for t in toks if t[0].isupper()) - set(t.lower() for t in toks if t[0].islower())
miss=collections.Counter(t for t in toks if t.lower() not in K)
lc_miss=collections.Counter(t for t in miss.elements() if t[0].islower())
print(f"found {100-100*sum(miss.values())/len(toks):.1f}% of running words; lowercase-word misses {sum(lc_miss.values())}")
if len(sys.argv)>4: print(' '.join(w for w,_ in miss.most_common(int(sys.argv[4]))))
