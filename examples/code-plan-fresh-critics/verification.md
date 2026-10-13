# Verification (orchestrator)
Repo untouched by solvers. All three cite shop/utils.py:7-9 correctly (regex `[^a-z0-9]+` after `.lower()`, no accent folding) and agree normalize_whitespace (utils.py:18-21) is irrelevant.
- a: NFKD + encode('ascii','ignore'). Fixes the target; drops ß/ø/æ letters (a's own notes: Straße→strae, Øl→l).
- b: transliteration table (ß→ss, æ→ae, œ→oe, ø→o, ł→l, đ→d, þ→th) + NFKD + drop marks; removes the stub call; adds tests.
- c: casefold + NFKD + drop combining marks + existing regex; optional table. casefold handles ß→ss.
None disqualified. b and c overlap (both fix ß), differing in table vs casefold and scope.
