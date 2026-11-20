# exec'd from make_site.py (uses SITE, TABS, PAGE, FSTAT; n_all, n_built, H_TOT, H_OK from site_heroes.py):
#   site/index.html      overview: current version + downloads, status of every part of the game, latest changes
#   site/changelog/      every version from 008_AoR/CHANGELOG.md (headings «## <version> · <date>»)
import html as _h, json as _json, os as _os, re as _re
from site_status import status as _status

_B008 = 'C:/Users/UserM/Documents/GitHub/BFME-Localizations/008_AoR/'
NEXUS_URL = 'https://www.nexusmods.com/lordoftheringsbattleformiddleearth2/mods/578?tab=files'
GITHUB_URL = 'https://github.com/clever-play-ua/BFME-Localizations/releases/latest'
_AOTR = _json.load(open(_B008 + 'AoR_10_UK/aotr_submod_details.json', encoding='utf-8')).get('aotr_version', '')


# ---------- changelog ----------
def _changelog():
    """[(version, date, body lines)] newest first; for old versions with «### UA / ### EN» only the UA block."""
    out = []
    for sec in _re.split(r'^## ', open(_B008 + 'CHANGELOG.md', encoding='utf-8').read(), flags=_re.M)[1:]:
        head, _, body = sec.partition('\n')
        ver, _, date = (x.strip() for x in head.partition('·'))
        if not _re.match(r'\d', ver):
            continue  # «Наступна версія (у роботі)»
        if '### UA' in body:
            body = body.split('### UA', 1)[1].split('\n### ', 1)[0]
        out.append((ver, date, [l.rstrip() for l in body.strip().split('\n')]))
    return out


def _inline(t):
    t = _h.escape(t)
    t = _re.sub(r'\*\*(.+?)\*\*', r'<b>\1</b>', t)
    return _re.sub(r'(https?://[^\s<]+[^\s<.,;:)])', r'<a href="\1">\1</a>', t)


def _body(lines):
    """Changelog lines -> HTML bullet lists (•, nested ◦), «**Title**» lines -> small headings.
    Old entries mark items with «- » (their other lines are plain paragraphs); since 0.20 every line is an item."""
    dashed = any(_re.match(r'^\s*[-*] ', l) for l in lines)
    out, items = [], []
    def flush():
        if items:
            out.append('<ul class="cl">' + ''.join(items) + '</ul>'); items.clear()
    for l in lines:
        if not l.strip():
            continue
        m = _re.match(r'^\*\*(.+)\*\*$', l.strip())
        if m:
            flush(); out.append(f'<h4>{_h.escape(m[1])}</h4>'); continue
        is_item = bool(_re.match(r'^\s*[-*] ', l)) or not dashed
        text = _inline(_re.sub(r'^\s*[-*] ', '', l).strip())
        if is_item:
            sub = ' class="sub"' if _re.match(r'^\s{2,}[-*] ', l) else ''
            items.append(f'<li{sub}>{text}</li>')
        else:
            flush(); out.append(f'<p>{text}</p>')
    flush()
    return '\n'.join(out)


CL = _changelog()


# ---------- status ----------
S = _status()
_SUBS = _json.load(open(_B008 + 'AoR_10/movie_subtitles/edited.json', encoding='utf-8'))
SUB_VIDEOS = sum(1 for v in _SUBS.values() if v.get('uk'))
SUB_LINES = sum(len(v.get('uk') or []) for v in _SUBS.values())
CAMPAIGNS = [('FotR', 'Кампанія «Братство Персня»'), ('TTT', 'Кампанія «Дві вежі»'), ('RotK', 'Кампанія «Повернення Короля»'),
             ('Angmar', 'Додаткова кампанія «Ангмар»')]


def _state(c):
    hum, tot = c['rev'] + c['ok'], max(c['total'], 1)
    if c['missing'] == c['total']:
        return 'Ще не перекладено (англійською)', 'none'
    if hum == c['total']:
        return 'Перекладено', 'done'
    if c['draft'] > hum:
        return 'Чернетка (машинний переклад), вичитка попереду', 'draft'
    return 'Перекладено, частина рядків — чернетка', 'part'


def _bar(c):
    tot = max(c['total'], 1)
    pc = lambda x: f'{100 * x / tot:.2f}%'
    return (f'<span class="bar"><span style="width:{pc(c["rev"] + c["ok"])};background:var(--ok)"></span>'
            f'<span style="width:{pc(c["draft"])};background:var(--draft)"></span></span>')


