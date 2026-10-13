## Read
- `shop/catalog.py:12-28`: load_catalog parses every call; save_product = load, mutate the returned dict, write_json.
- `shop/utils.py:170-176`: atomic_write writes `path+'.tmp'` then os.replace → every save is a new inode.
- requirements.md: HARD never-stale cross-process; criteria correctness 45 / simplicity 35 / speed 20.
## Ran
- `python3 spike.py /tmp`, `python3 spike.py <c/scratch>`, `python3 spike.py /dev/shm` (from c/scratch; 2000 iterations, two same-size atomic saves back to back) → all: `mtime+size_missed=0 bare_inode_reused=0 pinned_inode_missed=0` (ext4, tmpfs).
- 200 rapid writes, inline python → 200/200 distinct mtime_ns, min step ~46µs (fine-grained timestamps on kernel 6.18).
## Rejected
- mtime+size key: the obvious design (other solvers' territory); risks lie on 1s/coarse-mtime FS (HFS+, FAT, some NFS) — not reproduced here.
- bare st_ino compare without holding fd: inode numbers can be reused once freed (XFS/tmpfs do this); pinning removes that.
- inotify/push invalidation: not stdlib.
## Doubts
- Spike did not show the mtime design failing, so the advantage is theoretical on this box.
- Windows: held fd blocks os.replace — would disqualify if Windows matters.
- In-place external writers would be missed; I can't tell if any exist.
