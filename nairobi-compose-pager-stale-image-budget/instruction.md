I am Wanjiku from Nairobi Kenya, I build fintech app for M-Pesa with Jetpack Compose horizontal pager showing loan cards. Each pager page has image that loads async. Binding updates title immediately and schedules image fetch at tick. Requirement cell only shows image fetched for current binding. Recycling or rebinding even to same item starts new binding. Stale fetches must be discarded but still consume queued RESOLVE token. Budget accrual num over den capped at cap with fractional carry.

I work on compose pager where cells reused. Bug is stale image shows for wrong card after fast swipe. Need to fix generation tracking.

Please make file at app/src/main/java/com/example/pager/PagerState.kt you fix.

There is sample in app/data - not needed. Hidden evaluation uses contract tests in src/com/example/test.

File layout android. No binary. Must handle generation counters and budget.

Energy not relevant, lifecycle correct handling.

If you get generation right you pass.

Coding rules Kotlin.

Print not needed, tests in src.

Author Tosin Daniel Jimoh purple29th
