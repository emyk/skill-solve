# End-to-end run: ARCH light depth with spikes

`/solve find_product re-reads catalog.json on every call; how should caching in shop/catalog.py be structured so lookups are fast but saves are never missed?`

This run followed SKILL.md literally to exercise the newer paths:

- **Setup and `run.env`:** every command started by sourcing `run.env`, with a guard that stops if a variable is missing. The solver list was rewritten to `a c` after picking light depth.
  - **Bug found:** a command that had already loaded `run.env` kept the old list and created a `b/` folder. SKILL.md now says to re-read `run.env` after rewriting the list.
- **Light depth:** 2 solvers (a: simplest, c: different in kind), proposals of 336–365 words, and no worktrees. Both experiments ran in the solvers' scratch folders; the repo had no `.spike/` folder and a clean `git status`.
- **Notes:** the orchestrator re-ran both experiments from the exact commands in `notes.md`. The first attempt failed without the recorded argument, which shows why the notes record exact commands.
- **Critique:** solvers were resumed with SendMessage, and objections were kept to 1–2 sentences.
  - c showed that a's "inode guarantee" is false, because ext4 reuses inode numbers.
  - a reproduced c's bug where shared objects let a caller's change leak to disk.
- **Judge:** WINNER a, 87 vs 64. It borrowed two ideas: correct a's comment, and have `save_product` clear its own cache entry.
- **Approval:** the user chose a, then tests-first implementation: 3 new tests, 1 failing before the change, 7/7 passing after (`implemented.diff`).
- **Cleanup:** no worktrees or `solve/*` branches were created. The run folder was deleted by its literal path, and only the intended changes remained.
