# Critique by a

All three pass the target (`product_url("Crème Brûlée") == "/p/creme-brulee"`) and keep `Blue  Shirt!` -> `blue-shirt`. I re-implemented each one as specified in `a/scratch/crit.py` (run with `python3 -I`). So the differences are about scope and edge cases, not about whether the fix works.

## On b
Objection: b puts a hand-maintained table in front of the normalization step, and that table only sees letters in their precomposed lowercase/uppercase form. So it misses the very cases it was added for whenever the letter arrives in another form. b also widens the change beyond the bug. It rewrites `slugify` and removes the `normalize_whitespace` call at shop/utils.py:9. That call is the hook this stub-filled module (utils.py:18-21, like most helpers in the file) was evidently wired for.
Grounding: experiment `a/scratch/crit.py`, which runs b's pipeline in b's order (translate, then NFKD, then drop marks, then ascii-ignore). Results: `STRAẞE` (capital sharp s, U+1E9E) gives `strae`, and `Ǿl` gives `l`, because `Ǿ` only becomes `Ø` + mark after NFKD, when the table has already run. c's order (casefold, NFKD, then table) gives `strasse` and `ol` for the same inputs. The `normalize_whitespace` removal is in b/approach.md step 2. The target test does not need it.
Severity: minor. The target passes. The edge cases are rare, but they show the table is order-fragile, and the extra rewrite is scope the bug doesn't call for.
They do better than me: common Western and Nordic letters come out right (`Straße`->`strasse`, `Ærø`->`aero`, `Smørrebrød`->`smorrebrod`). Mine silently gives `strae`, `r` and `smrrebrd`. b also specifies the broadest regression tests.

## On c
Objection: c's diagnosis says "a character that belongs to a letter must never split a word". But the transliteration step (step 3) that makes this true for ø/æ/œ is marked "optional". Without that step, c's core fix (steps 1, 2 and 4) still gives `Smørrebrød` -> `sm-rrebr-d`, which is the exact separator symptom c claims to fix at its root. With step 3 included, c is essentially b's table approach. So the "root cause" framing promises more than the core change delivers. A builder who takes "optional" at face value gets a fix that is only partial by c's own standard.
Grounding: `a/scratch/crit.py`, c without the table: `Smørrebrød`->`sm-rrebr-d`, `Øl`->`l`, `Ærø`->`r`. c/approach.md step 3 is labelled "(Optional, recommended)", and c/notes.md "Doubts" calls it possible gold-plating.
Severity: minor. The target test passes either way. The issue is that the claimed invariant is not delivered unless the optional part is built.
They do better than me: `casefold()` before NFKD fixes `ß`/`ẞ` -> `ss` at no cost and in the right order. c also explicitly tests encoding independence (NFD input), the invariant that is actually broken. And c's step order (fold first, map after) is more robust than b's.

## On my own
Objection: my fix trades one visible failure for a silent one. Today `Straße` gives `stra-e`, which is plainly broken. With NFKD + `encode('ascii','ignore')` it gives `strae`, and `Ærø` gives `r`, `Smørrebrød` gives `smrrebrd` and `Øl` gives `l`. Those are plausible-looking but wrong slugs nobody will notice. My approach said "nothing regresses". Strictly, the output changes from obviously wrong to quietly wrong. c shows that adding `.casefold()` (one call) fixes ß/ẞ, and b and c show that a roughly 8-entry table fixes ø/æ/œ. Both are within "minimal" range.
Grounding: a/notes.md "Ran" (`Straße`->`strae`, `Øl`->`l`), confirmed again in `a/scratch/crit.py`.
Severity: minor for this ticket. The required test passes and nothing in the repo stores slugs (catalog.py:5 is the only caller). It becomes major if the shop sells products with German or Nordic names.
