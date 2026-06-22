# Cost-budgeted cache

You're writing a little C++ program that acts like an in-memory cache with a twist: every entry carries a cost, some entries can be pinned so they stick around, and the cache slowly frees up room as time passes. It reads commands on stdin, one per line, runs them in order, and prints what's left at the end.

## Commands

- `PUT <key> <value> <cost>`: add the key, or if it's already there just update its value and cost (you never end up with two copies of a key). Either way it counts as using the entry, so it lands in the current time tier.
- `GET <key>`: if the key is present, mark it used (current tier). If it isn't, ignore the command.
- `PIN <key>`: protect an existing key from eviction. Pinning doesn't count as using the entry, so it leaves recency alone.
- `UNPIN <key>`: drop that protection. Also doesn't touch recency.
- `DECAY <num> <den>`: turn on passive headroom: from here on the cache reclaims `num` units of room every `den` ticks.
- `EVICT_TO <budget>`: shrink the cache until it fits the budget.
- `TICK`: bump the clock by one. Anything used after a tick is newer than anything used before it.

Keys and values are non-empty tokens. Costs, budgets, num, and den are non-negative integers. If a command names a key that isn't there, it does nothing.

## How recency works

Time moves in tiers, not per command. A `PUT` or `GET` stamps the entry with whatever tier is current; a `TICK` starts a new tier. So if you `PUT a` and then `PUT b` with no tick in between, they're equally recent, and `b` is not newer than `a`. Only a `TICK` actually separates things in time. Pinning and decay don't change an entry's tier.

## The order for eviction and output

Eviction and the final printout both walk entries the same way, oldest-used to newest-used:

- older tier first;
- if two entries share a tier, the more expensive one comes first;
- if they're also the same cost, go by key alphabetically.

## Budget, decay, and pins

Once `DECAY <num> <den>` is set, the cache builds up headroom as ticks go by, `num` per `den` ticks. Keep it as a running total and carry the leftover fraction, so don't recompute it each time and don't throw the remainder away every tick. The headroom you can actually use at any point is the whole-number part of what's piled up so far.

`EVICT_TO <X>` looks at the effective cost, which is the total cost of all entries minus that whole-unit headroom, and evicts in the order above until the effective cost is `X` or less. It's an at-most bound: if you're already at or under `X`, leave everything alone (even if you're exactly at `X`).

Pinned entries get skipped; they never get evicted. So if you've evicted everything that isn't pinned and the effective cost is still over `X`, just stop. You don't break a pin to hit the budget.

## Output

When the input ends, print the surviving entries in that same eviction order, one per line, as `<key> <value> <cost>`.

## Build

Build your program to `/app/cache`. The grader runs it, pipes the commands in on stdin, and checks stdout against the expected output.
