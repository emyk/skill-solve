# Critique by c
Experiments: `c/scratch/crit.py` (run with `python -I`) re-implements a, b and c (core = steps 1, 2 and 4; full = with the step-3 table) exactly as each approach.md describes, and runs them on the target string plus a few realistic product names.

## On a
Objection: a's `encode('ascii','ignore')` turns "this letter became a hyphen" into "this letter silently disappears". That creates new URL collisions the current code doesn't have. `Straße` and `Strae` both become `strae` under a. Today they are distinct (`stra-e` vs `strae`). The same goes for `Kırmızı Elma` → `krmz-elma` and `Smørrebrød` → `smrrebrd`. a's approach.md says "nothing regresses". That is false for uniqueness: two different products can now map to the same `/p/` URL, and `product_url` (shop/catalog.py:5) has no disambiguation.
Grounding: scratch/crit.py output: `Straße a=strae`, `Strae a=strae`, `cur=stra-e`. a's own notes.md records `Straße→strae, Øl→l`.
Severity: minor for the stated test, which a passes. Major if the catalogue has any German, Nordic or Turkish names.
They do better than me: they are the smallest and most obvious diff (about 2 lines). Every reviewer recognises the NFKD+ascii idiom, and a can't make a policy mistake in a transliteration table, because it has none.

## On b
Objection: b's final `.encode('ascii','ignore')` safety net brings back exactly the silent-deletion bucket that b's own notes reject. Any letter its table forgets is erased with no signal. b also does case-sensitive translation before lowercasing, so the table has to list both cases, and it misses capital ẞ (U+1E9E): `STRAẞE` → `strae` while `Straße` → `strasse`. The same product name in caps gets a different URL. Turkish dotless ı isn't in the table either: `Kırmızı Elma` → `krmz-elma`.
Grounding: scratch/crit.py output: `STRAẞE b=strae`, `Kırmızı Elma b=krmz-elma`. b's table as listed in b/approach.md step 1 has no ẞ and no ı. The `casefold` that b rejected in notes.md ("handles only ß") would have covered ẞ.
Severity: minor. The target test and the 2 existing tests pass.
They do better than me: b commits to the transliteration table and writes tests for it (`Œuf→oeuf`, `Smørrebrød→smorrebrod`), and it adds the edge-case tests `--x--→x` and `""→""`. I marked my table "optional". If the builder skips it, my core gives `Smørrebrød → sm-rrebr-d` and `Œuf → uf`, which is exactly today's broken output (crit.py, c_core column). b's table version gives the right answer.

## On my own
Objection: my step order is wrong. I casefold **before** NFKD, but NFKD can produce new uppercase letters from compatibility characters, and nothing lowercases them afterwards. `Café™` → NFKD gives `cafeTM` → the regex removes `TM` → `cafe`, so the trademark text vanishes. a and b both give `cafetm`. The same applies to `℡`, roman numerals `Ⅻ`, and so on. `½` also comes out as `1-2` rather than a/b's `12`, because the fraction slash ⁄ becomes a separator. The fix is to casefold after NFKD (or both before and after). It's a one-token change, but my approach.md claims "NFKD(casefold)" as evidence without having tested any compatibility character that decomposes to uppercase. Second weakness, already conceded above: leaving step 3 "optional" means the core fix alone does not repair ø/æ/œ/ı.
Grounding: scratch/crit.py output: `Café™ c_core=cafe, a=cafetm, b=cafetm`; `½ Price Tee c=1-2-price-tee`.
Severity: minor. The target test and the 2 existing tests pass. Only names with ™, ℡ or roman numerals are affected.
