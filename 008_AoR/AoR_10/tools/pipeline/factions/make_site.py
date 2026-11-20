"""Build the deployable site: site/index.html (numbered factions) + site/<slug>.html for every faction page that exists."""
import base64, json, os, re, shutil, sys
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
from icons import icon

W = r'C:/Users/UserM/Documents/GitHub/BFME-Localizations/008_AoR/AoR_UK_WIP/Factions/'
SITE = os.path.join(HERE, 'site')
# game order (playertemplate.ini): key, English name, Ukrainian name, file slug
FACTIONS = [('Men', 'Gondor', 'Ґондор', 'gondor'), ('Rohan', 'Rohan', 'Роган', 'rohan'), ('Dwarves', 'Erebor', 'Еребор', 'erebor'),
            ('Elves', 'Lothlorien', 'Лотлоріен', 'lothlorien'), ('Arnor', 'Rivendell', 'Рівендел', 'rivendell'),
            ('Mirkwood', 'Woodland Realm', 'Лісове королівство', 'woodland-realm'), ('Mordor', 'Mordor', 'Мордор', 'mordor'),
            ('Isengard', 'Isengard', 'Ізенґард', 'isengard'), ('Wild', 'Misty Mountains', 'Імлисті гори', 'misty-mountains'),
            ('Guldur', 'Dol Guldur', 'Дол-Ґулдур', 'dol-guldur'), ('Angmar', 'Haradwaith', 'Харадвайт', 'haradwaith')]
STATUS_OK = {'вичитано'}
shutil.rmtree(SITE, ignore_errors=True); os.makedirs(SITE, exist_ok=True)


def rows_of(d):
    out = []
    def walk(n):
        out.extend(r for r in n.get('рядки', []) if 'див' not in r)
        for k in ('прибудови', 'юніти'):
            for c in n.get(k, []):
                walk(c)
    walk(d['Фортеця']); [walk(b) for b in d['Будівлі']]; [walk(h) for h in d['Герої']]; walk(d['Книга сил'])
    return out


# fortress icons of the factions that have no page yet (the built ones take it from their page data)
FORTRESS_ICON = {'Elves': 'BILorienFortress', 'Arnor': 'BIRivendellFortress', 'Mirkwood': 'UIGreenwoodFortress',
                 'Angmar': 'UIHaradFortress'}
cards = []
PAGES_F = {}
FSTAT = []  # per faction, for the overview page (site_overview.py)
for i, (key, en, ua, slug) in enumerate(FACTIONS, 1):
    page, js = W + f'{key}_AoR_UA.html', W + f'{key}_AoR_UA.json'
    if os.path.exists(page) and os.path.exists(js):
        # the faction list now lives at /factions/ (the site root is the overview)
        open(os.path.join(SITE, slug + '.html'), 'w', encoding='utf-8').write(open(page, encoding='utf-8').read().replace(
            'href="index.html" title="All factions"', 'href="/factions/" title="All factions"'))
        d = json.load(open(js, encoding='utf-8'))
        PAGES_F['f:' + key] = json.load(open(W + f'{key}_AoR_UA.vars.json', encoding='utf-8'))
        rs = rows_of(d)
        total = len(rs); ok = sum(r['status'] in STATUS_OK for r in rs); todo = sum(r['status'] == 'немає перекладу' for r in rs)
        draft = total - ok - todo
        ic = icon(d['Фортеця'].get('icon') or '', 96) if d['Фортеця'].get('icon') else None
        _vs = PAGES_F['f:' + key]  # same numbers as the faction list (its JS counts these vars)
        FSTAT.append({'key': key, 'en': en, 'ua': ua, 'slug': slug, 'built': True, 'total': len(_vs), 'ok': sum(st == 'ok' for st in _vs.values()), 'ic': ic})
        pc = lambda x: f'{100 * x / total:.1f}%'
        cards.append(f'''<a class="fac" href="/{slug}" data-page="f:{key}"><span class="num">{i:02d}</span>{f'<img src="{ic}" alt="">' if ic else '<span class="ph"></span>'}
  <span class="nm"><b>{en}</b><small>{ua}</small></span>
  <span class="st"><span>{total} lines</span><span><i style="background:var(--ok)"></i>{ok} reviewed</span></span>
  <span class="bar"><span style="width:{pc(ok)};background:var(--ok)"></span><span style="width:{pc(draft)};background:var(--draft)"></span></span></a>''')
    else:
        ic = icon(FORTRESS_ICON[key], 96) if key in FORTRESS_ICON else None  # shown grey until the page exists
        FSTAT.append({'key': key, 'en': en, 'ua': ua, 'slug': slug, 'built': False, 'total': 0, 'ok': 0, 'ic': ic})
        pic = f'<img class="grey" src="{ic}" alt="">' if ic else '<span class="ph"></span>'
        cards.append(f'''<div class="fac off"><span class="num">{i:02d}</span>{pic}<span class="nm"><b>{en}</b><small>{ua}</small></span><span class="soon">Coming soon</span></div>''')

