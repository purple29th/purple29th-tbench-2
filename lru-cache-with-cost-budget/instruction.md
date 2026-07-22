You are writing a little C++ program that acts like an in memory cache with a twist, every entry has a value and a cost, some entries can be pinned so they stick around, and the cache slowly frees up room as time ticks. It reads commands on stdin one per line and prints what is left at the end.

Add key value cost, or update value and cost if key already exists, either way it counts as using the entry so it lands in the current time tier. If key is present, GET marks it used, otherwise ignore. PIN protects a key from eviction and does not count as use, UNPIN drops that protection and also does not touch recency. DECAY sets passive headroom, from here on the cache reclaims num units every den ticks. EVICT_TO shrinks until it fits the budget. TICK bumps the clock by one. Commands on unknown keys do nothing.

Time moves in tiers not per command. PUT or GET stamps entry with current tier, TICK starts new tier, so two PUTs with no TICK between are equally recent. Only TICK separates things in time. Pinning and decay do not change tier.

Eviction and final print walk entries oldest to newest: older tier first, if same tier more expensive first, if same cost key alphabetical. Once DECAY is set, headroom builds as ticks go by, keep running total and leftover fraction. Effective cost is total cost minus whole unit headroom. EVICT_TO evicts in order above until effective cost is at most budget. Pinned entries are never evicted, if still over after evicting all unpinned, stop. When input ends print survivors in that same order one per line as key value cost.

Build your program to app cache. The grader runs it with stdin and checks stdout.
