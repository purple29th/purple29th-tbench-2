# codimango/android-wakelock-imbalance

## Description

Agent writes stdlib only Python at /app/solve.py that reads wakelock trace wklk magic WKLK from Android power manager doze QA. Each trace has flat background plus many acquire release events with timestamps and thread ids plus far dangling releases. Most balanced but some leaked where acquire exceeds release, need to compute total leaked duration as last timestamp minus first acquire summed across leaked ids.

This is OS wakelock leak detector, related to bitmap pool leak detector but for power manager, distinct from subvoxel void tasks and battery swell tasks.

## Completion Rates

Target: oracle 3/3, Avocado 3/5, Opus 4/5, GPT 5/5.

## Model Analysis

Failures: counting not integrating, recursion, dust handling.

## Anti-Cheating

Hardcoded fails, overfit blocked, generator not mounted, ground truth in ground_truth.json.

Author: Tosin Daniel Jimoh - Android wakelock imbalance
