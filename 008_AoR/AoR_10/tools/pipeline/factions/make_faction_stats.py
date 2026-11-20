"""Skirmish faction tree -> AoR_UK_WIP/Factions/<Faction>_AoR_UA.json
Фортеця (+ прибудови, покращення) / Будівлі (+ юніти, покращення) / Герої (+ здібності) / Книга сил / Загальні кнопки.
Each label appears once (first place in the tree); later places get a short {"var", "en", "див"} reference.
usage: python make_faction.py Isengard"""
import collections, json, os, re, sys
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
from iniparse import load, AOR

B008 = r'C:/Users/UserM/Documents/GitHub/BFME-Localizations/008_AoR/'
TOOLS = B008 + 'AoR_10/tools'
sys.path.insert(0, TOOLS)
import build_uk_submod as bu  # noqa: E402
from openpyxl import load_workbook  # noqa: E402

FACTION = sys.argv[1] if len(sys.argv) > 1 else 'Isengard'
UA_NAME = {'Isengard': 'Ізенґард', 'Mordor': 'Мордор', 'Men': 'Ґондор', 'Rohan': 'Роган', 'Dwarves': 'Еребор',
           'Elves': 'Лотлоріен', 'Arnor': 'Рівендел', 'Mirkwood': 'Лісове королівство', 'Wild': 'Імлисті гори',
           'Guldur': 'Дол-Ґулдур', 'Angmar': 'Харадвайт'}
D = load()
O, S, BTN, PARENT = D['Object'], D['CommandSet'], D['CommandButton'], D['parent']
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


# ---------------- INI helpers ----------------
def chain(o):
    out = [o]
    while out[-1] in PARENT and len(out) < 10:
        out.append(PARENT[out[-1]])
    return out


def body(o):
    return ''.join(O.get(x, '') for x in chain(o))


def field(text, name):
    m = re.search(r'^\s*' + name + r'\s*=\s*(\S+)', text, re.M)
    return m.group(1) if m else None


def fields(text, name):
    return re.findall(r'^\s*' + name + r'\s*=\s*(\S+)', text, re.M)


def kinds(o):
    ks = ' '.join(fields(body(o), 'KindOf') + re.findall(r'^\s*KindOf\s*=\s*(.+)$', body(o), re.M)).upper().split()
    return {x for k in ks for x in D['defines'].get(k, k).upper().split()}


def obj_sets(o):
    seen = []
    for t in TOK.findall(body(o)):
        if t in S and t not in seen and not SKIP_SET.search(t):
            seen.append(t)
    return seen


def set_buttons(s):
    out = []
    for m in re.finditer(r'^\s*\d+\s*=\s*(\S+)', S.get(s, ''), re.M):
        if m.group(1) in BTN and m.group(1) not in out:
            out.append(m.group(1))
    return out


OBJ_LABELS = [('DisplayName', 'Назва'), ('Description', 'Опис'), ('RecruitText', 'Текст вербування'),
              ('ReviveText', 'Текст відродження')]
BTN_LABELS = [('TextLabel', 'Кнопка'), ('DescriptLabel', 'Підказка'), ('LacksPrerequisiteLabel', 'Вимога'),
              ('ConflictingLabel', 'Конфлікт'), ('PurchasedLabel', 'Придбано')]
MAKES = ('UNIT_BUILD', 'DOZER_CONSTRUCT', 'FOUNDATION_CONSTRUCT', 'CASTLE_UNPACK_EXPLICIT_OBJECT')


def btn_objects(b):
    t = BTN[b]
    if (field(t, 'Command') or '') not in MAKES:
        return []
    return [x for x in fields(t, 'Object') if x in O]


# ---------------- generic labels: used by objects of many sides ----------------
SIDE = {}
for o in O:
    SIDE[o] = (field(body(o), 'Side') or '').strip()
label_sides = collections.defaultdict(set)
for o in O:
    if not SIDE[o]:
        continue
    for s in obj_sets(o):
        for b in set_buttons(s):
            for f, _ in BTN_LABELS[:2]:
                v = field(BTN[b], f)
                if v:
                    label_sides[v.lower()].add(SIDE[o])


