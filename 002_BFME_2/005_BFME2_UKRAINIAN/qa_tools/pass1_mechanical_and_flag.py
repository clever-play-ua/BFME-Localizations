"""
QA pass 1 for BFME2_strings_ua.json:

  1. Mechanical, deterministic fix: a Cyrillic word containing a Latin 'i'/'I'
     (keyboard-layout mix-up) gets that letter swapped for Cyrillic 'i'/'I'.
     Applied directly to BFME2_strings_ua.json - safe, no judgment call needed.
  2. Spellcheck flagging (hunspell uk_UA + a glossary of terms already
     established in the BFME1 Ukrainian translations, so real proper nouns
     like "Iзенгард"/"Назгул" aren't flagged as typos). NOT auto-corrected -
     written to a separate queue file for manual/LLM batch review, per entry,
     so a review pass can go through it a chunk at a time without re-scanning
     everything or losing track of what's already been looked at.

Run from this directory (qa_tools/) with the toolkit's embedded python:
    ..\..\..\000_TOOLKIT\BFME-loc-toolkit\python\python.exe pass1_mechanical_and_flag.py

Speed: dictionary.suggest() (candidate-correction generation) is by far the
slowest part - spylls is pure Python and tries several correction strategies
per word. Two things make repeat runs fast:
  - suggestions are cached to disk (SUGGEST_CACHE_PATH), keyed by word, and
    reused across runs - a second run only pays the cost for genuinely NEW
    unknown words, not ones already seen before.
  - pass --no-suggestions to skip suggestion generation entirely (still does
    the Latin-i fix and flags unknown words, just without candidate fixes) -
    useful for a quick "did my edit introduce anything new" check.
"""

import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
UA_DIR = os.path.dirname(HERE)  # 005_BFME2_UKRAINIAN
STRINGS_PATH = os.path.join(UA_DIR, 'BFME2_strings_ua.json')
QUEUE_PATH = os.path.join(UA_DIR, 'BFME2_ua_qa_queue.json')
SUGGEST_CACHE_PATH = os.path.join(HERE, '.suggest_cache.json')

BFME1_GLOSSARY_SOURCES = [
    os.path.join(UA_DIR, '..', '..', '000_TOOLKIT', 'BFME-loc-toolkit', 'locales', '2.22v7.0.4', 'ua', 'strings.json'),
    os.path.join(UA_DIR, '..', '..', '000_TOOLKIT', 'BFME-loc-toolkit', 'locales', '1.06', 'ua', 'strings.json'),
]

sys.path.insert(0, os.path.join(HERE, 'spylls_pkg'))
from spylls.hunspell import Dictionary  # noqa: E402

DICT_PATH = os.path.join(HERE, 'hunspell_uk', 'uk_UA')


# --- Step 1: Latin i/I -> Cyrillic i/I confusable fix -----------------------

_CYRILLIC_RE = re.compile(r'[А-ЩЬЮЯІЇЄҐа-щьюяіїєґ]')
_WORD_RE = re.compile(r"[^\W\d_]+", re.UNICODE)
_LATIN_I = {'i': 'і', 'I': 'І'}  # -> Cyrillic і / І

# The .str format's own line-break/escape tokens (literal backslash-n, -t, -")
# are two-character sequences, not real text. Left in place, the "n"/"t" glue
# onto whatever Cyrillic word follows with no space ("...\nПеревага"), and a
# naive word-tokenizer misreads that as a single bogus word "nПеревага". Strip
# these escapes before tokenizing for spellcheck; the stored 'ua' text itself
# is untouched (this only affects what the spellchecker sees).
_STR_ESCAPE_RE = re.compile(r'\\[nt"\\]')


def _for_spellcheck(text: str) -> str:
    return _STR_ESCAPE_RE.sub(' ', text)


def fix_latin_i_confusables(text: str) -> str:
    """Swap a Latin 'i'/'I' for its Cyrillic look-alike, but only inside a
    word that already contains a real Cyrillic letter (so pure-English words/
    placeholders like 'Isengard' or 'IronOre' are left untouched)."""
    def fix_word(m):
        word = m.group(0)
        if not _CYRILLIC_RE.search(word):
            return word
        if 'i' not in word and 'I' not in word:
            return word
        return ''.join(_LATIN_I.get(ch, ch) for ch in word)
    return _WORD_RE.sub(fix_word, text)


