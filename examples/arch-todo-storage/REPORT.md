## /solve result: restructure the todo storage layer
Mode: ARCH (a design decision about storage structure, not a specific patch) · Solvers: 3 · Critique round: yes · ADR: `docs/decisions/0001-sqlite-task-storage.md` (Proposed)

**Decision: b, SQLite in WAL mode with versioned schema migrations, trimmed using ideas from a.** Judge verdict: WINNER b, 92 vs 85 vs 64.

| Criterion (weight) | a: simplest (SQLite table) | b: scalable (SQLite + migrations) | c: different in kind (JSONL event log) |
|---|---|---|---|
| Concurrency correctness (25) | 4 | 5 | 3 |
| Performance at 50k (20) | 5 | 5 | 4 |
| Simplicity (20) | 5 | 3 | 2 |
| Migration risk (20) | 4 | 5 | 4 |
| Fit / extensibility (15) | 3 | 5 | 3 |
| **Total /100** | **85** | **92** | **64** |

Runner-up: a, the same core with half the code. Its simplifications were folded into the decision: no `*.json` backend dispatch, no `Store` protocol, and no `RETURNING`.

Objections that mattered:
1. **Sharing breaks under the default umask 022** for a and c. The judge reproduced it: the second user gets `PermissionError`. Both solvers' own spikes had hidden this by forcing `umask(0)` or `umask(002)`. Only b creates group-writable files in code.
2. **b's `*.json` dispatch re-enables the unlocked legacy store** through its own documented rollback path. That was cut from the decision, and rollback is now `todo export`.

Evidence collected by spikes:
- add/complete at 50k drop from 240–330 ms to 0.02–2 ms in all three options.
- The 50k migration came back identical (139–406 ms).
- 16 processes running as several uids lost no writes. The negative control on today's store kept 92 of 800 writes.
- A writer killed mid-import always left 0 or 50k rows.

**Next: break this into implementation steps?** Each would be a self-contained CODE task, for example:
1. `/solve --mode code Add todo/sqlite_store.py: SqliteStore(path) with add/list/complete matching JsonStore semantics, busy_timeout, group-writable file creation (0664 under umask 002), PRAGMA user_version + MIGRATIONS list applied only when behind; run tests/test_storage.py against both stores`
2. `/solve --mode code Add import_json/export_json to SqliteStore: atomic import of ~/.todo.json keeping ids (refuse non-empty target), rename source to .todo.json.migrated; export reproduces the old JSON format exactly`
3. `/solve --mode code Switch todo/cli.py default store to SqliteStore with path resolution --db > $TODO_DB > ~/.todo.db, auto-import on first run, add export/import subcommands`
4. `/solve --mode code Add a concurrency regression test: N processes adding/completing against one SqliteStore lose no writes and produce unique ids; plus SIGKILL-during-import leaves 0 or all rows`
5. `/solve --mode code Startup check: if the shared db (and -wal/-shm) is not group-writable, fail with a clear message explaining the setgid-directory setup; document it in README`
