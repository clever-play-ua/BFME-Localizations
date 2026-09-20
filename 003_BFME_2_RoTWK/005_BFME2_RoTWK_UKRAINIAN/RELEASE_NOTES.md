# RotWK Ukrainian — release notes / development history

**Status: done, not beta.** The working, confirmed-in-game recipe is
`release/build.py` → `release/french.big` + `release/frenchpatch201.big`.
Deploy those two files into a `french` 2.01 install's `lang\` folder (see
`release/build.py`'s own docstring for exact steps and prerequisites).

**For the general RotWK text/font engine reference (why this recipe looks
the way it does, applicable to localizing RotWK into any language) see
`../ROTWK_TEXT_AND_FONT_SYSTEM.md` — read that first.** Everything below
this line is the blow-by-blow session history that led there: how the
`.str`/`english`-slot approach was tried first, every wrong turn along the
way (CSF-in-`english` failing, the `"Generals"` dead end, the `ini.big`
crash, the `UnicodeFontName` discovery), kept for the record but superseded
by the clean reference doc for anything you need to *do* rather than
*understand historically*.

---

Companion to `002_BFME_2/005_BFME2_UKRAINIAN/BETA_PATCH_NOTES.md` — RotWK runs
on the exact same engine as BFME2 and the same fix transfers directly.
Session 2026-09-19, against a confirmed-clean vanilla 2.01 install at
`F:\RotWK`.

`beta/` (superseded — see `release/` instead, above) held the first result:
`english.big` + `englishpatch201.big`, ready to drop into a stock 2.01
install's `lang\` folder (same "patch the English slot in place" strategy
as BFME2 — no registry changes). `beta/build_beta_english_big.py`
rebuilds both from scratch from a pristine source.

## 1. Structural parity with BFME2 — confirmed, not assumed

Checked directly, byte-for-byte where possible, before touching anything:
- `lang\english.big` / `lang\englishpatch201.big` layout is identical to
  BFME2's `english.big`/`englishpatch105.big` — same 7 files, same
  `data\lotr.str`-only text (no CSF), same codepage-dependent mojibake risk.
- `language.ini` is **byte-for-byte identical** to BFME2's — same
  `LocalFontFile` lines, same font-role assignments (Albertus MT / SachaWynter).
- Font bytes live in `data1.big` (`albertusmt.otf`, `omnialtstd.ttf`,
  `sachwt__.ttf`) — same as BFME2.
- `data\ini\fontsubstitution.ini` lives only in `ini.big` (RotWK has no
  second copy in `maps.big`, unlike BFME2 — doesn't matter, our fix never
  touches the shared ini.big/maps.big archives anyway).
- Registry: `HKLM\...\The Lord of the Rings, The Rise of the Witch-king`
  (irrelevant here — we patch the English slot directly).

Because of this parity, `beta/fonts/AlbertusMTUA.otf` and
`sachawyntertight_ua.ttf` are **reused directly from
`002_BFME_2/005_BFME2_UKRAINIAN/beta/fonts/`** — not rebuilt.

## 2. Pre-existing translation assets found, and a serious bug in one of them

`005_BFME2_RoTWK_UKRAINIAN/` already had `lotr.csf` and `lotr.str` before
this session (origin unknown/older work). Both claim ~13,000 labels.

**`lotr.csf` has a real, baked-in double-encoding bug — do not use it as a
source.** Confirmed directly: reading it correctly (per the CSF spec:
UTF-16LE with every byte bit-inverted — verified this reader itself works,
via a clean round-trip test) produces garbled text like
`'РђСЂР°Т‘РѕСЂРЅ'` for what should be `'Араґорн'`. This is **not** a display
artifact (redisplaying the exact same bytes through a Windows/cp1251 console
by coincidence produces the correct-looking text, which is what made this
look fine on a first glance — always verify Cyrillic text via a file written
with explicit `encoding='utf-8'`, never trust a console redirect for this).
The actual mechanism: `original_text.encode('cp1251').decode('utf-8') ==
original_text` for the labels checked — i.e. whoever built this CSF took
correct UTF-8 Ukrainian text and ran it through a CP1251 decode step by
mistake before encoding it into the CSF's UTF-16LE form.

**`lotr.str` is fine** — checked directly, it decodes cleanly as UTF-8 with
no errors, and spot-checked labels read correctly. It has essentially none
of BFME2's `// context:` comment-line problem (2 stray `//` lines in the
whole file, negligible). **This session's build reads the translation from
`lotr.str`, not `lotr.csf`.** `lotr.csf` should not be trusted or reused
until someone rebuilds it properly from this `.str`.

One additional **content** bug, unrelated to encoding, found by inspection:
`GUI:FullGameName` in `lotr.str` resolves to `"Кільценосець"` ("Ring-bearer")
— clearly not a game title, most likely a value that got attached to the
wrong label somewhere in this file's own prior history. Overridden directly
in `beta/build_beta_english_big.py`'s source data (see
`RotWK_strings_ua.json`) rather than left as-is.

**Given two independent, unrelated bugs were found in under an hour of
spot-checking, treat the rest of this ~13,000-label translation as
unaudited** — it has not been through anything like the hunspell/г-ґ/
consistency QA pipeline `002_BFME_2/005_BFME2_UKRAINIAN/QA_NOTES.md`
documents for BFME2. Worth doing eventually, not done this session.

Also notable, not a bug: `Version:Format2` reads `"2.02 Версія 9.0.0"` —
this text is baked directly into the pre-existing translation and suggests
it was originally built against a different RotWK distribution (2.02? a
community patch labeled 9.0.0?) than the vanilla 2.01 this session tested
against. Left as-is (real content, not something to silently overwrite).

## 3. Reconciling the pre-existing translation against a real clean 2.01

Compared the pre-existing translation's label set against the actual keys
read from a confirmed-clean `F:\RotWK\lang\englishpatch201.big`:

- Live 2.01 English: **12,627** unique keys.
- Pre-existing UA translation: **12,992** unique keys.
- Shared: 12,556. **Missing from UA (needed translation): 71.** UA-only
  (not in this 2.01 at all — presumably content from whatever other RotWK
  build this translation was built against): 436, kept anyway (harmless,
  unused by vanilla 2.01, same "don't remove, only add" policy as BFME2).

Of the 71 missing:
- **49 filled by reuse** — identical English source text already exists
  (word-for-word) in `002_BFME_2/005_BFME2_UKRAINIAN/BFME2_strings_ua.json`
  (shared multiplayer maps, CREDITS role titles, a couple of tooltips) — the
  already-QA'd BFME2 Ukrainian text was reused directly.
