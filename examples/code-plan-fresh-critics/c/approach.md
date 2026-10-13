# Approach c — Root cause: slugify's one regex conflates "part of a letter" with "word separator"; fold letters first, then separate

## Diagnosis
The symptom is not "accents are dropped": they are turned into **separators**. `slugify` (shop/utils.py:9) has a single character class, `[^a-z0-9]`, that sends everything outside ASCII to the same place as `!` and spaces. The rule it breaks: *a character that belongs to a letter must never split a word*. Proof: the same name in NFD form (`e` + U+0300) gives `cre-me-bru-le-e`. So the accent mark itself becomes a hyphen, and the output even depends on how the input happens to be encoded. `normalize_whitespace` is a stub, but it is not the cause. Whitespace is already collapsed by `[^a-z0-9]+`, and an accent-folding step does not belong under that name. No earlier layer feeds in bad data: "Crème Brûlée" is a valid name. The bug is in slugify's model of what a character is.

## The change
In `shop/utils.py` only, rewrite `slugify` as a pipeline that sorts each character into one of three classes **before** any regex runs:
1. `unicodedata.normalize('NFKD', x.casefold())`. Casefold rather than lower, so `ß` becomes `ss` and `ﬁ` becomes `fi`. NFKD splits each precomposed letter into a base letter plus combining marks, and also handles NFD input.
2. **Delete** the combining marks: `''.join(c for c in s if not unicodedata.combining(c))`.
3. (Optional, recommended) **Transliterate** letters that have no decomposition, using a small module-level `str.maketrans` table: `ø→o, æ→ae, œ→oe, đ→d, ł→l, þ→th, ð→d, ı→i`. Today `Smørrebrød` gives `sm-rrebr-d` and `Ærø` gives `r`.
4. Only then **separate**: keep the existing `re.sub(r'[^a-z0-9]+', '-', s).strip('-')`.
Add `import unicodedata`, leave `normalize_whitespace` alone and keep the signature `slugify(x, pct=None)`. `catalog.product_url` stays unchanged.

**Obvious fix and why I didn't choose it:** `unicodedata.normalize('NFKD', x).encode('ascii', 'ignore').decode()` inserted before the regex. It passes the new test, but it only moves the problem: it silently **deletes** every letter it can't encode (`Straße`→`strae`, `Smørrebrød`→`smrrebrd`). The single bucket of "unknown characters" stays, and its fate just changes from "hyphen" to "nothing". Classifying characters as mark, foldable letter or separator fixes the model itself.

## Tests to add (tests/test_cart.py or new tests/test_slugify.py)
- `product_url("Crème Brûlée") == "/p/creme-brulee"` (required)
- `slugify(unicodedata.normalize('NFD', "Crème Brûlée")) == "creme-brulee"` (encoding-independence, the actual broken invariant)
- `slugify("Straße") == "strasse"`; if step 3 is adopted, `slugify("Smørrebrød") == "smorrebrod"`
- existing `Blue  Shirt!` stays `blue-shirt`

## Trade-offs and risks
- **Changes existing URLs** for any already-published non-ASCII product names (`cr-me-br-l-e` becomes `creme-brulee`). Any approach has this cost. If URLs are stored or indexed anywhere, redirects are needed. I found no persistence in the repo.
- NFKD compatibility folding also rewrites things like `№`→`no` and `½`→`1/2` (the slash then becomes `-`). That is acceptable for slugs, but it is a behaviour change.
- The transliteration table is a policy choice and is not exhaustive. Scripts such as CJK or Cyrillic still become separators or empty. A full transliteration would need a dependency, and the project uses only the stdlib.

## Evidence vs. assumptions
Evidence (run): current output is `cr-me-br-l-e`; NFD input gives `cre-me-bru-le-e`; the proposed steps 1, 2 and 4 give `creme-brulee` for both encodings and `strasse` for Straße; ascii-ignore gives `strae`; the existing 2 tests pass. Assumption: no stored slugs depend on the old output, and the ASCII-only slug policy is intended (inferred from the regex).

## Size: S
## Confidence: 9/10
