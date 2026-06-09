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
- Models that try to short-circuit by environment variables miss the rate-shift signal.
- Models that grep source can identify the buggy diff but cannot read the per-commit flake rates because those live in a root-only sidecar accessed only via a setuid helper.

## Anti-Cheating Analysis

- **Hidden ground truth:** Per-commit flake rates live at `/var/lib/bench/flake-rates/<sha>`. The directory is mode 700 owned by root; files are mode 600 owned by root. The agent runs as user `agent` (uid 1000) and cannot read these files directly.
- **Setuid helper:** `/usr/local/bin/flake-rate` is a small Go binary, setuid root, that takes a commit SHA and returns its rate. The Go test invokes the helper. The agent could also invoke it, but only by passing one SHA at a time and parsing scalar output — they still must enumerate commits, run the helper for each, and identify the first whose rate >= 0.5. That is equivalent to running the test, so this path is not a shortcut to the underlying statistical task.
- **Source-grep limitation:** The diagnosis line requires both keyword presence AND a mechanism description (off-by-one, `+1`, etc.). Pattern-matching on the source diff alone may pass keywords but cannot bypass the SHA check.
- **Decoy commits:** Several housekeeping commits modify `ledger.go` in ways that look similar to the buggy commit, so `git log -p ledger.go` does not point straight at the regression.
- **Generic commit messages:** All non-bootstrap commits use the same `chore: housekeeping pass N` template, so commit-message grep cannot identify the bad commit.
