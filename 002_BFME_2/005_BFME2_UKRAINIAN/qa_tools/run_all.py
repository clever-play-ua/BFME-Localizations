"""
Runs the full BFME2 Ukrainian QA pipeline in the correct order, in one shot.

Use this any time BFME2_strings_ua.json changes (new translation merged in,
more prototype text pulled in, a fresh English patch re-sync, etc.) - it's
safe to re-run on an already-clean file: every pass is idempotent (checks
before it writes, no-ops if there's nothing left to fix).

Order matters:
  1. pass1 - mechanical Latin i/I -> Cyrillic i/I fix, then flags spelling
     issues (hunspell + BFME1 glossary) into BFME2_ua_qa_queue.json.
  2. pass2 - scans for г/ґ spelling drift (same name, two spellings) and
     writes BFME2_ua_hg_consistency_report.json. Read-only, no edits.
  3. pass3 - applies the г/ґ fixes pass2 found (capitalized proper nouns
     found by the corpus-only scanner).
  4. pass3b - a short list of lowercase forms pass2's scanner structurally
     can't see (adjectives/genitives derived from a name pass3 already
     fixed in its capitalized form).
  5. pass4 - three specific hero/place-name spelling corrections confirmed
     directly by the project owner (Рохан/Фарамір/Піпін as of 2026-09-15 -
     see QA_NOTES.md before adding more entries here for a NEW name; these
     are hardcoded, not auto-detected).
  6. pass5 - варг->варґ (pass2's scanner requires 5+ letters, "варг" is 4 -
     found by manual review), клацн->клікн (matches BFME1's own established
     terminology), straight "\\"..\\"" quotes -> Ukrainian «...».
  7. pass6 - урон (Russian calque) -> шкода (proper Ukrainian), with full
     grammatical case/gender agreement. Aborts without saving if it finds
     any occurrence its rules don't cover (see the script's own docstring
     before extending FIX rules there).
  8. pass1 again - refreshes BFME2_ua_qa_queue.json so its counts reflect
     everything the passes above just fixed.

What this does NOT do: it does not touch the ~1300 entries still flagged in
BFME2_ua_qa_queue.json for actual spelling review - those need a human/LLM
to read hunspell's suggestions in context and decide. See QA_NOTES.md.
"""
import subprocess
import sys
import os

HERE = os.path.dirname(os.path.abspath(__file__))
PYTHON = os.path.join(HERE, '..', '..', '..', '000_TOOLKIT', 'BFME-loc-toolkit', 'python', 'python.exe')

STEPS = [
    'pass1_mechanical_and_flag.py',
    'pass2_h_vs_g_consistency.py',
    'pass3_apply_g_normalization.py',
    'pass3b_lowercase_residuals.py',
    'pass4_name_corrections.py',
    'pass5_warg_click_quotes.py',
    'pass6_uron_to_shkoda.py',
    'pass1_mechanical_and_flag.py',
]

for i, step in enumerate(STEPS, 1):
    print(f'\n=== [{i}/{len(STEPS)}] {step} ===')
    result = subprocess.run([PYTHON, os.path.join(HERE, step)])
    if result.returncode != 0:
        print(f'{step} failed (exit {result.returncode}) - stopping.')
        sys.exit(result.returncode)

print('\nAll passes completed.')
