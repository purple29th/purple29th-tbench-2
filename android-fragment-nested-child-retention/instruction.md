# Setting

This repo is a small Kotlin project that simulates an Android-style fragment manager with **nested child fragments**. You have root containers (like `main`, `sidebar`) that host fragments. A fragment can itself host child fragments in its own child containers (e.g. fragment `Home` hosts `childA` in container `homeTabs`). On top of that, fragments have a `hidden` state, a lifecycle, a `viewModel` store that must survive configuration changes, and a `savedState` bundle.

Some contract tests are failing; your job is to fix the implementation so it matches the intended Android behavior.

# Input operations (stdin)

The program reads one operation per line from `/app/scenario.txt`:

- `BEGIN <txn_id>` — start recording a new transaction.
- `ADD <txn_id> <container> <fragment>` — add a root fragment into a container.
- `ADD_CHILD <txn_id> <parent_fragment> <child_container> <child_fragment>` — add a child fragment under a parent. Parent must already exist.
- `REPLACE <txn_id> <container> <fragment>` — replace the contents of a container with the given fragment.
- `REMOVE <txn_id> <fragment>` — remove a specific fragment and all its descendants, clearing their ViewModels.
- `HIDE <txn_id> <fragment>` — hide a fragment.
- `SHOW <txn_id> <fragment>` — show a hidden fragment.
- `SAVE <fragment> <key> <value>` — immediate: write into fragment's `savedState`.
- `VM_PUT <fragment> <key> <value>` — immediate: write into fragment's `viewModel`.
- `ADD_TO_BACK_STACK <txn_id> <name_or_NONE>` — mark transaction as back-stack entry (`NONE` = unnamed `anon`).
- `COMMIT <txn_id>` — apply transaction; if marked, record on back stack.
- `POP <name_or_NONE>` — pop back-stack entries.
- `ROTATE` — simulate configuration change.
- `QUERY` — record a snapshot.

# Output format

At end of input, print one block per `QUERY`, in order they were issued. Blocks are separated by a blank line.

Each block contains:

1. One line per container, sorted by container name. Containers that have ever been used are still printed even if they become empty after REMOVE or REPLACE, with `fragments=[]`:
```
container=<name> fragments=[<frag1>, <frag2>, ...]
```

2. One line per fragment currently alive, sorted by fragment name:
```
fragment=<name> parent=<parent_or_NONE> hidden=<true|false> lifecycle=<STATE> viewModel={k1=v1, k2=v2} savedState={k1=v1} children=[<child1>, <child2>]
```

- `parent` is `NONE` for root fragments
- `lifecycle` is one of `RESUMED`, `STARTED`, `CREATED` (hidden fragments must be at most `STARTED`, shown fragments `RESUMED` unless parent is hidden)
- `viewModel` and `savedState` maps are sorted by key, printed as `{k=v, ...}` or `{}` if empty
- `children` sorted list of direct child fragment names
- When a fragment is removed or popped, its ViewModel is cleared and it no longer appears

3. Final line:
```
backstack=[<entry1>, <entry2>, ...]
```
Use `anon` for unnamed entries.

# Pop semantics

- `POP NONE` pops the most recent entry.
- `POP <name>` pops down to and including the most recent entry with that name when searching from the top of the stack. If the requested name is not on the back stack, it is a no-op.
- Popping must restore replaced fragments along with their entire child subtrees and their savedState/viewModel/hidden state that was captured at commit time.
- Removing a parent fragment must recursively remove all descendants from all containers and from the fragment registry.

# Rotation semantics

- `ROTATE` clears live container state, then rebuilds it from the saved back stack only.
- Transactions that were not added to the back stack are not preserved across rotation.
- ViewModel and savedState for fragments that are recreated via back-stack replay must be retained.
- Child fragments whose parent was never back-stacked must not reappear.

# Contract tests

Expected behavior is captured by:

```
/app/src/com/example/fragment/test/ManagerContract.kt
```

Run them with:

```
bash /app/src/run-contract.sh
```

Make all contract tests pass.

# Build / run

Run the program with:

```
bash /app/src/run.sh
```

Reads `/app/scenario.txt`, writes `/app/output.txt`.

# Where to start

- `/app/src/com/example/fragment/FragmentManager.kt`
- `/app/src/com/example/fragment/TransactionReplay.kt`
- `/app/src/com/example/fragment/Container.kt`
- `/app/src/com/example/fragment/Fragment.kt`
- `/app/src/com/example/fragment/BackStackEntry.kt`
