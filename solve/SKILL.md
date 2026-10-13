---
name: solve
description: Multi-agent "competing solutions" workflow for hard programming problems. Spawns 2-5 independent solver sub-agents that each attack the same problem from a different angle, has them critique each other, and has a fresh judge recommend one. Every option is then presented to the user, who approves which one to go with. By default solvers propose approaches without writing code; with --build they each implement and test a diff in their own git worktree. Handles CODE problems (a bug, failing behavior, algorithm or feature) and ARCHITECTURE problems (design decisions, patterns, data models, scaling, refactoring strategy → design proposals and an ADR). It is expensive, so use it ONLY when the user invokes /solve or explicitly asks for several competing/alternative approaches to be produced and compared (e.g. "have a few agents come up with different ways to fix this and pick the best"). Do NOT use it for ordinary bug fixes, features, design questions or reviews, however hard, unless the user asks for that multi-solver process.
argument-hint: "<problem description> [--build] [--mode code|arch] [--light|--full] [--n 2-5]"
---

# /solve: competing solutions, evidence-based pick, user approves

Several solvers work the same problem independently with deliberately different angles. They critique each other, and a judge who wrote none of it recommends one. The user then sees **every** option next to the judge's verdict and approves what gets built. The point is to beat the single-attempt answer, so the parts that matter most are **divergence** (solvers must not converge on the same idea) and **evidence** (code references, experiments and tests decide, not eloquence).

Input: `$ARGUMENTS`

## Variants

| | CODE (default) | CODE `--build` | ARCH |
|---|---|---|---|
| Solvers produce | an approach (`approach.md`), no code | a tested diff, each in its own worktree | a design proposal (`proposal.md`) with spikes |
| Worktrees | none | yes | yes (for spikes) |
| Evidence | code references and read-only checks | the oracle test run on every diff | spikes and constraint checks |
| Critique round | yes | no (tests are the critique) | yes |
| After approval | implement the chosen approach once, test-first | apply the chosen diff | write the ADR, offer implementation steps |

Prompt templates live next to this file in `prompts/` and `templates/`. Read the ones for the active variant when you reach the step that uses them, and fill every `{{PLACEHOLDER}}` before sending. Angle texts for CODE are in `prompts/code-angles.md`.

## 0. Setup

- Parse flags out of the input: `--build`, `--mode code|arch` (else auto-detect), `--n N` (default 3; clamp to 2..5 and say so if you clamp). The rest is the problem text. `--build` only applies to CODE; if it comes with an ARCH problem, say so and ignore it. `--light` / `--full` force the ARCH depth (see below).
- Locate the repo and create a run directory inside it, excluded from git locally so it never shows up in `git status`:
  ```bash
  REPO=$(git rev-parse --show-toplevel)
  RUN_ID=$(date +%Y%m%d-%H%M%S)
  RUN_DIR="$REPO/.claude/solve/$RUN_ID"; mkdir -p "$RUN_DIR"
  EXCL="$(git rev-parse --path-format=absolute --git-common-dir)/info/exclude"; mkdir -p "$(dirname "$EXCL")"
  grep -qxF '.claude/solve/' "$EXCL" 2>/dev/null || echo '.claude/solve/' >> "$EXCL"
  ```
- **Leftovers from earlier runs.** An interrupted run (Ctrl-C, crashed session) can leave worktrees, branches and run dirs behind. Check before creating new ones:
  ```bash
  git -C "$REPO" worktree prune
  git -C "$REPO" worktree list --porcelain | sed -n 's/^worktree //p' | grep '/\.claude/solve/'
  git -C "$REPO" branch --list 'solve/*' --format='%(refname:short)'
  ls -d "$REPO"/.claude/solve/*/ 2>/dev/null | grep -v "/$RUN_ID/"
  ```
  If anything shows up, list it (run ids and dates; note any run dir that still holds a `solution.diff`, `approach.md` or `judgment.md`) and ask whether to remove it. Ask rather than delete, because a leftover may be an unapplied winning diff or a `/solve` run still going in another session. To remove a run `<ID>`: `git worktree remove --force` each `.claude/solve/<ID>/wt-*`, `git branch -D` its `solve/<ID>-*` branches, then `rm -rf .claude/solve/<ID>`. Touch only paths under `.claude/solve/` and branches under `solve/`, never other worktrees or branches.
- Not a git repo? The default CODE variant doesn't need one (put the run dir in a temp dir instead). `--build` and ARCH spikes need worktrees: ask whether to `git init` and commit a baseline, or to stop.

## 1. UNDERSTAND

