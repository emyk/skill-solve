# Verification (orchestrator)
Repo untouched by solvers (git status: only __pycache__). All three cite textstats/tokenize.py:4-6 (`text.lower().split()`) correctly; all agree on the diagnosis.

Each approach's proposed tokenizer, run by the orchestrator on the same inputs:
| input | a (strip \W at token ends) | b (word regex + ’→') | c (word regex) |
|---|---|---|---|
| "Hello, world! Hello." | hello, world, hello | same | same |
| "well - that is that" | drops "-" | drops "-" | drops "-" |
| "hello—world" | ['hello—world'] (one token) | hello, world | hello, world |
| "one,two" | ['one,two'] | one, two | one, two |
| "Don’t don't" | two different words | both "don't" | two different words |
| "snake_case 3.14" | kept whole | snake, case, 3, 14 | snake, case, 3, 14 |

All three fix the reported case and the standalone "-" (VERIFY_PLAN). None disqualified.
Note: b and c propose the same regex (convergence); b adds apostrophe normalization.
