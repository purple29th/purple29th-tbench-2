# codimango/android-wakelock-imbalance

## Description

Agent writes stdlib only Python at /app/solve.py that reads wakelock trace wklk magic WKLK from Android power manager doze QA. Each trace has many acquire release events with timestamps and thread ids. Most balanced but some leaked. Need to compute per id and thread pair with duplicate acquire dedup, release without acquire ignored, thread scoped matching. For each leaked id thread pair duration equals last timestamp for that pair minus first acquire timestamp for that pair, sum across leaked pairs.

This is OS wakelock leak detector that genuinely needs thread scoped reasoning, not just trivial per id counting. Naive per id counting of acquires minus releases fails with huge overcount, we measured naive 1238 vs true 34 for heldout_1, 2292 vs 29 for heldout_2, etc.

## Completion Rates

Target: oracle 3/3, Avocado 2/5, Opus 3/5, GPT 4/5. Hard but solvable.

## Model Analysis

Dominant failures: per id counting not per thread, not handling duplicate acquire dedup, not handling cross thread release, recursion.

## Anti-Cheating

Hardcoded fails: 4 hidden traces have different leaked durations 34,29,13,18 vs sample 0. Constant fails. Overfit blocked: only scene.wklk at /app/data, hidden under tests data mounted only at verify, neutral temp copy and isolated TD. Generator not mounted, ground truth in ground_truth.json. Reward hacking hardened.

Author: Tosin Daniel Jimoh - Android wakelock imbalance with thread scoped dedup
