# BFME1 Localization Toolkit — Architecture & Findings

Living reference doc. Last major update: 2026-09-03 (patch 1.06 multi-build
support, the `\n` newline bug, the ini.big/textures.big → `_patch106.big`
archive-priority experiment, HD Edition texture pack, pre-built FR/ES/DE/IT
`englishaudio.big` voice drop-ins, Nexus Mods packaging guide). Earlier:
2026-08-31 font-substitution overhaul, audio-pack mixing feature, FR/ES/DE/IT
text database.

**If you're picking this project up fresh, read in this order:** §1 (what the
toolkit is and how it's structured) → §4 (current state — what's actually done
per language/build) → §10 (what to hand someone on Nexus) → the rest as
reference/when something breaks. §2/§3/§6/§6.5/§6.6 are bug/finding logs —
skim them once so you don't rediscover the same traps.

---

## 1. What the toolkit does

`BFME-loc-toolkit/` is a standalone, distributable folder (ships its own
embeddable Python + vendored `pyBIG`) that patches a *live, already-2.22-patched*
BFME1 install with:

1. **Text** — merges a full translation (currently only `ua`) into the active
   language's CSF (`lang\<X>.big`'s `lotr.csf`), font-by-font as needed.
2. **Audio** — independently, can swap in a *different* language's voice pack
   on top of whatever text language is active (e.g. English text + French
   voices). Text and audio are always physically separate archives, so any
   combination is valid.

Entry point: `apply-localization.bat` → `scripts/apply_localization.py`.

### 1.1 Key files
- `scripts/apply_localization.py` — the whole toolkit logic, single file.
- `scripts/csf_tools.py` — CSF (binary) and `.str` (legacy text) parsers.
  A second copy lives at `bfme1/scripts/csf_tools.py` (used by ad-hoc
  analysis scripts outside the toolkit — `001_build_localized_big.py`,
  `002_add_movie_subtitles.py`, also in that folder) — **keep both in
  sync**, they've drifted before.
- `scripts/banner.py` — startup banner + the bordered info table.
- `locales/<build>/<lang>/` — one folder per (patch build, text language).
  Currently only `2.22v7.0.4/ua/`. Holds `strings.json` (var/en/ua/ru),
  `meta.json` (font files, display name), and the font files themselves.
- `locales/audio/<lang>/` — one folder per voice-pack language, holding
  `<lang>.big` (text/reference copy) + `<lang>audio.big` (the actual voice
  archive). **Purely filesystem-driven**: whichever subfolder has a
  `<name>audio.big` inside it becomes a selectable pack — nothing hardcoded.
  Currently: english, french, german, italian, russian, spanish (the ONLY
  confirmed real full dubs — see §3.6).
- `locales/textures/<lang>/` — 4 stock UI textures + splash screen per
  language, extracted for reference/archival purposes (not currently used
  by the apply flow).
- `bfme1_localization.json` (repo root, **not** inside BFME-loc-toolkit) —
  the master reference database, one entry per CSF label:
  `{var, en, ua, ru, fr, es}`. `ru` is currently empty everywhere (never
  populated). This file is NOT what the toolkit applies at runtime — that's
  `locales/2.22v7.0.4/ua/strings.json` — this is the broader research/
  reference copy, kept roughly in sync by hand.

### 1.2 The apply flow (current, as of the menu rewrite)
`main()`:
1. Locate game (registry `HKLM\...\Battle for Middle-earth`, `InstallPath`),
   detect active text language (`Language` reg value → `lang\<x>.big`),
   detect installed build (`Version:Format2` in the CSF, or `data\lotr.str`
   pre-patch — see §2.2).
2. Print a bordered info table (`banner.print_info_table`): game folder,
   registry language, which archive gets patched, detected build,
   **CURRENT TEXT** and **CURRENT AUDIO** (see §1.3 — these read sidecar
   marker files, not just the filename, so they stay accurate after mixing).
3. Menu loop: `1) Change text` → pick from `locales/<build>/`.
   `2) Change audio` → pick from `locales/audio/`. Both are independent,
   optional, reviewed together before a single `Apply this? (y/n)`
   confirmation (accepts `н`/`да`/`т`/`ні`/`нет` too — see §2.7).
   `Restore from backup` loops back to the menu afterward instead of exiting.
4. `apply_language()` — text: strips `data\lotr.str` from `_patch222.big`,
   merges CSF, retargets `SachaWynter`'s FontSubstitution (§2.4), embeds
   fonts, bumps subtitle sizes, writes a `.source` marker.
   `apply_audio_pack()` — audio: rebuilds `lang\<X>audio.big` from a
   different pack, rewriting only the internal path's language segment,
   writes a `.source` marker (§1.3).
5. Every touched file gets a one-time `.orig` backup before any edit.

### 1.3 The `.source` marker files
`lang\<X>.big.source` and `lang\<X>audio.big.source` — plain text sidecars
holding the actual applied language/pack name. Needed because the archive's
**filename** always matches whatever's active in the registry, regardless
of what content was actually mixed in (e.g. `englishaudio.big` can secretly
hold French voice lines). Without these, the toolkit has no way to display
an honest "what's currently installed" status. Cleared on restore.

---

## 2. Bugs found and fixed this session (chronological, root causes)

