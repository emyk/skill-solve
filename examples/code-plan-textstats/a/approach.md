# Approach a — Minimal fix: strip leading/trailing non-word chars per token in `tokenize`, drop empties

## Diagnosis
`textstats/tokenize.py::tokenize` is `text.lower().split()` — whitespace-only splitting, so any punctuation adjacent to a word stays in the token ("hello," / "hello." / "world!") and a whitespace-surrounded "-" is a token. `word_frequencies`, `top_words` and `average_word_length` in `stats.py` all go through `tokenize`, so fixing it there fixes all three (including `average_word_length`, which currently counts punctuation in word lengths). Nothing in `stats.py` needs to change.

## The change
One file, `textstats/tokenize.py`, ~4 lines: keep whitespace splitting, strip non-word characters from both ends of each token, and drop tokens that become empty.

```python
import re

_EDGE_PUNCT = re.compile(r"^\W+|\W+$")

def tokenize(text):
    """Split text into lowercase words, ignoring surrounding punctuation."""
    words = (_EDGE_PUNCT.sub("", w) for w in text.lower().split())
    return [w for w in words if w]
```
Why edge-stripping rather than `re.findall(r"\w+")`: internal punctuation is preserved, so "don't", "well-known" and "3.14" stay single words (findall would split them into "don", "t", ...), which is the smaller behavioural change. Why `\W` rather than `str.strip(string.punctuation)`: `string.punctuation` is ASCII-only, so a standalone em dash "—" or curly quotes “word” would still survive — the same bug for non-ASCII input. `\W` is Unicode-aware in Python 3.

## Tests to add (tests/test_stats.py, existing style: one-line asserts)
- `test_top_words_ignores_punctuation`: `top_words("Hello, world! Hello.") == [("hello", 2), ("world", 1)]`
- `test_standalone_dash_not_a_word`: `word_frequencies("well - that is that") == Counter({"that": 2, "well": 1, "is": 1})` (or `"-" not in ...`)
- Optional: `word_frequencies("don't")["don't"] == 1` to pin internal-apostrophe behaviour.

## Trade-offs and risks
- Underscore is a `\w` char, so `_x_` keeps its underscores; acceptable (not punctuation in prose).
- Leading/trailing apostrophes are stripped ("'tis" → "tis", "dogs'" → "dogs"); fine for word counts.
- Hyphen-joined phrases without spaces ("well-known") count as one word — a policy choice; matches the "keep the change minimal" angle.
- Tokens of pure punctuation ("...", "—", "-") vanish entirely, which is the intended fix.

## Evidence vs. assumptions
- EVIDENCE: root cause is whitespace-only split — read `textstats/tokenize.py` → `return text.lower().split()`.
- EVIDENCE: all three stats functions call `tokenize` — read `textstats/stats.py`.
- EVIDENCE: sketch fixes both reported cases — scratch/exp2.py → `['hello','world','hello']`, `['well','that','is','that']`.
- EVIDENCE: ASCII `string.punctuation` variant misses Unicode — scratch/exp.py → `'—'` and `'“curly”'` survived; `\W` variant → dropped/`'curly'`.
- EVIDENCE: existing tests pass on current code (`python -m pytest -q` → 5 passed); the sketch yields identical tokens for their inputs ("a b a", "Cat cat CAT", "x y y z z z", "", "ab abcd") since they contain no punctuation.
- ASSUMPTION: callers want "don't"/"well-known" kept as single tokens — no spec or test says either way.

## Size: S
## Confidence: 9/10