def generic(var):
    return len(label_sides.get(var.lower(), ())) >= 4


# ---------------- tree ----------------
owner = {}  # var -> path where it is shown first
general = []
stat = collections.Counter()


def row(var, typ, path):
    k = var.lower()
    if k not in STR or not re.search(r'[A-Za-z]', STR[k]['en'] or ''):
        return None
    en = STR[k]['en'].replace('\n', '\\n')
    if k in owner:
        stat['див'] += 1
        return {'var': STR[k]['var'], 'type': typ, 'en': en, 'див': owner[k]}
    ua, st, src = UA.get(k, ('', 'немає перекладу', ''))
    if k in RP and path[0] != 'Книга сил':
        pass
    r = {'var': STR[k]['var'], 'type': typ, 'en': en, 'ru': (STR[k].get('ru') or '').replace('\n', '\\n'),
         'uk_ai': ua, 'status': st, 'джерело': src, 'uk': ''}
    if generic(var):  # shared by most factions: translated separately, not in faction files
        stat['загальні (пропущено)'] += 1
        return None
    owner[k] = ' › '.join(path)
    stat[st] += 1
    return r


def add(rows, var, typ, path, btn=None):
    if var:
        r = row(var, typ, path)
        if r and not any(x['var'] == r['var'] for x in rows):
            if btn:  # rows of one button share 'btn'; its picture goes to 'icon'
                r['btn'] = btn
                tl = (field(BTN[btn], 'TextLabel') or '').lower()
                if tl in STR and STR[tl]['en']:
                    r['btn_en'] = STR[tl]['en'].replace('\n', ' ')
                if tl in UA:
                    r['btn_ua'] = UA[tl][0]
                img = field(BTN[btn], 'ButtonImage')
                if img:
                    r['icon'] = img
                c = btn_cost(btn)
                if c:
                    r['cost'] = c
                for g in general:  # the shared copy in «Загальні кнопки» gets the same grouping/picture
                    if g['var'] == r['var'] and 'btn' not in g:
                        g['btn'] = btn
                        if img:
                            g['icon'] = img
            rows.append(r)


def num(v, depth=0):
    v = (v or '').strip()
    if re.fullmatch(r'-?\d+(\.\d+)?', v):
        return int(float(v))
    if depth < 6 and v.upper() in D['defines']:
        return num(D['defines'][v.upper()], depth + 1)
    return None


def btn_cost(b):
    t = BTN[b]
    cmd = field(t, 'Command') or ''
    if cmd in MAKES:
        o = field(t, 'Object')
        return {'gold': num(field(body(o), 'BuildCost'))} if o in O and num(field(body(o), 'BuildCost')) else None
    if cmd in ('OBJECT_UPGRADE', 'PLAYER_UPGRADE'):
        u = field(t, 'Upgrade')
        c = num(field(D['Upgrade'].get(u, ''), 'BuildCost'))
        return {'gold': c} if c else None
    if cmd == 'PURCHASE_SCIENCE':
        c = num(field(D['Science'].get(field(t, 'Science') or '', ''), 'SciencePurchasePointCostMP'))
        return {'points': c} if c else None
    return None


def obj_icon(o, made_by=None):
    if made_by and field(BTN[made_by], 'ButtonImage'):
        return field(BTN[made_by], 'ButtonImage')
    for f in ('ButtonImage', 'SelectPortrait'):
        v = field(body(o), f)
        if v:
            return v
    return None


def has_name(o):
    return any((field(O.get(x, ''), 'DisplayName') or '').lower() in STR for x in chain(o))


def en_name(o):
    for x in chain(o):
        v = field(O.get(x, ''), 'DisplayName')
        if v and v.lower() in STR:
            return STR[v.lower()]['en']
    return o


def ua_name(o):
    for x in chain(o):
        v = field(O.get(x, ''), 'DisplayName')
        if v and v.lower() in UA:
            return UA[v.lower()][0]
    return ''


