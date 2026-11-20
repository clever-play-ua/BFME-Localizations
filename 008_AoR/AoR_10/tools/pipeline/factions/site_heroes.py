# exec'd from make_site.py (uses PAGE, TABS, SITE, icon): site/heroes/campaign/index.html + one page per built hero
import unicodedata as _ud
from iniparse import load as _load
HW = r'C:/Users/UserM/Documents/GitHub/BFME-Localizations/008_AoR/AoR_UK_WIP/heroes_web/'
_H = json.load(open(os.path.join(HERE, '..', 'heroes', 'heroes_grouped.json'), encoding='utf-8'))
_STR = {s['var'].lower(): s for s in json.load(open(r'C:/Users/UserM/Documents/GitHub/BFME-Localizations/008_AoR/AoR_10/strings.json', encoding='utf-8'))['strings']}
exec(open(os.path.join(HERE, 'mf_ua.py'), encoding='utf-8').read().split('load_ua()\n')[0], globals())
load_ua()
_D = _load(); _O, _P = _D['Object'], _D['parent']

GROUPS = [  # player-controlled campaign heroes, in a reading order (hobbits first, then the wizard, the Fellowship…)
    ('Hobbits', ['Frodo', 'Sam', 'Merry', 'Pippin', 'Bilbo', 'Fatty Bolger', 'Farmer Maggot', 'Hamfast Gamgee']),
    ('Wizards', ['Gandalf the Grey', 'Gandalf', "Gandalf's Cart", 'Radagast']),
    ('The Fellowship', ['Aragorn', 'Legolas', 'Gimli', 'Boromir', 'Gollum']),
    ('Rohan', ['Théoden', 'Éomer', 'Éowyn', 'Théodred', 'Erkenbrand', 'Elfhelm', 'Gamling', 'Háma', 'Grimbold', 'Dúnhere', "Baldor's Ghost"]),
    ('Gondor', ['Faramir', 'Beregond', 'Prince Imrahil', 'Madril', 'Anborn', 'Damrod', 'Mablung', 'Angbor the Fearless', 'Forlong',
                'Derufin', 'Dervorin', 'Duilin', 'Irolas', 'Lord Duinhir', 'Lord Golasgil', 'Lord Hirluin the Fair', 'Master-at-Arms']),
    ('Rivendell & the Dúnedain', ['Lord Elrond', 'Arwen Undómiel', 'Glorfindel', 'Elladan', 'Elrohir', 'Gildor Inglorion', 'Lindir',
                                  'Halbarad Dúnadan', 'Elegost Dúnadan', 'Lothrandir', 'Toradan', 'Amdir']),
    ('Lothlórien', ['Galadriel', 'Celeborn', 'Haldir', 'Rumil', 'Orophin', 'Idrial']),
    ('Woodland Realm', ['Thranduil', 'Tauriel', 'Feren', 'Grimbeorn']),
    ('Dwarves', ['Thorin Oakenshield', 'Balin', 'Dwalin', 'Fili', 'Kili', 'Óin', 'Glóin', 'Bifur', 'Bofur', 'Bombur', 'Dori', 'Nori', 'Ori',
                 'King Thrór', 'Thráin', 'Lord Dáin II Ironfoot', 'King Dáin', 'Thorin III Stonehelm', 'Agmund']),
    ('Dale & the East', ['Prince Bard II', 'King Brand', 'Legate Vidú']),
    ('Ents', ['Treebeard']),
    ('The Last Alliance', ['Elendil the Tall', 'Isildur', 'Elendur', 'High King Gil-galad', 'Elrond', 'Sinda Spirit']),
    ('Forces of Darkness', ['Sauron', 'Annatar', 'The Necromancer', 'The Witch-king of Angmar', 'Khamûl', 'Ringwraith', 'Queen Saenathra',
                            'Undead Monstrosity', 'Gorbag', 'Wulfgar']),
]
_by = {h['name']: h for h in _H}
_listed = {n for _, ns in GROUPS for n in ns}
_left = [h['name'] for h in _H if h['name'] not in _listed]
if _left:
    GROUPS.append(('Other', _left))
_missing = [n for n in _listed if n not in _by]
assert not _missing, _missing


def hero_slug(name):
    a = _ud.normalize('NFKD', name).encode('ascii', 'ignore').decode().lower()
    return re.sub(r'[^a-z0-9]+', '-', a).strip('-')


