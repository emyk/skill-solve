# Proposal b — Most scalable / extensible: turn `shop/utils` into a package of per-domain modules behind a re-export facade

## Overview
Replace `shop/utils.py` with a `shop/utils/` package, one module per existing group. Growth axis it serves: more helpers and more contributors. A new helper lands in its domain module, a new domain gets a new file, and nothing lands back in a grab-bag. `shop/utils/__init__.py` re-exports all 36 names, so `from .utils import x` (the SOFT requirement) keeps working and importers can move over gradually.

## Components
- `shop/utils/text.py`, `money.py`, `dates.py`, `io.py`, `http.py`, `validation.py`: each file holds its group's functions verbatim.
- `shop/utils/__init__.py`: a facade with explicit `from .money import ...` lines and an `__all__`, plus a docstring that says new code should import from the submodule.
- Every cross-group call the orchestrator listed stays inside one group (slugify→normalize_whitespace, write_json→atomic_write→ensure_dir, safe_get→retry, require_fields→non_empty, money→round_cents), so no submodule imports another submodule. Each boundary is closed.

## Migration path
1. `git mv shop/utils.py shop/utils/__init__.py`, then cut each group out into its own file. Splitting the code mechanically by its `# --- group` markers works.
2. Write the facade re-exports and run the tests.
3. Optional follow-up: point cart, catalog and sync at their submodules (`from .utils.money import ...`). Each one is a single-line edit.

## Risks and trade-offs
- 7 files instead of 1. Each submodule repeats the stdlib imports, which can be trimmed per module.
- The submodules `io` and `http` share names with stdlib modules. This is safe under absolute imports (the spike confirms stdlib `io` and `http.client` still resolve), but it can confuse readers. If that matters, rename them to `files` and `net`.
- The facade lets callers keep skipping the boundaries. A lint rule could close that later, but I'm not proposing one now (it would be speculative).
- If any test monkeypatches `shop.utils.X`, it would stop affecting internal calls. No current test does.

## Evidence (spike)
I ran the scripted split in `b/scratch/repo`: 2/2 tests pass, all 36 names are re-exported, and `write_json` works through the facade.

## Effort
About 30 minutes. Roughly 260 lines move, and 0 importer lines change.

## Confidence
High (85%).
