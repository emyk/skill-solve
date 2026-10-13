## Read
- `shop/utils.py:7-9`: slugify = one regex `[^a-z0-9]+`→'-' over `.lower()`; non-ASCII chars are treated exactly like punctuation.
- `shop/utils.py:18-21`: normalize_whitespace is a stub, but whitespace is already handled by the `+` in the regex. Not the cause.
- `shop/catalog.py:4-5`: product_url = '/p/' + slugify(name); the only caller. No stored slugs anywhere in the repo.
- `tests/test_cart.py`: 2 tests (total, Blue  Shirt!).
## Ran
- `python -m pytest -q` → 2 passed
- current slugify: 'Crème Brûlée'→`cr-me-br-l-e`; NFD form→`cre-me-bru-le-e`; Straße→`stra-e`; Smørrebrød→`sm-rrebr-d`
- NFKD(casefold) + drop combining + same regex → `creme-brulee` (both NFC and NFD), `strasse`, `fish-o1` for 'ﬁsh №1'
- NFKD + ascii-ignore → `strae`, `smrrebrd` (silent letter loss)
## Rejected
- NFKD+encode('ascii','ignore'): passes the test but deletes letters it can't decompose (ß, ø).
- Implementing normalize_whitespace: wrong layer/name, and it would not fix accents.
- Unicode-aware regex `[\W_]+` (keeps é in slug): yields non-ASCII URLs and fails the target `/p/creme-brulee`.
## Doubts
- Whether the translit table (step 3) is in scope or gold-plating. It is optional; the core fix is steps 1, 2 and 4.
- Old-URL compatibility: if slugs are persisted outside this repo, redirects are needed.