visited = set()
buildings, heroes_sec = [], []


def node(o, path, made_by=None, sink=None):
    """one object: its name/description, the button that makes it, its own command sets; children nested."""
    visited.add(o)
    name = en_name(o)
    p = path + [name]
    n = {'назва': name, 'uk_назва': ua_name(o), "об'єкт": o, 'icon': obj_icon(o, made_by), 'рядки': []}
    rows = n['рядки']
    if made_by:
        for f, typ in BTN_LABELS:
            add(rows, field(BTN[made_by], f), typ, p, made_by)
    for x in chain(o):
        for f, typ in OBJ_LABELS:
            add(rows, field(O.get(x, ''), f), typ, p)
    # horde members (names shown on hover)
    for m in re.findall(r'^\s*InitialPayload\s*=\s*(\S+)', body(o), re.M):
        if m in O:
            for f, typ in OBJ_LABELS[:2]:
                add(rows, field(body(m), f), typ + ' (воїн загону)', p)
    kids = collections.OrderedDict()
    for s in obj_sets(o):
        for b in set_buttons(s):
            made = [x for x in btn_objects(b) if x != fortress_obj and has_name(x)
                    and (SIDE.get(x) in ('', FACTION) or 'STRUCTURE' not in kinds(x))]
            if btn_objects(b) and not made and any(not has_name(x) for x in btn_objects(b)):
                made = None  # dummy object (e.g. a Focus toggle): the button itself is the content
            elif btn_objects(b) and not made:
                continue  # another faction's structure / the fortress again
            if made:
                for x in made:
                    if x not in visited:
                        kids.setdefault(x, b)
                continue
            for f, typ in BTN_LABELS:
                add(rows, field(BTN[b], f), typ, p, b)
    for x, b in kids.items():
        if x in visited:
            continue
        ks = kinds(x)
        if 'HERO' in ks:
            continue  # heroes get their own section
        if 'STRUCTURE' in ks and sink is not None:
            sink.append((x, b))
            visited.add(x)
            continue
        key = 'прибудови' if 'STRUCTURE' in ks else 'юніти'
        c = node(x, p, b, sink)
        if any('див' not in r for r in c['рядки']) or c.get('юніти') or c.get('прибудови'):
            n.setdefault(key, []).append(c)
    if not rows and not any(k in n for k in ('прибудови', 'юніти')):
        return n
    return n


pt = re.search(r'^PlayerTemplate Faction' + FACTION + r'\b(.*?)^End', open(AOR + '/data/ini/playertemplate.ini',
               encoding='cp1252').read(), re.M | re.S).group(1)
fortress_obj = field(pt, 'StartingBuilding')
citadel = next((o for o in (fortress_obj + 'Citadel', fortress_obj) if o in O and obj_sets(o)), fortress_obj)
hero_list = [h for h in (field(pt, 'BuildableHeroesMP') and re.search(r'BuildableHeroesMP\s*=\s*(.*)', pt).group(1).split() or [])
             if h in O and h != 'CreateAHero']
for h in hero_list:
    visited.add(h)

# --- fortress: citadel + expansion pads + starting builder
pending = []
fort = node(citadel, ['Фортеця'], sink=pending)
fort['назва'] = en_name(fortress_obj)
add(fort['рядки'], field(O[fortress_obj], 'DisplayName'), 'Назва', ['Фортеця'])
for b in BTN:
    if fortress_obj in fields(BTN[b], 'Object') and 'Porter' in b:
        for f, typ in BTN_LABELS:
            add(fort['рядки'], field(BTN[b], f), typ, ['Фортеця'], b)
pads = [o for o in O if o.startswith(fortress_obj + 'ExpansionPad')]
for pad in pads:
    for s in obj_sets(pad):
        for b in set_buttons(s):
            for x in btn_objects(b):
                if x not in visited:
                    fort.setdefault('прибудови', []).append(node(x, ['Фортеця'], b))

