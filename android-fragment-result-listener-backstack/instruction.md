# Fix Fragment Result Listener Backstack

You are fixing a mini Android-style FragmentManager that supports the Fragment Result API. The program reads `/app/scenario.txt` (one operation per line) and writes `/app/output.txt`. Some contract tests fail — read the contract and fix the implementation. Do not change output format.

## Model

Root containers (e.g. main) hold root fragments. Each fragment has:
- container assignment (last container it was added to)
- resultListeners: map key -> true if a listener is registered for that key
- pendingResults: map key -> value queued when setResult happened but no listener existed yet
- deliveredResults: map key -> value of last delivered result (for snapshot visibility, cleared only on REMOVE)

Result semantics mirror AndroidX fragment result but simplified:

- `SET_RESULT_LISTENER txn fragment key` — inside transaction, register a listener for key on fragment. Ignore if fragment does not exist in registry (not yet added). If a pendingResult exists for same key, deliver immediately: move pendingResult value to deliveredResults, remove pendingResult and listener.
- `CLEAR_RESULT_LISTENER txn fragment key` — remove listener for key.
- `SET_RESULT txn targetFragment key value` — inside transaction, set a result for targetFragment. If target has a listener for that key, deliver immediately (deliveredResults[key]=value, remove listener and any pending for that key). If no listener, queue as pendingResults[key]=value (overwrite any previous pending for same key).
- `REMOVE txn fragment` — remove fragment from containers and registry, clear its resultListeners, pendingResults, deliveredResults.

Backstack and rotation:

- `ADD_TO_BACK_STACK txn name|NONE` — mark transaction as backstack entry (NONE=anon). Commit records ops plus snapshot of current containers and fragment result state (listeners/pending/delivered) for REPLACE ops.
- `COMMIT txn` — apply ops in order; if marked, push entry onto backStack. For REPLACE, capture previous container snapshot (fragments list) and for each replaced fragment, capture its full state (listeners/pending/delivered/container) to allow restore on POP.
- `POP name|NONE` — NONE pops most recent entry; `POP name` pops down to and including most recent entry with that name (search from top, case-sensitive, must use last occurrence, not first). If name not found, POP is no-op and must NOT drain entire stack. On pop, reverse entry ops and restore captured replaced state including listeners/pending/delivered.
- `ROTATE` — simulate config change: clear live containers and registry, keep backstack, replay only backstacked transactions in order to rebuild live state. Fragments that were never part of a backstacked ADD/REPLACE must NOT reappear. ResultListeners that were registered inside backstacked transactions must survive rotate (because replay re-registers them), and pending/delivered results that were part of backstacked state must also survive. Non-backstacked listeners/results are dropped.

## Operations

- BEGIN txn
- ADD txn container fragment
- REPLACE txn container fragment
- REMOVE txn fragment
- SET_RESULT_LISTENER txn fragment key
- CLEAR_RESULT_LISTENER txn fragment key
- SET_RESULT txn targetFragment key value
- ADD_TO_BACK_STACK txn name|NONE
- COMMIT txn
- POP name|NONE
- ROTATE
- QUERY — record snapshot

## Output format

One block per QUERY, in order, separated by blank line. Each block:

- container lines sorted by container name, e.g. `container=main fragments=[Home]`
- fragment lines sorted by name, e.g. `fragment=Home listeners=[requestKey] pending={} delivered={key=val} ` (listeners sorted, pending and delivered sorted by key as key=value comma-separated)
- final line `backstack=[entries comma-separated, anon for unnamed]`

Example block:
```
container=main fragments=[Home, Profile]
fragment=Home listeners=[rk1] pending={} delivered={}
fragment=Profile listeners=[] pending={k=v} delivered={}
backstack=[home, anon]
```

## Where to start

- `/app/src/com/example/fragment/FragmentManager.kt` — main buggy implementation
- `/app/src/com/example/fragment/Transaction.kt` — op definitions
- `/app/src/com/example/fragment/BackStackEntry.kt` — entry capture
- `/app/src/com/example/fragment/Container.kt`
- `/app/src/com/example/fragment/Fragment.kt`

Contract tests: `bash /app/src/run-contract.sh`. Build/run: `bash /app/src/run.sh` reads `/app/scenario.txt` writes `/app/output.txt`.

Make all contract tests pass. Pay attention to named POP using last occurrence, POP missing being no-op not draining, ROTATE retaining listeners/pending for backstacked fragments only, and queued result delivery when listener appears later.
