# Fix the nested FragmentManager

You are fixing a mini Android-style FragmentManager for nested tab fragments.
The program reads `/app/scenario.txt` (one operation per line) and writes `/app/output.txt`.
Some contract tests fail — read the contract and fix the implementation. Do not change the output format.

## Model
Root containers (e.g. main) hold root fragments; child containers (e.g. homeTabs) hold child fragments nested under a parent. Nesting can be arbitrarily deep.
Each fragment has: parent (NONE for root), hidden (bool), detached (bool), lifecycle in {INITIALIZED, CREATED, VIEW_CREATED, STARTED, RESUMED}, maxLifecycle (caps lifecycle to min(lifecycle, maxLifecycle)), viewModel map (survives ROTATE; cleared on REMOVE and on parent REMOVE; retained when restored via POP of a REPLACE), savedState map (survives ROTATE and POP restore), children set.

## Operations
- BEGIN txn — start a transaction.
- ADD txn container fragment — add root fragment into container.
- ADD_CHILD txn parent childContainer child — add child under parent; ignore if parent missing or detached.
- REPLACE txn container fragment — replace container contents, removing previous fragments and all descendants and clearing their viewModels.
- REMOVE txn fragment — remove fragment and all descendants from containers/registry; clear their viewModels.
- HIDE txn fragment — hidden=true; lifecycle -> min(STARTED, max); propagate downgrade and max cap to all descendants.
- SHOW txn fragment — hidden=false; lifecycle -> min(RESUMED, max, parentMax); if parent hidden or detached stay STARTED; propagate upgrade to children that are not hidden or detached.
- DETACH txn fragment — remove fragment and its children from containers; keep state; detached=true, lifecycle=CREATED; remember lastContainer for each.
- ATTACH txn fragment — only if detached; re-add to lastContainer and children to theirs; lifecycle = min(hidden?STARTED:RESUMED, max, parentMax).
- SET_MAX txn fragment state — set maxLifecycle; cap own lifecycle; cascade to descendants capping their max to min(theirMax, parentMax) and lifecycle to min(lifecycle, newMax).
- SAVE fragment key value — immediate savedState write.
- VM_PUT fragment key value — immediate viewModel write.
- ADD_TO_BACK_STACK txn name|NONE — mark transaction as a backstack entry (NONE = anon).
- COMMIT txn — apply ops in order; if marked, record on backstack capturing replaced fragments full child subtree (all fields + container mapping + hidden/max/detached snapshots).
- POP name|NONE — NONE pops most recent; name pops down to and including the most recent entry with that name (search from top, case-sensitive); no-op if not found (must not drain). Restores replaced subtrees with captured state and container mapping.
- ROTATE — clear live containers and registry; keep backstack; replay only backstacked entries. Recreated fragments retain pre-rotate viewModel and savedState. A fragment whose parent was never backstacked must not reappear, so a child added under a non-backstacked parent is dropped on rotate. Non-backstacked root fragments are also dropped.
- QUERY — record a snapshot.

## Output format
One block per QUERY, in order, blocks separated by a blank line. Each block:
- container lines, sorted by container name; containers ever used are printed even if empty, e.g. `container=main fragments=[Home]`
- fragment lines, sorted by name, e.g. `fragment=Home parent=NONE hidden=false detached=false lifecycle=RESUMED maxLifecycle=RESUMED viewModel={} savedState={} children=[]`
  (parent NONE for root; bools lowercase; lifecycle and maxLifecycle one of INITIALIZED, CREATED, VIEW_CREATED, STARTED, RESUMED; viewModel and savedState sorted by key as key=value comma-separated; children sorted direct child names; when fragment is removed or popped its viewModel is cleared)
- final line `backstack=[<entries comma-separated, anon for unnamed>]`

## Where to start
- `/app/src/com/example/fragment/FragmentManager.kt`
- `/app/src/com/example/fragment/TransactionReplay.kt`
- `/app/src/com/example/fragment/BackStackEntry.kt`
- `/app/src/com/example/fragment/Container.kt`
- `/app/src/com/example/fragment/Fragment.kt`

Contract tests: `bash /app/src/run-contract.sh`. Build/run: `bash /app/src/run.sh` reads `/app/scenario.txt` writes `/app/output.txt`.
