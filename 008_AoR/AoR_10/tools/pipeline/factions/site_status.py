"""Translation status of the whole game for the site's overview page.
Mirrors the source priority of build_uk_submod.load_uk() and records WHERE each label's Ukrainian comes from:
  rev   community proofread on the site (Factions/*_reviewed.json)
  ok    human translation (UK columns, editor files «uk», Serhii, menu «uk»)
  draft AI draft only (UK AI / uk_ai / Factions/*_AI_drafts.json)
  (missing) -> English in the game
Sections: interface, campaigns (sheet rows of RotK_campaign_strings.xlsx), War of the Ring, Create-a-Hero, everything."""
import json, os, re, sys
from openpyxl import load_workbook

TOOLS = 'C:/Users/UserM/Documents/GitHub/BFME-Localizations/008_AoR/AoR_10/tools'
sys.path.insert(0, TOOLS)
from sheets import ALL_SHEET, CAMPAIGN_SHEETS, MENU_JSON, UK_SHEETS, XLSX  # noqa: E402

AOR10 = os.path.dirname(TOOLS)
WIP = os.path.join(os.path.dirname(AOR10), 'AoR_UK_WIP')
FACTIONS = os.path.join(WIP, 'Factions')
TOOLTIPS_JSON = os.path.join(WIP, 'Menu_tooltips_strings.json')
WOTR_CATS = {'LW', 'LWA', 'LWSCENARIO', 'WOTR', 'WOTRSCRIPT', 'WOTRTUTORIAL', 'STRATEGICHUD'}
CAH_CATS = {'CREATEAHERO', 'CAH'}
HAS_TEXT = re.compile(r'[A-Za-z]{2}')


def _j(p):
    return json.load(open(p, encoding='utf-8'))


def resolve():
    """var(lower) -> 'rev' | 'ok' | 'draft' (same order as the build: the first source that has text wins)."""
    K = {}
    def put(v, kind, text):
        if (text or '').strip() and v.lower() not in K:
            K[v.lower()] = kind
    for fn in sorted(os.listdir(FACTIONS)):
        if fn.endswith('_reviewed.json'):
            for r in _j(os.path.join(FACTIONS, fn))['strings']:
                put(r['var'], 'rev', r.get('uk'))
    for sub in ('heroes', 'Skirmish', 'RoTK'):
        folder = os.path.join(WIP, sub)
        for fn in sorted(os.listdir(folder)) if os.path.isdir(folder) else []:
            if fn.endswith('.json'):
                d = _j(os.path.join(folder, fn))
                for sec in ('Кампанія', 'Битва', 'strings'):
                    for r in d.get(sec, []):
                        if (r.get('uk') or '').strip():
                            put(r['var'], 'ok', r['uk'])
                        else:
                            put(r['var'], 'draft', r.get('uk_ai'))
    for r in _j(os.path.join(WIP, 'Serhii_strings.json'))['strings']:
        put(r['var'], 'ok', r.get('sergii'))
    for fn in sorted(os.listdir(FACTIONS)):
        if fn.endswith('_serhii.json'):
            for r in _j(os.path.join(FACTIONS, fn))['strings']:
                put(r['var'], 'ok', r.get('sergii'))
    wb = load_workbook(XLSX, read_only=True)
    sheets = {}
    for name in UK_SHEETS:
        if name == ALL_SHEET:
            for p in (MENU_JSON, TOOLTIPS_JSON):
                for s in _j(p)['strings'] if os.path.exists(p) else []:
                    src = s.get('uk_ai_source') or ''
                    checked = (src.startswith('RotWK UA') and 'шаблон' not in src) or src == 'той самий EN'
                    if (s.get('uk') or '').strip() or checked:  # «RotWK UA» = our checked RotWK translation
                        put(s['var'], 'ok', s.get('uk') or s.get('uk_ai'))
                    else:
                        put(s['var'], 'draft', s.get('uk_ai'))
        if name not in wb.sheetnames:
            continue
        rows = wb[name].iter_rows(values_only=True)
        head = list(next(rows))
        recs = [dict(zip(head, r)) for r in rows]
        sheets[name] = recs
        for d in recs:
            if not d.get('Переменная'):
                continue
            if (d.get('UK') or '').strip():
                put(d['Переменная'], 'ok', d['UK'])
            else:
                put(d['Переменная'], 'draft', d.get('UK AI'))
    for fn in sorted(os.listdir(FACTIONS)):
        if fn.endswith('_AI_drafts.json'):
            dd = _j(os.path.join(FACTIONS, fn))
            if not dd.get('meta', {}).get('site_only'):
                for r in dd['strings']:
                    put(r['var'], 'draft', r.get('uk_ai'))
    return K, sheets


def count(K, labels):
    seen, c = set(), {'rev': 0, 'ok': 0, 'draft': 0, 'missing': 0}
    for v, en in labels:
        if v.lower() in seen or not HAS_TEXT.search(en or ''):
            continue
        seen.add(v.lower())
        c[K.get(v.lower(), 'missing')] += 1
    c['total'] = len(seen)
    return c


def status():
    K, sheets = resolve()
    allrows = sheets[ALL_SHEET]
    out = {}
    menu = _j(MENU_JSON)['strings'] + (_j(TOOLTIPS_JSON)['strings'] if os.path.exists(TOOLTIPS_JSON) else [])
    out['menu'] = count(K, [(s['var'], s.get('en')) for s in menu])
    for name in CAMPAIGN_SHEETS:
        rows = [(d['Переменная'], d['EN']) for d in sheets.get(name, []) if d.get('Переменная')]
        out['camp:' + name] = count(K, rows)
        missions = {}
        for d in sheets.get(name, []):
            if d.get('Переменная'):
                missions.setdefault(d.get('Задание') or '', []).append((d['Переменная'], d['EN']))
        out['missions:' + name] = {m: count(K, rs) for m, rs in missions.items()}
    out['wotr'] = count(K, [(d['Переменная'], d['EN']) for d in allrows if d.get('Категорія') in WOTR_CATS])
    out['cah'] = count(K, [(d['Переменная'], d['EN']) for d in allrows if d.get('Категорія') in CAH_CATS])
    out['all'] = count(K, [(d['Переменная'], d['EN']) for d in allrows if d.get('Переменная')])
    return out


if __name__ == '__main__':
    s = status()
    for k, v in s.items():
        if not k.startswith('missions:'):
            print(k, v)
    print(s['missions:FotR'])