font = base64.b64encode(open(os.path.join(HERE, 'fonts', 'cinzel.woff'), 'rb').read()).decode()
html = f'''<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Age of the Ring — Ukrainian translation</title>
<style>
@font-face {{ font-family: "UI Caps"; src: url(data:font/woff;base64,{font}) format("woff"); font-weight: 400 900; font-display: swap; }}
:root {{ color-scheme: dark; --bg: #0b131b; --bg-2: #0f1a24; --panel: #122030; --panel-3: #1d3246; --line: #253b50; --line-2: #2f4a63;
  --text: #dfe6ec; --muted: #8d9cab; --faint: #64768a; --accent: #8fb8d8; --accent-2: #5f8fb4;
  --ok: #6fc4a0; --draft: #93a8ec; --missing: #ec8a8a; --mine: #c9a2ea; --caps: "UI Caps", Georgia, serif; --sans: system-ui, -apple-system, "Segoe UI", Roboto, sans-serif; }}
* {{ box-sizing: border-box; }}
html, body {{ margin: 0; }}
body {{ min-height: 100vh; background: radial-gradient(1200px 600px at 70% -10%, #16293b 0%, transparent 60%), linear-gradient(180deg, var(--bg-2), var(--bg)); background-color: var(--bg);
  color: var(--text); font: 15px/1.5 var(--sans); }}
.wrap {{ max-width: 980px; margin: 0 auto; padding: 48px 16px 80px; }}
.kicker {{ display: inline-block; border: 1px solid var(--line-2); background: var(--panel-3); color: var(--accent); font: 700 11px var(--sans); letter-spacing: .16em; text-transform: uppercase; padding: 5px 10px; border-radius: 3px; }}
h1 {{ font: 500 40px/1.1 var(--caps); letter-spacing: .05em; margin: 14px 0 0; }}
.rule {{ width: 110px; height: 3px; background: var(--accent-2); margin: 14px 0 12px; border-radius: 2px; }}
.lead {{ color: var(--muted); max-width: 680px; margin: 0 0 30px; }}
.list {{ display: grid; gap: 10px; }}
.fac {{ display: grid; grid-template-columns: 44px 56px minmax(0, 1fr) auto; align-items: center; gap: 6px 16px; padding: 14px 18px; background: rgba(18,32,48,.94);
  border: 1px solid var(--line); border-radius: 4px; color: inherit; text-decoration: none; }}
a.fac:hover {{ border-color: var(--accent-2); background: rgba(23,40,57,.96); }}
.num {{ font: 500 22px var(--caps); color: var(--accent); }}
.fac img, .fac .ph {{ width: 56px; height: 56px; border-radius: 50%; border: 1px solid var(--line-2); display: block; background: var(--panel-3); }}
.nm b {{ display: block; font: 500 20px var(--caps); letter-spacing: .04em; }}
.nm b .pct {{ display: inline-block; margin-left: 12px; padding: 1px 9px; border-radius: 99px; font: 700 14px/1.5 var(--sans); letter-spacing: 0; vertical-align: 3px; color: var(--draft); background: rgba(147,168,236,.13); }}
.nm b .pct.full {{ color: var(--ok); background: rgba(111,196,160,.15); }}
.nm small {{ color: var(--accent); font-size: 14px; }}
.st {{ display: flex; flex-wrap: wrap; gap: 4px 14px; justify-content: flex-end; font-size: 13px; color: var(--muted); }}
.st i {{ display: inline-block; width: 8px; height: 8px; border-radius: 50%; margin-right: 6px; }}
.bar {{ grid-column: 3 / -1; height: 3px; background: var(--panel-3); border-radius: 2px; overflow: hidden; display: flex; }}
.bar span {{ height: 100%; }}
.off {{ opacity: .5; }}
.fac img.grey {{ filter: grayscale(1); }}
.soon {{ font-size: 12px; letter-spacing: .12em; text-transform: uppercase; color: var(--faint); }}
.foot {{ margin-top: 30px; color: var(--faint); font-size: 13px; }}
.marq {{ position: fixed; top: 0; left: 0; right: 0; height: 0; overflow: hidden; z-index: 20; background: #e3b341; color: #1d1604;
  font: 700 12px/22px var(--sans); letter-spacing: .14em; white-space: nowrap; transition: height .2s; }}
.marq.on {{ height: 22px; }}
.marq span {{ display: inline-block; padding-left: 100%; animation: marq 120s linear infinite; }}
@keyframes marq {{ from {{ transform: translateX(-100%); }} to {{ transform: translateX(0); }} }}
body:has(.marq.on) .wrap {{ padding-top: 70px; }}
a.fac.rvd {{ border-color: rgba(111,196,160,.55); box-shadow: inset 4px 0 0 var(--ok); }}
.tabs {{ display: flex; gap: 6px; margin: 0 0 26px; border-bottom: 1px solid var(--line); overflow-x: auto; scrollbar-width: none; }}
.tabs::-webkit-scrollbar {{ display: none; }}
.tabs a {{ padding: 9px 16px; color: var(--muted); text-decoration: none; font: 600 13px var(--sans); letter-spacing: .1em; text-transform: uppercase; border: 1px solid transparent; border-bottom: 0; border-radius: 4px 4px 0 0; margin-bottom: -1px; white-space: nowrap; }}
.tabs a:hover {{ color: var(--text); }}
.tabs a.on {{ color: var(--accent); background: var(--panel); border-color: var(--line); }}
.grp {{ font: 500 18px var(--caps); letter-spacing: .06em; color: var(--accent); margin: 26px 0 10px; }}
.grp:first-of-type {{ margin-top: 0; }}
@media (max-width: 640px) {{
  .fac {{ grid-template-columns: 34px 44px minmax(0, 1fr); }}
  .fac img, .fac .ph {{ width: 44px; height: 44px; }}
  .st, .soon {{ grid-column: 3 / -1; justify-content: flex-start; }}
  h1 {{ font-size: 24px; }}
  .tabs a {{ padding: 9px 11px; letter-spacing: .06em; }}
}}
</style>
</head>
<body>
<div class="wrap">
  <span class="kicker">Age of the Ring 10 · __KICKER__</span>
  <h1>Ukrainian translation</h1>
  <div class="rule"></div>
  __TABS__
  <p class="lead">__LEAD__ Every button and tooltip is shown the way the game draws it — type the Ukrainian text straight into the tooltip. Your work is kept in your browser; press <b>Export JSON</b> and send the file to the team.</p>
  <div class="list">
{chr(10).join(cards)}
  </div>
  <p class="foot">Shared buttons used by every faction (stances, stop, attack move…) will get their own page.</p>
</div>
<div class="marq" id="marq" aria-live="polite"><span>ALL CHANGES ARE ONLY IN YOUR BROWSER (COOKIES) — DON'T FORGET TO EXPORT JSON</span></div>
<script>
const PAGES = __PAGES__;
(function () {{
  let G = {{ edits: {{}} }};
  try {{ G = JSON.parse(localStorage.getItem('aor-ua-all-v2') || 'null') || G; }} catch (e) {{}}
  const E = G.edits || {{}};
  if (Object.keys(E).length) document.getElementById('marq').classList.add('on');
  document.querySelectorAll('[data-page]').forEach(card => {{
    const vars = PAGES[card.dataset.page]; if (!vars) return;
    let total = 0, ok = 0, ch = 0, dr = 0, todo = 0;
    for (const [v, st] of Object.entries(vars)) {{
      total++;
      const e = E[v], ed = e && e.uk != null && (e.b == null || e.uk !== e.b);
      if (e && e.rv) ok++;
      else if (ed) (e.uk.trim() ? ch++ : todo++);
      else if (st === 'ok') ok++;
      else if (st === 'missing') todo++;
      else dr++;
    }}
    const pc = x => (100 * x / Math.max(total, 1)).toFixed(1) + '%';
    card.querySelector('.st').innerHTML = `<span>${{total}} lines</span><span><i style="background:var(--ok)"></i>${{ok}} reviewed</span>` +
      (ch ? `<span><i style="background:var(--mine)"></i>${{ch}} changed</span>` : '');
    card.querySelector('.bar').innerHTML = `<span style="width:${{pc(ok)}};background:var(--ok)"></span><span style="width:${{pc(ch)}};background:var(--mine)"></span><span style="width:${{pc(dr)}};background:var(--draft)"></span>`;
    card.classList.toggle('rvd', total > 0 && ok === total);
    let pe = card.querySelector('.nm .pct');
    if (!pe) {{ pe = document.createElement('span'); pe.className = 'pct'; card.querySelector('.nm b').appendChild(pe); }}
    pe.textContent = (total ? Math.floor(100 * ok / total) : 0) + '%';
    pe.title = 'reviewed'; pe.classList.toggle('full', total > 0 && ok === total);
  }});
}})();
</script>
</body>
</html>
'''
ON = ' class="on"'
TABS = lambda on: '<nav class="tabs">' + ''.join(f'<a href="{h}"{ON if k == on else ""}>{t}</a>' for k, h, t in
    (('o', '/', 'Overview'), ('f', '/factions/', 'Skirmish factions'), ('h', '/heroes/campaign/', 'Campaign heroes'),
     ('v', '/cinematics/', 'Cinematics'), ('t', '/tree/', 'Tech tree'), ('c', '/changelog/', 'Changelog'))) + '</nav>'
html = (html.replace('__KICKER__', 'Skirmish').replace('__TABS__', TABS('f'))
        .replace('<p class="lead">__LEAD__', '<p class="lead">Pick a faction.'))
os.makedirs(os.path.join(SITE, 'factions'))
fac_html = re.sub(r'\n  <p class="lead">.*?</p>', '', html, count=1, flags=re.S)  # the faction list has no intro text
open(os.path.join(SITE, 'factions', 'index.html'), 'w', encoding='utf-8').write(fac_html.replace('__PAGES__', json.dumps(PAGES_F, ensure_ascii=False)))
PAGE = html  # reused for the campaign-heroes list (before __PAGES__ is filled)
exec(open(os.path.join(HERE, 'site_heroes.py'), encoding='utf-8').read())
exec(open(os.path.join(HERE, 'site_tree.py'), encoding='utf-8').read())
exec(open(os.path.join(HERE, 'site_overview.py'), encoding='utf-8').read())
exec(open(os.path.join(HERE, 'site_cinematics.py'), encoding='utf-8').read())
print({os.path.relpath(os.path.join(r, f), SITE): os.path.getsize(os.path.join(r, f)) // 1024 for r, _, fs in os.walk(SITE) for f in fs})
