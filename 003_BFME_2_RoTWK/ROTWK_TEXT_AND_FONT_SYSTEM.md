# RotWK text & font system — reference (read this before touching fonts again)

This is the distilled, confirmed-working knowledge from localizing RotWK
into Ukrainian (session ending 2026-09-20). It is written to be
language-agnostic — everything here applies to localizing RotWK into *any*
non-English language, not just Ukrainian. Read this before spending another
session rediscovering any of it.

The narrative, warts-and-all history of how this was found (including every
wrong turn) lives in `005_BFME2_RoTWK_UKRAINIAN/BETA_PATCH_NOTES.md`. This
document is the clean answer, not the story.

---

## 1. The one recipe that actually works

Patch a **named language slot that is not `english`** (this project uses
`french`), with a **CSF** (not `.str`), and set **`UnicodeFontName`** in
`language.ini` to your own real, Cyrillic/whatever-script-capable font.

Concretely, for a translation into language X:

1. Get a pristine copy of `lang\<slot>.big` + `lang\<slot>patch201.big` for
   whatever real named slot you're going to reuse (this project reuses
   `french` — see §3 for why, and why not `english`).
2. Build `lotr.csf` (binary, UTF-16, bit-inverted bytes — see §2) from your
   translation data. Set its header's `language_id` field to the value the
   slot you're reusing actually ships with (§4) — not 0, not a guess.
3. Remove `data\lotr.str` from the archive if present (it isn't in a
   pristine French/Russian/Chinese install, but always check).
4. Add your own font file (e.g. a renamed-family Cyrillic-capable
   OpenType/TrueType font) via a new `LocalFontFile` line in `language.ini`.
5. Set `UnicodeFontName = "<YourFontFamily>"` in the same `language.ini`
   block (§6 — this is the step every earlier attempt missed for an entire
   session).
6. Add `FontSubstitution "SachaWynter" -> "<YourFontFamily>"` and
   `FontSubstitution "Albertus MT" -> "<YourFontFamily>"` blocks to
   `data\ini\fontsubstitution.ini` (§7 — still needed for `.str`-fed text
   generally, and cheap insurance either way).
7. Deploy the two rebuilt archives into `lang\`. No registry edit is needed
   if the target slot's own language pack was ever installed on the machine
   (installing "French 2.01" already sets `Language = "French"` in the
   registry automatically).

Reference implementation:
`005_BFME2_RoTWK_UKRAINIAN/release/build.py`.

---

## 2. Two text formats exist: `.str` and `.csf` — know which one you're
## actually getting read

- **`.str`** — plain text, `LABEL\r\n"text"\r\nEND\r\n\r\n` blocks. Decoded
  by the engine through a **single-byte Windows codepage**
  (`MultiByteToWideChar(CP_ACP, ...)`-style), not UTF-8. A single byte maxes
  out at 0xFF (255) — Cyrillic Unicode starts at U+0400 (1024), so `.str`
  can represent Cyrillic *only* via a Cyrillic single-byte codepage
  (cp1251), never via UTF-8.
- **`.csf`** — binary, real UTF-16LE with every byte bit-inverted
  (`~byte & 0xFF`). No codepage ambiguity, genuinely wide-char.

**RotWK's engine does not read `.csf` at all when it lives in the `english`
slot** — confirmed by two separate, clean tests (a plain CSF-only deploy,
and a second attempt with the CSF header's `language_id` matched exactly to
a real working value) — both times the entire game fell back to English
with `MISSING:` errors for the handful of labels with no English fallback
baked into the executable. This is not a guess; it was directly tested.

**Every other named slot this project checked (`french`, `russian`, and the
official Chinese Taiwan reference) ships `.csf` only, no `.str` at all, and
CSF is read correctly there.** So: if you're patching `english` in place,
you're stuck with `.str` and its single-byte-codepage limits (workable, see
§8 for the one thing it can't do). If you patch any other real named slot,
CSF works and is strictly better — no codepage limit, no known widget-level
bugs.

`.str` details, if you do go that route (e.g. `english`-slot patch):
- Every quoted value must be **on one physical line**. A raw line break
  inside a value crashes the game outright with an in-engine parser error
  (`End quotes missing for string '...'`) — real line breaks must be the
  literal two-character escape `\n`, never an actual `\r\n` byte.
- Any embedded `"` inside a value must be escaped as `\"` (backslash-quote,
  two characters) — an unescaped raw `"` also crashes the parser the same
  way, at whatever label has one.
