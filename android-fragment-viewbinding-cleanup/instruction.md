I work on the Android shopping app for our flagship store. We have a product listing with nested fragment tabs: main container shows Home, and Home has its own child container tabs with Tab1, Tab1 has Inner for product variants. Each product fragment holds a ViewBinding that wraps the view. Our prod crash reports show memory leaks because binding references are kept after the view is destroyed. I need a correct FragmentManager.

The app reads a scenario file at /app/scenario.txt, one operation per line, and writes the visible state to /app/output.txt at each QUERY. Right now contract tests are failing because binding is leaked and backstack pop misbehaves on rotation.

Model for this exercise:

Root containers like main hold root fragments. Child containers like homeTabs hold fragments nested under a parent. Parent can be deep.

Each fragment keeps:
- parent name or NONE if root
- hidden bool, detached bool
- lifecycle enum INITIALIZED, CREATED, VIEW_CREATED, STARTED, RESUMED and maxLifecycle that caps it to min(lifecycle, maxLifecycle)
- viewModel map: survives ROTATE and POP restore, cleared only on REMOVE and on parent REMOVE, retained when restored via POP after REPLACE, NOT cleared on HIDE/DETACH
- savedState map: survives ROTATE and POP restore
- binding map: this is the critical leak-prone one. It simulates ViewBinding. It is created as empty dict when fragment view is created: ADD, ADD_CHILD, REPLACE (new fragment), SHOW (view recreated), ATTACH (view recreated), POP restore (view recreated), ROTATE replay (view recreated empty). It is cleared when view destroyed: HIDE (view destroyed), DETACH (view destroyed), REMOVE (view destroyed plus cleared state), REPLACE (old fragments view destroyed), ROTATE (all live bindings cleared before replay). So after ROTATE, binding is always empty, unlike viewModel and savedState which survive if fragment was part of backstacked transaction.
- children set: direct child fragment names

Rules you must respect for binding and lifecycle:

- On ADD: container added to ever-used set, fragment parent NONE, hidden false, detached false, lifecycle RESUMED capped by max, lastContainer remembered, binding cleared to empty, added to container.
- On ADD_CHILD: child container added to ever-used, parent must exist and not detached otherwise ignore. Child parent set, hidden false, detached false, lifecycle RESUMED capped by max and by parent max and parent hidden (if parent hidden then child STARTED), binding cleared empty, parent children add child, lastContainer remembered, added to child container.
- On REPLACE container fragment: old fragments in that container plus all their descendants must be removed from containers and from registry, their viewModel, savedState, binding all cleared. Then new fragment added with empty binding like ADD. For backstacked REPLACE, we capture old fragments list per container and full state snapshots of each removed fragment (including viewModel, savedState, binding, children, parent, hidden, max, lastContainer) to allow restore on POP. On POP restore, binding must be empty (view recreated fresh), not restored with old values.
- On REMOVE fragment: remove fragment and all its descendants recursively from containers and registry, clearing viewModel, savedState, binding. Parent children list updated.
- On HIDE fragment: hidden true, lifecycle down to min(STARTED, max), binding cleared for fragment and for all descendants recursively (cascade downgrade and binding clear, max cap also applied to descendants)
- On SHOW fragment: hidden false, lifecycle up to min(RESUMED, max, parentMax) but if parent hidden or detached it stays STARTED, binding recreated as empty for fragment and for children that are not hidden/detached (propagate upgrade + empty binding)
- On DETACH fragment: remove fragment and its children from containers, keep viewModel and savedState (do not clear them), set detached true, lifecycle CREATED, binding cleared for fragment and children, remember lastContainer for each
- On ATTACH fragment: only if detached, re-add to lastContainer and children to theirs, detached false, lifecycle min(RESUMED or STARTED if hidden, max, parentMax) with parent hidden/detached check, binding recreated empty for fragment and children
- On SET_MAX fragment state: set maxLifecycle, cap own lifecycle to min(lifecycle, max), cascade to descendants capping their max to min(their max, parent max) and lifecycle to min(lifecycle, new max). Does NOT clear binding — view stays.
- On SAVE, VM_PUT, BIND_PUT: immediate writes to savedState, viewModel, binding. BIND_PUT writes to current live binding map.
- On ADD_TO_BACK_STACK txn name|NONE: NONE means anon. Marks transaction as backstack entry. COMMIT then records ops plus snapshot of replaced fragments (for REPLACE) and for REMOVE (so POP can restore). If transaction not marked, it is not preserved across ROTATE.
- On COMMIT txn: apply ops in order; if marked, push onto backstack with captured replaced state.
- On POP name|NONE: NONE pops most recent entry. Named POP must pop down to and including most recent entry whose name equals given name, searching from top using last occurrence, case-sensitive. If name not found, POP does nothing and must not drain entire stack.
- On ROTATE: simulate config change. Clear live containers and registry (so all live bindings gone), keep backstack list, then replay only backstacked transactions in order to rebuild live state using a replay that creates empty binding for each added fragment. Recreated fragments must retain pre-rotate viewModel and savedState that were saved before clear if they were part of backstacked fragments, but binding must stay empty. Also, a child fragment whose parent was never part of any backstacked ADD/REPLACE must not reappear after rotate (orphan drop). Non-backstacked root fragments also dropped.

Output: One block per QUERY, in order, blank line between blocks. Each block:
- container lines sorted by container name; containers ever used printed even if empty: container=main fragments=[Home]
- fragment lines sorted by name: fragment=Home parent=NONE hidden=false detached=false lifecycle=RESUMED maxLifecycle=RESUMED viewModel={} savedState={} binding={} children=[]
  parent NONE for root; bools lowercase; lifecycle/max one of INITIALIZED, CREATED, VIEW_CREATED, STARTED, RESUMED; viewModel, savedState, binding sorted by key as key=value comma; children sorted; viewModel cleared on REMOVE and on parent REMOVE, binding cleared on HIDE/DETACH/REMOVE/REPLACE/ROTATE
- final line backstack=[entries comma-separated, anon for unnamed]

Where to start:
- /app/src/com/example/fragment/FragmentManager.kt (main bug: ViewBinding leak)
- /app/src/com/example/fragment/TransactionReplay.kt
- /app/src/com/example/fragment/BackStackEntry.kt
- /app/src/com/example/fragment/Container.kt
- /app/src/com/example/fragment/Fragment.kt

Run contract: bash /app/src/run-contract.sh. Run app: bash /app/src/run.sh reads /app/scenario.txt writes /app/output.txt.

All contract tests must pass. The binding leak is the central difficulty — viewModel stays, binding must be gone on view destroy. Also named POP last occurrence and ROTATE orphan drop are tricky. Do not change output format.

Thanks for fixing leak — our prod is OOMing because of this.