# game icons (MappedImage names, cut from the game's texture atlases by icons.py)
ICONS = {'menu': 'uipalantirwhitetower', 'FotR': 'hicampaignfrodo', 'TTT': 'hitheoden', 'RotK': 'hicampaignaragorn',
         'Angmar': 'hiangmarwitchking', 'wotr': 'aptlwmap', 'cah': 'archetype_hero', 'factions': 'uccommon_goodheroes',
         'heroes': 'hicampaigngandalfgrey', 'subs': 'uifrodoredbook'}


def _ic(key, size=64):
    try:
        u = icon(ICONS[key], size)
    except Exception:
        u = None
    return f'<img class="ic" src="{u}" alt="">' if u else '<span class="ic"></span>'


def _row(key, name, c, extra='', state=None, unit='рядків'):
    """-> (exact share, html): rows are shown from the most finished to the least."""
    st, cls = state or _state(c)
    hum = c['rev'] + c['ok']
    share = hum / max(c['total'], 1)
    nums = f'<span class="nums"><b>{hum}</b> / {c["total"]} {unit}</span>'
    inner = (f'{_ic(key)}<span class="rn"><b>{name}</b><small class="{cls}">{st}</small></span>'
             f'<span class="pct {cls}">{int(100 * share)}%</span>{nums}{_bar(c)}')
    if extra:
        return share, f'<details class="row"><summary>{inner}</summary><div class="more">{extra}</div></details>'
    return share, f'<div class="row">{inner}</div>'


import base64 as _b64, io as _io, struct as _struct
import icons as _icons
from PIL import Image as _Image

# mission load screens of the game, in mission order (MappedImage names)
MISSION_IMG = {
    'FotR': ['baraddur', 'longexpectedparty', 'bree', 'weathertop', 'orthanc', 'council', 'redhorn', 'moria', 'khazad',
             'lothlorien', 'amon'],
    'TTT': ['fordsofisen', 'taming', '3hunters', 'durinstower', 'ithilien', 'westfold', 'greycompany', 'osgiliath',
            'helmsdeep', 'isengard'],
    'RotK': ['lotr', 'beacons', 'potd', 'pelargir', 'minastirith_loadscreen1', 'ungol', 'minastirith_loadscreen2',
             'pelennor', 'mirkwood', 'dale', 'blackgate', 'manypartings', 'shire', 'greyhavens'],
    'Angmar': ['campaignangmar_angmar_loadscreen', 'campaignangmar_gundabad_loadscreen', 'campaignangmar_rhudaur_loadscreen',
               'campaignangmar_amonsul_loadscreen', 'wor_north_downs_loadscreen', 'wor_cardolan_loadscreen',
               'campaignangmar_carndum_loadscreen', 'campaignangmar_barrows_loadscreen', 'campaignangmar_fornost_loadscreen',
               'campaignangmar_eye_loadscreen'],
}


def _thumb(name, w=96, h=56):
    """Load-screen picture -> centre-cropped w x h webp data URL (icons.icon() would squash it into a square)."""
    if not name.startswith(('campaign', 'wor_')):
        name = f'campaignwotr_{name}' + ('' if name.startswith('minastirith') else '_loadscreen')
    mi = _icons.MI.get(name.lower())
    if not mi:
        return None
    tex, (l, t, r, b), tw, th = mi
    im = _icons.texture(tex)
    if im is None:
        return None
    sx, sy = (im.width / tw if tw else 1), (im.height / th if th else 1)
    im = im.crop((round(l * sx), round(t * sy), round(r * sx), round(b * sy))).convert('RGB')
    k = max(w / im.width, h / im.height)
    im = im.resize((max(w, round(im.width * k)), max(h, round(im.height * k))), _Image.LANCZOS)
    x, y = (im.width - w) // 2, (im.height - h) // 2
    buf = _io.BytesIO(); im.crop((x, y, x + w, y + h)).save(buf, 'WEBP', quality=80, method=6)
    return 'data:image/webp;base64,' + _b64.b64encode(buf.getvalue()).decode()


def _csf(path):
    """our built lotr.csf -> {label(lower): text}"""
    b, p, out = open(path, 'rb').read(), 24, {}
    while p < len(b):
        _tag, cnt, ln = _struct.unpack_from('<4sII', b, p); p += 12
        lab = b[p:p + ln].decode('latin-1'); p += ln
        for _ in range(cnt):
            t, sl = _struct.unpack_from('<4sI', b, p); p += 8
            out[lab.lower()] = bytes(~c & 255 for c in b[p:p + sl * 2]).decode('utf-16-le'); p += sl * 2
            if t == b'WRTS':
                p += 4 + _struct.unpack_from('<I', b, p)[0]
    return out


