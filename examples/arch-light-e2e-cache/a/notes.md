## Read
- `shop/catalog.py:12-28`: `load_catalog` parses the whole file. `save_product` mutates the dict that `load_catalog` returns, so `load_catalog` must not hand out a cached object.
- `shop/utils.py:170-176`: `atomic_write` writes `path+'.tmp'` and then calls `os.replace`, so every save gets a new inode.
- `shop/sync.py`, `shop/cart.py`: neither calls into the catalog.
- The filesystem is ext4 (`df -T`).

## Ran
All commands ran from `.../a/scratch/`, after copying `shop/` and `tests/` there and patching `catalog.py` as the proposal describes.
- `python3 spike.py`:
  - Stale reads after cross-process same-size saves: 0/300.
  - In-process back-to-back saves: 1000/1000 correct.
  - `load_catalog` calls for 1000 unchanged finds: 0.
  - 20k products: 48040 µs uncached vs 4.0 µs cached.
- `python3 -m pytest -q tests` → 4 passed.
- A loop of 1000 quick `write_json` calls with `os.stat` → mtime_ns was identical 0/1000 times and the inode was identical 0/1000 times. mtime alone would have been enough on this ext4, but the inode is the guarantee.

## Rejected
- TTL cache: it serves stale data within the TTL, which violates the HARD requirement.
- Caching inside `load_catalog`: `save_product` mutates the result, which would poison the cache, and it changes the semantics.
- inotify, file locks or a version-counter file: more parts, and not stdlib-portable (inotify). stat already gives the guarantee.
- Comparing mtime only: coarse-clock filesystems can produce equal mtimes. The inode costs nothing extra.

## Doubts
- `deepcopy` cost on very large products. A shallow `dict(...)` might be enough if callers only read.
- Non-atomic external writers on coarse-mtime filesystems, or NFS attribute caching, would break the guarantee. Either would change my mind toward adding a content hash.
