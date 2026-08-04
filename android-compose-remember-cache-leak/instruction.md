I work on our Android storefront app's product detail screen built with Jetpack Compose. Each product variant screen is a composable that holds two kinds of state: viewModel map that should survive a variant key change but be cleared when the composable is unmounted, and remember map that caches expensive calculations and must be cleared both when key changes and when unmounted. When parent variant changes, all child variant pickers must drop their remember caches too.

The app is showing stale variant data because remember leaks after key change and after navigation pop. Production OOMs have remember holding bitmaps for old variants.

The runner reads /app/scenario.txt one operation per line and writes snapshots to /app/output.txt at each QUERY. Current implementation in /app/src/com/example/compose/ComposeManager.kt leaks remember on UPDATE_KEY and leaks children on UNMOUNT. Fix it so tests pass.

Operations you must handle, each line is space separated:

* MOUNT id parent key — mount composable id with parent id or NONE for root and variant key. If id already exists ignore. If parent is not NONE and parent does not exist ignore. Create node with parent, key, empty viewModel and empty remember, add id to parent children set if parent exists.
* UPDATE_KEY id new_key — if node exists and new_key is different from old key, clear remember for that node and for all its descendants recursively, set key to new_key, remember stays empty after. If same key do nothing. viewModel must not be cleared.
* VM_PUT id k v — if node exists put k=v into its viewModel map
* REMEMBER_PUT id k v — if node exists put k=v into its remember map
* UNMOUNT id — if node exists remove it and all its descendants recursively from registry, clearing both viewModel and remember and removing from parent children lists. If parent itself is also being removed, do not try to update its children again.
* QUERY — capture snapshot of current state

Output for each QUERY block, blocks in order, blank line between blocks. Each block contains one line per existing node sorted by id:

node=id parent=parentOrNONE key=key viewModel={sorted k=v comma} remember={sorted k=v comma} children=[sorted ids comma]

Parent NONE for root. viewModel and remember sorted by key as k=v comma separated, empty as {}. Children sorted comma, empty as [].

Where to start:
* /app/src/com/example/compose/ComposeManager.kt — main bug
* /app/src/com/example/compose/Node.kt
* /app/src/com/example/app/Main.kt

Build and run:
* bash /app/src/build.sh compiles Kotlin
* bash /app/src/run.sh reads /app/scenario.txt writes /app/output.txt
* bash /app/src/run-contract.sh runs small contract checks

All contract and hidden scenarios must pass. The leak of remember on key change and child cascade on UPDATE_KEY and UNMOUNT is the central difficulty. Do not change output format.

Thanks for fixing the leak.
