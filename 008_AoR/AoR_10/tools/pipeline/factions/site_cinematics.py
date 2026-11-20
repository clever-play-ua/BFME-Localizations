# exec'd from make_site.py after site_overview.py (uses SITE, TABS, HERE, shutil and the overview's _page, _B008, _h, _json,
# _os, VIDEO_JS): site/cinematics/index.html - every story video, grouped by campaign, two columns; a click opens the
# card over the full width with the Vidstack player (HLS from 008_AoR/.temp/site_video/<camp>/, tools/build_site_videos.py).
CINE_GROUPS = [('intro', 'Вступ гри', ''), ('fotr', 'Кампанія «Братство Персня»', '«Братство Персня»'),
               ('ttt', 'Кампанія «Дві вежі»', '«Дві вежі»'), ('rotk', 'Кампанія «Повернення Короля»', '«Повернення Короля»')]


def _cine_assets():
    a = _os.path.join(SITE, 'assets')
    _os.makedirs(_os.path.join(a, 'fonts'), exist_ok=True)
    shutil.copy(_os.path.join(HERE, 'vendor', 'hls-1.6.16.min.js'), _os.path.join(a, 'hls.min.js'))  # hls.js 1.6.16
    shutil.copytree(_os.path.join(HERE, 'vendor', 'vidstack-1.15.6'), _os.path.join(a, 'vidstack'), dirs_exist_ok=True)
    shutil.copy(_os.path.join(HERE, '..', '..', 'lang_Ukrainian', 'Albertus_Medium.ttf'), _os.path.join(a, 'fonts', 'albertus-ua.ttf'))


def _cine_cards(camp, short):
    src = _B008 + f'.temp/site_video/{camp}/'
    if not _os.path.exists(src + 'index.json'):
        return [], 0
    dst = _os.path.join(SITE, 'video', camp)
    _os.makedirs(dst, exist_ok=True)
    cards, secs = [], 0
    for i, v in enumerate(_json.load(open(src + 'index.json', encoding='utf-8')), 1):
        base = v['file'][:-4]
        shutil.copytree(src + base, _os.path.join(dst, base), dirs_exist_ok=True)
        for f in (v.get('poster', ''), base + '.uk.vtt', base + '.en.vtt'):
            if f and _os.path.exists(src + f):
                shutil.copy(src + f, _os.path.join(dst, f))
        url = f'/video/{camp}/'
        secs += v['duration']
        mm, ss = divmod(int(round(v['duration'])), 60)
        title = f'{short} · Ролик №{i}' if short else 'Вступний ролик гри'
        lines = f' · {v["uk_lines"]} реплік' if v.get('uk_lines') else ' · без мовлення'
        if 'uk' in (v.get('audio') or []):  # Ukrainian dub (default track; the original stays in the player's audio menu)
            lines += ' · <span class="dub">українська озвучка</span>'
        first = _h.escape(v.get('first_uk') or '')
        if len(first) > 64:
            first = first[:62].rsplit(' ', 1)[0] + '…'
        cards.append(
            f'<div class="vid cv" data-src="{url}{base}/index.m3u8" data-poster="{url}{v.get("poster", "")}" data-title="{_h.escape(title)}"'
            + ''.join(f' data-{l}="{url}{base}.{l}.vtt"' for l in ('uk', 'en') if _os.path.exists(src + f'{base}.{l}.vtt')) + '>'
            f'<button class="vh" type="button"><img class="th" src="{url}{v.get("poster", "")}" alt="" loading="lazy">'
            f'<span class="mt"><b>{_h.escape(title)}</b><small>{mm}:{ss:02d}{lines}</small>'
            + (f'<em>{first}</em>' if first else '') +
            f'</span><span class="play">▶</span></button><div class="vp"><div class="vpi"></div></div></div>')
    return cards, secs


_cine_assets()
_cine_html, _cine_total = [], 0
for _camp, _name, _short in CINE_GROUPS:
    _cards, _secs = _cine_cards(_camp, _short)
    if not _cards:
        continue
    _cine_total += len(_cards)
    _m = int(round(_secs / 60))
    _cine_html.append(f'<h2 class="grp">{_name} <small class="gs">{len(_cards)} {"ролик" if len(_cards) == 1 else "роликів"} · ≈ {_m} хв</small></h2>\n'
                      f'<div class="cgrid">\n' + '\n'.join(_cards) + '\n</div>')
_cine_css = '''
<style>
.cgrid { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 10px; align-items: start; }
.vid.cv { border: 1px solid var(--line); border-radius: 6px; background: rgba(18,32,48,.94); padding: 0 12px; }
.vid.cv:hover { border-color: var(--accent-2); }
.vid.cv.open { border-color: rgba(111,196,160,.55); }  /* stays in its column, grows downwards */
.vid.cv .vh { padding: 10px 0; }
.vid.cv .mt b { font-size: 15px; }
.vid.cv .mt small { display: block; }
.vid.cv .mt em { display: block; margin-top: 2px; color: var(--faint); font-size: 12px; font-style: normal; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.vid.cv .dub { color: var(--ok); font-weight: 600; }
.lead2 { color: var(--muted); margin: 0 0 20px; max-width: 760px; }
@media (max-width: 640px) { .cgrid { grid-template-columns: minmax(0, 1fr); } }
</style>'''
_cine_body = (f'  <p class="lead2">Сюжетні ролики Age of the Ring з українськими субтитрами ({_cine_total}). '
              'Натисніть на ролик, щоб відкрити плеєр; субтитри (українські / English) та озвучку можна змінити в меню плеєра.</p>\n'
              + '\n'.join(_cine_html) + _cine_css)
_os.makedirs(_os.path.join(SITE, 'cinematics'), exist_ok=True)
open(_os.path.join(SITE, 'cinematics', 'index.html'), 'w', encoding='utf-8').write(
    _page('Сюжетні ролики — Українізатор Age of the Ring 10', 'v', 'Сюжетні ролики', _cine_body))
print('cinematics:', _cine_total, 'videos')
