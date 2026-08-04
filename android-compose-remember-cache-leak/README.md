# android-compose-remember-cache-leak

I own storefront product detail built with Compose. Each variant screen has viewModel that survives key change but cleared on unmount, remember cache that must be cleared on key change and on hide and on unmount and on rotate, saved map that survives hide key change rotate but not unmount, plus hidden flag. Parent key change must drop remember for all child pickers.

This version is made edgy like fragment viewbinding family to avoid too easy 5/5 pass. It adds transactions with BEGIN ADD_TO_BACKSTACK COMMIT POP, plus HIDE SHOW cascade, ROTATE that clears remember and unhides, SAVE, plus parent in same txn edge case where child mount should succeed if parent mounted earlier in same txn. Those combined make avocado 5/5 fail and require precise stateful reasoning.

Previously buggy baseline failed 9/12 but all models passed 5/5 because logic was too simple. New buggy fails more subtly: only clears self remember on UPDATE_KEY not descendants, only hides self on HIDE, only removes self on UNMOUNT not descendants, does not unhide on rotate, does not handle parent in same txn? Actually mount check now includes same txn earlier mounts so parent in same txn passes, but other leaks remain.

Why hard:

* remember vs viewModel vs saved lifetimes: viewModel survives UPDATE_KEY HIDE SHOW ROTATE but cleared on UNMOUNT POP, remember cleared on UPDATE_KEY HIDE UNMOUNT ROTATE always empty after key change, hidden flag set on HIDE cleared on SHOW and ROTATE, saved survives HIDE SHOW UPDATE_KEY ROTATE but cleared on UNMOUNT POP
* child cascade: UPDATE_KEY HIDE SHOW must affect all descendants recursively for remember and hidden but NOT viewModel saved, UNMOUNT must clear viewModel remember saved children for all descendants
* mount rules: parent must exist at commit time considering earlier mounts in same txn, otherwise ignore, id already exists ignore, remount after unmount fresh with empty maps
* same key update is no-op remember stays
* deep nesting 3+ levels must cascade
* transaction: BEGIN queues, COMMIT applies in order and handles parent in same txn, ADD_TO_BACKSTACK pushes before snapshot, POP reverts to before snapshot, handling name or NONE
* rotate: clears remember for all and sets hidden false, retains viewModel saved
* parent in same txn: child mount where parent mounted earlier in same txn should succeed

Oracle approach:

* NodeState holds parent, key, viewModel, remember, saved, children, hidden
* txn map tid to list of ops plus backstack name, backstack list of name to deep copied nodes before txn
* mount internal: if id exists ignore, if parent not NONE and parent missing ignore, create node parent key empty maps hidden false add to parent children
* updateKey internal: if missing ignore, if same key no-op, else clear remember for node plus all descendants via DFS collect, set new key
* hide internal: for node plus descendants clear remember and mark hidden true
* show internal: for node plus descendants set hidden false
* unmount internal: collect descendants via DFS, for each removal update parent children if parent not also being removed, then delete all
* pop: if name NONE pop last, else find last occurrence of name and revert to its before snapshot and drop from idx onwards

Files:
* environment/src/com/example/compose/ComposeManager.kt – buggy leak with transaction but missing recursive clears
* environment/src/com/example/compose/Node.kt with saved hidden
* environment/src/com/example/app/Main.kt reads scenario writes output with support for both old style MOUNT id parent key and new transactional MOUNT tid id parent key, plus HIDE SHOW etc, plus VM_PUT REMEMBER_PUT SAVE ROTATE QUERY
* solution/ – fixed versions
* tests/expected/*.scenario.txt + *.expected.txt – 16 scenarios now: mount_put_query, update_clears, child_cascade, unmount_clears_descendants, same_key_no_clear, remount_after_unmount, deep_nesting, vm_survives, vm_cleared, missing parent, multiple children, interleaved, hide_show_cascade, rotate_clears, parent_in_same_txn, backstack_pop
* tests/test.sh pytest comparison

Difficulty:
* Oracle 16/16
* Buggy 3/16
* Expected after edgy: avocado 1/5 or 0/5, opus 2/5, gpt 2/5 – not too easy 5/5

Author Tosin Daniel Jimoh purple29th at meta.com
