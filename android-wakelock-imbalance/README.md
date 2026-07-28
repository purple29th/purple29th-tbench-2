# codimango/android-wakelock-imbalance

## Description

Agent writes stdlib only Python at /app/solve.py that reads wakelock trace WKLK magic WKLK from Android power manager doze QA. Each trace has many acquire release events with timestamps and thread ids. Most balanced but some leaked. Need to compute per id and thread pair with duplicate acquire dedup, release without acquire ignored, thread scoped matching. For each leaked id thread pair duration equals last timestamp seen for that same (id, thread) pair minus first acquire timestamp of its final still-held interval, sum across leaked pairs. If same pair had earlier balanced cycles (acquire-release), only final continuously-held interval counts.

This is OS wakelock leak detector that genuinely needs thread scoped reasoning and timestamp sorting, not just trivial per id counting. Naive per id counting fails huge, and file-order vs timestamp-order mismatch causes gpt failures.

## Ordering Fix (BAD_LEAKAGE + BAD_AMBIGUOUS)

Previous instruction said hidden traces are sorted by timestamp, but fixtures were shuffled requiring timestamp sort. Fixed instruction to explicitly state file order is NOT timestamp order, records may be shuffled, solver must process in stable timestamp order preserving file order for equal timestamps (python stable sort). Sample now has timestamp-order total 358620 vs file-order 464265, demonstrating requirement. Added test_timestamp_order_required that generates shuffled trace and checks solver sorts.

## Leakage Fix (BAD_LEAKAGE)

Previous verifier mounted /tests/data/ground_truth.json readable and AST checker only blocked complete forbidden literals, allowing bypass via "/tes"+"ts/data/..." concatenation. Fixed by:
- Hardened AST checker to evaluate BinOp Add concatenation of string literals and block forbidden paths even via construction
- Block any open() with constant file path (only open(sys.argv[1]) or open(path) where path is input arg allowed)
- Limit open calls to <=2
- Block f-string parts containing banned tokens
- Still keep isolated temp dir copy (neutral scan.wklk) for execution, but now checker prevents hidden file access via constructed paths

Also updated instruction to explicitly say only built-in open for given scan path allowed, and that checker enforces concatenation detection.

## Complexity Fix (Too Easy)

Previous version had 320-520 ids, 3850-5935 events, avocado passed 5/5 -> too easy. Hardened to:
- 550-750 ids, 8457-11468 events (8k-11k), up to 12 threads
- 15% same-timestamp collisions requiring stable sort
- More negative ids (12% pool) testing signed parsing and filtering
- More cross-thread releases (2-4 per acquire)
- Garbage padding in header (0xAA) to catch offset hardcode
- Varied offsets still: 16,24,40,96,128,32,20
- Added more patterns: reacquire after balanced release, duplicate chains

Target: oracle 3/3, Avocado should drop from 5/5 to 2-3/5 due to larger traces and stable-sort requirement. GPT previously failed file-order, now with explicit spec should improve but still need thread scoping.

## Completion Rates

Previous: oracle 3/3, Avocado 5/5, Opus 5/5, GPT 1/5 (too easy). After hardening, expected Avocado 2-3/5, Opus 5/5, GPT 2-3/5 if they notice sorting. Oracle passes all 7 heldouts plus dynamic tests.

## Model Analysis

Dominant failures: per id counting not per thread, not handling duplicate acquire dedup, not handling cross thread release, using global final timestamp instead of pair-local last timestamp, recursion, hardcoding offset 64, using first-ever acquire vs final interval, not sorting by timestamp (file-order total 464265 vs timestamp-order 358620 for sample gives huge error), not stable for equal timestamps.

## Anti-Cheating

Hardcoded fails: 7 hidden traces have different leaked durations 8838685,9703572,10761750,10636466,10670622,8377390,8389999 vs sample 358620, with varied data_offset and shuffled order. Constant fails. Overfit blocked: only scene.wklk at /app/data, hidden under tests/data mounted only at verify, neutral temp copy and isolated TD with PYTHONPATH=td. Generator not mounted, ground truth in ground_truth.json. Reward hacking hardened via randomized dynamic traces (3 random), explicit offset tests, reacquire final-interval test, cross-thread/dedup test, timestamp-order-required test checking file-order vs timestamp-order mismatch, and hardened AST checker blocking "/tes"+"ts/data/..." concatenation and constant open paths.

Author: Tosin Daniel Jimoh - Android wakelock imbalance with thread scoped dedup, final-interval semantics, varied offset, stable timestamp sort, leakage hardening
