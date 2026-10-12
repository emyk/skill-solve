# Judgment
Verdict: WINNER c
## Why
b and c use the same pattern: b's `_WORD_CHARS = r"[^\W_]+"` plus `_JOINERS = r"['’-]"` builds exactly c's `re.compile(r"[^\W_]+(?:['’-][^\W_]+)*")`. I ran both worktrees on 8 edge inputs and they gave identical output on all of them. a's `w.strip(string.punctuation)` fixes the reported repro, but it only covers part of the cause. ASCII-only stripping leaves Unicode punctuation attached, so `“Hi” — he said…` gives `['“hi”', '—', 'he', 'said…']`. That lone `—` is a punctuation-only word, the same bug class that `test_punctuation_only_tokens_are_not_words` targets with `-`. a also leaves `one,two` as a single token. Of b and c, c reaches the same behaviour with less code: one commented regex line and a one-line docstring in `tokenize.py`, against b's three named pieces plus a doctest. c's 6 focused tests also suit this small repo better than b's 12.
## Per solution
| Sol | Correct? | Simplicity | Consistency | Risk | Perf | One-line verdict |
|---|---|---|---|---|---|---|
| a | Partial: passes oracle and regression; Unicode punctuation (— “ ” …) still sticks to words or counts as a word; `one,two` not split | Best (2 lines) | Good | Low; keeps `3.14`, `e.g`, `snake_case` whole | Fine | Fixes the repro, not the whole bug class |
| b | Yes (19 pass) | Good, but the regex is split into 3 constants plus a doctest | Good; adds a new test file | Same as c: splits `3.14`, `C++`, `snake_case`, drops possessive `’` | Fine (compiled) | Correct but more verbose twin of c |
| c | Yes (13 pass) | Very good: one compiled regex | Good; short docstring, tests in style of `test_stats.py` | Same policy changes as b, documented in report | Fine (compiled) | Correct, concise, root-cause fix |
## Borrow from runners-up
- From b: `test_punctuation_only_text_has_no_words` (`tokenize("... -- !? ---") == []`) and `average_word_length("?!") == 0.0`. Each is a one-line test that pins the empty-result path.
## Concerns about the winner
- Policy changes that maintainers should accept explicitly: `3.14` becomes `3`, `14`; `e.g.` becomes `e`, `g`; `C++` becomes `c`; `snake_case` becomes `snake`, `case`; `a--b` becomes `a`, `b`; the trailing possessive apostrophe in `students’` is dropped. For word statistics these look reasonable, but they are wider changes than the bug report asks for.
## Disagreements
- a's report calls ASCII-only stripping "a known gap" that is "fine". I disagree: a standalone em dash `—` still counts as a word, which is the same defect as the `-` case the oracle tests.
- b says its version is "clearer than" the alternatives and the "most robust". Its behaviour is identical to c's on every input I tried, so the extra structure buys no robustness.
