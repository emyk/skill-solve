# Proposal b — Most scalable / extensible: SQLite (WAL) behind a `Store` protocol, with versioned schema migrations and JSON import/export

## Overview
Replace the whole-file JSON rewrite with a stdlib `sqlite3` database in WAL mode. Each `add` and `complete` becomes one indexed, autocommitted statement. Its cost does not depend on task count, and SQLite's file locking makes concurrent writers atomic and isolated. The design adds only three extension points, and each one maps to a growth axis the requirements name:
1. **Data volume and load (P1, F3).** SQLite carries B-tree indexes, row-level writes and a WAL that lets readers run alongside a writer. That covers 50k tasks today and 10× more without another redesign.
2. **New fields such as due dates and tags (the "Fit / extensibility" criterion).** A `MIGRATIONS` list is keyed by `PRAGMA user_version`. A new field is one appended SQL string, applied automatically inside a `BEGIN IMMEDIATE` transaction. That makes it safe even when two users' first runs race.
3. **Team size / shared location (F2) and backend variants.** A small `Store` protocol and an `open_store(location)` factory. The factory takes `$TODO_DB` or `--db`, and returns `SqliteStore` by default or `JsonStore` for `*.json` paths. `main(store=...)` injection is unchanged.

Complexity cost I am paying knowingly: about 120 new lines, SQL in the codebase, one more concept (schema versions), and a binary file that is not human-readable. The `todo export` command and the `sqlite3` CLI partly offset that last point.

## Components / modules
- `Store` protocol (`add/list/complete`) — the typed contract the CLI and tests rely on (**new**: `todo/storage.py`, about 10 lines)
- `SqliteStore(path)` — the WAL connection, `busy_timeout`, group-writable file creation, row↔`Task` mapping, and `import_json`/`export_json` (**new**: `todo/sqlite_store.py`)
- `MIGRATIONS` + `_migrate()` — an ordered list of DDL. `user_version` records the applied prefix. Migrations only ever append (**new**, in `sqlite_store.py`)
- `open_store(location=None)` — resolves `--db` › `$TODO_DB` › `~/.todo.db`, picks the backend by suffix, and auto-imports `~/.todo.json` on first use (**new**: `todo/storage.py`)
- `JsonStore` — kept unchanged as the legacy and import source, so the existing tests pass as written (**reused**: `todo/storage.py`)
- `Task` — unchanged. Future fields get defaults so `from_dict` keeps accepting old JSON (**reused**: `todo/models.py`)
- `cli.main` — `store = store or open_store(args.db)`, plus `export` and `import` subcommands (**changed**: `todo/cli.py`, about 15 lines)

## Diagram
```mermaid
flowchart LR
  CLI["cli.main(argv, store=None)"] -->|store injected?| S{{Store protocol}}
  CLI -->|else| F["open_store(--db / $TODO_DB / ~/.todo.db)"]
  F -->|*.json| J[JsonStore legacy]
  F -->|default| Q[SqliteStore]
  F -.first run, ~/.todo.json exists.-> M[import_json in BEGIN IMMEDIATE]
  Q --> MIG["_migrate(): user_version → MIGRATIONS[v:]"]
  Q --> DB[("shared/todo.db + -wal + -shm<br/>mode 0664, setgid group dir")]
  J --> JS[(~/.todo.json)]
```

## Data flow
- **add:** `INSERT INTO tasks(title,done,created_at)` with autocommit. `INTEGER PRIMARY KEY AUTOINCREMENT` gives unique, increasing ids that are never reused. SQLite's write lock serializes writers, and `busy_timeout=30s` makes them wait instead of failing.
- **complete:** `UPDATE … SET done=1 WHERE id=? RETURNING …`. No row raises `KeyError`, as today.
- **list:** `SELECT … [WHERE done=0] ORDER BY id`, served by the `tasks(done)` index. WAL means a reader never blocks a writer.
- **open:** pre-create the file with mode 0664 under `umask 002`, connect, set `journal_mode=WAL`, then run `_migrate()`. It is a no-op when the db is current, which costs one PRAGMA read.
- **Sharing (F2):** the admin creates a setgid directory (`install -d -m 2775 -g todo /srv/todo`) and users set `TODO_DB=/srv/todo/todo.db`. SQLite gives `-wal` and `-shm` the db file's mode and group automatically (verified in the multi-uid spike).

## Fit with existing code
- The interface (`add/list/complete`) and its semantics are identical.
- `main(argv, store=None)` injection is untouched.
- The CLI output strings are unchanged.
- `JsonStore` and `tests/test_storage.py` stay as they are, and the same 5 tests pass against `SqliteStore` (spike).
- New tests go in `tests/test_sqlite_store.py`: a parametrized `store` fixture over both backends, a multiprocess concurrency test, a migration test, and an import/export round-trip.
- No dependencies. The `RETURNING` clause needs SQLite ≥ 3.35. If Python 3.10 on an older system lib is a concern, a `SELECT` after the `UPDATE` in the same transaction replaces it.

