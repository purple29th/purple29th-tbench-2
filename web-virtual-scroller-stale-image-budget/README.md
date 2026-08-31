## Description

Web virtual scroller reuses a small pool of dom nodes while scrolling. Mounting a node sets its title and schedules an async image load that completes on a later tick. The buggy implementation does not track binding generations, so a load scheduled before unmount or rebind corrupts the node later, and when several loads land on same tick a superseded result overwrites the current image. It also has a decode budget that should accrue fractional credits and cap, but buggy version loses fractions and does not stop correctly. This task tests state_management and concurrency_bugs in web_frontend.

The naive approach of applying every resolved url without checking token, or clearing image on unmount incorrectly, fails contract tests for stale after unmount and stale after rebind. Budget tests fail if fractional accrual is ignored.

Inspired by android-recycler-staleness from accepted portfolio which had recyclerview cell pool with similar staleness and budget, but moved to web frontend with different operations MOUNT UNMOUNT PREFETCH UPDATE_TITLE and python simulation, not a replication.

## Completion Rates

- Oracle: 3/3 passed (local docker)
- Avocado: 2/5 passed
- Opus: 3/5 passed
- Codex: 2/5 passed
- Sonnet: 1/5 passed

## Model Analysis

- Avocado 2/5 passed - 3/5 failed on same tick superseded not overwriting and stale consumes resolution
- Opus 3/5 passed - 2/5 failed on budget fractional accrual and cap
- Codex 2/5 passed - 3/5 failed on equal generation overwrite and unbound image never produced
- Sonnet 1/5 passed - failed on all budget and staleness

Dominant failure modes: (1) stale token check missing 40 percent, (2) budget fractional carry and cap 30 percent, (3) equal generation handling and corrupted gen 30 percent. Failures reflect reasoning gaps about binding generations and budget state, not setup issues like missing deps.

## Anti-Cheating Analysis

- Hardcoded outputs: scenario.json is random per trial, output depends on operation order and resolutions, cannot hardcode
- Overfitting to visible tests: hidden tests in /app/tests vary ticks and items, not visible to agent
- Modifying test files: verifier runs pytest from /app/tests and checks reward.txt, test files are read only in container
- Bypassing intended path: must fix pool.py and scheduler.py token check and budget logic, cannot bypass by editing main.py alone
