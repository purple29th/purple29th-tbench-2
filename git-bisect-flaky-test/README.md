# git-bisect-flaky-test

## Description

A small Go module's regression test started failing somewhere in the last 25 commits, but the test is also intermittently flaky on commits unrelated to the bug. The flake rate shifts at the bad commit (good commits flake at roughly 30%, buggy commits fail roughly 95% of the time), so naive `git bisect run`, simple "any pass means good", and "any fail means bad" classifiers all produce the wrong answer.

The agent must run each candidate commit multiple times, classify by failure-rate threshold, identify the commit at which the failure rate jumps, and write the SHA plus a short diagnosis to `/app/answer.txt`.

## Completion Rates

- Oracle: pending
- Avocado (`meta/avocado_dvsc_tester`): measured by platform on submission
- Opus (`claude-opus-4-6`): measured by platform on submission

## Model Analysis

Failure modes the task is designed to surface:

- Naive `git bisect run` on a single test invocation lands on a flake-affected good commit.
- Retry-once-and-trust strategies still produce wrong answers when the good-commit flake rate is non-trivial.
- Models that fix the seed via environment variables short-circuit the test entirely and miss the rate-shift signal.
- Models that grep source for the bug instead of running tests skip the statistical reasoning the task is built around.

## Anti-Cheating Analysis

- **Hidden ground truth:** The expected commit hash is resolved at verify time by grepping the commit message in `/tests/expected/regression_label.txt`, mounted only during verification.
- **No solution leakage:** The `solution/` directory is excluded from the Docker build context. Only the prepared repo at `/app/repo` is in the agent container.
- **Source-grep bypass:** The diagnosis line requires at least two of `settle`, `recipients`, `platform` (case-insensitive). Models can emit those words without running tests, but they will still get the SHA wrong without measurement.
- **Force-pass bypass:** Forcing tests to pass via env var (an obvious shortcut) makes the test pass on the buggy commit too, producing the wrong SHA.
