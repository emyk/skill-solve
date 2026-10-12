# Approach b — Most robust / maintainable: define a "word" once, as a named regex in `tokenize.py`, and extract words instead of splitting on whitespace

## Diagnosis
`textstats/tokenize.py::tokenize` is `text.lower().split()`, so any non-whitespace run is a "word": trailing/leading punctuation stays attached (`hello,` / `hello.`) and pure-punctuation tokens (`-`, `!!!`) count. All three public functions (`word_frequencies`, `top_words`, `average_word_length` in `stats.py`) go through `tokenize`, so the single fix point is `tokenize`; `stats.py` needs no change. Side effect of the bug: `average_word_length` is also inflated by punctuation.

## The change
Only `textstats/tokenize.py`. Replace "split on whitespace" with "find word-shaped runs", with the definition of a word stated explicitly at module level:

```python
import re

# A word is a run of letters/digits (any script), optionally joined by internal
# apostrophes or hyphens: "don't", "well-known". Punctuation around words, and
# tokens with no letters/digits at all ("-", "!!!"), are not words.
_WORD_RE = re.compile(r"[^\W_]+(?:['-][^\W_]+)*")
_APOSTROPHES = str.maketrans({"’": "'", "‘": "'"})  # curly -> straight

def tokenize(text):
    """Split text into lowercase words, ignoring surrounding punctuation."""
    return _WORD_RE.findall(text.lower().translate(_APOSTROPHES))
```
- `[^\W_]` = Unicode letter or digit (excludes `_`), so `café`, `über` work.
- Internal `'`/`-` kept so contractions/hyphenated compounds stay one word; leading/trailing ones (`'quoted'`, `--flag`) are stripped.
- Curly apostrophes normalised so `Don’t` and `don't` count as the same word.
- Keep `.lower()` (not `casefold`) to avoid changing existing behaviour beyond scope.

## Tests to add (`tests/test_stats.py`; optionally a new `tests/test_tokenize.py` for the tokenizer cases)
- `top_words("Hello, world! Hello.") == [("hello", 2), ("world", 1)]` (the required one)
- `"-" not in word_frequencies("well - that is that")` and full Counter == `{"that":2,"well":1,"is":1}`
- `tokenize("!!! ---") == []` and `average_word_length("!!! ---") == 0.0` (punctuation-only text = empty)
- `tokenize("don't well-known") == ["don't", "well-known"]` (internal joiners kept)
- `tokenize("'quoted' --flag") == ["quoted", "flag"]` (edge joiners stripped)
- `word_frequencies("Don’t don't")["don't"] == 2` (apostrophe normalisation)
- `average_word_length("hi, yo!") == 2.0` (punctuation no longer inflates length)
- `tokenize("Café Über") == ["café", "über"]` (non-ASCII letters)

## Trade-offs and risks
- Deliberate definitional choices that a reviewer should agree with: `3.14` → `["3","14"]`, `snake_case` → `["snake","case"]`, `rock 'n' roll` → `n`, em-dash splits (`em—dash` → `em`,`dash`). Documented in the regex comment; acceptable for word stats.
- `average_word_length` results change for punctuated input — this is a correction, but it is a behaviour change.
- No new dependencies; regex is precompiled; public API unchanged.

## Evidence vs. assumptions
- EVIDENCE: all functions route through `tokenize` — read `stats.py` → yes, `word_frequencies` and `average_word_length` call it; `top_words` calls `word_frequencies`.
- EVIDENCE: existing suite passes today — `python -m pytest -q` → 5 passed.
- EVIDENCE: regex gives the required behaviour and the edge cases above — scratch/exp.py → `Hello, world! Hello.` → `['hello','world','hello']`; `well - that is that` → no `-`; `!!! ---` → `[]`; `don't`, `well-known`, `café` kept; `'quoted'` → `quoted`; `x y y z z z` unchanged.
- EVIDENCE: without normalisation `Don’t` ≠ `don't` — exp.py printed `['don’t']` (curly kept) → normalisation needed.
- ASSUMPTION: callers want contractions/hyphenated compounds as single words — no spec or other callers in repo (single `init` commit, README silent).
- ASSUMPTION: existing 5 tests still pass after the change — inferred from regex output on their inputs (`a b a`, `Cat cat CAT`, `x y y z z z`, `""`, `ab abcd`), not run against a patched tree.

## Size: S
## Confidence: 9/10
