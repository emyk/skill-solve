# Judgment
Verdict: WINNER c (build step 3 as mandatory, and casefold after NFKD)

## Per approach
| Approach | Diagnosis correct? | Simplicity | Consistency | Risk | Effort | One-line verdict |
|---|---|---|---|---|---|---|
| a | Yes for the reported case. utils.py:9 sends non-ASCII to `-`; NFKD + ascii-ignore fixes it | Best (about 2 lines, 1 import) | Best: keeps the signature and the `normalize_whitespace` call | Low, but ß/ø/æ/œ/ł/ı are now silently deleted (`Straße`→`strae`, `Ærø`→`r`), which can make two products share a URL | XS | Correct and minimal, but it fixes the slug policy in a lossy form |
| b | Yes | Medium: a table plus a rewrite of `slugify` | Weaker: renames `x`→`text` and drops the `normalize_whitespace` call, neither needed for the bug | Low–medium: a keyword-API change, plus ascii-ignore still deletes letters the table misses (`STRAẞE`→`strae`, `Kırmızı`→`krmz`) | S | Good coverage, but more churn than it needs and order-fragile |
| c | Yes, and it is the clearest. Its NFD claim (`cre-me-bru-le-e`) is verified | Medium: casefold, NFKD, drop marks, a small table, then the existing regex | Good: keeps the signature, the stub call and the regex | Low. Two small flaws, both conceded in its own critique: (1) step 3 is marked "optional"; (2) casefold before NFKD loses `™` (`Café™`→`cafe`) | S | The best policy once step 3 is required and the order is fixed |

## Why
All three diagnoses match the code. `slugify` (shop/utils.py:9) lowercases the text, then maps every run outside `[a-z0-9]` to `-`, so accented letters become separators. `normalize_whitespace` is an unrelated stub, and `product_url` (catalog.py:5) is the only caller. All three pass the target and the 2 existing tests. I re-ran them in `judge-scratch/j.py` (baseline: `pytest` 2 passed). The decision comes down to what happens to Latin letters that NFKD cannot decompose. Any change here alters published slugs, so the policy should be right the first time.

a turns `sm-rrebr-d` into `smrrebrd` and `Straße` into `strae`. That trades a visible failure for silent deletion and new collisions (`Straße` and `Strae` both give `strae`). c-full gives `strasse`, `smorrebrod`, `aero`, `oeuf`, `lodz`, `kirmizi`, and handles NFD input and capital ẞ. It has no ascii-ignore backstop, so a letter it does not know becomes a visible `-` rather than vanishing. b reaches about the same coverage, but adds an API rename and removes the stub call, and it still misses ẞ and ı. c's extra cost over a is about 6 lines and a small table. That buys real correctness for the same bug class, so the larger approach earns its place here.

If the user wants strictly the ticket's single case and the catalogue is known to be French-only, a is an acceptable minimal choice.

## Objections that mattered
- **"a silently deletes undecomposable letters and creates URL collisions"** (raised by b [major] and c against a) — **holds.** Verified: `Straße`→`strae`, `Ærø`→`r`, `Œuf`→`uf`, `Kırmızı`→`krmz`. a's claim that "nothing regresses" is wrong for uniqueness, because `stra-e` and `strae` were distinct before. It does not block the ticket's test, but it is the main reason a loses.
- **"c's core fix, without the optional table, still turns letters into separators"** (raised by a and b against c) — **holds.** Verified: c-core gives `Smørrebrød`→`sm-rrebr-d` and `Ærø`→`r`. It is resolved by making step 3 mandatory, which the verdict requires.
- **"c casefolds before NFKD, so compatibility characters that decompose to uppercase are lost"** (raised by c against itself) — **holds, minor.** Verified: `Café™`→`cafe` with c, `cafetm` when casefold runs after NFKD. It is resolved by moving the casefold after NFKD. That ordering also keeps ẞ→ss, ı→i and Ǿ→o (checked: column `cf2`).
- **"b's table runs before NFKD and is case-sensitive, so it misses ẞ and Ǿ"** (raised by a and c against b) — **holds, minor.** Verified: `STRAẞE`→`strae`, `Ǿl`→`l`.
- **"b renames `x` and drops the `normalize_whitespace` call"** (raised by a and by b against itself) — **holds as unneeded churn.** It has no functional effect in the repo today.

## Borrow from runners-up
- From b: the extra tests `"--x--"`→`"x"`, `""`→`""`, `Œuf`→`oeuf`, and the docstring note that non-Latin scripts (CJK) still give `''`.
- From a: keep the diff contained to `slugify` plus one import, and leave `normalize_whitespace`, the `pct=None` signature and catalog.py untouched.

## What to watch when implementing
- Order of operations: `unicodedata.normalize('NFKD', x)` → `.casefold()` → drop `unicodedata.combining` characters → `.translate(table)` → the existing regex and `strip('-')`. Casefolding after NFKD keeps `™`→`tm`.
- The table needs only lowercase keys, because it runs after casefold: ø, æ, œ, đ, ł, þ, ð, ı. Do not add an ascii-ignore backstop. Unknown letters should stay visible as separators rather than vanish.
- Keep `normalize_whitespace(x)` as the input to the pipeline, to stay consistent with the current code.
- Tests: the required `product_url("Crème Brûlée") == "/p/creme-brulee"`, the NFD form of the same name, `Straße`/`STRAẞE`→`strasse`, `Smørrebrød`→`smorrebrod`, and the existing 2 tests.
- Existing non-ASCII slugs change (`cr-me-br-l-e`→`creme-brulee`). Nothing in the repo stores slugs, but production redirects may be needed. This applies to every approach.
