I work on storefront product detail built with Jetpack Compose. Each variant screen is a composable that holds viewModel map that survives key changes but is cleared on unmount, remember map that caches expensive work and must be cleared on key change and on hide and on unmount and on rotate, saved map that survives hide and key change and rotate but not unmount, plus hidden flag. Parent variant change must drop remember cache for all child pickers recursively.

The app shows stale variant data because remember leaks after key change and after navigation pop, and child pickers keep old variant caches. Production OOMs have remember holding bitmaps for old variants.

Runner reads /app/scenario.txt one operation per line and writes snapshots to /app/output.txt at each QUERY. Buggy file is at /app/src/com/example/compose/ComposeManager.kt.

Operations, all transactional except VM_PUT REMEMBER_PUT SAVE ROTATE QUERY which are immediate:

BEGIN tid — start transaction tid
MOUNT tid id parent key — queue mount of id with parent or NONE and variant key. If id already exists ignore at commit. If parent not NONE and parent does not exist at commit time considering earlier mounts in same transaction, ignore. Create node with parent, key, empty viewModel remember saved, hidden false, add to parent children.
UPDATE_KEY tid id new_key — queue key change. At commit if node exists and new_key different, clear remember for node and all descendants recursively, set key to new_key. If same key do nothing. viewModel and saved must survive.
HIDE tid id — queue hide. At commit clear remember for node and all descendants and mark hidden true for them.
SHOW tid id — queue show. At commit for node and descendants set hidden false. Remember stays empty.
UNMOUNT tid id — queue unmount. At commit remove node and all descendants recursively, clearing viewModel remember saved, and removing from parent children if parent not also removed.
ADD_TO_BACKSTACK tid name — mark txn to push its before snapshot onto backstack with name on commit
COMMIT tid — apply queued ops in order, handling parent in same transaction, handling backstack push
POP name — if name NONE or empty pop last backstack entry and revert to its before snapshot. If name given find last entry with that name and revert to its before snapshot and drop entries from that index onwards. If no entry with name do nothing.
VM_PUT id k v — immediate put into viewModel if node exists
REMEMBER_PUT id k v — immediate put into remember if node exists
SAVE id k v — immediate put into saved if node exists, saved survives HIDE SHOW UPDATE_KEY ROTATE but not UNMOUNT POP
ROTATE — immediate, clear remember for all and set hidden false for all, retains viewModel and saved
QUERY — capture snapshot

Output for each QUERY block, blocks separated by blank line. Each block has one line per existing node sorted by id:

node=id parent=parentOrNONE key=key viewModel={sorted k=v comma} remember={sorted k=v comma} saved={sorted k=v comma} children=[sorted ids comma] hiddenFlag

hiddenFlag is space plus hidden if hidden else nothing. Parent NONE for root. viewModel remember saved sorted by key, empty {}, children sorted empty [].

Build and run:
bash /app/src/build.sh compiles Kotlin
bash /app/src/run.sh reads /app/scenario.txt writes /app/output.txt
bash /app/src/run-contract.sh runs small contract checks

Contract checks include mount, update clears remember but vm survives, child cascade, unmount clears descendants, same key no-op, remount fresh, deep nesting, hide show cascade, rotate clears remember keeps vm saved, parent in same txn where child mounted after parent succeeds and child before parent fails, backstack pop, save survives hide show and rotate.

Fix the leak so all scenarios pass. Do not change output format.