- **22 translated fresh this session** — mostly the War of the Ring
  strategic-mode tutorial subtitles (`DIALOGEVENT:WOTR_Tutorial087/091/092/094/098/105subtitle`),
  a few Angmar/Arnor unit plural labels, 2 new multiplayer maps (Stonewain
  Valley, Nanduhirion), Mount Gundabad, and `GUI:FullGameName` (see the bug
  above). Not run through the hunspell/terminology QA pipeline — same
  caveat as the pre-existing 12,556.

Merged result saved as `RotWK_strings_ua.json` (13,095 entries — mirrors the
shape of `BFME2_strings_ua.json`) — this, not `lotr.csf`/`lotr.str`
directly, is what `build_beta_english_big.py` reads from now.

## 4. Textures

Reused directly from `006_LOCALIZED_LOGOS/RoTWK_LOGOS/009_UA/`:
`load_w_ea.jpg`, `logowithshadow.tga`, `titlescreenuserinterface.jpg`.

**Not included: `art\compiledtextures\lm\lm_text.dds`** (the loading-screen
text overlay — same asset class as BFME2's `lmtext`, see that game's
`BETA_PATCH_NOTES.md` §4). RotWK's own `textures2.big` does have this file
at the same path, but no Ukrainian version of it exists anywhere in this
repo yet (`009_UA/` has no `lm_text.dds`, unlike BFME2's prototype folder
which did). Loading-screen text stays in English until someone builds this
asset — everything else (menus, tooltips, dialogue, the three textures
above) is in Ukrainian.

## 5. Fonts

Identical technique to BFME2's beta (§3 there has the full "three attempts"
story) — went straight to the final, correct approach since it was already
proven: `AlbertusMTUA.otf` (renamed family, avoids the same-family collision
ambiguity) + `sachawyntertight_ua.ttf`, both added fresh into
`lang\english.big` only, with a real `FontSubstitution` rule for each
pointing at these distinct family names. `ini.big` was never touched.

## 6. Version string

`Version:Format2`/`Format3` — left as the pre-existing translation's own
`"2.02 Версія 9.0.0"`-style text rather than overwritten with the BFME2
beta's "UA 0.1 Clever Play" branding, since this file's version string
already carries real (if puzzling) content from wherever it originally came
from. Revisit once the "what build was this actually translated against"
question (§2) is resolved.

## 7. Deployed and verified

`beta/english.big` + `beta/englishpatch201.big` copied into
`F:\RotWK\lang\`. Verified directly from the deployed files (not just the
build output): `OBJECT:GondorAragorn` → `Араґорн`, `GUI:FullGameName` →
correct title, tutorial subtitle text reads correctly, `fontsubstitution.ini`
and the two new `LocalFontFile` lines are present exactly as intended.
**Not yet confirmed with an actual screenshot in-game** — BFME2's own font
switch needed two iterations before it visually worked (see that game's
notes §3), so treat this as a first cut needing the same in-game check
BFME2 got, not as done.

Backups of the pristine files (`english.big`, `englishpatch201.big`,
`englishaudio.big`) live at `F:\RotWK\lang_backup_original\`.

## 8. Open questions

- What RotWK build/patch is the pre-existing translation actually from (the
  "2.02 Версія 9.0.0" / 436 extra map-and-unit keys)? Answering this would
  explain (and let someone properly re-verify) more of the file than the two
  bugs found by spot-checking alone.
- `lm_text.dds` (§4) still needs a Ukrainian version built.
- `lotr.csf` is now confirmed **dead weight for RotWK** (see §9) — the repo's
  copy of it (`005_BFME2_RoTWK_UKRAINIAN/lotr.csf`) is the original,
  double-encoding-bugged one from §2, still unused by anything. Candidate for
  deletion so nobody reaches for it by mistake.
- **§10's ornate-title mojibake** — plan is to install a working official
  Russian RotWK localization (session 2026-09-20+) and inspect how it solves
  this, since Russian has the exact same single-byte-vs-Cyrillic problem we
  do. Specifically worth checking: does its `lang\` archive ship a `lotr.csf`
  alongside `.str` (i.e. a mixed system, CSF for specific wide-char-only
  widgets + `.str` for everything else)? Does its `language.ini` touch
  `UnicodeFontName` or add any `LocalFontFile`/font-role entry we haven't
  tried? Does the same "Special Powers" panel title actually work there, or
  is it a known/accepted limitation in every fan translation of this game?

## 9. The real fix — RotWK does not read CSF at all; `.str` needs a strict,
## single-line, single-byte-codepage format (in-game confirmed working)

Everything above (§1–§8) reflects the first pass, which turned out to be
based on two wrong assumptions carried over from BFME2 without re-checking
them against RotWK specifically. First deploy attempt (CSF-based, mirroring
BFME2's own working fix exactly) produced **zero visible change** — the
entire main menu stayed in English, plus two literal `MISSING:
'APT:Expansion1Campaign'` / `MISSING: 'APT:BonusCampaign'` engine errors.
Root-caused by direct, empirical testing (not by inspecting any other
language's reference files):

**1. RotWK's engine (`lotrbfme2ep1.exe`) does not read `lotr.csf` at all.**
Confirmed two ways: (a) independent community sources say BFME2/RotWK moved
to `.str` and dropped CSF, which is a BFME1-only format; (b) directly built a
CSF with verified-correct content for both "missing" labels
(`APT:Expansion1Campaign` = `'АНҐМАРСЬКА КАМПАНІЯ'`,
`APT:BonusCampaign` = `'ЕПІЛОГ'`) and it still didn't show — if the engine
had read the CSF at all, these two specific labels would have displayed
correctly even if everything else were somehow broken. It didn't, so the
CSF path is simply never consulted. **Do not use CSF for RotWK, at all.**

**2. `data\lotr.str` is what the engine actually reads, with its own strict,
native parser — not the lenient regex-based reader this toolkict uses.**
Proven by deploying the pre-existing `lotr.str` verbatim (unmodified) inside
`english.big`/`englishpatch201.big`: the game did not just fail silently, it
**crashed on startup** with an in-engine error dialog:
`End quotes missing for string 'STRATEGICHUD:FarmStructureArchetypeTooltip'
in file 'data\lotr.str', line 25454`. That label's value contained a **raw,
unescaped line break** in the middle of the quoted text (a real `\r\n`
instead of the literal two-character escape sequence `\n`) — something
BFME1's lenient block regex (used by `str_tools_bfme2.read_str_bfme2`)
silently tolerates by matching across the line break, but the real game
parser requires the entire quoted value to sit on **one physical line**.

A full scan of `RotWK_strings_ua.json` for the same two defect classes
found this was not an isolated typo but systemic, in the pre-existing
translation this file was built from (apparently authored for a 2.02 build,
per §2's version-string finding, whose parser may have been more forgiving):
- **2 labels** with a raw embedded line break instead of `\n`.
- **215 labels** with a raw, unescaped `"` character inside the text (e.g.
  `клацніть на кнопці "Прийняти"`) — never written as the required `\"`.
  Any one of these would have crashed the game the same way once reached.

