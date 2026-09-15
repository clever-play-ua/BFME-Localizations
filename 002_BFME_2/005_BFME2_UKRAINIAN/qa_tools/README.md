# QA tools (vendored, third-party)

Used by the Ukrainian translation QA pass (spelling + Latin/Cyrillic "i" confusables).
Not part of the game or the toolkit itself — just local tooling.

- `hunspell_uk/uk_UA.dic` + `uk_UA.aff` — Ukrainian hunspell dictionary,
  from [brown-uk/dict_uk](https://github.com/brown-uk/dict_uk) release v6.8.5
  (`hunspell-uk_UA_6.8.5.zip`, the same dictionary LibreOffice/Mozilla ship).
- `spylls_pkg/spylls/` — [spylls](https://github.com/zverok/spylls) 0.1.7,
  a pure-Python (MIT-licensed) Hunspell-compatible spellchecker, vendored
  because the embedded Python under `000_TOOLKIT/BFME-loc-toolkit/python/`
  has no `pip`/network-install path.

Usage: add `qa_tools/spylls_pkg` to `sys.path`, then:
```python
from spylls.hunspell import Dictionary
d = Dictionary.from_files(r'qa_tools/hunspell_uk/uk_UA')
d.lookup('слово')       # bool
list(d.suggest('слвоо'))  # candidate corrections
```
