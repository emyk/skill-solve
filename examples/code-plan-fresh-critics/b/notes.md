## Read
- `shop/utils.py:7-9`: slugify lowercases, then regex `[^a-z0-9]+`→`-`; nothing folds accents, so the bug is here.
- `shop/utils.py:18-21`: normalize_whitespace is a stub; irrelevant, because the regex already collapses spaces.
- `shop/catalog.py:5`: only caller (grep for slugify).
- `tests/test_cart.py`: 2 tests, incl. `'Blue  Shirt!'→'/p/blue-shirt'`.
## Ran
- `python -m pytest -q -p no:cacheprovider` → 2 passed.
- `python -I scratch/exp.py` (NFKD + ascii ignore) → Crème Brûlée→creme-brulee (composed and decomposed); Straße→strae, Œuf→uf, Ærø→r, ﬁne→fine, 寿司→''.
## Rejected
- NFKD + ascii-ignore only: passes the target test but mangles ß/æ/œ/ø (see above).
- unidecode: not stdlib.
- `str.casefold` for ß: handles only ß, not æ/ø/œ; an explicit table is clearer.
- Implementing normalize_whitespace: not needed; it would grow the scope.
## Doubts
- Whether production has stored/indexed old-style slugs; if it does, a redirect or migration would be needed.
- How big the translation table should be; I kept it to common Western/Nordic/Polish letters.
