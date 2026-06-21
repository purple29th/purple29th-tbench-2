# Setting

This project simulates a RecyclerView-style list where a small set of reusable cells are repeatedly bound to different items as you "scroll." Binding a cell updates its visible fields immediately and also schedules an asynchronous image result that may arrive on a later tick. In production we are seeing cells display the wrong image: a result fetched for an item the cell used to show sometimes writes through after the cell has already been recycled or rebound, and when several results land on the same tick a cell can end up showing a value that was already superseded. Some contract tests fail because the implementation does not consistently keep an outdated async result from changing a cell once its binding has moved on.

# Input operations (stdin)

The program reads one operation per line:

- `BIND <cell_id> <item_id> <title> <fetch_at_tick>` — attach the cell to the item, set its title immediately, and schedule an image fetch for that item due at `fetch_at_tick`.
- `REFETCH <cell_id> <fetch_at_tick>` — schedule another image fetch for the cell's current binding (e.g. a retry), due at `fetch_at_tick`. If the cell is unbound this does nothing.
- `BUDGET <num> <den> <cap>` — put the loader under a decode budget (see Expected behaviour). Without this op, decoding is unlimited.
- `RECYCLE <cell_id>` — detach the cell from any item (it becomes unbound).
- `RESOLVE <item_id> <image_url>` — provide a deterministic image URL for the next pending fetch of that `item_id`.
- `TICK <new_now>` — advance logical time to `new_now` and process pending fetches now due (`fetch_at_tick <= new_now`). When several are due, they resolve in scheduling order (then by `cell_id` to break ties).
- `QUERY <cell_id>` — record a snapshot of the cell's current state.

# Output format

At end of input, print one line per `QUERY`, in query order:

- Bound cell: `<cell_id> item=<item_id> title=<title> imageUrl=<url_or_NONE>`
- Unbound cell that holds no image: `<cell_id> unbound`
- Unbound cell that still holds an image: `<cell_id> unbound imageUrl=<url>` (this only happens if a stale result has corrupted a detached cell — correct behaviour never produces it)

# Expected behaviour

A cell must only ever display an image that was fetched for its *current* binding. Recycling a cell, rebinding it to a different item, or rebinding it to the *same* item again all start a new binding: any fetch scheduled under a previous binding must not write to the cell, even though it may still carry the same item id. When multiple fetches for one cell come due on the same tick, only the one belonging to the binding still in effect at the moment of writing may apply; once a cell has taken its image for the current binding, a later result from a superseded fetch on that same tick must not overwrite it. A recycled cell that no async result has touched is simply `unbound`. Pending fetches that come due are handled in scheduling order, and handling a fetch always consumes the next queued resolution for its item (or the deterministic `auto:<item_id>` fallback when none remain). This holds even when the fetch is stale: a result that arrives for a binding that has since changed is consumed and discarded, never put back, so a later valid fetch for the same item does not receive it.

When a `BUDGET` has been set, decoding an image costs one credit. The loader accrues decode credits continuously at `<num>/<den>` credits per tick of elapsed time — a single running quantity that carries its fractional part across ticks rather than being recomputed per tick — capped at `<cap>` credits. At a tick, after crediting the elapsed time, the due fetches are taken in the usual order and each valid (non-stale) fetch pays one credit to decode its image; when the next valid fetch in order cannot afford a credit, decoding stops for that tick and that fetch (and everything behind it) stays pending for a later tick. A stale fetch never decodes and costs nothing, but it still consumes its queued resolution. With no `BUDGET` op the budget is unlimited.

# Contract tests

The intended behaviour is captured by the contract tests in:

  /app/src/com/example/recycler/test/RecyclerContract.kt

Run them with:

  bash /app/src/run-contract.sh

Your goal is to make all contract tests pass.

# Build / run

Run the program with:

  bash /app/src/run.sh

It reads `/app/scenario.json` and writes `/app/output.txt` (the verifier checks that output).