# --- Step 2: build a glossary of already-established BFME1 UA terms --------

def build_glossary():
    words = set()
    for path in BFME1_GLOSSARY_SOURCES:
        path = os.path.normpath(path)
        if not os.path.exists(path):
            print(f'  (glossary source missing, skipped: {path})')
            continue
        with open(path, encoding='utf-8') as f:
            data = json.load(f)
        entries = data['strings'] if isinstance(data, dict) else data
        for entry in entries:
            ua = entry.get('ua') or ''
            for w in _WORD_RE.findall(_for_spellcheck(ua)):
                if _CYRILLIC_RE.search(w):
                    words.add(w.lower())
        print(f'  + {path}: {len(entries)} entries scanned')
    return words


# --- Step 3: spellcheck flagging --------------------------------------------

_word_known_cache = {}
_suggest_cache = {}


def check_word(dictionary, glossary, word):
    """True if word is considered known (correctly spelled or an established
    project term); False if it should be flagged for review. Cached per exact
    word string - the same term repeats across thousands of tooltip labels."""
    if word in _word_known_cache:
        return _word_known_cache[word]
    known = (
        word.lower() in glossary
        or dictionary.lookup(word)
        or dictionary.lookup(word.lower())
        or dictionary.lookup(word.capitalize())
    )
    _word_known_cache[word] = known
    return known


def suggest_for(dictionary, word):
    if word not in _suggest_cache:
        _suggest_cache[word] = list(dictionary.suggest(word))[:5]
    return _suggest_cache[word]


def main():
    want_suggestions = '--no-suggestions' not in sys.argv

    if want_suggestions and os.path.exists(SUGGEST_CACHE_PATH):
        with open(SUGGEST_CACHE_PATH, encoding='utf-8') as f:
            _suggest_cache.update(json.load(f))
        print(f'Loaded {len(_suggest_cache)} cached suggestions from a previous run.')

    print('Loading hunspell uk_UA dictionary...')
    dictionary = Dictionary.from_files(DICT_PATH)

    print('Building glossary from BFME1 UA translations...')
    glossary = build_glossary()
    print(f'  glossary size: {len(glossary)} distinct words')

    with open(STRINGS_PATH, encoding='utf-8') as f:
        data = json.load(f)
    entries = data['strings']
    print(f'Loaded {len(entries)} entries from {STRINGS_PATH}')

    fixed_count = 0
    queue = []
    for entry in entries:
        ua = entry.get('ua') or ''
        if not ua:
            continue

        fixed = fix_latin_i_confusables(ua)
        if fixed != ua:
            entry['ua'] = fixed
            ua = fixed
            fixed_count += 1

        unknown = []
        for w in _WORD_RE.findall(_for_spellcheck(ua)):
            if not _CYRILLIC_RE.search(w):
                continue  # pure-Latin token (English leftover, placeholder) - not this pass's job
            if len(w) <= 1:
                continue
            if not check_word(dictionary, glossary, w):
                if w not in unknown:
                    unknown.append(w)

        if unknown:
            suggestions = {w: suggest_for(dictionary, w) for w in unknown} if want_suggestions else {}
            queue.append({
                'var': entry['var'],
                'en': entry['en'],
                'ua': ua,
                'unknown_words': unknown,
                'suggestions': suggestions,
                'status': 'pending',
            })

    with open(STRINGS_PATH, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    with open(QUEUE_PATH, 'w', encoding='utf-8') as f:
        json.dump({'queue': queue}, f, ensure_ascii=False, indent=2)

    if want_suggestions:
        with open(SUGGEST_CACHE_PATH, 'w', encoding='utf-8') as f:
            json.dump(_suggest_cache, f, ensure_ascii=False, indent=2)
        print(f'Suggestion cache updated: {len(_suggest_cache)} words ({SUGGEST_CACHE_PATH})')

    print(f'Latin i/I confusable fixes applied: {fixed_count}')
    print(f'Entries flagged for spelling review: {len(queue)} (out of {len(entries)})')
    print(f'Saved: {STRINGS_PATH}')
    print(f'Saved: {QUEUE_PATH}')


if __name__ == '__main__':
    main()
