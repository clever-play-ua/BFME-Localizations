# Text storage: BFME1 vs BFME2

Where the actual, in-game translatable text physically lives is not the same
game to game. This note documents that one difference precisely, since it
decides which tool/parser applies to which game.

## BFME1

- The primary, authoritative text store is always a **binary CSF** file:
  `lang\<X>.big` -> `lang\<x>\lotr.csf`.
- A patch (e.g. 2.22) *additionally* ships a plain-text `data\lotr.str`
  override inside its own patch archive (`_patch222.big`). That `.str` file
  only overrides individual labels the patch touched — everything else still
  comes from the CSF.
- Deleting `data\lotr.str` is a valid, supported strategy: the base
  language's own CSF becomes authoritative again for every label (see
  `000_TOOLKIT/TOOLKIT_NOTES.md` §2.2/§3.2 for the full reasoning and the
  caveats around namespaces with no CSF fallback).
- Net effect: CSF = the real database, `.str` = an optional, partial patch
  overlay on top of it.

## BFME2

- Checked directly against a clean, patch-1.05 English install
  (`F:\BFME2\lang\english.big`): there is **no CSF for the main game text at
  all**. `lang\english.big` contains exactly 11 files, and none of them is a
  `lotr.csf`. Confirmed by listing every entry with `pyBIG.Archive.file_list()`.
- The **entire** in-game text (10,411 labels) lives directly in a plain-text
  `data\lotr.str` inside `lang\english.big`.
- The 1.05 patch archive, `lang\englishpatch105.big`, carries its own
  `data\lotr.str` at the exact same internal path (10,459 labels: 49 new, 1
  removed, 276 changed text). By analogy with BFME1's archive-priority rule
  (later-loaded archive wins for an identically-pathed entry — BFME1 notes
  §3.1/§6.1), the patch's copy is expected to be the one that actually wins
  at runtime. **Not confirmed in-game for BFME2** — this is a structural
  analogy, not an observed fact yet.
- The only actual CSF anywhere in the lang folder is a small, unrelated one:
  `lang\english.big -> launcher\launcher.csf` (48 labels) — this is text for
  the standalone patch **launcher** executable (pre-game error dialogs like
  "You must run the game from its install directory"), not for the game
  itself.

## Why this matters for tooling

A tool built for BFME1 assumes "read/patch the CSF, `.str` is optional." That
assumption is simply wrong for a from-scratch BFME2 localization on a clean
1.05 install — there, `.str` is not an optional overlay, it **is** the
database. Any BFME2 workflow has to target `data\lotr.str` in
`lang\<X>.big`/`lang\<X>patch105.big` as the primary edit target, not a CSF.

(Whether a *hand-built* BFME2 localization can instead ship a brand-new
binary CSF as a replacement mechanism, the way `002_BFME_2/005_BFME2_UKRAINIAN`
attempts to, is a separate, unverified question — see
`002_BFME_2/BFME2_structure.json` -> `fonts.unverified_ukrainian_prototype`
for why that specific example should not be trusted as a proven approach.)
