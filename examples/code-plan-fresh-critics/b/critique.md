# Critique by b
(Experiment: `RUN_DIR/b/scratch/crit.py` runs a, b, c-core (steps 1, 2 and 4) and c-full (with the step-3 table) on the same inputs. Baseline re-run: `pytest -q`, 2 passed.)

## On a
Objection: a fixes "Crème Brûlée" by **silently deleting** every letter that NFKD cannot decompose. It ships slugs that are wrong in a new way: `Straße`→`strae`, `Smørrebrød`→`smrrebrd`, `Ærø`→`r`, `Œuf`→`uf`, `Łódź`→`odz`. Every slug-policy change breaks published URLs (a's own trade-off section concedes that slugs change). So adopting a now means a second round of URL breakage when someone files "Smørrebrød → /p/smrrebrd". The cost of the URL change is paid once either way. It should buy a correct policy.
Grounding: crit.py output (a column). The deletion comes from `.encode('ascii','ignore')` placed before the regex at shop/utils.py:9. a's notes.md records `Straße→strae, Øl→l` and defers them as "out of scope".
Severity: major. It passes the required test and both existing ones, but it locks in a lossy policy for Germanic, Nordic and Polish names, which are the next most likely product names after French ones.
They do better than me: a is the smallest diff. It changes about 2 lines, touches only one import, and leaves the `slugify(x, pct=None)` signature and the `normalize_whitespace` call alone, so review risk is near zero.

## On c
Objection: c's **core** fix (steps 1, 2 and 4, with the table marked "optional") still turns letters into separators. That is the exact failure class c's own diagnosis names as the root cause ("a character that belongs to a letter must never split a word"). c-core gives `Smørrebrød`→`sm-rrebr-d`, `ılık`→`l-k` and `Ærø`→`r`. Those are the same shape as the reported `cr-me-br-l-e`. c's invariant only holds if step 3 ships. If the builder takes "optional" at face value, the bug class stays.
Grounding: crit.py, c_core column. With no ASCII fold, the regex at shop/utils.py:9 still maps every remaining non-ASCII letter to `-`. c's notes.md lists "Whether the translit table (step 3) is in scope or gold-plating" under Doubts.
Severity: minor if step 3 is made mandatory, because c-full is then correct on every input I tried. Major if it is shipped as written ("optional").
They do better than me: `casefold()` before NFKD covers cases my table misses. Capital sharp s `STRAẞE`→`strasse` (mine gives `strae`), and with its table dotless `ılık`→`ilik` (mine gives `lk`). It also keeps `½`→`1-2` instead of my `12`. c-full beats mine on every row of the experiment.

## On my own
Objection: I still end with `.encode('ascii','ignore')` as a backstop. So any letter missing from my hand-written table is **silently deleted**, which is the flaw I charge a with, just on a smaller set: `STRAẞE`→`strae`, `ılık`→`lk`. c's casefold-first ordering closes the ẞ gap with no extra table entry. I also add churn the bug doesn't need: I rename `x`→`text` (that breaks any keyword caller `slugify(x=...)`; none exist in the repo, but it is still an API change) and I drop the `normalize_whitespace` call at utils.py:9. If someone later implements that stub (utils.py:18-21), slugify would silently bypass it.
Grounding: crit.py, b column, rows `STRAẞE` and `ılık`. utils.py:7, 9 and 18-21.
Severity: minor. The required test and the 2 existing tests pass, and the common Western, Nordic and Polish cases are right. On the merits, c-full with the table made mandatory is at least as good as mine, with less churn.
