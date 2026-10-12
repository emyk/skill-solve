# Critique by c

## On a (SQLite, single table)
**Objection:** With the default umask, the shared list does not work for a second user. That user cannot even run `todo list`.

a's `SqliteStore.__init__` pre-creates the DB file with `os.open(path, O_RDWR|O_CREAT, 0o666)` and leaves the creator's umask in place (`wt-a/.spike/sqlite_store.py:14`). On a stock Linux or macOS account the umask is 022, so the first user creates `todo.db` as `0644`. Every other user then fails inside the constructor, because it opens the file `O_RDWR` unconditionally. Both reads and writes are affected, so F2 is broken out of the box. a's own concurrency spike does not show this because it forces `os.umask(0o002)` in every worker (`wt-a/.spike/concurrency.py:8`). The proposal admits it only as a README step ("first creator needs umask 002, or a one-off chmod g+w").

**Grounding:** this is checked, not assumed. I ran `python3 .spike/critique/a_umask.py` in wt-c. It imports a's spike store unmodified, sets up a 2775 setgid group directory, and runs uids 1001 and 1002 in the same group with umask 022:
```
uid 1001: 1
-rw-r--r-- 1 1001 ubuntu 12288 … todo.db
uid 1002: FAILED PermissionError(13, 'Permission denied')
--- same, but first user has umask 002 ---
uid 1001: 1
uid 1002: 2
```
It fails loudly and loses no data, so H2 and H3 still hold. But F2 depends on every user's umask at first-creation time, or on an admin running `chmod` by hand. The fix is one line: b's `os.umask(0o002)` around the pre-create (`wt-b/.spike/sqlstore.py`). The judge should not credit a with "works for several users" as written.

A second, smaller point: the proposal says complete uses "no `RETURNING`" to support older SQLite, but the spike uses `RETURNING` (`sqlite_store.py:31`). The measured code is therefore not the code the proposal describes.

**Severity:** major. It breaks F2 under default settings and the fix is trivial.

**They do better than me:** a gets the same guarantees as my design with about a third of the code and none of my hand-written protocol (locking, torn-tail truncation, binary search, compaction). Its `list` is also faster than today's (52/66 ms vs 84/92 ms), where mine is only at parity once compacted.

## On b (SQLite WAL + Store protocol + versioned migrations + import/export)
**Objection:** b spends the simplicity budget (weight 20) on speculative machinery, and one piece of that machinery reopens the H2 bug. The problem needs one `SqliteStore` class. b adds four further pieces:
- a `Store` protocol
- an `open_store` factory that picks a backend by file suffix
- a migrations framework
- `import`/`export` subcommands

That is about 120 lines and three new concepts, and the effort estimate doubles to about a day. The only one of these the requirements actually ask for is room for future fields, and that is 15 points shared by all designs. Worse, the factory routes any `*.json` path to `JsonStore`. b's documented rollback (`TODO_DB=~/.todo.json`) and any user who sets `TODO_DB=/srv/todo/tasks.json` would put the shared list back on the lock-free read-modify-write store. That store's negative controls lost 708 of 800 writes in a's spike and crashed all 8 writers in mine.

**Grounding:**
- Requirements weighting: Simplicity 20 against Fit/extensibility 15.
- F3/H2: `todo/storage.py:13-41` (today's `JsonStore`) has no locking and is exactly what the suffix dispatch selects.
- b's proposal, components `open_store` and "Migration path step 3".
- The dispatch is not in b's spike (`wt-b/.spike/sqlstore.py` has only the store), so its behaviour is proposal-level. My claim follows directly from the stated rule.

**Severity:** major. It is not fatal, because the default path is SQLite and passes H2. But it is the only design here where a supported configuration silently violates H2.

**They do better than me:** schema evolution is safe under concurrent first runs. `_migrate()` runs inside `BEGIN IMMEDIATE` keyed on `user_version`, measured at 1.9 ms for v1→v2 on 50k rows. b also handles the umask correctly (`os.umask(0o002)` around the pre-create). My event log only "asserts" extensibility, and a format change to existing events would need a hand-written rewrite.

## On my own proposal
**Strongest objection:** next to a and b, my design re-implements in about 120 hand-written lines what `sqlite3` already gives the stdlib for free:
- atomic commit
- crash recovery
- writer serialization
- id allocation

Its unique wins are plain-text inspectability (S2, a soft constraint) and add/complete at 0.02–0.1 ms instead of 0.3–2 ms. Both are irrelevant for a CLI where interpreter start-up alone is about 50 ms. Meanwhile it adds an ongoing compaction obligation, without which `list` regresses past today and violates P2. Its correctness rests on invariants a newcomer must not break: `hwm` monotonicity, truncation under the lock, and taking the lock before opening the file. For this problem a mature engine with fewer lines is the better choice. My angle's "different in kind" property does not earn its maintenance cost here.

**One more fact I found while checking a, against myself:** my design has the same umask bug. `python3 .spike/critique/c_umask.py` (uids 1001 and 1002, umask 022, 2775 group directory) printed `tasks.jsonl` and `tasks.jsonl.lock` both as `-rw-r--r--`, and the second user got `PermissionError(13)`. My race spike hid this because it calls `os.umask(0)` (`wt-c/.spike/race.py`). The "EVIDENCE: concurrency across uids" claim in my proposal therefore holds only with a permissive umask, and needs the same `os.umask` fix that b already has.
