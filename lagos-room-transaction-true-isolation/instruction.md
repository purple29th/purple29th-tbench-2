I am Chinedu from Lagos Nigeria, I build market app for Balogun market traders. Each stall has a small reusable cell in a list that shows stall photo that loads async. At one am we scroll fast to count inventory and we see wrong photo: a result fetched for a stall the cell used to show sometimes writes through after the cell has been recycled or rebound to another stall. When several results land on same tick a cell can show superseded image. Some contract tests fail.

This project simulates a RecyclerView-style list where a small set of reusable cells are repeatedly bound to different items as you scroll. Binding a cell updates its visible fields immediately and also schedules an asynchronous image result that may arrive on a later tick. The bug shows cells display wrong image: a result fetched for an item the cell used to show sometimes writes through after the cell has already been recycled or rebound, and when several results land on same tick a cell can end up showing a value that was already superseded.

Please fix `app/src/main/java/com/example/recycler/RecyclerPool.kt` and `FetchScheduler.kt`? Actually check `src/com/example/recycler/RecyclerPool.kt` and `FetchScheduler.kt` in environment. The reference solution is in solution/.

# Input operations (stdin)

The program reads one operation per line:

- `BIND <cell_id> <item_id> <title> <fetch_at_tick>` — attach the cell to the item, set its title immediately, and schedule an image fetch for that item due at `fetch_at_tick`.
- `REFETCH <cell_id> <fetch_at_tick>` — schedule another image fetch for the cell's current binding (retry), due at `fetch_at_tick`. If the cell is unbound this does nothing.
- `BUDGET <num> <den> <cap>` — put the loader under a decode budget. Without this op, decoding is unlimited.
- `RECYCLE <cell_id>` — detach the cell from any item (it becomes unbound).
- `RESOLVE <item_id> <image_url>` — provide a deterministic image URL for the next pending fetch of that `item_id`.
- `TICK <new_now>` — advance logical time to `new_now` and process pending fetches now due (`fetch_at_tick <= new_now`). When several are due, they resolve in scheduling order then by `cell_id`.
- `QUERY <cell_id>` — record snapshot of cell's current state.

# Output format

At end of input, print one line per QUERY, in query order:

- Bound cell: `<cell_id> item=<item_id> title=<title> imageUrl=<url_or_NONE>`
- Unbound cell that holds no image: `<cell_id> unbound`
- Unbound cell that still holds an image: `<cell_id> unbound imageUrl=<url>` (this only happens if stale result corrupted detached cell — correct behaviour never produces it)

# Expected behaviour

A cell must only ever display an image that was fetched for its current binding. Recycling a cell, rebinding it to a different item, or rebinding it to same item again all start a new binding: any fetch scheduled under previous binding must not write to the cell, even though it may still carry same item id. When multiple fetches for one cell come due on same tick, only the one belonging to binding still in effect at moment of writing may apply; once a cell has taken its image for current binding, later result from superseded fetch on same tick must not overwrite it. A recycled cell that no async result has touched is simply `unbound`. Pending fetches that come due are handled in scheduling order, and handling a fetch always consumes next queued resolution for its item (or deterministic `auto:<item_id>` fallback when none remain). This holds even when fetch is stale: result that arrives for binding that has since changed is consumed and discarded, never put back, so later valid fetch for same item does not receive it.

When BUDGET has been set, decoding an image costs one credit. Loader accrues decode credits continuously at `<num>/<den>` credits per tick of elapsed time — single running quantity that carries fractional part across ticks rather than recomputed per tick — capped at `<cap>` credits. At a tick, after crediting elapsed time, due fetches are taken in usual order and each valid non-stale fetch pays one credit to decode its image; when next valid fetch in order cannot afford credit, decoding stops for that tick and that fetch and everything behind it stays pending for later tick. Stale fetch never decodes and costs nothing, but still consumes its queued resolution. With no BUDGET op budget is unlimited.

# Lagos market story

Balogun market stalls have photos that load async from server. Traders scroll fast, cells recycled, stale photo must not overwrite new stall. Generation tracking per cell and WAL-like budget for decode tokens must be correct. Twenty three scenarios like simple_bind_resolve, recycle_invalidates_pending, rebind_same_item_invalidates_old, budget_carry_decode, stale_consumes_then_fresh.

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
