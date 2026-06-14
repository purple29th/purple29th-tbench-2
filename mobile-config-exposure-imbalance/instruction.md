# Setting

This project simulates a RecyclerView-style list where a small set of reusable cells are repeatedly bound to different items as you "scroll." Binding a cell updates its visible fields immediately and also schedules an asynchronous image result that may arrive later. Some tests currently fail because the implementation doesn't consistently prevent outdated async results from changing a cell after the cell has moved on.

# Input operations (stdin)

The program reads one operation per line:

- `BIND <cell_id> <item_id> <title> <fetch_at_tick>` — attach the cell to the item, set the cell's title immediately, and schedule an image fetch for that item that becomes due at `fetch_at_tick`.
- `RECYCLE <cell_id>` — detach the cell from any item (it becomes unbound).
- `RESOLVE <item_id> <image_url>` — provide a deterministic image URL to use for the next pending fetch of that `item_id`.
- `TICK <new_now>` — advance logical time to `new_now` and process any pending fetches that are now due (`fetch_at_tick <= new_now`). When multiple fetches become due, they resolve in the order they were scheduled (then by `cell_id` to break ties).
- `QUERY <cell_id>` — record a snapshot request of the cell's current state.

# Output format

At end of input, print one line per `QUERY`, in the same order the queries appeared:

- If the cell is bound: `<cell_id> item=<item_id> title=<title> imageUrl=<url_or_NONE>`
- If the cell is unbound: `<cell_id> unbound`

# Contract tests

The intended behavior is captured by the contract tests in:

  /app/src/com/example/recycler/test/RecyclerContract.kt

Run them with:

  bash /app/src/run-contract.sh

Your goal is to make all contract tests pass.

# Build / run

Run the program with:

  bash /app/src/run.sh

It reads `/app/scenario.json` and writes `/app/output.txt` (the verifier checks that output).

# Where to start

The behavior bugs are in the recycler + scheduling logic. Start by reading and fixing:

- `/app/src/com/example/recycler/RecyclerPool.kt`
- `/app/src/com/example/recycler/FetchScheduler.kt`
