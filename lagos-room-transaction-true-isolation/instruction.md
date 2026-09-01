I am Chinedu from Lagos Nigeria, I build market app for Balogun market traders where each stall has inventory count in Room database with WAL. Problem is transaction isolation: two concurrent writes to same stall inventory cause lost update, one write disappears, need proper transaction generation and isolation plus checkpoint.

App has StallDao with inventory column, async update scheduled at tick with scenario JSON that contains bind and resolve events. Requirement: only latest binding for same stall should win but stale that was scheduled before must still consume WAL token, similar to recycler staleness but for Room.

We have twenty three scenarios like simple_bind, concurrent_write_lost_update, isolation_repeatable_read etc. Must handle generation tracking per stall and WAL token budget.

Please fix app/src/main/java/com/example/room/StallRepository.kt.

Sample db in environment/src. Hidden tests in tests/expected check isolation.

File layout android Room no binary, Kotlin.

Coding rules Kotlin.

If you get generation and WAL checkpoint right you pass.

Author Tosin Daniel Jimoh purple29th at meta.com


We use Room with SQLite WAL mode. Our test harness writes scenario JSON that contains lines like BIND stall_id item_id at tick, RESOLVE fetch_id, QUERY stall_id, RECYLCE cell_id, TICK. The output is expected transaction log that must match. The generation tracking must ensure stale bind does not overwrite newer inventory even if stale resolves later. Also budget for WAL checkpoints must cap at cap and carry fractional remainder.

Our table is stalls with columns id, inventory, generation, last_modified. When you bind stall 5 with inventory 12 at tick 10, you schedule async fetch at tick 12 with generation 2. If at tick 11 you recycle cell for stall 5, that generation 2 must be invalidated. Any RESOLVE for generation 1 that arrives at tick 13 must be ignored as write but must still consume one token from checkpoint queue.

Bug we see: lost update happens when two concurrent writes both read old inventory 10, then both write 12 and 13, final is 13 not 15 that accounts for both increments. Need proper transaction isolation repeatable read.

We have twenty three scenarios like simple_bind_resolve, concurrent_write_lost_update, isolation_repeatable_read, phantom_read, write_skew, budget checks. Our current code in StallRepository.kt has missing synchronized and generation check.

A correct fix must use synchronized block around inventory read-modify-write, keep generation map per stall, check generation equals current before applying, but still call consumeCheckpointToken() even for stale.

If you get generation and WAL right you pass all twenty three.

Files: app/src/main/java/com/example/room/StallRepository.kt you fix, environment/src has Main.kt ScenarioParser etc, solution has correct FetchScheduler and RecyclerPool reference, tests/expected has twenty three expected files, test_outputs.py runs bash src/run.sh that writes /app/output.txt.

Coding rules Kotlin, no Thread.sleep blocking, use coroutines? But we use simple.

Author Tosin Daniel Jimoh purple29th at meta.com
