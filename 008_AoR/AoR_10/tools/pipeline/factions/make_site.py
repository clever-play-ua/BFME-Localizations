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
# faction emblems for the /factions/ list (the user's set, 2026-11-20: branding/factions/*.png, 60x60, round, transparent);
# factions without an emblem keep their fortress icon
EMBLEM = {'Men': 'default.png', 'Rohan': 'rohan.png', 'Dwarves': 'erebor.png', 'Elves': 'lorien.png', 'Arnor': 'riv.png',
          'Mordor': 'mordor.png', 'Wild': 'mm.png', 'Guldur': 'guldur.png'}
os.makedirs(os.path.join(SITE, 'assets', 'factions'), exist_ok=True)
for _k, _f in EMBLEM.items():
    shutil.copy(os.path.join(HERE, 'branding', 'factions', _f), os.path.join(SITE, 'assets', 'factions', _f))
# Animated emblem background on faction pages (test on /rohan, 2026-11-20, like war3-localizations /roa/): the emblem's
# white lines become a mask tile (two emblems, staggered), painted in the faction colour and drifting slowly diagonally.
FACTION_BG = {'gondor': ('default.png', '#6E86A8'), 'rohan': ('rohan.png', '#5B7D3A'), 'erebor': ('erebor.png', '#A8813A'),
              'mordor': ('mordor.png', '#9A3324'), 'misty-mountains': ('mm.png', '#7D6B4E'), 'dol-guldur': ('guldur.png', '#6A5488')}


