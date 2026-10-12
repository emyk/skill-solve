# Critique by b

I wrote one shared check for both other proposals: `wt-b/.spike/umask_check.py`. It loads each solver's own spike store without modifying it, then runs two steps in a setgid group directory (mode 2775, gid 100), both at the **default umask 022**:
1. uid 1 creates the store and adds a task.
2. uid 2 adds a task.

Command: `python3 .spike/umask_check.py <solve-dir>`. Output:
```
a ['uid1 add ok id=1', "uid2 FAILED PermissionError: [Errno 13] ... /s/todo.db"]          {'todo.db': '0o644'}
b ['uid1 add ok id=1', 'uid2 add ok id=2']   {'todo.db': '0o664', 'todo.db-shm': '0o664', 'todo.db-wal': '0o664'}
c ['uid1 add ok id=1', "uid2 FAILED PermissionError: [Errno 13] ... /s/tasks.jsonl.lock"]  {'tasks.jsonl': '0o644', 'tasks.jsonl.lock': '0o644'}
```

## On a
**Objection:** with the default umask, the shared list does not work at all. uid 1 creates the store and adds a task; uid 2's first write fails. a's fix is to pre-create the file with `os.open(path, O_CREAT, 0o666)` so that umask applies. That fix only helps when the creating user already has umask 002. With the usual 022 the file still comes out 0644, so every other user's first write fails with `EACCES`.

a's multi-user spike passed only because each worker explicitly ran `os.umask(0o002)` (`wt-a/.spike/concurrency.py:8`). The proposal does mention this under Risks: "the first creator needs umask 002, or a one-off `chmod g+w`". But the headline result ("16 processes as 2 OS users, 4800/4800") hides that the default setup fails. No data is lost: the write is refused loudly.

**Grounding:**
- F2, several OS users share one list.
- My run above: uid 2 got `PermissionError` and `todo.db` was 0644.
- `wt-a/.spike/concurrency.py:8` forces umask 002 in the workers.

**Severity:** major. It does not break a HARD constraint, because nothing is lost or corrupted. But F2 is broken out of the box, and the fix is small: widen the umask inside the store, which is the two lines b already has.

**They do better than me:**
- Much smaller: about 50 lines, one class, no protocol, factory or migrations list.
- No WAL, so no persistent `-wal`/`-shm` side files to manage.
- They spiked crash atomicity (SIGKILL during import gave 0 or 50k rows, never a partial count) and a negative control on today's store. I only asserted crash safety.

## On c
**Objection:** c has the same multi-user break as a, and it is worse because c hand-rolls the permission model.
- Both `tasks.jsonl.lock` and `tasks.jsonl` are created with `os.open(..., 0o666)` and nothing widens the umask (`wt-c/.spike/logstore.py:21,23`). Under umask 022 both files come out 0644.
- uid 2 then cannot even open the lock file with `O_RDWR`. Every command by every other user fails, including `list`, which takes the same lock.
- c's race spike passed only because it ran `os.umask(0)` in a world-writable 2777 directory (`wt-c/.spike/race.py:8-9`). That is not a realistic setup.
- `compact()` "fixes" the permissions with `chmod 0666`, which makes the shared list **world**-writable rather than group-writable. Until a compaction runs, the list stays unshareable.

This matters for the judge's weighting. c's case for correctness under concurrency (weight 25) rests on "hand-written but spiked". This is exactly the kind of gap a hand-written protocol leaves: the spike covered the lock logic but not the file setup any real deployment starts from.

**Grounding:**
- F2 and S1.
- My run above: uid 2 got `PermissionError` on `tasks.jsonl.lock`, and both files were 0644.
- `wt-c/.spike/race.py:8` (`os.umask(0)`) and `logstore.py:21,23`.

**Severity:** major. The fix is simple (set umask 002 around creation, or `fchmod` the new files to 0664), and no data is lost. Note that this comes on top of the issue verification already lists: `list` runs 25–40% slower than today on an uncompacted log, which P2 does not allow, unless the compaction policy is decided.

**They do better than me:**
- c is the only proposal that meets S2: the store stays plain-text JSON a human can read, and it records an audit history.
- add/complete is about 10× cheaper still (0.02–0.1 ms).
- New operations (reopen, retitle) are new event types and need no schema migration.

## On my own proposal
**Objection:** for this problem, b is overbuilt relative to a.
- About half of my additions are not required by anything in the requirements: the `Store` protocol, the `open_store` factory with backend selection by file suffix, and `--db`. F2 only needs a configurable path, which a gets with a single `TODO_DB` constant.
- Simplicity carries 20% of the score. A reviewer could fairly argue that "a + b's umask/pre-create lines + a 5-line `user_version` check" gives about 90% of b's value at about half the code.
- WAL also adds persistent `-wal`/`-shm` side files. With rollback-journal mode, as in a, these would not exist. Two persistent side files mean more permission surface: a user who hand-creates `todo.db` as 0644 breaks sharing.
- I did not spike crash atomicity. a did.

The concrete things b gets right that the others missed are versioned migrations and correct default-umask sharing (shown in the check above). Both are small enough to graft onto a.

**Severity:** minor. All HARD constraints are met and spiked.
