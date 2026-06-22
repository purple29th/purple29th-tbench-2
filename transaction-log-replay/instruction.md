# Setting

You're writing the replay engine for a small transactional key/value store. People run transactions against it concurrently, so the interesting part isn't the happy path — it's what happens when two open transactions touch the same key, when a transaction walks itself back to an earlier savepoint, and when someone snapshots the committed state midway through.

A transaction keeps its edits private until it commits. It can drop savepoints as it goes and later roll back to one without giving up the whole transaction. And at any point the system can take a checkpoint, freezing whatever is committed globally right then.

# Input operations (stdin)

One command per line:

- `BEGIN <tx>` — open transaction `<tx>`.
- `WRITE <tx> <key> <val>` — inside `<tx>`'s private view, set `<key>` to `<val>`.
- `READ <tx> <key>` — note that `<tx>` looked at `<key>`. It returns nothing and changes no value; it just records what the transaction relied on while it was open.
- `SAVEPOINT <tx> <sp>` — mark the transaction's current point as savepoint `<sp>`. If `<sp>` already exists for this transaction, move it to the current point.
- `ROLLBACK_TO <tx> <sp>` — undo everything `<tx>` wrote after savepoint `<sp>`, but keep the transaction open. `<sp>` itself survives; any savepoints made after it are discarded.
- `COMMIT <tx>` — try to publish `<tx>`'s writes to the global store and close it (see Conflicts).
- `ABORT <tx>` — throw `<tx>` away and close it.
- `CHECKPOINT` — snapshot the currently committed store as the latest checkpoint.

`<tx>`, `<key>`, `<val>`, and `<sp>` are non-empty tokens.

# Isolation

Every open transaction works against its own view. It sees its own writes right away but never another transaction's uncommitted work — only committed data is visible from the outside.

# Conflicts

The store uses optimistic concurrency with first-committer-wins. When a transaction opens, it takes an implicit snapshot of the committed state at that moment, and works against that snapshot for as long as it stays open. At commit time the store checks whether the transaction is still consistent with what it relied on: if the data it depended on has moved on under it — some other transaction has committed over it since this one began — then this transaction has lost the race, and its commit is rejected, none of its changes take effect, and it closes. The transaction that got there first keeps its result. A `ROLLBACK_TO` rewinds the transaction's state to the savepoint, so anything it did after that point no longer counts toward this check. Only a successful commit advances the committed state; a rejected commit changes nothing and doesn't count as a commit for anyone else, and a plain `ABORT` never causes a conflict for another transaction.

# Checkpoints

A checkpoint captures the committed store exactly when `CHECKPOINT` runs; later commits don't backfill into it.

# Other rules

Commands naming an unknown or already-closed transaction are no-ops, as is `ROLLBACK_TO` to a savepoint that doesn't exist for that transaction. Reusing a `<tx>` id that has already been closed is a no-op.

# Output (stdout)

At end of input, print, in order:

1. The final committed store, one `<key>=<val>` line per key, sorted by key ascending.
2. A line `CHECKPOINT:`.
3. The latest checkpoint store, same format (nothing here if no checkpoint was taken).
4. A line `CONFLICTS:`.
5. The ids of transactions whose commit was rejected for a conflict, one per line, in the order those commits were attempted (nothing here if there were none).

# Build target

Compile your solution to an executable at `/app/txlog`. The grader runs `/app/txlog`, feeds operations on stdin, and compares stdout to the expected output.
