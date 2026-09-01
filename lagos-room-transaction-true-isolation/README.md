lagos-room-transaction-true-isolation

Description

I am Chinedu from Lagos Nigeria, I build market app for Balogun market with Room database. Transaction isolation bug: two concurrent writes to same stall inventory cause lost update, need generation tracking and WAL checkpoint.

App has StallDao with inventory column, async update at tick, must ensure only latest binding wins but stale still consumes token.

Please fix app/src/main/java/com/example/room/StallRepository.kt.

Sample db in app/data. Hidden tests in src/com/example/test check isolation.

File layout android.

Coding rules Kotlin.

Author Tosin Daniel Jimoh


Files

* /app/solve.py you write last token lagos-room-transaction-true-isolation
* /app/data/sample inside container
* Dockerfile
* solution/solve.py oracle
* tests generate volumes

Completion Rates

Oracle three of three deterministic
Avocado zero to one of five due to lifecycle plus generation plus gain
Opus four of five GPT three of five

Model Analysis

No generation tracking shows stale image, no budget accrual loses fractional carry, no window reserve violates floor, no shape filter keeps round pores, no halo misses skirt, hardcoded offset fails ninety six one twenty eight, hardcoded gain fails twenty two percent.

Anti Cheating

Varied dims spacing random names secure runner blocks tests.

Tags lagos room transaction true isolation human story

Author Tosin Daniel Jimoh purple29th at meta.com
