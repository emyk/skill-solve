# Approach a — Minimal fix: transliterate to ASCII via NFKD inside `slugify`

## Diagnosis
`slugify` (shop/utils.py:9) lowercases the input and replaces every run of characters outside `[a-z0-9]` with `-`. `è`, `û`, `é` are outside that range, so each one becomes a separator. That is how "Crème Brûlée" turns into `cr-me-br-l-e`. Nothing removes accents before the regex runs. `normalize_whitespace` is a no-op, but whitespace is not the problem here. `product_url` (catalog.py:5) is the only caller.

## The change
One file, shop/utils.py:
- Add `unicodedata` to the existing stdlib import line (line 2).
- In `slugify`, before the regex, decompose the text and drop the combining marks:
  `unicodedata.normalize('NFKD', s).encode('ascii', 'ignore').decode('ascii')`, applied to `normalize_whitespace(x)`.
  The current regex, `.lower()` and `.strip('-')` stay as they are. Two or three lines change in total. Leave `normalize_whitespace` and `catalog.py` alone.

NFKD (not NFD) also folds compatibility characters such as the `ﬁ` ligature into `fi`. It also handles input that already arrives decomposed (`e` + U+0300).

## Tests to add
In tests/test_cart.py:
- `product_url('Crème Brûlée') == '/p/creme-brulee'`
- Optional: the decomposed form `'Crème'` gives `'/p/creme'`.

## Trade-offs and risks
- Letters that have no decomposition are dropped, not transliterated: `ß` gives `strae`, `Ø` gives nothing, and CJK gives an empty slug. This already happened before the fix, so nothing regresses. Proper transliteration would need a mapping table or a dependency, which is outside a minimal fix.
- Existing slugs only change for inputs that contain accented letters. Those inputs were broken before anyway.

## Evidence vs. assumptions
- Evidence: the scratch experiment (scratch/exp.py) prints `creme-brulee` and `blue-shirt` for the two inputs. The 2 existing tests pass on the unmodified code.
- Assumption: nobody depends on the old `cr-me-br-l-e` URLs (for example, stored links or redirects).

## Size: S
## Confidence: 9/10
