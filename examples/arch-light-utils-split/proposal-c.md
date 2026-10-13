# Proposal c — Prune and co-locate: delete the dead helpers, move each live one next to its only caller

## Overview
The obvious design turns `utils.py` into a `shop/utils/` package (text, money, dates, io, http, validation) with a re-export shim, which keeps all 36 functions. This one sorts by **who calls a helper**, not by what topic it belongs to. Only 17 of the 36 helpers are imported or reached through another helper. The other 19 are stubs that nothing calls (identity bodies like `truncate`, `is_email`, `add_business_days`), so they are deleted. Every live helper except `atomic_write`/`ensure_dir` has exactly one consuming module, so it moves into that module. `utils.py` is then deleted, and nothing remains for a new grab-bag to grow from.

## Components
- `shop/cart.py` gets `round_cents, format_price, apply_discount, sum_prices, non_empty, require_fields`
- `shop/catalog.py` gets `normalize_whitespace, slugify, read_json, write_json, is_sku` (+`import re, json`)
- `shop/sync.py` gets `retry, safe_get, build_url, parse_date` (+`import time`)
- New `shop/files.py` (18 lines) holds `ensure_dir, atomic_write`. It is the one helper set with two consumers (catalog through `write_json`, and sync).
- `shop/utils.py` is deleted, along with its 19 dead helpers.

## Migration path
1. Move the functions as listed, along with the stdlib imports they use, and drop each `from .utils import` line.
2. Delete `utils.py`.
3. Run pytest plus an import smoke test of all four modules.

## Risks and trade-offs
- **Boundaries:** cart now holds money rounding and validation code that belongs to no domain. That is fine while cart is its only user. A second user should get a dedicated module then, not now.
- **External `shop.utils` users break.** The soft constraint is met because all 3 importers are updated, but out-of-repo callers would fail. Add a `utils.py` shim only if some are known.
- **Dropped stdlib imports:** the spike caught a NameError when `import re` was missing from catalog, and the import smoke test catches this. The 2 tests don't exercise sync or io.

## Evidence (spike in `c/scratch/w`)
After the move, the 2 tests pass, `write_json` writes to a temp dir correctly, and `sync.fetch` works. Lines across `shop/*.py` fell from about 240 to 127 (+115/−232).

## Effort
About 30 minutes, 5 files.

## Confidence
High (0.85) that it works with no behavior change. Medium on boundary scoring, because cart and catalog absorb general-purpose code.
