"""Import FoLD_MacOS 2026-11-16 21:08 export (Misty Mountains) -> Factions/Wild_reviewed.json. User answers 11-17:
1 «Балроґ» in the goblin faction, 2 terrain standard, 3А 4А 5А, 6 «Придбання покращень та укріплення оборони», 7А. Global rules = terms9/round27.py."""
import glob, json, os, re, sys
HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(HERE, '..', 'review_fold8', 'AoR_UA_FoLD_MacOS_2026-11-16-21-08.json')
R = 'C:/Users/UserM/Documents/GitHub/BFME-Localizations/008_AoR/AoR_UK_WIP/'
F = R + 'Factions/'
exp = json.load(open(SRC, encoding='utf-8'))
DATE, BY, FILE = exp['exported'][:10], exp['translator'], os.path.basename(SRC)
ROW = {}
for p in glob.glob(R + 'heroes_web/*.html') + glob.glob(F + '*_AoR_UA.html'):
    D = json.loads(re.search(r'<script id="data" type="application/json">(.*?)</script>', open(p, encoding='utf-8').read(), re.S).group(1))
    for n in D['nodes']:
        for x in n['rows']:
            if 'ref' not in x:
                ROW.setdefault(x['v'], x)

NL = chr(10)
FIX = {  # FoLD_MacOS 2026-11-16: Misty Mountains; answers 1 «Балроґ» (goblins only) 2 standard 3А 4А 5А 6 «…укріплення оборони» 7А
    'CONTROLBAR:ToolTipConstructAltarofFire': [('Поклоняється Балроґу загибелі,', 'Поклоняється Балроґу,')],
    'CONTROLBAR:ToolTipSummonBalrog': [('Прикликати Балроґа з Морії, того самого, що є загибеллю дворфа Дуріна', 'Прикликати Балроґа з Морії')],
    'CONTROLBAR:TooltipChillWind': [('Не діє на вершників', 'Не діє на кавалерію')],
    'CONTROLBAR:ToolTipToggleGundabadFormation': [('Додаткові пошкодження вершникам', 'Додаткові пошкодження кавалерії')],
    'CONTROLBAR:ToolTipBuildWildMountainOrcScoutHorde': [('Цих орків людей боїться', 'Цих орків-мисливців на людей боїться')],
    'CONTROLBAR:ToolTipVampirism': [('уражені від атак велетенських кажанів', 'уражені атаками велетенських кажанів')],
    'CONTROLBAR:ToolTipTheyAreComing': [('Морійські орки впливають на очки командування', 'Орки Морії враховують ліміт очок командування')],
    'CONTROLBAR:PurchaseTechnologyWildHeavyArmor': [('Трофейна броня', 'Трофейні обладунки')],
    'CONTROLBAR:ToolTipPurchaseechnologyWildHeavyArmor': [('«Трофейна броня»', '«Трофейні обладунки»')],
    'OBJECT:WildTreasureTroveDescription': [('2 скарби:', '2 скарбниці:'), ('3 скарби:', '3 скарбниці:'), ('4 скарби:', '4 скарбниці:'), ('5+ скарбів:', '5+ скарбниць:')],
    'CONTROLBAR:ToolTipBuildWildLodgeLevel2Upgrade': [('розвідників гірських орків', 'гірських орків-розвідників')],
    'CONTROLBAR:ToolTipWildColdDrake': [('Лігво змія 2 рівня', 'Лігво зміїв 2 рівня')],
    'CONTROLBAR:ToolTipMuzgashDiscipline': [('+25% до швидкості руху', '+25% швидкості руху')],
    'CONTROLBAR:SummonBalrog': [('*', 'Балроґ')],
}
SAME_EN = {}


def gen(t):
    t = t.replace('’', "'").replace('ʼ', "'")
    t = re.sub(r'(?<![А-ЯІЇЄҐ])протягом (\d+) сек\.(?![^\n]*поступово)', r'на \1 сек.', t)  # rule: «на N сек.» (DoT lines keep «протягом»)
    t = re.sub(r'(?<=,)(?=\S)', ' ', t)
    t = re.sub(r'\(&([a-z])\)', lambda m: f'(&{m[1].upper()})', t)
    t = re.sub(r'[ \t]{2,}', ' ', t)
    t = re.sub(r'[ \t]+(?=\n|$)', '', t)
    t = re.sub(r'(?<=\n)[ \t]+', '', t)
    return t.strip()


DST = {}
for fn, fac in (('Heroes_reviewed.json', 'Heroes'), ('Wild_reviewed.json', 'Wild')):
    p = F + fn
    DST[fn] = json.load(open(p, encoding='utf-8')) if os.path.exists(p) else {'meta': {'faction': fac,
        'note': 'Community proofread lines (highest priority in the build and on the site).'}, 'strings': []}
REV = {r['var']: (fn, r) for fn, d in DST.items() for r in d['strings']}
n_new = n_upd = n_skip = 0
seen_fix = set()
for e in exp['edits']:
    v, master = e['var'], e.get('follows') or e['var']
    t = e['uk']
    for a, b in FIX.get(master, []):
        if a == '*':
            hk = re.search(r'\(&\w\)', t)
            t = b if master == v else (re.sub(r'\(&\w\)', hk.group(0), b) if hk else b)
        else:
            if a not in t:
                print('MISS', v, a[:40]); continue
            t = t.replace(a, b)
        seen_fix.add(master)
    t = gen(t)
    if v in REV and REV[v][1]['uk'] == t:
        n_skip += 1; continue
    rec = {'var': v, 'en': e['en'] or ROW.get(v, {}).get('en', ''), 'uk': t, 'by': BY, 'date': DATE, 'file': FILE}
    if v in REV:
        REV[v][1].update(rec); n_upd += 1
    else:
        fn = 'Wild_reviewed.json' if e['page'] == 'Misty Mountains' else 'Heroes_reviewed.json'
        DST[fn]['strings'].append(rec); REV[v] = (fn, rec); n_new += 1
bad = [(r['var'], r['uk']) for d in DST.values() for r in d['strings'] if (m := re.search(r'&(\w)', r['en'] or '')) and f'(&{m[1].upper()})' not in r['uk']]
for fn, d in DST.items():
    json.dump(d, open(F + fn, 'w', encoding='utf-8', newline=NL), ensure_ascii=False, indent=1)
    print(fn, len(d['strings']))
print('new', n_new, 'updated', n_upd, 'same', n_skip, 'fixes unused', set(FIX) - seen_fix, 'hotkey problems', bad)