def _emblem_tile(src, dst, tile=180, size=70):
    from PIL import Image as _I
    em = _I.open(src).convert('RGBA').resize((size, size), _I.LANCZOS)
    mask = _I.new('L', em.size, 0)
    mask.putdata([a if min(r, g, b) > 150 else 0 for r, g, b, a in em.getdata()])  # white lines only (no dark fill)
    out = _I.new('RGBA', (tile, tile), (255, 255, 255, 0))
    white = _I.new('RGBA', em.size, (255, 255, 255, 255))
    for x, y in ((tile // 4 - size // 2, tile // 4 - size // 2), (3 * tile // 4 - size // 2, 3 * tile // 4 - size // 2)):
        out.paste(white, (x, y), mask)
    out.save(dst)


def _bg_css(slug, color, tile=180):
    return f"""<style>
/* animated faction emblem in the background of the content pane */
.main {{ position: relative; }}
.main::after {{ content: ""; position: absolute; top: 0; bottom: 0; left: 340px; right: 0; pointer-events: none; z-index: 0;
  background-color: {color}; opacity: .22;
  -webkit-mask-image: url(/assets/factions/{slug}-bg.png); mask-image: url(/assets/factions/{slug}-bg.png);
  -webkit-mask-size: {tile}px {tile}px; mask-size: {tile}px {tile}px; -webkit-mask-repeat: repeat; mask-repeat: repeat;
  animation: emblem-drift 90s linear infinite; }}
.main > * {{ position: relative; z-index: 1; }}
@keyframes emblem-drift {{ from {{ -webkit-mask-position: 0 0; mask-position: 0 0; }} to {{ -webkit-mask-position: {tile}px {tile}px; mask-position: {tile}px {tile}px; }} }}
@media (max-width: 820px) {{ .main::after {{ left: 0; }} }}
@media (prefers-reduced-motion: reduce) {{ .main::after {{ animation: none; }} }}
</style>
"""


cards = []
PAGES_F = {}
FSTAT = []  # per faction, for the overview page (site_overview.py)
for i, (key, en, ua, slug) in enumerate(FACTIONS, 1):
    page, js = W + f'{key}_AoR_UA.html', W + f'{key}_AoR_UA.json'
    if os.path.exists(page) and os.path.exists(js):
        # the faction list now lives at /factions/ (the site root is the overview)
        _html_f = open(page, encoding='utf-8').read().replace('href="index.html" title="All factions"', 'href="/factions/" title="All factions"')
        if slug in FACTION_BG:
            _em, _col = FACTION_BG[slug]
            os.makedirs(os.path.join(SITE, 'assets', 'factions'), exist_ok=True)
            _emblem_tile(os.path.join(HERE, 'branding', 'factions', _em), os.path.join(SITE, 'assets', 'factions', slug + '-bg.png'))
            _html_f = _html_f.replace('</head>', _bg_css(slug, _col) + '</head>', 1)
        open(os.path.join(SITE, slug + '.html'), 'w', encoding='utf-8').write(_html_f)
        d = json.load(open(js, encoding='utf-8'))
        PAGES_F['f:' + key] = json.load(open(W + f'{key}_AoR_UA.vars.json', encoding='utf-8'))
        rs = rows_of(d)
        total = len(rs); ok = sum(r['status'] in STATUS_OK for r in rs); todo = sum(r['status'] == 'немає перекладу' for r in rs)
        draft = total - ok - todo
        ic = icon(d['Фортеця'].get('icon') or '', 96) if d['Фортеця'].get('icon') else None
        _vs = PAGES_F['f:' + key]  # same numbers as the faction list (its JS counts these vars)
        FSTAT.append({'key': key, 'en': en, 'ua': ua, 'slug': slug, 'built': True, 'total': len(_vs), 'ok': sum(st == 'ok' for st in _vs.values()), 'ic': ic})
        pc = lambda x: f'{100 * x / total:.1f}%'
        pic = (f'<img class="emb" src="/assets/factions/{EMBLEM[key]}" alt="" width="56" height="56">' if key in EMBLEM else
               f'<img src="{ic}" alt="">' if ic else '<span class="ph"></span>')
        cards.append(f'''<a class="fac" href="/{slug}" data-page="f:{key}"><span class="num">{i:02d}</span>{pic}
  <span class="nm"><b>{en}</b><small>{ua}</small></span>
  <span class="st"><span>{total} lines</span><span><i style="background:var(--ok)"></i>{ok} reviewed</span></span>
  <span class="bar"><span style="width:{pc(ok)};background:var(--ok)"></span><span style="width:{pc(draft)};background:var(--draft)"></span></span></a>''')
    else:
        ic = icon(FORTRESS_ICON[key], 96) if key in FORTRESS_ICON else None  # shown grey until the page exists
        FSTAT.append({'key': key, 'en': en, 'ua': ua, 'slug': slug, 'built': False, 'total': 0, 'ok': 0, 'ic': ic})
        pic = (f'<img class="emb grey" src="/assets/factions/{EMBLEM[key]}" alt="" width="56" height="56">' if key in EMBLEM else
               f'<img class="grey" src="{ic}" alt="">' if ic else '<span class="ph"></span>')
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
.fac img.emb {{ border: 0; background: none; border-radius: 0; image-rendering: auto; }}
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
exec(open(os.path.join(HERE, 'site_review_rotk.py'), encoding='utf-8').read())

# ---------- 404 page, link-preview image, favicon ----------
# Without 404.html Cloudflare Pages answers every unknown URL with the home page and status 200 ("soft 404" for search
# engines; the player once received HTML instead of a missing video file). With it, unknown URLs get this page + 404.
from PIL import Image as _Img
_body404 = """  <section class="rel" style="border-left-color: var(--missing)">
    <div class="rv"><span class="lbl">Помилка 404</span><b>Сторінку не знайдено</b></div>
  </section>
  <p class="lead2" style="color: var(--muted)">Можливо, адреса змінилася або сторінку ще не створено. Ось куди можна перейти:</p>
  <div class="fgrid">
    <a class="fc" href="/"><span class="fi"></span><span class="fn"><b>Головна</b></span><span class="fl"><span class="fp">статус перекладу й завантаження</span></span></a>
    <a class="fc" href="/factions/"><span class="fi"></span><span class="fn"><b>Фракції · Битва</b></span><span class="fl"><span class="fp">кнопки й підказки фракцій</span></span></a>
    <a class="fc" href="/heroes/campaign/"><span class="fi"></span><span class="fn"><b>Герої кампанії</b></span><span class="fl"><span class="fp">здібності героїв</span></span></a>
    <a class="fc" href="/cinematics/"><span class="fi"></span><span class="fn"><b>Сюжетні ролики</b></span><span class="fl"><span class="fp">з українськими субтитрами</span></span></a>
  </div>"""
open(os.path.join(SITE, '404.html'), 'w', encoding='utf-8').write(
    _page('Сторінку не знайдено — Українізатор Age of the Ring 10', '', 'Помилка 404', _body404))
_og = _Img.open(os.path.join(HERE, 'branding', 'og-source.jpg')).convert('RGB')  # user's banner «Епоха Персня»
_h = round(_og.width * 630 / 1200)
_top = max(0, (_og.height - _h) // 2)
_og.crop((0, _top, _og.width, _top + _h)).resize((1200, 630), _Img.LANCZOS).save(os.path.join(SITE, 'og.jpg'), quality=86, optimize=True)
shutil.copy(os.path.join(HERE, 'branding', 'favicon.ico'), os.path.join(SITE, 'favicon.ico'))  # BFME1 HD Edition icon, 32x32
_Img.open(os.path.join(HERE, 'branding', 'favicon.ico')).convert('RGBA').save(os.path.join(SITE, 'favicon-32.png'))

# Site analytics (Plausible, the user's own instance, 2026-11-20): into <head> of every page of the site
ANALYTICS = '''<!-- Privacy-friendly analytics by Plausible -->
<script async src="https://pls.khomenko.ovh/js/pa-i7ONMZqy009UM-TzLup_q.js"></script>
<script>
  window.plausible=window.plausible||function(){(plausible.q=plausible.q||[]).push(arguments)},plausible.init=plausible.init||function(i){plausible.o=i||{}};
  plausible.init()
</script>
'''
_n_an = 0
for _r, _d, _fs in os.walk(SITE):
    for _f in _fs:
        if _f.endswith('.html'):
            _p = os.path.join(_r, _f)
            _t = open(_p, encoding='utf-8').read()
            _new = _t
            if 'pls.khomenko.ovh' not in _new and '</head>' in _new:
                _new = _new.replace('</head>', ANALYTICS + '</head>', 1); _n_an += 1
            if 'rel="icon"' not in _new:
                _new = _new.replace('</head>', '<link rel="icon" href="/favicon.ico" sizes="32x32">\n'
                                    '<link rel="icon" type="image/png" href="/favicon-32.png">\n</head>', 1)
            if '<main' not in _new and 'role="main"' not in _new:  # the page's top container is its main content
                _new = re.sub(r'<div class="(wrap|app)"', r'<div class="\1" role="main"', _new, count=1)
            if _new != _t:
                open(_p, 'w', encoding='utf-8').write(_new)
print('analytics added to', _n_an, 'pages')

# ---------- search engines & AI agents: meta description / canonical / Open Graph, sitemap.xml, robots.txt, llms.txt ----------
import datetime as _dt, html as _html
SITE_URL = 'https://aor-uk-localization.pages.dev'
_FAC_UA = {slug: (en, ua) for _k, en, ua, slug in FACTIONS}
_TODAY = _dt.date.today().isoformat()


def _clean_url(rel):
    rel = rel.replace(os.sep, '/')
    if rel == 'index.html':
        return '/'
    if rel.endswith('/index.html'):
        return '/' + rel[:-len('index.html')]
    return '/' + rel[:-len('.html')]


def _describe(url, title):
    if url == '/':
        return ('Українізатор Age of the Ring 10 (мод для BFME2: The Rise of the Witch-king): статус перекладу кампаній, '
                'фракцій і героїв, завантаження актуальної версії з Nexus Mods, GitHub і з сайту.')
    if url == '/factions/':
        return 'Фракції режиму «Битва» Age of the Ring 10: стан українського перекладу та вичитки кожної фракції.'
    if url == '/heroes/campaign/':
        return 'Герої кампанії Age of the Ring 10: усі здібності кожного героя українською, місія за місією.'
    if url == '/tree/':
        return 'Дерево технологій фракцій Age of the Ring 10 українською: споруди, покращення, герої та вимоги.'
    if url == '/cinematics/':
        return ('Сюжетні ролики Age of the Ring 10 з українськими субтитрами та українською озвучкою — '
                '«Братство Персня», «Дві вежі», «Повернення Короля». Дивитися онлайн.')
    if url == '/changelog/':
        return 'Журнал змін українізатора Age of the Ring 10: що нового в кожній версії.'
    if url.lstrip('/') in _FAC_UA:
        en, ua = _FAC_UA[url.lstrip('/')]
        return (f'{en} ({ua}) — усі кнопки й підказки фракції Age of the Ring 10 українською: фортеця, споруди, загони, '
                'герої та Книга сил.')
    if url.startswith('/heroes/campaign/'):
        return f'{title.split(" — ")[0]} — здібності героя кампанії Age of the Ring 10 українською.'
    return f'{title} — українізатор Age of the Ring 10.'


_pages = []
for _r, _d, _fs in os.walk(SITE):
    for _f in sorted(_fs):
        if not _f.endswith('.html'):
            continue
        _p = os.path.join(_r, _f)
        _url = _clean_url(os.path.relpath(_p, SITE))
        _t = open(_p, encoding='utf-8').read()
        _m = re.search(r'<title>(.*?)</title>', _t, re.S)
        _title = _html.unescape(_m.group(1).strip()) if _m else 'Age of the Ring — Ukrainian translation'
        _desc = _describe(_url, _title)
        _head = []
        if 'name="description"' not in _t:
            _head.append(f'<meta name="description" content="{_html.escape(_desc)}">')
        if 'rel="canonical"' not in _t:
            _head.append(f'<link rel="canonical" href="{SITE_URL}{_url}">')
        if 'name="robots" content="noindex"' in _t:  # e.g. /review/rotk/: not for search engines
            continue
        if _f == '404.html' and _r == SITE:
            if 'name="robots"' not in _t:
                open(_p, 'w', encoding='utf-8').write(_t.replace('</head>', '<meta name="robots" content="noindex">\n</head>', 1))
            continue
        if 'property="og:image"' not in _t:
            _head += [f'<meta property="og:image" content="{SITE_URL}/og.jpg">', '<meta property="og:image:width" content="1200">',
                      '<meta property="og:image:height" content="630">', '<meta property="og:image:alt" content="Епоха Персня — українізатор">']
        if 'property="og:title"' not in _t:
            _head += [f'<meta property="og:type" content="website">', f'<meta property="og:site_name" content="Українізатор Age of the Ring">',
                      f'<meta property="og:locale" content="uk_UA">', f'<meta property="og:title" content="{_html.escape(_title)}">',
                      f'<meta property="og:description" content="{_html.escape(_desc)}">', f'<meta property="og:url" content="{SITE_URL}{_url}">',
                      '<meta name="twitter:card" content="summary_large_image">']
        if _head and '</head>' in _t:
            open(_p, 'w', encoding='utf-8').write(_t.replace('</head>', '\n'.join(_head) + '\n</head>', 1))
        _prio = '1.0' if _url == '/' else '0.8' if _url in ('/cinematics/', '/factions/', '/heroes/campaign/', '/changelog/', '/tree/') else '0.6'
        _pages.append((_url, _prio))
_pages.sort(key=lambda x: (-float(x[1]), x[0]))
with open(os.path.join(SITE, 'sitemap.xml'), 'w', encoding='utf-8', newline='\n') as _o:
    _o.write('<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n')
    for _url, _prio in _pages:
        _o.write(f'  <url><loc>{SITE_URL}{_url}</loc><lastmod>{_TODAY}</lastmod><changefreq>weekly</changefreq><priority>{_prio}</priority></url>\n')
    _o.write('</urlset>\n')
with open(os.path.join(SITE, 'robots.txt'), 'w', encoding='utf-8', newline='\n') as _o:
    _o.write('# Українізатор Age of the Ring 10 — all pages are open to search engines and AI agents.\n'
             '# /video/ (HLS fragments of the cinematics) and /assets/ (player libraries, fonts) are not pages.\n'
             'User-agent: *\nAllow: /\nDisallow: /video/\nDisallow: /assets/\n\n'
             f'Sitemap: {SITE_URL}/sitemap.xml\n')
_ver = re.search(r'^## (\d[\d.]*) · (.+)$', open('C:/Users/UserM/Documents/GitHub/BFME-Localizations/008_AoR/CHANGELOG.md', encoding='utf-8').read(), re.M)
_llms = f'''# Українізатор Age of the Ring 10

> Українська локалізація Age of the Ring 10 — безкоштовного мода для The Lord of the Rings: The Battle for Middle-earth II —
> The Rise of the Witch-king. Сайт показує статус перекладу, дає завантажити українізатор і переглянути сюжетні ролики
> з українськими субтитрами та озвучкою. Ukrainian translation of the Age of the Ring 10 mod (BFME2: RotWK).

Актуальна версія: {_ver.group(1) if _ver else ''} ({_ver.group(2) if _ver else ''}), для Age of the Ring {_AOTR}.

## Завантаження
- [Nexus Mods]({NEXUS_URL}): українізатор, архів для лаунчера AoR
- [GitHub Releases]({GITHUB_URL}): той самий архів
- [З сайту]({SITE_URL}/releases/ukrainian-localization_{_ver.group(1) if _ver else ''}.zip): той самий архів

## Сторінки
- [Головна]({SITE_URL}/): статус перекладу кампаній, фракцій, героїв, інтерфейсу
- [Фракції · Битва]({SITE_URL}/factions/): усі кнопки й підказки кожної фракції українською
- [Герої кампанії]({SITE_URL}/heroes/campaign/): здібності 106 героїв кампанії
- [Сюжетні ролики]({SITE_URL}/cinematics/): 47 роликів з українськими субтитрами, частина — з українською озвучкою
- [Дерево технологій]({SITE_URL}/tree/): споруди, покращення й вимоги фракцій
- [Журнал змін]({SITE_URL}/changelog/): що нового в кожній версії

## Для агентів
- Мова сайту: українська (назви вкладок англійською). Карта сайту: {SITE_URL}/sitemap.xml
- Терміни перекладу узгоджені з українськими перекладами BFME2 / RotWK (Ґендальф, Араґорн, Беґ-Енд, Мордор, Ізенґард).
'''
for _name in ('llms.txt', 'agents.txt'):  # llms.txt = the proposed standard AI agents look for; agents.txt = the same text
    open(os.path.join(SITE, _name), 'w', encoding='utf-8', newline='\n').write(_llms)
print('seo:', len(_pages), 'pages in sitemap.xml; robots.txt, llms.txt, agents.txt')
print({os.path.relpath(os.path.join(r, f), SITE): os.path.getsize(os.path.join(r, f)) // 1024 for r, _, fs in os.walk(SITE) for f in fs})