- Must be encoded as the target language's single-byte codepage matching
  the *system's own ANSI codepage* (cp1251 for Cyrillic on a Russian/
  Ukrainian-configured Windows) — not UTF-8. Writing it as UTF-8 doesn't
  crash, but produces a specific, recognizable mojibake: repeating
  Latin/Turkish-lookalike accented characters (`ğ`, `¢`, `¬`...), the
  signature of UTF-8's multi-byte lead bytes (`0xD0`/`0xD1`, common to
  nearly all Cyrillic letters) being decoded one byte at a time as if
  Latin-1/cp1252.

CSF details:
- Has **no escape processing at all** — whatever bytes are in the string
  render verbatim. A translation source authored with `.str`-style literal
  `\n`/`\t`/`\"` escapes must have those converted to real
  newline/tab/quote characters before being written into the CSF (a
  one-time `unescape_for_csf()` pass), or the literal backslash-n etc. show
  up as visible text in-game.
- Header layout (24 bytes): magic ` FSC` (4 bytes) · version (int32,
  always `3` seen) · num_labels (int32) · num_strings (int32, always equal
  to num_labels — one string per label) · unused (int32, `0`) ·
  **`language_id`** (int32 — see §4). Each label:
  ` LBL` magic, nstrings (int32, always `1`), namelen (int32), name (ASCII,
  no null terminator), then per string: `RTS` magic (bytes reversed —
  stored as `' RTS'`), length (int32, in UTF-16 code units), then that many
  UTF-16LE code units with every byte bit-inverted.

---

## 3. Language slots: `english` is not just "another slot"

Every install has a registry value at
`HKLM\SOFTWARE\WOW6432Node\Electronic Arts\Electronic Arts\The Lord of the
Rings, The Rise of the Witch-king` → `Language` (a plain string, e.g.
`"English"`, `"French"`, `"Russian"`), and `InstallPath`. The game loads
`lang\<Language-lowercased>.big` / `<Language-lowercased>patch201.big`
accordingly. Installing any official language pack sets this registry value
automatically — no manual registry edit is needed if you're reusing a slot
whose real language pack gets installed first.

**The official Korean localization already in this repo
(`003_BFME_2_RoTWK/002_BFME2_RoTWK_KOREAN`) does exactly what this project
ended up doing**: it doesn't create a new "Korean" slot. It sets
`Language = "French"` (via its `.reg` file) and ships as `lang\French.big`
+ `lang\frenchpatch201.big`, overwriting the French slot entirely. Whoever
built that patch had already hit the same "the `english` slot won't
cooperate" wall this project spent a full session on, and solved it the
same way: reuse an existing named slot instead of fighting `english` or
inventing a new one.

**Practical consequence:** patching a named slot like `french` means real
French is no longer available on that install (same trade-off Korean's own
approach accepts). If you need multiple languages coexisting, you need a
genuinely different slot name plus its own registry entry — untested by
this project, and likely to hit the same "does this engine build even
recognize a slot name it's never seen" uncertainty that made `english`
fail. Reusing a slot whose actual language pack you have and can verify
(French, Russian, etc.) is the only path this project actually confirmed
working.

---

## 4. `language_id` (the CSF header field) is real and per-language, not
## a fixed magic number

Confirmed by directly reading the `lotr.csf` header byte-offset 20 (a
little-endian int32) out of several real, working installs:

| Slot | `language_id` | Text format |
|---|---|---|
| English (the classic SAGE/Generals-era enum default) | `0` | `.str` |
| German | `3` | CSF |
| French | `4` | CSF |
| Russian | `17` | CSF |
| Chinese Taiwan | `22` | CSF |
| Turkish | *(no `lotr.csf` at all — N/A)* | `.str` |

(Turkish's own `launcher.csf`, a separate/unrelated file for the standalone
launcher UI rather than the main game text, reads `0` — not informative
about the main game language and not comparable to the values above.)

