"""Campaign hero page: every ability the player sees on one hero — per campaign mission (command sets swapped by the
mission's map / map.ini) and in Battle (other templates with the same name).
usage: python make_hero.py frodo   -> AoR_UK_WIP/heroes_web/<slug>.html + <slug>.json"""
import base64, glob, json, os, re, sys, collections
GAME_FONT = 'C:/Users/UserM/Documents/GitHub/BFME-Localizations/008_AoR/AoR_10/tools/lang_Ukrainian/Albertus_Medium.ttf'  # the in-game font (designer's)
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
from iniparse import load, AOR, DECL
from icons import icon

B008 = r'C:/Users/UserM/Documents/GitHub/BFME-Localizations/008_AoR/'
OUT = B008 + 'AoR_UK_WIP/heroes_web/'
exec(open(os.path.join(HERE, 'mf_ua.py'), encoding='utf-8').read().split('load_ua()\n')[0])  # STR, UA, put, load_ua
load_ua()

# ---- hero list (the campaign-heroes index uses the same order) ----
HEROES = {  # slug -> (name in heroes_grouped.json, name labels of every version of the hero)
    'frodo': ('Frodo', ['OBJECT:RohanFrodo']),
    'sam': ('Sam', ['OBJECT:RohanSam', 'OBJECT:ShireSam']),
    'aragorn': ('Aragorn', ['OBJECT:GondorAragorn']),
}
GROUPED = {h['name']: h for h in json.load(open(os.path.join(HERE, '..', 'heroes', 'heroes_grouped.json'), encoding='utf-8'))}


def _slug(name):  # same as site_heroes.hero_slug
    import unicodedata
    a = unicodedata.normalize('NFKD', name).encode('ascii', 'ignore').decode().lower()
    return re.sub(r'[^a-z0-9]+', '-', a).strip('-')


for _h in GROUPED.values():  # every grouped hero can be built by its slug; explicit entries above win
    HEROES.setdefault(_slug(_h['name']), (_h['name'], _h['names']))

D = load(); O, S, BTN, PARENT = D['Object'], D['CommandSet'], D['CommandButton'], D['parent']
TOK = re.compile(r'[A-Za-z0-9_]{3,}')


def field(t, n):
    m = re.search(r'^\s*' + n + r'\s*=\s*(\S+)', t or '', re.M)
    return m.group(1) if m else None


def chain(o, objs):
    out = [o]
    while out[-1] in PARENT and len(out) < 10:
        out.append(PARENT[out[-1]])
    return ''.join(objs.get(x, O.get(x, '')) for x in out)


def set_buttons(text, btns):
    return [m.group(2) for m in re.finditer(r'^\s*(\d+)\s*=\s*(\S+)', text or '', re.M) if m.group(2) in btns]


# ---- campaign missions: title, map folder, map.ini overrides ----
ini = open(AOR + '/data/ini/linearcampaignexpansion1.ini', encoding='cp1252').read()
MISSIONS = []
for m in re.finditer(r'((?:^[ \t]*;[^\n]*\n)*)[ \t]*Mission\s+(\S+)\s*\r?\n\s*Map\s*=\s*"([^"]+)"', ini, re.M):
    titles = [re.sub(r'[/;\s]+$', '', re.sub(r'^[;\s/]+', '', x)) for x in m.group(1).splitlines()]
    titles = [t for t in titles if t and not re.match(r'MISSION\s+\d+', t, re.I)]
    cn = STR.get('campaignname:' + m.group(2).lower())
    MISSIONS.append((m.group(2), cn['en'].strip() if cn and cn['en'] else (titles[-1].title() if titles else m.group(2)), m.group(3)))
MAPDIR = {os.path.basename(d).lower(): d for d in glob.glob(AOR + '/maps/*')}
_mapini = {}


def map_defs(mapname):
    """CommandSet / CommandButton / Object defined in the mission's map.ini (they override the game's)"""
    if mapname not in _mapini:
        out = {'CommandSet': {}, 'CommandButton': {}, 'Object': {}}
        d = MAPDIR.get(mapname.lower())
        p = d and os.path.join(d, 'map.ini')
        if p and os.path.exists(p):
            t = re.sub(r';.*|//.*', '', open(p, encoding='cp1252', errors='replace').read())
            ms = list(DECL.finditer(t))
            for i, x in enumerate(ms):
                if x.group(1) in out:
                    out[x.group(1)][x.group(2)] = t[x.end():ms[i + 1].start() if i + 1 < len(ms) else len(t)]
        _mapini[mapname] = out
    return _mapini[mapname]