1. Investigate the codebase enough to restate the problem in 1–2 sentences and list the relevant files and modules.
2. **Mode.** CODE means a concrete bug, failing behavior, algorithm or feature. ARCH means a decision about structure, patterns, technologies, data models, scaling or refactoring strategy. Tell the user which mode, and which variant, with a one-line reason.

   The difference that matters: in CODE the problem defines success, so fixed criteria work. In ARCH there are several valid answers, so the user's priorities must be written down first. For borderline requests, ask yourself:
   - **Is the correct outcome known and testable?** ("returns X instead of Y", "crashes on empty input") → leans CODE.
   - **Would the answer introduce a new technology, data model, persistence layer, or module/service boundary, or change one many callers depend on?** → leans ARCH.
   - **Does choosing between reasonable answers require the user's priorities** (cost vs. simplicity vs. scale vs. migration risk)? → leans ARCH.

   Investigate before answering these; the code often settles it. For example, a slow endpoint caused by one missing index is CODE, while one slow because of the data model is ARCH. If the answers point in different directions, or you can't tell without the user's priorities, ask. Borderline examples:

   | Request | Mode | Why |
   |---|---|---|
   | "`/report` takes 8 s" (one N+1 query found) | CODE | outcome testable (fast enough), fix is local |
   | "`/report` takes 8 s" (whole table scanned per request because of how events are stored) | ARCH | fixing it means changing the data model |
   | "Add retry to the HTTP client" | CODE | a feature with clear behavior, inside one module |
   | "Add caching to the API client" | ask | could be a small memoization (CODE) or an invalidation strategy shared across services (ARCH); depends on scope and priorities |
   | "Split `utils.py`, it's 3000 lines" | ARCH (light) | refactoring strategy: the new module boundaries are the decision, but it stays in one package and is easy to revert |
   | "Rename `get_user` to `fetch_user` everywhere" | CODE | mechanical, outcome checkable |
3. **Ambiguity.** If the problem is ambiguous in a way that would change the solution, ask at most 2 questions (one message, use AskUserQuestion if available). Otherwise proceed. Don't ask for the sake of asking.

### CODE (default): pin down the problem
Solvers need a shared, concrete picture of the failure, and the implementation step needs a way to prove the fix.
- Reproduce it: find an existing test, or run a short snippet or command that shows the wrong behavior. Show the user the command and its output. Don't add files to the repo yet; the failing test is written as the first step of implementation, once an approach is approved.
- Write `VERIFY_PLAN`: the test(s) a correct fix must make pass, and the existing tests that must keep passing.

