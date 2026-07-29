# codimango/android-wakelock-imbalance v0.16 - rebalance for solvability

## Description

Agent writes stdlib-only Python at /app/solve.py that reads WKLK wakelock trace from Android power manager Doze QA. Each trace has many acquire/release events with timestamps and thread ids. Most balanced but some leaked. Need to compute per (id, thread) pair with duplicate dedup, dangling ignore, thread-scoped matching, final-interval duration measured to per-pair last observation, stable timestamp order, plus thread 0 system force-release handling including global all-clear.

## Why v0.15 was too hard (0/5)

v0.15 made force clear scope vague: "System thread 0 does force clear with broader semantics, look at sample to infer exact scope, some clears affect more than just one id." Hidden semantic (0,0,ts,0) clears ALL ids was not described, had to be reverse engineered from binary. That made task unsolvable for GPT and Metacode (both failed). User wants hard that fails some but not all, using sister tasks as reference.

Sister task reference: android-fingerprint-oil-smear is accepted and hard. It gives explicit key property (energy conservation) but not an exhaustive failure checklist. It gives binary layout, story, sample, and says halo and far dust should be ignored, and gives tolerance. That is explicit enough to be solvable but still hard.

## Hardening v0.16 (target 1-2/5 pass, not 0/5)

* Keep instruction explicit about thread 0 semantics, like fingerprint gives explicit key property:
  - "System thread 0 is exception: a release event with thread id 0 for a given wakelock id releases all holders of that id across all threads"
  - "Additionally, a release event with thread id 0 and id 0 is a Doze entry that clears all wakelocks across all ids, not just id 0"
  This is now explicit, so task is solvable without binary reverse engineering, but still requires implementing both.
* Remove exhaustive failure checklist with percentages that made v0.14 too easy (5/5). v0.16 has no "Simple shortcuts are off by large margin" bullet list with 60-92%, 30-55%, etc. Only principles: per (id,thread) independence, idempotent acquire, cross-thread no-op, shuffled dump needs chronological order, same-ms write order preserved matters, per-pair last vs global, final interval only, single acquire age zero.
* Keep trace size large: 1500-2500 ids (30% negative), 20000-50000 events, up to 24 threads, 40% same-ts collisions, 8-12 cross-thread per acquire, 30-50 dangling, early leak with far continuation.
* Reduce global all-clear frequency from 75% to 40% of heldouts, so models missing it can still pass some heldouts but fail unit tests and 40% of heldouts, leading to overall fail. With explicit description, models should implement it and pass.
* Scene sample 34M leaked now includes one global all-clear early with post-clear leaks, demonstrating behavior without being 0.
* Tests: 28 total (9 heldouts + 19 unit) including global all-clear tests. Oracle passes all.

## Grading Strength v0.16

- 9 heldouts varied offsets 16,24,40,96,128,32,20,192,256, garbage padding fake magic
- Unit discriminators:
  varied_offset, reacquire_final_interval, cross_thread_and_dedup, per_pair_last_vs_global, final_interval_vs_first_ever, duplicate_updates_last_ts, cross_thread_heavy, multi_thread_same_id, stable_order_matters, thread_0_global_force_release (per-id), thread_0_with_same_timestamp_order, global_all_clear_id_0 (explicit now), global_all_clear_same_ts_order, randomized_dynamic, timestamp_order_required, negative_ids, same_timestamp_stable_order
- Oracle stable sort by (ts, orig_idx) plus per-pair last plus thread 0 handling

## Completion Rates expected v0.16

- oracle 28/28 100%
- v0.14: 5/5 avocado too easy
- v0.15: 0/5 all failed due to hidden all-clear
- v0.16 target: 1-2/5 pass (sister task pattern): some models that implement both per-id and all-clear correctly plus per-pair last and stable order will pass, others fail 1-2 heldouts. Expected avocado 1-2/5, opus 2-3/5, gpt 1-2/5. Not 0/5, not 5/5.

## Model Failure Modes v0.16

* per-id ignoring thread -> fails multi_thread_same_id
* file order not timestamp -> fails timestamp_order_required
* global trace end vs per-pair last -> fails per_pair_last_vs_global
* first-ever vs final interval -> fails final_interval_vs_first_ever
* duplicate not idempotent or not updating last -> fails duplicate_updates_last_ts
* cross-thread counted as valid -> fails cross_thread_heavy
* ignoring thread 0 per-id global -> fails thread_0_global_force_release
* ignoring global all-clear id 0 -> fails global_all_clear_id_0 (40% heldouts)
* offset hardcode, unsigned id, magic scanner

## Anti-Cheating

Same as v0.15: no ground_truth.json, expected computed in harness, AST checks for path concatenation, base64, banned modules os pathlib io etc, fake WKLK magic in padding.
