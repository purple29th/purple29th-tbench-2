# codimango/android-wakelock-imbalance v0.14

## Description

Agent writes stdlib-only Python at /app/solve.py that reads WKLK wakelock trace from Android power manager Doze QA. Each trace has many acquire/release events with timestamps and thread ids. Most balanced but some leaked. Need to compute per (id, thread) pair with duplicate dedup, dangling ignore, thread-scoped matching, final-interval duration measured to per-pair last observation, stable timestamp order, plus thread 0 system force-release handling.

This is precision escalation inspired by `foundry-thermal-subvoxel-void` but for wakelocks. Foundry uses intensity conservation vs threshold fails 80-130% over; here naive shortcuts fail similarly:

* per-id (ignoring thread) 60-92% over/under
* file order not timestamp 30-55% over/under
* global trace end vs per-pair last 42-73% over - analogous to speck heavy including far specks
* first-ever acquire vs final interval 120-310% over
* duplicate idempotency 20-45% over
* thread 0 global force-release ignored 25-45% over - leaked pairs that were actually cleared by system are counted as still leaking
* unsigned signed id misgroup 10-25% over
* hardcoding offset 64 fails 8/9 heldouts

Only genuine method with thread affinity, final interval isolation, per-pair last observation, stable sort, and system force-release handling passes.

## Leakage Fix - BAD_LEAKAGE (primary)

Previous version exposed `/tests/data/ground_truth.json` readable by solver and AST checker only blocked complete literals, allowing "/tes"+"ts/data" concatenation bypass and base64 encoded path.

Fixes in v0.12:
- Removed ground_truth.json entirely - verifier now computes expected directly by parsing heldout .wklk and running oracle logic `_compute_true` in harness process. No JSON file to steal.
- BANNED_MODULES now includes base64, binascii, codecs, builtins, zlib, posixpath, ntpath, genericpath - prevents encoded bypass. BANNED_DECODE_ATTRS b64decode etc blocked.
- AST checker detects base64-encoded strings that decode to banned paths via `_try_b64_decode`.
- Strict open dataflow: only `open(sys.argv[1])` or variable directly derived from `sys.argv[1]` or unmodified function param allowed. Variables assigned via Call marked tainted and blocked.
- Limit open calls <=2, block constant paths, concatenated paths, call-constructed paths.
- Still uses isolated temp dir copy neutral scan.wklk with PYTHONPATH=td, cwd=td.

## Difficulty Fix - Too Easy / Reasoning Required v0.13 and v0.14

v0.12: all models 5/5 pass despite removing worked example, because instruction still gave explicit formula and explicit bullet list of edge handling, and hidden traces only 10k-16k events, 15% negative, 2-5 cross-thread.

v0.13 (foundry-inspired):
- Rewrote instruction.md to foundry style: story intro, describes messy patterns narratively not as recipe, gives failure quantifications (per-id 60-92%, file-order 30-55%, global-end 42-73%, first-ever 120-310%, duplicate 20-45%, signed misgroup 10-25%, offset hardcode fails 6/7). Removes explicit formula, replaces with principle. Requires inference of per-pair last vs global and duplicate updates last.
- Increased trace size: 1000-1300 ids, 15000-25000 events, up to 16 threads, 30% same-ts, 20% negative, 3-6 cross-thread, dangling 20-40. Adds early leak with far global continuation trap.
- Added discriminators like foundry's speck_heavy: per_pair_last_vs_global, final_interval_vs_first_ever, duplicate_updates_last_ts, cross_thread_heavy, stable_order_matters.
- Target: reduce avocado from 5/5 to 0-2/5.

v0.14 (too easy still 5/5 avocado, 4/5 opus, 5/5 gpt at ec043ac):
- Root cause: v0.13 instruction still lists all traps explicitly in "Simple shortcuts are off by large margin" and then gives recipe paragraph that spells out required steps; stable sort is free in Python; per-pair last vs global is easy if you track max per pair. So all models still pass.
- Hardening:
  * Added new semantic: thread_id 0 system force-release that releases all holders of same id (Doze force-clear). Unlike normal cross-thread releases which are no-ops, release with tid 0 is global for that id. Ignoring it overcounts 25-45% on new heldouts. This is analogous to foundry's speck isolation requiring special handling of far specks.
  * Rewrote instruction to be even less prescriptive: removed explicit recipe paragraph that listed "separates cross-thread noise, dedupes idempotent acquires without biasing interval start, ignores dangling releases, isolates final continuous interval per pair, and measures its age to its own last observation with stable timestamp order will pass." Replaced with vaguer "handles system force-releases correctly, separates cross-thread noise, and measures final interval age correctly".
  * Increased trace size dramatically: 1500-2500 ids (30% negative), 20000-50000 events (was 15k-25k), up to 24 threads including thread 0, 40% same-ts collisions (was 30%), 8-12 cross-thread releases per acquire (was 3-6), 30-50 dangling (was 20-40). Garbage padding now may contain fake WKLK magic to trap magic scanners.
  * New sample scene.wklk leaked 33543939 (5178 events) vs previous 3834544 (1259 events). Hidden heldouts now 256M-378M leaked duration, 67k-95k events each, offsets 16,24,40,96,128,32,20,192,256 (9 heldouts vs 7).
  * Added new discriminators: test_thread_0_global_force_release (global release clears all threads for id, naive per-thread ignores it -> 220 vs 0), test_thread_0_with_same_timestamp_order (global release order within same ms matters, stable sort required).
  * Expanded randomized_dynamic to include thread 0 force-release patterns.
  * Kept per-(id,thread) independence explicit line per human reviewer request (ivann) to avoid single-owner misreading, but made other traps more implicit.
  * Banned modules unchanged (os, pathlib, io etc like foundry).
