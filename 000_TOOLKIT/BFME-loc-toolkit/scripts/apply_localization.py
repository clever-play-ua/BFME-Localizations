# -*- coding: utf-8 -*-
r"""
BFME1 localization toolkit -- apply_localization.py

Flow:
  1. Find the game folder (cached in scripts\game_path.txt, or ask).
  2. Read Version:Format2 from lang\english\lotr.csf to get the exact
     build string (e.g. "2.22v7.0.4") -- NOT just "2.22", because balance
     patches reuse the same "2.22" label across different builds with
     different tooltip text (see locales\<build>\ layout).
  3. Look for locales\<that exact build>\ -- if missing, stop and say so
     (never guess-apply a translation built for a different build).
  4. List the language subfolders found there, let the user pick one.
  5. Apply it: strip data\lotr.str from every installed _patch*.big that
     carries one, fix fontsubstitution.ini/language.ini in every copy
     found across those _patch*.big archives AND ini.big (which patch
     archives exist, and what they carry, differs per patch generation --
     2.22 ships one _patch222.big with everything; 1.06 splits it across
     _patch105.big and _patch106.big instead -- see list_patch_archives()),
     rebuild lang\english.big with the full CSF + embedded font +
     LocalFontFile. (This is the exact method validated by hand this
     session.)
  6. Back up any file before its first edit (.orig suffix, never overwritten).

This script has ZERO third-party pip dependencies -- only stdlib + the
vendored pyBIG (python\pyBIG) + the vendored csf_tools.py (scripts\).
"""
import sys
import os
import re
import json
import shutil
import glob

# Safety net regardless of the console's codepage (the .bat also runs
# `chcp 65001`, but that can fail/be skipped) -- never let a block-art
# banner or non-ASCII display name crash the whole tool.
try:
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
except (AttributeError, ValueError):
    pass

GREEN = '\033[92m'
YELLOW = '\033[93m'
RESET = '\033[0m'
CHECK = '[✓]'


def ok(msg):
    print(f'{GREEN}{CHECK} {msg}{RESET}')


def ok_backup(msg):
    print(f'{YELLOW}{CHECK} {msg}{RESET}')


HERE = os.path.dirname(os.path.abspath(__file__))
TOOLKIT_ROOT = os.path.dirname(HERE)
LOCALES_DIR = os.path.join(TOOLKIT_ROOT, 'locales')
AUDIO_DIR = os.path.join(LOCALES_DIR, 'audio')
GAME_PATH_CACHE = os.path.join(HERE, 'game_path.txt')

sys.path.insert(0, os.path.join(TOOLKIT_ROOT, 'python'))
sys.path.insert(0, HERE)
from pyBIG import Archive          # noqa: E402
from csf_tools import read_csf, build_csf, read_str  # noqa: E402

ANCHOR = 'LocalFontFile = AlbertusMT.otf ;// New opentype format font, allows private font registration from memory data'


REG_KEY = r'SOFTWARE\WOW6432Node\Electronic Arts\EA Games\The Battle for Middle-earth'


def _is_valid_game_folder(path):
    """A real BFME1 install folder, regardless of which patch build is
    installed on it -- checked via lotrbfme.exe itself rather than any one
    patch archive (used to require _patch222.big specifically, which wrongly
    rejected valid installs sitting on an older patch generation, e.g. a
    clean 1.06 install with no _patch222.big at all -- get_installed_build()
    is what actually determines the build, this check only confirms "is
    this a BFME1 folder")."""
    return os.path.exists(os.path.join(path, 'lotrbfme.exe'))


def find_game_path_from_registry():
    try:
        import winreg
        with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, REG_KEY) as k:
            path, _ = winreg.QueryValueEx(k, 'InstallPath')
        path = path.rstrip('\\/')
        if _is_valid_game_folder(path):
            return path
    except OSError:
        pass
    return None


def find_game_path():
    reg_path = find_game_path_from_registry()
    if reg_path:
        with open(GAME_PATH_CACHE, 'w', encoding='utf-8') as f:
            f.write(reg_path)
        return reg_path

    if os.path.exists(GAME_PATH_CACHE):
        with open(GAME_PATH_CACHE, encoding='utf-8') as f:
            cached = f.read().strip()
        if cached and _is_valid_game_folder(cached):
            return cached
    while True:
        path = input('Path to your BFME1 folder (containing lotrbfme.exe): ').strip().strip('"')
        if _is_valid_game_folder(path):
            with open(GAME_PATH_CACHE, 'w', encoding='utf-8') as f:
                f.write(path)
            return path
        print('  -- lotrbfme.exe not found there. Is this a real BFME1 install folder?')


def resolve_active_lang_folder(game_path, reg_language):
    """Which lang\\<X>.big to patch. Always follows the registry Language
    value (lowercased -- lang\\<X>.big filenames are always lowercase:
    english.big, french.big, russian.big...), NOT hardcoded to English --
    this covers the common "French/German/... base + 2.22 on top" case,
    where 2.22 dumps English text into whatever language slot is active
    but leaves that language's own audio archive untouched. Falls back to
    'english' if the registry is unreadable or that .big is missing."""
    if reg_language:
        candidate = reg_language.strip().lower()
        if os.path.exists(os.path.join(game_path, 'lang', f'{candidate}.big')):
            return candidate
    if os.path.exists(os.path.join(game_path, 'lang', 'english.big')):
        return 'english'
    return None


def find_path_in_archive(arc, suffix):
    """Case-insensitive search for the one entry ending in `suffix` (e.g.
    '\\lotr.csf') -- archives are NOT consistent about casing (english.big
    uses lowercase 'lang\\english\\...', french.big uses 'Lang\\French\\...'),
    so never hardcode a path, always discover it from the archive itself."""
    suffix_low = suffix.lower()
    for name in arc.entries:
        if name.lower().endswith(suffix_low):
            return name
    return None


def find_all_paths_in_archive(arc, suffix):
    """Same as find_path_in_archive but returns EVERY match, not just the
    first -- some patch archives carry more than one copy of the same
    filename under different path prefixes (confirmed: patch 1.06's
    _patch105.big ships BOTH data\\ini\\language.ini AND
    lang\\english\\language.ini, whereas 2.22's _patch222.big only has
    the one data\\ini\\language.ini copy)."""
    suffix_low = suffix.lower()
    return [name for name in arc.entries if name.lower().endswith(suffix_low)]


