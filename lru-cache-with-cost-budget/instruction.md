# Setting

Build a small C++ program that simulates a memory-budgeted cache. Each entry has a `key`, a `value`, and a numeric `cost`. Reads and writes update how recently an entry was used, entries can be pinned so they survive eviction, the cache can passively reclaim headroom over time, and it can be told to evict until it fits within a cost budget.

# Input operations (stdin)

One command per line:

- `PUT <key> <value> <cost>` — store `<key>`, or update it if it already exists (replace value and cost; still a single entry). A `PUT` touches the entry, putting it in the current recency tier.
- `GET <key>` — if `<key>` exists, touch it (current recency tier). Otherwise do nothing.
- `PIN <key>` — if `<key>` exists, mark it pinned. Pinned entries are never evicted. Pinning is not an access; it does not change recency.
- `UNPIN <key>` — if `<key>` exists, clear its pinned mark. Also not an access.
- `DECAY <num> <den>` — enable passive headroom reclamation at a rate of `<num>` units per `<den>` ticks (see Budget).
- `EVICT_TO <budget>` — evict entries until the cache fits the budget (see Budget).
- `TICK` — advance time by one step. Everything touched after a `TICK` is strictly more recent than everything touched before it.

`<key>` and `<value>` are non-empty tokens; `<cost>`, `<budget>`, `<num>`, `<den>` are non-negative integers. A command naming a key that does not exist is a no-op.

# Recency tiers

Recency is tracked in tiers, not per-operation. Every `PUT` and `GET` stamps its entry with the current tier; `TICK` moves to a new tier. Two entries touched in the same tier (no `TICK` between them) are equally recent — a later `PUT` is **not** more recent than an earlier one unless a `TICK` separates them. `PIN`/`UNPIN`/`DECAY` never change an entry's tier.

# Eviction and output order

Both eviction and the final printout use the same ordering, from least-recently-used to most-recently-used:

1. Lower (older) recency tier first.
2. Within the same tier, higher `cost` first.
3. If cost also ties, by `key` ascending.

# Budget

The system can passively reclaim memory as time passes. Once `DECAY <num> <den>` has been set, the cache accumulates headroom continuously as ticks elapse, at `<num>` units per `<den>` ticks. This headroom is a single running quantity that carries its fractional part across ticks — it is not recomputed from scratch and the remainder is never dropped. At any moment the reclaimed headroom available is the whole-number part of what has accumulated so far.

`EVICT_TO <X>` compares the cache's **effective** cost — the total cost of all entries minus the currently reclaimed (whole-unit) headroom — against `<X>`, and evicts in the order above until the effective cost is at most `<X>`. It is an at-most bound: if the effective cost is already `<= X`, nothing is evicted. With no `DECAY` set, headroom is zero and effective cost equals total cost.

Pinned entries are skipped — they are never removed. If, after evicting every unpinned entry, the effective cost is still above `<X>`, eviction stops and the cache stays over budget.

# Output

At end of input, print the surviving entries in the eviction order above, one per line as `<key> <value> <cost>`.

# Build target

Compile your program to an executable at `/app/cache`. The grader runs `/app/cache`, feeds operations on stdin, and compares stdout to expected output.
