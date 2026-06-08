# Context

There's a bug somewhere in the codebase under `/app/repo`. A test started failing recently, and the job is to identify which commit introduced the regression.

# What's failing

The specific failing test is `TestSettleWithRemainder`.

# Important caveat (flakiness)

This test is flaky, so you shouldn't trust the result of a single run. Reproduce carefully and rely on repeated runs when deciding whether a commit is actually good or bad.

# What to produce

Write your final output to `/app/answer.txt`:

- **Line 1:** the exact commit SHA where the regression was introduced.
- **Line 2:** a one-sentence diagnosis of what actually broke (the root cause, not just "the test failed").

The SHA is verified by the grader, so guessing a hash won't pass.
