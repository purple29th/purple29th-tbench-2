# codimango/android-wakelock-imbalance v0.15 - too easy fix

## Description

Agent writes stdlib-only Python at /app/solve.py that reads WKLK wakelock trace from Android power manager Doze QA. Each trace has many acquire/release events with timestamps and thread ids. Most balanced but some leaked. Need to compute per (id, thread) pair with duplicate dedup, dangling ignore, thread-scoped matching, final-interval duration measured to per-pair last observation, stable timestamp order, plus thread 0 system force-release handling including hidden global all-clear.

This is precision escalation inspired by foundry-thermal-subvoxel-void but for wakelocks.

## Why previous v0.14 was still too easy (5/5 avocado, 4/5 opus, 5/5 gpt)

v0.14 added thread 0 per-id global release but instruction still explicitly said "release event with thread id 0 for given wakelock id releases all holders of that id across all threads" and gave explicit failure percentages for all traps in a bullet list:

* per-id 60-92%, file-order 30-55%, global-end 42-73%, first-ever 120-310%, duplicate 20-45%, thread0 25-45%, etc.

That list is effectively a checklist for the solver. Stable sort is free in Python, per-pair last vs global is easy if you track max per pair. So all models still passed despite larger traces.

## Hardening v0.15 (target 0-2/5 pass)

* Removed "Simple shortcuts are off by large margin" section entirely that enumerated all failure modes with percentages. No more checklist.
* Shortened instruction from 45 lines to ~25 lines, removed explicit kernel behavior paragraph that spelled out recipe. Now instruction only says: same id can be held by several threads independently, dump is shuffled, system thread 0 does force clear with broader semantics than normal cross-thread releases, look at sample to infer exact scope and typical Doze behavior where system clears, some clears affect more than just one id. This forces reverse engineering from sample.
* Added hidden semantic not described: release (0,0,ts,0) i.e. id 0 from thread 0 is Doze entry that clears ALL wakelocks across ALL ids, not just id 0. This is plausible (Doze suspend clears all) and appears in sample and heldouts but not explicitly described. Naive solvers that only clear that id (or only clear per-id) will overcount dramatically.
  - Example discriminator: two ids leak 90 and 180, then global all-clear 0,0,250,0 => correct 0, naive ignoring all-clear => 270, naive clearing only id 0 => 270.
  - After global clear, re-acquire and leak again tests final interval isolation after global clear.
* Increased difficulty via inference requirement: agent must inspect sample.wklk to discover that thread 0 release sometimes clears more than one id. Sample scene now has 34M leaked with one early global all-clear example that clears early leaks then re-leaks, hinting at behavior.
* Trace size kept large: 1500-2500 ids (30% negative), 20000-50000 events, up to 24 threads, 40% same-ts collisions, 8-12 cross-thread per acquire, 30-50 dangling.
* Heldouts regenerated: 9 heldouts with varied offsets 16,24,40,96,128,32,20,192,256, garbage padding with fake WKLK magic, plus hidden global all-clear events in 75% of heldouts (1 per trace early) with 20-40 post-clear reacquires that leak. Leaked totals now 61M-331M plus small cases 85M etc.
* Added discriminators: test_global_all_clear_id_0 (global all-clear clears all, naive per-id fails), test_global_all_clear_same_ts_order (order matters within same ms for all-clear).
* Kept all previous discriminators: per_pair_last_vs_global, final_interval_vs_first_ever, duplicate_updates_last_ts, cross_thread_heavy, stable_order_matters, thread_0_global_force_release, etc.
* Banned modules unchanged.

## Grading Strength v0.15

- 9 heldouts with varied offsets and garbage padding
- Tests: 28 total (9 heldouts + 19 unit) including new global all-clear tests
  - varied_offset_hardcode_guard (10 offsets)
  - reacquire_final_interval
  - cross_thread_and_dedup
  - per_pair_last_vs_global (overcounts if using global end)
  - final_interval_vs_first_ever
  - duplicate_updates_last_ts
  - cross_thread_heavy
  - multi_thread_same_id_independent_holds
  - stable_order_matters
  - thread_0_global_force_release (per-id global)
  - thread_0_with_same_timestamp_order
  - global_all_clear_id_0 (new, hidden, naive overcounts 25-60% if ignoring)
  - global_all_clear_same_ts_order (new)
  - randomized_dynamic (5 heavy random with thread 0 and global all-clear)
  - timestamp_order_required, negative_ids, same_timestamp_stable_order
- Oracle passes all 28, base fails

## Completion Rates expected after v0.15

- oracle 28/28 100%
- previous v0.14: avocado 5/5, opus 4/5, gpt 5/5 too easy
- expected v0.15: avocado 0-1/5, opus 1-2/5, gpt 0-2/5 due to:
  * hidden global all-clear not described, must be inferred from sample binary analysis
  * no more explicit failure mode checklist, instruction vague about force clear scope
  * per-pair last vs global still traps global-end solvers
  * stable order within same ms matters for both per-id and all-clear

Target 15-30% pass rate, harder than foundry.

## Model Failure Modes v0.15

* per-id counting not per thread -> over/under
* file order not timestamp -> over/under
* global final timestamp instead of per-pair last -> over
* first-ever acquire vs final interval -> over
* duplicate dedup not updating last -> under/over
* cross-thread release counted as valid -> undercount
* ignoring thread 0 per-id global force-release -> overcounts
* ignoring hidden global all-clear id 0 -> overcounts 25-60% (main new discriminator, not described explicitly)
* hardcoding offset 64 -> fails heldouts
* not stable sort -> fails same-ts tests
* unsigned parsing of negative ids -> misgroups

## Anti-Cheating

- 9 hidden traces varied offsets, shuffled order, large, cross-thread heavy, thread 0 releases, plus hidden global all-clear
- No ground_truth.json, expected computed in harness via oracle logic including global all-clear
- Overfit blocked: only scene.wklk at /app/data, hidden under tests/data, neutral temp copy
- Reward hacking blocked via AST checks for concatenation, constant open, base64, tainted assignments
- From-scratch guard: bans os, pathlib, io, etc
- Fake WKLK magic in padding traps magic scanners
