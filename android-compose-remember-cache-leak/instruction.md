I work on our Android storefront app's product detail screen built with Jetpack Compose. Each product variant screen is a composable that holds two kinds of state: viewModel map that should survive a variant key change but be cleared when the composable is unmounted, and remember map that caches expensive calculations and must be cleared both when key changes and when unmounted. When parent variant changes, all child variant pickers must drop their remember caches too.

The app is showing stale variant data because remember leaks after key change and after navigation pop. Production OOMs have remember holding bitmaps for old variants.

The runner reads /app/scenario.txt one operation per line and writes snapshots to /app/output.txt at each QUERY. Current implementation in /app/src/com/example/compose/ComposeManager.kt leaks remember on UPDATE_KEY and leaks children on UNMOUNT. Fix it so tests pass.

I work on storefront product detail built with Jetpack Compose. Each variant screen is a composable that holds viewModel map that survives key changes but is cleared on unmount, remember map that caches expensive work and must be cleared on key change and on unmount and on hide, saved map that survives hide and key change and rotate, plus hidden flag. Parent variant change must drop remember for all child pickers too.

To make it production realistic we use transactions like FragmentManager. You BEGIN a txn, queue mounts and key updates and hide show and unmount, optionally ADD_TO_BACKSTACK with a name, then COMMIT which applies ops in order and if name given pushes snapshot before txn onto backstack. POP reverts. ROTATE simulates config change clearing remember for all and unhiding. This transaction plus cascade plus rotate makes the leak hard.

Runner reads /app/scenario.txt one op per line and writes snapshots to /app/output.txt at each QUERY. Buggy ComposeManager leaks remember on UPDATE_KEY and does not cascade to children and leaks children on UNMOUNT and fails parent in same txn and hide show and rotate.

Operations you must handle:

* BEGIN tid — start transaction tid
* MOUNT tid id parent key — queue mount of composable id with parent or NONE and variant key. If id already exists in nodes ignore at commit time. If parent not NONE and parent does not exist in nodes at commit time considering earlier mounts in same txn, ignore. Create node with parent, key, empty viewModel remember saved, hidden false, add id to parent children if parent exists.
* UPDATE_KEY tid id new_key — queue key change. At commit if node exists and new_key different, clear remember for that node and all descendants recursively, set key to new_key. If same key do nothing. viewModel saved must not be cleared.
* HIDE tid id — queue hide. At commit clear remember for node and all descendants and mark hidden true.
* SHOW tid id — queue show. At commit for node and descendants set hidden false
* UNMOUNT tid id — queue unmount. At commit remove node and all descendants recursively, clearing viewModel remember saved and removing from parent children lists. If parent itself also being removed do not update its children again.
* ADD_TO_BACKSTACK tid name — mark txn tid to push its before snapshot onto backstack with name on commit
* COMMIT tid — apply queued ops in order, handle parent in same txn, handle backstack push if name given
* POP name — if name NONE or empty pop last backstack entry and revert to its before snapshot. If name given find last entry with that name and revert to its before snapshot and drop entries from that index onwards. If no entry with name do nothing.
* VM_PUT id k v — immediate put into viewModel if node exists
* REMEMBER_PUT id k v — immediate put into remember if node exists
* SAVE id k v — immediate put into saved if node exists, saved survives hide show update rotate but not unmount pop
* ROTATE — immediate, clear remember for all existing nodes and set hidden false, retains viewModel saved
* QUERY — capture snapshot

Also old style without txn id is allowed for backward compat in some hidden files: MOUNT id parent key, UPDATE_KEY id new_key, HIDE id, SHOW id, UNMOUNT id — treat as immediate mount via auto txn begin commit as in Main.

Output for each QUERY block, blocks in order, blank line between blocks. Each block contains one line per existing node sorted by id:

node=id parent=parentOrNONE key=key viewModel={sorted k=v comma} remember={sorted k=v comma} saved={sorted k=v comma} children=[sorted ids comma] hiddenFlag

hiddenFlag is space plus word hidden if node hidden else nothing. Parent NONE for root. viewModel remember saved sorted by key k=v comma, empty {}. Children sorted comma empty [].

Where to start:
* /app/src/com/example/compose/ComposeManager.kt — main bug
* /app/src/com/example/compose/Node.kt
* /app/src/com/example/app/Main.kt

Build and run:
* bash /app/src/build.sh compiles Kotlin
* bash /app/src/run.sh reads /app/scenario.txt writes /app/output.txt
* bash /app/src/run-contract.sh runs contract checks

All contract and hidden scenarios must pass. The leak of remember on key change and child cascade plus hide show rotate plus parent in same txn and backstack pop is the central difficulty. Do not change output format.
