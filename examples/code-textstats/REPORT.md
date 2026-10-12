## /solve result: punctuation sticks to words in `top_words`
Mode: CODE (concrete failing behavior with an expected output) · Solvers: 3 · Verified by: `python -m pytest -q tests/test_punctuation.py` (+ full suite)

**Winner: c (root cause / alternative approach)**: solver confidence 8/10, judge verdict WINNER c
`tokenize()` now matches words (letters or digits, optionally joined by a single `'`, `’` or `-`) instead of splitting on whitespace. Punctuation can't end up in a word, which also fixes `average_word_length`, since it shares the tokenizer. It won because it fixes the whole class of bug (Unicode punctuation, `one,two`, a standalone `—`) in one commented regex, while b's equivalent took more code to do the same thing.

```
 tests/test_tokenize.py | 28 ++++++++++++++++++++++++++++
 textstats/tokenize.py  | 11 +++++++++--
```
```diff
+import re
+
+# A word is a run of letters or digits, optionally joined by a single
+# apostrophe or hyphen ("don't", "well-known"). Everything else, including
+# punctuation and whitespace, separates words and is never part of one.
+_WORD = re.compile(r"[^\W_]+(?:['’-][^\W_]+)*")

 def tokenize(text):
-    """Split text into lowercase words."""
-    return text.lower().split()
+    """Return the lowercase words in text, without surrounding punctuation."""
+    return _WORD.findall(text.lower())
```
(plus 6 edge-case tests in `tests/test_tokenize.py`)

Borrow from runners-up: two one-line tests from b. `tokenize("... -- !? ---") == []` and `average_word_length("?!") == 0.0` both pin down the empty-result path.

| Solver | Angle | Verify | Why it lost |
|---|---|---|---|
| a | minimal fix | pass (2/2, suite 7/7) | `strip(string.punctuation)` is ASCII-only, so `—`, `“”` and `…` still stick to or become words. It also leaves `one,two` as a single token. |
| b | robust / maintainable | pass (2/2, suite 19/19) | Its regex behaves the same as c's on every input the judge tried, but takes 3 constants and a doctest. More code for no extra robustness. |

Disagreements:
- a's report called the ASCII-only gap acceptable. The judge disagrees: a standalone `—` is exactly the defect the repro tests with `-`.
- b claimed to be the "most robust". It is identical in behavior to c.
- Note: b and c **converged independently** on the same regex. That raises confidence in the approach, but it means the angles diverged less than intended.

Policy changes to accept before merging: `3.14` → `3`, `14`; `e.g.` → `e`, `g`; `C++` → `c`; `snake_case` → `snake`, `case`; the trailing possessive `’` is dropped.

**Apply c's diff to your working tree?** (`git apply .claude/solve/<run>/c/solution.diff`, optionally with the two borrowed tests)
