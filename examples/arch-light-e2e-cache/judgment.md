# Judgment
Verdict: WINNER a
## Scores
| Criterion (weight) | a | c |
|---|---|---|
| Correctness of invalidation (45) | 4 | 3 |
| Simplicity (35) | 5 | 3 |
| Lookup speed (20) | 4 | 4 |
| **Weighted total /100** | **87** | **64** |
## Why
a changes only `find_product`: one `os.stat` per call and a deepcopy on each hit. It leaves the `load_catalog`/`save_product` contracts alone, works on any OS, and has a spike behind it: 0/300 stale reads across processes, 4 µs vs 48 ms per lookup, and the tests pass. c's identity check is exact in principle. But it returns a shared, mutable cache from `load_catalog`, holds an fd open (POSIX only), and touches two functions, all to fix an edge case that neither spike could reproduce (c says so itself in its notes).
## Objections that mattered
- **c's cache hands out shared objects, so a caller's mutation is served back and then written to disk on the next save** (raised by a against c). This holds. `save_product`'s `dict(...)` is a shallow copy, so the product dicts inside are still shared, and a's experiment shows the mutated value reaching disk. That is a real correctness risk under the HARD never-stale rule, so c loses correctness points.
- **a's "the inode is the guarantee" claim is false because ext4 reuses freed inodes** (raised by c against a). This holds. I reproduced it in `judge-scratch/`: after two more saves the current file had the first file's inode number in 500/500 runs on ext4. a's actual protection is therefore `mtime_ns` plus size, which is fine-grained on this machine (0 misses measured). A stale read would need a coarse-mtime filesystem and two same-size saves within one clock tick. This is a minor-to-major risk, not a fatal one. I docked a one point on correctness.
## Borrow from runner-up
- Correct the docs and comment in a: freshness comes from `(st_ino, st_mtime_ns, st_size)` together, not from the inode alone.
- c's in-process idea, done without holding an fd: if `save_product` drops `_cache[path]` after it writes, same-process saves become exactly fresh whatever the clock resolution. That's one extra line.
## Risks to watch in the winner
- Coarse-mtime or NFS attribute-cached filesystems combined with fast same-size cross-process saves. If deployment ever moves there, add a content hash or a generation counter.
- The cost of the deepcopy on large product records. If profiling shows it matters, a shallow copy is likely enough.
- The cache dict grows without bound when many distinct paths are used (unlikely here).
