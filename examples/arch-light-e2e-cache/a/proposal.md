# Proposal a — Simplest design: a per-path dict cache in `find_product`, validated by `os.stat` on every call

## Overview
Every `find_product` call runs one `os.stat(path)`. If the `(st_ino, st_mtime_ns, st_size)` signature matches the cached one, it serves from memory. Otherwise it re-parses the file. No TTL, no locks, no new module and no change to the writer. The only state is a module-level dict.

## Components
- `shop/catalog.py` only, about 15 lines:
  - `_cache = {}` maps path → (signature, catalog).
  - `_signature(path)` returns the stat tuple, or `None` if the file is missing.
  - `find_product` checks the signature and, on a mismatch, calls `load_catalog(path)`. It returns `copy.deepcopy` of the product, so a caller that mutates the result cannot corrupt the cache.
- `load_catalog` and `save_product` stay uncached and unchanged. `save_product` mutates what `load_catalog` returns, so caching there would leak edits into the cache.

## Migration path
1. Add `_cache`, `_signature` and the new `find_product` body.
2. Add a test where a subprocess saves a same-size change and the next `find_product` sees it.
3. Run the existing tests.

## Risks and trade-offs
- A save always changes the inode, so the cache can't go stale after `save_product`. `atomic_write` creates the `.tmp` file while the old file is still linked, then calls `os.replace`, so the new file always has a different inode. This holds even when mtime has coarse resolution.
- Each lookup still pays one stat syscall, roughly 1–2 µs. That is the price of seeing other processes' saves with no IPC.
- An external editor that rewrites the file in place could keep the same inode, size and mtime tick. That needs a non-atomic writer plus a coarse clock, and nothing in this repo writes that way.
- The dict grows by one entry per distinct path, which is fine at the current scale.

## Effort and Confidence
About 30 minutes. Confidence is high.

## Evidence
The full design was spiked in a scratch copy; all 4 existing tests pass there. In 300 cross-process same-size saves, a warm cache never returned stale data (0/300). Unchanged lookups made 0 calls to `load_catalog`. On a 20k-product catalog, a find took 48 ms uncached and 4 µs cached.