## Migration path
Each step can be shipped and reverted on its own:
1. Add `sqlite_store.py`, `open_store` and the tests. The CLI still uses `JsonStore`.
2. Switch the CLI default to `open_store()`. On first run, if `~/.todo.db` is missing and `~/.todo.json` exists, `import_json` runs in one transaction. It keeps the original ids and fails if the target is non-empty. Afterwards `.todo.json` is renamed to `.todo.json.migrated`, never deleted.
3. **Rollback:** `todo export > ~/.todo.json` produces the exact old format, and `TODO_DB=~/.todo.json` points the CLI back at `JsonStore`.
4. Document the shared-directory setup in the README.

## Requirements check
- **H1 stdlib only — met.** Uses `sqlite3`, `os` and `json` only.
- **H2 no lost updates or corruption — met by mechanism.** SQLite's atomic commit plus WAL, `BEGIN IMMEDIATE` for migrate and import, and AUTOINCREMENT ids. The spikes show zero loss across 16 processes and across different uids.
- **H3 lossless migration — met.** The 50k round-trip compares equal field-for-field, and the source file is kept.
- **H4 no daemon — met.** SQLite runs in-process.
- **Correctness under concurrency (25):** strong. The guarantees come from SQLite's locking, and both the multiprocess and multi-uid spikes ran with no lost writes.
- **Performance at 50k (20):** strong. add/complete take about 0.3 ms (vs 237–255 ms today), and a cold open plus add takes about 0.8 ms. `list` matches today's speed.
- **Simplicity (20):** medium. It adds SQL, the migrations list and a factory, about 120 lines and 3 new concepts. This is the main cost of this angle.
- **Migration risk (20):** good. Automatic, transactional, non-destructive, with an export path back to JSON.
- **Fit / extensibility (15):** strongest. A new field is one appended migration (measured at 1.9 ms at 50k). Tags get a join table, not a JSON blob. A new backend implements the 3-method protocol.

## Evidence vs. assumptions
All spikes are in `wt-b/.spike/`:
- **EVIDENCE: today's baseline at 50k.** `python3 .spike/baseline.py` → JsonStore add 237 ms, complete 255 ms, list(all) 65 ms, list(open) 74 ms. This sandbox is faster than the reported 1 s.
- **EVIDENCE: add/complete cost is independent of n.** `python3 .spike/bench.py` → at 50k, add median 0.35 ms (max 1.15), complete median 0.29 ms (max 0.98), cold open+add median 0.75 ms. list(all) 63 ms, list(open) 42 ms. Both lists are no slower than today (P2).
- **EVIDENCE: migration is lossless and fast.** `bench.py` → import of 50k tasks takes 139–253 ms, and `[t.to_dict() for t in list(True)] == original JSON` → `True`.
- **EVIDENCE: concurrent writers lose nothing.** `python3 .spike/conc.py` → 16 processes × 300 adds plus 150 completes each gave 4800 ids, 4800 unique, 4800 rows, done=2400 as expected, and `integrity_check` returned ok.
- **EVIDENCE: different uids can share the list.** `python3 .spike/multiuser.py` → uids 1 and 2 wrote 1200 unique ids with umask 022, and uid 3 completed a task and listed 1200.
  - The first attempt failed with `attempt to write a readonly database`. **SQLite creates the db file with mode 0644 regardless of umask.**
  - Fix: pre-create the file with `os.open(path, O_CREAT, 0o664)` under umask 002. After that, `-wal` and `-shm` inherited 0664 and gid 100 automatically.
  - The spike used a temporary `/tmp/todo-spike-b-*` directory, removed afterwards, because the scratchpad's parent directories are 0700.
- **EVIDENCE: the existing tests pass on the new store.** `python3 -m pytest .spike/test_sqlite_compat.py tests/` → 10 passed (the 5 original tests × 2 backends).
- **EVIDENCE: schema extension is cheap and safe.** `python3 .spike/ext.py` → the v1→v2 migration (`ADD COLUMN due` plus a `task_tags` table) took 1.9 ms on 50k rows, and v1 code paths still work.
- **ASSUMPTION: macOS behaves like Linux for WAL, the file-mode inheritance and the setgid directory.** Not tested, because no macOS host was available. The multiuser spike run on a Mac would settle it.
- **ASSUMPTION: the shared path is on a local filesystem, not NFS or SMB, where WAL is unsupported.** Mitigation: detect the filesystem or fall back to `journal_mode=DELETE`, and document the requirement.

## Risks and trade-offs
- **S2, human-inspectable:** this is lost for the binary db. It is mitigated by `todo export` (the exact old JSON) and the `sqlite3` CLI.
- **WAL side files:** the `-wal` and `-shm` files must stay writable by the group. The spike handled this, but a user who hand-creates the db file with 0644 would break sharing. `open_store` should check the mode and emit a clear error.
- **Concurrent open while one user is migrating:** this is serialized by `BEGIN IMMEDIATE`, and the second user sees the bumped `user_version`.
- **Extra concepts:** the `Store` protocol, the factory and the migrations list are more than a minimal fix needs. They are justified by F2's configurable shared path and by the named future fields. They are about 30 lines combined.

## Effort
About 1 day:
- `sqlite_store.py` plus the factory: about 120 lines.
- CLI changes: about 15 lines.
- Tests (parametrized backends, multiprocess, migration, round-trip): about 100 lines.
- README section on shared setup.

## Confidence: 8/10
