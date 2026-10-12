# Solver b — Most robust / maintainable
## Approach
The cause is `tokenize` using `str.split()`, which only splits on whitespace. Punctuation stays attached ("hello," and "hello." count as different words), and a standalone "-" becomes a word. All three public functions go through `tokenize`, so I fixed it there and nowhere else. `tokenize` now extracts words with one compiled, documented regex instead of splitting and stripping. A word is a run of Unicode letters/digits (underscore excluded), and runs can be joined by a single internal apostrophe (ASCII or ’) or hyphen. That keeps "don't", "it’s", "well-known" and "rock'n'roll" whole, while leading/trailing punctuation, quotes, standalone dashes and punctuation-only text all drop out. Matching words is clearer than chained `strip` calls and also handles text with no spaces, such as "one,two...three", which strip-based fixes miss. The docstring has a doctest showing the intended behaviour, and a new tokenizer test file pins down each edge case.
## Files changed
- textstats/tokenize.py — replace whitespace split with a regex word matcher (named, commented parts plus a doctest)
- tests/test_tokenize.py — new: 12 tests for surrounding punctuation, punctuation-only input, internal apostrophes/hyphens, typographic apostrophe, leading/trailing joiners, no-space punctuation, numbers, non-ASCII letters, underscores, plus effects on average_word_length and word_frequencies
## Test results
- `python -m pytest -q tests/test_punctuation.py` → 2 passed (failed before)
- `python -m pytest -q` → 19 passed (5 original + 2 repro + 12 new; baseline was 5 passed)
- `python -m doctest textstats/tokenize.py` → Test passed
## Risks
- Behaviour change for all callers, on purpose: `average_word_length` now ignores punctuation ("Hi!" counts as 2 letters, not 3), and punctuation-only text now gives 0.0. No existing test depended on the old behaviour.
- Policy choices that callers might disagree with: digits count as words ("101"); underscores split words ("snake_case" becomes two words); hyphenated compounds are one word; "--" between letters ("a--b") splits; contractions are one token. Other symbols (e.g. "C++", "e-mail@x.com", "3.14") get split up.
- Kept `.lower()` rather than `casefold()` so existing case handling doesn't change.
## Confidence: 9/10
The root cause is fixed in the one shared place, the change is small, both suites pass, and the edge cases are covered by tests. The one remaining question is product policy on the edge cases above.
