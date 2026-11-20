"""Import FoLD_MacOS 2026-11-19 20:07 export (Erebor) -> Factions/Dwarves_reviewed.json (labels already reviewed on other
pages are updated in place in their own *_reviewed.json). User answers 11-19: 1А «Немилість воронів», 2А «Загони поряд»,
3Б «Друг ельф» (also the campaign button ElfFriendCampaign), 4Б goblin banner wording, 5А «Піт-стоп!», 6А «Тренує …»,
7А «Зростаючий гнів», 8А «щитами-вежами заввишки з дворфа», 9А horde bonus without «одиниць», 10А shared labels take the
Erebor text. Plus typo fixes."""
import glob, json, os, re, sys
HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(HERE, '..', 'review_fold9', 'AoR_UA_FoLD_MacOS_2026-11-19-20-07.json')
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
FIX = {
    'OBJECT:HeroicStatueDescription': [('до пошкоджен та', 'до пошкоджень та')],
    'CONTROLBAR:ToolTipBuildDwarvenBattleWagon': [('Ефективніий', 'Ефективний')],
    'CONTROLBAR:ToolTipToggleKhazadUzbadulFormation': [('Коли Казад-узбадул в оброні вони НЕ', 'Коли Казад-узбадул в обороні, вони НЕ')],
    'CONTROLBAR:ToolTipPurchaseUpgradeDwarvenSiegeHammer': [('Аннулює', 'Анулює'), ('по спорудам', 'по спорудах')],
    'CONTROLBAR:ToolTipToggleIHFighterLineToBlockFormation': [('+40% броні, і штраф', '+40% броні і штраф')],
    'CONTROLBAR:StopRightThere': [('Ану стій там!', 'А ну стій там!')],
    'CONTROLBAR:ToolTipPromoteArcahToLevel3': [('3 рівень: Загони поряд', '3 рівень: Герої поряд')],
    'CONTROLBAR:ToolTipArcahLadyofRavens': [('3 рівень: Загони поряд', '3 рівень: Герої поряд')],
    'CONTROLBAR:ToolTipFireWeaponDwarvenFortressOilCasks': [('«Укріплення»', '«Щільна оборона»')],
    'CONTROLBAR:ToolTipPurchaseUpgradeSentryTowerForgedBlades': [('цю бойову вежу', 'цю сторожову вежу')],
    'CONTROLBAR:ToolTipUpgradeDwarvenBarracksLevel3': [('захисну сторожову вежу', 'захисну вежу')],
    'CONTROLBAR:ToolTipPurchaseUpgradeDwarvenFortressBanners': [('Знижує вартість героїв та час їх вербування на 10%', 'Скорочує час та вартість вербування героїв на 10%')],
    'CONTROLBAR:DwarvenWagonButon3': [('Піт стоп!', 'Піт-стоп!')],
    'CONTROLBAR:ToolTipConstructDwarvenHusbandry': [('Дозволяє тренувати елітні війська Еребору', 'Тренує особливі загони Еребору')],
    'OBJECT:DwarvenForgeWorksDescription': [('Тренування елітних військ Еребору', 'Тренує елітні війська Еребору')],
    'CONTROLBAR:TooltipConstructDwarvenAssembly': [('Тренування союзників', 'Тренує союзників')],
    'CONTROLBAR:ToolTipBuildEreborVWHorde': [('щитами вежами, що заввишки з дворфа', 'щитами-вежами заввишки з дворфа')],
}
EXTRA = {  # not in the export: same decision on another label
    'CONTROLBAR:ElfFriendCampaign': ('Elf-friend', 'Друг ельф'),  # 3Б, Gimli's campaign button
}


def gen(t):
    t = t.replace('’', "'").replace('ʼ', "'")
    t = re.sub(r'(?<![А-ЯІЇЄҐ])протягом (\d+) сек\.(?![^\n]*поступово)', r'на \1 сек.', t)
    t = re.sub(r'(?<=,)(?=\S)', ' ', t)
    t = re.sub(r'\(&([a-z])\)', lambda m: f'(&{m[1].upper()})', t)
    t = re.sub(r'кількості (\d+) (?:одиниць|од\.) і більше', r'кількості \1 і більше', t)  # 9А: 0.14 standard
    t = re.sub(r'[ \t]{2,}', ' ', t)
    t = re.sub(r'[ \t]+(?=\n|$)', '', t)
    t = re.sub(r'(?<=\n)[ \t]+', '', t)
    return t.strip()


DST = {}
for p in sorted(glob.glob(F + '*_reviewed.json')):
    DST[os.path.basename(p)] = json.load(open(p, encoding='utf-8'))
DST.setdefault('Dwarves_reviewed.json', {'meta': {'faction': 'Dwarves',
    'note': 'Community proofread lines (highest priority in the build and on the site).'}, 'strings': []})
REV = {r['var']: (fn, r) for fn, d in DST.items() for r in d['strings']}
n_new = n_upd = n_skip = 0
seen_fix = set()


def put(v, en, t, by=BY, date=DATE, file=FILE):
    global n_new, n_upd, n_skip
    if v in REV and REV[v][1]['uk'] == t:
        n_skip += 1; return
    rec = {'var': v, 'en': en, 'uk': t, 'by': by, 'date': date, 'file': file}
    if v in REV:
        REV[v][1].update(rec); n_upd += 1
    else:
        DST['Dwarves_reviewed.json']['strings'].append(rec); REV[v] = ('Dwarves_reviewed.json', rec); n_new += 1


for e in exp['edits']:
    v, master = e['var'], e.get('follows') or e['var']
    t = e['uk']
    for a, b in FIX.get(master, []):
        if a not in t:
            print('MISS', v, a[:40]); continue
        t = t.replace(a, b)
        seen_fix.add(master)
    put(v, e['en'] or ROW.get(v, {}).get('en', ''), gen(t))
for v, (en, t) in EXTRA.items():
    put(v, en, t, file=FILE + ' (decision 3Б)')
bad = [(r['var'], r['uk']) for d in DST.values() for r in d['strings'] if (m := re.search(r'&(\w)', r['en'] or '')) and f'(&{m[1].upper()})' not in r['uk']]
for fn, d in DST.items():
    json.dump(d, open(F + fn, 'w', encoding='utf-8', newline=NL), ensure_ascii=False, indent=1)
    print(fn, len(d['strings']))
print('new', n_new, 'updated', n_upd, 'same', n_skip, 'fixes unused', set(FIX) - seen_fix, 'hotkey problems', bad)
