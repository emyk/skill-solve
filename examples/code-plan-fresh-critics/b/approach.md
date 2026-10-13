# Approach b — Most robust / maintainable: fold text to ASCII explicitly before slugging
## Diagnosis
`slugify` (shop/utils.py:7-9) lowercases the input and then replaces every run of characters outside `[a-z0-9]` with `-`. Nothing converts `è`/`û`/`é` to ASCII first, so they count as separators: "Crème Brûlée" becomes `cr-me-br-l-e`. `normalize_whitespace` is a no-op stub. It is not the cause, because the regex already collapses whitespace.
## The change
All in `shop/utils.py`, text section. `catalog.py` stays as it is.
1. Add a private helper, `_to_ascii(text) -> str`:
   - `text = text.translate(_LATIN_EXTRA)`: a small module-level `str.maketrans` table for Latin letters that NFKD cannot decompose: `ß→ss, æ/Æ→ae, œ/Œ→oe, ø/Ø→o, đ/Đ→d, ł/Ł→l, þ/Þ→th, ð/Ð→d`. Use lowercase targets, because the slug is lowercased later anyway.
   - `unicodedata.normalize('NFKD', text)`, then drop the characters where `unicodedata.combining(c)` is true, then `.encode('ascii','ignore').decode()` to remove anything left over.
2. Rewrite `slugify(text)` as three readable steps with a real docstring (ASCII-fold, lowercase, collapse runs of other characters to `-`, strip `-`). Name the argument `text` and keep the unused `pct=None` parameter for signature compatibility. Remove the `normalize_whitespace` call, because the regex already does that job. Add `import unicodedata`.
3. Document in the docstring that non-Latin scripts (e.g. CJK) still produce `''`, as they do today. That case is out of scope.
## Tests to add
Add to tests/test_cart.py, or to a new tests/test_slug.py:
- `product_url("Crème Brûlée") == "/p/creme-brulee"` (required).
- Decomposed input (`"Crème Brûlée"`) gives the same slug.
- `slugify("Straße") == "strasse"`, `"Œuf"→"oeuf"`, `"Smørrebrød"→"smorrebrod"`, `"ﬁne"→"fine"`.
- Unchanged behavior: `"Blue  Shirt!"→"blue-shirt"`, `"--x--"→"x"`, `""→""`.
## Trade-offs and risks
- Existing URLs that contain accented names change from `cr-me-br-l-e` to `creme-brulee`. Old links break unless redirects exist. Nothing in the repo stores slugs, but production might.
- The translation table is hand-maintained, but small and bounded. A full transliteration dependency (unidecode) is ruled out by the stdlib-only constraint.
## Evidence vs. assumptions
Evidence: scratch/exp.py runs NFKD+ASCII and gives `creme-brulee` for both composed and decomposed input, but `Straße→strae`, `Œuf→uf`, `Ærø→r`. That result is why the extra table is needed. The baseline is 2 tests passing. Assumption: `slugify` has no callers other than catalog.py (confirmed by grep in this repo).
## Size: S
## Confidence: 9/10