_UA = _csf(_B008 + 'AoR_10_UK/lotr.csf')
_EN2LAB = {}
for _s in _json.load(open(_B008 + 'AoR_10/strings.json', encoding='utf-8'))['strings']:
    if _s['var'].lower().startswith(('campaignname:', 'lw:displaynameangmarcampaign')):
        _EN2LAB.setdefault(_s['en'].strip().lower(), _s['var'].lower())


def _missions(name):
    out = []
    imgs = MISSION_IMG.get(name, [])
    for i, (m, c) in enumerate(S['missions:' + name].items()):
        mm = _re.match(r'0*(\d+)_(.*)', m)
        num, en = (mm[1], mm[2]) if mm else ('', m)
        ua = _UA.get(_EN2LAB.get(en.strip().lower(), ''), '')
        ua = ua if ua and ua.strip().lower() != en.strip().lower() else ''
        th = _thumb(imgs[i]) if i < len(imgs) else None
        pic = f'<img class="th" src="{th}" alt="">' if th else '<span class="th"></span>'
        title = (f'<b>{num}. {_h.escape(ua)}</b><small>{_h.escape(en)}</small>' if ua else f'<b>{num}. {_h.escape(en)}</b>')
        hum = c['rev'] + c['ok']
        out.append(f'<div class="mi ms">{pic}<span class="mt">{title}</span><span class="nums"><b>{hum}</b> / {c["total"]}</span>{_bar(c)}</div>')
    return '\n'.join(out)


_fac_done = sum(1 for f in FSTAT if f['built'] and f['ok'] == f['total'])
_fac_cards = []  # two-column grid of faction cards: icon + name, second line = progress
for f in sorted(FSTAT, key=lambda f: -(f['ok'] / f['total'] if f['built'] and f['total'] else -1)):
    pic = f'<img class="fi" src="{f["ic"]}" alt="">' if f.get('ic') else '<span class="fi"></span>'
    if f['built']:
        c = {'rev': f['ok'], 'ok': 0, 'draft': f['total'] - f['ok'], 'missing': 0, 'total': f['total']}
        done = f['ok'] == f['total']
        pct = int(100 * f['ok'] / max(f['total'], 1))
        line = (f'<span class="fp {"done" if done else "part"}">{"Вичитано" if done else "Вичитка триває"} · {pct}%</span>'
                f'<span class="nums"><b>{f["ok"]}</b> / {f["total"]}</span>')
        _fac_cards.append(f'<a class="fc{" done" if done else ""}" href="/{f["slug"]}">{pic}<span class="fn"><b>{f["en"]}</b>'
                          f'<small>{f["ua"]}</small></span><span class="fl">{line}</span>{_bar(c)}</a>')
    else:
        _fac_cards.append(f'<div class="fc off">{pic}<span class="fn"><b>{f["en"]}</b><small>{f["ua"]}</small></span>'
                          f'<span class="fl"><span class="fp">Незабаром</span></span></div>')
# counted in factions / heroes (line totals of 7 built pages would hide the 4 factions that have no page yet)
_fac_built = sum(1 for f in FSTAT if f['built'])
_fac_c = {'rev': _fac_done, 'ok': 0, 'draft': _fac_built - _fac_done, 'missing': len(FSTAT) - _fac_built, 'total': len(FSTAT)}
_hero_done = n_built if H_OK == H_TOT else 0
_hero_c = {'rev': _hero_done, 'ok': 0, 'draft': n_built - _hero_done, 'missing': n_all - n_built, 'total': n_all}
_sub_c = {'rev': SUB_VIDEOS, 'ok': 0, 'draft': 0, 'missing': 0, 'total': SUB_VIDEOS}

# ---------- story videos: site_cinematics.py (/cinematics/) builds the list; the player below is shared ----------


