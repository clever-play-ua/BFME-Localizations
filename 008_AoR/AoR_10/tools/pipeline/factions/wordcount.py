"""Count word forms (regex from argv) in every Ukrainian text field of the project sources."""
import collections, glob, json, os, re, sys
R = 'C:/Users/UserM/Documents/GitHub/BFME-Localizations/008_AoR/'
pat = re.compile(sys.argv[1], re.I)
c = collections.Counter()


def walk(x):
    if isinstance(x, dict):
        for k, v in x.items():
            if k in ('uk', 'uk_ai', 'sergii') and isinstance(v, str):
                for w in pat.findall(v):
                    c[w.lower()] += 1
            else:
                walk(v)
    elif isinstance(x, list):
        for v in x:
            walk(v)


for f in glob.glob(R + 'AoR_UK_WIP/**/*.json', recursive=True) + [R + 'AoR_10/menu_strings.json']:
    if os.sep + 'site' + os.sep in f or '/site/' in f.replace('\\', '/'):
        continue
    try:
        walk(json.load(open(f, encoding='utf-8')))
    except Exception:
        pass
for k, v in sorted(c.items(), key=lambda x: -x[1]):
    print(v, k)