### 2.1 `.str` parser — 4 distinct desync bugs, all in `_STR_BLOCK_RE`
The legacy `data\lotr.str` override format silently desyncs (splices two
labels' text together, or drops a label as invisible) if the regex isn't
tolerant of real-world formatting quirks. Confirmed causes, all fixed:
1. `END` must match case-insensitively (some blocks ship as `End`).
2. Trailing whitespace **before** `END` (`"...text"  \r\nEND`).
3. Trailing whitespace **after** `END`/`End` (`END \r\n`) — this one kept
   resurfacing on fresh non-English installs (Italian, Spanish, German)
   because `_patch222.big` is the same physical file for every language,
   so the same handful of labels (`Color:Marsala`, `CONTROLBAR:ShatteredHope`,
   `CONTROLBAR:WretchedFate`, `Map:MAPMPFordsofIsenWinter`,
   `Map:MAPMPDorwinion*/Desc`) kept re-corrupting on every new test install
   until the regex was actually fixed (not just patched around).
4. Trailing whitespace in the **label name itself** (`'SCRIPT:scout1 '`) —
   the game looks labels up without the trailing space, so a mismatched key
   is invisible in-game (`MISSING: 'SCRIPT:scout1'`) even though the JSON
   has an entry, just under the wrong (untrimmed) key.

Current regex (both `csf_tools.py` copies):
```python
_STR_BLOCK_RE = re.compile(
    r'^(?P<label>[^\r\n]+?)\r?\n"(?P<text>.*?)"[ \t]*\r?\n[Ee][Nn][Dd][ \t]*\r?\n',
    re.MULTILINE | re.DOTALL,
)
```
Labels are `.rstrip()`-ed after capture.

### 2.2 `data\lotr.str` priority + the "no CSF fallback" trap
`data\lotr.str`, when present, overrides the CSF **per label**, but for
some namespaces (`APT:`, `LWA:`, `BANNERUI:`, likely others — never fully
enumerated) there is **no CSF fallback at all**: if the label isn't in
`.str`, the game shows `MISSING: 'label'` instead of checking the CSF.
Shipping a *partial* `.str` (even just the APT: labels) is strictly worse
than deleting it — you can never predict every namespace that needs it.
**Confirmed fix: delete `data\lotr.str` entirely** and make sure every
label lives in the CSF instead. This is what the toolkit does.

### 2.3 The "PUA icon" font myth — checked and debunked
Long-standing project assumption: `SachaWynter` (`sachwt__.ttf`) carries
Private-Use-Area decorative icon glyphs that a straight FontSubstitution
redirect to Albertus MT would destroy, so it was necessary to build a full
Cyrillic-extended clone of the original font instead. **This was checked
directly this session and is false**: dumping every glyph name in
`sachwt__.ttf` (fontTools) shows an entirely ordinary Western/Central
European character set. The only two Private-Use-Area codepoints
(0xF001/0xF002) are, rendered and visually confirmed, the "fi"/"fl"
typographic ligatures in the font's own gothic style — not icons.
**Current approach (matches the official Chinese/Thai localizations,
confirmed by direct inspection):** `FontSubstitution "SachaWynter"` is
retargeted straight to `"Albertus MT"` — no separate font file needed for
it at all. `sachawyntertight_ua.ttf` (the Cyrillic clone) is still shipped
and registered under its own name in case anything requests that literal
family, but nothing requires it for the redirect to work.

### 2.4 The catastrophic regex bug: eating the real SachaWynter block
While adding "strip a pre-existing `FontSubstitution "Albertus MT"` block"
(needed for Polish, see §3.3), the new regex wasn't anchored to real code
lines. The stock `fontsubstitution.ini`'s comment header includes a
**commented-out example** using that exact text
(`;   FontSubstitution "Albertus MT" ...`). The regex doesn't care about
the leading `;`, starts matching from inside the comment, and because a
commented `;   End` doesn't satisfy the closing pattern either, the
non-greedy match is forced to skip all the way down to the **real**
SachaWynter block's closing `End` — deleting the entire real substitution
block and everything between. Result: `_patch222.big`/`ini.big`'s
fontsubstitution.ini got truncated to just its 3-line comment header,
silently reverting all font fixes (garbled/tiny subtitles again).
**Fix:** anchor both `FontSubstitution` and the SachaWynter block regex to
`^[ \t]*` (line start, `re.MULTILINE`) so a `;`-prefixed comment line can
never match. **Lesson: any regex touching an `.ini`-style file must be
anchored against comments, always** — this exact bug class (matching text
inside a comment) is very easy to reintroduce.

### 2.5 The "Albertus MT → Arial" surprise (Polish)
Polish's own stock `fontsubstitution.ini` (unlike French/Italian/Spanish/
German) already ships a **native** `FontSubstitution "Albertus MT" → "Arial"`
block — presumably because stock Albertus MT lacks Polish diacritics. Since
our Cyrillic Albertus MT registers under that same family name, this
pre-existing rule silently redirected our font to Arial too, with no error
(different typeface, not garbled — this is why it was hard to spot: "menu
font looks different, not albertusmt_ua"). **Fix:** always strip any
pre-existing `FontSubstitution "Albertus MT"` block (see §2.4 for the
anchoring bug this introduced) — we always want our own font, never a
redirect away from it, regardless of what a given base language ships.

### 2.6 Fourth font: "Generals" (headertemplate.ini)
`headertemplate.ini`'s `Title`/`MainButton` templates use a `"Generals"`
font that is **not registered by any `LocalFontFile` line anywhere** —
found via a full archive scan when screen titles/big buttons rendered as
garbled runes. Briefly patched by adding a substitution to Albertus MT;
**this was reverted** once the direct SachaWynter→Albertus MT approach
(§2.3) turned out to fix everything, including this — the substitution
cleanup code (§2.4/2.5) explicitly strips any leftover `"Generals"` block
too, so a machine patched by an older toolkit version ends up clean.

### 2.7 Small robustness fixes
- **y/n confirmation** re-asks instead of silently cancelling on an
  unrecognized answer, and accepts the Cyrillic look-alikes typed by
  mistake on a JCUKEN keyboard layout (`н`/`да` = yes, `т`/`ні`/`нет` = no)
  — a `y` press became `н` under RU/UA layout and silently cancelled the
  whole apply.
- **Embeddable Python was missing `python310.zip`** (the compiled stdlib,
  including the `encodings` module) — the interpreter couldn't even boot,
  so `.bat` closed instantly with zero output, before the toolkit's own
  `try/except` could ever run. Recovered by downloading the official
  python.org embeddable distribution and copying just that file over.
  `.bat` now also checks the exit code and prints an explicit diagnostic +
  `pause` if the interpreter itself fails, instead of vanishing silently.
- **Hotkey markers**: several translations had `&` embedded directly before
  a *translated* Cyrillic letter (e.g. `&Замок`) instead of preserving the
  original **Latin** hotkey letter as a separate `(&X)` suffix. A Cyrillic
  letter can't function as a real keyboard accelerator on a Latin layout.
  Fixed 8 occurrences by extracting the true hotkey letter from the EN
  source and re-appending it as `(&X)`, matching the established
  convention used everywhere else in the database.

---

## 3. Key findings (not bugs in our code, but real discoveries about the game/patch)

### 3.1 `_patch222.big`'s fontsubstitution.ini exists in 3 places
`_patch222.big`, `ini.big` (both shared/global, same for every language),
and `lang\<X>.big`'s own copy. **No proven rule for which wins** if they
disagree — always patch all three, every time.

### 3.2 Non-English base + 2.22 = English text overlaid via `.str`
2.22's whole trick for supporting "French base + English 2.22 content" is:
the shared `_patch222.big` ships `data\lotr.str`, which **overrides the
CSF** with English text for anything the patch changed/added, regardless of
the base language's own CSF. Deleting `.str` (our fix, §2.2) means the
**base language's own CSF becomes authoritative again** — and for a
*handful* of labels that 2.22 genuinely never touches at all
(`Color:RohanGreen`, `CONTROLBAR:ToolTipEntAllies`,
`CONTROLBAR:ToolTipGandalfLeadership`, `CONTROLBAR:ToolTipBuildGondorFireStonePorter`,
`CONTROLBAR:ToolTipBuildGondorRangerHordeForGoodIthilien`), that CSF still
holds whatever language the base install itself shipped (confirmed: showed
French text on a French base, Italian on Italian, Spanish on Spanish,
German on German) — **not English**. `check_build_health()`'s "compare
against real English" model breaks down for exactly these vars, so they're
now hard-pinned (`PINNED_VARS` in `apply_localization.py`) — the
reconciliation step skips them entirely and trusts our already-verified
translation, rather than re-stomping it every time a new base language is
tested.

### 3.3 2.22's own vanilla base-language CSFs are NOT 2.22-aware
Directly disproved a wrong assumption: extracting the raw CSF from
`french.big`/`spanish.big` and diffing against known 2.22 balance values
shows **stale, pre-2.22 numbers** (e.g. French `SCRIPT:MEIsengard_...`
said "100 Uruks" where 2.22 English says "50") and, most tellingly,
`Version:Format2` is still the literal unpatched format-string placeholder
(`"Version %d.%02d"` / `"Versión %d.%02d"`) — proof these CSFs were never
touched by anything 2.22-aware. **2.22 has no real updated French or
Spanish translation** — what looks "translated" in a normal (non-toolkit)
non-English install is only the `data\lotr.str` English overlay (§3.2)
masking it. Confirmed by the user from independent community knowledge.

### 3.4 Bogus `ENDUPGRADE:RohanHorseBow` artifact — recurring
A `.str`-parsing split artifact (duplicates the real `UPGRADE:RohanHorseBow`
entry, always with the SAME meaning translated into whatever base language
was active) kept reappearing across different test installs even after the
underlying regex bugs (§2.1) were fixed — evidently the source `.str` bytes
themselves are just malformed for this one label, not a parser bug.
Now hard-blocked (`BLACKLIST_VARS`) — `check_build_health()` refuses to
ever re-add it, and also actively purges it from `entries` if it's already
snuck in from an older run.

### 3.5 Turkish "voice pack" is a byte-for-byte copy of English
Full archive scan (all 7371 files) of `turkishaudio.big` vs a genuine
`englishaudio.big`: **100% identical SHA1 hashes**, every single file.
Not a real dub — someone repackaged the English audio under Turkish paths,
likely just to make the archive "exist" with the right structure/size.
(An earlier spot-check against Russian audio showed differences and
wrongly seemed to disprove this — the correct comparison needed a genuine
English reference, which wasn't available until later in the session.)

### 3.6 Partial/fake "dubs": which languages actually have a full VO
Checked file sizes and content directly:
- **Real, full dubs** (~400 MB, thousands of unique per-line files):
  English, French, German, Italian, Russian, Spanish.
- **Text-only, ~2 MB "dub"** (just ~76 files — world-map narrator lines,
  nothing else; real gameplay dialogue is confirmed silent in these):
  Polish, Norwegian, Dutch, Swedish. Their own `language.ini` even
  explicitly declares `AudioLanguage = English`, confirming this is by the
  base game's own design, not a broken file — these languages were always
  meant to fall back to English VO except for that narrator layer. (There
  is a shared root `audio.big`, ~300 MB, that's *always* loaded regardless
  of active language, but it holds only generic sound effects/ambience —
  **no mission dialogue at all** — so the fallback for text-only languages
  is genuinely silent for anything beyond that narrator layer, not filled
  in from anywhere else.)
- **Turkish**: fake, see §3.5.

`locales/audio/` only keeps the 6 confirmed-real dubs — the picker in the
toolkit is purely filesystem-driven (§1.1) specifically so a fake/partial
pack never has to be special-cased in code, just removed from the folder.

### 3.7 Two archive-priority facts (empirically confirmed, not assumed)
- **Per-language archives win over shared ones.** Official RU's entire font
  fix lives 100% inside `lang\russian.big` — it never touches
  `_patch222.big`/`ini.big` at all, and it works. Confirmed structurally
  (their `language.ini`'s `LocalFontFile` lines and their
  `fontsubstitution.ini`'s retarget are both inside the per-language
  archive only).
- **A `LocalFontFile` filename collision is resolved by which line comes
  later in `language.ini`.** Registering a Cyrillic font under a brand-new
  name (`bfme_loc_ua_omniafont.ttf`) alongside the stock
  `LocalFontFile = OmniaLTStd.ttf` line left it ambiguous which one wins
  for the family "Omnia LT Std". The official RU approach (and now ours,
  where applicable) avoids the ambiguity entirely by shipping the
  replacement font under the **exact stock filename** instead, so it
  shadows the original by filename rather than competing on family name.

### 3.8 Compiled APT/Scaleform UI assets bypass `language.ini` entirely
`Options.apt` (and presumably other `apt\*.big` screens) embed raw font
family name strings directly in the compiled binary (confirmed: literal
ASCII `"SachaWynter"` found via byte search in `Options.apt`). These
screens' fonts are controlled **only** by `FontSubstitution` rules — they
never go through `headertemplate.ini`'s named templates at all. This is
why the world-map narration / settings-screen titles kept breaking
independently of whatever `language.ini`/`headertemplate.ini` fix was
tried — the actual fix always had to be a `FontSubstitution` rule.

---

## 4. Current state (2026-08-31, 1.06 bullet added 2026-09-03)

- **Ukrainian**: fully translated and wired into the toolkit
  (`locales/2.22v7.0.4/ua/`), including the ~300+ entry batch translated
  this session, terminology passes (Клацніть→Клікніть, істота→одиниця in
  mechanic contexts, seconds abbreviated to "сек."), and hotkey fixes.
- **French / Spanish**: `bfme1_localization.json` has complete `fr`/`es`
  fields for all 8672 entries (vanilla CSF merged + balance numbers
  corrected to match 2.22 + ~719 entries per language translated from
  scratch where the vanilla base never had them), **and both are now wired
  into the toolkit** as selectable text options
  (`locales/2.22v7.0.4/fr/`, `locales/2.22v7.0.4/es/` — `strings.json` +
  `meta.json`, generated straight from the master database). Confirmed
  working end-to-end against a live English install (menu lists all three
  languages, applies cleanly, `check_build_health()` runs and self-corrects
  as expected).
  - `apply_language()`'s font handling is now conditional
    (`meta.get('font_file')`/`meta.get('sacha_font_file')`, both optional):
    French/Spanish ship **no font_file at all** — standard Latin + accents
    (é, ñ, ü...) is exactly what the stock Albertus MT already covers (it's
    what EA's own original European localizations shipped with), so unlike
    Ukrainian these two don't need any font touched.
  - Testing surfaced 2 more of the same §3.2 "vanilla leftover, base
    install text ≠ real 2.22 English" casualties
    (`UPGRADE:StoneworkerUpgradeToUseFireArrows`,
    `CONTROLBAR:ToolTipEomerLeadership`) — translated properly (not just
    pinned) for both fr and es, in both `bfme1_localization.json` and the
    respective `locales/2.22v7.0.4/<lang>/strings.json`. Not added to
    `PINNED_VARS` since these aren't vanilla-only labels 2.22 skips
    entirely (unlike the UA-discovered set) — they were just genuinely
    stale in the vanilla CSF's own text and needed a one-time fix, the
    same as the earlier balance-number corrections.
  - A same-instance sanity scan afterward turned up ~440 more `fr==en` /
    `es==en` entries that look alarming in bulk but are legitimate: EA's
    own vanilla release never localized certain content into French/Spanish
    at all — internal dev/QA test strings (`GUI:TEST`, `MSG:Testing` =
    "Mary had a little lamb..."), and proper nouns (`Aragorn`, `Gondor`,
    `Osgiliath`...) that are correctly identical across languages by
    design. Not a bug, same category as Ukrainian's own ~74-entry
    "legitimately neutral" set, just larger because vanilla French/Spanish
    had more gaps to begin with (§3.3).
- **German / Italian**: same treatment as French/Spanish, same session
  (follow-up pass). `bfme1_localization.json` has complete `de`/`it` fields
  for all 8672 entries — vanilla CSF merged (`lang\german.big` /
  `lang\italian.big`, 7953 labels each, confirmed genuinely pristine
  pre-2.22 via their own `Version:Format2` placeholders: `'Version
  %d.%02d'` / `'Versione %d.%02d'`), balance numbers corrected (52 German,
  66 Italian fixes), the ~209-entry `Map:*` template+prose set translated
  (114 auto + 95 hand-translated prose sentences, same set as every other
  language since it's the same underlying vanilla-CSF gap), and the same
  506-entry gameplay/UI batch (`CONTROLBAR`/`OBJECT`/`UPGRADE`/`SCRIPT`/
  `BONUSROUND`/`TOOLTIP`/T3A:Online-UI) translated from scratch against the
  2.22-accurate `en` field. **Both wired into the toolkit**
  (`locales/2.22v7.0.4/de/`, `locales/2.22v7.0.4/it/` — `strings.json` +
  `meta.json`, generated from the master DB exactly like fr/es), confirmed
  picked up automatically by `list_languages()`'s filesystem scan (no code
  changes needed — `de`/`it`/`es`/`fr`/`ua` all list correctly). Same 4
  leftover neutral/empty entries filled
  (`TOOLTIP:.../popupLocale/Accept/buttonClip` → "Akzeptieren"/"Accetta",
  `Buttonclip`/`disableButton`/`SCRIPT:hero` → `''`), `Version:Format2`
  fixed to the literal `en` value for both. No font_file needed for either
  (same reasoning as fr/es — standard Latin + accented characters only:
  ä/ö/ü/ß for German, à/è/é/ì/ò/ù for Italian, both already covered by
  stock Albertus MT).
  - The known `UPGRADE:StoneworkerUpgradeToUseFireArrows` /
    `CONTROLBAR:ToolTipEomerLeadership` casualty pair (§ above, same class
    as the balance-number fixes — stale vanilla CSF text, not a 2.22-skip)
    was checked directly against the master DB without needing a live
    install and confirmed present for de/it too (same truncated/wrong-%
    vanilla fragments as fr/es originally had) — fixed the same way,
    translated properly against the 2.22-accurate `en` value, in both
    `bfme1_localization.json` and the regenerated
    `locales/2.22v7.0.4/<lang>/strings.json` (fr/es `strings.json` were
    regenerated from the master at the same time, so all four stay in
    sync).
  - **Not yet verified end-to-end against a live install** (unlike fr/es):
    the cached `game_path.txt` install (`F:\BFME1`) no longer has
    `_patch222.big` present at the time this pass ran, so
    `get_installed_build()` can't identify a supported build there and the
    toolkit's own path prompt loops asking for a valid one. This is an
    environment/install-state fact, not a defect in the de/it data itself.
    Worth a real live-install smoke test (menu lists all 5 languages,
    applies cleanly, `check_build_health()` finds 0 "FULLY REWRITTEN"
    lines) the next time a 2.22-patched install is available.
- **Audio packs**: English/French/German/Italian/Russian/Spanish voice
  archives + textures archived in `locales/audio/` and `locales/textures/`,
  independently selectable via the toolkit's audio-pack menu.
- `ru` field in `bfme1_localization.json`: still empty everywhere, never
  populated this session. Wiring it into the toolkit would follow the exact
  same recipe as §5 below, once populated.
- **Patch 1.06, Ukrainian** (2026-09-02/03, see §6 onward for the full
  story): the toolkit now detects and supports 1.06 installs generically
  (not hardcoded — any future patch generation is handled the same way,
  §6.2). `locales/1.06/ua/strings.json` is fully translated — 0 remaining
  English-fallback entries beyond ~65 genuinely untranslatable technical
  placeholders (letters/digits/URLs/format strings/easter-egg dev names,
  confirmed by inspection each time, not assumed) — verified applied for
  real against two *different* actual 1.06 installs (§6.6 found they don't
  share one fixed English baseline; both were reconciled and translated).
  German/Italian/French/Spanish were **not** extended to 1.06 this pass —
  only 2.22 has fr/es/de/it; 1.06 only has ua. Pre-built FR/ES/DE/IT
  drop-in `englishaudio.big` voice packs exist for 1.06 regardless (§9 —
  audio pack selection is independent of which text languages are wired
  up for a build). An archive-priority experiment (§7) that would let a
  1.06 UA package skip touching `ini.big`/`textures.big` entirely is
  implemented but **still awaiting an in-game visual confirmation** — see
  §7 before assuming it's safe to rely on. §10 has the exact file list for
  packaging either way.

## 5. Recipe: adding another text language to the toolkit

1. Get a genuine vanilla CSF for that language (`lang\<X>.big`'s
   `lotr.csf`) — **never assume it's 2.22-accurate** (§3.3), always diff a
   few known-changed balance values and check `Version:Format2` first.
2. Merge into `bfme1_localization.json` as a new field (matching the
   `en`/`ua`/`fr`/`es` pattern), fix balance-number drift
   (`_numbers_only_diff`-style substitution), translate whatever's
   genuinely missing (labels 2.22 added that the vanilla base never had).
3. Generate `locales/2.22v7.0.4/<lang>/strings.json` from the master
   (`{var, en, <lang_code>, ru}` per entry — the field name MUST equal
   `meta.json`'s `lang_code`, `apply_language()` looks it up by that key).
4. Write `meta.json`: `lang_code`, `display_name`, and **only** `font_file`/
   `sacha_font_file` if that language's alphabet needs glyphs the stock
   Albertus MT lacks (Cyrillic, etc.) — both are optional, omit entirely
   for any Latin-alphabet-with-accents language.
5. Apply once against a live install and read the console output: any
   "FULLY REWRITTEN" casualties are real content that needs a proper
   translation (not just pinning) unless they match the §3.2 vanilla-
   leftover pattern exactly (i.e. 2.22 never touches that label in ANY
   language) — check whether they're already in `PINNED_VARS` before
   assuming a new pin is needed.

## 6. Multi-build support: patch 1.06 (2026-09-02)

The toolkit originally hardcoded `_patch222.big` as THE patch archive
everywhere (path detection, build-string reading, the whole write path) —
it silently refused to even recognize a valid BFME1 install that wasn't on
2.22 (`find_game_path()` gated on `_patch222.big` existing at all, and
would loop forever re-asking for a path on a clean 1.06 install). This
section documents making the whole pipeline build-generic, using a real
clean-English 1.06 install as the second data point (previously only 2.22
had ever been exercised).

### 6.1 What actually differs between 2.22 and 1.06's archive layout

2.22 keeps *everything* patch-related in one `_patch222.big`: the
`data\lotr.str` English text overlay, **and** a duplicate
`data\ini\fontsubstitution.ini`, **and** a duplicate `data\ini\language.ini`
(the actual runtime-priority winner over the base `lang\<X>.big` copies of
each, confirmed empirically, see §3.7). 1.06 splits the exact same three
responsibilities across **two** separate archives instead:

| role | 2.22 | 1.06 |
|---|---|---|
| `data\lotr.str` English text overlay | `_patch222.big` | `_patch106.big` |
| duplicate `fontsubstitution.ini` | `_patch222.big` (`data\ini\...`) + `ini.big` | `_patch105.big` (`lang\english\fontsubstitution.ini` — note the *different path prefix*) + `ini.big` |
| duplicate `language.ini` (LocalFontFile registration) | `_patch222.big` (`data\ini\language.ini` only) | `_patch105.big` — **two** copies: `data\ini\language.ini` AND `lang\english\language.ini` |

`_patch106.big` carries *only* the `.str` overlay — no font-related files
at all. `_patch105.big` carries the font-related files but no `.str`.
Confirmed by dumping every archive's entry list and diffing against what
`apply_language()` was reading — nothing here was guessed.

The build-token string itself is a different shape too: 2.22's
`data\lotr.str`'s `Version:Format2` reads `"Patch 2.22v7.0.4"`; 1.06's own
`data\lotr.str` (yes — the same label lives in the *text overlay*, not
just the CSF, on both) reads `"Version T3A 1.06"` — no `Patch` prefix, no
`v`-separated build suffix, just a bare `X.YZ`. `_extract_build_token()`
only recognized the `v`-suffixed shape; it now also accepts any
digit-leading token containing a `.`, which covers both without breaking
the 2.22 case.

### 6.2 The fix: stop hardcoding, discover instead

Six places hardcoded `_patch222.big` by name:
`find_game_path_from_registry()`/`find_game_path()` (gate on the archive's
mere *existence* to accept a folder at all — now checks for `lotrbfme.exe`
instead, via `_is_valid_game_folder()`, since that's actually build-
independent), `get_installed_build()` and `get_build_baseline_en()` (read
`.str` from exactly that one archive), the whole font/str-patching block
in `apply_language()`, and `has_backups()`/`restore_from_backup()`.

All six now go through one new helper, `list_patch_archives(game_path)` —
a `glob.glob('_patch*.big')` over the install root, sorted for
determinism. Wherever the old code did something to `_patch222.big`
specifically, the new code loops over every archive `list_patch_archives()`
finds and does the same thing to whichever entries actually exist in each
one (a second new helper, `find_all_paths_in_archive()`, returns *every*
matching entry by suffix, not just the first — needed because `_patch105.big`
carries two `language.ini` copies at different paths, where the original
`find_path_in_archive()` would have silently only patched one). An archive
with none of the three relevant files (`_patch106textures.big`, e.g. — it's
a pure texture patch, matches the `_patch*.big` glob but contributes
nothing) is left completely untouched (still gets a `.orig` backup taken
up front alongside everything else, out of caution, but is never rewritten
since nothing in it changes — the `changed` flag stays `False`).

This is genuinely future-proof, not just "now also handles 1.06 specifically"
— *any* patch generation that ships its overrides via one or more
`_patch*.big` archives is handled automatically, whatever it's named and
whatever it puts where, with zero further code changes.

### 6.3 Building `locales/1.06/ua/`

Rather than translate 1.06 from scratch, `locales/1.06/ua/strings.json`
was generated by taking the existing, complete
`locales/2.22v7.0.4/ua/strings.json` (8671 entries) and running it through
the *exact same reconciliation `check_build_health()` already does on
every live apply* — but offline, against `en` baseline text read straight
from the real 1.06 install (`get_build_baseline_en()`), never touching the
install's files. Where 1.06's English text matches 2.22's exactly
(normalized), the 2.22 Ukrainian translation carries over unchanged. Pure
balance-number or appended-tail differences were auto-adjusted the same
way a live apply would. Result:

- **0** labels present in the 1.06 baseline that weren't already covered
  (1.06 is *older* than 2.22, so its label set is a subset — nothing new
  to add).
- **25** labels auto-corrected (balance numbers / appended build-time
  lines).
- **46** labels were a casing-only difference, ignored.
- **355** labels (~4%) came back genuinely different in wording/mechanics
  — confirmed by hand via a diagnostic dump (not assumed): older/different
  balance values (`ToolTipToggleWargLineToSkirmishFormation`: 2.22's
  "-20% Armor, +20% Damage" vs 1.06's "No bonus" — the whole *mechanic*
  didn't exist yet), renamed abilities/objects (`OBJECT:IsengardWildman`:
  "Wildman of Dunland" vs 1.06's "Isengard Wildman"), rewritten mission
  objectives (entire early-campaign objective text is different at 1.06),
  and encoding artifacts fixed upstream by 2.22 (`GUI:EACopyright`'s `©`
  was literally mangled to `ï¿½` in whatever the 2.22-era CSF had cached).
  This is real content drift between patch generations, not a bug in the
  reconciliation. **Update: all 355 translated** (same session, follow-up
  pass) — a fresh terminology glossary was pulled straight from the
  existing 2.22 UA data (grepping for how it already renders "Required:
  Rank X" / "Passive ability" / "Left click then right click on target" /
  "Revive the fallen Hero, X" / building & unit names / map-description
  template fields, etc.) before translating, so the 1.06-only content
  matches the established UA voice exactly rather than introducing a
  second, inconsistent style. Applied and verified directly in the
  rebuilt `lang\english.big` CSF against the live 1.06 install. The only
  remaining `ua == en` entries (64) are legitimately untranslatable
  technical placeholders (`LETTER:G`, `NUMBER:1`, URL/format-string
  labels, `Shift+`/`Alt+`/`Ctrl+`, resolution strings, and a handful of
  easter-egg developer names like `ItziTeaTyme`/`ya_boy_goku`) — confirmed
  by inspection, not assumed.

`locales/1.06/ua/meta.json` mirrors `2.22v7.0.4/ua/meta.json` exactly
(same Cyrillic `font.otf`/`sachawyntertight_ua.ttf` — the font-substitution
mechanism needed zero build-specific changes once §6.2's archive discovery
was generic) — `font.otf` and `sachawyntertight_ua.ttf` were physically
copied into the new folder since `apply_language()` loads font files
relative to `locales/<build>/<lang>/`.

### 6.4 Verified end-to-end against a real 1.06 install

Applied for real against a clean-English 1.06 install (the same one used
to extract the baseline) — `get_installed_build()` correctly read `"1.06"`,
`locales/1.06/` showed up in the menu, `check_build_health()` re-ran at
apply time and reported **zero** further drift (proof the offline
reconciliation in §6.3 used the exact same baseline the live apply path
does), all three auxiliary archives got patched
(`_patch105.big`/`_patch106.big`/`ini.big`), `lang\english.big` was
rebuilt with 8672 labels, and the embedded font entries
(`bfme_loc_ua_font.otf`, `bfme_loc_ua_sachafont.ttf`) came out exactly as
expected. Spot-checked the rebuilt CSF directly: `CHAT:Buddies` →
"КОМУНІКАТОР" (real translation, reused from 2.22 UA since the English
matched), `Version:Format2` → baked to the literal `"Version T3A 1.06"`
string (this specific label is itself one of the 355 English-fallback
casualties — cosmetic, low priority).

**Not yet done**: translating the 355 English-fallback entries against
1.06's actual wording (§6.3). `apply-localization.bat` itself needed no
changes — it's a thin launcher with no build-specific logic at all; the
detection failure the user hit lived entirely in
`apply_localization.py`.

### 6.5 Bug found via in-game screenshot: literal `\n` instead of a line break

After the first live 1.06 apply above, the user sent an in-game screenshot
of Aragorn's Athelas tooltip showing the ability name correctly translated
("Ателас (T)") but its effect line rendering as literal text:
`Heals nearby friendly heroes \n left click to activate` — with a visible
backslash-n instead of a line break, and in English instead of Ukrainian.
Traced to **two separate bugs**, both about the same underlying confusion
(`.str`'s own line-break convention is the literal two characters `\`+`n`,
not a real newline byte — `_normalize_text()` already converts one to the
other for *comparison* purposes, but nothing was converting it for
anything actually *persisted*):

1. **New, introduced by §6.2/§6.3's work this session**: `check_build_health()`
   computed `base_norm = _normalize_text(base_en)` for comparing against our
   stored text, but every branch that *writes* `entry['en']` /
   `entry[lang_field]` (the `added`, `casing_synced`, `number_synced`,
   `append_synced`, and `rewritten_synced` cases) used the raw,
   still-`.str`-escaped `base_en` instead of the normalized form. Any label
   reconciled through one of those paths ended up with a literal `\n` baked
   into its stored text — invisible in the console summary (which only
   prints counts), but very visible in-game the moment that label's text
   was ever actually displayed. `CONTROLBAR:TooltipAthelas` was one of the
   355 "rewritten -> English fallback" labels from §6.3, so it hit this
   exactly. **Fixed**: `base_en` is now normalized once, at the top of the
   loop, before anything derives from it — every write site now stores the
   normalized form.
2. **Old, pre-existing, unrelated to 1.06 or this session**: a scan of
   `bfme1_localization.json` turned up **398** entries (out of 8672) whose
   `en` field *already* had this exact same literal-`\n` bug baked in
   directly — all under `TOOLTIP:OnlineShell/...` (multiplayer chat/friend
   list) and a couple of `CONTROLBAR:ToolTip...Formation` labels, all
   clustered together, strongly suggesting a single historical bulk-import
   from a raw `.str` source, before this session, that never got
   unescaped. Confirmed via character-code inspection (not just eyeballing
   `repr()` output, which is easy to misread here — a real newline and a
   literal `\`+`n` both *display* as `\n` in a naive glance, they only
   differ in whether `repr()` needs to escape one extra backslash).
   Crucially this was **`en`-only** — every already-translated field
   (`ua`, `fr`, `es`, `de`, `it`, `ru`) was clean for all 398, so it was
   invisible in every language that has real translation coverage for
   those labels; it would only have surfaced the same way §6.5.1 did, the
   next time any language's build fell back to English for one of these
   398 specific labels. **Fixed**: unescaped all 398 directly in
   `bfme1_localization.json`, then regenerated every already-shipped
   `locales/2.22v7.0.4/<lang>/strings.json` (fr/es/de/it) from the
   corrected master DB, and patched `locales/2.22v7.0.4/ua/strings.json`
   in place the same way (it isn't machine-generated from the master DB).

Verified clean afterward with a careful character-code-level scan (not a
naive substring match against `repr()` output) across every
`locales/*/*/strings.json` — zero literal `\`+`n` sequences left anywhere.
Rebuilt `locales/1.06/ua/strings.json` from scratch against a freshly
`restore_from_backup()`'d pristine 1.06 install (needed since
`check_build_health()` refuses to reconcile against an install this
toolkit already patched — the live files no longer hold real English to
compare against) using the now-fixed code, and re-applied it for real:
confirmed directly in the rebuilt `lang\english.big` CSF that
`CONTROLBAR:TooltipAthelas` now carries a real newline.

### 6.6 "1.06" is not one fixed English baseline — a platform re-verify
proved it, and surfaced a real encoding quirk in the source data

After §6.5's fix shipped, the user's platform did a file-integrity
verify/repair ("clean update") on the install. This reset `lang\english.big`
back to bone-stock (matching the very first pristine check from early in
the 1.06 work, byte for byte) **but left `_patch105.big`/`_patch106.big`
completely alone** — they still carried our font retarget / `.str` strip
from before. Net effect: only the CSF+font archive needs rebuilding after
an event like this, not the whole pipeline — but re-running the *full*
`apply_language()` blindly would be wrong (see below), and — more
importantly — the "fresh" English text turned out to differ slightly from
what had been reconciled against before, meaning **the same nominal "1.06"
label can correspond to more than one real-world English baseline**,
depending on exactly where/how the install got its files. This is a real
property of the target, not a bug — plan for a live apply to occasionally
surface a small new batch of drifted labels even on a build string you've
already fully translated once.

**Rebuilding just `lang\english.big` safely.** `apply_language()`'s
aux-archive loop (§6.2) is driven by `list_patch_archives()`, but `ini.big`
is appended to `aux_archives` **unconditionally** by a separate hardcoded
`if os.path.exists(ini_big): aux_archives.append(ini_big)` line — a
monkeypatch of `list_patch_archives()` alone does *not* stop `ini.big` from
being re-touched. Re-running the full flow against an install where
`_patch105.big` is *already* retargeted would re-apply
`retarget_sachawynter()`'s `+10`pt SachaWynter size bump **a second time**
(cumulative, not idempotent) — a real corruption risk on repeated re-applies
that was caught by inspection, not by symptom. The safe recipe used:
monkeypatch `list_patch_archives` to return `[]` for the call, **and**
temporarily `os.rename()` `ini.big` out of the way for the duration of the
`apply_language()` call (renamed back in a `finally:` block) — this
guarantees `ini.big` is never even opened, and the aux loop does nothing at
all, so only the `lang\<lang_folder>.big` CSF+font rebuild step runs. See
`rebuild_lang_only_v2.py` in this session's scratch history for the exact
pattern; worth promoting into a real `--rebuild-lang-only` toolkit mode if
this keeps coming up.

**What actually drifted this time**, found via a proper JSON-level diff
(not a naive line-count) against the known 355+64 already-accounted-for
vars:
- **13 brand-new labels** never seen as fallback before: `Color:Pink`,
  three `TOOLTIP:OnlineShell/OnlineLogin/...` registration strings,
  `CONTROLBAR:ConstructCastle`/`ConstructCamp`/`ConstructOutpost`, and six
  `APT:` online-menu labels (`DisconnectRules`, `OnlineEAAccountName`,
  `Password`, `ServiceTerms`, `OfficialSite`, `ESRBNotice`).
- **11 already-translated labels whose English text itself changed again**
  on this specific install (`CONTROLBAR:EyeofSauron`/`ToolTipEyeofSauron`
  gained a `+50% Armor` clause it didn't have before; four Hero `Recruit`
  tooltips lost their `Command Points` tail; five tutorial subtitles).
- **The URLs are a smoking gun for "different lineage" 1.06 installs**:
  `URL:LotrHome`/`LotrLadder`/`LotrTOS` pointed at `online.the3rdage.net`
  (the T3A community service) on the first install, and at
  `eagames.com`/`gamespy.com`/`ea.com` (EA's own 2004-era, long-dead
  addresses) on this freshly-verified one — these are genuinely different
  distributions of "1.06", not a fluke.

**Real encoding bug found in the source data (not ours):** five of the
tutorial subtitles contained raw byte values `0x92`/`0x93`/`0x94`/`0x96`
sitting directly in the decoded CSF text — the Windows-1252 codes for a
right single quote (’), left/right double quotes (“ ”), and an en dash (–)
respectively. Confirmed by inspecting character codes directly (`ord(c)`
per character), not by eyeballing — a real newline and this kind of raw
byte both look identical at a glance in a `repr()` dump, exactly the trap
§6.5 already flagged once for a different reason. **This is authored-in
directly in EA's own CSF for this build**: someone typed the original
English text with "smart quotes" in a Windows-1252 editor, and whatever
produced the retail CSF preserved those exact byte values as literal
low-byte code points instead of mapping them to the correct Unicode
characters (U+2019/U+201C/U+201D/U+2013). Both `en` (cleaned to the real
Unicode characters) and `ua` (translated properly, off the cleaned text)
were fixed for all five. **If this shows up again** (any language, any
build): it's always going to be one of `0x91`/`0x92` (single quotes),
`0x93`/`0x94` (double quotes), `0x96`/`0x97` (en/em dash), `0x85`
(ellipsis) — the classic Windows-1252 "smart punctuation" range — map to
the proper Unicode character before translating, never carry the raw byte
through.

All 24 translated using the same glossary-first method as §6.3's original
355, verified applied for real in the rebuilt CSF, `ini.big`/`textures.big`
confirmed untouched (`filecmp.cmp` against `.orig`, byte-for-byte) after
the rebuild-only recipe above.

---

## 7. Experiment: moving `ini.big`/`textures.big`'s overrides into `_patch106.big`

**Status: applied, structurally verified, NOT yet visually confirmed
in-game.** Treat as a hypothesis under test, not an established fact, until
someone actually launches the game and checks both items below.

**The idea:** `ini.big`'s duplicate `fontsubstitution.ini` and
`textures.big`'s `lmtext.png` (loading-screen text overlay) were originally
patched in place, directly inside those two archives (13 MB and 224 MB
respectively — both huge, both otherwise-untouched base-game files). If
BFME1's archive loader gives a later-loaded `_patch*.big` priority over the
base `.big`s for an identically-pathed entry (the same mechanism already
established for `.str` overriding the CSF, §3.2/§6.1), the same override
could instead live inside the much smaller `_patch106.big` — meaning a
distributable mod package would never need to touch (or redistribute)
`ini.big`/`textures.big` at all.

**What was done:** extracted the *already-correct* (retargeted/UA) bytes
for `data\ini\fontsubstitution.ini` and `art\textures\lmtext.png` straight
out of the live, already-patched `ini.big`/`textures.big`, reverted both of
those archives to their true `.orig` (confirmed byte-identical afterward),
then added both files as new entries into `_patch106.big` at their
*original, unchanged relative paths* (`data\ini\fontsubstitution.ini`,
`art\textures\lmtext.png`) via `pyBIG.LargeArchive.add_file()`. Structural
verification only: `_patch106.big` grew from 68 → 70 entries, its copy of
`fontsubstitution.ini` decodes with the real `Albertus MT` retarget and no
stock `SachaWynterTight` line, its `lmtext.png` is byte-identical to the
UA-translated texture. `ini.big`/`textures.big` are byte-identical to
their own `.orig`.

**What still needs eyes-on confirmation, in-game:**
1. Any screen that used to render via SachaWynter (Options.apt and similar
   — see §3.8, these bypass `language.ini` and go through
   `FontSubstitution` rules directly) still shows proper Albertus MT, not
   a garbled/fallback font.
2. The loading screen shows the Ukrainian `lmtext.png` overlay, not the
   original English one still sitting untouched in `textures.big`.

If both hold: the recipe for **every future language/build** on this
toolkit should route new `fontsubstitution.ini`/texture overrides through
the highest-numbered `_patch*.big` present, and §10's packaging list
shrinks by ~237 MB. If either fails: revert `_patch106.big` from its own
`.orig` (predates this experiment) and go back to patching
`ini.big`/`textures.big` directly, like the original §6.1–§6.4 flow did.

**`lmtext` alpha-channel trap, found while preparing the replacement
texture (worth remembering for any future loading-screen text swap):** the
vanilla `lmtext` asset ships as **two** sibling files in `textures.big` —
`lmtext.jpg` (opaque RGB) and `lmtext.png` (RGBA). The `.dds` source
extracted from the Ukrainian fan patch that was used as the replacement
is ~99% fully transparent (alpha `0` for ~99% of pixels, topping out at
`128` — half-opacity — only where the actual glyphs are) — it's a text
overlay meant to sit on top of a loading video/image, not a standalone
picture. Converting straight to JPEG (which has no alpha channel) would
have silently discarded exactly the transparency that makes it usable,
leaving a solid block instead of an overlay. **Only `lmtext.png` was
replaced; `lmtext.jpg` was deliberately left untouched** — if the engine
turns out to actually read the `.jpg` sibling for this asset (unconfirmed,
same "which copy does the engine really use" uncertainty as §3.1's
"patch every copy, don't guess" caveat), that one still needs a properly
flattened (e.g. composited onto a solid background, not just alpha-dropped)
JPEG built from the same source before it'll show anything correct.

---

## 8. Separate HD Edition texture pack (`F:\BFME1HD\HDEditionv1.0.big`)

A **completely separate, optional** install/archive from the base
`F:\BFME1` game — a fan-made "HD Edition" texture replacement pack living
in its own folder, loaded via the game's `-mod "<path to .big>"` launch
argument rather than by touching the base install at all. Two textures
inside it were swapped for the Ukrainian-patch equivalents:

- `art\textures\logowithshadow.tga` — **two** copies exist inside this one
  archive at different paths (`art\textures\logowithshadow.tga` and
  `lang\english\art\textures\logowithshadow.tga`) — both replaced with the
  UA logo, byte-identical, verified by direct re-read after save.
- `art\textures\load_w_ea.jpg` — the archive only carries a `.jpg` here
  (no `.tga` entry exists in this pack, unlike the source `.tga` we had),
  so the replacement had to be converted `.tga` → JPEG first (Pillow,
  quality 95, no alpha needed — this asset is opaque, unlike `lmtext`
  above) before injecting.
- `art\textures\lmtext.dds`/`.png`/`.jpg` — **this archive has no `lmtext`
  entry of any kind.** Only the *base* game's `textures.big` (§7) has one.
  Don't go looking for it here.

Backed up first (`HDEditionv1.0.big.orig`, standard `.orig`-before-any-edit
convention). Note the file **grew** by ~10 MB after the edit
(172,412,999 → 182,293,570 bytes) — expected, not a bug: `pyBIG` doesn't
try to match the original compression of whatever entries it rewrites, it
just stores the new bytes; a swapped-in PNG/TGA/JPEG can legitimately be
larger than whatever the original archive-internal representation was.

**Launcher**: `F:\BFME1\Play HD Edition.bat` — a thin wrapper around
`lotrbfme.exe -mod "<path>\HD\BTFME1_HD.big"` (the user's own chosen
folder/filename inside the base game folder, **not** the original
`F:\BFME1HD\HDEditionv1.0.big` path — same file, just physically relocated
and renamed by the user afterward). Built with `%~dp0`-relative paths (so
it keeps working if the whole `F:\BFME1` folder is ever moved to a
different drive/path) and existence checks for both the exe and the mod
archive with a friendly error + `pause` instead of silently doing nothing
if either is missing — same philosophy as the hardened `apply-localization.bat`
(§2.7).

---

## 9. Pre-built drop-in voice packs for 1.06 (`locales/1.06/lang/{FR,ES,DE,IT}/`)

Goal: let someone get "Ukrainian text + French/Spanish/German/Italian
voices" on the English-registry/`english`-lang-folder 1.06 install **by
copying one file**, with zero registry changes and zero use of the
interactive toolkit menu — useful for a Nexus package that wants to offer
voice-pack variants as separate optional downloads.

**How:** exactly the transformation `apply_audio_pack()` already does at
apply time (rewrite every entry's `lang\<PackLanguage>\...` prefix to
`lang\English\...`), just pre-baked into a standalone file instead of
written straight into a live game's `lang\` folder. Source: the existing
`locales/audio/<lang>/<lang>audio.big` packs (§3.6 — these are the 6
confirmed-real, non-fake dubs). Output:
`locales/1.06/lang/FR/englishaudio.big` (414 MB),
`.../ES/englishaudio.big` (420 MB), `.../DE/englishaudio.big` (406 MB),
`.../IT/englishaudio.big` (419 MB) — each one a straight drop-in
replacement for `F:\BFME1\lang\englishaudio.big`.

**Verified content-complete, not just "ran without error":** built a
proper case-insensitive path diff (see the trap below) between each output
pack and the reference English pack. Result: every single one of the
7370 audio files in each FR/ES/DE/IT pack has an exact 1:1 counterpart in
English, and vice versa — the *only* file present in English and absent
elsewhere is `data\audio\sounds\empty.txt`, which isn't audio at all (a
placeholder/filler entry). **Nothing is missing, and 1.06 requires no
voice lines these vanilla-sourced dubs don't already have** — 1.06 predates
any dialogue-adding content patch, so there's no "1.06-only" line that a
stock non-English dub could conceivably lack.

**Case-sensitivity trap (cost one wasted comparison pass — the first,
naive diff falsely showed 100% mismatch, zero overlap, for every pack):**
the saved `englishaudio.big` stores every internal path in **all
lowercase** (`lang\english\data\audio\sounds\ecalcam_losea.wav`), while
French/Spanish/German/Italian's own packs use `MixedCase`
(`lang\French\Data\audio\sounds\ECAlCam_losea.wav`). A case-sensitive
string-set comparison between the two sees zero shared filenames even
though the actual underlying files are identical (BIG archive paths are
case-insensitive to the engine, same "archives are NOT consistent about
casing" fact `find_path_in_archive()`'s own docstring already flags for
CSF/`.ini` entries) — always `.lower()` full paths before diffing archive
contents across two different source packs, not just when reading a single
archive's own entries.

**Why total archive size differs per language** (405–420 MB across the
four, ~410 MB for English) despite every pack having the exact same file
count: purely natural — the same line recorded in different languages by
different voice actors simply runs a different length. Not missing or
truncated content; confirmed by comparing summed `.wav` byte totals
per-file-matched, not just archive size.

---

## 10. Packaging for distribution (Nexus Mods or similar)

**Text + font + UA logo/loading-screen, for a 1.06 install** (assuming §7's
archive-priority experiment is confirmed working in-game — see that
section's two pending checks before relying on this shorter list):
- `lang\english.big`
- `_patch105.big`
- `_patch106.big`

If §7 turns out **not** to hold (SachaWynter or the loading screen breaks),
fall back to the original 5-file set instead:
- `lang\english.big`, `_patch105.big`, `_patch106.big`, `ini.big`,
  `textures.big`

**Never include in a distributed package:**
- Any `*.orig` file — these are this toolkit's own local pre-edit safety
  backups (`backup_once()`), meaningless (and potentially confusing —
  they're *pristine* copies) to a third party.
- `lang\<X>.big.source` / `lang\<X>audio.big.source` — internal
  bookkeeping for the toolkit's own "what's actually installed" status
  display (§1.3), not consumed by the game.
- `.hidden_tmp`-suffixed files — a transient artifact of the §6.6
  rebuild-only technique if it's ever interrupted mid-run; shouldn't exist
  in a clean state, but check before zipping.

**Optional, separate, HD Edition texture pack** (§8) — entirely independent
of the base-game package above, only relevant to someone who also has the
separate HD Edition install:
- `HDEditionv1.0.big` (only if the logo/texture swap is wanted)
- `Play HD Edition.bat` (only meaningful alongside it, and only if it's
  placed at the exact relative location the `.bat` expects — see §8)

**Optional, separate, voice-pack variants** (§9) — one file each, entirely
independent of everything else, drop-in replacements for
`lang\englishaudio.big`:
- `locales/1.06/lang/FR/englishaudio.big` (French voices)
- `locales/1.06/lang/ES/englishaudio.big` (Spanish voices)
- `locales/1.06/lang/DE/englishaudio.big` (German voices)
- `locales/1.06/lang/IT/englishaudio.big` (Italian voices)

**How "which files were actually touched" was determined, every time, for
this whole session** — worth reusing as a technique, not just trusting
memory of what was edited: `filecmp.cmp(path, path + '.orig',
shallow=False)` against every archive `backup_once()` could plausibly have
touched. `shallow=False` matters — a shallow compare only checks file
size/mtime and would happily call two different files "the same" if they
happened to end up the same size.

**A general packaging caveat worth restating from §6.6:** "1.06" is not
one fixed thing — different real installs of a build carrying that exact
same version string can have slightly different English baseline text
(confirmed: different community-service vs. EA-original URLs on two
different real installs this session). A package built and verified
against one specific 1.06 install may show a small number of English-
fallback labels on a *different* 1.06 install. This isn't fixable in
general — the fix, when it happens, is always the same §6.3/§6.6
reconcile-then-translate cycle, not a sign anything is broken.
