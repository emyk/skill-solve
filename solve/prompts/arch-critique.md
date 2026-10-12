# ARCH critique prompt

Send to each surviving solver via SendMessage (preferred — it keeps the solver's own investigation in context). If that isn't possible, send to a fresh agent and prepend: "You are standing in for solver {{LABEL}}, whose proposal is `{{RUN_DIR}}/{{LABEL}}/proposal.md`. Read it first and argue from that position."

---

Critique round. You are solver **{{LABEL}}**. The other surviving proposals are:

{{OTHER_PROPOSALS}}
(one line each: label — path to proposal.md)

Requirements and weighted criteria: `{{RUN_DIR}}/requirements.md`. Verification notes (constraint checks, evidence vs. assumption): `{{RUN_DIR}}/verification.md`.

For **each other proposal**, give the **single strongest objection** — the one most likely to make it the wrong choice for *this* problem, given the requirements and criteria. A judge who never wrote any proposal will read this; your job is to surface what they might miss.

- Be concrete. Tie the objection to a requirement, a specific piece of existing code (`path:line`), a spike result, or an untested assumption the design depends on. "Might not scale" is not an objection; "the per-request lookup in step 3 is O(n) over tenants and requirements.md says 5k tenants" is.
- If an objection hinges on a checkable fact and you can check it in a couple of minutes in your worktree (`{{WORKTREE}}`), check it and report the result.
- Then name **one thing that proposal does better than yours**. Honesty here makes your objections more credible.
- Finally, the strongest objection to **your own** proposal, now that you've seen the alternatives.

Don't rewrite your proposal and don't list nitpicks — one sharp objection per proposal is worth more than five soft ones.

Write `{{RUN_DIR}}/{{LABEL}}/critique.md`:

```
# Critique by {{LABEL}}
## On <label>
Objection: ...
Grounding: <requirement / code ref / spike / assumption>
Severity: fatal | major | minor — fatal means it violates a HARD constraint or can't work
They do better than me: ...
## On <label>
...
## On my own proposal
...
```

Final message: one line per proposal with the objection's headline and severity.
