# BFME2 Ukrainian translation — QA pipeline notes

Living reference doc for `002_BFME_2/005_BFME2_UKRAINIAN/`. Companion to
`002_BFME_2/BFME2_structure.json` (overall BFME2 archive/text-system
structure) and `000_TOOLKIT/TOOLKIT_NOTES.md` (the BFME1 toolkit — different
game, some shared lessons). Session: 2026-09-15.

## 1. What's in this folder

- `prototype/` — the original, unverified draft Ukrainian localization this
  whole QA pass started from (`lang/Ukrainian/`, `lang/ukrainianpatch105/`,
  `UkrainianSplash.jpg`). **Status: draft/prototype, not a proven, in-game-
  tested translation** — no font file (`.ttf`/`.otf`) is even present in it,
  though its `language.ini`/`fontsubstitution.ini` reference one by name (see
  `002_BFME_2/BFME2_structure.json` → `fonts.unverified_ukrainian_prototype`
  for the full writeup). Treat its *text* as a first draft; treat its *font
  setup* as an untested intention only.
- `beta/` — the first in-game-tested milestone: `english.big` +
  `englishpatch105.big` ready to drop into a stock 1.05 install's `lang\`
  folder, plus `build_beta_english_big.py` to reproduce them and
  `fonts/` (the renamed Cyrillic fonts + the fontTools-based renaming
  script). See `BETA_PATCH_NOTES.md` for the full story (CSF vs `.str`,
  three font attempts, textures, version-string branding).
- `BFME2_strings_ua.json` — **the actual working file**: `{var, en, ua}` for
  all 10,892 unique labels from `lang\englishpatch105.big`'s `data\lotr.str`
  (the most complete English baseline — see `BFME2_structure.json` →
  `text_system`), with `ua` seeded from `prototype/lang/ukrainianpatch105/
  lotr.str` and then run through the whole pipeline below. This is what a
  future `apply_localization.py`-style BFME2 tool should read from.
- `tolkien_glossary_ua.json` — external reference (Ukrainian Wikipedia +
  direct user corrections), used to settle г/ґ and short-vs-long name
  disputes. Read its `_CAVEAT_important` before trusting any single entry —
  Wikipedia itself isn't fully consistent, some entries are explicitly
  "not found this pass," and a few were corrected in place after being wrong
  (see `known_stem_matching_limitation` and the Rohan entry's own history).
- `BFME2_ua_qa_queue.json` — the **pending spelling-review queue**: every
  entry hunspell (+ the BFME1 glossary) couldn't recognize a word in, with
  candidate corrections attached. Not yet processed — see §5.
- `BFME2_ua_hg_consistency_report.json` — output of the г/ґ consistency
  scanner (pass 2). Regenerated every run; not meant to be hand-edited.
- `qa_tools/` — all the scripts and vendored third-party tools (§2/§3).
- `str_tools_bfme2.py`, `pass1..6*.py` under `qa_tools/` — see §3 for what
  each does and in what order to run them (`run_all.py` does this for you).

## 2. Why a custom pipeline was needed (not just "run a spellchecker")

- **BFME2's own `data\lotr.str` format has two quirks BFME1's toolkit never
  had to handle** — see `002_BFME_2/BFME2_structure.json` →
  `text_system.CRITICAL_BUG_found_in_existing_toolkit_str_parser` and
  `.second_format_quirk_found_in_draft_localization`:
  1. An optional `// context: ...` (or any `// ...`) comment line between a
     label and its quoted text — BFME1's `_STR_BLOCK_RE` regex silently
     mis-parses these (~16% of all labels), losing the real label and
     inventing a bogus one from the comment text.
  2. The prototype translation indents its quoted text with a tab
     (`LABEL\r\n\t"text"\r\nEND`) — again not tolerated by BFME1's regex.
  Fixed in `002_BFME_2/str_tools_bfme2.py`'s `read_str_bfme2()` — two small,
  separate functions (`strip_str_comments`, `normalize_str_quote_indent`)
  rather than touching BFME1's own `csf_tools.py`, which must keep working
  exactly as-is.
- **No `pip` in the toolkit's embedded Python** (`python -m pip` →
  `No module named pip`), but outbound internet access does work via
  `urllib`. So: downloaded a real Ukrainian hunspell dictionary
  (`brown-uk/dict_uk` GitHub release, the same one LibreOffice ships) and
  vendored **spylls** (a pure-Python, MIT-licensed Hunspell port — no C
  extension, no `pip` needed, just drop the package folder in and
  `sys.path.insert`) instead of a real `hunspell` binding. See
  `qa_tools/README.md`.

