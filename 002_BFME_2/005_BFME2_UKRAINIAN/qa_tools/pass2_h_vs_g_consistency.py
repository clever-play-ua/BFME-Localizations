"""
QA pass 2: find internal г/ґ (and to a lesser extent г/х) inconsistency in
BFME2_strings_ua.json's translated text - the same proper name spelled with
'г' in some lines and 'ґ' in others.

Two complementary checks:

  1. Glossary-anchored: for each name in tolkien_glossary_ua.json, generate the
     г<->ґ swapped variant of its given spelling and count how many entries
     use each variant. Flags a real split.

  2. Corpus-only, glossary-free: group every capitalized Cyrillic word in the
     corpus by its "г/ґ-neutral" form (both letters replaced by a placeholder)
     - two different actual spellings mapping to the same neutral form, both
     appearing more than once, is a strong signal of a real inconsistency,
     independent of whether the name is even in our (incomplete) glossary.

Writes a report json for manual/LLM review - does NOT auto-edit
BFME2_strings_ua.json (unlike pass 1's mechanical Latin-i fix, choosing which
spelling is "right" here is a judgment call, not a deterministic fix).
"""

import json
import os
import re
from collections import defaultdict

HERE = os.path.dirname(os.path.abspath(__file__))
UA_DIR = os.path.dirname(HERE)
STRINGS_PATH = os.path.join(UA_DIR, 'BFME2_strings_ua.json')
GLOSSARY_PATH = os.path.join(UA_DIR, 'tolkien_glossary_ua.json')
REPORT_PATH = os.path.join(UA_DIR, 'BFME2_ua_hg_consistency_report.json')


def swap_h_g(s: str) -> str:
    table = str.maketrans({'г': 'ґ', 'Г': 'Ґ', 'ґ': 'г', 'Ґ': 'Г'})
    return s.translate(table)


def neutral_form(word: str) -> str:
    return word.translate(str.maketrans({'г': '*', 'Г': '*', 'ґ': '*', 'Ґ': '*'}))


with open(STRINGS_PATH, encoding='utf-8') as f:
    strings_data = json.load(f)
entries = strings_data['strings']

with open(GLOSSARY_PATH, encoding='utf-8') as f:
    glossary = json.load(f)


# --- Check 1: glossary-anchored --------------------------------------------

def clean_glossary_value(v: str):
    """Only use values that are a plain name (no parenthetical commentary)."""
    if '(' in v or '/' in v and len(v) > 40:
        return None
    v = v.split('/')[0].strip()
    if not v or 'не знайдено' in v or 'не підтверджено' in v:
        return None
    return v


glossary_terms = {}
for section in ('characters', 'places'):
    for en, ua in glossary.get(section, {}).items():
        cleaned = clean_glossary_value(ua)
        if cleaned and ('г' in cleaned.lower() or 'ґ' in cleaned.lower()):
            glossary_terms[en] = cleaned

glossary_findings = []
for en, ua_spelling in glossary_terms.items():
    variant_a = ua_spelling
    variant_b = swap_h_g(ua_spelling)
    if variant_a == variant_b:
        continue
    stem_a = variant_a[:max(4, len(variant_a) - 2)]
    stem_b = variant_b[:max(4, len(variant_b) - 2)]
    hits_a = [e['var'] for e in entries if stem_a.lower() in (e.get('ua') or '').lower()]
    hits_b = [e['var'] for e in entries if stem_b.lower() in (e.get('ua') or '').lower()]
    if hits_a and hits_b:
        glossary_findings.append({
            'english_name': en,
            'wikipedia_spelling': variant_a,
            'other_variant_found_in_corpus': variant_b,
            'count_matching_wikipedia_spelling': len(hits_a),
            'count_matching_other_variant': len(hits_b),
            'example_vars_wikipedia_spelling': hits_a[:5],
            'example_vars_other_variant': hits_b[:5],
        })

print(f'Glossary-anchored g/h split findings: {len(glossary_findings)}')


# --- Check 2: corpus-only, glossary-free ------------------------------------

_WORD_RE = re.compile(r"[А-ЩЬЮЯІЇЄҐа-щьюяіїєґ'-]+")

spelling_variants = defaultdict(lambda: defaultdict(set))  # neutral -> spelling -> {vars}
for e in entries:
    ua = e.get('ua') or ''
    for w in _WORD_RE.findall(ua):
        if len(w) < 5:
            continue
        if 'г' not in w.lower() and 'ґ' not in w.lower():
            continue
        if not w[0].isupper():
            continue  # only proper-noun-shaped (capitalized) words
        n = neutral_form(w)
        spelling_variants[n][w].add(e['var'])

corpus_findings = []
for neutral, variants in spelling_variants.items():
    if len(variants) < 2:
        continue
    # ignore pure case/declension noise where one spelling is just a prefix of another
    spellings = list(variants.keys())
    total_hits = sum(len(v) for v in variants.values())
    if total_hits < 2:
        continue
    corpus_findings.append({
        'neutral_form': neutral,
        'variants': {
            sp: {'count': len(vars_set), 'example_vars': sorted(vars_set)[:5]}
            for sp, vars_set in variants.items()
        },
    })

corpus_findings.sort(key=lambda f: -sum(v['count'] for v in f['variants'].values()))
print(f'Corpus-only (glossary-free) g/h split findings: {len(corpus_findings)}')

with open(REPORT_PATH, 'w', encoding='utf-8') as f:
    json.dump({
        'glossary_anchored_findings': glossary_findings,
        'corpus_only_findings': corpus_findings,
    }, f, ensure_ascii=False, indent=2)

print(f'Saved: {REPORT_PATH}')