# Player: Vidstack 1.15.6 + hls.js 1.6.16 (both MIT, self-hosted in /assets/vidstack/, loaded on the first click) with its default video
# layout: menus for subtitles (Українська / English / off), audio tracks (appears with a 2nd voice-over), speed,
# fullscreen, keyboard. HLS through our own /assets/hls.min.js (Vidstack would fetch hls.js from a CDN otherwise).
VIDEO_JS = """<script>
(function () {
  var VS = '/assets/vidstack/';
  var ready = null;
  function loadPlayer() {
    if (ready) return ready;
    ['player/styles/default/theme.css', 'player/styles/default/layouts/video.css'].forEach(function (f) {
      var l = document.createElement('link'); l.rel = 'stylesheet'; l.href = VS + f; document.head.appendChild(l);
    });
    ready = import(VS + 'cdn/with-layouts/vidstack.js');
    return ready;
  }
  var UA = {
    'Audio': 'Озвучка', 'Auto': 'Авто', 'Captions': 'Субтитри', 'Chapters': 'Розділи', 'Default': 'Типово',
    'Enter Fullscreen': 'На весь екран', 'Exit Fullscreen': 'Вийти з повноекранного', 'Enter PiP': 'Картинка в картинці',
    'Exit PiP': 'Вийти з «картинки в картинці»', 'Fullscreen': 'Повний екран', 'Mute': 'Вимкнути звук', 'Unmute': 'Увімкнути звук',
    'Normal': 'Звичайна', 'Off': 'Вимкнено', 'Pause': 'Пауза', 'Play': 'Відтворити', 'Playback': 'Відтворення',
    'Quality': 'Якість', 'Seek Backward': 'Назад', 'Seek Forward': 'Уперед', 'Settings': 'Налаштування', 'Speed': 'Швидкість',
    'Volume': 'Гучність', 'Loop': 'Повтор', 'Accessibility': 'Доступність', 'Announcements': 'Оголошення',
    'Keyboard Animations': 'Анімації клавіатури', 'Caption Styles': 'Вигляд субтитрів', 'Font': 'Шрифт', 'Text': 'Текст',
    'Text Background': 'Тло тексту', 'Display Background': 'Тло екрана', 'Family': 'Гарнітура', 'Size': 'Розмір',
    'Color': 'Колір', 'Opacity': 'Непрозорість', 'Shadow': 'Тінь', 'Reset': 'Скинути', 'Boost': 'Підсилення',
    'Closed-Captions On': 'Субтитри ввімкнено', 'Closed-Captions Off': 'Субтитри вимкнено', 'Continue': 'Продовжити',
    'Replay': 'Ще раз', 'LIVE': 'НАЖИВО', 'Download': 'Завантажити', 'AirPlay': 'AirPlay', 'Google Cast': 'Google Cast'
  };
  function setup(box, inner) {
    loadPlayer().then(function () {
      var p = document.createElement('media-player');
      p.setAttribute('title', box.dataset.title || '');
      p.setAttribute('playsinline', '');
      p.setAttribute('crossorigin', '');
      p.setAttribute('load', 'eager');
      p.setAttribute('stream-type', 'on-demand');  // VOD: otherwise Vidstack briefly treats HLS as live and caps the timeline at the buffered end
      p.addEventListener('provider-change', function (e) {
        var pr = e.detail;
        if (pr && pr.type === 'hls') pr.library = '/assets/hls.min.js';
      });
      p.innerHTML = '<media-provider>' +
        (box.dataset.poster ? '<media-poster class="vds-poster" src="' + box.dataset.poster + '"></media-poster>' : '') +
        (box.dataset.uk ? '<track src="' + box.dataset.uk + '" kind="subtitles" label="Українська" srclang="uk" default>' : '') +
        (box.dataset.en ? '<track src="' + box.dataset.en + '" kind="subtitles" label="English" srclang="en">' : '') +
        '</media-provider><media-video-layout></media-video-layout>';
      p.querySelector('media-video-layout').translations = UA;
      inner.appendChild(p);
      p.src = { src: box.dataset.src, type: 'application/x-mpegurl' };
      box._player = p;
    });
  }
  document.querySelectorAll('.vid').forEach(function (box) {
    box.querySelector('.vh').addEventListener('click', function () {
      var open = box.classList.toggle('open');
      var inner = box.querySelector('.vpi');
      if (open && !inner.firstChild) setup(box, inner);
      if (!open && box._player) box._player.pause();
    });
  });
})();
</script>"""


