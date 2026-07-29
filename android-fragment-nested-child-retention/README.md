# android-fragment-nested-child-retention

This task simulates an Android-style FragmentManager with nested child fragments, hide/show lifecycle, ViewModel retention across rotation, and back-stack restore of replaced child trees.

Fix the buggy implementation in `/app/src/com/example/fragment/FragmentManager.kt` and `TransactionReplay.kt` to pass all contract tests.

Key bugs to fix (mirroring real Android fragment pitfalls):

- `POP <name>` must use `indexOfLast` (most recent) and be a no-op when name missing (must NOT drain stack)
- `REPLACE` must capture displaced fragment's child subtree for restore
- `REMOVE` parent must recursively remove descendants
- `ADD_CHILD` must validate parent exists
- `HIDE` must downgrade lifecycle to STARTED, `SHOW` to RESUMED, and propagate to children
- `ROTATE` must retain viewModel/savedState and child hierarchy, replaying only back-stacked entries

Run `bash /app/src/run-contract.sh` to check contract tests.
Run `bash /app/src/run.sh` which reads `/app/scenario.txt` and writes `/app/output.txt`.
