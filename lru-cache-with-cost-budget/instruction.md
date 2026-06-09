# Setting

Build a small C++ program that simulates a memory-budgeted cache. Entries have a `key`, `value`, and a numeric `cost`. Reads and writes affect recency, and the cache can be forced to evict entries until it fits a given cost budget.

# Input operations (stdin)

One command per line:

- `PUT <key> <value> <cost>` — store or update `<key>`. If the key already exists, replace its value and cost. This counts as an access and moves the entry to most-recently-used.
- `GET <key>` — if `<key>` exists, mark it most-recently-used. If it does not exist, do nothing.
- `EVICT_TO <budget>` — evict entries until total cost is at most `<budget>`.
- `TICK` — advance time by one step so subsequent accesses are clearly newer than prior ones (used for tie-breaking).

`<key>` and `<value>` are non-empty tokens; `<cost>` and `<budget>` are non-negative integers.

# Output (stdout)

At end of input, print the remaining entries in least-recently-used-first order — oldest access at the top, most-recently-used at the bottom — one per line, formatted as `<key> <value> <cost>`.

# Eviction rule

When `EVICT_TO` runs, evict in least-recently-used order. If multiple entries are in the same recency tier (touched without any `TICK` between them, or both untouched since the last `TICK`), break ties by evicting the higher-cost entry first.

# Budget rule

`EVICT_TO X` means the cache must end with total cost at most `X`. If it is already exactly `X`, nothing should be evicted.

# PUT overwrite rule

A `PUT` on an existing key is an update, not a second copy. After `PUT a v2 10`, there is exactly one `a` entry with value `v2` and cost `10`, and it is the most-recently-used.

# Build target

Compile your program to an executable at `/app/cache`. The grader runs `/app/cache`, feeds operations on stdin, and compares stdout to expected output.
