"""Faction JSON (make_faction.py) -> one self-contained HTML page for community translation.
usage: python make_web.py Isengard"""
import base64, json, os, sys
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
from icons import icon

FACTION = sys.argv[1] if len(sys.argv) > 1 else 'Isengard'
B008 = r'C:/Users/UserM/Documents/GitHub/BFME-Localizations/008_AoR/'
SRC = B008 + f'AoR_UK_WIP/Factions/{FACTION}_AoR_UA.json'
DST = B008 + f'AoR_UK_WIP/Factions/{FACTION}_AoR_UA.html'
d = json.load(open(SRC, encoding='utf-8'))

TYPES = {'Кнопка': 'Button', 'Підказка': 'Tooltip', 'Назва': 'Name', 'Опис': 'Description', 'Вимога': 'Requirement',
         'Конфлікт': 'Conflict', 'Придбано': 'Purchased', 'Текст вербування': 'Recruit text',
         'Текст відродження': 'Revive text'}
STATUS = {'вичитано': 'ok', 'чернетка AI': 'draft', 'переклад Сергія': 'comm', 'RotWK UA': 'rotwk', 'немає перекладу': 'missing'}


def ty(t):
    soldier, ingame = ' (воїн загону)' in t, ' (у грі)' in t
    t = t.replace(' (воїн загону)', '').replace(' (у грі)', '')
    return TYPES.get(t, t) + (' (soldier)' if soldier else '') + (' (in game)' if ingame else '')


nodes, owner_id, refs = [], {}, []


def add_node(n, section, parent=None, kind='object'):
    nid = f'n{len(nodes) + 1}'
    rows = []
    for r in n.get('рядки', []):
        if 'див' in r:
            x = {'v': r['var'], 't': ty(r['type']), 'en': r['en'], 'ref': None}
            refs.append(x)
        else:
            x = {'v': r['var'], 't': ty(r['type']), 'en': r['en'], 'uk': r.get('uk') or r.get('uk_ai', ''),
                 'st': STATUS.get(r.get('status'), 'draft')}
            owner_id[r['var']] = nid
        if r.get('btn'):
            x['btn'] = r['btn']
        if r.get('btn_en'):
            x['be'] = r['btn_en']
        if r.get('btn_ua'):
            x['bu'] = r['btn_ua']
        if r.get('icon'):
            x['icon'] = r['icon']
        if r.get('cost'):
            x['cost'] = r['cost']
        rows.append(x)
    name_var = next((r['var'] for r in n.get('рядки', []) if r['type'] == 'Назва'), None)
    node = {'id': nid, 'section': section, 'parent': parent, 'name': n.get('назва', ''), 'ua': n.get('uk_назва', ''),
            'icon': n.get('icon'), 'nameVar': name_var, 'kindLabel': kind, 'rows': rows, 'kids': []}
    nodes.append(node)
    for key, label, k2 in (('прибудови', 'expansions', 'expansion'), ('юніти', 'units', 'unit')):
        for c in n.get(key, []):
            node['kids'].append(add_node(c, section, nid, k2))
            node['kidsLabel'] = label
    return nid


add_node(d['Фортеця'], 'fortress', kind='building')
for h in d['Герої']:
    add_node(h, 'heroes', kind='hero')
for b in d['Будівлі']:
    add_node(b, 'buildings', kind='building')
bid = add_node({'назва': 'Spell book', 'рядки': d['Книга сил']['рядки']}, 'book', kind='spell book')
book = next(n for n in nodes if n['id'] == bid)
book['spells'] = d['Книга сил'].get('spells', [])
book['icon'] = book['spells'][0]['icon'] if book['spells'] else None
for x in refs:
    x['ref'] = owner_id.get(x['v'])

# 100% identical English (hotkey/spacing ignored) is shown once: later rows follow the first one
import re as _re
def _key(en):
    t = _re.sub(r'\s*\(&\w\)', '', (en or '').replace(chr(92) + 'n', '\n')).replace('&', '')
    return _re.sub(r'\s+', ' ', t).strip().lower()
_first = {}
for n in nodes:
    for x in n['rows']:
        k = _key(x['en'])
        if k and not x.get('ref') and k not in _first:
            _first[k] = (n['id'], x['v'])
for n in nodes:
    for x in n['rows']:
        k = _key(x['en'])
        if k in _first and _first[k] != (n['id'], x['v']):
            x['dup'] = _first[k][1]

# every picture used once, base64
names = {n['icon'] for n in nodes if n['icon']} | {r['icon'] for n in nodes for r in n['rows'] if r.get('icon')}     | {s['icon'] for s in book['spells'] if s.get('icon')} | {'Resource_Icon'}
ICONS = {}
for nm in sorted(names):
    v = icon(nm)
    if v:
        ICONS[nm] = v

EN_NAME = {'Men': 'Gondor', 'Dwarves': 'Erebor', 'Elves': 'Lothlorien', 'Arnor': 'Rivendell', 'Mirkwood': 'Woodland Realm', 'Wild': 'Misty Mountains', 'Guldur': 'Dol Guldur', 'Angmar': 'Haradwaith'}
data = {'faction': EN_NAME.get(FACTION, FACTION), 'factionUA': d['meta'].get('uk_name', ''), 'title': EN_NAME.get(FACTION, FACTION),
        'icon': nodes[0]['icon'], 'nodes': nodes}
GAME_FONT = 'C:/Users/UserM/Documents/GitHub/BFME-Localizations/008_AoR/AoR_10/tools/lang_Ukrainian/Albertus_Medium.ttf'  # the in-game font (designer's)
font = lambda f: base64.b64encode(open(os.path.join(HERE, 'fonts', f), 'rb').read()).decode()
js = lambda o: json.dumps(o, ensure_ascii=False, separators=(',', ':')).replace('</', '<\\/')
html = open(os.path.join(HERE, 'template.html'), encoding='utf-8').read()
html = (html.replace('__TITLE__', f'{EN_NAME.get(FACTION, FACTION)} — AoR Ukrainian translation').replace('__FONT_CINZEL__', font('cinzel.woff')).replace('__FONT_GAME__', base64.b64encode(open(GAME_FONT, 'rb').read()).decode())
        .replace('__DATA__', js(data)).replace('__ICONS__', js(ICONS)))
open(DST, 'w', encoding='utf-8').write(html)
json.dump({x['v']: x['st'] for n in nodes for x in n['rows'] if 'ref' not in x and not x.get('dup')},
          open(DST.replace('.html', '.vars.json'), 'w', encoding='utf-8'), ensure_ascii=False)
own = sum(1 for n in nodes for r in n['rows'] if not r.get('ref') and 'ref' not in r)
print(DST, len(html) // 1024, 'KB;', len(nodes), 'nodes;', own, 'own rows;', len(ICONS), 'icons;',
      sum(1 for x in refs if not x['ref']), 'dangling refs')
