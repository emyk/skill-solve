# Solver a — Minimal fix
## Approach
`tokenize` split on whitespace only (`text.lower().split()`), so the punctuation next to a word stayed part of the token ("hello," and "hello." were different words), and a lone "-" counted as a word. All three stats functions get their words from `tokenize`, so the fix goes there and nowhere else. Each whitespace token now has `string.punctuation` stripped from both ends, and tokens left empty are dropped. Stripping only the ends keeps punctuation inside a word, so "don't", "well-known" and "e.g" stay whole, where a `\w+` regex would split them. It is one file, standard library only, and no caller changes.
## Files changed
- textstats/tokenize.py — strip punctuation from both ends of each token and drop tokens that end up empty
## Test results
- `python -m pytest -q tests/test_punctuation.py` → 2 passed (was 2 failed)
- `python -m pytest -q` → 7 passed (baseline 5 passed, plus the 2 repro tests)
- Manual check: `tokenize("Don't stop -- well-known (yes)! ... e.g. 'quoted'")` → `["don't", 'stop', 'well-known', 'yes', 'e.g', 'quoted']`
## Risks
- `average_word_length` changes too: it no longer counts edge punctuation and ignores tokens that are only punctuation. This is the intended effect of the fix.
- `string.punctuation` covers ASCII only. Unicode punctuation such as “curly quotes”, « » or the em dash — is not stripped. That is fine for the tests and ASCII text, but a known gap.
- Abbreviations lose their final dot ("e.g." becomes "e.g"). Punctuation inside a word, like "a.b", stays.
## Confidence: 9/10
The fix is small and targets the actual cause; the only real limit is ASCII-only punctuation.
