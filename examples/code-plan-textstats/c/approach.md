# Approach c — Root cause: make `tokenize` *match words* instead of *splitting on whitespace*

## Diagnosis
`top_words` and `word_frequencies` are fine; they faithfully count whatever `tokenize` returns. The bug lives one layer down: `textstats/tokenize.py::tokenize` is `text.lower().split()`, i.e. it defines a word negatively ("anything between whitespace"). That model has no notion of what a word *is*, so punctuation glued to a word stays on it ("hello,") and a run of pure punctuation ("-") becomes a word. The broken invariant is "every token is a word"; it leaks into **every** consumer, not just `top_words`: `average_word_length("Hello, world!")` currently returns 6.0 instead of 5.0. So the fix belongs in `tokenize`, not in `stats.py`.

## The change
Only `textstats/tokenize.py`. Replace the split with a positive definition of a word, extracted with a compiled regex:

```python
import re
# a word = run of letters/digits, optionally joined by an inner apostrophe or hyphen
_WORD = re.compile(r"[^\W_]+(?:['’-][^\W_]+)*")

def tokenize(text):
    """Return the lowercase words in text, ignoring punctuation."""
    return _WORD.findall(text.lower())
```
`[^\W_]` = Unicode letters/digits (not underscore), so "café" works. Inner `'`/`-` keep "don't" and "well-known" whole; a lone "-" or "—" or "..." can never match. `stats.py` is untouched.

**Obvious fix, and why not:** keep `.split()` and do `w.strip(string.punctuation)` per token, dropping empties (either in `tokenize` or, worse, in `word_frequencies`). It passes the new test, but it still treats whitespace as the word boundary: `"hello—world"` stays one token (em dash isn't whitespace or in `string.punctuation`), `"(word)"`-style cases rely on ASCII-only punctuation lists, and patching in `word_frequencies` would leave `average_word_length` wrong. Matching words directly removes the whole class of bug rather than trimming its symptoms.

## Tests to add (tests/test_stats.py)
- `top_words("Hello, world! Hello.") == [("hello", 2), ("world", 1)]`
- `"-" not in word_frequencies("well - that is that")` and `== Counter({"that": 2, "well": 1, "is": 1})`
- `average_word_length("Hello, world!") == 5.0` (pins the shared-root-cause symptom)
- `word_frequencies("don't stop; well-known")` has keys `"don't"`, `"well-known"` (pins inner-punctuation policy)

## Trade-offs and risks
- Behaviour change beyond the reported bug: "3.5" -> "3","5"; "x_y" -> "x","y"; "e-mail" kept whole. These are policy choices; acceptable for a word-stats library but worth stating.
- Leading/trailing apostrophes dropped ("'tis" -> "tis", "dogs'" -> "dogs").
- Slightly slower than `split()`; irrelevant at this scale. No new dependencies (`re` is stdlib).

## Evidence vs. assumptions
- EVIDENCE: counting layer is correct, tokenizer is the source — read `stats.py`/`tokenize.py`: all three public functions go through `tokenize`, which is just `lower().split()`.
- EVIDENCE: same root cause produces a second bug — ran `average_word_length("Hello, world!")` → 6.0 (should be 5.0).
- EVIDENCE: proposed regex fixes both cases — scratch run: `"Hello, world! Hello."` → `['hello','world','hello']`; `"well - that is that"` → `['well','that','is','that']`; `"--- ..."` → `[]`; `"don't well-known café — 3.5"` → `["don't",'well-known','café','3','5']`.
- EVIDENCE: existing inputs unaffected — regex on "a b a", "Cat cat CAT", "ab abcd", "" gives same tokens as `split()`; current suite: 5 passed.
- EVIDENCE: obvious strip-fix is weaker — `'hello—world'.split()` + strip → `['hello—world']`.
- ASSUMPTION: users want "don't"/"well-known" as single words and numbers split on "." — no spec or README states a policy.

## Size: S
## Confidence: 8/10
