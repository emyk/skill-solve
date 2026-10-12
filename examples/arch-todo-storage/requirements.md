# Requirements: todo storage restructure

## Functional needs
- F1 Keep the operations `add(title) -> Task`, `list(include_done) -> [Task]`, `complete(id) -> Task` (KeyError if missing) with today's semantics. Ids are unique and increasing.
- F2 Several OS users on the same machine share one task list (a shared file/dir path they can all write to).
- F3 Concurrent commands from different users must not lose or corrupt writes (no lost updates, no duplicate ids, no truncated file).

## Scale / performance
- P1 At 50k tasks, `add` and `complete` should take well under 100 ms (today ~1 s). Target: cost roughly independent of task count.
- P2 `list` at 50k may stay O(n). It's a full listing anyway, but should not be slower than today.

## Conventions
- Pure standard library, Python 3.10+ (README promises this). Small, plain modules; dataclass `Task`; pytest tests.

## Existing dependencies worth reusing
- Python stdlib only: `json`, `sqlite3` (bundled), `fcntl`, `os`, `dbm`.

## What must not break
- The CLI commands and their output; the existing tests in `tests/test_storage.py`; `JsonStore(path)`-style injection used by `main(store=...)`.
- Existing users' `~/.todo.json` data must be migratable without loss.

## Constraints
| # | Constraint | Type |
|---|---|---|
| H1 | No third-party runtime dependencies (stdlib only) | HARD |
| H2 | No lost updates/corruption under concurrent writers from different processes/users (F3) | HARD |
| H3 | Existing `~/.todo.json` data can be migrated without loss | HARD |
| H4 | No long-running daemon/server process required | HARD |
| S1 | Linux and macOS supported; Windows nice-to-have | SOFT |
| S2 | Keep the store human-inspectable | SOFT |

## Evaluation criteria (weights sum to 100)
| Criterion | Weight | What good looks like |
|---|---|---|
| Correctness under concurrency | 25 | Atomicity and isolation guaranteed by mechanism, not by luck; demonstrated by a spike |
| Performance at 50k | 20 | Measured add/complete latency at 50k ≪ 100 ms |
| Simplicity / maintainability | 20 | Few new concepts and lines; easy for a newcomer |
| Migration risk & effort | 20 | Small, reversible steps; existing data and tests carried over |
| Fit with codebase / extensibility | 15 | Same interface; leaves room for future fields (due dates, tags) |