def list_patch_archives(game_path):
    """Every top-level _patch*.big archive actually present in the install
    root, sorted for determinism. These carry build-specific overrides on
    top of the base lang\\<X>.big archive -- a data\\lotr.str text overlay,
    and/or duplicate fontsubstitution.ini/language.ini copies -- and which
    files exist, and in which archive, differs per patch generation
    (confirmed: 2.22 ships one _patch222.big with all three; 1.06 instead
    splits it across _patch105.big -- fontsubstitution.ini + TWO
    language.ini copies, no .str -- and _patch106.big -- only the .str
    text overlay, no font-related files at all). Rather than hardcode one
    archive name, discover whatever is actually installed and patch every
    copy of every relevant file found in each one -- the same "don't guess
    which copy wins, patch them all" philosophy this toolkit already uses
    for ini.big's own duplicate fontsubstitution.ini."""
    return sorted(glob.glob(os.path.join(game_path, '_patch*.big')))


def get_registry_language():
    """The active game language per the registry (HKLM\\...\\Language) --
    the OS-level switch that decides which lang\\<X>.big the engine loads,
    separate from the patch build detected from the CSF."""
    try:
        import winreg
        with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, REG_KEY) as k:
            value, _ = winreg.QueryValueEx(k, 'Language')
        return value
    except OSError:
        return None


def _extract_build_token(raw):
    # raw looks like "Patch 2.22v7.0.4" (or "...v7.0.4 UA" if already patched
    # by this toolkit before) -- pull out the "2.22vX.Y.Z" token. Also
    # accepts a version-like token with no 'v' at all (confirmed: patch
    # 1.06's own data\lotr.str carries "Version T3A 1.06", not
    # "Patch X.YZvA.B.C" -- so a bare "1.06" must match too), as long as it
    # starts with a digit and looks like a dotted version number.
    for token in raw.replace('Patch', '').split():
        if token[:1].isdigit() and ('v' in token or '.' in token):
            return token
    return None


def get_installed_build(game_path, lang_folder):
    """The literal patch build string (e.g. "2.22v7.0.4", or "1.06" on an
    older install) lives in a patch archive's data\\lotr.str on a
    FRESH/untouched install -- the CSF's own Version:Format2 is still the
    stock '%d.%02d'-style format string until this toolkit (or a manual
    rebuild) overwrites it. So: check every installed _patch*.big's .str
    first (the pristine, pre-patch source of truth -- 2.22 keeps it in
    _patch222.big, 1.06 in _patch106.big instead), and only fall back to
    the CSF for installs this toolkit already applied once (which deletes
    data\\lotr.str and bakes the literal string into the CSF)."""
    for patch_path in list_patch_archives(game_path):
        with open(patch_path, 'rb') as f:
            p_data = f.read()
        p_arc = Archive(p_data)
        str_path = find_path_in_archive(p_arc, r'data\lotr.str')
        if str_path is None:
            continue
        str_txt = p_arc.read_file(str_path).decode('latin-1', errors='replace')
        m = re.search(r'Version:Format2\s*\r?\n\s*"([^"]*)"', str_txt, re.IGNORECASE)
        if m:
            token = _extract_build_token(m.group(1))
            if token:
                return token

    lang_big = os.path.join(game_path, 'lang', f'{lang_folder}.big')
    if not os.path.exists(lang_big):
        return None
    with open(lang_big, 'rb') as f:
        data = f.read()
    arc = Archive(data)
    csf_path = find_path_in_archive(arc, r'\lotr.csf')
    if csf_path is None:
        return None
    csf = arc.read_file(csf_path)
    labels, _ = read_csf(csf)
    return _extract_build_token(labels.get('Version:Format2', ''))


def is_already_patched(game_path, lang_folder):
    """True if this toolkit (any language) has already been applied to
    this install -- our embedded fonts always carry the bfme_loc_ prefix."""
    lang_big = os.path.join(game_path, 'lang', f'{lang_folder}.big')
    if not os.path.exists(lang_big):
        return False
    with open(lang_big, 'rb') as f:
        arc = Archive(f.read())
    return any(name.startswith('bfme_loc_') for name in arc.entries)


def get_build_baseline_en(game_path, lang_folder):
    """Pristine EN text read straight from the CURRENTLY installed game
    files -- no separate backup/snapshot needed. This only makes sense
    when the game hasn't been patched by this toolkit yet, which is
    exactly when our own flow calls it (the health-check always runs
    BEFORE the patch step). If it's already patched, don't bother trying
    to reconstruct history ourselves -- the player can just verify/
    reinstall the game via their platform (e.g. Steam: Verify Integrity
    of Game Files) in seconds, any time, as many times as they like, and
    that's a far more reliable pristine copy than anything we could cache
    on our own."""
    def read_bytes(name):
        p = os.path.join(game_path, *name.split('\\'))
        return open(p, 'rb').read() if os.path.exists(p) else None

    baseline = {}
    lang_data = read_bytes(f'lang\\{lang_folder}.big')
    if lang_data:
        arc = Archive(lang_data)
        csf_path = find_path_in_archive(arc, r'\lotr.csf')
        if csf_path:
            labels, _ = read_csf(arc.read_file(csf_path))
            baseline.update(labels)
    # Overlay every installed _patch*.big's own data\lotr.str, in sorted
    # (deterministic) order -- 2.22 carries this in _patch222.big, 1.06 in
    # _patch106.big instead (_patch105.big has none). Whichever patch
    # archives are actually present get applied on top of the CSF baseline,
    # str always wins over CSF for a label both define (see the §3.7-style
    # archive-priority facts in TOOLKIT_NOTES.md).
    for patch_path in list_patch_archives(game_path):
        arc = Archive(open(patch_path, 'rb').read())
        str_path = find_path_in_archive(arc, r'data\lotr.str')
        if str_path:
            txt = arc.read_file(str_path).decode('cp1252', errors='replace')
            labels, _ = read_str(txt)
            baseline.update(labels)
    return baseline


_NUMBER_RE = re.compile(r'\d+(?:\.\d+)?%?')


def _normalize_text(s):
    """Put a string from EITHER source (real-newline CSF/JSON text, or
    .str's literal two-character '\\n' line-break convention) into one
    common form before comparing, so a pure representation difference
    doesn't get flagged as a wording change."""
    s = s.replace('\r\n', '\n').replace('\r', '\n')
    s = s.replace('\\n', '\n')
    return s.strip()


