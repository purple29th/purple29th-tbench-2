# codimango/android-wakelock-imbalance v0.17 - genuine hard, not too easy, not unsolvable

## Description

Agent writes stdlib-only Python at /app/solve.py that reads WKLK wakelock trace from Android power manager Doze QA. Each trace has many acquire/release events with timestamps and thread ids. Most balanced but some leaked. Need to compute per (id, thread) pair with duplicate dedup, dangling ignore, thread-scoped matching, final-interval duration measured to per-pair last observation, stable timestamp order, plus thread 0 system force-release handling including global all-clear.

## History of difficulty tuning

* v0.12: all models 5/5 pass, too easy, had ground_truth.json leakage and explicit formula plus checklist.
* v0.13: rewrote to foundry style, increased to 15k-25k events, still 5/5 because checklist with percentages gave recipe.
* v0.14: added thread 0 per-id global release, increased to 20k-50k events, 40% same-ts, 8-12 cross-thread. Still 5/5 avocado, 4/5 opus, 5/5 gpt because instruction listed all traps explicitly with percentages (60-92%, 30-55%, etc) and gave recipe paragraph.
* v0.15: removed checklist, made force clear vague "some clears affect more than one id, look at sample to infer". Added hidden (0,0,ts,0) all-clear not described. Result 0/5 all failed - too hidden, unsolvable, GPT and Metacode failed.
* v0.16: made rules explicit again (per-id and all-clear) but kept no checklist, added global all-clear explicit. Result still 5/5 avocado, 5/5 gpt - too easy again, because once rules are spelled out, dict tracking is easy for LLMs.

## v0.17 - sister task pattern (fingerprint-oil-smear reference)

Sister task android-fingerprint-oil-smear is accepted, hard, and has 5/5? Actually it has 3/5 etc. Its instruction:

* Short story, task at /app/solve.py, sample at /app/data/scene.fpos
* Binary layout (header + payload)
* Image content description (background + noise + oil smear + bleed lines + halo + far dust that should be ignored)
* Why naive counting fails (brief, no percentages for each trap)
* Key property: optical blur preserves integrated brightness energy, peak suppressed but total light conserved
* Parsing banned modules, grading tolerance, implementation notes (use iterative stack)

It gives explicit key property but not exhaustive failure percentages. It gives binary layout and high-level goal, not full state machine.

Wakelock v0.17 follows same pattern:

* Story, program path, sample at /app/data/scene.wklk
* Binary layout WKLK
* Each trace many ids, each (id, thread) independent hold - explicit per reviewer ivan request, plus multi-thread same id counted separately
* Messy patterns: duplicate idempotent, dangling, cross-thread attempts, reacquire after balanced cycles, system thread 0 force clear
* Kernel behavior explicit for core rules:
  - hold bound to (id,thread), acquire idempotent, release no-op when not held
  - normal cross-thread release only affects releasing thread own pair, no-op otherwise
  - system thread 0 exception: release for given id releases all holders of that id across all threads
  - additionally release id 0 from thread 0 is Doze entry clears ALL ids
  - acquires from thread 0 normal holds for (id,0) only
* Why naive counting fails: qualitative list without percentages (per-id ignoring thread, file order not timestamp, global end vs pair timeline, first-ever vs last interval, duplicate, thread 0 clears)
* Key property: leaked hold measured from first acquire of final still-held interval to its own last observation, not global end. Earlier balanced cycles irrelevant. If single acquire with no later activity for that pair, duration zero. Duplicate while held does not restart interval but updates last observation. Stable order matters: shuffled, reconstruct chronological, same-ms write order preserved.
* Hidden traces vary: up to 2500 ids (30% negative), up to 24 threads, up to 50000 events, many same-ts collisions (now 50% vs 40% to make stable order more important), 10-16 cross-thread per acquire (was 8-12) to make heavy, 30-50 dangling, reacquire patterns, early leak with far continuation, thread 0 force releases including full clear.

This is explicit enough to be solvable (rules given) but not a checklist with percentages that makes it trivial. Key property section gives final interval and per-pair last and zero case and duplicate last update, but without saying "You need per-pair last observation, not global trace end, and final interval only" as a directive checklist item. Instead it's described as property.

## Grading Strength v0.17

* 9 heldouts varied offsets 16,24,40,96,128,32,20,192,256, garbage padding fake WKLK magic
* 28 tests total (9 heldouts + 19 unit):
  - varied_offset_hardcode_guard (10 offsets)
  - reacquire_final_interval
  - cross_thread_and_dedup
  - per_pair_last_vs_global (global overcounts if using global end, analogous to speck heavy)
  - final_interval_vs_first_ever (first-ever overcounts 120-310% if not isolated)
  - duplicate_updates_last_ts (duplicate must update last)
  - cross_thread_heavy (10-16 cross-thread per acquire, naive cross-thread as valid fails)
  - multi_thread_same_id_independent_holds (visible test for per-(id,thread) independence, reviewer requested)
  - stable_order_matters (same ms order matters)
  - thread_0_global_force_release (per-id global, overcounts 25-45% if ignored)
  - thread_0_with_same_timestamp_order
  - global_all_clear_id_0 (id 0 from thread 0 clears all, overcounts 25-60% if ignored, 40% heldouts have it)
  - global_all_clear_same_ts_order
  - randomized_dynamic (5 heavy random with thread 0 and global all-clear)
  - timestamp_order_required, negative_ids, same_timestamp_stable_order
* Increased difficulty vs v0.16: same-ts 50% vs 40%, cross-thread 10-16 vs 8-12, so stable order and cross-thread heavy more likely to trap.
* Oracle passes all 28, base fails.

## Completion Rates expected v0.17

* oracle 28/28 100%
* v0.14: 5/5 too easy because checklist
* v0.15: 0/5 too hidden
* v0.16: 5/5 too easy again because explicit rules + small traces? Actually still explicit.
* v0.17 target: 1-3/5 pass, not 0, not 5. Expected avocado 1-2/5 (may miss per-pair last or duplicate last update), opus 2-3/5, gpt 1-3/5. Genuine hard task, not checklist easy.

Why still hard even with explicit rules:
- Need to implement 6 interacting rules correctly: idempotent, cross-thread no-op, thread 0 per-id clear, thread 0 id 0 all-clear, per-pair last (not global), final interval (not first-ever), duplicate updates last, stable timestamp order
- Many models implement basic dict tracking but forget per-pair last (use global trace end) or first-ever, or forget duplicate updates last, or forget stable order, or forget all-clear
- Increased same-ts and cross-thread makes those more likely to fail
- Binary parsing must respect data offset and ignore garbage with fake WKLK magic

## Anti-Cheating

No ground_truth.json, expected computed in harness, AST checks for path concatenation, base64, banned modules os pathlib io etc, fake WKLK magic trap, isolated temp copy.
