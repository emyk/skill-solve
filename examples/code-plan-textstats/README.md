# Example: default (approaches-only) CODE run

`/solve top_words("Hello, world! Hello.") gives [('hello,', 1), ...] instead of [('hello', 2), ('world', 1)]`

1. **Understand.** The bug was reproduced with a one-line snippet, and no files were added. VERIFY_PLAN was written.
2. **Approaches.** Three solvers each wrote an `approach.md` without editing the repo: a (strip punctuation at token ends), b (word regex plus apostrophe normalization), c (the same regex without normalization).
3. **Verify.** The orchestrator ran all three proposed tokenizers on the same inputs. a only works when a space follows the punctuation (`verification.md`).
4. **Critique.** Each solver objected to the others (`*/critique.md`). c conceded to b, and b found its own NFD-accent gap.
5. **Judge.** WINNER b. Borrow NFC normalization and c's `average_word_length` test (`judgment.md`).
6. **Present and approve.** All three approaches were shown with the judge's pick. The user chose b.
7. **Implement.** 6 failing tests were written first, then b was implemented with the borrowed ideas, giving 11/11 passing (`implemented.diff`).

No worktrees were created. The run directory was deleted after implementation.
