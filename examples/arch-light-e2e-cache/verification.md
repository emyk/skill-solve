# Verification (orchestrator)
Repo untouched by both solvers (git status clean, no .spike/); both spikes live in their scratch folders.
HARD constraints: both keep signatures, stdlib only, invalidate on save. Neither disqualified.
- a (dict cache keyed by path, revalidated by os.stat inode+mtime_ns+size, deepcopy on return): EVIDENCE, spike re-run by orchestrator from the command in a/notes.md: 0 stale reads across processes, cached lookup µs vs 48 ms.
- c (keep the parsed file's fd open; fresh iff os.path.samestat(fstat(fd), stat(path))): EVIDENCE, spike re-run from c/notes.md: 0 missed saves. ASSUMPTION: POSIX-only (held fd blocks os.replace on Windows, per c's own risk list); returns a shared dict.
