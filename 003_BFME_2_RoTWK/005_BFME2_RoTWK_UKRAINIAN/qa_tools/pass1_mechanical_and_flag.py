"""
QA pass 1 for RotWK_strings_ua.json - mirrors
002_BFME_2/005_BFME2_UKRAINIAN/qa_tools/pass1_mechanical_and_flag.py exactly
(same two jobs: mechanical Latin-i fix + hunspell/glossary flagging queue),
just re-pointed at RotWK's own translation file. Reuses BFME2's vendored
spylls/hunspell_uk directly rather than duplicating ~ hundreds of KB of
vendored dictionary/library files.

Glossary now also includes BFME2_strings_ua.json (already QA'd this session)
and 007_TERMS&VOCABULARY/LOTR_UA_VOCABULARY.md's established terms, so
correct shared proper nouns (Араґорн, Ґондор, etc.) aren't flagged again.

Run from this directory with the toolkit's embedded python:
    ..\..\..\000_TOOLKIT\BFME-loc-toolkit\python\python.exe pass1_mechanical_and_flag.py
"""

import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
UA_DIR = os.path.dirname(HERE)  # 005_BFME2_RoTWK_UKRAINIAN
REPO_ROOT = os.path.dirname(os.path.dirname(UA_DIR))
BFME2_UA_DIR = os.path.join(REPO_ROOT, '002_BFME_2', '005_BFME2_UKRAINIAN')
BFME2_QA_TOOLS = os.path.join(BFME2_UA_DIR, 'qa_tools')

STRINGS_PATH = os.path.join(UA_DIR, 'RotWK_strings_ua.json')
QUEUE_PATH = os.path.join(UA_DIR, 'RotWK_ua_qa_queue.json')
SUGGEST_CACHE_PATH = os.path.join(HERE, '.suggest_cache.json')

GLOSSARY_SOURCES = [
    os.path.join(REPO_ROOT, '000_TOOLKIT', 'BFME-loc-toolkit', 'locales', '2.22v7.0.4', 'ua', 'strings.json'),
    os.path.join(REPO_ROOT, '000_TOOLKIT', 'BFME-loc-toolkit', 'locales', '1.06', 'ua', 'strings.json'),
    os.path.join(BFME2_UA_DIR, 'BFME2_strings_ua.json'),
]

sys.path.insert(0, os.path.join(BFME2_QA_TOOLS, 'spylls_pkg'))
from spylls.hunspell import Dictionary  # noqa: E402

DICT_PATH = os.path.join(BFME2_QA_TOOLS, 'hunspell_uk', 'uk_UA')


# --- Step 1: Latin i/I -> Cyrillic i/I confusable fix -----------------------

_CYRILLIC_RE = re.compile(r'[А-ЩЬЮЯІЇЄҐа-щьюяіїєґ]')
_WORD_RE = re.compile(r"[^\W\d_]+", re.UNICODE)
_LATIN_I = {'i': 'і', 'I': 'І'}  # -> Cyrillic і / І

_STR_ESCAPE_RE = re.compile(r'\\[nt"\\]')


def _for_spellcheck(text: str) -> str:
    return _STR_ESCAPE_RE.sub(' ', text)


def fix_latin_i_confusables(text: str) -> str:
    def fix_word(m):
        word = m.group(0)
        if not _CYRILLIC_RE.search(word):
            return word
        if 'i' not in word and 'I' not in word:
            return word
        return ''.join(_LATIN_I.get(ch, ch) for ch in word)
    return _WORD_RE.sub(fix_word, text)


# --- Step 2: build a glossary of already-established UA terms ---------------

def build_glossary():
    words = set()
    for path in GLOSSARY_SOURCES:
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

    print('Building glossary from BFME1 + BFME2 UA translations...')
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
                continue
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
