# Fix ViewBinding leak in nested FragmentManager

You are fixing a mini Android-style FragmentManager for nested tab fragments that also tracks ViewBinding. The program reads `/app/scenario.txt` (one operation per line) and writes `/app/output.txt`. Some contract tests fail — read the contract and fix the implementation. Do not change output format.

## Model

Root containers (e.g. main) hold root fragments; child containers (e.g. homeTabs) hold child fragments nested under a parent. Nesting can be arbitrarily deep.

Each fragment has:
- parent (NONE for root)
- hidden (bool), detached (bool)
- lifecycle in {INITIALIZED, CREATED, VIEW_CREATED, STARTED, RESUMED}, maxLifecycle caps lifecycle to min(lifecycle, maxLifecycle)
- viewModel map (survives ROTATE; cleared on REMOVE and on parent REMOVE; retained when restored via POP of a REPLACE)
- savedState map (survives ROTATE and POP restore)
- binding map (simulates ViewBinding): created empty when fragment's view is created (ADD, ADD_CHILD, REPLACE, SHOW, ATTACH, POP restore, ROTATE replay all create a new empty binding if fragment becomes active), cleared when view is destroyed (HIDE, DETACH, REMOVE, REPLACE of old, ROTATE clears all live bindings before replay). Binding does NOT survive ROTATE — it is always empty after ROTATE replay, unlike viewModel and savedState which do survive.
- children set (direct child fragment names)

View destruction rules:
- HIDE: hidden=true; lifecycle -> min(STARTED, max); binding cleared for fragment and all descendants (propagate downgrade and binding clear)
- SHOW: hidden=false; lifecycle -> min(RESUMED, max, parentMax); if parent hidden or detached stay STARTED; binding recreated as empty for fragment and for children that are not hidden/detached (propagate upgrade + empty binding)
- DETACH: remove fragment and its children from containers; keep viewModel and savedState; detached=true, lifecycle=CREATED; binding cleared for fragment and children; remember lastContainer
- ATTACH: only if detached; re-add to lastContainer and children to theirs; detached=false; lifecycle = min(RESUMED or STARTED if hidden, max, parentMax); binding recreated empty for fragment and children
- REMOVE: remove fragment and all descendants from containers/registry; clear their viewModels, savedState, binding
- REPLACE: replace container contents, removing previous fragments and all descendants and clearing their viewModels, savedState, binding
- SET_MAX: cap own lifecycle and max, cascade to descendants capping their max to min(theirMax, parentMax) and lifecycle to min(lifecycle, newMax). Does NOT clear binding (view stays).
- ROTATE: clear live containers and registry (including binding for all live fragments); keep backstack; replay only backstacked entries in order. Recreated fragments retain pre-rotate viewModel and savedState, but binding is always empty after rotate (view recreated fresh). A fragment whose parent was never backstacked must not reappear, so child added under non-backstacked parent is dropped. Non-backstacked root fragments dropped.
- SAVE, VM_PUT, BIND_PUT are immediate writes to savedState, viewModel, binding respectively.

## Operations

- BEGIN txn
- ADD txn container fragment
- ADD_CHILD txn parent childContainer child
- REPLACE txn container fragment
- REMOVE txn fragment
- HIDE txn fragment
- SHOW txn fragment
- DETACH txn fragment
- ATTACH txn fragment
- SET_MAX txn fragment state
- SAVE fragment key value
- VM_PUT fragment key value
- BIND_PUT fragment key value
- ADD_TO_BACK_STACK txn name|NONE
- COMMIT txn
- POP name|NONE — NONE pops most recent; name pops down to and including most recent entry with that name (search from top last occurrence, case-sensitive); no-op if not found must not drain
- ROTATE
- QUERY — record snapshot

## Output format

One block per QUERY, separated by blank line. Each block:
- container lines sorted by container name; containers ever used printed even if empty: `container=main fragments=[Home]`
- fragment lines sorted by name: `fragment=Home parent=NONE hidden=false detached=false lifecycle=RESUMED maxLifecycle=RESUMED viewModel={} savedState={} binding={} children=[]` (parent NONE for root; bools lowercase; lifecycle values as above; viewModel, savedState, binding sorted by key as key=value; children sorted)
- final line `backstack=[entries comma-separated, anon for unnamed]`

## Where to start

- `/app/src/com/example/fragment/FragmentManager.kt`
- `/app/src/com/example/fragment/TransactionReplay.kt`
- `/app/src/com/example/fragment/BackStackEntry.kt`
- `/app/src/com/example/fragment/Container.kt`
- `/app/src/com/example/fragment/Fragment.kt`

Contract tests: `bash /app/src/run-contract.sh`. Build/run: `bash /app/src/run.sh` reads `/app/scenario.txt` writes `/app/output.txt`.

Make all contract tests pass. Focus on binding not leaking: it must be cleared on HIDE/DETACH/REMOVE/REPLACE and always empty after ROTATE, unlike viewModel. Child propagation must also clear/create binding.
