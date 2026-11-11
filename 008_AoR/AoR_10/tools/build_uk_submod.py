"""
Build the Ukrainian AotR 10.0 submod into 008_AoR/AoR_10_UK, laid out like the RU 9.3.1 submod (008_AoR/ru),
minus the audio:

    lotr.csf                       all strings: UK where translated, English otherwise
    _rotwk_/lang/Ukrainian.big     the files from tools/lang_Ukrainian: stock RotWK English.big content (English text, no
                                   localized logos) + Albertus_Medium.ttf (the designer's Ukrainian font, family
                                   "Albertus Medium"), registered in language.ini (LocalFontFile + UnicodeFontName),
                                   both FontSubstitution blocks on that one font
    _rotwk_/UkrainianSplash.jpg    copy of the RU splash (AoR logo only, no Russian text)
    data/movies/CS01.vp6           tools/nointro (0.17 s black stub + silent data/audio/speech/CS01.mp3), or
                                   everything under tools/media, same relative path (intro with Ukrainian subtitles)
    _rotwk_/EnglishSplash.jpg,     from tools/branding/splash.png / loading.png when present (see BRANDING_IMAGES)
    art/compiledtextures/in/installload.jpg
    aotr_submod_details.json       manifest with sha256 checksums, same format as the RU one

plus 008_AoR/<slug>_<VERSION>.zip (e.g. ukrainian-localization_0.10.zip, the launcher's own name) with the same files at the zip root, for the launcher's Mods > Install from Zip.

Text sources:
    ../strings.json                       every label of AoR 10.0 (data/lotr.str + all maps/*/map.str), English
    ../menu_strings.json                  menu/interface labels: uk wins, then uk_ai
    ../../AoR_UK_WIP/Menu_tooltips_strings.json  menu/interface tooltips (ToolTip:/TOOLTIP:), same format
    ../../AoR_UK_WIP/heroes|Skirmish|RoTK/*.json  per-hero / per-mission editor files: uk, else uk_ai; win over the xlsx
    ../RotK_campaign_strings.xlsx         sheets.UK_SHEETS: UK column wins, then UK AI; literal \\n in cells = line break
    extra_uk.json                         labels AoR's own files lack, e.g. movie subtitles DIALOGEVENT:<sound>Subtitle

Run:  python build_uk_submod.py      (needs openpyxl)
"""
import collections, hashlib, json, os, shutil, struct, sys, zipfile

HERE = os.path.dirname(os.path.abspath(__file__))
AOR10 = os.path.dirname(HERE)
REPO = os.path.dirname(os.path.dirname(AOR10))
OUT = os.path.join(os.path.dirname(AOR10), 'AoR_10_UK')
RU = os.path.join(os.path.dirname(AOR10), '.temp', 'ru')  # RU 9.3.1 reference (not in git), only RU_AotR_9.3.1_all.json

sys.path.insert(0, os.path.join(REPO, '000_TOOLKIT', 'BFME-loc-toolkit', 'scripts'))
from csf_tools import build_csf, read_csf  # noqa: E402
from openpyxl import load_workbook  # noqa: E402
from fontTools.ttLib import TTFont  # noqa: E402
from sheets import ALL_SHEET, MENU_JSON, UK_SHEETS, XLSX  # noqa: E402