def _portrait(h):
    for t in h['campaign_templates'] + h['skirmish_templates']:
        x = t
        for _ in range(10):
            m = re.search(r'^\s*(?:ButtonImage|SelectPortrait)\s*=\s*(\S+)', _O.get(x, ''), re.M)
            if m:
                return m.group(1)
            if x not in _P:
                break
            x = _P[x]
    return None


HD = os.path.join(SITE, 'heroes', 'campaign'); os.makedirs(HD, exist_ok=True)
out, n_all, n_built = [], 0, 0
H_TOT = H_OK = 0  # all lines on the built hero pages / reviewed ones (overview page)
PAGES_H = {}
for g, names in GROUPS:
    out.append(f'<h2 class="grp">{g}</h2><div class="list">')
    for nm in names:
        h = _by[nm]; n_all += 1
        slug = hero_slug(nm)
        lab = (h['names'] or [''])[0].lower()
        ua = UA.get(lab, ('',))[0] if lab else ''
        p = _portrait(h); ic = icon(p, 64) if p else None
        pic = f'<img src="{ic}" alt="">' if ic else '<span class="ph"></span>'
        page, js = HW + slug + '.html', HW + slug + '.json'
        if os.path.exists(page) and os.path.exists(js):
            n_built += 1
            shutil.copy(page, os.path.join(HD, slug + '.html'))
            rs = [r for x in json.load(open(js, encoding='utf-8'))['nodes'] for r in x['rows'] if not r.get('ref') and not r.get('dup')]
            total = len(rs); ok = sum(r['st'] == 'ok' for r in rs); todo = sum(r['st'] == 'missing' for r in rs); draft = total - ok - todo
            H_TOT += total; H_OK += ok
            pc = lambda x: f'{100 * x / max(total, 1):.1f}%'
            PAGES_H['h:' + slug] = json.load(open(HW + slug + '.vars.json', encoding='utf-8'))
            out.append(f'''<a class="fac" id="{slug}" href="{slug}" data-page="h:{slug}">{pic}<span class="nm"><b>{nm}</b><small>{ua}</small></span>
  <span class="st"><span>{total} lines</span><span><i style="background:var(--ok)"></i>{ok} reviewed</span></span>
  <span class="bar"><span style="width:{pc(ok)};background:var(--ok)"></span><span style="width:{pc(draft)};background:var(--draft)"></span></span></a>''')
        else:
            out.append(f'<div class="fac off" id="{slug}">{pic}<span class="nm"><b>{nm}</b><small>{ua}</small></span><span class="soon">Coming soon</span></div>')
    out.append('</div>')

hp = PAGE.replace('Age of the Ring 10 · Skirmish</span>', 'Age of the Ring 10 · Campaign</span>').replace(TABS('f'), TABS('h'))
hp = hp.replace('<p class="lead">Pick a faction.', '<p class="lead">Every hero you control in the campaign, with all of their abilities: '
                'mission by mission, plus their Battle versions.')
hp = re.sub(r'<div class="list">.*?\n  </div>\n  <p class="foot">.*?</p>', lambda m: '\n'.join(out) +
            f'\n  <p class="foot">{n_built} of {n_all} heroes ready. A line shared with a faction page is the same line — it can be edited on either page.</p>',
            hp, flags=re.S)
hp = hp.replace('<title>Age of the Ring — Ukrainian translation</title>', '<title>Campaign heroes — Age of the Ring Ukrainian translation</title>')
# the hero cards have no number column
hp = hp.replace('</style>', '.grp + .list .fac { grid-template-columns: 56px minmax(0, 1fr) auto; }\n'
                '.grp + .list .bar { grid-column: 2 / -1; }\n'
                '.grp + .list .fac { scroll-margin-top: 30vh; }\n'
                '.grp + .list .fac:target { outline: 2px solid var(--accent); outline-offset: 2px; animation: tgt 2.4s ease-out; }\n'
                '@keyframes tgt { 0%, 40% { box-shadow: 0 0 0 6px rgba(143,184,216,.35); } 100% { box-shadow: 0 0 0 0 rgba(143,184,216,0); } }\n'
                '@media (max-width: 640px) { .grp + .list .fac { grid-template-columns: 44px minmax(0, 1fr); } .grp + .list .st, .grp + .list .soon { grid-column: 2 / -1; } }\n</style>')
hp = hp.replace('__PAGES__', json.dumps(PAGES_H, ensure_ascii=False))
open(os.path.join(HD, 'index.html'), 'w', encoding='utf-8').write(hp)
print('campaign heroes:', n_built, 'of', n_all, 'built')
