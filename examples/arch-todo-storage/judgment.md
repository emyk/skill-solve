# Judgment
Verdict: WINNER b

## Scores
| Criterion (weight) | a | b | c |
|---|---|---|---|
| Correctness under concurrency (25) | 4 | 5 | 3 |
| Performance at 50k (20) | 5 | 5 | 4 |
| Simplicity / maintainability (20) | 5 | 3 | 2 |
| Migration risk & effort (20) | 4 | 5 | 4 |
| Fit with codebase / extensibility (15) | 3 | 5 | 3 |
| **Weighted total /100** | **85** | **92** | **64** |

## Why
All three meet the HARD constraints, and all three bring add/complete at 50k far below 100 ms (a about 2 ms, b about 0.3 ms, c about 0.05 ms). At CLI scale that gap makes no difference, so performance does not separate them. The deciding evidence is F2, sharing under a default umask of 022. I re-ran b's `wt-b/.spike/umask_check.py`, which loads each spike store unmodified. uid 2 fails with `PermissionError` on a (`todo.db` 0644) and on c (`tasks.jsonl.lock` 0644). On b it succeeds, and `todo.db`, `-wal` and `-shm` all come out 0664. So b is the only design whose multi-user claim holds as spiked, without a README step or a lucky umask. b also has the best migration story: one atomic import that refuses a non-empty target, the legacy file renamed rather than deleted, and `todo export` to get back to the old JSON exactly. Its `user_version` migrations are spiked: v1→v2 took 1.9 ms on 50k rows, inside `BEGIN IMMEDIATE`, so they are safe when two users' first runs race. That suits the "room for due dates and tags" criterion. b pays for this in Simplicity: about 120 lines, a protocol and a factory, against a's about 50 lines. That cost is real but smaller than b's lead elsewhere, and the extras that cost the most can be cut (see Borrow). c is a well-executed different-in-kind design. But it hand-rolls locking, torn-tail recovery, id allocation and compaction, all of which SQLite provides. It has the same umask bug, makes the log world-writable on compaction, and its P2 result depends on a compaction policy nobody has decided.

## Objections that mattered
- **Default umask breaks sharing for a** (raised by b and c against a): **holds.** I reproduced it with `umask_check.py`. a's `sqlite_store.py:14` pre-creates with 0o666 but keeps the caller's umask, and a's multi-uid spike forced `os.umask(0o002)` in its workers (`concurrency.py:8`). No data is lost, because the write fails loudly, so H2 and H3 stand. But F2 does not work out of the box. a acknowledged this in its self-critique. The fix is two lines, which is why a loses one point and not more.
- **Default umask breaks sharing for c, and compaction makes the log world-writable** (raised by a and b against c): **holds.** Reproduced: both the lock and the log are 0644 under umask 022. c's race spike ran with `os.umask(0)` in a 2777 directory. c conceded this in its self-critique. Together with the hand-written protocol, this weakens c's 25-point correctness case.
- **b's `open_store` sends `*.json` paths to the unlocked `JsonStore`, so a supported configuration (including the documented rollback `TODO_DB=~/.todo.json`) brings lost updates back** (raised by a and c against b): **holds** as a design flaw at proposal level. It follows directly from the stated dispatch rule and from today's `JsonStore` (`todo/storage.py`: no lock, read-modify-write). It is not in b's spike, and the default path is correct. It is easy to remove, and removing it is a condition of adopting b (see Borrow). I counted it against Simplicity rather than Correctness, because it is opt-in and can be cut.
- **b is overbuilt for the stated needs** (raised by a, c and b itself): **partly holds.** The `Store` protocol (one real implementation) and the suffix factory are YAGNI. The `user_version` migrations are not YAGNI: they are about 10 lines, they are spiked, and a's self-critique admits a would need an ad-hoc equivalent for its first new column. Hence b scores 3 on Simplicity, not lower.
- **c's `list` is slower than today until the log is compacted, which P2 forbids** (raised in verification, and by b and c against c): **holds.** 100–117 ms against about 70–82 ms with 20k uncompacted done events, and the compaction trigger is an open assumption.
- **a's proposal says it avoids `RETURNING`, but its spike uses it** (raised by c against a): **holds** (`wt-a/.spike/sqlite_store.py:31`), but it is minor. b's spike uses `RETURNING` too. It matters only for the Python 3.10 / old-SQLite risk below.

## Borrow from runners-up
- **From a (simplicity):**
  - Drop the suffix-based backend dispatch. `open_store` should resolve only the path (`--db` › `$TODO_DB` › `~/.todo.db`) and always return `SqliteStore`. Keep `JsonStore` only as the import source and for the existing tests.
  - Drop the formal `Store` protocol unless a second backend actually appears. Duck typing plus `main(store=...)` already gives the injection point.
  - The rollback path becomes `todo export > ~/.todo.json`, followed by reverting the CLI version. It is no longer "point `TODO_DB` at JSON".
- **From a (evidence):** port `wt-a/.spike/control_and_kill.py` into the test suite. That means the negative control on `JsonStore`, and SIGKILL during a 50k import leaving either 0 or 50k rows. b only asserted crash atomicity.
- **From a (`complete`):** use `UPDATE … WHERE id=?`, check `rowcount`, then `SELECT`, instead of `RETURNING`. This keeps Python 3.10 builds with SQLite older than 3.35 working.
- **Optional, from a (journal mode):** consider `journal_mode=DELETE` instead of WAL. It removes the persistent `-wal`/`-shm` side files and the NFS/WAL caveat. The cost is that a long `list` briefly blocks writers, which is fine for a CLI. Either choice is acceptable, and b's umask fix covers the WAL side files (verified).
- **From c:** nothing structural. Offering `todo export` (already in b) serves S2's goal of a human-inspectable store well enough.

## Risks to watch in the winner
- **Every open runs `_migrate()` under `BEGIN IMMEDIATE`, so every command, including `list`, briefly takes the write lock.** Test: run `conc.py` with concurrent `list` callers and record the worst-case busy wait. Cheaper fix: read `PRAGMA user_version` first and take `BEGIN IMMEDIATE` only when it is behind, re-checking inside the transaction.
- **`os.umask(0o002)` is process-global.** Fine for a single-threaded CLI, but restore it in `finally`, as the spike does, and do not call it from library contexts that use threads.
- **Group setup is still manual.** The setgid directory `install -d -m 2775 -g todo` and group membership are admin steps. If they are missing, files get the creator's primary group and other users fail with "readonly database". Add a startup check that the db (and `-wal`/`-shm`, if WAL is kept) is group-writable, with a clear error message, as b itself proposes.
- **macOS is untested.** That covers WAL behaviour, `-wal`/`-shm` mode inheritance and setgid directory semantics. Run `multiuser.py` and `umask_check.py` on a Mac before announcing macOS support.
- **Network filesystems.** SQLite locking (and WAL in particular) is unsafe on NFS/SMB. Document "local filesystem only", or detect it and fall back to `journal_mode=DELETE`.
- **First-run auto-import race.** Two users starting at once with legacy files: b's `import_json` refuses a non-empty target inside `BEGIN IMMEDIATE`, so the second user gets an error and loses no data. Add a test for this, and a clear message telling the second user how to merge, or that merging is unsupported.
- **Old SQLite on Python 3.10.** Any remaining use of `RETURNING` fails below SQLite 3.35. Run the test suite against a 3.10 build with an older bundled SQLite (for example `python:3.10-bullseye`).
