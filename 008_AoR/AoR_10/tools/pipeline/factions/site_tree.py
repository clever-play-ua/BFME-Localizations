# exec'd from make_site.py (uses SITE, TABS, HERE): site/tree/index.html - a Warcraft-III-style tech tree per faction,
# built from the faction pages' data (Factions/<F>_AoR_UA.html: nodes with EN + UA rows and icons).
import base64 as _b64, json as _json, os as _os, re as _re, unicodedata as _ud

_W = 'C:/Users/UserM/Documents/GitHub/BFME-Localizations/008_AoR/AoR_UK_WIP/Factions/'
_TREE_FACTIONS = [('Isengard', 'Isengard', 'Ізенґард'), ('Men', 'Gondor', 'Ґондор'), ('Rohan', 'Rohan', 'Роган'), ('Mordor', 'Mordor', 'Мордор'), ('Guldur', 'Dol Guldur', 'Дол-Ґулдур'), ('Dwarves', 'Erebor', 'Еребор'), ('Wild', 'Misty Mountains', 'Імлисті гори')]


def _norm(s):
    s = _ud.normalize('NFKD', s or '').encode('ascii', 'ignore').decode().lower()
    s = _re.sub(r'\(&\w\)|&', '', s)
    return _re.sub(r'[^a-z0-9]+', ' ', s).strip()


def _lines(t):
    return [l.strip() for l in (t or '').replace('\\n', '\n').split('\n')]


def _txt(t):
    return '\n'.join(_lines(t)).strip()


def _strip_hk(t):
    return _re.sub(r'\s*\(&\w\)\s*$', '', t or '').replace('&', '').strip()


def _groups(rows):
    """button groups: btn -> {'button': row, 'tooltip': row, 'req': [rows]} in row order"""
    out = {}
    for r in rows:
        if r.get('ref') or not r.get('btn'):
            continue
        g = out.setdefault(r['btn'], {'button': None, 'tooltip': None, 'req': []})
        if r['t'] == 'Button' and not g['button']:
            g['button'] = r
        elif r['t'] == 'Tooltip' and not g['tooltip']:
            g['tooltip'] = r
        elif r['t'] == 'Requirement':
            g['req'].append(r)
    return out


def _reqs(*texts):
    """'Requires …' lines -> list of requirement strings (EN)"""
    out = []
    for t in texts:
        for l in _lines(t):
            m = _re.match(r'(?i)^(?:requires|required:)\s+(.*)$', l)
            if not m:
                continue
            for part in _re.split(r'\s+and\s+|,\s*', m.group(1)):
                part = _re.sub(r'(?i)\s+(?:to be used|upgrade)$', '', part.strip().rstrip('.')).strip()
                part = _re.sub(r'(?i)^the\s+', '', part)
                if part and not _re.fullmatch(r'(?i)(level|rank) \d+', part):
                    out.append(part)
    return out


def _item(iid, kind, name_row, btn_g, icon, extra_req=()):
    b, t = (btn_g or {}).get('button'), (btn_g or {}).get('tooltip')
    en = _strip_hk((name_row or b or {}).get('en', ''))
    ua = _strip_hk((name_row or b or {}).get('uk', '')) or ''
    req_rows = (btn_g or {}).get('req', [])
    return {'id': iid, 'kind': kind, 'en': en, 'ua': ua, 'icon': icon or (b or {}).get('icon'),
            'ten': _txt((t or {}).get('en')), 'tua': _txt((t or {}).get('uk')),
            'ren': [_txt(r.get('en')) for r in req_rows], 'rua': [_txt(r.get('uk')) for r in req_rows],
            'needs': _reqs((t or {}).get('en'), *[r.get('en') for r in req_rows], *extra_req)}


