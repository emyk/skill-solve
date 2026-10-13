# Proposal c — Different in kind: pin the parsed file's inode, invalidate on file identity, not timestamps

## Overview
The obvious design caches the parsed dict keyed on `(st_mtime_ns, st_size)` and re-parses when either changes — a *timestamp heuristic*. This one uses an invariant the codebase already guarantees: every save goes through `utils.atomic_write`, which `os.replace`s a fresh file, so **a save always means a new inode**. The cache keeps the file object it parsed *open*; the snapshot is fresh iff `os.path.samestat(os.fstat(held_fd), os.stat(path))`. Holding the fd prevents the old inode from being freed, so its number cannot be reused by the next save — the check is exact, with no timestamp granularity or same-size edge cases. Same-process and cross-process saves are handled by the one check; no notifications, no extra code in `save_product`.

## Components
- `shop/catalog.py` only: module dict `_snapshots = {path: (fileobj, data)}`. `load_catalog`: open the path, `fstat` the opened fd, compare with the held one; if same inode, close the new one and return cached data, else `json.load` and replace (closing the old fd). Missing file → drop entry, return `{}`.
- `save_product`: `catalog = dict(load_catalog(path))` so a failed write can't poison the cache.

## Migration path
1. Add `_snapshots` + identity check in `load_catalog` (~15 lines).
2. Shallow-copy in `save_product`.
3. Add test: two back-to-back same-size saves from a subprocess, then `find_product` sees the second.

## Risks and trade-offs
- Relies on "all writers replace, never write in place". True for `atomic_write`; a hand-edit with an in-place editor would be missed (add `fstat(held).st_mtime_ns` as a cheap belt if wanted).
- One open fd per catalog path; on Windows a held fd makes `os.replace` fail — POSIX only.
- Each lookup still costs one `open`+`fstat` syscall pair (no parse); `find_product` returns a shared dict, so callers must not mutate it.

## Effort and Confidence
~1 hour. Confidence: medium-high in correctness; on this machine (kernel 6.18, ext4/tmpfs) the plain mtime design also never missed a save, so the edge here is robustness on coarse-timestamp filesystems, not a measured win.