The original Command & Conquer/Generals-era CSF spec (confirmed via a
web search of community documentation) defines `0`=US English, `1`=UK
English, `2`=German, `3`=French, `4`=Spanish, `5`=Italian, `6`=Japanese,
`7`=Jabberwockie, `8`=Korean, `9`=Chinese, `>9`=unassigned/engine-specific.
**RotWK's actual values don't match this table exactly** — its French is
`4` (`Spanish` in the classic enum) and its German is `3` (`French` in the
classic enum); Russian/Chinese Taiwan use values far outside the original
0-9 range entirely. RotWK evidently reshuffled the *original* languages'
numbers too, not just appended new ones after `9`. **Do not assume a value
from the classic table is correct for RotWK — always read it directly from
a real, working install of the slot you're targeting.**

Also notable: German's `data\ini\fontsubstitution.ini` is byte-for-byte
identical to French's (§7's "upscaling" size table, `Size 8 = 12` through
`Size 40 = 70`) — this specific table is likely RotWK's standard template
for Western European languages generally, not something French-specific.
Russian's simpler 1:1-mapped table (§7) may be the Russia-specific
variant, or Cyrillic-specific — untested which.

Whether this field actually matters for whether CSF gets read at all was
tested directly, from both directions:
- An `english`-slot CSF with `language_id=17` (Russian's real value) had
  **zero effect** — still completely ignored, same as `language_id=0`.
- A `french`-slot CSF with a deliberately *wrong* `language_id=0` (English's
  value, not French's real `4`) **worked exactly the same as the correct
  value** — full Ukrainian text, ornate title included, screenshot-
  confirmed. Rebuilding it with the correct `4` afterward changed nothing
  observable either.

**Conclusion: `language_id` does not matter at all, in either direction.**
It is not what makes `english` reject CSF, and it is not required to match
the slot's own real value for a named slot to work. The only thing that
actually matters is the slot's *name* (`french`/`russian`/etc. vs
`english`) — a hard, slot-name-based restriction with nothing to do with
header metadata. Still worth setting to a real value out of general
correctness/hygiene, but treat it as cosmetic, not functional.

---

## 5. `headertemplate.ini`'s `Title`/`MainButton` roles reference a font
## called `"Generals"` that does not exist anywhere in the game

`headertemplate.ini` (present per-language, e.g. inside `french.big`) has a
`HeaderTemplate Title` block (used, per its own comment, for "large
Titles") and `HeaderTemplate MainButton` block, both with
`Font = "Generals"`. **This is dead code.** Confirmed three independent
ways:

1. Searched every major stock archive (`data1.big`, `data2.big`, `ini.big`,
   `maps.big`, `terrain.big`, `w3d.big`, `textures0.big`) directly for any
   font file with internal family name `"Generals"`, and any
   `LocalFontFile` line anywhere referencing it. **Found nothing, in either
   category.**
2. Cross-checked three official localizations (Russian, French, Chinese
   Taiwan) — all three leave `Title`/`MainButton` as `"Generals"`,
   untouched, even Chinese Taiwan, which rewrote *every other*
   `HeaderTemplate` role to a real CJK font (`"Microsoft YaHei UI"`)
   because it has zero choice in the matter for anything that's actually
   rendered. If `"Generals"` were load-bearing for anything visible in the
   modern UI, Chinese Taiwan would have had to fix it too.
3. Direct proof by elimination: force-replaced *every* font role in both
   `language.ini` (~22 roles) and `headertemplate.ini` (13 roles) with a
   maximally distinctive test font (a cursive script font, embedded fresh
   into the archive, never installed to Windows) and deployed it — every
   other visible UI element changed to the test font; the "ornate panel
   title" widget (the exact kind of element `Title`/`MainButton` sound like
   they'd control) did not change at all.

The file's own header comment already says why: *"For the most part, only
Apt... are now being used in the game; Most others have become obsolete."*
Community modding forums (Revora, "Changing the color, size and the font of
the UI") independently corroborate this: *"[headertemplate.ini] change the
first 2 [roles, i.e. `AptGadgets`/`AptGadgetsTiny`], the rest don't have
any use"* and *"the main menu is in the apt files, but these files are
unreadable, so you can't edit the apt files."*

**Do not spend time on `"Generals"` or on editing `headertemplate.ini`
roles beyond `AptGadgets`/`AptGadgetsTiny` (which do map to `"Albertus MT"`
and are covered by the `FontSubstitution` fix anyway).** This is settled,
not an open question.

---

## 6. `UnicodeFontName` — the actual missing piece for decorative/ornate
## title widgets

`language.ini` has a line `UnicodeFontName = "Arial Unicode MS"` in every
stock/untouched language variant (English, French, Russian all checked
directly). **"Arial Unicode MS" is not installed on a typical Windows
machine** (it shipped with old Microsoft Office/Publisher, not with Windows
itself — confirmed directly via `System.Drawing.Text.InstalledFontCollection`
on the machine this was tested on: only `Arial`, `Arial Black`, `Arial
Narrow`, `Arial Rounded MT Bold`, `Lucida Sans Unicode` were present, no
"Arial Unicode MS"). When the engine asks Windows to load a font family
that isn't installed, **Windows itself** — not the game, not
`FontSubstitution`, not `HeaderTemplate` — silently substitutes something
else, and *which* font it substitutes depends on the Windows install, not
on anything in the game's own files.

At least one specific widget class (a decorative, ornate panel-title
element — confirmed instance: the "Special Powers"/Palantir ability-tree
panel header, and the Options-menu title) reads its font through this
`UnicodeFontName` path, completely bypassing `FontSubstitution` and
`HeaderTemplate` entirely. This explains an entire session's worth of
confusion: text rendered here was always correctly encoded (once CSF was in
use), but its typeface was whatever Windows happened to substitute for the
missing "Arial Unicode MS" — which looked like plain Arial on the machine
this was built on, and would look like something else entirely on a
different Windows install/locale.

**Confirmed the real fix by checking the actual official localizations
already in this repo**, which don't rely on Windows' guesswork at all —
both explicitly override `UnicodeFontName`:
- Chinese Taiwan: `UnicodeFontName = "Microsoft YaHei UI"` (a real,
  broadly-available Windows CJK font).
- Korean: `UnicodeFontName = "가는윤로마체체"` (a real Korean font name —
  reads as garbled `"°¡´ÂÀ¸¶äÃ¼"` if the file is opened as Latin-1/cp1252,
  which is just an artifact of reading Korean text with the wrong codepage,
  not a sign of anything broken) — *and* it registers three of its own
  Korean `LocalFontFile`s (`연세본문체.ttf` / `HYKANM.ttf` / `Utuml.ttf`) to
  back it up with real font files.

**The fix, applied and confirmed working for Ukrainian:** set
`UnicodeFontName = "<YourOwnFontFamily>"` (this project uses `AlbertusMTUA`,
the same custom-renamed, already-Cyrillic-capable font used for
`FontSubstitution`). This alone — on top of the §1 recipe (named slot +
CSF) — fixed the ornate-title widget completely: correct encoding *and*
the intended custom typeface, not just readable text in a random
Windows-substituted font.

**If a future localization into a different script hits "most text works,
but one specific decorative/title element renders in some plain, wrong-
looking font despite `FontSubstitution` and `HeaderTemplate` both being
correctly set" — check `UnicodeFontName` first.** It's the one line that
took an entire session to find because it's easy to skim past as boilerplate.

**Setting `UnicodeFontName` does NOT fix this widget under the `english`-
slot `.str` recipe, and won't for any single-byte-codepage text source.**
This is a common enough follow-up question that it's worth spelling out
explicitly: `UnicodeFontName` only controls *which font* renders this
widget's text — it does nothing about *what the text actually is*. Under
`.str`, this exact widget receives text through a raw byte-to-codepoint
widen (§2's mojibake, `×àêëóâàííÿ`-style) *before* any font is even
selected — the wrong characters are already wrong by the time font
selection happens. Pointing `UnicodeFontName` at a real, glyph-complete
font (even `AlbertusMTUA`) in the `english` slot would render those same
wrong characters in a nicer typeface — the font in question does have
ordinary Latin-1 glyphs like `×`/`à`/`ê`/`ë` (it's a full commercial-derived
font) — but the text itself stays garbage. Only real wide-char text (CSF)
avoids the byte-widen step entirely, which is why this fix only applies
together with the §1 named-slot-plus-CSF recipe, never on its own in
`english`.

**This byte-widen bug only actually breaks scripts whose characters don't
fit in a single byte — it is not a universal "any non-English language"
problem.** Confirmed by inspecting an official Turkish RotWK install
(session 2026-09-20, a later addition — note it ships as its own genuinely
named `turkish` slot, not reusing another language's slot the way Korean
reuses `french`): Turkish uses **`.str` only** (no `lotr.csf` in the slot
at all, just the unrelated `launcher.csf`), and leaves `UnicodeFontName`
at the untouched stock `"Arial Unicode MS"` — i.e. the exact same
"broken" setup as `english`, with none of this document's fixes applied.
**And the ornate title widget renders correctly anyway** (confirmed in a
screenshot — `SEÇENEKLER`, with a correct `Ç`). This is not an exception to
the byte-widen bug, it's the bug *not manifesting*: nearly every Turkish
letter (`Ç Ğ İ Ö Ş Ü` and lowercase) sits at the same numeric position in
Windows-1254 (Turkish codepage) as its own Unicode codepoint is in the
Latin-1 Supplement/Latin Extended-A block — both are under 256. A raw
byte-to-codepoint widen of a Turkish letter therefore *coincidentally*
lands on the correct character. Cyrillic can never get this coincidence:
its Unicode block starts at U+0400 (1024), so no single byte (max 255) can
ever widen into it correctly, regardless of codepage. **Rule of thumb: if
the target script fits inside a single byte under some Windows codepage
(Western European accented Latin, Turkish, Baltic, etc.), the `english`-
slot `.str` recipe (sections 9-14 of `RELEASE_NOTES.md`) is likely
sufficient on its own, ornate title included, with no need for the
named-slot-plus-CSF detour this document spends most of its length on.
That detour is specifically a Cyrillic (or CJK, or any script starting
beyond U+00FF) problem.**

**These are two independent requirements, not one — know which one you
actually need before copying a language's approach:**
1. **A real named slot (not `english`)** — needed only so the engine reads
   `lotr.csf` at all (§2-3). Irrelevant to whether the byte-widen bug
   happens; Turkish's own dedicated `turkish` slot uses `.str`, not CSF.
2. **CSF instead of `.str`** — needed only to dodge the byte-widen bug on
   the one ornate-title-class widget (§6, this section). Irrelevant to
   which slot it's in.

Ukrainian needs **both**, together: a named slot so CSF is read at all,
*and* CSF specifically (not just any named slot) so Cyrillic survives that
one widget. Copying only Turkish's part of the recipe (a dedicated slot,
plain `.str`) would read fine everywhere else but reproduce the exact same
`×àêëóâàííÿ`-style mojibake on the ornate title that the `english`-slot
`.str` build already had — the slot name was never the cause of that one
bug, the text format was.

---

## 7. `FontSubstitution` still matters, and has a subtlety of its own

`data\ini\fontsubstitution.ini` (per-language, e.g. inside `french.big`)
lets you redirect requests for a font family name to a different one, with
a size table (`Size <requested> = <substitute-size> "<SubstituteFamily>"`).
Per the file's own documentation comment: sizes interpolate between
adjacent defined anchors, and values are clamped to the lowest/highest
size specified — so a sparse table (e.g. just `Size 8` and `Size 40`) is
*supposed* to cover every size in between and beyond via interpolation/
clamping.

**Observed gotcha:** for `.str`-fed text specifically (the `english`-slot
recipe), the *presence* of a `FontSubstitution` rule for a given font
family appears to be what flags that family's text as needing a real
codepage-aware decode at all. Removing the `"Albertus MT"` substitution
block entirely (reasoning: "the stock font already has the right glyphs,
no substitution needed" — which is true, see §9) still broke *all*
Cyrillic text project-wide, reverting to the same kind of mojibake §2
describes for raw UTF-8-in-`.str`. Restoring a **self-referencing** rule
(`FontSubstitution "Albertus MT" -> "Albertus MT"`, no custom font file
needed) was sufficient to fix it again. This is specific to the `.str`
delivery path — it was never re-tested whether CSF-delivered text has the
same requirement (untested, but the §1 recipe includes the substitution
blocks anyway since they cost nothing and are needed regardless for the
`SachaWynter` role, which never has Cyrillic in any stock font checked).

Different official localizations ship meaningfully different size tables
for the same `SachaWynter` substitution (Russian: 14 explicit sizes,
1:1-mapped to themselves; French: 14 explicit sizes with real upscaling,
e.g. `Size 8 = 12`). Neither matches the stock English rule's sparse
2-entry table (`Size 8 = 12`, `Size 40 = 70`). The exact numbers don't
appear to be load-bearing magic — copy a real, working table rather than
inventing one, but don't assume Russian's specific numbers are the "right"
ones either.

---

## 8. Font files: check what's already there before building a custom one

Every stock `albertusmt.otf` checked this session (English 2.01's own
`data1.big`, and Russian 2.1's own `data1.big`) **already has real
Cyrillic glyph coverage out of the box** — confirmed with fontTools cmap
inspection: 66/256 of the Cyrillic Unicode block, including every letter
needed for a test word. **It does not have the four Ukrainian-specific
letters** (Ґ/ґ U+0490/U+0491, і U+0456, ї U+0457, є U+0454) — confirmed
absent by direct cmap lookup, despite otherwise looking "already Cyrillic."
`sachwt__.ttf` (the `SachaWynter` role) and `omnialtstd.ttf` (`Omnia LT
Std`) have **zero** Cyrillic coverage in every install checked, English and
Russian alike — not even base Russian letters.

**Practical implication:** for a language that only needs the Cyrillic
letters shared with Russian, the stock `Albertus MT` may already be
sufficient with no custom font work needed for that role at all — only
`SachaWynter`/`Omnia LT Std` need a substitute. For Ukrainian specifically
(needs Ґ/і/ї/є), a custom font supplying at least those four glyphs is
still required for full correctness, even though the bulk of the alphabet
was never actually missing.

A custom font used via `FontSubstitution` must have an internal family
name **distinct** from what it's replacing, or the registration is
ambiguous (registering two different files under the same family name is
documented — BFME1 `TOOLKIT_NOTES.md` §3.7, and confirmed again for BFME2 —
as unreliable, not "last one wins"). Renaming a font's internal family
(nameID 1/3/4/6 in its `name` table) is done with `fontTools`
(`TTFont(...)['name'].setName(...)`) — see
`002_BFME_2/005_BFME2_UKRAINIAN/beta/fonts/rename_albertus_family.py` for
a working example. This project's `AlbertusMTUA.otf` is exactly the stock
Albertus MT renamed to a distinct family this way, used both for BFME2 and
reused as-is for RotWK.

---

## 9. Hard rules — things that will cost you a session or crash the game
## if ignored

- **Never edit `ini.big` or `maps.big`** (shared, non-per-language
  archives). Only touch the per-language archive
  (`<slot>.big`/`<slot>patch201.big`). This was already established for
  BFME2 (`002_BFME_2/005_BFME2_UKRAINIAN/BETA_PATCH_NOTES.md` §6) and
  re-violated once on RotWK during font debugging: a blind regex meant to
  bulk-replace font names also matched `ResolutionFontAdjustment = 1.0` (a
  float multiplier, not a font name — the regex only checked that the key
  *contained* the substring "Font") and rewrote it as a string, which
  **crashed the game outright** with a fatal INI-parser error on startup.
  If you ever need to bulk-edit font declarations for a diagnostic test,
  scope the regex precisely (require a trailing `<size> Yes|No` pattern, as
  real font-role lines actually have) — never match on a bare key
  substring.
- **Never add/edit a `FontSubstitution "Generals"` block, and don't bother
  editing `headertemplate.ini` beyond `AptGadgets`/`AptGadgetsTiny`.**
  Settled dead code, see §5.
- **A file's mere presence inside this repo does not mean it's a proven
  fix.** This repo uses a `prototype/` naming convention specifically to
  mean "unverified, don't treat as ground truth" — a `prototype/`
  `headertemplate.ini` that rewrites every role to `"Arial"` was mistaken
  for a proven BFME2 fix once and applied to RotWK; the actual confirmed-
  working BFME2 beta (per its own `BETA_PATCH_NOTES.md` §6, "Everything
  touched, final state") never touches `headertemplate.ini` at all. When
  checking "what did a sibling project already do," check its *actual
  shipped output and its own written notes*, not any file sitting in its
  folder tree.
- **`.exe`/`game.dat` are the same binary across every language SKU** — a
  reasonable, industry-standard assumption for this kind of data-driven
  localization, not independently re-verified by hashing across a
  reinstall this session, but treated as correct (and there is no evidence
  against it). Whatever differs in behavior between language slots is
  driven entirely by data (registry `Language` value + which archives
  exist + their content), not by different code per SKU.