def _faction(key, en, ua):
    s = open(_W + f'{key}_AoR_UA.html', encoding='utf-8').read()
    D = _json.loads(_re.search(r'<script id="data" type="application/json">(.*?)</script>', s, _re.S).group(1))
    ICN = _json.loads(_re.search(r'<script id="icons" type="application/json">(.*?)</script>', s, _re.S).group(1))
    nodes = D['nodes']; by = {n['id']: n for n in nodes}
    kids = lambda n: [by[k] for k in n.get('kids', []) if k in by]
    name_row = lambda n: next((r for r in n['rows'] if r['t'] == 'Name' and not r.get('ref')), None) or \
        {'en': n['name'], 'uk': n.get('ua', '')}
    cols = []
    # ---- fortress: upgrades (+ their chain), expansions
    fort = next(n for n in nodes if n['section'] == 'fortress' and not n.get('parent'))
    fg = _groups(fort['rows'])
    ups = []
    for btn, g in fg.items():
        b = g['button']
        if not b or _re.match(r'(?i)^(build|upgrade fortress)', b['en']) or 'SelectUpgrades' in btn:
            continue
        ups.append(_item(f'{key}:{btn}', 'upgrade', None, g, b.get('icon')))
    has_name = lambda n: any(r['t'] == 'Name' and not r.get('ref') for r in n['rows'])  # some expansions have no name label
    exps = [_item(f'{key}:{x["id"]}', 'expansion', name_row(x) if has_name(x) else None, next(iter(_groups(x['rows']).values()), None), x.get('icon'))
            for x in kids(fort) if x.get('kindLabel') == 'expansion']
    cgrp = next((g for b2, g in fg.items() if g['button'] and _re.match(r'(?i)^build', g['button']['en'])), None)
    cols.append({'id': f'{key}:fort', 'kind': 'fortress', 'en': name_row(fort)['en'], 'ua': name_row(fort).get('uk', ''),
                 'icon': fort.get('icon'), 'tip': _item('', '', None, cgrp, None),
                 'bands': [{'lvl': 0, 'label': 'Upgrades', 'labelUA': 'Покращення', 'items': ups},
                           {'lvl': 0, 'label': 'Expansions', 'labelUA': 'Прибудови', 'items': exps}]})
    # ---- heroes
    heroes = []
    for h in [n for n in nodes if n['section'] == 'heroes']:
        rec = next((r for r in h['rows'] if r['t'] == 'Recruit text' and not r.get('ref')), None)
        it = _item(f'{key}:{h["id"]}', 'hero', name_row(h), None, h.get('icon'))
        if rec:
            it['ten'], it['tua'] = _txt(rec.get('en')), _txt(rec.get('uk'))
            it['needs'] = _reqs(rec.get('en'))
        heroes.append(it)
    cols.append({'id': f'{key}:heroes', 'kind': 'heroes', 'en': 'Heroes', 'ua': 'Герої', 'icon': heroes[0]['icon'] if heroes else None,
                 'tip': None, 'bands': [{'lvl': 0, 'label': 'Recruited at the Fortress', 'labelUA': 'Вербуються у фортеці', 'items': heroes}]})
    # ---- buildings
    for bnode in [n for n in nodes if n['section'] == 'buildings' and not n.get('parent') and 'MordorBase' not in (n.get('nameVar') or '')]:  # skip the dev test base
        g = _groups(bnode['rows'])
        construct = next((x for x in g.values() if x['button'] and _re.match(r'(?i)^build ', x['button']['en'])), None)
        levels, techs = {}, []
        for btn, x in g.items():
            b = x['button']
            if not b or x is construct or _norm(_strip_hk(b['en'])) == _norm(name_row(bnode)['en']):
                continue
            m = _re.match(r'(?i)^upgrade .* to level (\d)', b['en'])
            if m:
                levels[int(m.group(1))] = _item(f'{key}:{btn}', 'level', None, x, b.get('icon'))
            else:
                techs.append(_item(f'{key}:{btn}', 'tech', None, x, b.get('icon')))
        units = []
        for u in kids(bnode):
            ug = _groups(u['rows'])
            ub = next((x for x in ug.values() if x['button'] and _norm(_strip_hk(x['button']['en'])) == _norm(u['name'])), None) \
                or next(iter(ug.values()), None)
            units.append(_item(f'{key}:{u["id"]}', 'unit', name_row(u), ub, u.get('icon')))
        bname = name_row(bnode)['en']

        def place(it, bname=bname):
            for nd in it['needs']:
                m = _re.match(r'(?i)^level (\d) (.+)$', nd)
                if m and _norm(m.group(2)) == _norm(bname):
                    return int(m.group(1))
                m = _re.match(r'(?i)^(.+) level (\d)$', nd)
                if m and _norm(m.group(1)) == _norm(bname):
                    return int(m.group(2))
            return None
        for lv, up in levels.items():  # «Allows training of A and B» puts units on that level
            for u in units:
                if place(u) is None and _norm(u['en']) and (_norm(u['en']) in _norm(up['ten']) or _norm(u['en']).rstrip('s') in _norm(up['ten'])):
                    u['needs'].append(f'Level {lv} {bname}')
        bands = {1: []}
        for it in units + techs:
            bands.setdefault(place(it) or 1, []).append(it)
        out_b = []
        for lv in sorted(set(bands) | set(levels)):
            out_b.append({'lvl': lv, 'up': levels.get(lv), 'items': bands.get(lv, [])})
        cols.append({'id': f'{key}:{bnode["id"]}', 'kind': 'building', 'en': bname, 'ua': name_row(bnode).get('uk', ''),
                     'icon': bnode.get('icon'), 'tip': _item('', '', None, construct, None),
                     'needs': _reqs((construct or {}).get('tooltip', {}) and construct['tooltip'].get('en')), 'bands': out_b})
    # ---- links: requirement text -> element id
    targets = {}
    for c in cols:
        if c['kind'] == 'building':
            targets[_norm(c['en'])] = (c['id'], {b['lvl']: f"{c['id']}:L{b['lvl']}" for b in c['bands']})
        for b in c['bands']:
            for it in b['items']:
                if it['kind'] in ('hero', 'upgrade'):
                    targets.setdefault(_norm(it['en']), (it['id'], {}))
    links = []

    def resolve(nd):
        m = _re.match(r'(?i)^level (\d) (.+)$', nd) or _re.match(r'(?i)^(.+) level (\d)$', nd)
        if m:
            lv, nm = (m.group(1), m.group(2)) if nd.lower().startswith('level') else (m.group(2), m.group(1))
            t = targets.get(_norm(nm))
            return (t[1].get(int(lv)) or t[0]) if t else None
        t = targets.get(_norm(nd))
        if not t:  # loose match: «Wisdom of Curunir» vs «Wisdom of Curunír», «Morgul Spire upgrade»
            t = next((v for k, v in targets.items() if k and (k in _norm(nd) or _norm(nd) in k)), None)
        return t[0] if t else None
    for c in cols:
        own = c['id']
        for nd in c.get('needs', []):
            src = resolve(nd)
            if src and src != own:
                links.append([src, own])
        for b in c['bands']:
            for it in b['items'] + ([b['up']] if b.get('up') else []):
                for nd in it['needs']:
                    src = resolve(nd)
                    if src and not src.startswith(own + ':L') and src != own and src != it['id']:
                        links.append([src, it['id']])
    used = set()
    for c in cols:
        used.add(c.get('icon'))
        for b in c['bands']:
            for it in b['items'] + ([b['up']] if b.get('up') else []):
                used.add(it.get('icon'))
    icons = {k: v for k, v in ICN.items() if k in used}
    return {'key': key, 'en': en, 'ua': ua, 'cols': cols, 'links': [list(x) for x in dict.fromkeys(map(tuple, links))]}, icons


