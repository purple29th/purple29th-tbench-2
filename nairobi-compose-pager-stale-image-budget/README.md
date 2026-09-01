# nairobi compose pager stale image budget

## Description

I am Wanjiku from Nairobi Kenya I build fintech app for M-Pesa with Jetpack Compose horizontal pager showing loan cards. Each pager page has image that loads async. Binding updates title immediately and schedules image fetch at tick. Requirement cell only shows image fetched for current binding. Recycling or rebinding even to same item starts new binding. Stale fetches must be discarded but still consume queued RESOLVE token. Budget accrual num over den capped at cap with fractional carry.

I work on compose pager where cells reused. Bug is stale image shows for wrong card after fast swipe. Need to fix generation tracking and budget.

Please make file at app/src/main/java/com/example/pager/PagerState.kt you fix. There is sample in app/data not needed. Hidden evaluation uses contract tests in src/com/example/test with twenty three scenarios simple_bind_resolve recycle_invalidates_pending rebind_to_different_item etc. If generation tracking missing fails half.

File layout android. No binary. Must handle generation counters and budget remainder accumulation two thirds case.

If you get generation right you pass.

Coding rules Kotlin.

Files: app/src/main/java/com/example/pager/PagerState.kt you fix, environment/Dockerfile builds with gradle, tests/expected twenty three scenarios, test_outputs.py runs run.sh which writes /app/output.txt.

Completion Oracle three of three all scenarios pass, Avocado zero to one of five due to stale consumption plus budget carry decode, Opus four of five.

Model Analysis failure modes: no generation tracking shows stale image for wrong card, no discard still consumes token fails stale_steals_resolution, no budget carry loses fractional, no remainder accumulation fails budget_two_thirds, hardcoded.

Anti Cheating varied scenarios random order secure runner.

Tags nairobi compose pager stale image budget M-Pesa fintech halo not needed but generation tracking

Author Tosin Daniel Jimoh purple29th at meta.com


## Files

* /app/solve.py you write last token
* /app/data/scene sample
* Dockerfile
* solution/solve.py oracle
* tests/_gen.py generates
* test_outputs.py secure verifier random names

## Completion Rates

Oracle three of three deterministic
Avocado zero to one of five
Opus four of five GPT three of five

## Model Analysis

No background overcounts, fixed cutoff over and under, no speck keeps far dust, no shape keeps round, no halo under, hardcoded offset fails 96/128, hardcoded gain fails 22 percent.

## Anti-Cheating

Varied dims spacing amp bg sig noise seed random temp names so constant fails. Secure runner blocks tests.

## Tags

Tags nairobi compose pager stale image budget human story

Author Tosin Daniel Jimoh purple29th at meta.com
