# Critique by c

## On a
Objection: a keeps whitespace as the only word boundary, so punctuation *between* words stays glued in. The same bug comes back as soon as a space is missing after punctuation. `top_words("Hello,world! Hello.")` gives `[('hello,world', 1), ('hello', 1)]`, which is the reported failure with one space removed.
Grounding: Proposed `tokenize` keeps `text.lower().split()` (textstats/tokenize.py:6) and strips only at token edges. Experiment c/scratch/crit.py results:
- `"It ended.Then it began."` → `'ended.then'`
- `"yes/no yes"` → `'yes/no'`
- `"hello—world"` stays one token (the orchestrator's table shows the same)
a cites `\W` being Unicode-aware for em dashes, but that only helps when the dash is surrounded by spaces.
Severity: major. It passes the required test, but it fixes the symptom and leaves the cause in place.
They do better than me: a keeps "3.14", "3.50" and "i.e" as single tokens, where b and I split them into "3", "14" and "i", "e". So a's change to existing behaviour is smaller and less opinionated.

## On b
Objection: Beyond the reported bug, b turns several debatable choices into tested behaviour: `3.14` → `3`, `14` and `snake_case` → `snake`, `case` (listed under its trade-offs), plus eight new tests that pin them. Nobody asked for these. Splitting `"$3.50, i.e. 3.5"` into `3, 50, i, e, 3, 5` (crit.py) adds made-up "words" like `i` and `e` to frequency counts. Pinning that in tests makes it harder to change later.
Grounding: Proposed tests in b/approach.md. crit.py shows identical output from b and c on every input except curly apostrophes.
Severity: minor. b's core is the same regex as mine. Its tests could simply stop pinning the number/underscore cases.
They do better than me: b normalises `’`/`‘` to `'`, so `Don’t` and `don't` count as one word. Mine keeps them as two different words: crit.py gives `['don’t', "don't"]`. For a word-counting library that is a real correctness gap in my version, and b's fix costs one line.

## On my own
b strictly dominates my approach. It uses the same regex and the same diagnosis, plus apostrophe normalisation that I left out. As a result, mine double-counts `Don’t`/`don't`. Like b, I also break decimals and abbreviations into fragments (`3.5` → `3`, `5`; `i.e.` → `i`, `e`). This is the one area where a's edge-stripping behaves better.
