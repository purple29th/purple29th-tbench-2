# Setting

This repo is a small Kotlin project that simulates an Android-style fragment manager: you build up fragment transactions, optionally add transactions to a back stack, and the manager updates which fragments are currently visible in each container. Some contract tests are failing; your job is to fix the implementation so it matches the intended behavior.

# Input operations (stdin)

The program reads one operation per line:

- `BEGIN <txn_id>` — start recording a new transaction.
- `ADD <txn_id> <container> <fragment>` — add a fragment into a container as part of the transaction.
- `REPLACE <txn_id> <container> <fragment>` — replace the contents of a container with the given fragment.
- `REMOVE <txn_id> <fragment>` — remove a specific fragment as part of the transaction.
- `ADD_TO_BACK_STACK <txn_id> <name_or_NONE>` — mark the transaction as a back-stack entry (`NONE` means unnamed).
- `COMMIT <txn_id>` — apply the transaction; if marked, record it on the back stack.
- `POP <name_or_NONE>` — pop back-stack entries.
- `ROTATE` — simulate a configuration change by clearing live state and rebuilding from saved information.
- `QUERY` — record a snapshot of the current live state.

# Output format

At end of input, print one snapshot per `QUERY`, in the order they were issued.

  container=<name> fragments=[<frag1>, <frag2>, ...]

(one line per container, sorted by container name) followed by:

  backstack=[<entry1>, <entry2>, ...]

Use `anon` for unnamed back-stack entries.

# Pop semantics

`POP NONE` pops the most recent eligible entry. `POP <name>` pops down to and including the named entry. If the requested name is not on the back stack, `POP <name>` is a no-op.

# Rotation semantics

`ROTATE` clears the live container state, then rebuilds it from the saved back stack. Transactions that were not added to the back stack are not preserved across rotation.

# Contract tests

The expected behavior is captured by the contract tests:

  /app/src/com/example/fragment/test/ManagerContract.kt

Run them with:

  bash /app/src/run-contract.sh

Make all contract tests pass. Pay attention to test cases that exercise non-obvious interactions between named and unnamed back-stack entries.

# Build / run

Run the program with:

  bash /app/src/run.sh

Reads `/app/scenario.txt`, writes `/app/output.txt`.

# Where to start

- `/app/src/com/example/fragment/FragmentManager.kt`
- `/app/src/com/example/fragment/TransactionReplay.kt`
