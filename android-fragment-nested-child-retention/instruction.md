# Setting

This repo is a small Kotlin project that simulates AndroidX-style fragments but with nested children: root containers like `main` hold fragments, a fragment can host child fragments in child containers like `Home` -> `homeTabs` -> `Tab1`, and so on. Each fragment has hidden, lifecycle (RESUMED/STARTED), a viewModel map that survives rotation, and a savedState map. Some contract tests are failing; fix the implementation so it matches the intended behavior. Leave the app Main and parser alone, fix only the fragment package.

# Input operations (stdin)

Driver reads `/app/scenario.txt` one operation per line:

- `BEGIN <txn_id>` start a transaction
- `ADD <txn_id> <container> <fragment>` add root fragment
- `ADD_CHILD <txn_id> <parent_fragment> <child_container> <child_fragment>` add child under parent, parent must exist else ignore
- `REPLACE <txn_id> <container> <fragment>` replace container contents
- `REMOVE <txn_id> <fragment>` remove fragment and all its descendants, clear their ViewModels
- `HIDE <txn_id> <fragment>` hide, downgrades to STARTED and propagates to children
- `SHOW <txn_id> <fragment>` show, upgrades to RESUMED unless parent is hidden
- `SAVE <fragment> <key> <value>` immediate savedState write, survives rotation and pop restore
- `VM_PUT <fragment> <key> <value>` immediate viewModel write, survives ROTATE, cleared on REMOVE and when fragment is popped off (re-adding later must be empty), retained when restored via pop of a REPLACE
- `ADD_TO_BACK_STACK <txn_id> <name_or_NONE>` mark, NONE = anon
- `COMMIT <txn_id>` apply; if marked record on back stack capturing replaced fragments with full child subtree, hidden state, viewModel/savedState, and container mapping
- `POP <name_or_NONE>` pop entries
- `ROTATE` simulate config change, clear live containers and fragment registry, snapshot current back stack and replay it via TransactionReplay. Non-backstacked transactions are lost. ViewModel/savedState for recreated fragments must be retained from pre-rotate stores. Child whose parent was never backstacked must not reappear.
- `QUERY` snapshot

# Output format

At end print one block per QUERY in order, blocks separated by blank line.

1. container lines sorted by name, containers ever used are still printed even if empty after REMOVE/REPLACE:
```
container=<name> fragments=[frag1, frag2]
```

2. fragment lines sorted by name:
```
fragment=<name> parent=<parent_or_NONE> hidden=<true|false> lifecycle=<STATE> viewModel={k=v} savedState={k=v} children=[c1, c2]
```
- parent NONE for root
- lifecycle RESUMED if shown and parent not hidden, else STARTED, hidden fragments at most STARTED
- viewModel/savedState sorted by key, {} when empty, cleared on remove/parent remove (re-add must be empty)
- children sorted direct child names

3. `backstack=[e1, e2]` anon for unnamed, order committed.

# Pop semantics

POP NONE pops most recent. POP <name> pops down to and including most recent entry with that name searching from top, case-sensitive. If name not found it is a no-op, must not drain stack. Popping restores replaced fragments with entire child subtree and their captured viewModel/savedState/hidden/container mapping.

# Contract tests

Expected behavior is in:

```
/app/src/com/example/fragment/test/ManagerContract.kt
```

Run:

```
bash /app/src/run-contract.sh
```

Make all pass.

# Build / run

```
bash /app/src/run.sh
```
Reads `/app/scenario.txt`, writes `/app/output.txt`.

# Where to start

- `/app/src/com/example/fragment/FragmentManager.kt`
- `/app/src/com/example/fragment/TransactionReplay.kt`
- `/app/src/com/example/fragment/BackStackEntry.kt`
