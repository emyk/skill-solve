# Critique prompt (CODE approaches and ARCH proposals)

Send to each surviving solver via SendMessage (preferred, because it keeps the solver's own investigation in context). If that isn't possible, send it to a fresh agent and prepend: "You are standing in for solver {{LABEL}}, whose work is `{{RUN_DIR}}/{{LABEL}}/{{DOC}}`. Read it first and argue from that position."

`{{DOC}}` is `approach.md` (CODE) or `proposal.md` (ARCH). `{{CRITERIA}}` is `{{RUN_DIR}}/requirements.md` (ARCH), or the problem statement plus how a fix would be verified (CODE).

---

Critique round. You are solver **{{LABEL}}**. The other surviving solutions are:

{{OTHERS}}
(one line each: label, then the path to its {{DOC}})

What they're judged against: {{CRITERIA}}. The orchestrator's checks (claims verified, evidence vs. assumption): `{{RUN_DIR}}/verification.md`.

For **each other solution**, give the **single strongest objection**: the one most likely to make it the wrong choice for *this* problem. A judge who wrote none of them will read this, and so will the user, who picks which one gets built. Your job is to surface what they might miss.

- Be concrete. Tie the objection to a requirement, a specific piece of existing code (`path:line`), an experiment's result, or an untested assumption the solution depends on. "Might not scale" is not an objection; "the lookup in step 3 is O(n) over tenants and requirements.md says 5k tenants" is.
- If an objection hinges on a checkable fact and you can check it in a couple of minutes ({{CHECK_WHERE}}), check it and report the result. Test under the conditions users really have, not a tuned environment.
- Then name **one thing that solution does better than yours**. Honesty here makes your objections more credible.
- Finally, give the strongest objection to **your own** solution, now that you've seen the alternatives.

Don't rewrite your own solution and don't list nitpicks. One sharp objection per solution is worth more than five soft ones.

Write `{{RUN_DIR}}/{{LABEL}}/critique.md`:

```
# Critique by {{LABEL}}
## On <label>
Objection: ...
Grounding: <requirement / code ref / experiment / assumption>
Severity: fatal | major | minor (fatal means it violates a HARD constraint, misdiagnoses the problem, or can't work)
They do better than me: ...
## On <label>
...
## On my own
...
```

Final message: one line per solution with the objection's headline and severity.
