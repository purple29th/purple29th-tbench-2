# git-bisect-flaky-test

## Description

A small Go module's regression test started failing somewhere in the last 25 commits, but the test is also intermittently flaky on commits unrelated to the bug. The flake rate shifts at the bad commit (good commits flake at roughly 30%, buggy commits fail roughly 95% of the time), so naive `git bisect run`, simple "any pass means good", and "any fail means bad" classifiers all produce the wrong answer.

The agent must run each candidate commit multiple times, classify by failure-rate threshold, identify the commit at which the failure rate jumps, and write the SHA plus a short mechanism diagnosis to `/app/answer.txt`.

## Completion Rates

- Oracle: 3/3 deterministic
- Avocado (`meta/avocado_dvsc_tester`): measured by platform on submission
- Opus (`claude-opus-4-6`): measured by platform on submission

## Model Analysis

Failure modes the task is designed to surface:

- Naive `git bisect run` on a single test invocation lands on a flake-affected good commit.
- Retry-once-and-trust strategies still produce wrong answers when the good-commit flake rate is non-trivial.
- Models that fix the flake by setting environment variables short-circuit the test entirely and miss the rate-shift signal.
- Models that grep source for the bug pattern can identify the buggy diff but cannot identify which commit's `.flake_rate` is high without running the test, because that data lives outside the repo.

## Anti-Cheating Analysis

- **Hidden ground truth:** Per-commit flake rates live at `/var/lib/bench/flake-rates/<sha>`, written by Dockerfile during image build. They are NOT part of git history. The agent cannot grep history to find the bad SHA.
- **Verifier sidecar isolation:** The verifier reads from the same sidecar to determine the expected SHA at test time. There is no committed file the agent can use to derive the answer.
- **Source-grep limitation:** The diagnosis line requires both keyword presence AND a mechanism description (off-by-one, `+1`, etc.). Pattern-matching on the source diff alone may pass keywords but cannot bypass the SHA check, which requires statistical measurement.
- **Decoy commits:** Five housekeeping commits modify `ledger.go` in ways that look similar to the buggy commit (variable rename, function reorder), so `git log -p ledger.go` does not point straight at the regression.
- **Generic commit messages:** All non-bootstrap commits use the same `chore: housekeeping pass N` template, so commit-message grep cannot identify the bad commit.