def _numbers_only_diff(a, b):
    """True if a and b are identical once every number is masked out --
    i.e. the wording is the same, only a balance value changed."""
    return _NUMBER_RE.sub('#', a) == _NUMBER_RE.sub('#', b)


def _casing_only_diff(a, b):
    return a.lower() == b.lower()


def _split_lines(s):
    return [l.strip() for l in s.split('\n') if l.strip()]


def _ua_number_unit(n, unit):
    n = int(n)
    if unit == 'second':
        # abbreviated form ("5 сек.") -- no pluralization needed, matches
        # the terminology pass applied across the whole database
        return f'{n} сек.'
    forms = ('хвилина', 'хвилини', 'хвилин')
    if n % 10 == 1 and n % 100 != 11:
        form = forms[0]
    elif n % 10 in (2, 3, 4) and n % 100 not in (12, 13, 14):
        form = forms[1]
    else:
        form = forms[2]
    return f'{n} {form}'


def _ua_duration(text):
    parts = []
    m = re.search(r'(\d+)\s*minutes?', text)
    if m:
        parts.append(_ua_number_unit(m.group(1), 'minute'))
    m = re.search(r'(\d+)\s*seconds?', text)
    if m:
        parts.append(_ua_number_unit(m.group(1), 'second'))
    return ' '.join(parts) if parts else text


def _translate_tail_line(line):
    """Translate ONE appended info line using this project's established
    terminology (Час будівництва / Час вербування / Перезарядка /
    Тривалість / Час воскресіння). Returns None if unrecognized."""
    m = re.match(r'^Build time:\s*(.+)$', line, re.IGNORECASE)
    if m:
        return f'Час будівництва: {_ua_duration(m.group(1))}'
    m = re.match(r'^Recruit time for (.+?) Level (\d+):\s*(.+)$', line, re.IGNORECASE)
    if m:
        return f'Час вербування для {m.group(2)} рівня {m.group(1)}: {_ua_duration(m.group(3))}'
    m = re.match(r'^Recruit time:\s*(.+)$', line, re.IGNORECASE)
    if m:
        return f'Час вербування: {_ua_duration(m.group(1))}'
    m = re.match(r'^Revive time for levels? ([\d\-]+):\s*(.+)$', line, re.IGNORECASE)
    if m:
        return f'Час воскресіння для рівнів {m.group(1)}: {_ua_duration(m.group(2))}'
    m = re.match(r'^Revive time\s*(.+)$', line, re.IGNORECASE)
    if m:
        return f'Час воскресіння {_ua_duration(m.group(1))}'
    m = re.match(r'^Cooldown:\s*(.+)$', line, re.IGNORECASE)
    if m:
        return f'Перезарядка: {_ua_duration(m.group(1))}'
    m = re.match(r'^Duration:\s*(.+)$', line, re.IGNORECASE)
    if m:
        return f'Тривалість: {_ua_duration(m.group(1))}'
    return None


def _try_append_update(our_en_norm, base_en_norm, our_ua):
    our_lines = _split_lines(our_en_norm)
    base_lines = _split_lines(base_en_norm)
    if len(base_lines) <= len(our_lines):
        return None
    if [l.lower() for l in our_lines] != [l.lower() for l in base_lines[:len(our_lines)]]:
        return None
    translated_tail = []
    for line in base_lines[len(our_lines):]:
        t = _translate_tail_line(line)
        if t is None:
            return None
        translated_tail.append(t)
    return (our_ua or '').strip() + ' \n ' + ' \n '.join(translated_tail)


# Labels that must NEVER be touched by check_build_health(), discovered the
# hard way across repeated French/Italian/Spanish/German test installs:
# without this, EVERY new base-language install re-triggers the exact same
# handful of false positives and stomps an already-correct translation, or
# resurrects a bogus artifact label -- forever, on every single install.
#
# PINNED_VARS: 2.22 never overwrites these particular labels in ANY base
# language, so get_build_baseline_en() ends up reading whatever language
# the BASE install itself shipped for them (confirmed: this exact set showed
# French text on a French base, Italian on Italian, Spanish on Spanish,
# German on German) -- not real English. The whole "compare our stored EN
# against the live build's EN" model breaks down for these specific vars, so
# just skip them unconditionally; our stored en/ua already describe the
# real, correctly-researched meaning (verified by hand against multiple
# installs).
PINNED_VARS = {
    'Color:RohanGreen',
    'CONTROLBAR:ToolTipEntAllies',
    'CONTROLBAR:ToolTipGandalfLeadership',
    'CONTROLBAR:ToolTipBuildGondorFireStonePorter',
    'CONTROLBAR:ToolTipBuildGondorRangerHordeForGoodIthilien',
    'Color:Marsala',
    'Map:MAPMPFordsofIsenWinter',
    'CONTROLBAR:ShatteredHope',
    'CONTROLBAR:WretchedFate',
    'Map:MAPMPDorwinion/Desc',
    'Map:MAPMPDorwinionffa/Desc',
}

# BLACKLIST_VARS: labels produced by a historical .str-parsing edge case (a
# stray "ENDUPGRADE:"-prefixed split artifact that always duplicates a real,
# already-correctly-translated "UPGRADE:" label) -- keeps reappearing on
# fresh base installs even though the underlying regex bugs were fixed, so
# just refuse to ever add it instead of re-diagnosing the same artifact
# every time a new language gets tested.
BLACKLIST_VARS = {
    'ENDUPGRADE:RohanHorseBow',
}