def map_tokens(mapname):
    d = MAPDIR.get(mapname.lower())
    toks = set()
    for f in glob.glob(d + '/*') if d else []:
        if f.lower().endswith(('.map', '.ini')):
            toks |= {x.decode() for x in re.findall(rb'[A-Za-z0-9_]{3,}', open(f, 'rb').read())}
    return toks


# ---- generic labels (stances, stop, …): used by many different heroes ----
users = collections.defaultdict(set)
for o, t in O.items():
    dn = field(chain(o, {}), 'DisplayName')
    if not dn:
        continue
    for st in dict.fromkeys(x for x in TOK.findall(chain(o, {})) if x in S):
        for b in set_buttons(S[st], BTN):
            for f in ('TextLabel', 'DescriptLabel'):
                v = field(BTN[b], f)
                if v:
                    users[v.lower()].add(dn.lower())
GENERIC = {l for l, u in users.items() if len(u) >= 25}  # stances, stop, capture… (Elven Cloak = 13, rock throw = 21 stay)

# ---- where a hero template appears in Battle ----
FACTION_EN = {'FactionMen': 'Gondor', 'FactionRohan': 'Rohan', 'FactionDwarves': 'Erebor', 'FactionElves': 'Lothlórien',
              'FactionArnor': 'Rivendell', 'FactionMirkwood': 'Woodland Realm', 'FactionMordor': 'Mordor',
              'FactionIsengard': 'Isengard', 'FactionWild': 'Misty Mountains', 'FactionGuldur': 'Dol Guldur',
              'FactionAngmar': 'Haradwaith'}
BATTLE = collections.defaultdict(list)  # template -> ['Rivendell', 'Ring hero', 'Shire map', 'Summoned', …]


def _pt_lists(text, label):
    for m in re.finditer(r'^\s*PlayerTemplate\s+(\S+)(.*?)^\s*End\b', text, re.M | re.S):
        name = FACTION_EN.get(m.group(1)) if label is None else label
        if not name:
            continue
        for key, tag in (('BuildableHeroesMP', name), ('BuildableRingHeroesMP', 'Ring hero')):
            for line in re.findall(r'^\s*' + key + r'\s*=([^;\n]*)', m.group(2), re.M):
                for t in line.split():
                    if tag not in BATTLE[t]:
                        BATTLE[t].append(tag)


_pt_lists(open(AOR + '/data/ini/playertemplate.ini', encoding='cp1252', errors='replace').read(), None)
for _d in sorted(glob.glob(AOR + '/maps/map mp alternate *')):
    _p = os.path.join(_d, 'map.ini')
    if os.path.exists(_p):
        _pt_lists(open(_p, encoding='cp1252', errors='replace').read(),
                  os.path.basename(_d)[len('map mp alternate '):].title() + ' map')
for _o in O:
    if 'Summoned' in _o and 'Summoned' not in BATTLE[_o]:
        BATTLE[_o].append('Summoned')

TYPES = {'TextLabel': 'Button', 'DescriptLabel': 'Tooltip', 'LacksPrerequisiteLabel': 'Requirement'}
STATUS = {'вичитано': 'ok', 'чернетка AI': 'draft', 'переклад Сергія': 'comm', 'RotWK UA': 'rotwk', 'немає перекладу': 'missing'}


