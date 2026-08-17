I own the Settings search flow on our Android flagship. We use fragments for every settings page and we let fragments talk to each other with the Fragment Result API so a child picker can send a result back to its parent without tight coupling. The picker sets a result, the parent has a result listener, and the result is delivered even if the listener was added after the result was set because we queue it. If the result handling is wrong we lose user choices and we get bug reports about settings not sticking.

I have a small Kotlin simulation of our FragmentManager that should do this. It reads a scenario file at /app/scenario.txt with one operation per line and writes snapshots to /app/output.txt at each QUERY. Right now some contract tests are failing and the manager misbehaves on rotate and named backstack pops. I need you to fix it.

The model: root containers like main hold fragments. Each fragment keeps resultListeners map (key -> registered), pendingResults map (key -> value queued when no listener yet), deliveredResults map (last delivered, for debugging). 

Result handling:
- SET_RESULT_LISTENER txn fragment key inside a transaction: register listener for key on that fragment. Ignore if fragment not in registry yet. If a pending result already exists for same key, deliver right away: move pending value to delivered, clear pending and listener (listener consumed).
- CLEAR_RESULT_LISTENER txn fragment key: clear listener.
- SET_RESULT txn targetFragment key value inside transaction: set result for target. If target currently has a listener for that key, deliver instantly (delivered[key]=value, remove listener and any pending for that key). If no listener, queue as pending[key]=value overwriting any previous pending for same key.
- REMOVE txn fragment: removes fragment from any container and deletes its listeners, pending, delivered, and all registration. If transaction is marked for backstack, capture its full state before removal so POP restores it with listeners pending delivered and container.

Backstack:
- ADD_TO_BACK_STACK txn name|NONE marks transaction as backstack entry, NONE means anon. COMMIT applies ops in order; if marked, push entry onto backstack capturing replaced fragments full child state (all result maps plus container) for REPLACE ops and removed fragment full state for REMOVE ops so POP can restore either.
- POP name|NONE: NONE pops most recent entry. POP with a name must pop down to and including the most recent entry with that name, searching from the top and using the last occurrence, not the first. Name search is case sensitive. If name not found on stack, POP is no-op and must not drain the whole stack, otherwise you lose user navigation history.
- ROTATE simulates config change: clear live containers and registry, keep backstack, replay only transactions that were added to backstack, in order. Fragments never part of a backstacked ADD or REPLACE must not reappear after rotate. Listeners and pending/delivered that were registered or set inside backstacked transactions must survive rotate because replay re-creates them; anything only from non-backstacked transactions is dropped.

Operations you will see in scenario.txt:
BEGIN txn, ADD txn container fragment, REPLACE txn container fragment, REMOVE txn fragment, SET_RESULT_LISTENER txn fragment key, CLEAR_RESULT_LISTENER txn fragment key, SET_RESULT txn targetFragment key value, ADD_TO_BACK_STACK txn name|NONE, COMMIT txn, POP name|NONE, ROTATE, QUERY.

Output format per QUERY, in order, blank line between blocks:
- container lines sorted by name, printed even if empty if ever used: container=main fragments=[Home]
- fragment lines sorted by name: fragment=Home listeners=[reqKey] pending={} delivered={key=val}
  listeners sorted, pending and delivered sorted as key=value comma
- final line backstack=[entries, anon for unnamed]

Example block:
container=main fragments=[Home, Profile]
fragment=Home listeners=[rk1] pending={} delivered={}
fragment=Profile listeners=[] pending={k=v} delivered={}
backstack=[home, anon]

Where to start:
- /app/src/com/example/fragment/FragmentManager.kt — this is where most bugs are
- /app/src/com/example/fragment/Transaction.kt
- /app/src/com/example/fragment/BackStackEntry.kt
- /app/src/com/example/fragment/Container.kt
- /app/src/com/example/fragment/Fragment.kt

Build: bash /app/src/build.sh uses kotlinc to compile. Run: bash /app/src/run.sh reads /app/scenario.txt writes /app/output.txt. Contract tests: bash /app/src/run-contract.sh runs ManagerContractKt with 5 smoke cases covering simple add, listener registration, result delivery, queuing, pending delivery later, pop missing is noop, and rotate drops non-backstacked (full 24-scenario coverage is in tests/expected).

Fix the manager so all contract tests pass. The logic for result queuing and named POP using last occurrence is the hard part. Do not change output format.

Thanks for fixing our Settings result flow — losing results is blocking release.
