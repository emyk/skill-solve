# CODE angles

Shared by `code-plan-solver.md` (approaches only) and `code-solver.md` (`--build`). Paste the block for the solver's letter into `{{ANGLE}}`. In approaches-only mode, the angle shapes the approach you propose rather than the code you write.

**a — Minimal fix.** The smallest correct change: fewest lines and files touched, no refactoring, no drive-by cleanups, existing style. "Minimal" means minimal *correct* — it must fix the actual cause for all inputs, not just the reported one.

**b — Most robust / maintainable.** The fix you'd want to live with for years. Handle the related edge cases you discover (and test them), make the intent obvious in the code, and do a small local refactor if it makes the fix clearer. Stay within the problem's scope — robust, not sprawling.

**c — Root cause or alternative approach.** Question the framing. Trace *why* the problem exists — a broken invariant, wrong data structure, misused API, an earlier layer producing bad data — and fix it where it originates rather than where it surfaces. If the surface location really is the root cause, use a materially different technique from the obvious patch (different algorithm, different control flow). Say what the obvious fix would have been and why you didn't choose it.

**d — Reuse-first.** Look for something that already solves this: a utility elsewhere in the codebase, the standard library, a feature of an existing dependency or framework. Replace hand-rolled logic with it where that fixes the problem. If nothing fits, say what you checked and fall back to the cleanest fix built on existing abstractions.

**e — Change the representation.** Make the bug impossible rather than fixed: change how the data is modeled, typed or validated (stronger types, an invariant enforced at construction, a different data structure) so this class of error can't recur. If the problem is performance-shaped, change the data structure or algorithm instead. Keep the change proportionate.
