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
  `AlbertusMTUA.otf`, `sachawyntertight_ua.ttf`, `data\ini\fontsubstitution.ini`,
  the 4 texture files in §4
- **Edited:** `language.ini` (2 new `LocalFontFile` lines appended, nothing
  removed)
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

- Attempt 3's own font (AlbertusMTUA/SachaWynterTight) hasn't been
  screenshot-confirmed in-game yet — only attempt 2 (Tahoma) was.
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
