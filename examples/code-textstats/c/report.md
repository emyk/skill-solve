# Solver c — Root cause / alternative approach
## Approach
The bug lives where it surfaces: `tokenize` decides what a word is, and all three stats functions inherit its answer. The underlying flaw is that it defines a word *negatively*, as "whatever lies between whitespace". Because of that, every non-space character, punctuation included, ends up inside some token. The obvious patch keeps that model and cleans each chunk afterwards (`w.strip(string.punctuation)`, then drop empty strings). That approach misses Unicode punctuation such as curly quotes, em dashes and `…`. It leaves "one,two" as a single token. It also needs a separate filter step to drop tokens that are only punctuation. Instead I reversed the definition so a word is described *positively*: `re.findall(r"[^\W_]+(?:['’-][^\W_]+)*", text.lower())`, which matches runs of Unicode letters and digits, optionally joined by a single internal apostrophe or hyphen ("don't", "well-known"). Punctuation can now never be part of a token, so the punctuation-only token `-` cannot occur and no cleanup pass is needed. The fix also corrects `average_word_length`, which previously counted punctuation characters in word length.
## Files changed
- textstats/tokenize.py — tokenizer now matches words with a regex (findall) instead of splitting on whitespace
- tests/test_tokenize.py — new tests for the tokenizer: surrounding punctuation, splitting on punctuation without spaces, contractions/hyphenated words, dangling hyphens and quotes, non-ASCII letters and digits, average_word_length no longer counting punctuation
## Test results
- `python -m pytest -q tests/test_punctuation.py` → 2 passed (baseline: 2 failed)
- `python -m pytest -q` → 13 passed (baseline 5 passed; 5 original + 2 repro + 6 new)
## Risks
- Behaviour change for anything that relied on raw tokens: "c++", "e-mail@x.com" and "3.14" now split into several words ("c", "e-mail"/"x"/"com", "3"/"14"). Underscores now separate words. For word statistics this seems reasonable, but it is a judgement call.
- Only one joiner is allowed between letters: "a--b" becomes "a" and "b", and a leading or trailing apostrophe (e.g. the possessive "students'") is dropped.
- Blast radius is limited to `textstats/tokenize.py`, which is used only by stats.py. No public signature changed and no dependencies were added.
## Confidence: 8/10
The repro and all existing tests pass. The fix removes the cause (words defined by what separates them) rather than cleaning up its symptoms. The remaining uncertainty is policy: exactly which characters should count as part of a word.
