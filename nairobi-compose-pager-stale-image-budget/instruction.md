I am Wanjiku from Nairobi Kenya, I build fintech app for M-Pesa with Jetpack Compose. My team has horizontal pager showing loan cards with images that load from network that is slow in Kibera. Each pager page cell is reused like RecyclerView. Bug is when you swipe fast, image from old card shows on new card for a second, then correct image appears, but also budget for decoding gets wrong.

The pager logic we have: each bind updates title immediately and schedules async image fetch at current tick and we have budget accrual number of decode tokens per denominator ticks capped at cap with fractional carry. When fetch resolves we apply only if generation still matches current binding. Recycling or rebinding even to same item starts new generation, new fetch. Stale fetches that resolve after recycle must be discarded as image but still must consume one queued RESOLVE token from budget if it was scheduled, so they still cost decode budget.

There are twenty three scenarios in tests/expected like simple_bind_resolve, recycle_invalidates_pending, rebind_to_different_item, rebind_same_item_invalidates_old, new_fetch_after_rebind, two_cells_independent, auto_url_when_no_resolution, tick_processes_only_due, multiple_pending_resolve_in_order, rapid_recycle_and_rebind, interleaved_binds_across_cells, unbound_query_after_recycle, recycle_leak_gated, refetch_first_write_wins, stale_steals_resolution, stale_consumes_then_fresh, refetch_revalidates_after_apply, stale_consume_triple_interleave, tie_break_by_schedule_order, budget_carry_decode, budget_remainder_accumulates, budget_two_thirds, refetch_unbound_noop. Budget accrual tricky remainder accumulation two thirds.

Please make file at app/src/main/java/com/example/pager/PagerState.kt you fix. Current code has race where stale image overwrites new and budget remainder lost.

We have sample in environment/src not needed. Hidden evaluation uses contract tests in tests/expected plus run.sh that writes /app/output.txt via bash src/run.sh reading scenario.json.

File layout android compose pager no binary, Kotlin only. Must handle generation counters per cell and budget fractional carry capped.

If you get generation and budget right you pass all twenty three scenarios.

Coding rules Kotlin no blocking.

Author Tosin Daniel Jimoh purple29th at meta.com