def check_build_health(game_path, lang_folder, entries, lang_field, lang_display_name):
    """Pre-apply reconciliation against the installed build's real text
    (never blocks, this only edits `entries` in place -- the caller still
    does the actual .big writing): for every label whose EN text drifted
    since we translated it,
      1. label missing from strings.json entirely -> add it with the
         build's EN text as a placeholder translation (English fallback,
         better than the label silently disappearing from the game --
         this bit us once already, see sachawyntertight_pua_decoration_
         WARNING-adjacent history).
      2. casing-only EN drift ("left click" -> "Left click") -> sync EN,
         translation is unaffected, not worth mentioning.
      3. pure balance-number drift, and our translation's numbers appear
         in the same order -> sync EN, swap the numbers into place in the
         translation automatically.
      4. EN text is the old text plus one or more APPENDED templated info
         lines (Build time / Recruit time / Cooldown / Duration / Revive
         time) -> sync EN, translate just the new tail and append it.
      5. anything else (genuinely rewritten content) -> sync EN, and set
         the translation to the EN text too (English fallback) rather
         than keep a stale translation describing a mechanic that no
         longer matches -- reported to the console explicitly.
    Returns True if `entries` was modified (caller should re-save it)."""
    if is_already_patched(game_path, lang_folder):
        print('  this install is already patched by this toolkit -- skipping reconciliation')
        print('  (the live files no longer hold the build\'s real English text to compare')
        print('  against). Verify/reinstall the game via your platform first for an accurate check.')
        return False

    baseline = get_build_baseline_en(game_path, lang_folder)
    if not baseline:
        return False

    # defensively purge any BLACKLIST_VARS that already snuck into `entries`
    # from a run before this pin list existed -- the loop below only stops
    # FUTURE re-additions, it doesn't retroactively clean up old ones
    before_purge = len(entries)
    entries[:] = [e for e in entries if e.get('var') not in BLACKLIST_VARS]
    purged = before_purge - len(entries)
    if purged:
        print(f'  removed {purged} blacklisted artifact label(s) left over from an older run')

    our_by_var = {e['var']: e for e in entries}
    added = casing_synced = number_synced = append_synced = rewritten_synced = 0

    for var, base_en_raw in baseline.items():
        if var in PINNED_VARS or var in BLACKLIST_VARS:
            continue
        # Normalize the baseline text ONCE, up front, and use that
        # normalized form for everything we might persist -- never the raw
        # `.str`-sourced text. .str's own convention encodes a line break as
        # the literal two characters '\' + 'n' (not a real newline byte),
        # and read_str()/get_build_baseline_en() intentionally don't
        # unescape that (it's needed verbatim for _numbers_only_diff-style
        # comparison against our own '\n'-in-JSON-normalized text further
        # down). Every assignment below used to store this raw, still-
        # escaped text straight into entry['en']/entry[lang_field] -- fine
        # for comparison, wrong for anything actually written to
        # strings.json/the CSF, where it shows up in-game as a literal
        # visible "\n" instead of a line break (confirmed: this is exactly
        # what happened to CONTROLBAR:TooltipAthelas and ~354 other labels
        # the first time this ran against a 1.06 install).
        base_en = _normalize_text(base_en_raw)
        entry = our_by_var.get(var)
        if entry is None:
            new_entry = {'var': var, 'en': base_en, lang_field: base_en}
            entries.append(new_entry)
            our_by_var[var] = new_entry
            added += 1
            continue

        our_en = entry.get('en') or ''
        our_norm = _normalize_text(our_en)
        base_norm = base_en
        if our_norm == base_norm:
            continue

        if _casing_only_diff(our_norm, base_norm):
            entry['en'] = base_en
            casing_synced += 1
            continue

        if _numbers_only_diff(our_norm, base_norm):
            old_nums = _NUMBER_RE.findall(our_norm)
            new_nums = _NUMBER_RE.findall(base_norm)
            ua_text = entry.get(lang_field) or ''
            ua_nums = _NUMBER_RE.findall(ua_text)
            if ua_nums == old_nums:
                it = iter(new_nums)
                entry[lang_field] = _NUMBER_RE.sub(lambda m: next(it, m.group(0)), ua_text)
                entry['en'] = base_en
                number_synced += 1
                continue
            # numbers didn't line up cleanly (e.g. translation reworded the
            # sentence) -- fall through to the generic rewritten handling

        new_ua = _try_append_update(our_norm, base_norm, entry.get(lang_field))
        if new_ua is not None:
            entry[lang_field] = new_ua
            entry['en'] = base_en
            append_synced += 1
            continue

        entry['en'] = base_en
        entry[lang_field] = base_en  # English fallback -- stale translation would be wrong, not just untranslated
        rewritten_synced += 1

    total_changed = added + casing_synced + number_synced + append_synced + rewritten_synced + purged
    if total_changed == 0:
        ok('Translation is fully up to date with the installed build.')
        return False

    print('Checking translation freshness against the installed build...')

    if added:
        print(f'  {added} FULLY NEW LINE(S) WITH NO TRANSLATION TO {lang_display_name.upper()}, ADDED IN ENGLISH')
    if rewritten_synced:
        print(f'  {rewritten_synced} FULLY REWRITTEN LINE(S) WITH NO TRANSLATION TO {lang_display_name.upper()}, WILL BE ADDED IN ENGLISH')
    if number_synced or append_synced:
        print(f'  {number_synced + append_synced} label(s) auto-updated (balance numbers / added build-time lines)')
    if casing_synced:
        print(f'  {casing_synced} label(s) had a casing-only change, ignored')

    return True


def list_available_builds():
    if not os.path.isdir(LOCALES_DIR):
        return []
    return sorted(d for d in os.listdir(LOCALES_DIR) if os.path.isdir(os.path.join(LOCALES_DIR, d)))


def list_languages(build):
    build_dir = os.path.join(LOCALES_DIR, build)
    langs = []
    for d in sorted(os.listdir(build_dir)):
        meta_path = os.path.join(build_dir, d, 'meta.json')
        if os.path.exists(meta_path):
            with open(meta_path, encoding='utf-8') as f:
                meta = json.load(f)
            langs.append((d, meta))
    return langs


def backup_once(path):
    bak = path + '.orig'
    if not os.path.exists(bak):
        shutil.copy2(path, bak)
        ok_backup(f'backed up -> {os.path.basename(bak)}')


def list_audio_packs():
    """Purely filesystem-driven: whatever subfolder of locales\\audio\\ has
    a matching <name>audio.big inside it IS an available pack, full stop --
    no hardcoded language list. Only real, full voice dubs belong here
    (confirmed by hand: English/French/German/Italian/Spanish/Russian are
    real; several others turned out to be silent/near-empty or, for
    Turkish, a byte-for-byte copy of the English pack -- those were removed
    from this folder, which is exactly why this stays a filesystem scan
    instead of a fixed list)."""
    if not os.path.isdir(AUDIO_DIR):
        return []
    packs = []
    for name in sorted(os.listdir(AUDIO_DIR)):
        pack_dir = os.path.join(AUDIO_DIR, name)
        if os.path.isfile(os.path.join(pack_dir, f'{name}audio.big')):
            packs.append(name)
    return packs