Fixed globally (see `RotWK_strings_ua.json`'s values, re-derived into
`lotr_fixed.str` — script: ask for `fix_rotwk_str.py`'s logic if rebuilding,
not checked into the repo, trivial to reproduce): real line breaks become
literal `\n`; any `"` not already preceded by a backslash becomes `\"`.
Verified after the fix: 0 remaining raw quotes, 0 remaining multi-line
quoted values, round-trips cleanly through the reader.

**3. Even with valid `.str` syntax, the file must be encoded as `cp1251`,
not UTF-8.** With a syntactically-valid but UTF-8-encoded `.str`, the game
stopped crashing and text appeared everywhere — but as mojibake (repeating
`ğ`, `¢`, `¬`-style Latin/Turkish-lookalike characters, not tofu boxes or
missing glyphs). That specific pattern is the signature of a Western/Turkish
single-byte codepage (e.g. `cp1254`) misreading UTF-8's multi-byte lead
bytes (`0xD0`/`0xD1`, common to nearly all Cyrillic letters) as individual
characters — i.e. the engine reads `data\lotr.str` through
`MultiByteToWideChar(CP_ACP, ...)` (the classic SAGE-engine convention), not
as UTF-8. This machine's system ANSI codepage is `1251`
(`HKLM\SYSTEM\CurrentControlSet\Control\Nls\CodePage\ACP`), which fully
covers the Ukrainian alphabet including ґ/і/ї/є. Re-encoding
`data\lotr.str` as `cp1251` (keeping the same fixed content from step 2)
fixed it completely.

**Confirmed working in-game** (screenshot, 2026-09-19): RotWK splash/menu
renders correct Ukrainian text with the custom Cyrillic fonts, no crash, no
`MISSING:` errors, no mojibake.

**Practical takeaway for future work on this file:** rebuild
`data\lotr.str` from `RotWK_strings_ua.json` — plain `.str`, `cp1251`-encoded,
via `str_tools_bfme2.build_str_bfme2()` — and never touch/ship `lotr.csf`
for RotWK. Any newly-added or edited translation text must avoid a literal
line break (use `\n`) and must escape any embedded `"` as `\"`, since the
game's parser has no tolerance for either.

## 10. One remaining cosmetic bug — an ornate panel-title widget mojibakes,
## root cause mathematically proven, no fix found yet

Everything above works: menus, tooltips, dialogue, unit names, all correct
Ukrainian with the custom fonts. One exception, screenshot 2026-09-19 (the
"Special Powers"/palantir ability-purchase panel): the big stylized panel
title renders as `×àêëóâàííÿ` instead of `Чаклування`
(`APT:SpecialPowersTitle`, `en: "Special Powers"`). Everything else on that
same screen — "СИЛА:", the ability tooltip text, the "СКИНУТИ"/"ПРИЙНЯТИ"
buttons — renders correctly.

Ruled out, each confirmed directly rather than assumed:
- **Not missing glyphs.** `sachawyntertight_ua.ttf`'s cmap (platform 3,
  Windows, the table the engine actually reads) has all 10 characters of
  "Чаклування", identical coverage to `AlbertusMTUA.otf` which works fine
  elsewhere.
- **Not corrupted data.** The deployed `data\lotr.str`'s raw bytes for
  `APT:SpecialPowersTitle` are `d7e0eaebf3e2e0ededff` — byte-for-byte the
  correct cp1251 encoding of "Чаклування". Confirmed by direct hex dump of
  the live deployed archive, not just the build output.
- **Not our FontSubstitution rule.** Its `SachaWynter` block is structurally
  identical to the pattern BFME2 already uses (`Size 8 = 12` / `Size 40 = 70`
  → `SachaWynterTight`) - same two anchor points, same target font.

**Root cause, proven by arithmetic, not guessed:** cp1251 byte values for
"Чаклування" are `D7 E0 EA EB F3 E2 E0 ED ED FF`. Widening each byte
*directly* to the Unicode code point of the same number (i.e. decoding as
Latin-1/`cp1252`, not translating through the cp1251 code-page table) gives
exactly `×àêëóâàííÿ` — a character-for-character match with what's on
screen. This specific widget is doing something like `WCHAR ch = (unsigned
char)byte` per character instead of a real `MultiByteToWideChar(1251, ...)`
call. `language.ini` has a separate `UnicodeFontName = "Arial Unicode MS"`
entry (line 9) that nothing else in this file references — plausibly this
ornate-title widget is one of a small number of legacy/special text fields
wired to a wide-char-only code path inherited from BFME1's CSF era, and
whatever glues our narrow (`.str`) string into it does the naive per-byte
widen instead of a proper codepage-aware conversion.

**Why this can't be fixed by re-encoding the file:** a single byte maxes out
at `0xFF` (255); Cyrillic Unicode starts at `U+0400` (1024). If this widget
really does a direct numeric byte-to-codepoint widen, there is no possible
single-byte source encoding that could ever produce a correct Cyrillic
codepoint through it - not cp1251, not anything else. This is not a
data/font/ini problem on our end; it would need either a genuinely
wide-char-fed source for this one label, or an engine-side fix neither of
which we have a lead on yet.

