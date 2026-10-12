# Critique by a

## On b
**Objection:** b's extension points are speculative, and one of them weakens H2. `open_store` picks the backend by file suffix (`*.json` → `JsonStore`). The documented rollback is `TODO_DB=~/.todo.json`. Together they make today's unlocked read-modify-write store (`todo/storage.py`, `JsonStore._load`/`_save`) a *supported, configurable* backend. Point a shared `TODO_DB` at a `.json` path and the CLI silently runs the store that loses writes.

The same YAGNI cost applies to the other additions:
- the `Store` protocol has a single real implementation;
- the `MIGRATIONS`/`user_version` framework covers changes that are, today, one `ALTER TABLE ADD COLUMN`;
- WAL adds two persistent side files (`-wal`, `-shm`) whose permissions must stay group-writable.

None of this is needed for P1, F2 or F3. b pays about 120 lines and 3 new concepts against Simplicity (weight 20) to win on Fit/extensibility (weight 15). Its own extension spike (1.9 ms on 50k rows) shows the ALTER is cheap, which is not the same as showing the framework is needed.

**Grounding:**
- H2 / F3: the negative control in my spike (`.spike/control_and_kill.py`) has JsonStore keeping 92 of 800 writes, and c's control ends in a corrupt file. b's factory keeps that store reachable through `TODO_DB=*.json`.
- Criterion weights: Simplicity 20 vs Fit 15.
- `requirements.md` lists future fields only as "leaves room for", not as a requirement.

**Severity:** major. The default path is correct. The weakness is that a documented configuration reintroduces lost updates, and the extra machinery costs simplicity points without meeting any stated requirement.

**They do better than me:** b makes the store group-writable *in code*. It sets `os.umask(0o002)` around creating the DB file and pre-creates it as 0664 (`wt-b/.spike/sqlstore.py:15-19`), and its multi-uid spike deliberately runs under umask 022. My design relies on the first user's umask, or on a manual `chmod g+w` documented in the README. Theirs works out of the box. b also offers `todo export`, which gives an exact path back to the old JSON format.

## On c
**Objection:** c's multi-user correctness rests on hand-written permission and locking code, and its spike never tested realistic permissions. `wt-c/.spike/race.py:8-9` runs with `os.umask(0)` and a world-writable `0o2777` directory. I re-ran c's `LogStore` (an unmodified copy) under a normal umask of 022 in a `2775` group directory, with two uids sharing a gid:

```
uid 1001 add ok id=1
uid 1002 add FAILED: PermissionError: [Errno 13] Permission denied: '.../tasks.jsonl.lock'
-rw-r--r-- 1 1001 1500 101 tasks.jsonl
-rw-r--r-- 1 1001 1500   0 tasks.jsonl.lock
```

So with c as spiked and documented ("Files are created 0666 & ~umask"), F2 fails as soon as a second user runs a command. Compaction then `chmod`s the log to 0666, which is world-writable. Because the directory is `o+x`, any local user outside the group can then append to it.

The fix is easy (an `fchmod` call or a umask change). The issue is that c owns this class of problem, along with torn-tail truncation, the `hwm` binary search and a compaction policy that is still undecided. That last item is the open ASSUMPTION in `verification.md` about whether c meets P2 (list is 25–40% slower than today until the log is compacted). All of that adds roughly 40 lines of subtle code that SQLite already provides and has tested. On "Correctness under concurrency (25): guaranteed by mechanism, not luck", c's guarantee depends on all of that bespoke code being right, and the multi-user part of its evidence was gathered under conditions users won't have.

**Grounding:**
- F2 / H2 and the Correctness criterion (25).
- My check: `python3 wt-a/.spike/c_umask.py` (runs a copy at `wt-a/.spike/c_copy/logstore.py`), output above.
- `wt-c/.spike/race.py:8-9` and `logstore.py:21,23,38`.

**Severity:** major. It doesn't break a HARD constraint, because no data is lost: the second user gets an error. But shared use fails as spiked, and the evidence for the 25-point criterion is weaker than presented.

**They do better than me:** c keeps the store plain-text and greppable (S2), and the log holds full per-task history. Both a and b give up S2 for a binary file.

## On my own proposal
The strongest objection is the same permission trap I found in c, and only half fixed in my design. Pre-creating the file with `os.open(..., 0o666)` only *honours* the umask. Under the common default umask of 022, the first user still creates `todo.db` as 0644, and every other user gets `attempt to write a readonly database` until someone runs `chmod g+w`. My proposal moves this into a README setup step instead of handling it in code, as b does. So the "out of the box" claim for F2 depends on users following documentation.

A second, smaller point: I ship no schema-version marker. The first future column will need an ad-hoc "add column if missing" check, done safely when several users at different versions share the same DB. That is roughly the small piece of b's migration framework that I dismissed.
