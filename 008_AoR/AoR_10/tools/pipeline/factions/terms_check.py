"""How existing UA text renders a few EN terms: for each EN regex, print the most common UA snippets around matches."""
import re, sys, os, collections
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import mf_ua
UA = {k: v[0] for k, v in mf_ua.UA.items()}
allua = '\n'.join(UA.values())
for w in ['Ізенґард', 'Ізенгард', 'Дунланд', 'дунландц', 'дунлендин', 'Дунлендин', 'урук-ха', 'Урук-ха', 'варґ', 'Курунір', 'берсерк', 'Сарума', 'Червеуст', 'Вульфґар', 'Вульфгар', 'Уґлук', 'Углук', 'Лурц', 'Шарку', 'Рогірим', 'рогірим', 'Ізен']:
    print(w, len(re.findall(w, allua)))
for pat in sys.argv[1:]:
    c = collections.Counter()
    for k, s in mf_ua.STR.items():
        if k in UA and re.search(pat, s['en'] or '', re.I):
            for line in UA[k].split(chr(92) + 'n'):
                c[line.strip()[:90]] += 1
    print('==', pat)
    for t, n in c.most_common(6):
        print('  ', n, t)
