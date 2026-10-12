# Judgment
Verdict: WINNER b

## Per approach
| Approach | Diagnosis correct? | Simplicity | Consistency | Risk | Effort | One-line verdict |
|---|---|---|---|---|---|---|
| a | Partly. It finds the right place (`tokenize` = `lower().split()`), but leaves whitespace as the only word boundary, so punctuation with no space after it stays attached | Highest: about 4 lines, one regex, keeps the split | Good | Lowest: keeps "3.14", "e.g", "10,000" whole | S | The cheapest fix, but "Hello,world! Hello." still gives `hello,world`, which is the reported bug again |
| b | Yes. It defines a word positively and finds every word | High: one regex plus one `translate` line | Good. Uses a module-level compiled constant with a comment and only touches `tokenize.py` | Medium: splits "3.14", "e.g.", "10,000" and "snake_case" into fragments; changes `average_word_length` on punctuated text, which is a correction | S | Best fit: fixes the cause for all spacings and also merges curly and straight apostrophes |
| c | Yes. Same regex as b | High | Good | Same as b, but `Don’t` and `don't` count as two different words | S | Strictly dominated by b, as c concedes in its own critique |

## Why
All three diagnose the cause correctly: `textstats/tokenize.py:6` is `text.lower().split()`, and all three public functions go through it. All three pass the required test and drop a standalone "-". I checked this in judge-scratch/j.py, and the existing suite passes (5 passed). The difference is what "punctuation attached to words" covers. Under a, `"Hello,world! Hello."` gives `['hello,world', 'hello']`, which I verified, and `"hello—world"` and `"one,two"` stay single tokens. So a only fixes the bug when a space follows the punctuation. b and c fix it for every spacing. The cost is the same size of change, plus a few policy choices about decimals and abbreviations. c uses the same regex as b but lacks b's apostrophe normalisation, so b dominates it. a is genuinely smaller in behavioural change. If the user cares more about keeping "3.14", "e.g." and "10,000" whole than about text with missing spaces, a is a reasonable choice. That is a preference only the user can state, not a correctness gap in b for the reported problem.

## Objections that mattered
- **a keeps whitespace as the word boundary, so `"Hello,world!"` and `"hello—world"` keep their punctuation** (raised by b and c against a): holds. I verified `['hello,world', 'hello']`. This is the reported symptom with one space removed.
- **The b/c regex breaks "e.g.", "U.S.A.", "10,000" and "3.14" into fragments** (raised by a against b and c): holds as a fact. I verified `['e','g','3','14','10','000']`. It is a policy change, not a failure of the stated fix. I rate it major only if the user's texts are full of numbers and abbreviations, and it can be reduced cheaply (see "Borrow").
- **NFD (decomposed) text is split mid-word, e.g. "naïve" becomes `nai`, `ve`** (raised by a against c, and by b against itself): holds, but it is an edge case. It is fixed with one line, `unicodedata.normalize("NFC", text)`. a also mishandles NFD text, slightly, by stripping a trailing accent.
- **c does not normalise `’`, so `Don’t` and `don't` are counted separately** (raised by b against c, and conceded by c): holds. This is why b beats c.
- **b's tests lock in debatable splits ("3.14" becomes `3`, `14`; `snake_case` becomes `snake`, `case`)** (raised by c against b): holds. Don't add tests that pin those cases.

## Borrow from runners-up
- From a's critique: apply `unicodedata.normalize("NFC", ...)` before matching, so decomposed accented words stay whole.
- Optional, if the user wants a's number behaviour: also allow `.` and `,` as internal joiners between digits, e.g. `[^\W_]+(?:(?:['-]|(?<=\d)[.,](?=\d))[^\W_]+)*`. That keeps "3.14" and "10,000" whole. Only do this if asked.
- From c: add the test `average_word_length("Hello, world!") == 5.0`. It pins the shared root cause.

## What to watch when implementing
- Required tests: `top_words("Hello, world! Hello.") == [("hello", 2), ("world", 1)]`, and `word_frequencies("well - that is that") == Counter({"that": 2, "well": 1, "is": 1})`. `tests/test_stats.py` will then need `from collections import Counter`. Also add a no-space case such as `top_words("Hello,world! Hello.")`, so the regression a would miss is covered.
- Keep the new tests in `tests/test_stats.py` as one-line asserts, matching the existing style. Don't pin the `3.14`/`snake_case` splitting.
- Run the 5 existing tests after the change. The tokens for their inputs are unchanged (verified).