**Next step (planned, not yet done):** install a working official Russian
RotWK localization and inspect how *it* handles this - Russian hits the
identical single-byte-vs-Cyrillic wall we do. Worth checking specifically:
does its `lang\` archive carry a `lotr.csf` *alongside* `.str` (suggesting a
mixed system - CSF only for the handful of wide-char-locked widgets like
this one, `.str` for everything else)? Does its `language.ini` do anything
with `UnicodeFontName` or add a font role this session hasn't tried? Or does
the same panel simply show the same kind of mojibake there too (i.e. a
known, accepted limitation across every fan translation of this game, not
something we're missing)? See §8.

## 11. Inspected the official Russian 2.1 localization - reopens the CSF
## question, and the stock font situation is not what §9/§10 assumed

Session 2026-09-20. User did a **full clean reinstall** of RotWK as vanilla
Russian 2.1 (not just swapping `lang\` files - `data1.big` etc. are this
release's own, not the English 2.01 ones §1-§10 were built against) and
asked to inspect its encoding setup directly.

Findings, from the actual shipped archives (`F:\RotWK\lang\russian.big`,
`russianpatch201.big`):

- **It ships `lotr.csf` at archive root - and *no* `data\lotr.str` at all.**
  This directly contradicts §9's conclusion that "RotWK's engine does not
  read `lotr.csf` at all" - an official, working localization is CSF-only.
  Something in this session's own earlier CSF deploy attempt must have been
  the actual cause of that failure (the language.ini edit and/or the
  fontsubstitution.ini addition made *alongside* the CSF in that attempt are
  the prime suspects, not CSF itself) - **not yet re-tested**, since this
  install is Russian now, not the English 2.01 the earlier attempt used.
- **It adds zero custom font files and does not touch `fontsubstitution.ini`
  at all.** `language.ini` is nearly byte-identical to English's (same
  `LocalFontFile = AlbertusMT.otf` / `omnialtstd.ttf`, nothing added).
- **Checked the actual stock font files in *this Russian release's*
  `data1.big` directly (fontTools cmap inspection, not assumed):**
  `albertusmt.otf` already has real Cyrillic glyphs (66/256 of the Cyrillic
  block; all 10 characters of a test word "Чаклування" present) - **out of
  the box, no modification.** `omnialtstd.ttf` and `sachwt__.ttf` (the
  `SachaWynter` role) have **zero** Cyrillic coverage, even in this official
  release.
- Whether the English 2.01 install's own `data1.big`/`albertusmt.otf` (the
  one §1-§10's custom `AlbertusMTUA.otf` was built to replace) *also*
  already had Cyrillic and the custom font was never actually necessary is
  now an open question - that install is gone (overwritten by this
  reinstall) and was never checked this way before building a replacement.
  Re-check once English 2.01 is back.

**Interpretation:** the `SachaWynter`-rendered ornate panel title bug from
§10 is very likely **not a bug introduced by this translation at all** - the
official Russian localization's own stock `SachaWynter`-mapped font has no
Cyrillic either, so it almost certainly shows the same kind of broken text
for that one widget even in the shipped, EA-approved release. Whatever is
special about that widget (§10's "direct byte-widen" finding) is a
pre-existing engine/font limitation nobody has actually fixed - Russian
just never got a Cyrillic `SachaWynter` either, they only fixed `Albertus
MT`.

**User's decision, going forward (session 2026-09-20, continuing):** stop
chasing a real fix for that one widget. Once a clean English 2.01 is
reinstalled: rebuild "clean" - redirect whatever font role the ornate panel
title actually uses away from `SachaWynter` and onto `AlbertusMTUA`
instead, sidestepping the broken role entirely rather than trying to give
`SachaWynter` real Cyrillic glyphs. Also worth re-testing a **minimal
CSF-only** deploy (no font/ini changes at all, mirroring the Russian
archive's shape exactly) against a fresh English 2.01, to settle whether
CSF genuinely works for RotWK's "english" slot once nothing else in the
archive is changed alongside it.

## 12. Clean rebuild, no custom fonts at all (deployed, current state)

Session 2026-09-20, continued, against a freshly-reinstalled clean English
2.01 (`F:\RotWK`, `lang\` backed up again to `lang_backup_original\`).

**Checked the fresh install's own stock `data1.big\albertusmt.otf` directly
before doing anything else** - same fontTools cmap check as §11 did for the
Russian release. Result: **identical** - 66/256 Cyrillic block coverage, all
10 characters of a test word present, completely unmodified. This confirms
§11's suspicion: the custom `AlbertusMTUA.otf` built earlier in this session
(and reused from BFME2) was solving a problem RotWK's stock font doesn't
actually have. Only `SachaWynter`/`sachwt__.ttf` has zero Cyrillic coverage,
confirmed in every install checked (English 2.01 fresh, English 2.01
previous, Russian 2.1 official).

**`build_beta_english_big.py` rewritten (third revision) to match:**
- `data\lotr.str` - unchanged from §9's approach (cp1251, built from
  `RotWK_strings_ua.json` via `str_tools_bfme2.build_str_bfme2()`), still the
  proven-working text path. `lotr.csf` still never added (§9's finding
  stands as this build's basis; §11's contradicting Russian-CSF-only
  evidence is noted there as something to separately re-test, not yet
  incorporated into this build).
- **No custom font files at all** - `AlbertusMTUA.otf` and
  `sachawyntertight_ua.ttf` dropped entirely. No `language.ini` edit either
  (nothing new to register - stock `Albertus MT` is already registered and
  already Cyrillic).
- `data\ini\fontsubstitution.ini`: a single rule,
  `FontSubstitution "SachaWynter" -> "Albertus MT"` (the stock family, not a
  custom one), same `Size 8 = 12` / `Size 40 = 70` anchor pattern as every
  version of this rule so far.
- Textures: unchanged (§4).

Deployed archive's file list, verified directly: `data\lotr.str`,
`data\ini\fontsubstitution.ini`, the 3 textures, plus the untouched stock
files - no font files, `language.ini` byte-identical to stock. Simpler and
smaller than every prior revision.

**Correction, same session, minutes later:** the above prediction was wrong,
and worse than expected - a screenshot showed the ENTIRE main menu had
reverted to garbled text (e.g. the Skirmish button showed as raw Latin-1-
widened garbage, exactly §10's byte-arithmetic pattern), not just the one
ornate title. Dropping the `FontSubstitution "Albertus MT" -> "..."` rule
entirely (reasoned: "stock font already has the glyphs, no redirect needed")
broke everything that rule used to touch.

**Revised understanding:** the presence of a `FontSubstitution` rule for a
given font family name appears to be what flags that family's text as
needing a real `MultiByteToWideChar(1251, ...)`-style decode in the first
place - without one, the engine falls back to a naive direct byte-to-
codepoint widen (harmless for Western cp1252 text, exactly reproduces the
garbage seen for Cyrillic). It's not about *which* font ends up rendering
the glyphs - it's the rule's mere existence that matters. Fixed by adding
back a **self-referencing** `FontSubstitution "Albertus MT" -> "Albertus
MT"` block (same family, same sizes, every size role Albertus MT is used at
- 8/9/10/12/14/16/18/20/22/24) - still no custom font *file*, just the rule
itself. `SachaWynter -> Albertus MT` kept as before. Rebuilt and redeployed;
not yet re-confirmed with a screenshot after this specific fix.

This still doesn't resolve the §10 ornate-title widget specifically (that
one has its own, separate, per-widget decode bug per the byte-arithmetic
proof there) - but it should restore everything else that regressed.

## 13. Reverted fully to the §9 recipe - stop simplifying this

