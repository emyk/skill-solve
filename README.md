# solve: a Claude Code skill for competing solutions

`/solve <problem> [--build] [--mode code|arch] [--n 2-5]`

Several sub-agents work the same problem independently, each from a different angle (minimal, robust, root-cause, …). They critique each other, and a judge who wrote none of the solutions recommends one. **You see every option next to the judge's verdict and approve which one to go with.**

| | What solvers produce | After you approve |
|---|---|---|
| **CODE** (default) | approaches only: diagnosis, the change, trade-offs, size. No code. | Claude implements the chosen approach once, test-first |
| **CODE `--build`** | a tested diff each, in separate git worktrees | the chosen diff is applied to your working tree |
| **ARCH** | design proposals with diagrams, migration paths and spikes | an ADR is written, and optionally implementation steps |

Install (user-level, works in every project):

```bash
cp -r solve ~/.claude/skills/
```

Layout:
- `solve/SKILL.md`: the workflow.
- `solve/prompts/`: solver, critique and judge prompts per variant. CODE angles are in `code-angles.md`.
- `solve/templates/adr.md`: the ADR template.
- `evals/`: test prompts and fixture repos.
- `examples/`: full outputs of test runs.