MAIN_CAMPAIGNS = ('FotR', 'TTT', 'RotK')  # their own section, first, in story order
_camp_rows = [_row(k, t, S['camp:' + k], _missions(k))[1] for k, t in CAMPAIGNS if k in MAIN_CAMPAIGNS]
_camp_rows += [
    _row('heroes', 'Герої кампанії', _hero_c, unit='героїв', state=(('Вичитано, ' + f'{H_TOT} рядків', 'done') if _hero_done == n_all else ('Вичитка триває', 'part')))[1],
    _row('subs', 'Субтитри сюжетних відео', _sub_c, state=('Вичитано · ' + f'{SUB_LINES} рядків', 'done'), unit='відео')[1],
]
def _card(key, name, c, unit='рядків'):
    _st, cls = _state(c)
    st = {'done': 'Перекладено', 'part': 'Частково чернетка', 'draft': 'Чернетка', 'none': 'Не перекладено'}[cls]  # short: one line
    hum = c['rev'] + c['ok']
    share = hum / max(c['total'], 1)
    pic = _ic(key, 64).replace('class="ic"', 'class="fi"')
    html = (f'<div class="fc oc">{pic}<span class="fn"><b>{name}</b></span>'
            f'<span class="fl"><span class="fp {cls}">{st} · {int(100 * share)}%</span>'
            f'<span class="nums"><b>{hum}</b> / {c["total"]} {unit}</span></span>{_bar(c)}</div>')
    return share, html


_other = [
    _card('menu', 'Інтерфейс і меню', S['menu']),
    *[_card(k, t.replace('Додаткова кампанія', 'Кампанія'), S['camp:' + k]) for k, t in CAMPAIGNS if k not in MAIN_CAMPAIGNS],
    _card('wotr', 'Режим «Війна Персня»', S['wotr']),
    _card('cah', 'Створення героя', S['cah']),
]
_other = [h for _, h in sorted(_other, key=lambda r: -r[0])]  # most finished first (stable for ties)


def _camp_done():
    return sum(1 for k, _ in CAMPAIGNS if S['camp:' + k]['rev'] + S['camp:' + k]['ok'] >= 0.99 * S['camp:' + k]['total'])


def _tile(key, big, small, label, cls=''):
    return (f'<div class="tile {cls}">{_ic(key, 48)}<span class="tb">{big}<small>{small}</small></span>'
            f'<span class="tl">{label}</span></div>')


_tiles = ''.join([
    _tile('factions', _fac_done, f' / {len(FSTAT)}', 'фракцій (Битва) вичитано', 'done' if _fac_done == len(FSTAT) else ''),
    _tile('heroes', n_built if H_OK == H_TOT else 0, f' / {n_all}', 'героїв кампанії вичитано', 'done' if n_built == n_all and H_OK == H_TOT else ''),
    _tile('FotR', _camp_done(), f' / {len(CAMPAIGNS)}', 'кампаній перекладено', ''),
    _tile('subs', SUB_VIDEOS, f' / {SUB_VIDEOS}', 'сюжетних відео з субтитрами', 'done'),
])

_ver, _date, _ = CL[0]
_zip = _B008 + f'ukrainian-localization_{_ver}.zip'  # the released archive (same file on Nexus and GitHub)
_size = f' · {_os.path.getsize(_zip) / 1e6:.2f} МБ' if _os.path.exists(_zip) else ''
# the same archive is also served by the site itself: /releases/<zip>
_direct = ''
if _os.path.exists(_zip):
    _os.makedirs(_os.path.join(SITE, 'releases'), exist_ok=True)
    shutil.copy(_zip, _os.path.join(SITE, 'releases', _os.path.basename(_zip)))
    _direct = (f'<a class="btn alt" href="/releases/{_os.path.basename(_zip)}" download>'
               f'Завантажити з сайту<small>{_size}</small></a>')
_rel = f'''<section class="rel">
  <div class="rv"><span class="lbl">Актуальна версія</span><b>{_ver}</b><span class="dt">від {_date}{f" · для Age of the Ring {_AOTR}" if _AOTR else ""}</span></div>
  <div class="btns"><a class="btn" href="{NEXUS_URL}" target="_blank" rel="noopener">Завантажити з Nexus Mods<small>{_size}</small></a><a class="btn alt" href="{GITHUB_URL}" target="_blank" rel="noopener">Завантажити з GitHub Releases<small>{_size}</small></a>{_direct}</div>
</section>'''


def _ver_block(v, d, lines):
    return f'<article class="ver"><h3>{v}<small>{d}</small></h3>{_body(lines)}</article>'


_latest = '\n'.join(_ver_block(*x) for x in CL[:3])
_all = '\n'.join(_ver_block(*x) for x in CL)