The self-referencing-rule fix in §12 was still not enough - user reinstalled
clean English 2.01 again and reported the same widespread garbled text.
Rather than keep debugging the "clean" simplification further,
`build_beta_english_big.py` was reverted, in full, to the exact recipe
confirmed working by screenshot on 2026-09-19 (§9): both custom font files
(`AlbertusMTUA.otf`, `sachawyntertight_ua.ttf`) added back to the archive,
`language.ini` gets its 2 `LocalFontFile` lines again, and
`fontsubstitution.ini` has both blocks again (`SachaWynter ->
SachaWynterTight`, `Albertus MT -> AlbertusMTUA`). Rebuilt against a fresh
clean English 2.01 and redeployed; verified directly (not assumed) that the
deployed archive's `language.ini` and file list match this shape exactly.

**Lesson for next time:** §11/§12's finding that the *stock* fonts already
have Cyrillic glyphs is still true and still worth knowing, but it is *not*
sufficient on its own to make the game render them correctly - something
about a custom, distinctly-named font file plus its own `LocalFontFile`
registration is doing real work here beyond just "having the glyphs
available", that a self-referencing substitution rule alone does not
reproduce. Do not attempt to drop the custom fonts again without a
confirmed in-game screenshot at each step - this was tried twice today
(§12's self-reference attempt, and before that no substitution rule at
all) and both regressed. The §10 ornate-title widget bug is unaffected
either way and remains open.

## 14. The §10 ornate-title bug was already solved in BFME2 - found by
## reading the prior work instead of re-experimenting

Same session, immediately after §13. A guess at fixing §10's bug by adding
`FontSubstitution "Generals" -> "AlbertusMTUA"` (reasoning:
`headertemplate.ini`'s `Title` role names `"Generals"`, which has zero
Cyrillic) was tried and **explicitly rejected by the user** - not because
the idea was necessarily wrong, but because this exact problem was already
solved once, for BFME2, and should have been looked up rather than
re-derived from scratch. Reverted immediately (see git history / the
`build_beta_english_big.py` comment marking `FontSubstitution "Generals"` as
never-to-touch).