def build(slug):
    hname, labels = HEROES[slug]
    labels = [x.lower() for x in labels]
    lab = labels[0]
    H = {'label': labels[0], 'campaign': GROUPED[hname]['campaign_templates']}
    mine = [o for o in O if (field(chain(o, {}), 'DisplayName') or '').lower() in labels]
    H['battle'] = [o for o in mine if BATTLE.get(o)]
    nodes, owner = [], {}

    def rowx(var, typ, btn_text=None, btn=None):
        k = var.lower()
        if k not in STR or not re.search(r'[A-Za-z]', STR[k]['en'] or '') or k in GENERIC:
            return None
        en = STR[k]['en'].replace('\n', '\\n')
        if k in owner:
            x = {'v': STR[k]['var'], 't': typ, 'en': en, 'ref': owner[k]}
        else:
            ua, st, src = UA.get(k, ('', 'немає перекладу', ''))
            x = {'v': STR[k]['var'], 't': typ, 'en': en, 'uk': ua, 'st': STATUS.get(st, 'draft')}
            owner[k] = f'n{len(nodes) + 1}'
        if btn_text is not None:
            x['btn'] = btn
            tl = (field(btn_text, 'TextLabel') or '').lower()
            if tl == (field(btn_text, 'DescriptLabel') or '').lower():
                tl = ''
            if tl in STR and STR[tl]['en']:
                x['be'] = STR[tl]['en'].replace('\n', ' ')
            if tl in UA:
                x['bu'] = UA[tl][0]
            img = field(btn_text, 'ButtonImage')
            if img:
                x['icon'] = img
        return x

    def add_node(name, section, kind, buttons, btns, portrait, extra_rows=()):
        rows = [r for r in extra_rows if r]
        for b in buttons:
            for f, typ in TYPES.items():
                v = field(btns[b], f)
                r = v and rowx(v, typ, btns[b], b)
                if r and not any(y['v'] == r['v'] for y in rows):
                    rows.append(r)
        if not any(not r.get('ref') for r in rows) and not rows:
            return None
        nid = f'n{len(nodes) + 1}'
        nodes.append({'id': nid, 'section': section, 'parent': None, 'name': name, 'ua': '', 'icon': portrait,
                      'nameVar': None, 'kindLabel': kind, 'rows': rows, 'kids': []})
        return nid

    tmpl_sets = {t: [x for x in dict.fromkeys(TOK.findall(chain(t, {}))) if x in S] for t in H['campaign']}
    prefixes = sorted({s for v in tmpl_sets.values() for s in v}, key=len)
    portrait = next((field(chain(t, {}), f) for t in H['campaign'] + H['battle']
                     for f in ('ButtonImage', 'SelectPortrait') if field(chain(t, {}), f)), None)

    # campaign: missions where the hero's template is on the map -> its command sets there
    per_mission = []
    for mid, title, mapname in MISSIONS:
        toks = map_tokens(mapname)
        here = [t for t in H['campaign'] if t in toks]
        if not here:
            continue
        md = map_defs(mapname)
        sets = {**S, **md['CommandSet']}
        btns = {**BTN, **md['CommandButton']}
        named = [x for x in sorted(toks) if x in sets and any(x.startswith(p) for p in prefixes)]
        if not named:  # no script swaps: the templates' own sets (map.ini may redefine the object)
            for t in here:  # a map.ini 'Object X' block only patches the game's object (ReplaceModule …)
                ov = field(md['Object'].get(t, ''), 'CommandSet')
                named += [ov] if ov in sets else [x for x in dict.fromkeys(TOK.findall(chain(t, {}))) if x in sets]
        named = sorted(set(named), key=lambda x: (not any(x == p for p in prefixes), x))
        bl = list(dict.fromkeys(b for x in named for b in set_buttons(sets[x], btns)))
        sig = tuple((b, btns[b]) for b in bl)
        per_mission.append((mid, title, sig, btns, named))
        if os.environ.get('DBG'):
            print('  #', mid, title, here, named, bl)
    # every place the player sees the hero: each campaign mission + each Battle version
    places = [{'name': title, 'section': 'campaign', 'kind': 'Campaign mission', 'where': title,
               'buttons': [b for b, _ in sig], 'btns': btns, 'icon': portrait} for mid, title, sig, btns, named in per_mission]
    bgroups = collections.OrderedDict()  # identical buttons -> one Battle version
    for tmpl in H['battle']:
        sets = [x for x in dict.fromkeys(TOK.findall(chain(tmpl, {}))) if x in S]
        bl = tuple(dict.fromkeys(b for x in sets for b in set_buttons(S[x], BTN)))
        g = bgroups.setdefault(bl, {'tmpls': [], 'src': []})
        g['tmpls'].append(tmpl)
        g['src'] += [x for x in BATTLE[tmpl] if x not in g['src']]
    for bl, g in bgroups.items():
        tmpl = g['tmpls'][0]
        title = ' · '.join(g['src'])
        img = next((field(chain(tmpl, {}), f) for f in ('ButtonImage', 'SelectPortrait') if field(chain(tmpl, {}), f)), portrait)
        places.append({'name': title, 'section': 'battle', 'kind': 'Battle: ' + ', '.join(g['tmpls']), 'where': 'Battle: ' + title,
                       'buttons': list(bl), 'btns': BTN, 'icon': img, 'tmpl': tmpl})
    ok = lambda v: v and v.lower() in STR and re.search(r'[A-Za-z]', STR[v.lower()]['en'] or '') and v.lower() not in GENERIC
    selfname = lambda bt: (field(bt, 'TextLabel') or '').lower() == (field(bt, 'DescriptLabel') or '#').lower()  # AoR bug: name = tooltip
    seen = collections.OrderedDict()  # label -> [(place, typ, button text, button)]
    for p in places:
        for b in p['buttons']:
            for f, typ in TYPES.items():
                v = field(p['btns'][b], f)
                if f == 'TextLabel' and selfname(p['btns'][b]):
                    continue
                if ok(v) and p['where'] not in [x[0]['where'] for x in seen.get(v.lower(), [])]:
                    seen.setdefault(v.lower(), []).append((p, typ, p['btns'][b], b))
    shared = {k for k, occ in seen.items() if len(occ) >= 2}
    # ability = the button name (TextLabel); a tooltip belongs to the first ability it is shown with
    ab_of, ab_rows, ab_places = {}, collections.OrderedDict(), collections.OrderedDict()
    for p, b in sorted(((p, b) for p in places for b in p['buttons']), key=lambda pb: selfname(pb[0]['btns'][pb[1]])):
            bt = p['btns'][b]
            tl = field(bt, 'TextLabel')
            tlk = tl.lower() if ok(tl) and not selfname(bt) else None
            for f, typ in TYPES.items():
                v = field(bt, f)
                if not ok(v) or (f == 'TextLabel' and tlk is None and selfname(bt)):
                    continue
                k = v.lower()
                a = ab_of.setdefault(k, tlk or k)
                if k not in ab_rows.setdefault(a, []):
                    ab_rows[a].append(k)
                if p['where'] not in ab_places.setdefault(a, []):
                    ab_places[a].append(p['where'])
    ab_home = {a: ('common' if len(ws) >= 2 else ws[0]) for a, ws in ab_places.items()}

    def ability_rows(home):
        rows = []
        for a, ks in ab_rows.items():
            if ab_home[a] != home:
                continue
            tips = [k for k in ks if seen[k][0][1] == 'Tooltip']
            for k in ks:
                p, typ, bt, b = next((o for o in seen[k] if not selfname(o[2])), seen[k][0])
                r = rowx(STR[k]['var'], typ, bt, b)
                if not r:
                    continue
                r['btn'] = 'ab:' + a
                if k in shared:
                    r['wh'] = [o[0]['where'] for o in seen[k]]
                if len(tips) > 1 and k in tips:
                    r['vw'] = [o[0]['where'] for o in seen[k]]
                rows.append(r)
        return rows

    def place_rows(p):
        return ability_rows(p['where'])

    # 1) abilities used in several missions / Battle: shown once; 2) each place: only its own abilities
    rows = [r for r in [rowx(H['label'], 'Name')] if r] + ability_rows('common')
    nodes.append({'id': 'n1', 'section': 'common', 'parent': None, 'name': 'Common abilities', 'ua': '', 'icon': portrait,
                  'nameVar': None, 'kindLabel': 'Used in several missions or in Battle', 'rows': rows, 'kids': []})
    for p in places:
        own = place_rows(p)
        if p['section'] == 'battle':
            dn = field(chain(p['tmpl'], {}), 'DisplayName')
            nr = rowx(dn, 'Name') if dn and dn.lower() != lab else None
            if nr:
                own.insert(0, nr)
        if own:
            nodes.append({'id': f'n{len(nodes) + 1}', 'section': p['section'], 'parent': None, 'name': p['name'], 'ua': '',
                          'icon': p['icon'], 'nameVar': None, 'kindLabel': p['kind'], 'rows': own, 'kids': []})

    # 100% identical English (hotkey/spacing ignored) is shown once (same rule as the faction pages)
    def _key(en):
        t = re.sub(r'\s*\(&\w\)', '', (en or '').replace('\\n', '\n')).replace('&', '')
        return re.sub(r'\s+', ' ', t).strip().lower()
    _first = {}
    for n in nodes:
        for x in n['rows']:
            k = _key(x['en'])
            if k and not x.get('ref') and k not in _first:
                _first[k] = (n['id'], x['v'])
    for n in nodes:
        for x in n['rows']:
            k = _key(x['en'])
            if k in _first and _first[k] != (n['id'], x['v']) and not x.get('ref'):
                x['dup'] = _first[k][1]
    # a place whose every line is a repeat of a line shown elsewhere has nothing to edit: leave it out
    # (its hidden repeats move next to their master line, so they are still exported together with it)
    home = {x['v']: n for n in nodes for x in n['rows'] if not x.get('ref') and not x.get('dup')}
    for n in [n for n in nodes if not any(not x.get('ref') and not x.get('dup') for x in n['rows'])]:
        for x in n['rows']:
            if x.get('dup') and x['dup'] in home:
                home[x['dup']]['rows'].append(x)
        nodes.remove(n)

    names = {n['icon'] for n in nodes if n['icon']} | {r['icon'] for n in nodes for r in n['rows'] if r.get('icon')} | {'Resource_Icon'}
    ICONS = {nm: v for nm in sorted(names) if (v := icon(nm))}
    en_name = STR[lab]['en']
    ua_name = UA.get(lab, ('',))[0]
    data = {'faction': en_name, 'key': 'hero-' + slug, 'factionUA': ua_name, 'title': en_name, 'icon': portrait,
            'mode': 'Campaign hero', 'back': {'href': '/heroes/campaign/#' + slug, 'text': 'Campaign heroes', 'title': 'All campaign heroes'},
            'sections': [['common', 'Common'], ['campaign', 'Campaign missions'], ['battle', 'Battle']],
            'help1': '<b>Common</b> holds the abilities the hero has in several missions (or also in Battle) — each one is shown once, '
                     'with the list of places it is used in. Under each campaign mission and Battle version you find only what is '
                     'unique to it. Cards show the English tooltip on the left and the Ukrainian one on the right, drawn the way '
                     'the game draws them.',
            'nodes': nodes}
    font = lambda f: base64.b64encode(open(os.path.join(HERE, 'fonts', f), 'rb').read()).decode()
    js = lambda o: json.dumps(o, ensure_ascii=False, separators=(',', ':')).replace('</', '<\\/')
    html = open(os.path.join(HERE, 'template.html'), encoding='utf-8').read()
    html = (html.replace('__TITLE__', f'{en_name} — campaign hero — AoR Ukrainian translation')
            .replace('__FONT_CINZEL__', font('cinzel.woff')).replace('__FONT_GAME__', base64.b64encode(open(GAME_FONT, 'rb').read()).decode()).replace('__DATA__', js(data)).replace('__ICONS__', js(ICONS)))
    os.makedirs(OUT, exist_ok=True)
    open(OUT + slug + '.html', 'w', encoding='utf-8').write(html)
    json.dump({x['v']: x['st'] for n in nodes for x in n['rows'] if not x.get('ref') and not x.get('dup')},
              open(OUT + slug + '.vars.json', 'w', encoding='utf-8'), ensure_ascii=False)
    own = [r for n in nodes for r in n['rows'] if not r.get('ref')]
    summary = {'hero': en_name, 'uk_name': ua_name, 'nodes': [{'name': n['name'], 'section': n['section'], 'missions': n.get('missions'),
               'rows': [{k: r[k] for k in ('v', 't', 'en', 'uk', 'st', 'ref', 'dup') if k in r} for r in n['rows']]} for n in nodes]}
    json.dump(summary, open(OUT + slug + '.json', 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    print(OUT + slug + '.html', len(html) // 1024, 'KB;', len(nodes), 'nodes;', len(own), 'own rows;',
          dict(collections.Counter(r['st'] for r in own)), len(ICONS), 'icons')
    for n in nodes:
        print(' ', n['section'], '|', n['name'], '|', len(n['rows']), 'rows', [r['v'].split(':')[1][:28] + ('*' if r.get('ref') else '') for r in n['rows']])
    return data


if __name__ == '__main__':
    for s in sys.argv[1:] or list(HEROES):
        build(s)
