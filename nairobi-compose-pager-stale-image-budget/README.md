# nairobi compose pager stale image budget - M-Pesa loan cards recycler staleness

## Description

I am Wanjiku from Nairobi Kenya building fintech app for M-Pesa with Jetpack Compose horizontal pager showing loan cards. Each card has image that loads async over slow network in Kibera. At one am we swipe fast and wrong image shows: result fetched for card cell used to show writes through after cell recycled or rebound, and budget for decoding gets wrong and next card stays blank.

Project simulates RecyclerView-style list where small set of reusable cells are repeatedly bound to different items as you scroll. Binding updates visible fields immediately and schedules async image result that may arrive later tick. Bug shows cells display wrong image and budget loses fractional remainder.

What works is generation tracking per cell plus budget for decode tokens that carries fractional remainder in units of denominator. Correct fix uses capUnits = cap*den, budgetUnits that accrues dt*num and capped, checks budgetUnits < den to gate valid fetches, and afterImageApplied bumps token to enforce first-write-wins on same tick, plus stale still consumes queued resolution.

Completion oracle three of three deterministic twenty three scenarios including simple_bind_resolve recycle_invalidates_pending rebind_same_item_invalidates_old budget_carry_decode stale_consumes_then_fresh tie_break budget_two_thirds. Avocado zero to one of five due to generation plus budget plus stale consume. Opus three of five GPT two of five.

Model Analysis failure modes: no generation tracking lets stale overwrite, no first-write-wins lets later stale overwrite valid on same tick, no stale consume causes resolution leak, no budget remainder loses fractional two_thirds, no cap fails budget.

Anti cheating varied scenarios with BIND REFETCH BUDGET RECYCLE RESOLVE TICK QUERY with random temp names scenario.json so constant fails. Secure runner blocks tests.

Tags nairobi compose pager recycler staleness M-Pesa budget generation human story

Author Tosin Daniel Jimoh purple29th at meta.com


## Files

* /app/src/com/example/recycler/RecyclerPool.kt you fix
* /app/src/com/example/recycler/FetchScheduler.kt you fix
* /app/src/run.sh reads scenario.json writes output.txt
* /app/src/run-contract.sh runs contract tests
* Dockerfile eclipse-temurin:17 kotlin 1.9.22
* solution/ correct FetchScheduler and RecyclerPool
* tests/expected twenty three scenarios
* test_outputs.py secure verifier

## Completion Rates

Oracle three of three deterministic
Avocado zero to one of five
Opus three of five GPT two of five

## Model Analysis

No generation tracking fails recycle and rebind, no first-write-wins fails refetch_first_write_wins, no stale consume fails stale_steals_resolution, no budget remainder fails budget_carry_decode and budget_two_thirds, no cap fails budget.

## Anti-Cheating

Varied scenarios BIND REFETCH BUDGET RECYCLE RESOLVE TICK QUERY random names so constant fails. Secure runner blocks tests.

## Tags

Tags nairobi compose pager stale image budget human story

Author Tosin Daniel Jimoh purple29th at meta.com