**The actual already-proven fix, found in
`002_BFME_2/005_BFME2_UKRAINIAN/prototype/lang/Ukrainian/headertemplate.ini`:**
that prototype rewrites **every single `HeaderTemplate` role's `Font =
"..."` line to `Font = "Arial"`** - `AptGadgets`, `Title` (stock:
`"Generals"`), `MainButton`, `Button`, `ButtonSmall`, `TextEntry`,
`ComboBoxEntry`, `MinorTitle`, `LabelRegular`, `LabelSmall`,
`LoadScreenCameos`, `LoadScreenMissionLocation` - all switched uniformly to
a real system font with full Unicode/Cyrillic support, sidestepping
`Generals` (and every other stock header font) entirely rather than trying
to redirect it. This is editing `headertemplate.ini` directly - a different
mechanism from `fontsubstitution.ini`'s `FontSubstitution` rules, and one
this session hadn't tried for RotWK at all before this.

**Correction, minutes later: this was also wrong.** The
`prototype/lang/Ukrainian/headertemplate.ini` file that pattern was copied
from lives in `005_BFME2_UKRAINIAN/prototype/` - a folder this project's own
earlier history explicitly downgraded to unverified/not-proven-working (no
font files were ever confirmed present there). It is not the actual shipped
fix. The real confirmed-working BFME2 beta's own notes
(`002_BFME_2/005_BFME2_UKRAINIAN/BETA_PATCH_NOTES.md` §6, "Everything
touched, final state") explicitly list `headertemplate.ini` under
**"Untouched: everything else."** BFME2 never actually solved this problem
- there was nothing to copy. User caught this immediately ("где я просил
переключить на ариал?"); the `headertemplate.ini` edit was reverted from
`build_beta_english_big.py` and RotWK is back to the exact §9/§13 recipe.

**Corrected process lesson:** "check what a sibling project already did"
means checking its *actual confirmed-working output and its own written
notes* - not any file that happens to sit in that project's folder tree. A
file's mere presence in a project does not mean it was ever shipped, tested,
or even correct; this repo specifically uses `prototype/` to mean
"unverified." The §10 ornate-title bug remains **open and unsolved** - do
not reach for `headertemplate.ini` or `"Generals"` again without either an
explicit ask from the user or a source that's actually confirmed working.

## 15. Cross-checked three official RotWK localizations directly - Russian,
## French, Chinese Taiwan. Consistent picture, still unsolved for us.

Session 2026-09-20, continued. Installed each official localization in turn
and inspected its actual shipped files directly (not assumptions).

**Russian 2.1** (`F:\RotWK\lang\russian.big`, copies saved to
`005_BFME2_RoTWK_UKRAINIAN/reference_russian/`):
- Ships `lotr.csf` only, no `data\lotr.str` at all.
- `lotr.csf` header `language_id = 17` (confirmed by direct byte inspection:
  header hex `...11000000` at offset 20, little-endian `0x11` = 17).
- `data\ini\fontsubstitution.ini`: only one block,
  `FontSubstitution "SachaWynter" -> "Omnia LT Std"`, with a dense size
  table (8,9,10,11,12,14,16,18,20,22,24,26,28,40, each mapped 1:1 to itself).
  No `"Albertus MT"` rule at all.
- `language.ini`: byte-for-byte the same `LocalFontFile` lines as stock
  English (`AlbertusMT.otf`, `OmniaLTStd.ttf`) - no custom fonts added, no
  new registrations.
- `headertemplate.ini`: identical to stock - `Title`/`MainButton` still
  `Font = "Generals"`, untouched.
- Stock `data1.big\albertusmt.otf` (this Russian release's own copy) already
  has full Cyrillic (66/256 block coverage, fontTools-verified) - matches
  what English 2.01's own `albertusmt.otf` has too (see section 12).
- **In-game: the exact ornate-title widget that mojibakes for us
  ("МЕНЮ НАСТРОЙКИ") renders perfectly correctly.** Screenshot-confirmed.

**French 2.01** (`F:\RotWK\lang\french.big`):
- Same shape as Russian: `lotr.csf` only, no `.str`.
- `data\ini\fontsubstitution.ini`: only `"SachaWynter" -> "Omnia LT Std"`,
  again no `"Albertus MT"` rule - but a *different* size table than
  Russian's, using real upscaling (`Size 8 = 12`, `Size 10 = 14`, ... `Size
  40 = 70`) rather than Russian's 1:1 mapping. Confirms the exact numbers
  aren't magic - different localizations ship different tables for the same
  underlying mechanism.
- `language.ini`: same as stock/Russian, no custom fonts, only
  `ThousandSeparator` differs (`" "` vs Russian's `","`).
- `headertemplate.ini`: byte-identical to Russian's and stock - `Title`/
  `MainButton` still `"Generals"`, untouched.

**Chinese Taiwan** (`003_BFME_2_RoTWK/003_BFME2_RoTWK_CHINESE_TAIWAN/lang/chinese_t.big`,
already in this repo as a reference):
- Same shape again: `lotr.csf` only. `language_id = 22` (0x16) - a third
  distinct value, confirming this field is per-language and not a fixed
  magic number RotWK expects universally.
- **`headertemplate.ini` is the interesting one.** Chinese *needs* a real
  CJK-capable font almost everywhere - and indeed every single
  `HeaderTemplate`'s `Font = "Arial"` was changed to
  `Font = "Microsoft YaHei UI"` (a real Windows CJK font)... **except
  `Title` and `MainButton`, which are still `Font = "Generals"`,
  untouched** - exactly like Russian and French. If `"Generals"` genuinely
  couldn't render non-Latin text at all, Chinese - which has zero choice in
  the matter - would have had to fix it too. It didn't. Strongest evidence
  yet that `Title`/`MainButton` are dead/unused `HeaderTemplate` roles in
  the modern APT-based UI (the file's own header comment already says "For
  the most part, only Apt... are now being used... most others have become
  obsolete") - i.e. **nothing in the live game actually reads this role
  through headertemplate.ini at all**, and the real ornate-title rendering
  path is something else this project hasn't located yet (an APT-internal
  font reference, most likely).

**Consistent pattern across all three:** CSF only, no `.str`; no
`"Albertus MT"` FontSubstitution rule (stock Albertus MT already suffices,
matches section 12's finding); `headertemplate.ini`'s `Title`/`MainButton`
left as `"Generals"` untouched even where the language absolutely cannot
render through a Latin/Generals-only path (Chinese). None of the three
localizations does anything special to fix this widget - it just isn't
broken for them, because their text is genuinely wide-char CSF from the
start, not because of an ini setting. This is the strongest evidence so far
that the fix is inherently tied to using CSF, not to any ini/font
combination reachable while staying on `.str`.

**Resolved (negatively): it really is the `english` slot itself, not any
config file.** `build_ru_emulation_experiment.py`'s output (Russian's
`language.ini`/`headertemplate.ini`/`fontsubstitution.ini` copied onto a
clean English 2.01 *verbatim, byte-for-byte*, with only the CSF content
swapped to ours) was deployed and tested: **entire menu still in English**,
identical to every earlier CSF attempt. This rules out every config-file
explanation there could be - the three ini files are now provably identical
to a working Russian install's, and it still doesn't work. The `english`
slot itself does not consult `lotr.csf`, full stop, regardless of what
accompanies it. Reverted back to the proven `.str`-based build
(`build_beta_english_big.py`) immediately after this test.

Also checked while investigating: the standard SAGE-engine CSF language-ID
enum (0=US English, 1=UK English, 2=German, 3=French, 4=Spanish, 5=Italian,
6=Japanese, 7=Jabberwockie, 8=Korean, 9=Chinese, >9=game-specific extension)
confirms `0` is the *correct* semantic value for English - meaning the
original section 9 CSF attempt's `language_id=0` was never actually
"wrong" for English; RotWK's higher values (17 for Russian, 22 for Chinese
Taiwan) are its own extensions for languages added after the original
Generals-era table. This closes off the language-ID theory entirely as an
explanation for the `english`-slot failures - it was never the cause.

**Where this leaves things:** CSF is not viable for the `english` slot no
matter what accompanies it. The `.str` + FontSubstitution-flag approach
(sections 9-14) remains the only working path *for the `english` slot*,
with the one known remaining defect being the `APT:SpecialPowersTitle`-class
ornate-title mojibake (section 10) - see section 16, which fixes this
properly by moving off the `english` slot entirely.

## 16. BREAKTHROUGH - the `french` slot, CSF, zero font changes: the
## ornate-title bug is actually solved

Directly inspired by a real precedent already in this repo: the official
Korean RotWK localization
(`003_BFME_2_RoTWK/002_BFME2_RoTWK_KOREAN/Korean.reg`) doesn't create a
"Korean" slot - it sets registry `Language = "French"` and ships as
`lang\French.big` / `lang\frenchpatch201.big`. Whoever built that Korean
patch had already hit and solved the exact same "the `english` slot won't
cooperate" problem this project spent sections 9-15 on, by not fighting the
`english` slot at all and reusing an existing *named* slot instead.

**Applied the same idea.** With French 2.01 installed (registry `Language`
already `"French"` on this machine, no registry edit needed), extracted
French's own `lotr.csf` and confirmed its header `language_id = 4` by
direct byte inspection (a fourth distinct value alongside Russian's 17,
Chinese Taiwan's 22 - and the classic SAGE enum's `3` for French, confirmed
via web search of the original Generals-era CSF spec, meaning RotWK
renumbered even some of the original languages, not just the newly-added
ones). Built `build_french_slot_experiment.py`: replaces only `lotr.csf`
(Ukrainian content, `language_id=4`) inside `french.big` /
`frenchpatch201.big`, leaving `language.ini`, `headertemplate.ini`,
`data\ini\fontsubstitution.ini`, and every font file completely untouched -
exactly as French shipped them. No custom fonts, no `LocalFontFile`
additions, no `FontSubstitution` edits at all.

**Result, screenshot-confirmed: everything works, including the ornate
title.** The exact "Special Powers"-class panel ("Чаклування") that
mojibaked as `×àêëóâàííÿ` in every single `.str`-based `english`-slot
attempt (sections 10, 12, 13, 14) rendered **perfectly correctly** - with
zero font-related changes of any kind. This conclusively proves the section
10 bug was never about `SachaWynter`, `Generals`, or any font substitution -
it was purely that `.str` feeds this one widget narrow bytes it can't
handle, while CSF feeds it genuine wide-char text it handles fine.

**Where the text was actually coming from, confirmed by elimination:**
searched every major stock archive (`data1.big`, `data2.big`, `ini.big`,
`maps.big`, `terrain.big`, `w3d.big`, `textures0.big`) for any font file
named `"Generals"` or any `LocalFontFile` line referencing it - found
**nothing, anywhere**. `"Generals"` (`headertemplate.ini`'s `Title`/
`MainButton` role) is not a real registered font in this game at all; that
role is dead code in the modern APT-based UI, consistent with three-for-
three official localizations (Russian, French, Chinese Taiwan - section 15)
leaving it untouched even where they desperately need a different font
everywhere else (Chinese Taiwan). The ornate title actually renders through
stock `"Albertus MT"` (via the `AptGadgets`/`AptGadgetsTiny` role), which
has been confirmed Cyrillic-capable out of the box since section 12. This
question is now closed - do not investigate `"Generals"` further in this
project.

**What this means going forward:** the `french`-slot + CSF approach is
strictly better than the `english`-slot + `.str` approach this project
built sections 9-14 around - no custom fonts, no font-collision risk, no
`FontSubstitution` bookkeeping, and it fixes the one bug that was otherwise
unfixable. The practical tradeoffs to weigh before switching the "real"
beta over to this approach:
- Requires a registry edit (`Language = "French"`) instead of the
  no-registry-changes philosophy sections 1-14 followed - though this is
  exactly what the official Korean localization already does, so it's a
  proven-acceptable pattern, not a novel risk.
- Overwrites the "french" slot entirely - anyone with a French Windows/EA
  account setting, or who wants French *and* Ukrainian available
  separately, loses French. Same tradeoff Korean's own approach accepts.
- Should double check `frenchaudio.big`/voice-over behavior is unaffected
  (not tested this session - this experiment only touched the archives
  under `lang\french.big`/`frenchpatch201.big`, not audio).
- The full `RotWK_strings_ua.json` corpus should be re-verified against
  this delivery mechanism (this test used the same JSON that's been
  QA'd/deployed for the `.str` build - no reason to expect a difference,
  but not yet screenshot-checked beyond this one panel and whatever else
  was visible in the test session).

Not yet decided/actioned: whether to formally switch `build_beta_english_big.py`'s
output to this `french`-slot CSF recipe, keep both side by side, or some
other resolution. `build_french_slot_experiment.py` and its output
(`beta/french.big`, `beta/frenchpatch201.big`) exist alongside the proven
`english`-slot build and haven't replaced it as of this writing. Pristine
French 2.01 reference copies (`french.big`, `frenchpatch201.big`) are saved
at `005_BFME2_RoTWK_UKRAINIAN/reference_french/` for future rebuilds without
needing to reinstall French again.

## 17. RESOLVED - `UnicodeFontName`, the missing piece. Everything works,
## including the ornate title. This is the final recipe.

Same session, continued. §16 proved `french`-slot CSF fixes the ornate
title's *encoding*, but the title still rendered in a plain, undecorated
font (looked like generic Arial) instead of the intended custom typeface -
different from the pretty-but-broken `english`-slot rendering. Chased down
why with a long side-quest (documented for completeness, since it was a lot
of wrong turns before the real answer):

- **Confirmed the game's own `.exe`/`game.dat` are the same file across
  every language SKU** (this was never actually re-verified by hashing
  across a reinstall, but is standard EA/SAGE practice and the user's own
  reasoning was accepted as correct - data-driven localization, not
  per-language binaries. Saved hashes for the record if ever needed:
  `lotrbfme2ep1.exe` sha256 `034a5b91...82d69c4` (499712 bytes),
  `game.dat` sha256 `5481de75...92256ba` (11346944 bytes), both from the
  French 2.01 install).
- **Diagnostic proof that neither `language.ini` nor `headertemplate.ini`
  drive this widget at all:** built and deployed a test that force-replaced
  *every* font role in both files (~35 lines total) with `Pacifico`, a
  maximally distinctive cursive font embedded fresh into the archive (never
  installed to Windows, sourced from the Desktop) - screenshot confirmed
  every other visible UI element (buttons, labels, body text) switched to
  Pacifico, **but the panel title did not change at all.** Also tried adding
  `FontSubstitution "Arial" -> Pacifico` (a guess, since the title's
  typeface visually resembled Arial) - no effect either.
- **A parallel attempt to brute-force *every* discoverable font declaration
  in `ini.big` (mouse.ini, ingameui.ini, ingamenotificationbox.ini,
  strategichud.ini, drawgroupinfo.ini) crashed the game** - the blind
  regex matched `ResolutionFontAdjustment = 1.0` (a float multiplier, not a
  font name, just because the key contains the substring "Font") and wrote
  `"Pacifico"` into a numeric field, which the INI parser rejected fatally.
  **`ini.big` was restored from backup immediately; it must not be edited
  for this project** (this was already documented as off-limits by BFME2's
  own `BETA_PATCH_NOTES.md` section 6/Attempt 2, and got violated here under
  time pressure chasing a diagnostic - don't do this again, on either game).
- Dumped every readable ASCII string out of the compiled `apt\Options.big`
  bundle (`.apt`, `.const`, `.dat` files) looking for an embedded font-name
  string for this widget - found none. Matches an independent, real
  modding-community source (Revora Forums, "Changing the color, size and
  the font of the UI" thread, found via web search): "the main menu is in
  the apt files, but these files are unreadable" and "[headertemplate.ini]
  change the first 2 [roles], the rest don't have any use" - independently
  corroborating this project's own section 15 finding that most
  `HeaderTemplate` roles (including `Title`/`MainButton`/`"Generals"`) are
  dead code.
- **The actual answer: `UnicodeFontName`.** `language.ini` has a line
  `UnicodeFontName = "Arial Unicode MS"` in every stock/untouched language
  variant checked this session (English, French, Russian). Checked directly
  or this machine (`System.Drawing.Text.InstalledFontCollection`): **"Arial
  Unicode MS" is not installed** (only `Arial`, `Arial Black`, `Arial
  Narrow`, `Arial Rounded MT Bold`, `Lucida Sans Unicode`). When the engine
  asks Windows for a missing font family, *Windows itself* - not the game -
  picks a substitute, and apparently picks something Arial-like on this
  machine. This is why the title rendered as plausible, correctly-encoded
  text in a generic sans-serif face: it was never going through the game's
  own `FontSubstitution`/`HeaderTemplate` systems at all, it was falling
  through to `UnicodeFontName`, which fell through to *Windows'* own
  missing-font substitution.
- **Confirmed by checking the real official Korean and Chinese Taiwan
  RotWK localizations already in this repo:** both explicitly override
  `UnicodeFontName` to a real, actually-present font instead of leaving the
  stock `"Arial Unicode MS"` value. Chinese Taiwan:
  `UnicodeFontName = "Microsoft YaHei UI"` (a real, broadly-available
  Windows CJK font). Korean: `UnicodeFontName = "가는윤로마체체"` (a real
  Korean font name, garbled to `"°¡´ÂÀ¸¶äÃ¼"` when read as Latin-1 - a
  genuine font, not English-fallback mojibake this time), *and* it adds
  three of its own `LocalFontFile` lines for actual Korean font files
  (`연세본문체.ttf` / `HYKANM.ttf` / `Utuml.ttf`, similarly garbled in a
  Latin-1 read). Neither relies on Windows' own fallback for a missing
  font - both explicitly supply one. This is the pattern this project had
  never tried in ~15 sections of font work: `UnicodeFontName` was never
  touched once, the whole time.

**The fix:** set `UnicodeFontName = "AlbertusMTUA"` (our own custom,
already-Cyrillic, distinctly-named font - the same file already used for
`FontSubstitution`), on top of the section 16 `french`-slot CSF recipe.
`build_french_slot_final.py` is the resulting script: builds `lotr.csf`
(Ukrainian, `language_id=4`) exactly as section 16 did, adds
`AlbertusMTUA.otf` via `LocalFontFile`, sets `UnicodeFontName` to it, and
keeps the `FontSubstitution "SachaWynter"`/`"Albertus MT"` block pointing
at it too (same pattern proven for the `english`-slot build). Built,
deployed to `F:\RotWK\lang\french.big` + `frenchpatch201.big`, and
**confirmed working in-game by the user** - the ornate panel title now
renders correctly *and* in the intended custom typeface, not just readably.

**This is now the recommended recipe for RotWK**, superseding the
`english`-slot `.str`-based build (sections 9-14) for anything beyond a
quick reference: it fixes the one defect that recipe could never solve, at
the cost of overwriting the "french" slot and requiring the registry
`Language` value to be `"French"` (already the case automatically once
French 2.01 is installed - no manual registry edit needed on a fresh
install, exactly matching how the official Korean localization already
ships). `build_beta_english_big.py` and its output are kept as-is,
untouched, for anyone who specifically needs the English slot preserved.

**Files as of this writing:**
- `beta/build_french_slot_final.py` - the final, recommended build script.
- `beta/french.big`, `beta/frenchpatch201.big` - its output, currently
  deployed and confirmed working.
- `beta/build_french_slot_experiment.py` - superseded by
  `build_french_slot_final.py` (identical except it didn't set
  `UnicodeFontName` or add a custom font) - kept for the historical record,
  not the one to use going forward.
- `beta/build_pacifico_test.py`, `beta/build_safe_pacifico.py` (this
  repo)/analogous scratch scripts (BFME2 side, not committed) - pure
  diagnostic tools, not meant to ever be deployed for real; safe to delete
  once this section's findings are trusted, kept for now in case the
  ornate-title question ever needs re-diagnosing on a future patch version.
- `reference_french/french.big`, `reference_french/frenchpatch201.big` -
  pristine French 2.01 source archives, needed by every French-slot build
  script's `--source` argument.

**Still open / not yet done:**
- `lm_text.dds` Ukrainian loading-screen texture (section 4) - independent
  of everything in this section, still not built.
- The ~13,000-label QA pass (hunspell, terminology) covered sections
  earlier in this document (not re-summarized here) - unaffected by the
  CSF/font delivery mechanism, still valid regardless of which recipe ships.
- Whether `frenchaudio.big` (voice-over) needs any attention - not tested
  or touched this session, only `french.big`/`frenchpatch201.big` were
  ever modified.
- BFME2's own equivalent fix (`UnicodeFontName` + French-slot CSF) has NOT
  been ported back to `002_BFME_2/005_BFME2_UKRAINIAN/beta/` - everything
  in this section 17 was done and confirmed for RotWK specifically. BFME2's
  own beta still uses the English-slot CSF recipe from its own
  `BETA_PATCH_NOTES.md`, which was never confirmed to have this exact
  ornate-title defect in the first place (never screenshot-checked for it).

## 18. Cleanup pass - `release/` folder, one-command installer, a real bug
## found and fixed along the way

Session 2026-09-20, final pass. `beta/` renamed to `release/` (this is
shipped, not beta); `build_french_slot_final.py` renamed to `build.py`;
every superseded experimental script removed (their findings are fully
captured in `../../ROTWK_TEXT_AND_FONT_SYSTEM.md`, no need to keep half-
working variants around). `AlbertusMTUA.otf` copied into
`release/fonts/` so this project no longer reaches into
`002_BFME_2/`'s folder for a font file. The original, confirmed-corrupted
`lotr.csf`/`lotr.str` (section 2's double-encoding bug) were deleted -
`RotWK_strings_ua.json` has been the only real source of truth for a while,
keeping the broken originals around only risked someone reaching for them
by mistake.

**Added a one-command installer** so this doesn't require manually running
scripts and copying files by hand:
`000_TOOLKIT/BFME-loc-toolkit/apply-localization-rotwk.bat` (calls
`scripts/apply_localization_rotwk.py`). It auto-detects the game folder via
the registry, backs up pristine French archives on first run (into
`lang\lang_backup_original_ua\`, safe to re-run any number of times - it
always rebuilds from that backup, never from an already-patched file), sets
registry `Language = "French"` if it isn't already, and writes the patched
archives straight into `lang\`. Tested end-to-end from a freshly-reinstalled
pristine French 2.01 install.

**Found a real bug while building the installer:** `build.py` (inherited
from `build_french_slot_final.py`) never actually included the localized
texture-replacement step (`load_w_ea.jpg`, `logowithshadow.tga`,
`titlescreenuserinterface.jpg`) - it was dropped somewhere between the
earlier experimental scripts (which did have it) and the "final" one. This
means **the build the user tested and confirmed working in-game
(section 17) was shipping with stock English loading-screen/title
textures**, not the localized ones - never noticed because none of that
session's screenshots happened to be the loading or title screen
specifically. Confirmed by comparing archive contents byte-for-byte between
the old `release/french.big` and the new installer's output: only the three
texture files differed, and the installer's versions matched the actual
source files in `006_LOCALIZED_LOGOS/RoTWK_LOGOS/009_UA/` exactly while the
old build's didn't. Fixed in both `build.py` and
`apply_localization_rotwk.py` (kept in sync - same texture list, same
logic); `release/french.big`/`frenchpatch201.big` rebuilt and reconfirmed
byte-identical to the installer's own output. Not yet re-screenshotted
specifically for the loading/title screen, but the fix itself is
mechanical and low-risk (same texture-swap logic already proven correct
for BFME2 and for RotWK's own earlier `english`-slot build).

Cleared out leftover backup debris from the day's testing on the actual
game installs (`F:\RotWK\lang_backup_original_french\`,
`F:\BFME2\lang_backup_original_french\`, `F:\BFME2\ini_backup_original.big`)
- all pristine-file safety copies that had already served their purpose;
the installer now manages its own single backup location going forward.
