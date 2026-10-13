# solve: a Claude Code skill for competing solutions

`/solve <problem> [--build] [--mode code|arch] [--n 2-5]`

Several sub-agents work the same problem independently, each from a different angle (minimal, robust, root-cause, …). They critique each other, and a judge who wrote none of the solutions recommends one. **You see every option next to the judge's verdict and approve which one to go with.**

| | What solvers produce | After you approve |
|---|---|---|
| **CODE** (default) | approaches only: diagnosis, the change, trade-offs, size. No code. | Claude implements the chosen approach once, test-first |
| **CODE `--build`** | a tested diff each, in separate git worktrees | the chosen diff is applied to your working tree |
| **ARCH** | design proposals with diagrams, migration paths and spikes | an ADR is written, and optionally implementation steps |

## Install

**Claude Code** (user-level, works in every project):

```bash
cp -r solve ~/.claude/skills/
```

**GitHub Copilot, agent mode** (VS Code, JetBrains/IntelliJ). This is untested.

1. Turn on skills. In JetBrains this is Settings → GitHub Copilot → Chat → Agent; it was a public preview as of early 2026. On Business or Enterprise plans, an admin may need to enable the "Editor preview features" policy first.
2. Install the skill, ideally in both places:

   ```bash
   cp -r solve ~/.copilot/skills/                # personal, all projects
   mkdir -p .github/skills && cp -r solve .github/skills/   # per project, if the personal folder isn't picked up
   ```

3. In agent mode, ask "which skills do you have?" to confirm `solve` is listed.

Differences from Claude Code:
- Critiques run in fresh subagents rather than resuming each solver, so they're somewhat shallower.
- The approval question is asked in plain chat.
- Solvers may run one after another rather than in parallel.

Layout:
- `solve/SKILL.md`: the workflow.
- `solve/prompts/`: solver, critique and judge prompts per variant. CODE angles are in `code-angles.md`.
- `solve/templates/adr.md`: the ADR template.
- `evals/`: test prompts and fixture repos.
- `examples/`: full outputs of test runs.
