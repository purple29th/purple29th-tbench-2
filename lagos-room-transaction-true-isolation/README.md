# lagos room transaction true isolation - Balogun market recycler staleness

## Description

I am Chinedu from Lagos Nigeria building market app for Balogun market traders. Each stall has a reusable cell in a list that shows stall photo that loads async. At one am we scroll fast to count inventory and see wrong photo: result fetched for stall the cell used to show writes through after cell recycled or rebound. When several results land on same tick a cell can show superseded image.

Project simulates RecyclerView-style list where small set of reusable cells are repeatedly bound to different items as you scroll. Binding updates visible fields immediately and schedules async image result that may arrive later tick. Bug shows cells display wrong image: result fetched for item cell used to show sometimes writes through after cell recycled or rebound, and when several results land on same tick a cell can end up showing value already superseded.

What works is generation tracking per cell plus budget for decode tokens that carries fractional remainder. Correct fix uses synchronized block, keeps generation map per cell, checks generation equals current before applying, but still consumes checkpoint token even for stale, plus first-write-wins on same tick.

Completion oracle three of three deterministic twenty three scenarios including simple_bind_resolve recycle_invalidates_pending rebind_same_item_invalidates_old budget_carry_decode stale_consumes_then_fresh tie_break. Avocado zero to one of five due to generation plus budget plus stale consume. Opus three of five GPT two of five.

Model Analysis failure modes: no generation tracking lets stale overwrite, no first-write-wins lets later stale overwrite valid on same tick, no stale consume causes resolution leak, no budget remainder loses fractional, no cap fails budget.

Anti cheating varied scenarios with BIND REFETCH BUDGET RECYCLE RESOLVE TICK QUERY with random temp names scenario.json so constant fails. Secure runner audit hook blocks tests.

Tags lagos recycler staleness Balogun market generation budget human story

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

No generation tracking fails recycle and rebind, no first-write-wins fails refetch_first_write_wins, no stale consume fails stale_steals_resolution, no budget remainder fails budget_carry_decode, no cap fails budget.

## Anti-Cheating

Varied scenarios BIND REFETCH BUDGET RECYCLE RESOLVE TICK QUERY random names so constant fails. Secure runner blocks tests.

## Tags

Tags lagos room transaction true isolation Balogun market recycler staleness human story

Author Tosin Daniel Jimoh purple29th at meta.com