## 3. The pipeline, in order (`qa_tools/run_all.py` runs all of this)

| # | script | what it does | idempotent? |
|---|---|---|---|
| 1 | `pass1_mechanical_and_flag.py` | Latin i/I → Cyrillic і/І inside any word that also has a real Cyrillic letter (mechanical, auto-applied). Then flags every word hunspell+glossary don't recognize into `BFME2_ua_qa_queue.json` (not auto-fixed). | Yes — second run finds 0 Latin-i fixes, re-flags whatever's still actually unknown. |
| 2 | `pass2_h_vs_g_consistency.py` | Read-only scanner: finds the same capitalized (proper-noun-shaped) word spelled with `г` in some lines and `ґ` in others. Two sub-checks — glossary-anchored (looser, stem-based, **known false-positive risk**, see §4) and corpus-only (exact whole words, reliable). | Yes, pure read. |
| 3 | `pass3_apply_g_normalization.py` | Applies pass 2's *corpus-only* findings: folds the г-minority spelling into whatever the ґ-form already is. | Yes — re-run after a fix finds nothing left. |
| 4 | `pass3b_lowercase_residuals.py` | A short hardcoded list of lowercase adjective/genitive forms pass 2's capitalized-word-only scanner structurally can't see (e.g. "гондорська"). | Yes (`str.replace`, no-ops once fixed). |
| 5 | `pass4_name_corrections.py` | Three specific corrections the project owner confirmed directly (not auto-detected): Рохан (not Рохан with х), Фарамір (not Фарамир), Піпін (not Піппін). | Yes. |
| 6 | `pass5_warg_click_quotes.py` | варг→варґ (same class as pass 3, just a 4-letter word pass 2's ≥5-letter filter misses); клацн→клікн (matches BFME1's own established "Клацніть→Клікніть" terminology); straight `\"..\"` quotes → Ukrainian «...» guillemets (odd/even alternation per string). | Yes. |
| 7 | `pass6_uron_to_shkoda.py` | "урон" (Russian calque, masc.) → "шкода" (proper Ukrainian, fem.), **with full case/gender agreement** — not a word swap, see §4. Refuses to save (prints every leftover instead) if any `урон` occurrence doesn't match one of its rules, rather than guessing. | Yes — 0 occurrences left after a clean run, so it becomes a no-op. |
| 8 | `pass1` again | Refreshes the queue/counts to reflect everything passes 2-7 just changed. | — |

Run order matters (pass 2 must read before pass 3 writes; pass 6's verb regexes
must not clash with `завда*`/`отримує*` matched by pass 1's tokenizer, etc.) —
`run_all.py` encodes the correct order, always use it rather than calling
scripts individually unless debugging one specific step.

**Speed**: `pass1`'s hunspell `.suggest()` call (candidate-correction
generation) is by far the slowest part — spylls is pure Python. Fixed for
repeat runs: suggestions are cached to `qa_tools/.suggest_cache.json` (keyed
by word) and reused, so a second run only pays the cost for genuinely new
unknown words. Pass `--no-suggestions` to `pass1_mechanical_and_flag.py` for
a fast dry-run that only reports counts, without generating candidates.

## 4. Real findings this session (chronological, root causes)

### 4.1 г/ґ was genuinely inconsistent, not a false alarm
Confirmed by direct measurement, not assumption: `CONTROLBAR:`/`OBJECT:`
namespaces (button/tooltip text) tended to use `г` (Гондор, Гімлі, Глоїн...)
while `DIALOGEVENT:`/`SCRIPT:`/`Map:` namespaces (dialogue/flavor text) tended
to use `ґ` (Ґондор, Ґімлі, Ґлоїн...) for the *same name* — strong evidence the
prototype was translated in at least two separate sessions/by different
people with different habits, not random typos. Examples (BFME2 counts before
the fix): Ґондор/Гондор ≈85/150, Ґімлі/Гімлі 2/9, Араґорн/Арагорн 20/1,
Назґул/Назгул 33/2, варґ/варг 29/32.

