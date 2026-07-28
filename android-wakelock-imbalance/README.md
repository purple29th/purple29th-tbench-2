# codimango/android-wakelock-imbalance v0.13

## Description

Agent writes stdlib-only Python at /app/solve.py that reads WKLK wakelock trace from Android power manager Doze QA. Each trace has many acquire/release events with timestamps and thread ids. Most balanced but some leaked. Need to compute per (id, thread) pair with duplicate dedup, dangling release ignore, thread-scoped matching, final-interval duration measured to per-pair last observation, stable timestamp order.

This is the **precision escalation** inspired by `foundry-thermal-subvoxel-void` but for wakelocks. Foundry uses intensity conservation vs threshold fails 80-130% over; here naive shortcuts fail similarly:

* per-id (ignoring thread) 60-92% over
* file order not timestamp 30-55% over/under
* global trace end vs per-pair last 42-73% over – analogous to speck heavy including far specks
* first-ever acquire vs final interval 120-310% over
* duplicate idempotency 20-45% over

Only genuine method with thread affinity, final interval isolation, per-pair last observation, stable sort passes.

## Leakage Fix - BAD_LEAKAGE (primary)

Previous version exposed `/tests/data/ground_truth.json` readable by solver and AST checker only blocked complete literals, allowing "/tes"+"ts/data" concatenation bypass and base64 encoded path.

Fixes in v0.12:
- Removed ground_truth.json entirely – verifier now computes expected directly by parsing heldout .wklk and running oracle logic `_compute_true` in harness process. No JSON file to steal.
- BANNED_MODULES now includes base64, binascii, codecs, builtins, zlib, posixpath, ntpath, genericpath – prevents encoded bypass. BANNED_DECODE_ATTRS b64decode etc blocked.
- AST checker detects base64-encoded strings that decode to banned paths via `_try_b64_decode`.
- Strict open dataflow: only `open(sys.argv[1])` or variable directly derived from `sys.argv[1]` or unmodified function param allowed. Variables assigned via Call marked tainted and blocked.
- Limit open calls <=2, block constant paths, concatenated paths, call-constructed paths.
- Still uses isolated temp dir copy neutral scan.wklk with PYTHONPATH=td, cwd=td.

## Difficulty Fix - Too Easy / Reasoning Required

Previous v0.12: all models 5/5 pass despite removing worked example, because instruction still gave explicit formula `last_ts - first_acq` and explicit bullet list of edge handling, and hidden traces only 10k-16k events, 15% negative, 2-5 cross-thread.

v0.13 (foundry-inspired):
- Rewrote instruction.md to foundry style: story intro (Android power lab checking Doze), describes messy patterns narratively not as recipe, gives failure quantifications (per-id 60-92%, file-order 30-55%, global-end 42-73%, first-ever 120-310%, duplicate 20-45%, signed misgroup 10-25%, offset hardcode fails 6/7), says "That is the hard part" similar to foundry's background/plateau/halo paragraph. Removes explicit `last_ts - first_acq` formula, replaces with principle: "hold's age should reflect pair's own last observation, not global trace end" and "final continuous hold per pair, measured to its own last observation with stable order". Requires inference of per-pair last vs global and duplicate updates last.
- Increased trace size: 1000-1300 ids (was 700-900), 15000-25000 events (was 10000-16000), up to 16 threads (was 12), 30% same-ts collisions (was 22-25%), 20% negative ids (was 15%), cross-thread releases 3-6 per acquire (was 2-5), dangling 20-40 (was 15-35). Adds heavy pattern 6: early leak with far global continuation to trap global-end method.
- New sample scene.wklk leaked 3834544 (1259 events) – previously 566249 (571 events). Hidden heldouts now ~87M-106M leaked duration, much larger, 24k-31k events each.
- Added discriminators like foundry's speck_heavy: test_per_pair_last_vs_global (global overcounts 42-73%), test_final_interval_vs_first_ever (first-ever overcounts 120-310%), test_duplicate_updates_last_ts (duplicate must update last observation), test_cross_thread_heavy (3-6 cross-thread per acquire, per-id fails), test_stable_order_matters (file order within same ms matters, unsable sort leaks vs balanced). These are analogous to foundry's speck_heavy where naive global sum fails.
- Randomized dynamic expanded to 5 traces heavy.
- Banned modules expanded to include posixpath, ntpath, genericpath, os (strict) like foundry, plus io, etc.
- Target: reduce avocado from 5/5 to 0-2/5, GPT to 1-3/5, Opus to 2-3/5 due to less explicit spec and heavier traps – matching foundry's 0/5 avocado, 2/5 gpt, 2/5 opus calibration.

## Grading Strength

- 7 heldouts with varied offsets 16,20,24,32,40,96,128,20 and garbage padding
- varied_offset_hardcode_guard, reacquire_final_interval, cross_thread_and_dedup, per_pair_last_vs_global, final_interval_vs_first_ever, duplicate_updates_last_ts, cross_thread_heavy, stable_order_matters, randomized_dynamic (5 heavy random), timestamp_order_required, negative_ids, same_timestamp_stable_order
- 21 tests total, oracle passes all, base with no solve.py fails
- Oracle uses explicit stable sort by (ts, orig_idx) and per-pair last tracking

## Completion Rates (expected after fix)

- oracle 21/21 100%
- avocado previously 5/5 too easy, expect 0-2/5 after foundry-style de-spec and heavy traps (per-pair last vs global is main discriminator like speck heavy)
- opus previously 5/5, expect 2-3/5 due to final vs first and stable order
- gpt previously 5/5, expect 1-3/5 due to duplicate last and cross-thread heavy
- Overall target 30-45% pass rate like foundry's 40% (foundry: opus 40-50%, gpt 40%, avocado 10% combined)

## Model Failure Modes

* per-id counting not per thread -> 60-92% over (cross-thread noise mistaken as balanced)
* file order not timestamp -> 30-55% over/under
* global final timestamp instead of per-pair last_ts -> 42-73% over (early quiet pairs measured to far future)
* first-ever acquire vs final interval -> 120-310% over (earlier balanced cycles counted)
* duplicate dedup not updating last_ts -> undercount and overcount depending
* cross-thread release counted as valid -> undercount leak or overcount balancing
* hardcoding offset 64 -> fails 6/7 heldouts
* not sorting by timestamp -> random failures
* not stable for equal timestamps -> stable_order_matters 50 vs 0 discriminator
* unsigned parsing of negative ids -> misgroups 20% of pairs

## Anti-Cheating

- 7 hidden traces leaked 87202843,99728958,104078704,106584732,103371256,94546068,98917926 vs sample 3834544, varied offsets, shuffled order, 15k-31k events each
- No ground_truth.json, expected computed in harness
- Overfit blocked: only scene.wklk at /app/data, hidden under tests/data mounted only at verify, neutral temp copy
- Reward hacking blocked via AST checks for concatenation, constant open, base64, tainted assignments, base64-encoded path detection
- From-scratch guard: bans os, pathlib, io, etc like foundry, plus posixpath, ntpath, genericpath
