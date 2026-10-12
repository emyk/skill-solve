# Verification (orchestrator)

## HARD constraints
| | H1 stdlib only | H2 no lost updates / corruption | H3 lossless migration | H4 no daemon | Result |
|---|---|---|---|---|---|
| a (SQLite, single table) | met (sqlite3) | met: SQLite transactions; re-run by orchestrator: `.spike/concurrency.py` → done 1600/1600, integrity ok | met: spike, 50k identical | met | SURVIVES |
| b (SQLite WAL + Store protocol + migrations) | met | met: re-run `.spike/conc.py` → 4800/4800 unique, done 2400/2400, integrity ok | met: spike + JSON round-trip | met | SURVIVES |
| c (append-only JSONL event log + flock) | met | met *by hand-written protocol* (flock + torn-line truncation); re-run `.spike/race.py` → all ids unique and present, all completed ids done | met: spike, roundtrip identical | met (compaction runs in-process) | SURVIVES |

## Evidence vs. assumption (key claims)
- add/complete independent of n at 50k: EVIDENCE for all three (a ~2 ms with fresh connection, b ~0.3 ms, c ~0.02–0.1 ms). All ≪ 100 ms target; differences are irrelevant at CLI scale.
- list not slower than today: EVIDENCE a (faster), b (equal); c EVIDENCE equal when compacted, ~25–40% slower with 20k uncompacted done events → depends on compaction policy (ASSUMPTION: when/who compacts).
- Multi-user file permissions: EVIDENCE a and b both discovered SQLite creates the DB 0644 regardless of umask and fixed it by pre-creating the file (0666/0664 under umask). c: orchestrator observed compaction leaves `tasks.jsonl` owned by the compacting user and relies on an explicit `chmod 0666` (world-writable, broader than the group-writable a/b use) — works, but the permission model is hand-maintained.
- Crash safety: EVIDENCE a (SIGKILL during import → 0 or 50k rows); c (torn line recovery tested by hand-crafted torn line, an earlier version disproved). b: relies on SQLite atomicity (well-established, not spiked).
- Portability: ASSUMPTION for all (macOS untested; NFS unsupported for SQLite locking and for flock). Windows: c needs a locking shim (untested); a/b get it from SQLite.
- Extensibility: EVIDENCE b (v1→v2 migration 1.9 ms on 50k). a, c: asserted only.
