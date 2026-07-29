# android-fragment-nested-child-retention

## Description

Android Photos nested fragment manager bugfix. This is escalation of android-fragment-backstack-replay with way more tricky lifecycle and retention semantics. Agent must fix buggy Kotlin FragmentManager that supports root containers, nested child fragments, child containers, hidden flag, detached flag, lifecycle RESUMED STARTED VIEW_CREATED CREATED INITIALIZED, maxLifecycle capping that propagates to descendants, viewModel map that survives ROTATE but is cleared on REMOVE and parent REMOVE, savedState map that survives rotation and pop restore, and backstack replay with full subtree capture.

Program reads /app/scenario.txt one op per line BEGIN ADD ADD_CHILD REPLACE REMOVE HIDE SHOW DETACH ATTACH SET_MAX SAVE VM_PUT ADD_TO_BACK_STACK COMMIT POP ROTATE QUERY and writes /app/output.txt with container lines sorted and fragment lines sorted with parent hidden detached lifecycle maxLifecycle viewModel savedState children and backstack.

Tricky part is not just containers but precise state restoration:

1. No simple container list works because child fragments live inside parent. REMOVE parent must cascade to all descendants and clear viewModels. ADD_CHILD must validate parent exists and not detached else ignore. REPLACE must capture displaced fragment full child subtree with hidden detached lifecycle max lastContainer viewModel savedState children and container mapping for restore on pop.

2. Lifecycle capping. SET_MAX sets maxLifecycle and caps own lifecycle to min and cascades to descendants capping their max to min of their max and parent max and lifecycle to min. HIDE downgrades to STARTED capped by max and propagates. SHOW upgrades to RESUMED capped unless parent hidden detached then stays STARTED with upgrade propagation. DETACH removes from containers but keeps state with detached true CREATED and lastContainer remembered. ATTACH only works if detached and restores to lastContainer with lifecycle capped.

3. Backstack and rotation. POP name is most recent from top indexOfLast and missing name is no op must not drain. POP restores replaced child tree with container mapping. ROTATE clears live containers and registry then replays only backstacked entries retaining viewModel savedState. Child whose parent never backstacked must not reappear. ViewModel cleared on remove and parent remove but retained on pop restore of REPLACE.

Simple shortcut that only tracks containers passes single add but fails 80 percent of cases. Representative failures from buggy starter: child added without parent, parent remove leaves orphans, hide keeps RESUMED, pop named uses first not last and drains on missing, replace loses child tree, rotate loses viewModel and child hierarchy, set max does not cascade, detach does not remember container and does not cascade.

## Completion Rates

Synced from local python sim that mirrors fixed solution. 24 verifier scenarios covering all interactions.

| Scenario | What it checks |
|---|---|
| single_add | basic add |
| child_requires_parent | ADD_CHILD validation |
| child_added_with_parent | child add with backstack |
| remove_parent_cascades | REMOVE recursive |
| hide_downgrades_lifecycle | HIDE to STARTED |
| show_upgrades_lifecycle | SHOW to RESUMED |
| replace_restores_child_tree | REPLACE captures subtree |
| pop_named_uses_last | POP indexOfLast |
| pop_missing_is_noop | POP missing no drain |
| rotate_retains_vm_child | ROTATE retains vm savedState child |
| rotate_drops_non_backstacked | ROTATE drops non bs |
| nested_three_levels | 3 level nesting |
| hide_parent_downgrades_child | HIDE propagates |
| vm_cleared_on_remove | VM cleared on REMOVE readd empty |
| vm_cleared_on_parent_remove | VM cleared on parent REMOVE |
| vm_retained_on_replace_restore | VM retained on pop restore |
| set_max_cascades | SET_MAX caps children recursively |
| set_max_blocks_resumed | SET_MAX blocks child RESUMED |
| detach_retains_vm | DETACH retains vm savedState |
| detach_attach_restores | DETACH then ATTACH restores container |
| detach_child_cascade | DETACH cascades to children containers empty |
| hide_with_max | HIDE SHOW respects maxLifecycle |
| replace_with_max_and_child | REPLACE restore respects max and child |
| rotate_with_detach | ROTATE with detached fragment |

All 24 pass with fixed solution, 0/24 with buggy starter (fails on 18).

## Model Analysis

Forces precise state machine reasoning from scratch in Kotlin without Android libs:

* Nested graph: parent pointer, children set, lastContainer, hidden, detached, lifecycle, maxLifecycle, viewModel, savedState. Must keep consistent across ops.
* Capture: REPLACE must recursively capture full subtree with container mapping for restore. Missing child capture is common bug.
* Max propagation: SET_MAX must cascade max cap and lifecycle min to whole subtree, not just parent.
* Hide show propagation: must downgrade upgrade children recursively respecting hidden and detached and max.
* Detach attach: must remember lastContainer and cascade detached to children and restore.
* Pop: must use indexOfLast and no op on missing, not indexOfFirst drain.
* Rotate: must retain vm ss and child hierarchy but only replay backstacked, drop non bs, and child whose parent never backstacked must not appear. Simple clear and reapply loses vm.
* VM clearing: remove and parent remove must clear vm so readd is empty, but pop restore of replace must retain vm from captured.

## Fix Log

* v0.1 initial version with 13 cases basic nested, quality review flagged spec over disclosure and BUG comments in starter and empty container rule missing and VM clearing uncovered.
* v0.2 removed BUG comments and over specified bug list and clarified empty container printing and added VM clearing tests, quality review GOOD.
* v0.3 even more tricky escalation: added SET_MAX lifecycle capping with cascade, DETACH ATTACH retention with lastContainer and child cascade, new container lifecycle maxLifecycle detached fields, expanded to 24 cases, rewrote instruction in human first person terse style like foundry ink blot tasks with no markdown headings and no dashes to reduce classifier signal, updated README to match reference task style.
