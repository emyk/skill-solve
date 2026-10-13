# Requirements (ARCH, light depth)
HARD: no behavior change; no new dependencies; all tests pass.
SOFT: existing `from shop.utils import x` imports keep working, or every importer is updated in the same change.
Criteria: clear module boundaries 40 · migration risk 30 · churn (lines/files touched) 30
