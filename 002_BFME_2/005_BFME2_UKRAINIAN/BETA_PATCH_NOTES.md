# BFME2 Ukrainian — in-game beta patch notes

Companion to `QA_NOTES.md` (which covers the *text QA* pipeline that produced
`BFME2_strings_ua.json`) and `002_BFME_2/BFME2_structure.json` (the general
BFME2 archive/text-system reference). This document covers the separate
step of actually **patching that translation into a live 1.05 install** and
getting it to render correctly — session 2026-09-15.

`beta/` holds the result: `english.big` + `englishpatch105.big`, ready to
copy into a stock 1.05 install's `lang\` folder (registry stays on
`Language=english` — this patches the English slot in place rather than
creating a new `Ukrainian` language folder, matching the same strategy the
Czech/Korean localizations in `002_BFME_2/` use). `beta/build_beta_english_big.py`
rebuilds both files from scratch from a pristine source — see its own
docstring for exact usage; this doc explains *why* each step is there.

## 1. Text: CSF, not `.str`

First attempt wrote the translation into `data\lotr.str` (the format the
stock English install actually ships text in). Result: garbled text in
Ukrainian —"Приведіть Ϊедовеу..."-style mojibake. Root cause: BFME2's
`.str` pipeline is codepage-dependent (raw bytes get decoded through
whatever ANSI codepage is active), and there's no way to declare "these
bytes are cp1251" from inside the file itself.

Real fix, found by reading the **official Chinese Taiwanese and Thai
localizations already in this repo** (`002_BFME_2/001_BFME2_CHINESE_TAIWAN`,
`002_BFME_2/004_BFME2_THAI`) rather than guessing: both ship a **binary
`lotr.csf`** (root path inside their `lang\<x>.big`, e.g. `lotr.csf`, not
`lang\english\lotr.csf` like BFME1) — the exact same UTF-16 CSF format
BFME1 uses, reusing `csf_tools.read_csf`/`build_csf` directly, unmodified.
CSF is real Unicode; no codepage guessing needed at all. `data\lotr.str` is
removed from both `lang\english.big` and `lang\englishpatch105.big` once the
CSF is in place (mirrors BFME1's own "`.str` overrides CSF, so delete `.str`"
finding, `TOOLKIT_NOTES.md` §2.2/§3.2 — the same priority behavior appears to
hold for BFME2, confirmed indirectly since the mojibake disappeared once
`.str` was removed and CSF added).

## 2. Second bug: literal `\n` showing as visible text