### CODE `--build`: establish the oracle
Here the oracle test is what makes the pick evidence-based, so get it right before spending N agents on the problem.
- Look for existing tests covering the behavior, a documented repro, or a way to run the code.
- If nothing demonstrates the problem, write a small failing test (preferred, in the project's test framework and location) or a repro script. Show the user the file and its failing output, then continue (they can interrupt).
- Record `VERIFY_CMD` (fails now, must pass after), `REGRESSION_CMD` (the related existing tests, or the full suite if it is fast), `REPRO_FILES`, and the baseline output of both. Note tests that already fail on HEAD so solvers aren't blamed for them.
- A repro that fails for the wrong reason (import error, missing fixture) is not a repro. Check that the failure message matches the reported bug.

### ARCH: pick the depth first
The ceremony must fit the size of the decision. A two-page proposal per solver for splitting one module is waste, and the user will stop reading.
- **Light** applies when the decision stays inside one module or package, adds no new technology, dependency, data model or persistence, doesn't change an API that other teams or services consume, and is cheap to reverse. Examples: splitting a large file, choosing between two patterns for one component, reorganizing a package's internals.
- **Full** applies to anything else: new technology or storage, data model changes, cross-module or service boundaries, scaling, or decisions that are costly to undo.

Say which one and why in the same line as the mode, e.g. "ARCH (light): splitting `utils.py` stays inside one package and is easy to revert". The user can override it, or pass `--light` / `--full`.

| | Light | Full |
|---|---|---|
| Requirements | 3–5 constraints and 2–4 weighted criteria, shown inline in chat, with one quick confirm | `requirements.md` as below, with the user approving it |
| Proposal length | under half a page (~300 words) | 1–2 pages |
| Diagram | only if it says more than a list | required |
| Spikes / worktrees | only for an assumption the choice actually hinges on | for every uncertain key assumption |
| Critique | 1–2 sentences per objection | as in `prompts/critique.md` |
| After approval | implement now, or list the steps; ADR only if asked | ADR, then optionally steps |

### ARCH: requirements and criteria (user checkpoint)
(Light depth: the same content, condensed to a short inline list.) Write `$RUN_DIR/requirements.md` containing:
- **Functional needs**, **scale/performance** expectations, **team & codebase conventions**, **existing dependencies** worth reusing, and **what must not break**.
- Mark each constraint **HARD** (violating it disqualifies a proposal) or **SOFT**.
- **Evaluation criteria with weights** summing to 100 (e.g. simplicity 25, fit with existing code 20, scalability 15, migration risk 20, effort 20), chosen for this problem rather than a generic list.

Show it to the user and **wait for approval or edits**. Every later step scores against this, so a wrong weight here quietly picks the wrong design.

## 2. DIVERGE

### Worktrees (`--build`, and ARCH full depth; ARCH light only if a spike is needed)
Worktrees branch from HEAD, so they do NOT contain uncommitted work, including a repro you just wrote. Create them yourself (explicit paths make verification and cleanup reliable) and seed each with the current state:
```bash
cd "$REPO"; git diff HEAD --binary > "$RUN_DIR/base.patch"
for L in a b c; do                 # one letter per solver
  WT="$RUN_DIR/wt-$L"
  git worktree add -q -b "solve/$RUN_ID-$L" "$WT" HEAD
  [ -s "$RUN_DIR/base.patch" ] && git -C "$WT" apply "$RUN_DIR/base.patch"
  # copy untracked files the problem depends on (e.g. the new repro test) into "$WT" at the same relative path
  git -C "$WT" add -A && git -C "$WT" -c user.name=solve -c user.email=solve@localhost commit -qm "solve: base" --no-verify --allow-empty
  git -C "$WT" rev-parse HEAD > "$RUN_DIR/base-$L.sha"; mkdir -p "$RUN_DIR/$L"
done
```
A worktree is a bare checkout, which causes two common problems:
- **Missing untracked dependencies.** Symlink or reinstall `node_modules`, `.venv`, `vendor/` and `.env`.
- **Tests importing the main checkout.** Editable Python installs and absolute `PYTHONPATH`s point at the main tree, so run from the worktree root or set `PYTHONPATH` to it.

**`--build`: run `VERIFY_CMD` in one fresh worktree before launching solvers.** It must fail the same way it does in the main tree, which proves the oracle works inside worktrees.

For the default CODE variant, just `mkdir -p "$RUN_DIR"/{a,b,c}`. Solvers read the main checkout and don't edit it.

### Launch
Prompts:
- CODE (default): `prompts/code-plan-solver.md`
- `--build`: `prompts/code-solver.md`
- ARCH: `prompts/arch-solver.md`

Angles are assigned in order a, b, c, d, e:

| | CODE (`prompts/code-angles.md`) | ARCH (in `prompts/arch-solver.md`) |
|---|---|---|
| a | minimal fix | simplest design that meets the requirements |
| b | most robust / maintainable | most scalable / extensible |
| c | root cause or alternative approach | different in kind (other pattern, or reuse what exists) |
| d | reuse-first (library/stdlib/existing util) | incremental / evolutionary path |
| e | change the data model so the bug can't exist | buy-not-build (off-the-shelf) |

Launch **all solvers in a single message**: parallel `Agent` calls, general-purpose type, no `isolation` (they get their worktree path in the prompt). Give each a short name like `solver-a` so you can message it later. Pass them what you learned in step 1 (restatement, relevant files, repro, requirements path) so they don't redo it, but never another solver's ideas. Wait until all have finished.

## 3. VERIFY

### CODE (default)
Check each `approach.md`'s load-bearing claims:
- Do the cited `path:line`s exist and say what the approach claims?
- Does the diagnosis match the repro?
- Where solvers disagree on the cause, find out who's right: read the code, or run the repro once.

Disqualify an approach that doesn't solve the stated problem or rests on a false claim about the code, and record why. Write `$RUN_DIR/verification.md`. If all are disqualified, report what each proposed and why it fails, and suggest a next step. Stop there.

### CODE `--build`
For each solver, in its worktree:
```bash
git -C "$WT" add -A && git -C "$WT" diff --cached "$(cat $RUN_DIR/base-$L.sha)" > "$RUN_DIR/$L/solution.diff"
```
Then restore the canonical repro files over the solver's copy. A solver that edited the test to pass must not get credit, so flag it if the diff touches them. Run `VERIFY_CMD` and `REGRESSION_CMD` from the worktree and save the outputs to `$RUN_DIR/$L/verify.txt`.

A solution **fails** if any of these hold, and you record the reason:
- the repro still fails
- it introduces a regression vs. baseline
- the diff is empty
- it only passes by special-casing the test input

**All failed?** Skip judging. Report what each tried, why it failed, the most informative failure, and a concrete next step (a better repro, a narrower problem, a specific hypothesis to test). Then clean up.

### ARCH
Check every proposal (`$RUN_DIR/$L/proposal.md`) against each HARD constraint in `requirements.md`, and disqualify violators with the reason. Mark each key claim:
- **evidence**: a spike ran and its output is in the report. Re-run it if that's cheap and decisive.
- **assumption**: asserted, untested.

Write `$RUN_DIR/verification.md`. If all are disqualified, report why and propose what to relax or investigate. Stop there.

## 4. CRITIQUE (CODE default and ARCH)

Each surviving solver reviews the others. Read `prompts/critique.md` and send it to every solver via `SendMessage`; continuing a solver keeps its own investigation in context. If messaging a finished agent isn't possible, spawn one fresh agent per solver and tell it which solution is "its own". Send all in one message and wait for all. Output goes to `$RUN_DIR/$L/critique.md`.

## 5. JUDGE

Spawn **one fresh agent** that wrote none of the solutions. Prompts:
- CODE (default): `prompts/code-plan-judge.md`
- `--build`: `prompts/code-judge.md`
- ARCH: `prompts/arch-judge.md`

Give it file paths, not pasted content: the problem restatement, the solutions, verification results (including disqualified ones and why), the critiques, and for ARCH the weighted requirements. Don't share your own preference. The judge may declare a **close call** instead of forcing a pick, and must then say what would decide it. With a single survivor the judge still reviews it, and can reject it.

## 6. PRESENT ALL AND GET APPROVAL

The user decides, not the judge. Show **every** solution (disqualified ones included, briefly) next to the judge's verdict, in one view:

```
## /solve: <one-line problem>
Mode: CODE · approaches only | CODE · --build | ARCH · Solvers: N · Judge: WINNER <L> | CLOSE CALL <L1> vs <L2>

### a: <angle>: <one-line summary>          [judge's pick] / [disqualified: reason]
<2–4 sentences: what it changes and where (`path:line`), and why that fixes it>
+ <its main strength>
− <its strongest objection, from the critiques or the judge>
Size: S/M/L · Confidence: N/10 · <--build: Verify pass/FAIL · diffstat> <ARCH: score NN/100>

### b: ...

### Judge's recommendation: <L>
<3–5 sentences: why. If it's a close call, say what decides it.>
Borrow from runners-up: <specific ideas, or "none">
Convergence: <solvers that independently landed on the same idea despite different angles, or "none">
```

Convergence is worth reporting either way. Independent agreement raises confidence in an idea, but it also means the comparison covered fewer real alternatives than N suggests. Each solver's full write-up is in `$RUN_DIR/<L>/`; point to it.

Then ask with AskUserQuestion in one call:
1. **Which one?** One option per solution, with the judge's pick first and marked "(Recommended)". With more than 4 solutions, show the top 3 and let "Other" cover the rest or a combination ("b, plus c's test for X").
2. **What next?** Choices depend on the variant:
   - CODE (default): "Implement it now" / "Just keep the plan"
   - `--build`: "Apply the diff to my working tree" / "Don't apply"
   - ARCH (full): "Write the ADR and break it into steps" / "Write the ADR only"
   - ARCH (light): "Implement it now" / "Just list the steps" / "Write an ADR"

## 7. AFTER APPROVAL

- **CODE (default), implement:**
  1. Write the failing test from `VERIFY_PLAN` and show it failing.
  2. Implement the approved approach, plus any borrowed ideas, in the user's working tree.
  3. Run the tests and show the diff.
  4. Don't commit unless asked.
  If implementation reveals the approach was wrong, stop and say so rather than silently switching approaches.
- **CODE (default), keep the plan:** print the approved approach in full and offer to save it as a file.
- **`--build`, apply:** `git apply "$RUN_DIR/<L>/solution.diff"` onto the working tree (the base changes, e.g. the repro test, are already there). Fold in any borrowed ideas, then re-run `VERIFY_CMD`.
- **ARCH (light):** implement as for CODE (default), as a sequence of small steps that each keep the tests green, or print the steps. Write an ADR only if asked.
- **ARCH (full):**
  1. Write the ADR. Find where the repo keeps decisions (`docs/decisions/`, `docs/adr/`, `doc/adr/`, `adr/`, `architecture/decisions/`) and follow its numbering and format. Otherwise use `docs/decisions/NNNN-<slug>.md` with `templates/adr.md`.
  2. Record the option the user chose as the decision, with status `Accepted`. If they overrode the judge, say so and give their reason in the rationale.
  3. If they asked for steps, write each implementation step as a self-contained `/solve --mode code …` prompt they can run later.

## Cleanup (always, including after failure or abort)

Save anything still needed before removing worktrees (diffs are in `$RUN_DIR`). If the run created worktrees:
```bash
for L in a b c; do git -C "$REPO" worktree remove --force "$RUN_DIR/wt-$L"; git -C "$REPO" branch -D "solve/$RUN_ID-$L"; done
git -C "$REPO" worktree prune
```
After the user's decision has been carried out, delete `$RUN_DIR` (mention it first if they might want the other solutions' write-ups or diffs). Confirm that `git worktree list` and `git branch --list 'solve/*'` show nothing left from this run.