_style = PAGE.split('<style>', 1)[1].split('</style>', 1)[0]
_extra = '''
.rel { display: flex; flex-wrap: wrap; align-items: center; justify-content: space-between; gap: 14px 24px; padding: 18px 20px; margin: 0 0 30px;
  background: linear-gradient(180deg, rgba(29,50,70,.95), rgba(18,32,48,.95)); border: 1px solid var(--line-2); border-left: 4px solid var(--ok); border-radius: 4px; }
.rel .rv { display: flex; flex-wrap: wrap; align-items: baseline; gap: 4px 12px; }
.rel .lbl { color: var(--muted); font-size: 13px; letter-spacing: .08em; text-transform: uppercase; }
.rel b { font: 500 30px/1 var(--caps); color: var(--text); }
.rel .dt { color: var(--accent); }
.btns { display: flex; flex-wrap: wrap; gap: 10px; }
.btn { display: inline-block; padding: 10px 16px; border-radius: 4px; background: var(--ok); color: #08130e; font: 700 14px var(--sans); text-decoration: none; }
.btn small { font-weight: 500; opacity: .8; }
.btn:hover { filter: brightness(1.08); }
.btn.alt { background: transparent; color: var(--text); border: 1px solid var(--line-2); }
.btn.alt:hover { border-color: var(--accent-2); }
.tiles { display: grid; grid-template-columns: repeat(4, minmax(0, 1fr)); gap: 10px; margin: 0 0 8px; }
.tile { position: relative; padding: 14px 16px; background: rgba(18,32,48,.94); border: 1px solid var(--line); border-radius: 4px; }
.tile .ic { position: absolute; top: 12px; right: 12px; width: 40px; height: 40px; }
.ic { display: block; border-radius: 50%; border: 1px solid var(--line-2); background: var(--panel-3); }
.tile.done { border-color: rgba(111,196,160,.55); box-shadow: inset 0 3px 0 var(--ok); }
.tb { display: block; font: 500 30px/1.1 var(--caps); color: var(--text); }
.tb small { font-size: 18px; color: var(--muted); }
.tl { display: block; margin-top: 4px; color: var(--muted); font-size: 13px; }
.legend { display: flex; flex-wrap: wrap; gap: 4px 16px; color: var(--muted); font-size: 13px; margin: -2px 0 12px; }
.legend i { display: inline-block; width: 9px; height: 9px; border-radius: 50%; margin-right: 6px; }
.rows { display: grid; gap: 8px; }
.row { background: rgba(18,32,48,.94); border: 1px solid var(--line); border-radius: 4px; }
.row > summary, div.row { display: grid; grid-template-columns: 48px minmax(0, 1fr) auto auto; align-items: center; gap: 6px 16px; padding: 12px 16px; }
.row .ic { width: 48px; height: 48px; grid-row: span 2; }
.row > summary { cursor: pointer; list-style: none; }
.row > summary::-webkit-details-marker { display: none; }
.row > summary .rn b::after { content: " ▾"; color: var(--faint); font-size: 12px; }
details[open].row > summary .rn b::after { content: " ▴"; }
.row .bar { grid-column: 2 / -1; }
.rn b { display: block; font-weight: 600; }
.rn small { font-size: 13px; color: var(--muted); }
small.done, .nums.done { color: var(--ok); }
small.draft { color: var(--draft); }
small.none { color: var(--missing); }
.row .pct { font: 700 14px var(--sans); padding: 1px 9px; border-radius: 99px; color: var(--draft); background: rgba(147,168,236,.13); }
.row .pct.done { color: var(--ok); background: rgba(111,196,160,.15); }
.row .pct.none { color: var(--missing); background: rgba(236,138,138,.12); }
.nums { color: var(--muted); font-size: 13px; white-space: nowrap; }
.nums b { color: var(--text); }
.more { padding: 4px 16px 14px; display: grid; gap: 8px; border-top: 1px solid var(--line); }
.mi { display: grid; grid-template-columns: minmax(0, 1fr) auto; gap: 4px 12px; align-items: center; padding-top: 8px; font-size: 14px; color: var(--text); text-decoration: none; }
a.mi:hover span:first-child { color: var(--accent); }
.mi .bar { grid-column: 1 / -1; height: 2px; }
.grp .gs { margin-left: 10px; font: 400 13px var(--sans); color: var(--muted); letter-spacing: 0; }
.fgrid { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 10px; }
.fc { display: grid; grid-template-columns: 56px minmax(0, 1fr); column-gap: 14px; align-items: center;
  padding: 12px 14px; background: rgba(18,32,48,.94); border: 1px solid var(--line); border-radius: 6px; color: inherit; text-decoration: none; }
a.fc:hover { border-color: var(--accent-2); background: rgba(23,40,57,.96); }
.fc.done { border-color: rgba(111,196,160,.5); }
.fc.off { opacity: .55; }
.fc.off .fi { filter: grayscale(1); }
.fi { display: block; width: 56px; height: 56px; border-radius: 50%; border: 1px solid var(--line-2); background: var(--panel-3); grid-row: 1 / span 3; }
.fn b { font: 500 19px/1.2 var(--caps); letter-spacing: .03em; }
.fn small { margin-left: 8px; color: var(--accent); font-size: 14px; }
.fl { display: flex; justify-content: space-between; gap: 10px; font-size: 13px; margin-top: 2px; }
.fp { color: var(--muted); }
.fp.done { color: var(--ok); }
.fp.part { color: var(--draft); }
.fp.draft { color: var(--draft); }
.fp.none { color: var(--missing); }
.oc .fn b { font: 600 16px/1.3 var(--sans); letter-spacing: 0; }
.fc .bar { grid-column: 2; margin-top: 6px; }
@media (max-width: 640px) { .fgrid { grid-template-columns: minmax(0, 1fr); } }
.sub-h { margin: 14px 0 0; padding-top: 12px; border-top: 1px solid var(--line); font-size: 14px; color: var(--accent); }
.vid { border-bottom: 1px solid rgba(37,59,80,.6); }
.vh { display: grid; grid-template-columns: 96px minmax(0, 1fr) auto; gap: 4px 14px; align-items: center; width: 100%; padding: 8px 0;
  background: none; border: 0; color: var(--text); font: inherit; font-size: 14px; text-align: left; cursor: pointer; }
.vh:hover b { color: var(--accent); }
.vh .th { grid-row: auto; }
.play { width: 34px; height: 34px; border-radius: 50%; display: grid; place-items: center; background: var(--panel-3); color: var(--accent); font-size: 13px; }
.vid.open .play { background: var(--ok); color: #08130e; }
.vp { display: grid; grid-template-rows: 0fr; transition: grid-template-rows .35s ease; }
.vid.open .vp { grid-template-rows: 1fr; }
.vpi { overflow: hidden; }
.vpi video { display: block; width: 100%; max-height: 70vh; margin: 6px 0 4px; background: #000; border-radius: 4px; }
.subs { display: flex; flex-wrap: wrap; align-items: center; gap: 6px; padding: 4px 0 12px; font-size: 13px; color: var(--muted); }
.subs .grpb { display: flex; flex-wrap: wrap; align-items: center; gap: 6px; margin-right: 14px; }
.subs button { padding: 4px 10px; border-radius: 99px; border: 1px solid var(--line-2); background: transparent; color: var(--text); font: inherit; cursor: pointer; }
.subs button.on { background: var(--ok); border-color: var(--ok); color: #08130e; }
media-player { display: block; margin: 6px 0 12px; border-radius: 6px; overflow: hidden; --video-brand: #6fc4a0;
  --video-border-radius: 6px; --video-font-family: system-ui, -apple-system, "Segoe UI", Roboto, sans-serif;
  --media-menu-bg: #122030; --media-menu-section-bg: #1d3246; --media-menu-border: 1px solid #2f4a63;
  --media-tooltip-bg-color: #122030; --media-slider-track-fill-bg: #6fc4a0; aspect-ratio: 16 / 10; background: #000; }
media-player [data-media-provider] { height: 100%; }
@font-face { font-family: "AoR Game"; src: url(/assets/fonts/albertus-ua.ttf) format("truetype"); font-display: swap; }
media-player .vds-captions { --media-user-font-family: "AoR Game", Georgia, serif; }
media-player .vds-captions [data-part="cue"] { font-family: "AoR Game", Georgia, serif; }
/* not needed on this site: speed, caption-style menu, picture-in-picture, casting */
media-player .vds-pip-button, media-player .vds-google-cast-button, media-player .vds-airplay-button,
.vds-speed-menu, .vds-accessibility-menu { display: none !important; }  /* settings menus are portalled into <body> */
@media (max-width: 520px) { .vh { grid-template-columns: 72px minmax(0, 1fr) auto; } }
.mi.ms { grid-template-columns: 96px minmax(0, 1fr) auto; column-gap: 14px; }
.mi.ms .bar { grid-column: 2 / -1; }
.th { display: block; width: 96px; height: 56px; border-radius: 3px; border: 1px solid var(--line-2); background: var(--panel-3); object-fit: cover; grid-row: span 2; }
.mt b { display: block; font-weight: 600; }
.mt small { color: var(--muted); font-size: 12px; }
@media (max-width: 520px) { .mi.ms { grid-template-columns: 72px minmax(0, 1fr); } .th { width: 72px; height: 42px; } .mi.ms .nums { grid-column: 2 / -1; } }
.mi.off { opacity: .55; }
.ver { padding: 14px 18px; background: rgba(18,32,48,.94); border: 1px solid var(--line); border-radius: 4px; margin: 0 0 10px; }
.ver h3 { margin: 0 0 6px; font: 500 20px var(--caps); color: var(--accent); }
.ver h3 small { margin-left: 12px; font: 400 13px var(--sans); color: var(--muted); }
.ver h4 { margin: 12px 0 2px; font-size: 14px; color: var(--text); }
.ver p { margin: 3px 0; color: var(--text); }
.ver ul.cl { list-style: none; margin: 4px 0; padding: 0; }
.ver ul.cl li { position: relative; margin: 4px 0; padding-left: 18px; }
.ver ul.cl li::before { content: "•"; position: absolute; left: 3px; color: var(--accent); font-weight: 700; }
.ver ul.cl li.sub { margin-left: 18px; color: var(--muted); }
.ver ul.cl li.sub::before { content: "◦"; }
.ver a { color: var(--accent); }
.morelink { display: inline-block; margin-top: 4px; color: var(--accent); text-decoration: none; font-weight: 600; }
.morelink:hover { text-decoration: underline; }
@media (max-width: 760px) { .tiles { grid-template-columns: repeat(2, minmax(0, 1fr)); } }
@media (max-width: 520px) {
  .row > summary, div.row { grid-template-columns: 40px minmax(0, 1fr) auto; gap: 6px 12px; }
  .row .ic { width: 40px; height: 40px; grid-row: auto; }
  .row .nums { grid-column: 2 / -1; }
  .tile .ic { width: 32px; height: 32px; }
  .rel b { font-size: 26px; }
}
'''