- Target after v0.14: reduce avocado from 5/5 to 0-2/5, GPT to 1-2/5, Opus to 1-3/5 due to thread 0 wildcard not described as simple checklist item, plus much larger traces and more same-ts collisions. Thread 0 is main discriminator like speck heavy.

## Grading Strength v0.14

- 9 heldouts with varied offsets 16,24,40,96,128,32,20,192,256 and garbage padding with fake magic
- Tests: varied_offset_hardcode_guard (10 offsets), reacquire_final_interval, cross_thread_and_dedup, per_pair_last_vs_global (global overcounts 42-73%), final_interval_vs_first_ever (120-310%), duplicate_updates_last_ts, cross_thread_heavy (8-12 cross-thread), multi_thread_same_id_independent_holds (reviewer-requested visible test for per-(id,thread) independence), stable_order_matters, thread_0_global_force_release (new, 25-45% overcount if ignored), randomized_dynamic (5 heavy random with thread 0), timestamp_order_required, negative_ids, same_timestamp_stable_order, thread_0_with_same_timestamp_order (new, global release order matters)
- 26 tests total (9 heldouts + 17 unit), oracle passes all, base with no solve.py fails
- Oracle uses explicit stable sort by (ts, orig_idx) and per-pair last tracking plus thread 0 global force-release handling

## Completion Rates (expected after v0.14 fix)

- oracle 26/26 100%
- avocado previously 5/5 too easy at v0.13, expect 0-2/5 after thread 0 wildcard and much larger traces and less explicit recipe (per-pair last vs global is main discriminator like speck heavy, thread 0 is additional)
- opus previously 4/5, expect 1-3/5 due to thread 0 and stable order with global
- gpt previously 5/5, expect 1-2/5 due to thread 0 and duplicate last
- Overall target 20-35% pass rate like foundry's 40% (foundry: opus 40-50%, gpt 40%, avocado 10% combined) - harder than v0.13 due to new semantics

## Model Failure Modes v0.14

* per-id counting not per thread -> 60-92% over/under (cross-thread noise mistaken as balanced, misses independent holds)
* file order not timestamp -> 30-55% over/under
* global final timestamp instead of per-pair last_ts -> 42-73% over (early quiet pairs measured to far future)
* first-ever acquire vs final interval -> 120-310% over (earlier balanced cycles counted)
* duplicate dedup not updating last_ts -> undercount and overcount
* cross-thread release counted as valid -> undercount leak or overcount balancing
* ignoring thread 0 global force-release -> overcounts 25-45% (leaked pairs that were actually cleared by system are counted)
* hardcoding offset 64 -> fails 8/9 heldouts
* not sorting by timestamp -> random failures
* not stable for equal timestamps -> stable_order_matters 50 vs 0 discriminator, thread_0_with_same_timestamp_order 50 vs 0 discriminator
* unsigned parsing of negative ids -> misgroups 30% of pairs
* magic scanner instead of respecting data_offset -> fails due to fake WKLK in padding

## Anti-Cheating

- 9 hidden traces leaked 256M-378M vs sample 33M, varied offsets, shuffled order, 67k-95k events each, 8-12 cross-thread per acquire, 40% same-ts, 30% negative, thread 0 force-releases
- No ground_truth.json, expected computed in harness
- Overfit blocked: only scene.wklk at /app/data, hidden under tests/data mounted only at verify, neutral temp copy
- Reward hacking blocked via AST checks for concatenation, constant open, base64, tainted assignments, base64-encoded path detection
- From-scratch guard: bans os, pathlib, io, etc like foundry, plus posixpath, ntpath, genericpath
- Fake WKLK magic in padding traps scanners that search for magic instead of using data_offset
