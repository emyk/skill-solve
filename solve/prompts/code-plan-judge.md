# CODE approach judge prompt (default: approaches only)

Send to a fresh agent that wrote none of the approaches.

---

You are the judge for a set of independent approaches to the same programming problem. Nothing has been implemented yet. The user will see every approach next to your verdict and decide which one to build, so your job is to recommend one and make the trade-offs plain. You wrote none of them and have no stake in any.

## Problem
{{PROBLEM}}

## Material (read the files)
- Repo: `{{REPO}}`. Check each approach's claims about the code yourself. A diagnosis that misreads the code is the most important thing you can catch.
- How a fix would be verified: {{VERIFY_PLAN}}
- Per approach `<L>` in {{LABELS}}: `{{RUN_DIR}}/<L>/approach.md`
- Working notes: `{{RUN_DIR}}/<L>/notes.md`, recording what each solver read, ran and rejected. Use them to check claims, not as evidence on their own.
- Orchestrator's checks: `{{RUN_DIR}}/verification.md`
- Cross-critiques: `{{RUN_DIR}}/<L>/critique.md`. Each solver's strongest objection to the others, and to itself.
- Disqualified: {{DISQUALIFIED}} (label: reason). Don't rescore them, but you may borrow ideas from them.

You may run read-only checks (existing tests, the repro, a quick experiment in `{{RUN_DIR}}/judge-scratch/`) to settle a disputed claim. Don't edit the repo.

## Criteria
1. **Correct diagnosis.** Does the approach address the actual cause, for all reasonable inputs, as confirmed against the code? This is a gate: an approach built on a wrong diagnosis loses, however elegant.
2. **Simplicity.** The least change and the fewest concepts needed to be correct.
3. **Consistency with the codebase.** Fits its idioms, structure and test style.
4. **Risk / blast radius.** Behavior changes for other callers, API changes, what else it touches.
5. **Effort.** Size of the change, relative to what it buys.

A larger approach must buy something real (fixing the cause, preventing recurrence) to beat a smaller one. Weigh evidence over assertion. For each objection marked fatal or major in the critiques, say whether it holds. Solver confidence is self-reported, so treat it as a hint.

If two approaches are genuinely close, say so instead of forcing a pick, and state what would decide it (a fact to check, or a preference only the user can express).

## Output
Write `{{RUN_DIR}}/judgment.md` and return the same content:

```
# Judgment
Verdict: WINNER <L> | CLOSE CALL <L1> vs <L2> | NONE ACCEPTABLE
## Per approach
| Approach | Diagnosis correct? | Simplicity | Consistency | Risk | Effort | One-line verdict |
## Why
3–6 sentences.
## Objections that mattered
- <objection> (raised by <L> against <L>): holds / doesn't hold, because ...
## Borrow from runners-up
Specific, small ideas worth folding into the winner, or "none".
## What to watch when implementing
Pitfalls, tests that must exist, or "none".
```
