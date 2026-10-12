---
name: solve
description: Multi-agent "competing solutions" workflow for hard programming problems. Spawns 2-5 independent solver sub-agents that each attack the same problem from a different angle, verifies their work, and has a fresh judge pick a winner from the evidence. Handles CODE problems (a bug, failing behavior, algorithm or feature → a tested diff, each solver in its own git worktree) and ARCHITECTURE problems (design decisions, patterns, data models, scaling, refactoring strategy → cross-critiqued proposals and an ADR). It is expensive, so use it ONLY when the user invokes /solve or explicitly asks for several competing/alternative solutions to be produced and compared (e.g. "have a few agents try this independently and pick the best"). Do NOT use it for ordinary bug fixes, features, design questions or reviews, however hard, unless the user asks for that multi-solver process.
argument-hint: "<problem description> [--mode code|arch] [--n 2-5]"
---

# /solve — competing solutions, evidence-based pick

Several solvers work the same problem independently with deliberately different angles; you verify what they produce; a judge who wrote none of it picks. The point is to beat the single-attempt answer, so the parts that matter most are **divergence** (solvers must not converge on the same idea) and **evidence** (tests, spikes and constraint checks decide, not eloquence).

Input: `$ARGUMENTS`

Prompt templates live next to this file (`prompts/`, `templates/`). Read the ones for the active mode when you reach the step that uses them; fill every `{{PLACEHOLDER}}` before sending.

## 0. Setup

- Parse flags out of the input: `--mode code|arch` (else auto-detect), `--n N` (default 3; clamp to 2..5 and say so if you clamp). The rest is the problem text.
- Locate the repo and create a run directory inside it, excluded from git locally so it never shows up in `git status`:
  ```bash
  REPO=$(git rev-parse --show-toplevel)
  RUN_ID=$(date +%Y%m%d-%H%M%S)
  RUN_DIR="$REPO/.claude/solve/$RUN_ID"; mkdir -p "$RUN_DIR"
  EXCL="$(git rev-parse --path-format=absolute --git-common-dir)/info/exclude"; mkdir -p "$(dirname "$EXCL")"
  grep -qxF '.claude/solve/' "$EXCL" 2>/dev/null || echo '.claude/solve/' >> "$EXCL"
  ```
- Not a git repo? Worktrees need one. Tell the user and ask whether to `git init` + commit a baseline, or stop. (ARCH mode can run without worktrees if no spike is needed.)

## 1. UNDERSTAND

1. Investigate the codebase enough to restate the problem in 1–2 sentences and list the relevant files/modules.
2. **Mode.** CODE = a concrete bug, failing behavior, algorithm or feature whose output is a diff. ARCH = a decision about structure, patterns, technologies, data models, scaling or refactoring strategy whose output is a design. Tell the user which mode and the one-line reason. If it genuinely could be either (e.g. "fix our slow sync" could be a patch or a redesign), ask.
3. **Ambiguity.** If the problem is ambiguous in a way that would change the solution, ask at most 2 questions (one message, use AskUserQuestion if available). Otherwise proceed — don't ask for the sake of asking.

### CODE mode: establish the oracle

