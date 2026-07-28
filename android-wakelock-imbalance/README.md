# codimango/android-wakelock-imbalance v0.12

## Description

Agent writes stdlib-only Python at /app/solve.py that reads WKLK wakelock trace from Android power manager doze QA. Each trace has many acquire/release events with timestamps and thread ids. Most balanced but some leaked. Need to compute per (id, thread) pair with duplicate dedup, dangling release ignore, thread-scoped matching, final-interval duration sum.

## Leakage Fix - BAD_LEAKAGE (primary)

Previous version exposed `/tests/data/ground_truth.json` readable by solver and AST checker only blocked complete literals, allowing "/tes"+"ts/data" concatenation bypass and base64 encoded path.

Fixes in v0.12:
- Removed ground_truth.json entirely – verifier now computes expected directly by parsing heldout .wklk and running oracle logic `_compute_true` in harness process. No JSON file to steal.
- BANNED_MODULES now includes base64, binascii, codecs, builtins, zlib – prevents encoded bypass. BANNED_DECODE_ATTRS b64decode etc blocked.
- AST checker now detects base64-encoded strings that decode to banned paths via `_try_b64_decode` heuristic.
- Strict open dataflow: only `open(sys.argv[1])` or variable directly derived from `sys.argv[1]` or unmodified function param allowed. Variables assigned via Call (e.g., b64decode) marked tainted and blocked. Prevents `path = b64decode(...); open(path)`.
- Limit open calls <=2, block constant paths, concatenated paths, call-constructed paths.
- Still uses isolated temp dir copy neutral scan.wklk with PYTHONPATH=td, cwd=td.

## Difficulty Fix - Too Easy / Reasoning Required

Previous: all models 5/5 pass, instruction gave full algorithm with worked example acquire@10 release@20 acquire@30 dup@40 => 10, plus explicit file-order 464265 vs timestamp-order 358620.

v0.12:
- Rewrote instruction.md to remove implementation recipe and worked example. Keeps format precise but describes leak detection abstractly: thread-scoped matching, duplicate handling, final-interval only, last_ts - first_acq. No explicit example of final-interval calc. Says file order not timestamp order must sort, mentions stable for equal ts but doesn't give file-order total.
- Increased trace size: 700-900 ids (was 550-750), 10000-16500 events (was 8457-11468), up to 12 threads, 22-25% same-ts collisions (was 15%), 15% negative ids (was 12%), more cross-thread releases 2-5 per acquire, more dangling releases 15-35.
- New sample scene.wklk leaked 566249 (571 events) – previously 358620. Hidden heldouts now ~18M-24M leaked duration, much larger, to avoid sample overfit.
- Added new tests: test_negative_ids and test_same_timestamp_stable_order to enforce signed parsing and stable order.
- Target: reduce avocado from 5/5 to 2-3/5, GPT to 2-3/5 due to less explicit instruction and larger traces.

## Grading Strength

- 7 heldouts with varied offsets 16,24,40,96,128,32,20 and garbage padding
- varied_offset_hardcode_guard, reacquire_final_interval, cross_thread_and_dedup, randomized_dynamic (3 random), timestamp_order_required, negative_ids, same_timestamp_stable_order
- Oracle passes 16 tests, base with no solve.py fails

## Completion Rates (expected after fix)

- oracle 3/3 (now 16 tests)
- avocado previously 5/5 too easy, expect 2-3/5 after larger traces and reduced spec
- opus 5/5 may remain high but should show some failures on edge tests
- gpt previously 5/5 after spec clarified, expect 2-4/5 after de-specification

## Model Failure Modes

Per id counting not per thread, not handling duplicate dedup, cross-thread release ignored incorrectly, using global final timestamp instead of per-pair last_ts, hardcoding offset 64, using first-ever acquire vs final interval, not sorting by timestamp, not stable for equal timestamps, unsigned parsing of negative ids.

## Anti-Cheating

- 7 hidden traces leaked 18723242,22840801,24367344,24458127,23256618,22393981,24662569 vs sample 566249, varied offsets, shuffled order, 10k-16k events each
- No ground_truth.json, expected computed in harness
- Overfit blocked: only scene.wklk at /app/data, hidden under tests/data mounted only at verify, neutral temp copy
- Reward hacking blocked via AST checks for concatenation, constant open, base64, tainted assignments
