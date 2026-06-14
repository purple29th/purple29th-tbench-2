# Setting

This repo is a small Kotlin project that simulates an Android-style fragment manager: you build up fragment transactions, optionally add transactions to a back stack, and the manager updates which fragments are currently visible in each container. Some contract tests are failing; your job is to fix the implementation so it matches the intended behavior.

# Input operations (stdin)

The program reads one operation per line:

- `BEGIN <txn_id>` — start recording a new transaction.
- `ADD <txn_id> <container> <fragment>` — add a fragment into a container as part of the transaction.
- `REPLACE <txn_id> <container> <fragment>` — replace the contents of a container with the given fragment as part of the transaction.
- `REMOVE <txn_id> <fragment>` — remove a specific fragment as part of the transaction.
- `ADD_TO_BACK_STACK <txn_id> <name_or_NONE>` — mark the transaction as a back-stack entry (optionally named; `NONE` means unnamed).
- `COMMIT <txn_id>` — apply the transaction to the live state; if it was marked for the back stack, record it there.
- `POP <name_or_NONE>` — request to pop back-stack entries (either the latest entry, or based on a provided name).
- `ROTATE` — simulate a configuration change by clearing the current live state and rebuilding it from saved information.
- `QUERY` — record a snapshot of the current live state for output.

# Output format

At end of input, print one snapshot per `QUERY`, in the same order the queries were issued.

Each snapshot prints containers (sorted by container name) as:

  container=<name> fragments=[<frag1>, <frag2>, ...]

Then print the current back stack as:

  backstack=[<entry1>, <entry2>, ...]

Use `anon` for unnamed back-stack entries. Print a blank line after each snapshot.

# Contract tests

The expected behavior is captured by the contract tests:

  /app/src/com/example/fragment/test/ManagerContract.kt

Run them with:

  bash /app/src/run-contract.sh

Your goal is to make all contract tests pass.

# Build / run

Run the program with:

  bash /app/src/run.sh

It reads `/app/scenario.txt` and writes `/app/output.txt` (the verifier checks this output).

# Where to start

The bugs are in the fragment manager and transaction replay logic. Start here:

- `/app/src/com/example/fragment/FragmentManager.kt`
- `/app/src/com/example/fragment/TransactionReplay.kt`
