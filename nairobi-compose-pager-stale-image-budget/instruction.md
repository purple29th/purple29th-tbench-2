I am Wanjiku from Nairobi Kenya, I build fintech app for M-Pesa with Jetpack Compose. We have horizontal pager showing loan cards with images that load from network that is slow in Kibera. Each pager page is a reusable cell like RecyclerView. At one am we swipe fast and image from old card shows on new card for a second, then correct image appears, but also budget for decoding gets wrong and next card stays blank. Some contract tests fail.

This project simulates a RecyclerView-style list where a small set of reusable cells are repeatedly bound to different items as you scroll. Binding a cell updates its visible fields immediately and also schedules an asynchronous image result that may arrive on a later tick. Bug is cells display wrong image: a result fetched for an item the cell used to show sometimes writes through after the cell has already been recycled or rebound, and when several results land on same tick a cell can end up showing a value that was already superseded.

Please fix `app/src/main/java/com/example/recycler/RecyclerPool.kt` and `FetchScheduler.kt` in environment. Reference solution is in solution/.

# Input operations (stdin)

The program reads one operation per line:

- `BIND <cell_id> <item_id> <title> <fetch_at_tick>` — attach the cell to the item, set its title immediately, and schedule an image fetch for that item due at `fetch_at_tick`.
- `REFETCH <cell_id> <fetch_at_tick>` — schedule another image fetch for the cell's current binding (retry), due at `fetch_at_tick`. If unbound does nothing.
- `BUDGET <num> <den> <cap>` — put loader under decode budget. Without this, decoding unlimited.
- `RECYCLE <cell_id>` — detach cell from any item (becomes unbound).
- `RESOLVE <item_id> <image_url>` — provide deterministic image URL for next pending fetch of that item.
- `TICK <new_now>` — advance logical time to `new_now` and process pending fetches due (`fetch_at_tick <= new_now`). When several due, resolve in scheduling order then by cell_id.
- `QUERY <cell_id>` — record snapshot of cell's current state.

# Output format

At end, print one line per QUERY, in query order:

- Bound cell: `<cell_id> item=<item_id> title=<title> imageUrl=<url_or_NONE>`
- Unbound cell no image: `<cell_id> unbound`
- Unbound cell still holds image: `<cell_id> unbound imageUrl=<url>` (only happens if stale corrupted detached cell — correct never produces it)

# Expected behaviour

A cell must only ever display image fetched for its current binding. Recycling, rebinding to different item, or rebinding to same item again all start new binding: any fetch scheduled under previous binding must not write to cell, even if same item id. When multiple fetches for one cell come due on same tick, only one belonging to binding still in effect at moment of writing may apply; once cell has taken image for current binding, later result from superseded fetch on same tick must not overwrite it. Recycled cell with no async result touched is simply `unbound`. Pending fetches that come due are handled in scheduling order, and handling a fetch always consumes next queued resolution for its item (or deterministic `auto:<item_id>` fallback when none remain). This holds even when fetch is stale: result that arrives for binding that has since changed is consumed and discarded, never put back.

When BUDGET set, decoding an image costs one credit. Loader accrues decode credits continuously at `<num>/<den>` credits per tick of elapsed time — single running quantity that carries fractional part across ticks rather than recomputed per tick — capped at `<cap>` credits. At a tick, after crediting elapsed time, due fetches are taken in usual order and each valid non-stale fetch pays one credit to decode; when next valid fetch cannot afford credit, decoding stops for that tick and that fetch and everything behind stays pending for later tick. Stale fetch never decodes and costs nothing, but still consumes its queued resolution. With no BUDGET, budget unlimited.

# Nairobi market story

M-Pesa loan cards have photos that load async. Users swipe fast in low network, cells recycled, stale photo must not overwrite new card, and budget must carry fractional remainder, cap respected. Twenty three scenarios like simple_bind_resolve, recycle_invalidates_pending, rebind_same_item_invalidates_old, budget_carry_decode, stale_consumes_then_fresh, budget_two_thirds.

# Contract tests

Intended behaviour is captured by contract tests in:

  /app/src/com/example/recycler/test/RecyclerContract.kt

Run them with:

  bash /app/src/run-contract.sh

Your goal is to make all contract tests pass.

# Build / run

Run program with:

  bash /app/src/run.sh

It reads `/app/scenario.json` and writes `/app/output.txt` (verifier checks that output).

Author Tosin Daniel Jimoh purple29th at meta.com
