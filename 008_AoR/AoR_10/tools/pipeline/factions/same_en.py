"""For each untranslated row (todo.json) list existing UA of any label with the same English (hotkey and spacing ignored),
plus UA of a few related phrases. python same_en.py [extra EN regex ...]"""
import json, os, re, sys, collections
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import mf_ua
BS = chr(92) + 'n'


def key(s):
    s = (s or '').replace(BS, '\n')
    s = re.sub(r'\s*\(&\w\)', '', s).replace('&', '')
    return re.sub(r'\s+', ' ', s).strip().lower()


idx = collections.defaultdict(collections.Counter)
for k, (ua, st, src) in mf_ua.UA.items():
    if k in mf_ua.STR and 'Factions/' not in src:
        idx[key(mf_ua.STR[k]['en'])][re.sub(r'\s*\(&\w\)', '', ua.replace(BS, '\n')).strip()] += 1
todo = json.load(open(os.path.join(HERE, 'todo.json'), encoding='utf-8'))
for r in todo:
    hit = idx.get(key(r['en']))
    print(r['var'], '|', r['en'].replace(BS, ' / ')[:70], '=>', dict(hit.most_common(2)) if hit else '-')
for pat in sys.argv[1:]:
    print('==', pat)
    for k, s in mf_ua.STR.items():
        if k in mf_ua.UA and re.search(pat, s['en'] or '', re.I):
            print('  ', (s['en'] or '').replace('\n', ' / ')[:70], '=>', mf_ua.UA[k][0].replace(BS, ' / ')[:90])
