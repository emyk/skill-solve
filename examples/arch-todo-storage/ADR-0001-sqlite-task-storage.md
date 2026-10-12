# 1. Store tasks in a shared SQLite database instead of a single JSON file

- Status: Proposed
- Date: 2026-10-12
- Decided via: /solve. Three independent proposals were spiked, cross-critiqued, and scored by an independent judge.

## Context

`JsonStore` (`todo/storage.py`) loads and rewrites all of `~/.todo.json` on every `add` and `complete`. At 50k tasks that costs 240–330 ms per write as measured here (about 1 s on users' machines). It has no locking, so concurrent writers lose updates: in a spike, 8 writers × 100 adds kept only 92 of 800 tasks, and another run corrupted the file. We now also want several OS users on one machine to share one list.

Constraints: stdlib only (H1), no lost updates or corruption under concurrent writers (H2), existing `~/.todo.json` migrated without loss (H3), no daemon (H4). Linux and macOS (soft), human-inspectable store (soft).

### Evaluation criteria

| Criterion | Weight |
|---|---|
| Correctness under concurrency | 25 |
| Performance at 50k | 20 |
| Simplicity / maintainability | 20 |
| Migration risk & effort | 20 |
| Fit with codebase / extensibility | 15 |

## Options considered

### Option A: one SQLite table, same three-method store (simplest)
`SqliteStore` next to `JsonStore`, about 50 lines, one SQL statement per command, one-shot import. add/complete about 2 ms at 50k. Weighted score: **85/100**.

### Option B: SQLite (WAL) with versioned schema migrations and import/export (scalable): chosen
`SqliteStore` in WAL mode, `PRAGMA user_version` with an append-only `MIGRATIONS` list, path resolution via `--db` / `$TODO_DB`, a group-writable file created in code, and `todo export`/`import`. add/complete about 0.3 ms at 50k. Weighted score: **92/100**.

### Option C: append-only JSON Lines event log with `flock` (different in kind)
Each write appends one line under an exclusive lock, ids come from the last line, `complete` binary-searches, and `list` replays the log with periodic compaction. add about 0.02 ms. It keeps a plain-text store, but hand-writes locking, crash recovery and compaction. Weighted score: **64/100**.

## Decision

We will replace `JsonStore` as the CLI's default with a stdlib `sqlite3` store, following Option B and trimmed using ideas from Option A:

- `SqliteStore(path)` uses `busy_timeout`. It creates the DB file group-writable (0664 under umask 002) **in code** before SQLite opens it.
- Schema versioning uses `PRAGMA user_version` and an append-only `MIGRATIONS` list, applied inside `BEGIN IMMEDIATE` **only when the stored version is behind**.
- Path resolution: `--db` › `$TODO_DB` › `~/.todo.db`. It **always** returns `SqliteStore`; no `*.json` dispatch (borrowed from A).
- No formal `Store` protocol until a second backend exists; `main(store=...)` stays the injection point (borrowed from A).
- `complete` uses `UPDATE … WHERE id=?` plus a `rowcount` check rather than `RETURNING`, so it works on SQLite older than 3.35 (borrowed from A).
- Migration: on first run, `~/.todo.json` is imported atomically and renamed to `.todo.json.migrated`. Rollback is `todo export > ~/.todo.json` and reverting the CLI.

```mermaid
flowchart LR
  CLI["cli.main(argv, store=None)"] -->|store injected| Q
  CLI -->|else| P["resolve path: --db / $TODO_DB / ~/.todo.db"]
  P --> Q[SqliteStore]
  P -.first run, ~/.todo.json exists.-> M["import_json in BEGIN IMMEDIATE<br/>rename to .todo.json.migrated"]
  Q --> MIG["_migrate() only if user_version behind"]
  Q --> DB[("shared/todo.db (+ -wal, -shm)<br/>0664, setgid group dir")]
  CLI -->|todo export| X[(JSON in the old format)]
```

## Rationale

- **Performance doesn't decide it.** All three options bring add/complete at 50k well below the 100 ms target.
- **Sharing under a default umask decided it.** Under the default umask 022, b's design was the only one whose multi-user sharing worked as spiked. The judge re-ran `umask_check.py`: a second uid got `PermissionError` on A (`todo.db` 0644) and on C (`tasks.jsonl.lock` 0644), and succeeded on B with all files at 0664.
- **B had the strongest migration story:** an atomic import that refuses a non-empty target, the legacy file renamed rather than deleted, and an exact JSON export.
- **Extension is cheap:** the schema-version mechanism is spiked (v1→v2 took 1.9 ms on 50k rows) and covers the expected due-date and tag fields.
- **What B gave up:** it lost on simplicity, with about 120 lines and a protocol and factory. Taking A's simplifications closes most of that gap.
- **Why not C:** C reimplements, by hand, locking, recovery and compaction that SQLite already provides. Its `list` is slower than today until compaction runs.

Not a close call: 92 vs 85, and the deciding factor was evidence (the umask spike) rather than weighting.

## Consequences

- Positive: add/complete costs O(1) in task count, writes are atomic and isolated across processes and users, and schema changes become one appended migration.
- Negative / accepted trade-offs: the store is binary rather than human-readable, so `todo export` and the `sqlite3` CLI are the inspection paths. Network filesystems (NFS/SMB) are not supported for the shared DB. Sharing still needs an admin step: a setgid group directory and group membership.
- Migration, with every step shippable and reversible:
  1. Add `SqliteStore` and tests while the CLI stays on JSON.
  2. Switch the CLI default, with automatic import on first run.
  3. Add `export`/`import` subcommands.
  4. Document the shared-directory setup.
- Open assumptions to validate early:
  - macOS behaviour (WAL, file-mode inheritance on `-wal`/`-shm`, setgid directories): run `multiuser.py` and `umask_check.py` on a Mac.
  - Worst-case lock wait with concurrent `list` callers.
  - Python 3.10 with an older bundled SQLite.
  - A first-run import race between two users.

## Objections raised

- **Default umask 022 breaks sharing for A and C** (raised by B and C against A, and by A and B against C). It **holds**: both are reproduced, and both spikes had hidden it by forcing `umask(0)` or `umask(002)`. B's in-code permission handling was adopted.
- **B's `*.json` factory dispatch, including its documented rollback `TODO_DB=~/.todo.json`, re-enables the unlocked store and its lost updates** (raised by A and C against B). It **holds**. It was removed from the decision, and rollback is now export-based.
- **B is overbuilt** (raised by A, by C, and by B against itself). It **partly holds**. The protocol and factory were cut, and schema versioning was kept because A would need an ad-hoc equivalent anyway.
- **C's `list` is slower than today until compaction runs** (raised in verification, and by B and C). It **holds**. It was one reason C was not chosen.
- **Every open takes the write lock to check migrations** (raised by the judge against B). It was mitigated by reading `user_version` first.