FONT = os.path.join(HERE, 'lang_Ukrainian', 'Albertus_Medium.ttf')  # the designer's Ukrainian font
MEDIA = os.path.join(HERE, 'media')  # files shipped as-is at the same relative path (movies, ...)
TOOLTIPS_JSON = os.path.join(os.path.dirname(AOR10), 'AoR_UK_WIP', 'Menu_tooltips_strings.json')  # same format as menu
WIP = os.path.join(os.path.dirname(AOR10), 'AoR_UK_WIP')
WIP_DIRS = ('heroes', 'Skirmish', 'RoTK')  # editor files that override the xlsx (see load_wip)
SERHII_JSON = os.path.join(WIP, 'Serhii_strings.json')  # community translation, field «sergii»
FACTIONS = os.path.join(WIP, 'Factions')  # <Faction>_AI_drafts.json from the faction pages (see load_uk)
SHIP_MEDIA = False  # the subtitled intro (media/data/movies/CS01.vp6) is on hold
# "No intro": tools/nointro/<path> ships as <path> - CS01.vp6 = first 4 (black) frames of the original intro, audio
# chunks dropped (~0.17 s; ffmpeg's EA demuxer cannot open fewer than 4); CS01.mp3 = 0.13 s silence (the intro's
# voice/music is DialogEvent CS01). Overridden by media/ when SHIP_MEDIA is on.
NO_INTRO = os.path.join(HERE, 'nointro')
SHIP_NO_INTRO = True
# Custom start-up images, used only when the PNG exists (converted to the stock JPEG size):
#   branding/splash.png   -> _rotwk_/EnglishSplash.jpg              800x600, shown while the exe starts (rotwk\)
#   branding/loading.png  -> art/compiledtextures/in/installload.jpg 1920x1440, MappedImage ShellMapLowLOD
#                            (the launcher puts one of its installload_*.jpg there; the mod copy wins at launch)
BRANDING = os.path.join(HERE, 'branding')
BRANDING_IMAGES = [('splash.png', '_rotwk_/EnglishSplash.jpg', (800, 600)),
                   ('loading.png', 'art/compiledtextures/in/installload.jpg', (1920, 1440))]
VERSION = '0.14'  # also names the zip: ukrainian-localization_0.14.zip
# 'shadow': stay English, override the stock albertusmt.otf with the designer font (no registry needed)
# 'slot':   own rotwk\lang\Ukrainian.big language slot (needs registry Language=ukrainian)
MODE = 'shadow'
# shadow mode: (source font, family it pretends to be, PostScript name, file name it shadows in rotwk\Data1.big,
#               unitsPerEm override or None)
SHADOW_FONTS = [
    (FONT, 'Albertus MT', 'AlbertusMT', 'albertusmt.otf', None),  # all body text
    # Decorative titles: AoR menus (MenuExport, Palantir, SpellStore, StrategicPalantir APTs) name "Omnia LT Std"
    # directly; SachaWynter (audio subtitles) is substituted to it too. Omnia has no Cyrillic -> Aniron (Pete Klassen,
    # freeware, Cyrillic incl. ҐЄІЇ). Aniron's capitals are 1320 units on a 1000 em vs Omnia's 0.59 em, so the em
    # is enlarged to 2240 (same cap height as Omnia), then -20% for slightly bigger titles: 1867. Digits 0-9 are the
    # stock Omnia ones (make_aniron_omnia_digits.py); all other outlines untouched.
    (os.path.join(HERE, 'fonts', 'Aniron_OmniaDigits.ttf'), 'Omnia LT Std', 'OmniaLTStd', 'omnialtstd.ttf', 1867),
]
# characters editors type that the font lacks -> a look-alike the font has
GLYPH_FALLBACK = {'ʼ': '’'}  # ʼ modifier-letter apostrophe -> ’


def fit_to_font(uk):
    """Swap known look-alikes and stop on any other character the font cannot draw."""
    cmap = TTFont(FONT).getBestCmap()
    bad = collections.defaultdict(list)
    for k, text in uk.items():
        for a, b in GLYPH_FALLBACK.items():
            text = text.replace(a, b)
        uk[k] = text
        for ch in set(text) - {'\n'}:
            if ord(ch) not in cmap:
                bad[ch].append(k)
    if bad:
        sys.exit('characters missing in ' + os.path.basename(FONT) + ': ' +
                 '; '.join(f'{ch!r} U+{ord(ch):04X} in {ks[:3]}' for ch, ks in bad.items()))


def load_menu(uk):
    """menu_strings.json + Menu_tooltips_strings.json: uk, else uk_ai (not stripped: menu texts may carry meaningful
    spaces)."""
    for path in (MENU_JSON, TOOLTIPS_JSON):
        if not os.path.exists(path):
            continue
        for s in json.load(open(path, encoding='utf-8'))['strings']:
            text = s.get('uk') or s.get('uk_ai')
            if text and s['var'].lower() not in uk:
                uk[s['var'].lower()] = text.replace('\\n', '\n')


