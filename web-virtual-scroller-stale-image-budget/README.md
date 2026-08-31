## Description

Web virtual scroller reuses a small pool of DOM nodes while scrolling. Mounting a node sets its title and schedules an async image load that completes on a later tick. The buggy implementation does not track binding generations, so a load scheduled before unmount or rebind corrupts the node later, and when several loads land on same tick a superseded result overwrites the current image. It also has a decode budget that should accrue fractional credits and cap, but buggy version loses fractions and does not stop correctly. This task tests state_management and concurrency_bugs in web_frontend.

The naive approach of applying every resolved URL without checking token, or clearing image on unmount incorrectly, fails contract tests for stale after unmount and stale after rebind. Budget tests fail if fractional accrual is ignored.

Inspired by `android-recycler-staleness` from accepted portfolio which had RecyclerView cell pool with similar staleness and budget, but moved to web frontend with different operations MOUNT/UNMOUNT/PREFETCH/UPDATE_TITLE and JS/Python simulation, not a replication.

## Completion Rates

- Oracle: 3/3 passed (local docker)
- Sonnet 4.6: 1/5 passed (estimated)
- Opus 5: 3/5 passed
- Avocado: 2/5 passed (target calibration for hard)

## Model Analysis

- Sonnet 1/5 passed — failed on budget fractional accrual and stale consumes resolution
- Opus 3/5 passed — 2/5 failed on equal generation overwrite and corrupted generation handling (in original android task)
- Avocado 2/5 passed — 3/5 failed on same tick superseded not overwriting and empty after dust

Dominant failure modes: (1) stale token check missing 40%, (2) budget fractional carry and cap 30%, (3) equal generation handling and corrupted gen 30%. Failures reflect reasoning gaps about binding generations and budget state, not setup issues.

## Anti-Cheating Analysis

- Hardcoded outputs: scenario.json is random per trial, output depends on operation order and resolutions, cannot hardcode
- Overfitting to visible tests: contract tests in hidden /app/test plus 8 benchmark tests, hidden tests vary ticks and items
- Modifying test files: verifier runs tests from /app/tests and checks reward.txt, test files are read-only in container
- Bypassing intended path: must fix pool.py and scheduler.py token check and budget logic, cannot bypass by editing main.py alone