Screenshot showed `Пробудження сил природи. \n Всі союзники отримують...`
with the backslash-n printed as literal characters instead of a line break.
Cause: `.str`'s own two-character `\n` escape convention is baked into every
string in `BFME2_strings_ua.json` (that's the source format), but **CSF has
no escape processing at all** — whatever bytes are in the string are shown
verbatim. The exact same bug class BFME1 hit (`TOOLKIT_NOTES.md` §6.5).

Fix: `unescape_for_csf()` (in `build_beta_english_big.py`) converts the
literal two-char sequences `\n`/`\t`/`\"`/`\\` into real
newline/tab/quote/backslash characters before the text goes into
`build_csf()`. Verified directly: `CONTROLBAR:ToolTipTameTheBeast`'s value
now contains a real `\n` (0x0A) byte, not the two characters `\`+`n`.

## 3. Fonts: three attempts, only the third is right

### Attempt 1 — embed a custom font under the SAME family name as stock
Added `albertusmt_ua.otf`/`sachawyntertight_ua.ttf` (already-Cyrillic fonts
from the BFME1 toolkit, `000_TOOLKIT/fonts/`) as extra `LocalFontFile` lines
in `language.ini`, hoping a later declaration for the same family
("Albertus MT") would win over the stock one. **Wrong** — re-reading
`TOOLKIT_NOTES.md` §3.7 carefully, it never actually claims "last one wins"
is *reliable*; it says exactly this kind of same-family/different-filename
setup is **ambiguous**, and BFME1's own real fix was to shadow the stock
file *by identical filename* instead. In-game this showed correctly-encoded
Cyrillic (once the CSF fix above landed) but in the wrong typeface — the
engine was falling back to something like Times New Roman, not our font.

### Attempt 2 — FontSubstitution to a system font (Tahoma)
Found EA's own **Thai** localization's shipped
`data\ini\fontsubstitution.ini` (`002_BFME_2/004_BFME2_THAI/lang/thai.big`)
does real `FontSubstitution "Albertus MT" -> "Tahoma"` /
`"SachaWynter" -> "Tahoma"` rules, and ships **zero custom font files** —
its `language.ini` even comments out the `AlbertusMT.otf`/`SACHINWRG_.TTF`
`LocalFontFile` lines. This confirmed `FontSubstitution` to a totally
different family name is the real, reliable, EA-proven mechanism (unlike
attempt 1's same-name collision). Implemented and working, but abandoned
per the project owner's preference to keep the intended custom typeface
rather than fall back to a generic system font.

### Attempt 3 (final) — FontSubstitution to OUR OWN font, renamed
Combines both lessons: use a real `FontSubstitution` rule (attempt 2's
proven mechanism), but point it at our own embedded Cyrillic font instead of
a system one. This only works if the target font has a family name
**different** from what it's substituting away from — `sachawyntertight_ua.ttf`
already qualifies (`"SachaWynterTight"`, distinct from `"SachaWynter"`), but
`albertusmt_ua.otf` doesn't (`"Albertus MT"`, same as stock, same problem as
attempt 1). Fixed by renaming the font's internal family
(`beta/fonts/rename_albertus_family.py`, using a vendored pure-Python
**fontTools** — no `pip` in the toolkit's embedded Python, downloaded the
wheel directly like `spylls` was for the QA pipeline, see `QA_NOTES.md` §2)
from `"Albertus MT"` to `"AlbertusMTUA"`, producing `beta/fonts/AlbertusMTUA.otf`.
Final `data\ini\fontsubstitution.ini` (added fresh into `lang\english.big`
only — `ini.big`/`maps.big` are never touched, per the project owner's
explicit preference; relies on the per-language archive taking priority for
this file, same assumption `TOOLKIT_NOTES.md` §3.7 establishes for BFME1):

```
FontSubstitution "SachaWynter"
    Size 8 = 12 "SachaWynterTight"
    Size 40 = 70 "SachaWynterTight"
End

FontSubstitution "Albertus MT"
    Size 8 = 8 "AlbertusMTUA"
    ... (one line per size stock lists, all -> "AlbertusMTUA")
End
```

Two new `LocalFontFile` lines are appended to `language.ini` (existing lines
untouched) registering `AlbertusMTUA.otf` and `sachawyntertight_ua.ttf`.

**Not yet re-confirmed in-game after switching from Tahoma to our own font**
(attempt 2 was confirmed working visually; attempt 3 changes only *which*
font family is loaded, same substitution mechanism — should work, but
hasn't had its own screenshot check yet).

### Attempt 4 (actual final, 2026-09-20) — ONE font for both substitution targets, not two

Attempt 3 shipped and was used for months, but it carried a latent bug that
took roughly ten separate debugging sessions (project owner's own count) to
finally pin down, because it only manifests on specific screens and looks
completely unrelated to fonts at first glance.

**Symptom.** On certain screens — confirmed on the Options menu (title area)
and a War-of-the-Ring campaign tutorial popup — a second, garbled line of
text rendered directly under/overlapping each line of otherwise-correct,
readable Ukrainian text. The garbled line looked like a dense hash/lattice
pattern, not recognizable glyphs. Alongside it, the whole screen's UI took on
an unexplained green tint that had never appeared in this project before.
Zooming into the WoTR popup screenshot, the project owner noticed something
specific: the guillemet quote marks («»/„") in that garbled overlay appeared
to be rendering in a visibly different style from the surrounding body text —
i.e. **not uniformly garbled**, but as if two different fonts were being
composited into the same line, one of them missing/misrendering most glyphs.

**Root cause (confirmed).** Attempt 3's `fontsubstitution.ini` pointed the
two `FontSubstitution` blocks at **two different font files**:
`FontSubstitution "SachaWynter"` → `"SachaWynterTight"` (a separate embedded
TTF, `sachawyntertight_ua.ttf`), and `FontSubstitution "Albertus MT"` →
`"AlbertusMTUA"` (a different embedded OTF). Some UI text-rendering path
(exact mechanism not identified — likely some multi-pass/shadow-and-fill
text effect used by certain APT/Scaleform widgets, see `TOOLKIT_NOTES.md`
§3.8 for the general "APT bypasses language.ini, only FontSubstitution
matters" finding) ends up resolving glyphs for the *same* line of text from
**both** substituted fonts at once. When those two font files don't have
matching glyph IDs/metrics/coverage for whatever character set the effect
expects, the mismatched second pass renders as the garbled hash-pattern
duplicate line, and something about that failure mode also pushes the
color blend into green.

**The project owner's own working theory**, which matches the evidence and
is recorded here verbatim in substance: SachaWynter, when configured as a
genuinely distinct font, is missing certain glyphs; whatever text-rendering
path needs a glyph SachaWynter doesn't have pulls it from Albertus MT
*instead*, on the same line, and the two fonts' mismatched metrics produce
the visible artifact. This may be a quirk specific to SachaWynter's own
glyph coverage rather than a general two-font problem — not fully isolated,
but irrelevant to the fix, which sidesteps the question entirely.

**The fix:** stop shipping `sachawyntertight_ua.ttf` at all. Point **both**
`FontSubstitution` blocks at the exact same single font file
(`AlbertusMTUA.otf`):

```
FontSubstitution "SachaWynter"
    Size 8 = 12 "AlbertusMTUA"
    Size 40 = 70 "AlbertusMTUA"
End

FontSubstitution "Albertus MT"
    Size 8 = 8 "AlbertusMTUA"
    ... (one line per size stock lists, all -> "AlbertusMTUA")
End
```

Confirmed fixed in-game by the project owner ("ПРОБЛЕМА решилась") after
rebuilding both `english.big` and the toolkit installer with this change.
`language.ini`'s `LocalFontFile` list also drops the `sachawyntertight_ua.ttf`
line — only `AlbertusMTUA.otf` is registered now.

**A second, unrelated regression surfaced and was reverted while chasing
this bug**: porting RotWK's own `UnicodeFontName = "AlbertusMTUA"` fix
(see `003_BFME_2_RoTWK/ROTWK_TEXT_AND_FONT_SYSTEM.md`) into BFME2's
`language.ini`, on the theory that it might be "cheap insurance," actually
*caused* a very similar-looking glitch (garbled title area + green tint) on
its own, independent of the two-font bug above. BFME2 never had RotWK's
ornate-title mojibake problem in the first place (that bug is specific to
RotWK's `.str`-vs-CSF byte-widening quirk, not present in BFME2's text
pipeline), so there was nothing for `UnicodeFontName` to fix here — only
something to break. **`UnicodeFontName` is left at its stock value for
BFME2 and must not be set to a custom font.** This is a different root
cause from the two-font bug above; both happened to produce a
similar-looking green-tinted garbled overlay, which is what made this so
hard to separate out during debugging.

**Cross-game corroboration — this is a general engine rule, not a BFME2
quirk.** `001_BFME_1/004_BFME1_UKRAINIAN/v3/english.big`, a pre-existing,
independently-built BFME1 Ukrainian localization, uses exactly ONE font
("Noto Sans") for absolutely everything: every `language.ini` font role,
every `headertemplate.ini` role (including the dead `Title`/`MainButton`
"Generals" roles, §2.6 of `TOOLKIT_NOTES.md`), and **both**
`FontSubstitution` blocks — `"SachaWynter"` → Noto Sans AND a
self-referencing `"Noto Sans"` → Noto Sans block. It never uses a second,
different font file anywhere. Separately, `TOOLKIT_NOTES.md` §2.3 (written
in an earlier BFME1 session, long before this BFME2 bug was pinned down)
already reached the same conclusion from a completely different angle:
BFME1's current toolkit output retargets `FontSubstitution "SachaWynter"`
straight to `"Albertus MT"` (the *same* family as the other block, not a
second file) specifically because a separate SachaWynter-clone file was
found to be unnecessary — "no separate font file needed for it at all."
Three independent investigations (BFME1's toolkit code, BFME1's `v3`
hand-built archive, and this BFME2 bug hunt) all converge on the same rule:

> **Never register two different font files for the two `FontSubstitution`
> targets. Use exactly one font, everywhere — every `language.ini` role,
> every `headertemplate.ini` role, and both `FontSubstitution` blocks.**

RotWK's own working build (`003_BFME_2_RoTWK/005_BFME2_RoTWK_UKRAINIAN/release/build.py`)
already followed this rule by the time it was written (its `FONTSUB`
constant points both blocks at `AlbertusMTUA` only) — which is presumably
why RotWK never exhibited this exact duplicate-text bug, though that causal
link wasn't separately re-verified since RotWK never had two fonts to
compare against.

For completeness, the project owner's own informal framing of RotWK's
*separate* text problem (the `.str`-vs-CSF byte-widening bug, fully
documented in `ROTWK_TEXT_AND_FONT_SYSTEM.md`) is worth recording here too,
since it was given in the same conversation: "in the Witch-king game it
looks like there's some add-on on top of the English version that reads
single-byte (looks like the developers were too lazy to finish something)."
That is a fair plain-language summary of the finding, though the actual
documented root cause is more specific — see §2 there for the precise
byte-widen mechanism, which is unrelated to the two-font bug on this page.

## 4. Textures

Four files from `005_BFME2_UKRAINIAN/prototype/lang/Ukrainian/art/compiledtextures/`
were added into `lang\english.big` at their stock paths. Each was checked
against the real stock copy via SHA1 first — all four are genuinely
different content, not accidental duplicates:

| file | stock lives in | prototype size | stock size |
|---|---|---|---|
| `lm\lm_text.dds` | `textures2.big` | 524,416 B | 1,398,256 B |
| `lo\load_w_ea.jpg` | `textures0.big` | 336,771 B | 699,220 B |
| `lo\logowithshadow.tga` | `maps.big` **and** `textures2.big` (2 stock copies, themselves slightly different from each other - not investigated further) | 2,249,038 B | 1,383,717 B / 1,382,700 B |
| `ti\titlescreenuserinterface.jpg` | `textures0.big` | 313,109 B | 658,260 B |

**Caveat, same class as BFME1's `lmtext.jpg`+`lmtext.png` finding
(`TOOLKIT_NOTES.md` §7):** `titlescreenuserinterface` has a `.png` sibling
in `textures0.big` alongside the `.jpg` the prototype provided. Only the
`.jpg` was replaced — if the engine actually reads the `.png` for this
asset, it still needs a proper Ukrainian version. Not confirmed either way.

## 5. Version string branding

`Version:Format2` (`"Version %d.%02d"` → the CSF label that produces the
"Версія 1.06" text visible on the options screen) and `Version:Format3`
(adds a third version component) both got `" UA 0.1 Clever Play"` appended
to their Ukrainian value, e.g. `'Версія %d.%02d UA 0.1 Clever Play'` →
renders as "Версія 1.06 UA 0.1 Clever Play". Same label name and same kind
of edit the project already did by hand for BFME1. `Version:Format4`
(adds a build tag) was left alone - not confirmed to be the one actually
shown anywhere, lower priority.

## 6. Everything touched, final state

`lang\english.big` (relative to a stock 1.05 archive):
- **Removed:** `data\lotr.str`
- **Added:** `lotr.csf` (10,892 labels, real newlines, version-branded),
  `AlbertusMTUA.otf` (only — `sachawyntertight_ua.ttf` was dropped in
  Attempt 4, §3, once it was root-caused as the source of the duplicate-line
  glitch), `data\ini\fontsubstitution.ini` (both blocks retargeted to
  `AlbertusMTUA` only), the 4 texture files in §4
- **Edited:** `language.ini` (1 new `LocalFontFile` line appended for
  `AlbertusMTUA.otf`; `UnicodeFontName` left at its stock value — see §3
  Attempt 4 for why setting it broke things)
- **Untouched:** everything else (`headertemplate.ini`, `commandmap.ini`,
  `tos.txt`, `launcher\launcher.csf`, the 5 stock `art\textures\*.tga`)

`lang\englishpatch105.big`:
- **Removed:** `data\lotr.str`
- **Added:** `lotr.csf` (identical content to the one above)

`ini.big` / `maps.big` / `data1.big` / `_patch103.big`: **never modified** —
touched and reverted once during the attempt-2 experiment, confirmed back to
stock byte-for-byte before this final version.

Backups of the pristine files (`english.big`, `englishpatch105.big`,
`englishaudio.big`) live at `F:\BFME2\lang_backup_original\` on the machine
this was built on.

## 7. Reproducing this

```
cd 002_BFME_2/005_BFME2_UKRAINIAN/beta
..\..\..\000_TOOLKIT\BFME-loc-toolkit\python\python.exe build_beta_english_big.py --source "F:\path\to\a\pristine\1.05\install"
```

`--source` needs a folder containing an untouched `lang\english.big` +
`lang\englishpatch105.big` (e.g. a copy of `lang_backup_original\` restored
under a `lang\` subfolder, or a fresh install). Output lands next to the
script. Re-run any time `BFME2_strings_ua.json` changes — everything here is
derived from that one file plus the fixed set of font/texture assets in
`beta/fonts/` and the prototype's texture folder.

If `AlbertusMTUA.otf` ever needs rebuilding (e.g. the source
`albertusmt_ua.otf` changes), re-run `beta/fonts/rename_albertus_family.py`.

## 8. Open questions / not yet verified

- ~~Attempt 3's own font (AlbertusMTUA/SachaWynterTight) hasn't been
  screenshot-confirmed in-game yet~~ — confirmed in-game, and confirmed
  buggy (duplicate garbled text line + green tint). Superseded by Attempt 4
  (§3), which IS screenshot-confirmed working with no artifacts.
- Whether `lang\english.big` vs `lang\englishpatch105.big` archive priority
  for identically-pathed files actually works the way assumed (patch wins)
  is inherited from BFME1's confirmed behavior, not independently verified
  for BFME2.
- Whether a per-language `data\ini\fontsubstitution.ini` (a file that didn't
  exist there before) actually gets picked up ahead of the shared
  `ini.big`/`maps.big` copies for BFME2 specifically — inherited assumption
  from BFME1 (`TOOLKIT_NOTES.md` §3.7), not independently confirmed. If
  fonts *don't* render correctly, this is the first thing to check.
- `titlescreenuserinterface.png` sibling (§4) — untouched, unknown if it
  matters.
- `Version:Format4` — not customized, not confirmed whether it's shown
  anywhere reachable in-game.