def load_wip(uk):
    """Per-hero and per-mission editor files (newest edits, so they win over the xlsx): uk, else uk_ai.
    heroes/*.json and Skirmish/*.json: sections «Кампанія» / «Битва»; RoTK/*.json: «strings»."""
    for sub in WIP_DIRS:
        folder = os.path.join(WIP, sub)
        if not os.path.isdir(folder):
            continue
        for fn in sorted(os.listdir(folder)):
            if not fn.endswith('.json'):
                continue
            d = json.load(open(os.path.join(folder, fn), encoding='utf-8'))
            for sec in ('Кампанія', 'Битва', 'strings'):
                for r in d.get(sec, []):
                    text = (r.get('uk') or '').strip() or (r.get('uk_ai') or '').strip()
                    if text and r['var'].lower() not in uk:
                        uk[r['var'].lower()] = text.replace('\\n', '\n')
    # Serhii's translation (Gondor + alternate factions), labels we did not have; text in field «sergii»
    if os.path.exists(SERHII_JSON):
        for r in json.load(open(SERHII_JSON, encoding='utf-8'))['strings']:
            text = (r.get('sergii') or '').strip()
            if text and r['var'].lower() not in uk:
                uk[r['var'].lower()] = text.replace('\\n', '\n')
    # faction community translations (Factions/<Faction>_serhii.json, e.g. Rohan since 0.12), same order as the site
    for fn in sorted(os.listdir(FACTIONS)) if os.path.isdir(FACTIONS) else []:
        if fn.endswith('_serhii.json'):
            for r in json.load(open(os.path.join(FACTIONS, fn), encoding='utf-8'))['strings']:
                text = (r.get('sergii') or '').strip()
                if text and r['var'].lower() not in uk:
                    uk[r['var'].lower()] = text.replace('\\n', '\n')


def load_uk():
    """var(lower) -> Ukrainian text (UK first, UK AI as fallback): WIP hero/mission files, campaign sheets,
    menu_strings.json, «Усі рядки»."""
    wb = load_workbook(XLSX, read_only=True)
    uk = {}
    # community proofread from the faction pages (Factions/<Faction>_reviewed.json) wins over everything
    for fn in sorted(os.listdir(FACTIONS)) if os.path.isdir(FACTIONS) else []:
        if fn.endswith('_reviewed.json'):
            for r in json.load(open(os.path.join(FACTIONS, fn), encoding='utf-8'))['strings']:
                if (r.get('uk') or '').strip() and r['var'].lower() not in uk:
                    uk[r['var'].lower()] = r['uk'].strip().replace('\\n', '\n')
    load_wip(uk)
    for name in UK_SHEETS:
        if name == ALL_SHEET:
            load_menu(uk)
        if name not in wb.sheetnames:
            continue
        rows = wb[name].iter_rows(values_only=True)
        head = list(next(rows))
        iv, iai, iuk = head.index('Переменная'), head.index('UK AI'), head.index('UK')
        for r in rows:
            text = (r[iuk] or '').strip() or (r[iai] or '').strip()
            if r[iv] and text and r[iv].lower() not in uk:  # campaign copies on «Усі рядки» never override
                uk[r[iv].lower()] = text.replace('\\n', '\n')
    # AI drafts made for the faction proofreading pages: only labels nobody translated yet (lowest priority)
    for fn in sorted(os.listdir(FACTIONS)) if os.path.isdir(FACTIONS) else []:
        if fn.endswith('_AI_drafts.json'):
            dd = json.load(open(os.path.join(FACTIONS, fn), encoding='utf-8'))
            if dd.get('meta', {}).get('site_only'):  # e.g. Rohan: proofreading on the site first
                continue
            for r in dd['strings']:
                text = (r.get('uk_ai') or '').strip()
                if text and r['var'].lower() not in uk:
                    uk[r['var'].lower()] = text.replace('\\n', '\n')
    return uk


