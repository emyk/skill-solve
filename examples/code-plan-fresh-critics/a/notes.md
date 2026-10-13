## Read
- `shop/utils.py:9`: slugify does `re.sub('[^a-z0-9]+','-', normalize_whitespace(x).lower()).strip('-')`, so non-ASCII letters become separators.
- `shop/utils.py:18-21`: normalize_whitespace returns its input unchanged; it plays no part in this bug.
- `shop/utils.py:2`: stdlib imports go on one comma-separated line; `unicodedata` can join it.
- `shop/catalog.py:5`: the only caller of slugify.
## Ran
- `python -m pytest -q` → 2 passed (before any change).
- `python -I scratch/exp.py` → Crème Brûlée→creme-brulee, Blue  Shirt!→blue-shirt, Crème→creme, ﬁne→fine, Straße→strae, Øl→l, 日本→''
## Rejected
- Putting the accent stripping in normalize_whitespace: the name doesn't fit, and it would widen that function's job.
- NFD instead of NFKD: it misses compatibility characters such as ligatures.
- A hand-written accent map: more lines, and still incomplete.
- Allowing Unicode `\w` in slugs: the expected output is ASCII.
## Doubts
- ß and Ø get dropped. If the product owner wants `strasse`/`ol`, a small extra mapping is needed (out of scope here).
