# Example: critique through fresh agents (how Copilot runs it)

`/solve product_url("Crème Brûlée") returns "/p/cr-me-br-l-e" instead of "/p/creme-brulee"` on `evals/fixtures/shop-repo`.

Solvers were **not** resumed for the critique. Instead, one fresh agent per solver was told which approach was "its own" and read that solver's `approach.md` plus `notes.md`. This is the fallback used when `SendMessage` isn't available, as in GitHub Copilot.

- **Notes:** 147–187 words each, listing files read (`path:line`), commands run and their results, alternatives rejected, and doubts.
- **Critics used the notes:** each reported which entries it relied on or re-ran. For example, b's critic re-ran the baseline and reproduced c's recorded `casefold` results. c's critic used b's "rejected casefold" note to show that b misses `ẞ`.
- **New findings that no solver had:**
  - a's lossy fix creates URL collisions (`Straße` and `Strae` both become `strae`).
  - b's table runs in the wrong order (`STRAẞE` → `strae`).
  - c casefolds before NFKD, which loses `™` (`Café™` → `cafe`).
- **Judge:** WINNER c, with its "optional" table made mandatory and casefold moved after NFKD. Every major objection was checked against a scratch script.
