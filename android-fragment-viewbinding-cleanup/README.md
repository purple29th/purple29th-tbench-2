# Android Fragment ViewBinding Cleanup

## Description

Agent fixes a mini Android FragmentManager for nested fragments that also tracks ViewBinding. Each fragment has parent, hidden, detached, lifecycle {INITIALIZED, CREATED, VIEW_CREATED, STARTED, RESUMED}, maxLifecycle, lastContainer, viewModel (survives ROTATE and POP), savedState (survives), binding (must be cleared on view destruction), children.

Binding is ViewBinding leak sensitive:
- Created empty on view creation: ADD, ADD_CHILD, REPLACE (new), SHOW (recreated empty), ATTACH (recreated empty), POP restore (empty), ROTATE replay (empty)
- Cleared on view destruction: HIDE (hidden=true, lifecycle STARTED, binding cleared for self and descendants), DETACH (detached=true, CREATED, binding cleared), REMOVE (clear all state and descendants), REPLACE (old fragments binding/viewModel/savedState cleared), ROTATE (all live bindings cleared before replay)

viewModel vs binding:
- viewModel retained across HIDE/SHOW and DETACH/ATTACH, binding not
- savedState retained across ROTATE and POP, binding not — always empty after ROTATE

Child propagation:
- HIDE/SHOW/DETACH/ATTACH/SET_MAX propagate to descendants, binding cleared/created accordingly
- REMOVE/REPLACE cascade to all descendants

Operations: BEGIN, ADD, ADD_CHILD, REPLACE, REMOVE, HIDE, SHOW, DETACH, ATTACH, SET_MAX, SAVE, VM_PUT, BIND_PUT, ADD_TO_BACK_STACK, COMMIT, POP (last occurrence, noop if missing), ROTATE, QUERY.

Output per QUERY: container lines sorted even if empty if ever used, fragment lines sorted with parent NONE, hidden/detached lowercase bool, lifecycle enums, viewModel/savedState/binding sorted key=value, children sorted, backstack line.

## Why Hard

- ViewBinding leak: buggy version keeps binding on HIDE/DETACH, violates Android view lifecycle and leaks references
- Child propagation: HIDE must clear binding for children, SHOW must recreate empty binding for children
- ROTATE: must clear binding for all live fragments, retain viewModel/savedState only if fragment was backstacked, drop non-backstacked fragments including children of non-backstacked parent
- POP: must use last occurrence of name, not first, and be no-op if missing (not drain)
- REPLACE/REMOVE must capture full state including binding for restore on POP, but binding restored as empty (view recreated)
- SET_MAX cascades maxLifecycle and lifecycle to children without clearing binding

Previous periscope task flagged 0.823 similar to ceramic because same subvoxel tech; this switches to Fragment UI architecture, completely different method.

## Completion

Oracle solution fixes all 6 failing cases on buggy version:
- hide clears binding, hide+show binding empty
- viewModel retained across hide, binding not
- detach clears binding retains vm, detach+attach binding empty vm retained
- hide propagates binding clear to children
- rotate clears binding retains vm savedState
- pop named uses last, pop missing noop

Build: Kotlin 1.9.22 via kotlinc compiles, contract tests via `bash src/run-contract.sh` 15 PASS.

Verifier: `tests/test_outputs.py` runs scenarios via `run.sh` comparing snapshot to expected (15 cases). No `_gen.py` leakage.

Author: Tosin Daniel Jimoh <purple29th@meta.com> - Android Fragment architecture track.