def _text_source_marker(game_path, lang_folder):
    """Sidecar file next to lang\\<lang_folder>.big recording which
    translation (locales\\<build>\\<lang_dir>) is actually applied right
    now -- mirrors _audio_source_marker() for the same reason: the archive
    is_already_patched() alone can't say WHICH language was applied, only
    that this toolkit touched it at all."""
    return os.path.join(game_path, 'lang', f'{lang_folder}.big.source')


def get_current_text_source(game_path, lang_folder, build):
    """Display name of whatever text is actually installed right now: the
    applied translation's own meta.json display_name if the marker says so,
    else the native/vanilla language of lang_folder itself (untouched)."""
    marker = _text_source_marker(game_path, lang_folder)
    if os.path.exists(marker):
        with open(marker, encoding='utf-8') as f:
            lang_dir = f.read().strip()
        if lang_dir:
            meta_path = os.path.join(LOCALES_DIR, build, lang_dir, 'meta.json')
            if os.path.exists(meta_path):
                with open(meta_path, encoding='utf-8') as f:
                    return json.load(f)['display_name']
    return f'{lang_folder.capitalize()} (original)'


def _audio_source_marker(game_path, lang_folder):
    """Sidecar file next to lang\\<lang_folder>audio.big recording which
    voice pack is ACTUALLY inside it right now. Needed because the archive's
    FILENAME always matches the active text language (e.g. spanishaudio.big)
    regardless of whose voice audio was swapped in -- without this, there's
    no way to tell "spanishaudio.big" apart from "spanishaudio.big, but
    secretly holding French voice lines" just by looking at the filename."""
    return os.path.join(game_path, 'lang', f'{lang_folder}audio.big.source')


def get_current_audio_source(game_path, lang_folder):
    """The voice pack actually loaded right now: whatever the marker says,
    or lang_folder itself if no swap has ever been applied (native/default,
    matching the text language, exactly what a totally fresh install has)."""
    marker = _audio_source_marker(game_path, lang_folder)
    if os.path.exists(marker):
        with open(marker, encoding='utf-8') as f:
            saved = f.read().strip()
        if saved:
            return saved
    return lang_folder


def apply_audio_pack(game_path, lang_folder, pack_name):
    """Rebuild lang\\<lang_folder>audio.big from a DIFFERENT language's voice
    pack (locales\\audio\\<pack_name>\\<pack_name>audio.big) -- e.g. English
    text + French voice acting. Text and audio are always physically
    separate archives (lang\\<X>.big = text/fonts/UI, lang\\<X>audio.big =
    just .wav/.mp3 voice lines), so this never touches the text side at all.
    Every entry's internal path gets its language-name segment rewritten to
    match lang_folder (e.g. 'lang\\French\\...' -> 'lang\\English\\...') --
    the raw audio bytes are copied through completely untouched, only the
    path prefix changes."""
    src_big = os.path.join(AUDIO_DIR, pack_name, f'{pack_name}audio.big')
    dst_big = os.path.join(game_path, 'lang', f'{lang_folder}audio.big')

    backup_once(dst_big)

    with open(src_big, 'rb') as f:
        src_data = f.read()
    src_header = src_data[:4]
    src_arc = Archive(src_data)

    new_arc = Archive.empty(header=src_header.decode('ascii'))
    target_lang_seg = lang_folder.capitalize()
    for name in src_arc.file_list():
        parts = name.split('\\')
        if len(parts) >= 2 and parts[0].lower() == 'lang':
            parts[1] = target_lang_seg
        new_arc.add_file('\\'.join(parts), src_arc.read_file(name))
    new_arc.save(dst_big)
    with open(_audio_source_marker(game_path, lang_folder), 'w', encoding='utf-8') as f:
        f.write(pack_name)
    ok_backup(f'lang\\{lang_folder}audio.big rebuilt with {pack_name} voice audio')


