# android-fragment-nested-child-retention

This task simulates an Android-style FragmentManager with nested child fragments, hide/show lifecycle handling, ViewModel retention across rotation, and back-stack restore of replaced child trees.

Fix the buggy implementation in `/app/src/com/example/fragment/FragmentManager.kt` and `TransactionReplay.kt` to pass all contract tests and the verifier scenarios.

Run `bash /app/src/run-contract.sh` to check contract tests.
Run `bash /app/src/run.sh` which reads `/app/scenario.txt` and writes `/app/output.txt`.
