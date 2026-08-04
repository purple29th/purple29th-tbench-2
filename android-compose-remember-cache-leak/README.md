# android-compose-remember-cache-leak

## Summary
I own the Android storefront app's product detail screen built with Jetpack Compose. Composables use `remember` to cache expensive calculations keyed by product variant, and `viewModel` to survive config changes. Production shows `remember` leaking after a variant key change and after navigation pop — stale caches survive and show wrong variant data, while `viewModel` should survive key changes but be cleared on unmount.

The task ships a buggy `ComposeManager.kt` that fails to invalidate remember cache on key change and fails to cascade disposal to children. Agent must fix it.

## Why Hard
* remember vs viewModel lifetime: viewModel survives UPDATE_KEY, remember must be cleared on UPDATE_KEY and on UNMOUNT, always empty after key change.
* Child cascade: UPDATE_KEY must clear remember for all descendants recursively but NOT clear their viewModel. UNMOUNT must clear viewModel, remember, and children for all descendants recursively.
* Mount rules: parent must exist and not be disposed, otherwise mount ignored. Child container ever-used tracking not needed here, but parent check matters.
* Re-mount after unmount must be fresh with empty maps.
* Same key update must be no-op (remember stays).
* Deep nesting 3+ levels must cascade correctly.

Buggy baseline fails 9/12 scenarios (3 pass) → reward 0: remember stays after UPDATE_KEY, child remember stays after parent UPDATE_KEY, unmount leaks children viewModel, mount with missing parent not ignored correctly.

## Oracle Approach
* NodeState holds parent, key, viewModel map, remember map, children set
* mount: if id exists ignore, if parent != NONE and parent missing ignore, create node with parent, key, empty maps, add to parent children
* updateKey: if node missing ignore, if new_key == old key no-op, else clear remember for node + all descendants recursively, set new key
* unmount: collect node + descendants via DFS, for each removal update parent children if parent not also being removed, then delete all from registry (both vm and remember)
* vm_put/remember_put: put into respective maps if node exists
* query: sorted by id, format `node=id parent=... key=... viewModel={...} remember={...} children=[...]`

Method works for varied operation sequences, deep nesting, and re-mount.

## Files
* `environment/src/com/example/compose/ComposeManager.kt` – buggy leak
* `environment/src/com/example/compose/Node.kt`
* `environment/src/com/example/app/Main.kt` – reads /app/scenario.txt writes /app/output.txt
* `solution/` – fixed versions
* `tests/expected/*.scenario.txt + *.expected.txt` – 12 scenarios
* `tests/test.sh` – pytest comparison

## Difficulty
* Oracle 12/12
* Buggy 3/12
* Expected gpt 2/5, opus 2/5, avocado 1/5 – similar to fragment viewbinding cleanup but simpler domain (single container, no backstack, no rotate)

Author Tosin Daniel Jimoh purple29th at meta.com