def apply_language(game_path, lang_folder, build, lang_dir, meta):
    lang_root = os.path.join(LOCALES_DIR, build, lang_dir)
    with open(os.path.join(lang_root, 'strings.json'), encoding='utf-8') as f:
        data = json.load(f)
    entries = data['strings'] if isinstance(data, dict) and 'strings' in data else data
    lang_field = meta['lang_code']

    changed = check_build_health(game_path, lang_folder, entries, lang_field, meta['display_name'])
    if changed:
        if isinstance(data, dict) and 'strings' in data:
            data['strings'] = entries
        else:
            data = entries
        with open(os.path.join(lang_root, 'strings.json'), 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        ok_backup('strings.json updated with the reconciled text')

    # font_file is OPTIONAL -- languages whose alphabet the stock Albertus MT
    # already covers (French, Spanish: standard Latin + accents, exactly
    # what EA's own original European localizations shipped with) don't
    # need any font replaced at all. Only languages needing glyphs the stock
    # font lacks (Ukrainian: Cyrillic) ship a font_file/sacha_font_file.
    font_file = meta.get('font_file')
    font_ext = os.path.splitext(font_file)[1] if font_file else None
    embedded_font_name = f'bfme_loc_{lang_field}_font{font_ext}' if font_file else None
    sacha_font_file = meta.get('sacha_font_file')
    sacha_ext = os.path.splitext(sacha_font_file)[1] if sacha_font_file else None
    embedded_sacha_font_name = f'bfme_loc_{lang_field}_sachafont{sacha_ext}' if sacha_font_file else None

    def add_font_lines(ini_text):
        """Strip any stale bfme_loc_* LocalFontFile lines (from a previous
        run/language/font) and add fresh ones for whichever fonts this
        language actually ships (none, for a language that doesn't need any)."""
        ini_text = ''.join(
            line for line in ini_text.splitlines(keepends=True)
            if not line.strip().startswith('LocalFontFile = bfme_loc_')
        )
        if ANCHOR not in ini_text:
            return ini_text
        extra = ''
        if embedded_font_name:
            extra += f'\n  LocalFontFile = {embedded_font_name}'
        if embedded_sacha_font_name:
            extra += f'\n  LocalFontFile = {embedded_sacha_font_name}'
        if not extra:
            return ini_text
        return ini_text.replace(ANCHOR, ANCHOR + extra)

    lang_big = os.path.join(game_path, 'lang', f'{lang_folder}.big')
    ini_big = os.path.join(game_path, 'ini.big')
    # Every top-level _patch*.big archive found (2.22's _patch222.big;
    # 1.06's _patch105.big + _patch106.big instead; any future patch
    # generation, automatically, via list_patch_archives()'s glob), PLUS
    # ini.big -- these are the "auxiliary" archives that may carry a
    # data\lotr.str text overlay and/or duplicate fontsubstitution.ini/
    # language.ini copies on top of the base lang\<lang_folder>.big
    # archive handled separately below.
    aux_archives = list_patch_archives(game_path)
    if os.path.exists(ini_big):
        aux_archives.append(ini_big)

    for p in aux_archives + [lang_big]:
        backup_once(p)

    # ---- every auxiliary archive: strip data\lotr.str, register our fonts
    # in every language.ini copy found, retarget every fontsubstitution.ini
    # copy found ----
    # fontsubstitution.ini gets exactly ONE edit: the EXISTING "FontSubstitution
    # SachaWynter" block's target is retargeted from its stock "SachaWynterTight"
    # to "Albertus MT" directly -- matching the approach used by the official
    # Chinese and Thai localizations (both redirect straight to their main text
    # font, no separate decorative-font clone). Earlier this toolkit avoided a
    # direct-to-Albertus-MT redirect over a fear of losing "PUA decorative icon
    # glyphs" in sachwt__.ttf -- that fear was checked and disproven: dumping
    # every glyph name in the font (fontTools) shows a completely ordinary
    # Western/Central European character set (accented Latin, punctuation, a
    # few math symbols) plus exactly two Private-Use-Area entries at
    # 0xF001/0xF002, which turned out to be the "fi"/"fl" typographic
    # ligatures (rendered and visually confirmed), not icons. Nothing decorative
    # is lost by redirecting. See sachawyntertight_pua_decoration_WARNING in
    # bfme1_localization.json -- flagged there as SUPERSEDED, not deleted, so
    # the reasoning trail stays visible.
    # cleans up earlier, now-abandoned approaches this toolkit briefly tried
    # (standalone "FontSubstitution Omnia LT Std / Generals -> Albertus MT"
    # blocks, then a SachaWynter -> "Omnia LT Std" retarget with a cloned
    # Omnia font) -- strip any leftover trace of either so a machine that was
    # patched by an older version of this script ends up clean too.
    #
    # ALSO strips any pre-existing "FontSubstitution Albertus MT -> X" block
    # some base languages ship natively (confirmed on Polish: stock
    # fontsubstitution.ini already redirects "Albertus MT" -> "Arial", almost
    # certainly because stock Albertus MT lacks Polish diacritics -- other
    # languages tested so far didn't have this block at all). Since it
    # matches by FAMILY NAME, it silently redirects OUR Cyrillic-extended
    # font away too (it's registered under that same family name), so the
    # entire localized look-and-feel quietly reverts to plain Arial with zero
    # error. We always want "Albertus MT" requests to resolve to our own
    # font file directly, so this block is never wanted, on any base
    # language -- always strip it, don't try to retarget it like SachaWynter.
    # ^[ \t]* (not just \b or nothing) anchors the opening match to an
    # ACTUAL code line -- critical, because the stock file's comment header
    # includes a commented-out EXAMPLE block using this exact same text
    # (";   FontSubstitution "Albertus MT"   ; Substitute requests for...")
    # as format documentation. Without the anchor, this regex doesn't care
    # about the leading ';' and matches starting from inside that comment;
    # since a commented "End" line (";   End") doesn't satisfy the closing
    # '\n[ \t]*End' either (semicolon isn't in the whitespace class), the
    # non-greedy match is forced to skip past it and keeps consuming
    # everything downstream until it finds the NEXT real End -- which is the
    # real SachaWynter block's own closing End far below, deleting
    # everything in between including that entire working block. Confirmed:
    # this exact bug wiped _patch222.big/ini.big's fontsubstitution.ini down
    # to just its 3-line comment header on a real install.
    _STALE_BLOCK_RE = re.compile(
        r'\n?^[ \t]*FontSubstitution\s+"(?:Omnia LT Std|Generals|Albertus MT)"[^\n]*\n.*?\n[ \t]*End\n?',
        re.IGNORECASE | re.DOTALL | re.MULTILINE,
    )

    def strip_stale_substitutions(ini_text):
        return _STALE_BLOCK_RE.sub('', ini_text)

    # same line-start anchor for the same reason -- this file happens not to
    # have a commented "SachaWynter" example today, but nothing guarantees
    # that stays true, and the fix costs nothing.
    _SACHA_BLOCK_RE = re.compile(
        r'(^[ \t]*FontSubstitution\s+"SachaWynter"[^\n]*\n)(.*?)(\n[ \t]*End)',
        re.IGNORECASE | re.DOTALL | re.MULTILINE,
    )
    # +6pt on top of the requested size, not a straight 1:1 map -- SachaWynter
    # text (APT/Scaleform screens in particular, e.g. Options.apt, which
    # requests this font directly and isn't reachable through language.ini's
    # AudioSubtitleFont/MilitaryCaptionFont sizes at all) still read a bit
    # small once redirected to plain Albertus MT. Works for both table shapes
    # in the wild: the narrow 2-anchor "Size 1 = 1 / Size 500 = 500" range
    # table (interpolated, so shifting both anchors by +6 shifts every size
    # in between by ~+6 too) and the explicit per-size table.
    _SACHA_SIZE_BUMP = 10
    _SACHA_SIZE_LINE_RE = re.compile(r'Size\s+(\d+)\s*=\s*\d+\s+(?:"[^"]*"|\S+)')

    def retarget_sachawynter(ini_text):
        ini_text = strip_stale_substitutions(ini_text)
        def replace_block(m):
            header, body, end = m.group(1), m.group(2), m.group(3)
            new_body = _SACHA_SIZE_LINE_RE.sub(
                lambda sm: f'Size {sm.group(1)} = {int(sm.group(1)) + _SACHA_SIZE_BUMP} "Albertus MT"',
                body,
            )
            return header + new_body + end
        return _SACHA_BLOCK_RE.sub(replace_block, ini_text, count=1)

    # data\ini\fontsubstitution.ini (and language.ini) exist as SEPARATE
    # copies across multiple archives, and there is no proven rule for
    # which one wins for a given text element -- confirmed the hard way
    # (font_duplicate_fontsubstitution_WARNING in bfme1_localization.json):
    # patching only one copy left some UI (APT/Scaleform screens in
    # particular -- e.g. Options.apt requests the raw "SachaWynter" family
    # by name) still reading an unpatched copy. Always patch every copy of
    # fontsubstitution.ini/language.ini found in every auxiliary archive,
    # regardless of which we think "should" win -- exactly why this loop
    # uses find_all_paths_in_archive (not find_path_in_archive) for both.
    for patch_path in aux_archives:
        with open(patch_path, 'rb') as f:
            p_data = f.read()
        p_arc = Archive(p_data)
        changed = False

        str_path = find_path_in_archive(p_arc, r'data\lotr.str')
        if str_path:
            p_arc.remove_file(str_path)
            changed = True

        for fontsub_path in find_all_paths_in_archive(p_arc, r'\fontsubstitution.ini'):
            fontsub_txt = p_arc.read_file(fontsub_path).decode('latin-1')
            fontsub_txt = retarget_sachawynter(fontsub_txt)
            p_arc.remove_file(fontsub_path)
            p_arc.add_file(fontsub_path, fontsub_txt.encode('latin-1'))
            changed = True

        for aux_lang_ini_path in find_all_paths_in_archive(p_arc, r'\language.ini'):
            aux_lang_ini_txt = p_arc.read_file(aux_lang_ini_path).decode('latin-1')
            aux_lang_ini_txt = add_font_lines(aux_lang_ini_txt)
            p_arc.remove_file(aux_lang_ini_path)
            p_arc.add_file(aux_lang_ini_path, aux_lang_ini_txt.encode('latin-1'))
            changed = True

        if changed:
            p_arc.save(patch_path)
            ok_backup(f'{os.path.basename(patch_path)} patched')

    # ---- lang\<lang_folder>.big: full CSF + font + language.ini ----
    with open(lang_big, 'rb') as f:
        e_data = f.read()
    e_header = e_data[:4]
    e_arc = Archive(e_data)
    csf_path = find_path_in_archive(e_arc, r'\lotr.csf')
    lang_ini_path = find_path_in_archive(e_arc, r'\language.ini')
    if csf_path is None or lang_ini_path is None:
        raise RuntimeError(f'lang\\{lang_folder}.big is missing lotr.csf or language.ini -- not a normal language archive')

    existing_csf = e_arc.read_file(csf_path)
    labels, order = read_csf(existing_csf)
    for entry in entries:
        var = entry['var']
        text = entry.get(lang_field) or entry.get('en') or ''
        if var not in labels:
            order.append(var)
        labels[var] = text
    csf_bytes = build_csf(labels, order)

    e_lang_ini = e_arc.read_file(lang_ini_path).decode('latin-1')
    e_lang_ini = add_font_lines(e_lang_ini)
    # bump the tiny in-mission subtitle/caption sizes (AudioSubtitleFont
    # etc. ship at 8-9pt, which is legible in English but cramped and hard
    # to read once translated -- 2x reads far better, still fits)
    for role in ('AudioSubtitleFont', 'MilitaryCaptionFont', 'MilitaryCaptionTitleFont'):
        e_lang_ini = re.sub(
            rf'({role}\s*=\s*\S+\s+)(\d+)',
            lambda m: m.group(1) + str(round(int(m.group(2)) * 2.0)),
            e_lang_ini,
        )

    e_fontsub_path = find_path_in_archive(e_arc, r'\fontsubstitution.ini')
    if e_fontsub_path:
        e_fontsub_txt = e_arc.read_file(e_fontsub_path).decode('latin-1')
        e_fontsub_txt = retarget_sachawynter(e_fontsub_txt)
    else:
        e_fontsub_txt = None

    new_arc = Archive.empty(header=e_header.decode('ascii'))
    skip = {csf_path, lang_ini_path}
    if e_fontsub_path:
        skip.add(e_fontsub_path)
    # also drop any previously-embedded bfme_loc_*_font.* from an earlier run,
    # AND a stale "OmniaLTStd.ttf" entry left behind by the abandoned
    # SachaWynter->Omnia-LT-Std-clone approach this toolkit briefly tried
    for name in e_arc.file_list():
        if name in skip or name.startswith('bfme_loc_') or name.lower() == 'omnialtstd.ttf':
            continue
        new_arc.add_file(name, e_arc.read_file(name))
    new_arc.add_file(csf_path, csf_bytes)
    new_arc.add_file(lang_ini_path, e_lang_ini.encode('latin-1'))
    if e_fontsub_path:
        new_arc.add_file(e_fontsub_path, e_fontsub_txt.encode('latin-1'))
    if font_file:
        with open(os.path.join(lang_root, font_file), 'rb') as f:
            new_arc.add_file(embedded_font_name, f.read())
    if sacha_font_file:
        with open(os.path.join(lang_root, sacha_font_file), 'rb') as f:
            new_arc.add_file(embedded_sacha_font_name, f.read())
    new_arc.save(lang_big)
    with open(_text_source_marker(game_path, lang_folder), 'w', encoding='utf-8') as f:
        f.write(lang_dir)
    ok_backup(f'lang\\{lang_folder}.big rebuilt')
    print()
    ok(f'Done -- {len(entries)} labels applied ({meta["display_name"]}).')


def _backup_candidate_paths(game_path, lang_folder):
    """Every file this toolkit might have backed up (backup_once() always
    appends '.orig' to the exact path it patched) -- whichever _patch*.big
    archives are actually installed (2.22's _patch222.big, 1.06's
    _patch105.big/_patch106.big, or any future patch generation), plus
    ini.big and the two lang\\<lang_folder> archives. Discovered by name,
    not hardcoded to one patch generation, since which _patch*.big files
    exist depends entirely on the installed build."""
    names = list_patch_archives(game_path) + [
        os.path.join(game_path, 'ini.big'),
        os.path.join(game_path, 'lang', f'{lang_folder}.big'),
        os.path.join(game_path, 'lang', f'{lang_folder}audio.big'),
    ]
    return names


def has_backups(game_path, lang_folder):
    return any(os.path.exists(p + '.orig') for p in _backup_candidate_paths(game_path, lang_folder))


def restore_from_backup(game_path, lang_folder):
    restored = 0
    for p in _backup_candidate_paths(game_path, lang_folder):
        bak = p + '.orig'
        if os.path.exists(bak):
            shutil.copy2(bak, p)
            print(f'  restored {os.path.relpath(p, game_path)} from backup')
            restored += 1
    for marker, label in (
        (_text_source_marker(game_path, lang_folder), 'text'),
        (_audio_source_marker(game_path, lang_folder), 'voice-audio'),
    ):
        if os.path.exists(marker):
            os.remove(marker)
            print(f'  cleared {label} source marker (back to native)')

    print()
    ok(f'Done -- {restored} file(s) restored to their pre-patch original.')


def main():
    from banner import print_banner
    print_banner()
    game_path = find_game_path()
    reg_language = get_registry_language()
    lang_folder = resolve_active_lang_folder(game_path, reg_language)
    build = get_installed_build(game_path, lang_folder) if lang_folder else None

    labels = [
        ('GAME FOLDER', game_path),
        ('GAME LANGUAGE [IN REGISTRY]', reg_language if reg_language else 'unknown'),
        ('PATCHING', f'lang\\{lang_folder}.big' if lang_folder else 'unknown'),
        ('CURRENT PATCH', build if build else 'unknown'),
    ]
    if lang_folder:
        current_text = get_current_text_source(game_path, lang_folder, build) if build else 'unknown'
        labels.append(('CURRENT TEXT', current_text))
        labels.append(('CURRENT AUDIO', get_current_audio_source(game_path, lang_folder).capitalize()))
    from banner import print_info_table
    print_info_table(labels)
    print()

    if not lang_folder:
        print(f'Could not find lang\\{(reg_language or "english").lower()}.big or lang\\english.big -- aborting.')
        return

    if not build:
        print(f'Could not read the installed patch build from lang\\{lang_folder}.big -- aborting.')
        return

    available = list_available_builds()
    if build not in available:
        print(f'\nNo translations available yet for build {build}.')
        print(f'Available builds: {", ".join(available) if available else "(none)"}')
        print('Not applying anything -- wrong-build text would be worse than none.')
        return

    langs = list_languages(build)
    if not langs:
        print(f'locales\\{build}\\ exists but has no language subfolders.')
        return

    # ---- top-level menu: pick WHAT to change first (text and/or audio --
    # they're always physically separate archives, so any combination is
    # valid, e.g. Ukrainian text + French voice acting), review the pending
    # choice(s), THEN apply -- instead of forcing straight through both
    # pickers in one pass every time.
    pending_text = None   # (lang_dir, meta) or None = no change
    pending_audio = None  # pack name or None = no change

    while True:
        current_text = get_current_text_source(game_path, lang_folder, build)
        current_audio = get_current_audio_source(game_path, lang_folder)

        text_line = f'Change text  (current: {current_text}'
        if pending_text:
            text_line += f' -> {pending_text[1]["display_name"]}'
        text_line += ')'
        audio_line = f'Change audio (current: {current_audio.capitalize()}'
        if pending_audio:
            audio_line += f' -> {pending_audio.capitalize()}'
        audio_line += ')'

        print('\nWhat would you like to do?')
        print(f'  1) {text_line}')
        print(f'  2) {audio_line}')

        apply_opt = restore_opt = None
        next_num = 3
        if pending_text or pending_audio:
            apply_opt = str(next_num)
            print(f'  {apply_opt}) Apply the change(s) above')
            next_num += 1
        if has_backups(game_path, lang_folder):
            restore_opt = str(next_num)
            print(f'  {restore_opt}) Restore from backup (undo this toolkit\'s changes)')
            next_num += 1
        print('  0) Exit without applying')

        choice = input('\nPick a number: ').strip()

        if choice == '1':
            print('\nAvailable languages:')
            for i, (d, meta) in enumerate(langs, 1):
                print(f'  {i}) {meta["display_name"]}')
            sub = input('\nPick a number (Enter = cancel): ').strip()
            if sub:
                try:
                    pending_text = langs[int(sub) - 1]
                except (ValueError, IndexError):
                    print('Invalid choice.')
            continue

        if choice == '2':
            audio_packs = [p for p in list_audio_packs() if p != current_audio]
            if not audio_packs:
                print('No other voice packs available in locales\\audio\\.')
                continue
            print('\nAvailable voice packs:')
            for i, p in enumerate(audio_packs, 1):
                print(f'  {i}) {p.capitalize()}')
            sub = input('\nPick a number (Enter = cancel): ').strip()
            if sub:
                try:
                    pending_audio = audio_packs[int(sub) - 1]
                except (ValueError, IndexError):
                    print('Invalid choice.')
            continue

        if choice == '0':
            print('Exiting without applying anything.')
            return

        if restore_opt and choice == restore_opt:
            restore_from_backup(game_path, lang_folder)
            # back to native -- any pending (not-yet-applied) picks no
            # longer make sense to silently keep around, and the tool
            # stays open so the user can keep navigating the menu
            # (pick a fresh language/audio, apply again, restore again...)
            pending_text = None
            pending_audio = None
            continue

        if apply_opt and choice == apply_opt:
            print()
            print(f'Text  : {pending_text[1]["display_name"] if pending_text else current_text + " (unchanged)"}')
            print(f'Audio : {pending_audio.capitalize() if pending_audio else current_audio.capitalize() + " (unchanged)"}')
            # accept the Cyrillic look-alike too -- on a JCUKEN (RU/UA)
            # keyboard layout the physical key in the "y" position types
            # 'н' (and 'т' for "n"), so someone confirming without
            # checking their layout can easily type the wrong-looking
            # letter -- re-ask instead of silently cancelling on anything
            # unrecognized.
            confirmed = False
            while True:
                confirm = input('Apply this? (y/n): ').strip().lower()
                if confirm in ('y', 'yes', 'н', 'да'):
                    confirmed = True
                    break
                if confirm in ('n', 'no', 'т', 'ні', 'нет'):
                    print('Cancelled.')
                    break
                print('Answer not recognized, please type y or n.')
            if not confirmed:
                return

            if pending_text:
                lang_dir, meta = pending_text
                print(f'\nApplying {meta["display_name"]}...')
                apply_language(game_path, lang_folder, build, lang_dir, meta)
            if pending_audio:
                apply_audio_pack(game_path, lang_folder, pending_audio)
            return

        print('Invalid choice.')


if __name__ == '__main__':
    try:
        main()
    except Exception as e:
        print(f'\nERROR: {e}')
    input('\nPress Enter to exit...')