_TD, _TI = [], {}
for _k, _en, _ua in _TREE_FACTIONS:
    if _os.path.exists(_W + f'{_k}_AoR_UA.html'):
        _f, _ic = _faction(_k, _en, _ua)
        _TD.append(_f); _TI.update(_ic)
_tpl = open(_os.path.join(HERE, 'tree_template.html'), encoding='utf-8').read()
_game = _b64.b64encode(open('C:/Users/UserM/Documents/GitHub/BFME-Localizations/008_AoR/AoR_10/tools/lang_Ukrainian/Albertus_Medium.ttf', 'rb').read()).decode()
_caps = _b64.b64encode(open(_os.path.join(HERE, 'fonts', 'cinzel.woff'), 'rb').read()).decode()
_js = lambda o: _json.dumps(o, ensure_ascii=False, separators=(',', ':')).replace('</', '<\\/')
_html = (_tpl.replace('__TABS__', TABS('t')).replace('__FONT_GAME__', _game).replace('__FONT_CAPS__', _caps)
         .replace('__TREE__', _js(_TD)).replace('__ICONS__', _js(_TI)))
_os.makedirs(_os.path.join(SITE, 'tree'), exist_ok=True)
open(_os.path.join(SITE, 'tree', 'index.html'), 'w', encoding='utf-8').write(_html)
print('tree:', {f['key']: (len(f['cols']), len(f['links'])) for f in _TD}, len(_html) // 1024, 'KB')
