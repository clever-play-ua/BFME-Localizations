"""FoLD_MacOS 2026-11-19 20:07 export (Erebor + leftovers): drop lines already in *_reviewed.json, dump the rest."""
import difflib, glob, json, os, re, collections
HERE = os.path.dirname(os.path.abspath(__file__))
RD = os.path.join(HERE, '..', 'review_fold9')
SRC = os.path.join(RD, 'AoR_UA_FoLD_MacOS_2026-11-19-20-07.json')
R = 'C:/Users/UserM/Documents/GitHub/BFME-Localizations/008_AoR/AoR_UK_WIP/'
d = json.load(open(SRC, encoding='utf-8'))
REV = {r['var']: r['uk'] for f in glob.glob(R + 'Factions/*_reviewed.json') for r in json.load(open(f, encoding='utf-8'))['strings']}
ROW = {}
for p in glob.glob(R + 'heroes_web/*.html') + glob.glob(R + 'Factions/*_AoR_UA.html'):
    D = json.loads(re.search(r'<script id="data" type="application/json">(.*?)</script>', open(p, encoding='utf-8').read(), re.S).group(1))
    for n in D['nodes']:
        for x in n['rows']:
            if 'ref' not in x:
                ROW.setdefault(x['v'], dict(x, node=n.get('name') or n.get('title') or ''))
def wdiff(a, b):
    A, B = re.findall(r'\S+|\n', a), re.findall(r'\S+|\n', b)
    out = []
    for op, i1, i2, j1, j2 in difflib.SequenceMatcher(None, A, B).get_opcodes():
        if op == 'equal': out.append(' '.join(A[i1:i2]))
        else:
            if i1 < i2: out.append('[-' + ' '.join(A[i1:i2]) + '-]')
            if j1 < j2: out.append('{+' + ' '.join(B[j1:j2]) + '+}')
    return ' '.join(out).replace(' \n ', ' / ').replace('\n', ' / ')
groups = collections.defaultdict(list); skipped = collections.Counter()
for n, e in enumerate(d['edits'], 1):
    v = e['var']
    if REV.get(v) == e['uk']: skipped['same as reviewed'] += 1; continue
    if e.get('follows'): skipped['follower'] += 1; continue
    r = ROW.get(v, {})
    base = re.sub(r'\\+n', '\n', r.get('uk') or e['before'] or '')
    norm = lambda t: re.sub(r'[ \t]+', ' ', re.sub(r'[ \t]*\n[ \t]*', '\n', t)).strip()
    k = 'B_changed' if norm(base) != norm(e['uk']) else 'C_ticked'
    groups[k].append((n, e, base))
with open(os.path.join(RD, 'dump.txt'), 'w', encoding='utf-8') as o:
    for k in sorted(groups):
        o.write(f'=================== {k} ({len(groups[k])})\n\n')
        for n, e, base in groups[k]:
            r = ROW.get(e['var'], {})
            o.write(f"#{n} [{e['page']}] {e['var']}  [{e['type'] or r.get('t', '')}]  ({r.get('st', '?')}) rev={e['reviewed']}\n")
            o.write('  EN :' + (e['en'] or r.get('en', '')).replace('\n', '\n').replace('\n', ' / ') + '\n')
            o.write(('  UA :' + e['uk'].replace('\n', ' / ') if k == 'C_ticked' else '  ΔUA:' + wdiff(base, e['uk'])) + '\n\n')
print(dict(skipped), {k: len(v) for k, v in groups.items()}, collections.Counter(e.get('reviewed') for e in d['edits']))