The verification command is what makes the final pick evidence-based, so get it right before spending N agents on the problem.
- Look for existing tests covering the behavior, a documented repro, or a way to run the code.
- If nothing demonstrates the problem, write a small failing test (preferred, in the project's test framework and location) or a repro script. Show the user the file and its failing output, then continue (they can interrupt).
- Record: `VERIFY_CMD` (fails now, must pass after), `REGRESSION_CMD` (the relevant/related existing tests; the full suite if it is fast), `REPRO_FILES`, and the baseline output of both. Note tests that already fail on HEAD so solvers aren't blamed for them.
- A repro that fails for the wrong reason (import error, missing fixture) is not a repro. Check the failure message matches the reported bug.

### ARCH mode: requirements and criteria — user checkpoint

Write `$RUN_DIR/requirements.md` containing:
- **Functional needs**, **scale/performance** expectations, **team & codebase conventions**, **existing dependencies** worth reusing, **what must not break**.
- Mark each constraint **HARD** (violating it disqualifies a proposal) or **SOFT**.
- **Evaluation criteria with weights** summing to 100 (e.g. simplicity 25, fit with existing code 20, scalability 15, migration risk 20, effort 20) — chosen for this problem, not a generic list.

Show it to the user and **wait for approval or edits** — every later step scores against this, so a wrong weight here quietly picks the wrong design.

## 2. DIVERGE

### Worktrees (CODE always; ARCH so solvers can spike)
Worktrees branch from HEAD, so they do NOT contain uncommitted work — including a repro you just wrote. Create them yourself (explicit paths make verification and cleanup reliable) and seed each with the current state:
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
Environment pitfalls — a worktree is a bare checkout: symlink or reinstall untracked deps (`node_modules`, `.venv`, `vendor/`, `.env`), and make sure tests import the worktree's code, not the main checkout (editable Python installs and absolute `PYTHONPATH`s point at the main tree; run from the worktree root or set `PYTHONPATH` to it). **CODE mode: run `VERIFY_CMD` in one fresh worktree before launching solvers** — it must fail the same way it does in the main tree. That proves the oracle works inside worktrees.

### Launch
Read `prompts/code-solver.md` or `prompts/arch-solver.md`. Angles (full text in the prompt file) are assigned in order a, b, c, d, e:

| | CODE | ARCH |
|---|---|---|
| a | minimal fix | simplest design that meets the requirements |
| b | most robust / maintainable | most scalable / extensible |
| c | root cause or alternative approach | different in kind (other pattern, or reuse what exists) |
| d | reuse-first (library/stdlib/existing util) | incremental / evolutionary path |
| e | change the data model so the bug can't exist | buy-not-build (off-the-shelf) |

Launch **all solvers in a single message** (parallel `Agent` calls, general-purpose type, no `isolation` — they get their worktree path in the prompt). Give each a short name like `solver-a` so you can message it later. Pass them what you learned in step 1 (restatement, relevant files, requirements path) so they don't redo it, but never another solver's ideas. Wait until all have finished.

## 3. VERIFY

### CODE mode
For each solver, in its worktree:
```bash
git -C "$WT" add -A && git -C "$WT" diff --cached "$(cat $RUN_DIR/base-$L.sha)" > "$RUN_DIR/$L/solution.diff"
```
Then restore the canonical repro files over the solver's copy (a solver that edited the test to pass must not get credit — flag it if the diff touches them), and run `VERIFY_CMD` and `REGRESSION_CMD` from the worktree. Save outputs to `$RUN_DIR/$L/verify.txt`. A solution **fails** if the repro still fails, it introduces a regression vs. baseline, the diff is empty, or it only passes by special-casing the test input. Record the reason for each failure.

**All failed?** Skip judging. Report what each tried, why it failed, the most informative failure, and a concrete next step (a better repro, a narrower problem, a specific hypothesis to test). Then clean up (step 6).

### ARCH mode
Check every proposal (`$RUN_DIR/$L/proposal.md`) against each HARD constraint in `requirements.md`. Disqualify violators, with the reason. For each key claim, mark it **evidence** (a spike ran; output in the report — re-run it if it's cheap and decisive) or **assumption** (asserted, untested). Write `$RUN_DIR/verification.md`. If all are disqualified, report why and propose what to relax or investigate; stop.

## 4. CRITIQUE (ARCH mode only)

Each surviving solver reviews the others: read `prompts/arch-critique.md` and send it to every solver via `SendMessage` (continuing it keeps its own investigation in context). If messaging a finished agent isn't possible, spawn one fresh agent per solver, telling it which proposal is "its own". Send all in one message; wait for all. Output: `$RUN_DIR/$L/critique.md`. One strong, specific objection per proposal beats a list of nitpicks — the prompt says so.

## 5. JUDGE

Spawn **one fresh agent** that wrote none of the solutions, using `prompts/code-judge.md` or `prompts/arch-judge.md`. Give it file paths, not pasted content: problem restatement, the diffs/proposals, verification results (including disqualified ones and why), and for ARCH the requirements with weights and all critiques. Don't share your own preference. The judge may declare a **close call** instead of a forced pick and must say what would decide it. With a single survivor the judge still reviews it — it can reject it.

## 6. REPORT

### CODE mode
```
## /solve result — <one-line problem>
Mode: CODE (<why>) · Solvers: N · Verified by: `VERIFY_CMD`

**Winner: <label> — <angle>**  (confidence x/10, judge's verdict)
<2–4 sentences: what it does and why it won>
<diff stat, and the diff itself if short (< ~60 lines)>
Borrow from runners-up: <specific ideas, or "none">

| Solver | Angle | Verify | Why it lost |
|---|---|---|---|
| b | robust | pass | <one line> |
| c | root cause | FAIL: <reason> | — |

Disagreements: <where the judge and solver confidences/claims conflicted, or "none">
Convergence: <solvers that independently landed on the same approach despite different angles, or "none">
```
Convergence is worth reporting either way: independent agreement raises confidence in that approach, but it also means the comparison covered fewer real alternatives than N suggests.
If it's a close call, present both with the deciding question instead of a winner. Then **ask before applying**: `git apply "$RUN_DIR/<L>/solution.diff"` onto the user's working tree (the base changes, e.g. the repro test, are already there). If they want borrowed ideas folded in, make those edits after applying and re-run `VERIFY_CMD`.

### ARCH mode
Write an ADR. Find where the repo keeps decisions (`docs/decisions/`, `docs/adr/`, `doc/adr/`, `adr/`, `architecture/decisions/`) and follow its numbering and format; otherwise use `docs/decisions/NNNN-<slug>.md` with `templates/adr.md`. Status `Proposed` — the user accepts it, not you. Summarize in chat: decision, runner-up, the 1–2 objections that mattered, scores table, link to the ADR. Then **offer to break the chosen design into implementation steps**, each written as a self-contained `/solve --mode code …` prompt the user can run later.

### Cleanup (both modes, always — including after failure or abort)
Save anything still needed (diffs are in `$RUN_DIR`) before removing worktrees, then:
```bash
for L in a b c; do git -C "$REPO" worktree remove --force "$RUN_DIR/wt-$L"; git -C "$REPO" branch -D "solve/$RUN_ID-$L"; done
git -C "$REPO" worktree prune
```
After the user has decided about applying, delete `$RUN_DIR` (mention it first if they might want the losing diffs). Confirm `git worktree list` and `git branch --list 'solve/*'` show nothing left from this run.