# --- buildings: everything the builders put down (porter + other units' build menus), in button order
while pending:
    x, b = pending.pop(0)
    c = node(x, ['Будівлі'], b, pending)
    if any('див' not in r for r in c['рядки']) or c.get('юніти'):
        buildings.append(c)

# --- heroes
for h in hero_list:
    btn = next((b for b in BTN if h in fields(BTN[b], 'Object') and (field(BTN[b], 'Command') or '') in MAKES), None)
    visited.discard(h)
    heroes_sec.append(node(h, ['Герої'], btn))

# --- spell book (also in RingPowers_Skirmish_strings.json)
book = {'назва': 'Книга сил', 'рядки': [], 'spells': []}
store = field(pt, 'PurchaseScienceCommandSetMP')
sci_btn = {}
slots = [(int(m.group(1)), m.group(2)) for m in re.finditer(r'^\s*(\d+)\s*=\s*(\S+)', S.get(store, ''), re.M) if m.group(2) in BTN]
for slot, b in slots:
    sci_btn[(field(BTN[b], 'Science') or '').lower()] = b
side_sci = 'SCIENCE_' + FACTION.upper()
for slot, b in slots:
    for f, typ in BTN_LABELS[:3]:
        add(book['рядки'], field(BTN[b], f), typ, ['Книга сил'], b)
    # the spell the player actually casts (spell book button) may have its own tooltip
    trig = field(BTN[b], 'CommandTrigger')
    if trig in BTN:
        for f, typ in BTN_LABELS[:2]:
            add(book['рядки'], field(BTN[trig], f), typ + ' (у грі)', ['Книга сил'], b)
    sci = D['Science'].get(field(BTN[b], 'Science') or '', '')
    m = re.search(r'PrerequisiteSciences\s*=\s*(.*)', sci)
    pre = m.group(1) if m else ''
    parents = []
    for alt in re.split(r'OR', pre):
        toks = alt.split()
        if side_sci in [x.upper() for x in toks]:
            parents += [sci_btn[x.lower()] for x in toks if x.lower() in sci_btn]
    book['spells'].append({'btn': b, 'slot': slot, 'cost': num(field(sci, 'SciencePurchasePointCostMP')),
                           'icon': field(BTN[b], 'ButtonImage'), 'parents': list(dict.fromkeys(parents))})

out = {
    'meta': {
        'faction': FACTION, 'uk_name': UA_NAME.get(FACTION, FACTION), 'режим': 'Битва',
        'note': ('Усе, що бачить гравець фракції в режимі «Битва»: Фортеця (покращення, прибудови, будівельник) → '
                 'Будівлі (юніти та їхні здібності, покращення) → Герої (вербування, здібності) → Книга сил. '
                 'Кожен рядок трапляється у файлі лише ОДИН раз — там, де його видно вперше; далі стоїть коротке '
                 'посилання «див»: правте рядок там, куди воно веде. Кнопки, спільні для багатьох фракцій '
                 '(стійки, продати, назад…), — у розділі «Загальні кнопки» наприкінці. '
                 'status: вичитано / чернетка AI / переклад Сергія / немає перекладу; джерело — звідки текст зараз '
                 'потрапляє в гру. Правте прямо в uk_ai. \\n — перенос рядка, кількість як в EN; '
                 'гарячі клавіші (&W) латиницею; %d/%s не чіпати.'),
    },
    'Фортеця': fort,
    'Будівлі': buildings,
    'Герої': heroes_sec,
    'Книга сил': book,
    'Загальні кнопки': general,
}
os.makedirs(B008 + 'AoR_UK_WIP/Factions', exist_ok=True)
os.makedirs(os.path.join(HERE, '..', 'stats_out'), exist_ok=True)
dst = os.path.join(HERE, '..', 'stats_out', '') + f'{FACTION}_AoR_UA.json'
json.dump(out, open(dst, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
print(dst)
print(dict(stat))
print('будівель', len(buildings), 'героїв', len(heroes_sec), 'загальних', len(general))
