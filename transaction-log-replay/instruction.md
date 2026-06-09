# Setting

Build a small log-replay program for a transactional key/value store. Transactions stage writes privately, can mark intermediate points with savepoints, and can roll back partway without aborting the whole transaction. Separately, the system can take checkpoints that snapshot only what's committed globally at that moment.

# Input operations (stdin)

One command per line:

- `BEGIN <tx>` — start transaction `<tx>`.
- `WRITE <tx> <key> <val>` — set `<key>` to `<val>` inside `<tx>`'s private view.
- `SAVEPOINT <tx> <sp>` — record a named savepoint `<sp>` for `<tx>` at its current state. A transaction may have multiple savepoints.
- `ROLLBACK_TO <tx> <sp>` — undo everything `<tx>` wrote after savepoint `<sp>`. The transaction stays open and the savepoint still exists.
- `COMMIT <tx>` — make `<tx>`'s current writes globally visible and close it.
- `ABORT <tx>` — discard `<tx>` entirely and close it.
- `CHECKPOINT` — snapshot the current globally committed store as the latest checkpoint.

`<tx>`, `<key>`, `<val>`, and `<sp>` are non-empty tokens.

# Isolation and visibility

Each open transaction has its own view: it sees its own writes immediately, but it never sees another transaction's uncommitted writes. Only committed data is visible outside the transaction.

# Checkpoint behavior

A checkpoint captures the globally committed store exactly when `CHECKPOINT` runs. Later commits do not backfill into that earlier checkpoint.

# Semantics

Commands referencing an unknown or already-closed transaction are treated as no-ops. `ROLLBACK_TO <tx> <sp>` against a savepoint that does not exist for that transaction is also a no-op. A `BEGIN` against a transaction id that has previously been used (and closed) is a no-op.

# Output (stdout)

At end of input, print:

1. The final committed store as `<key>=<val>` lines, sorted by key ascending.
2. A literal line `CHECKPOINT:`.
3. The latest checkpoint store in the same format. If no checkpoint was ever taken, nothing follows the `CHECKPOINT:` line.

# Build target

Compile your solution to an executable at `/app/txlog`. The grader runs `/app/txlog`, feeds operations on stdin, and compares stdout to expected output.
