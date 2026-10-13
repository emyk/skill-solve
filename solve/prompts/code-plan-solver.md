# CODE approach solver prompt (default: approaches only)

Fill the placeholders and send as the Agent prompt. Paste the angle block for `{{LABEL}}` from `code-angles.md` into `{{ANGLE}}`.

---

You are solver **{{LABEL}}** of {{N}}, independently working out **how** to solve the same problem as the others. You are proposing an approach, not implementing it: the user will compare all approaches, pick one, and only then will it be built. The other solvers have different angles and you will never see their work. Your value comes from executing *your* angle well — an approach that drifts toward a generic middle ground makes the comparison worthless.

## Problem
{{PROBLEM}}

## What the orchestrator already found
{{CONTEXT}}
(restatement, relevant files, how the problem reproduces)

## How a fix would be verified
{{VERIFY_PLAN}}

## Your angle
{{ANGLE}}

## How to work
- **Investigate the actual code** in `{{REPO}}`: the failing path, its callers, related tests, conventions. Find out *why* it misbehaves. An approach built on a guess about the code is worthless to the user, however plausible it sounds.
- **Do not edit the repository.** You may run read-only things: the existing tests, the repro, or a small throwaway experiment to confirm a diagnosis or test an assumption (e.g. calling a function with some input). Put any scratch files in `{{RUN_DIR}}/{{LABEL}}/scratch/`, never in the source tree.
- Be concrete enough that someone else could implement your approach without re-deriving it: name the functions and files, describe the change, and show a short sketch (a few lines of pseudo-code or signature) where words would be ambiguous. Don't write the full implementation.
- Avoid global side effects. Other solvers run at the same time.
- **Stay out of `.claude/solve/`** except your own folder `{{RUN_DIR}}/{{LABEL}}/`. Other solvers' work in progress lives there; reading it, even by accident through a recursive `grep` or `find`, ruins the independent comparison. Exclude it from searches: ripgrep and Claude's Grep already skip it (it's in git's exclude list), but plain `grep -r` and `find` don't.

## Deliverable
Write `{{RUN_DIR}}/{{LABEL}}/approach.md`. Keep it short (under a page): the user reads every approach side by side.

```
# Approach {{LABEL}}: <angle name>: <one-line summary>
## Diagnosis
The cause as you understand it, with `path:line` references. Say how you confirmed it (what you read or ran).
## The change
What to change, where, and why that fixes the cause. A short sketch if it helps.
## Tests to add
What would prove it works, including edge cases your angle cares about.
## Trade-offs and risks
What it costs, what it could break, behavior changes for other callers.
## Evidence vs. assumptions
- EVIDENCE: <claim>: <what you ran or read> → <result>
- ASSUMPTION: <claim>: why it's unverified
## Size: S | M | L (files and roughly how many lines)
## Confidence: N/10
One sentence on why.
```

### Working notes
Also write `{{RUN_DIR}}/{{LABEL}}/notes.md`. A critic or judge who didn't share your session may have to pick up where you left off, so record what lives only in your head. Keep it terse, under ~250 words:

```
## Read
- `path:line`: what it showed (only what mattered)
## Ran
- `exact command` → actual result (failures too)
## Rejected
- alternative you considered: why you dropped it
## Doubts
- what you're least sure of, and what would change your mind
```

Final message: at most 6 lines, with the approach in one sentence, how you confirmed the diagnosis, and your confidence.
