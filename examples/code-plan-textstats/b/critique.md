# Critique by b

## On a
Objection: It still uses whitespace as the only word boundary, so punctuation *between* words without a space glues them into one bogus token. That is the reported bug again, in another form. `"Hello,world! Hello."` gives `['hello,world', 'hello']`: "hello" is counted once, not twice, and the made-up word "hello,world" appears. The same happens with `"end.Start"` → `'end.start'` and `"word...word"` → `'word...word'`, and the orchestrator found `"hello—world"` and `"one,two"` stay single tokens. The cause is that `tokenize` still runs `text.lower().split()` (textstats/tokenize.py:6); a only trims the ends of each token. So "punctuation stays attached to words" is fixed only when a space follows the punctuation.
Grounding: scratch/crit.py runs a's sketch verbatim. Missing spaces after commas and periods are common in real text (chat, scraped text, OCR), and em dashes without spaces are normal typography.
Severity: major. It passes the required test, but it treats the symptom: the tokenizer still has no definition of a word.
They do better than me: Combining-accent text survives. a strips `\W` only at the ends of tokens, so a decomposed (NFD) "naïve" stays one word. My regex splits it (see "On my own"). a is also the smallest change to existing behaviour: "3.14" and "snake_case" stay whole.

## On c
Objection: c's regex lists `’` as a joiner but never normalises it, so the same word is counted as two different words depending on which apostrophe was typed. `word_frequencies("Don’t don't")` gives `{"don’t": 1, "don't": 1}` (orchestrator's table). Curly apostrophes come from word processors, macOS and iOS smart punctuation, and most published text. In a word-*frequency* library that splits the counts, the same kind of problem as "hello," vs "hello.". c clearly thought about curly apostrophes (it put `’` in the class), yet the result still splits the counts, and none of c's tests cover it.
Grounding: c's sketch `_WORD = re.compile(r"[^\W_]+(?:['’-][^\W_]+)*")` and `_WORD.findall(text.lower())` with no translate step. verification.md row "Don’t don't" → "two different words".
Severity: minor. It meets the verification criteria; the gap is in robustness, and the fix is one line.
They do better than me: Their write-up states the design intent more sharply ("define a word positively; the obvious strip fix is weaker", with the `hello—world` evidence). That makes the reason for choosing a regex over a's approach easy for a reviewer to see.

## On my own
Objection: `[^\W_]` does not match Unicode combining marks (category Mn), so decomposed (NFD) text is split in the middle of a word. `"naïve café"` in NFD gives `['nai', 've', 'cafe']`. I claimed "café works", but that holds only for precomposed (NFC) input. NFD text shows up in macOS filenames and some copy-paste sources. c has the same defect; a does not split such words, though it does drop a trailing accent. A proper fix is `unicodedata.normalize("NFC", text)` before matching, or adding `̀-ͯ` to the class. My plan does neither and has no test for it. My curly-apostrophe step is also a half-measure: Unicode hyphens (U+2010) are not normalised, so `"e‐mail"` → `['e', 'mail']`.
Grounding: scratch/crit.py, and a one-line `python -I` check on `unicodedata.normalize('NFD', 'naïve café')` → `['nai', 've', 'cafe']`.
Severity: minor for this problem (ASCII test inputs), but it is the weakest point of a plan that sells itself as "robust".
