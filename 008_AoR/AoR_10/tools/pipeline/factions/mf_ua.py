"""Skirmish faction tree -> AoR_UK_WIP/Factions/<Faction>_AoR_UA.json
Фортеця (+ прибудови, покращення) / Будівлі (+ юніти, покращення) / Герої (+ здібності) / Книга сил / Загальні кнопки.
Each label appears once (first place in the tree); later places get a short {"var", "en", "див"} reference.
usage: python make_faction.py Isengard"""
import collections, json, os, re, sys
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)

B008 = r'C:/Users/UserM/Documents/GitHub/BFME-Localizations/008_AoR/'
TOOLS = B008 + 'AoR_10/tools'
sys.path.insert(0, TOOLS)
import build_uk_submod as bu  # noqa: E402
from openpyxl import load_workbook  # noqa: E402

FACTION = sys.argv[1] if len(sys.argv) > 1 else 'Isengard'
UA_NAME = {'Isengard': 'Ізенґард', 'Mordor': 'Мордор', 'Men': 'Ґондор', 'Rohan': 'Роган', 'Dwarves': 'Еребор',
           'Elves': 'Лотлоріен', 'Arnor': 'Рівендел', 'Mirkwood': 'Лісове королівство', 'Wild': 'Імлисті гори',
           'Guldur': 'Дол-Ґулдур', 'Angmar': 'Харадвайт'}
TOK = re.compile(r'[A-Za-z0-9_]{3,}')
SKIP_SET = re.compile(r'(_?WOTR|WotR|ForAI|EasyNormalAI|_AI$|RealTime|Strategic|LW_|Campaign)', re.I)

# ---------------- texts: EN/RU + effective UA with its source (same order as the build) ----------------
STR = {s['var'].lower(): s for s in json.load(open(B008 + 'AoR_10/strings.json', encoding='utf-8'))['strings']}
UA = {}  # var -> (text, status, source)


def put(var, text, status, src):
    if text and var.lower() not in UA:
        UA[var.lower()] = (text.replace('\n', '\\n'), status, src)


def load_ua():
    import glob as _g
    for path in sorted(_g.glob(os.path.join(bu.WIP, 'Factions', '*_reviewed.json'))):  # community proofread wins
        for r in json.load(open(path, encoding='utf-8'))['strings']:
            put(r['var'], r['uk'], 'вичитано', 'Factions/' + os.path.basename(path))
    for sub in bu.WIP_DIRS:
        folder = os.path.join(bu.WIP, sub)
        for fn in sorted(os.listdir(folder)) if os.path.isdir(folder) else []:
            if fn.endswith('.json'):
                d = json.load(open(os.path.join(folder, fn), encoding='utf-8'))
                for sec in ('Кампанія', 'Битва', 'strings'):
                    for r in d.get(sec, []):
                        uk, ai = (r.get('uk') or '').strip(), (r.get('uk_ai') or '').strip()
                        st = 'вичитано' if uk else (r.get('status') or 'чернетка AI')
                        put(r['var'], uk or ai, st, f'{sub}/{fn}')
    for r in json.load(open(bu.SERHII_JSON, encoding='utf-8'))['strings']:
        put(r['var'], (r.get('sergii') or '').strip(), 'переклад Сергія', 'Serhii_strings.json')
    for path in sorted(_g.glob(os.path.join(bu.WIP, 'Factions', '*_serhii.json'))):  # site only, not in the build
        for r in json.load(open(path, encoding='utf-8'))['strings']:
            put(r['var'], (r.get('sergii') or '').strip(), 'переклад Сергія', 'Factions/' + os.path.basename(path))
    wb = load_workbook(bu.XLSX, read_only=True)
    for name in bu.UK_SHEETS:
        if name == bu.ALL_SHEET:
            for path in (bu.MENU_JSON, bu.TOOLTIPS_JSON):
                for s in json.load(open(path, encoding='utf-8'))['strings']:
                    put(s['var'], s.get('uk') or s.get('uk_ai'), 'вичитано' if s.get('uk') else 'чернетка AI',
                        os.path.basename(path))
        if name not in wb.sheetnames:
            continue
        rows = wb[name].iter_rows(values_only=True)
        head = list(next(rows))
        iv, iai, iuk = head.index('Переменная'), head.index('UK AI'), head.index('UK')
        for r in rows:
            if r[iv]:
                uk, ai = (r[iuk] or '').strip(), (r[iai] or '').strip()
                put(r[iv], uk or ai, 'вичитано' if uk else 'чернетка AI', 'xlsx:' + name)
    # AI drafts made for the faction pages (lowest priority)
    import glob as _g
    for path in sorted(_g.glob(os.path.join(bu.WIP, 'Factions', '*_AI_drafts.json'))):
        for r in json.load(open(path, encoding='utf-8'))['strings']:
            put(r['var'], r['uk_ai'].replace(chr(92) + 'n', chr(10)), 'чернетка AI', 'Factions/' + os.path.basename(path))


load_ua()
RP = {r['var'].lower() for r in json.load(open(bu.WIP + '/RingPowers_Skirmish_strings.json', encoding='utf-8'))['strings']}


