"""Show EN | current UA for labels matching a regex (var) or EN text regex: python peek.py var <re> | en <re> [limit]"""
import re, sys, os
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import mf_ua
mode, pat = sys.argv[1], re.compile(sys.argv[2], re.I)
lim = int(sys.argv[3]) if len(sys.argv) > 3 else 15
n = 0
for k, s in mf_ua.STR.items():
    hay = s['var'] if mode == 'var' else (s['en'] or '')
    if pat.search(hay) and k in mf_ua.UA:
        ua, st, src = mf_ua.UA[k]
        print('##', s['var'], '|', st, '|', src)
        print('  EN:', (s['en'] or '').replace('\n', ' / '))
        print('  UA:', ua.replace(chr(92) + 'n', ' / '))
        n += 1
        if n >= lim:
            break
