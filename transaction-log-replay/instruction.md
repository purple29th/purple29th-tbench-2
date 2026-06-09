# Setting

Implement a tiny in-memory transactional key/value store. Transactions buffer their writes privately; commits make those writes visible globally; aborts discard them. The log also includes `CHECKPOINT`, which snapshots the globally committed state at that moment.

# Input operations (stdin)

One command per line:

- `BEGIN <tx>` — open transaction `<tx>`.
- `WRITE <tx> <key> <val>` — record a write to `<key>` inside `<tx>`.
- `COMMIT <tx>` — apply `<tx>`'s writes to the committed store and close the transaction.
- `ABORT <tx>` — discard all of `<tx>`'s writes and close the transaction.
- `CHECKPOINT` — save a snapshot of the current committed store as the latest checkpoint.

`<tx>`, `<key>`, and `<val>` are non-empty tokens.

# Output (stdout)

At end of input, print:

1. The current committed state as `<key>=<val>` lines, sorted by key ascending.
2. A literal line `CHECKPOINT:`.
3. The latest checkpoint's state in the same format and ordering. If no checkpoint was ever taken, nothing follows the `CHECKPOINT:` line.

# Trap 1 — checkpoint atomicity

A checkpoint includes only transactions that were already committed at the moment `CHECKPOINT` ran. If a transaction is still open at checkpoint time and commits later, its writes show up in the final committed state but do not retroactively appear in that earlier checkpoint.

# Trap 2 — latest commit wins

If multiple committed transactions write the same key, the value from the most recent commit is the one that ends up in the committed store (and in any checkpoint taken after that commit).

# Trap 3 — abort is total

`ABORT` wipes out the transaction completely. None of its writes survive, even if it wrote the same key multiple times before aborting.

# Trap 4 — closed transactions are inert

After a transaction has committed or aborted, any later `WRITE`, `COMMIT`, or `ABORT` for that transaction is a silent no-op. It must not change state or crash.

# Build target

Compile your solution to an executable at `/app/txlog`. The grader runs `/app/txlog`, feeds operations on stdin, and compares stdout to expected output.
