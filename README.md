# solve — a Claude Code skill for competing solutions

`/solve <problem> [--mode code|arch] [--n 2-5]` runs several sub-agents on the same problem from different angles, verifies their work, and has an independent judge pick a winner from the evidence.

- **CODE mode** (bug, failing behavior, algorithm, feature): each solver works in its own git worktree, and the result is a verified diff.
- **ARCH mode** (design decisions): solvers write proposals and run spikes, critique each other, and a judge scores them against weighted criteria. The result is an ADR.

Install (user-level, works in every project):

```bash
cp -r solve ~/.claude/skills/
```

Layout: `solve/SKILL.md` holds the workflow, `solve/prompts/` the solver, critique and judge prompts for each mode, and `solve/templates/adr.md` the ADR template. `evals/` holds the test prompts.
