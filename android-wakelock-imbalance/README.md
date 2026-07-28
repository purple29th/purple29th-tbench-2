# codimango/android-wakelock-imbalance

## Description

Agent writes stdlib only Python at /app/solve.py that reads wakelock trace wklk magic WKLK from Android power manager doze QA. Each trace has many acquire release events with timestamps and thread ids. Most balanced but some leaked. Need to compute per id and thread pair with duplicate acquire dedup, release without acquire ignored, thread scoped matching. For each leaked id thread pair duration equals last timestamp seen for that same (id, thread) pair minus first acquire timestamp of its final still-held interval, sum across leaked pairs. If same pair had earlier balanced cycles (acquire-release), only final continuously-held interval counts.

This is OS wakelock leak detector that genuinely needs thread scoped reasoning, not just trivial per id counting. Naive per id counting of acquires minus releases fails with huge overcount, we measured naive 1238 vs true 34 for heldout_1 previously, now varied offsets enforce header parsing.

## Complexity Fix (BAD_GRADING_WEAK)

Previous version hardcoded data_offset=64 in all fixtures, so parsers ignoring header offset passed. Fixed by generating 7 heldouts with varied offsets: 16,24,40,96,128,32,20. At least 5 of them fail if parser hardcodes 64. Added explicit offset guard test and reacquire final-interval tests.

Also added acquire-release-acquire-final-leak pattern to enforce final-interval semantics: e.g., acq@10 rel@20 acq@30 dup@40 leak => duration 10 (final interval) not 30 (first-ever). Clarified instruction to state final interval rule and allowed built-in open() for scan path.

## Completion Rates

Target: oracle 3/3, Avocado 1/5, Opus 5/5, GPT 0/5 previously; now with harder offset + reacquire coverage expected similar or harder. Oracle passes all 7 heldouts plus dynamic random tests.

## Model Analysis

Dominant failures: per id counting not per thread, not handling duplicate acquire dedup, not handling cross thread release, using global final timestamp instead of pair-local last timestamp (produces huge overestimates 15060 vs 34), recursion. New failures: hardcoding offset 64, using first-ever acquire vs final interval.

## Anti-Cheating

Hardcoded fails: 7 hidden traces have different leaked durations 162,114,143,324,167,278,162 vs sample 18, with varied data_offset. Constant fails. Overfit blocked: only scene.wklk at /app/data, hidden under tests data mounted only at verify, neutral temp copy and isolated TD. Generator not mounted, ground truth in ground_truth.json. Reward hacking hardened via randomized dynamic traces at grading time (3 random traces with random offsets), explicit offset variation tests, reacquire semantics test, cross-thread/dedup test.

Author: Tosin Daniel Jimoh - Android wakelock imbalance with thread scoped dedup, final-interval semantics, varied offset fix