def _page(title, tab, kicker, body):
    return f'''<!DOCTYPE html>
<html lang="uk">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{title}</title>
<style>{_style}{_extra}</style>
</head>
<body>
<div class="wrap">
  <span class="kicker">Age of the Ring 10 · {kicker}</span>
  <h1>Ukrainian translation</h1>
  <div class="rule"></div>
  {TABS(tab)}
{body}
</div>
{VIDEO_JS}
</body>
</html>
'''


_legend = ('<div class="legend"><span><i style="background:var(--ok)"></i>перекладено (у фракціях і героях — вичитано)</span>'
           '<span><i style="background:var(--draft)"></i>чернетка</span><span><i style="background:var(--panel-3)"></i>англійською</span></div>')
_overview = f'''{_rel}
  <h2 class="grp">Загальний статус</h2>
  <div class="tiles">{_tiles}</div>
  <h2 class="grp">Кампанії Age of the Ring</h2>
  {_legend}
  <div class="rows">
{chr(10).join(_camp_rows)}
  </div>
  <h2 class="grp">Фракції · Битва <small class="gs">{_fac_done} з {len(FSTAT)} вичитано</small></h2>
  <div class="fgrid">
{chr(10).join(_fac_cards)}
  </div>
  <h2 class="grp">Інше</h2>
  <div class="fgrid">
{chr(10).join(_other)}
  </div>
  <h2 class="grp">Останні зміни</h2>
{_latest}
  <a class="morelink" href="/changelog/">Усі зміни →</a>'''
open(_os.path.join(SITE, 'index.html'), 'w', encoding='utf-8').write(
    _page('Українізатор Age of the Ring 10 — статус перекладу', 'o', 'Українізатор', _overview))
_os.makedirs(_os.path.join(SITE, 'changelog'), exist_ok=True)
open(_os.path.join(SITE, 'changelog', 'index.html'), 'w', encoding='utf-8').write(
    _page('Журнал змін — Українізатор Age of the Ring 10', 'c', 'Журнал змін', f'{_rel}\n{_all}'))
print('overview:', {k: v for k, v in S.items() if not k.startswith('missions:')}, 'changelog versions', len(CL))