def build_big(files):
    """BIG4 archive, same layout as the RU Russian.big: index, 'L253', data."""
    names = sorted(files)
    index_len = 16 + sum(8 + len(n.encode('ascii')) + 1 for n in names)
    first = index_len + 9  # 'L253' + 5 bytes, as in the RU archive
    out, off = bytearray(), first
    entries = []
    for n in names:
        entries.append(struct.pack('>II', off, len(files[n])) + n.encode('ascii') + b'\0')
        off += len(files[n])
    out += b'BIG4' + struct.pack('<I', off) + struct.pack('>II', len(names), first - 1)
    out += b''.join(entries) + b'L253' + b'\0' * 5
    assert len(out) == first
    for n in names:
        out += files[n]
    return bytes(out)


def sha256(path):
    return hashlib.sha256(open(path, 'rb').read()).hexdigest()


def main():
    strings = json.load(open(os.path.join(AOR10, 'strings.json'), encoding='utf-8'))['strings']
    uk = load_uk()
    extra = {k: v.replace('\\n', '\n')
             for k, v in json.load(open(os.path.join(HERE, 'extra_uk.json'), encoding='utf-8')).items()
             if not k.startswith('_')}
    uk.update({k.lower(): v for k, v in extra.items()})
    fit_to_font(uk)

    labels, order, used = {}, [], 0
    for s in strings:
        k = s['var'].lower()
        if k in uk:
            labels[s['var']] = uk[k]
            used += 1
        else:
            labels[s['var']] = s['en']
        order.append(s['var'])
    for k in extra:  # labels no AoR string file has (e.g. movie subtitles DIALOGEVENT:<sound>Subtitle)
        labels[k] = uk[k.lower()]
        order.append(k)
        used += 1
    missing = sorted(set(uk) - {k.lower() for k in order})
    if missing:
        sys.exit(f'labels in xlsx but not in strings.json: {missing[:10]}')

    csf = bytearray(build_csf(labels, order))
    csf[4:8] = struct.pack('<i', 0)  # header version 0, as in the RU AotR lotr.csf
    back, back_order = read_csf(bytes(csf))
    assert back == labels and back_order == order

    shutil.rmtree(OUT, ignore_errors=True)  # generated output only - rebuilt from scratch every run
    os.makedirs(OUT)
    open(os.path.join(OUT, 'lotr.csf'), 'wb').write(csf)
    files = {}

    if MODE == 'shadow':
        # Game stays English. The designer's font, renamed internally to the stock family "Albertus MT", ships as
        # albertusmt.otf in the mod root (-> aotr\) and shadows rotwk\Data1.big's albertusmt.otf by identical file
        # name - BFME1's proven fix (002_BFME_2/.../BETA_PATCH_NOTES.md, attempt 1 notes). Glyphs are untouched.
        shipped = ['lotr.csf']
        for src, family, ps, name, upem in SHADOW_FONTS:
            # recalcTimestamp=False: keep head.modified from the source font, so every build gives the same bytes
            # (same sha256 in the manifest -> players don't re-download unchanged fonts)
            font = TTFont(src, recalcTimestamp=False)
            if upem:
                font['head'].unitsPerEm = upem  # glyphs render smaller at the same point size
            for rec in font['name'].names:
                if rec.nameID in (1, 4, 16):
                    rec.string = family
                elif rec.nameID == 6:
                    rec.string = ps
            font.save(os.path.join(OUT, name))
            shipped.append(name)
    else:
        # Own language slot: rotwk\lang\Ukrainian.big with the font registered by language.ini (needs registry
        # Language=ukrainian, which the launcher does not set for this language).
        os.makedirs(os.path.join(OUT, '_rotwk_', 'lang'))
        src = os.path.join(HERE, 'lang_Ukrainian')
        for root, _, names in os.walk(src):
            for n in names:
                p = os.path.join(root, n)
                files[os.path.relpath(p, src).replace('/', '\\')] = open(p, 'rb').read()
        open(os.path.join(OUT, '_rotwk_', 'lang', 'Ukrainian.big'), 'wb').write(build_big(files))
        shutil.copyfile(os.path.join(HERE, 'branding', 'RussianSplash_ru931.jpg'), os.path.join(OUT, '_rotwk_', 'UkrainianSplash.jpg'))
        shipped = ['lotr.csf', '_rotwk_/UkrainianSplash.jpg', '_rotwk_/lang/Ukrainian.big']

    # media overrides (e.g. data/movies/CS01.vp6 - the intro with burnt-in Ukrainian subtitles): tools/media/<path>
    # ships as <path> in the mod root, which the launcher copies over aotr\<path> (backed up, restored on exit)
    for base, on in ((NO_INTRO, SHIP_NO_INTRO), (MEDIA, SHIP_MEDIA)):
        for root, _, names in os.walk(base) if on else []:
            for n in sorted(names):
                rel = os.path.relpath(os.path.join(root, n), base).replace(os.sep, '/')
                os.makedirs(os.path.dirname(os.path.join(OUT, *rel.split('/'))), exist_ok=True)
                shutil.copyfile(os.path.join(root, n), os.path.join(OUT, *rel.split('/')))
                if rel not in shipped:
                    shipped.append(rel)

    from PIL import Image
    for png, rel, size in BRANDING_IMAGES:
        src = os.path.join(BRANDING, png)
        if not os.path.exists(src):
            continue
        dst = os.path.join(OUT, *rel.split('/'))
        os.makedirs(os.path.dirname(dst), exist_ok=True)
        im = Image.open(src).convert('RGB')
        if im.size != size:
            im = im.resize(size, Image.LANCZOS)
        im.save(dst, 'JPEG', quality=92)
        shipped.append(rel)

    manifest = {
        'slug': 'ukrainian-localization',  # the published mod (Submod ID assigned)
        'display_name': 'Українізатор AotR 10.0',
        'version': VERSION,
        # same text as the user's description in the launcher's Creator Tools (0.10), typos fixed
        'description': 'Українська локалізація для AoR 10\n\n'
                       'УВАГА ПЕРЕКЛАД В АКТИВНІЙ РОБОТІ ТА МАЄ РЕГУЛЯРНІ ОНОВЛЕННЯ\n\n'
                       'Перекладено та вичитано:\n\n'
                       '- Меню та налаштування\n'
                       '- Кампанія «Братство Персня» та кампанія «Дві вежі»\n'
                       '- Загальні тексти та тексти фракції Ґондор у режимі «Битва»\n\n'
                       'Чорновий переклад\n\n'
                       '- Всі сюжетні діалоги кампанії «Повернення короля»',
        'author': 'Clever Play UA',
        'aotr_version': '10.0.1',  # launcher Creator Tools wants X.Y.Z (strings.json updated to the 10.0.1 lotr.str)
        'genre': 'Translation',
        'language': 'English',  # the launcher writes this field (BFME language left English: shadow-font mode)
        'checksums': {f: {'checksum': sha256(os.path.join(OUT, *f.split('/')))} for f in shipped},
        'extra_artifacts': [],
    }
    with open(os.path.join(OUT, 'aotr_submod_details.json'), 'w', encoding='utf-8', newline='\n') as f:
        json.dump(manifest, f, ensure_ascii=False, indent=4)

    # same name as the launcher's Creator Tools "Publish Submod": <slug>_<version>.zip
    zip_path = os.path.join(os.path.dirname(OUT), f"{manifest['slug']}_{VERSION}.zip")
    with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as z:
        for f in shipped + ['aotr_submod_details.json']:  # manifest last, like the launcher's own zips
            z.write(os.path.join(OUT, *f.split('/')), f)

    print(f'lotr.csf: {len(order)} labels, {used} Ukrainian, {len(order) - used} English')
    print(f'zip: {zip_path}')
    print(f'mode {MODE}: {shipped}' + (f' | Ukrainian.big: {sorted(files)}' if files else ''))
    print(f'-> {OUT}')


if __name__ == '__main__':
    main()