**Resolution (user-confirmed 2026-09-15): always ґ**, matching what BFME1's
own already-shipped translation overwhelmingly already uses (Ґондор 292 vs
Гондор 67 ≈ 81%, Ґімлі 29 vs 1 ≈ 97%, Ґолум 9 vs 0 = 100%, etc. — checked
directly in `000_TOOLKIT/BFME-loc-toolkit/locales/2.22v7.0.4/ua/strings.json`).
This is a *content decision*, not a spelling rule the scripts can re-derive
on their own — if a brand-new name shows the same г/ґ split pattern in a
future run, it needs the same kind of confirmation, not an assumed "always ґ."

### 4.2 A false positive inside the false-positive hunt
`pass2`'s glossary-anchored check (short substring "stem" matching, e.g.
`'Роган'[:-2]` → `'Рог'`) flagged a bogus 132-vs-1 "Роган/Роґан" split for
Rohan. Root cause: the stem `Рог` also matches inside `рога`/`рогом`, the
ordinary Ukrainian word for "horn" (there's a lot of "Horn of Gondor" text).
The corpus's real, 100%-consistent spelling was `Рохан` (х) the whole time —
confirmed by a direct case-insensitive scan, not by trusting the scanner.
**Lesson, now documented directly in the script's own docstring**: pass 2's
Check 1 (glossary-anchored) is a lead to verify by hand, never a fact by
itself — Check 2 (corpus-only, whole real words) is the reliable one, and is
the only one `pass3` actually acts on automatically.

Separately, and unrelated to that false positive: **the user explicitly
wants `Рохан` changed to `Роган`** (with г) project-wide as a deliberate
choice, overriding what the prototype currently uses 100% consistently.
Implemented in `pass4`.

### 4.3 `\n`/`\t`/`\"` escapes glued to the next word broke naive tokenization — twice
The `.str` format's own escape sequences are literal two-character sequences
(backslash + `n`/`t`/`"`), not real newlines/tabs, and the prototype text
often has zero space after one before the next word starts (`...\nПеревага`).
This broke two different things independently before being fixed:
1. **pass 1's spellcheck tokenizer** read the literal `n`/`t` as glued onto
   the following Cyrillic word, inventing hundreds of bogus "unknown words"
   like `nПеревага`, `nКількість` (fixed: `_for_spellcheck()` strips these
   escapes before tokenizing — the stored text itself is untouched).
2. **pass 6's verb-matching regexes** (`\bЗнижує`, `\bЗавдає`, ...) required a
   word-boundary `\b` immediately before the verb, which doesn't exist
   between a Latin `n` and a following Cyrillic capital letter (`\b` is a
   transition between "word" and "non-word" characters — Latin `n` and
   Cyrillic `З` are *both* "word" characters to Python's regex engine, so
   there's no transition between them at all). Fixed by dropping the leading
   `\b` for these specific enumerated verb forms (safe: they're long,
   distinctive words, not likely to false-match mid-word) and adding
   case-insensitive first-letter alternation (`[Зз]навдає`-style) for verbs
   that can also appear capitalized at the start of a sentence.
**If a future regex needs to anchor on "start of word" in this corpus,
assume it might be glued to a preceding `\n`/`\t`/`\"` and don't rely on `\b`
alone.**

### 4.4 "урон" → "шкода" needed real grammar, not a word swap
"урон" (Russian calque, masculine, absent from the `uk_UA` hunspell
dictionary — 407 raw regex hits, but 86 of those were false positives from
matching inside "Саурон"/"Сауронa"/etc., i.e. **322 real occurrences**) had
to become "шкода" (proper Ukrainian, feminine). Since the genders differ,
every adjective agreeing with the noun, and the noun's own case ending, had
to change correctly depending on grammatical role — verified by reading all
~183 distinct surrounding-context patterns before writing any rule, not
guessed from the word alone:
- `завдає/завдають/завдаючи` (+optional adjective) → **always genitive**
  "шкоди" (`завдати` idiomatically governs genitive; this also silently fixes
  the Russian-calqued accusative-looking `завдає X урон` some lines used
  instead of the correct `завдає X урону`, since both collapse to the same
  correct genitive target).
- `завдається` (passive) → **nominative** "шкода" (шкода is the passive
  verb's grammatical subject here, not its object — different case than the
  active `завдає` above).
- `отримує/отримують` → **accusative** "шкоду" (`отримати` governs
  accusative).
- bare `Знижує/Скорочує/Збільшує/Зменшує` (no adjective) → **accusative**
  "шкоду".
- `Збільшення/Зменшення/Зниження/Скорочення/Підвищення/Завдання` + genitive
  → "шкоди" (already genitive case in the source, no adjective-agreement
  change needed).
- standalone nominative labels ("Урон в ближньому бою:", "Додатковий урон")
  → "Шкода в ближньому бою:", "Додаткова шкода".
- any leftover bare genitive (`урону`/`урона` not caught by a more specific
  rule above — after a percentage, "більше/менше", a preposition) → "шкоди"
  unconditionally (genitive is genitive regardless of what governs it, no
  role-based branching needed for the noun's own case).
`pass6` refuses to save anything if even one `урон` occurrence doesn't match
one of these rules — it prints every leftover and stops, rather than silently
leaving (or mis-guessing) an edge case. Ran clean on the second attempt (the
first attempt's 7 leftovers were all instances of the §4.3 glued-`\n`/
capitalization bug, not a grammar-rule gap).

## 5. What's NOT done yet

- **`BFME2_ua_qa_queue.json`** (spelling-review queue) — **1283 entries**
  (out of 10,892) as of the final `pass1` run this session (started at 1608,
  before the escape-tokenizer fix in §4.3 and the г/ґ/Рохан/Фарамір/Піпін/
  варг/клацн/урон fixes above resolved a chunk of the false positives).
  These 1283 collapse to a much smaller number of *distinct* unknown words
  (582 unique words the last time this was measured, before the fixes above
  — re-count after any further pipeline change) — review by unique word, not
  by entry, since the same term repeats across dozens of tooltip labels.
  Each queue entry carries hunspell's own candidate corrections
  (`suggestions`) as a starting point, not a verdict — some flagged words are
  real typos, many are legitimate game/fantasy terms hunspell just doesn't
  know (add those to a glossary rather than "fixing" them). **Not started**
  as of this doc — this is the next piece of work.
- `tolkien_glossary_ua.json`'s `open_gaps_not_found_this_pass` list (Isengard,
  Shire, Rivendell, Moria, Lothlorien, Edoras, Helm's Deep, Witch-king,
  Isildur, ...) — worth filling in if a future г/ґ-style dispute comes up for
  any of these.
- Font setup for the actual Ukrainian localization (see §1's warning about
  `prototype/` — its `language.ini`/`fontsubstitution.ini` reference font
  files that aren't present anywhere in this repo).

## 6. Recipe: re-running this after new translation text arrives

1. Merge the new text into `BFME2_strings_ua.json` (keep the `{var, en, ua}`
   shape).
2. `qa_tools/run_all.py` (needs the toolkit's embedded Python — see the
   script's own path resolution, it finds it relative to itself).
3. Read the console summary: Latin-i fixes / г-ґ fixes / name-correction
   counts should mostly be 0 on a file that's already been through this once
   — a nonzero count means genuinely new occurrences of a known issue class.
4. If pass 2 reports a *new* glossary-anchored or corpus-only г/ґ split for a
   name not already covered by pass 3/pass 5, that's a new instance of §4.1 —
   verify by hand (checking BFME1's own precedent first, same as §4.1) before
   deciding which spelling to standardize on and writing a new pass (or
   extending `pass5`'s `WARG_FIXES`-style dict).
5. Check `BFME2_ua_qa_queue.json`'s new size against the previous run's — the
   diff is what's actually new and needs review.
