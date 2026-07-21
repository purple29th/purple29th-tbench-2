Hey, quick one, we are replaying transaction logs for a small key value store where every transaction keeps its own view until it commits. Fix the txlog binary so it matches the behavior here. The verifier builds and runs it.

You get one operation per line from stdin. BEGIN opens a transaction, WRITE sets a key inside that transaction's private view, READ notes that the transaction looked at a key but returns nothing, SAVEPOINT marks the current point with a name and if it already exists moves it, ROLLBACK_TO undoes everything after that savepoint but keeps the transaction open and that savepoint survives while later savepoints are forgotten, COMMIT tries to publish writes to the global store and closes, ABORT throws it away, CHECKPOINT snapshots the currently committed store as latest.

Every open transaction works against its own view. It sees its own writes right away but never another transaction's uncommitted work, only committed data is visible outside.

We use optimistic first committer wins. When a transaction opens it takes an implicit snapshot of committed state at that moment. At commit time the store checks whether the data it relied on has moved — if some other transaction has committed over a key it wrote or read since it began, then its commit is rejected, none of its changes take effect, and it closes. ROLLBACK_TO shrinks the dependency set so anything after that point no longer counts. Only a successful commit advances committed state, a rejected commit changes nothing and does not count as a commit for others, and ABORT never causes a conflict.

Commands naming unknown or already closed transaction are no ops, as is ROLLBACK_TO to a savepoint that does not exist. Reusing a tx id that has already been closed is a no op.

At end of input print final committed store one key equals value line per key sorted by key ascending, then line CHECKPOINT colon, then latest checkpoint store same format, then line CONFLICTS colon, then ids of transactions whose commit was rejected for conflict, one per line in order those commits were attempted.

Compile your solution to an executable at /app/txlog. The grader runs /app/txlog, feeds operations on stdin, and compares stdout to expected output.
