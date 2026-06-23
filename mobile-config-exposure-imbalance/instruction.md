# Setting

This project simulates MetaConfig-style mobile configuration reads and exposure logging. A config read may produce an exposure, but exposures are not written immediately: they are buffered and released later under a shared logging budget, so that when the budget is tight, higher-priority configs win. The current implementation logs the wrong exposures because of bugs in the logging path.

# Input operations (/app/scenario.txt)

- SESSION_START <user> — begin a new session. Each new session for a user gets a monotonically increasing integer id (1, 2, 3, ...). A second SESSION_START while a session is active is a no-op.
- SESSION_END <user> — end the active session.
- READ <user> <config> <param> <branch> — the app reads a config param. <branch> is one of test, control, gate; every branch is exposure-worthy (subject to dedup). A read with no active session does nothing.
- DEFAULT_READ <user> <config> <param> — a default read because no bucketing decision was made. Never produces an exposure.
- VARIANT_FLIP <user> <config> <new_variant> — server-pushed variant change for (user, config). Also invalidates the dedup entry so the next read on (user, current session, config) re-qualifies.
- OVERRIDE <user> <config> <variant> — engineer override for (user, config): sets the rendered variant and marks exposures for that (user, config) as overridden=true.
- PRIORITY <config> <n> — set the integer flush priority of <config> (default 0 until set; higher wins when the budget is scarce).
- GRANT <n> — add <n> credits to the shared logging budget.
- FLUSH — release buffered exposures under the current budget (see below).
- QUERY — append the log written so far to /app/output.txt.

# Dedup

Within the same (user, session, config), only the first qualifying read buffers an exposure; later reads of the same (user, session, config) are suppressed. A VARIANT_FLIP clears that dedup entry so the next read in the same session buffers again. Sessions are independent. Dedup is keyed by session.

# Variant resolution (bound when the read is buffered)

The logged variant is NOT the <branch>. When a read is buffered, its variant is fixed then, for that (user, config), as: an active OVERRIDE variant (with overridden=true), else the most recent VARIANT_FLIP variant, else the default "control". Overrides and flips belong to (user, config) and persist across sessions. Because the variant is fixed at buffer time, an OVERRIDE or VARIANT_FLIP that happens after a read is buffered does not change that already-buffered exposure.

# Buffering, budget, and flush

A qualifying read does not log immediately — it appends a pending exposure to a single global buffer, tagged with the order it arrived. GRANT adds credits to one shared budget (starts at 0, persists for the whole run). FLUSH releases pending exposures:

1. Sort all pending exposures by each config's EFFECTIVE priority descending, where effective priority = the config's current priority minus its fatigue (fatigue starts at 0). Break ties by arrival order (earliest first).
2. Walk that order: while the budget is at least 1, spend 1 credit and LOG the exposure, and increase that config's fatigue by 1 (so each logged exposure makes its config one step lower-priority for all future flushes); once the budget reaches 0, every remaining pending exposure stays buffered for a later FLUSH.

Deferred exposures remain pending and are reconsidered at the next FLUSH, re-sorted against whatever is pending then by effective priority (so both a priority change and accumulated fatigue between flushes reorder them). Fatigue persists for the whole run and is never reset. The budget is shared across all configs and never resets.

# Output format

On each QUERY, append the log so far. If nothing has been logged, append exactly:

  exposures=[]

(followed by a newline). Otherwise:

  exposures=[
    user=<u> config=<c> variant=<v> session=<n> overridden=<true|false>,
    user=<u> config=<c> variant=<v> session=<n> overridden=<true|false>
  ]

A line "exposures=[", one line per logged event prefixed with two spaces, events separated by a trailing comma, a closing "]" on its own line, then a newline. Events appear in the order they were LOGGED (i.e. flush-release order across all flushes), not the order they were read. The verifier compares output byte-for-byte.

# What you need to do

Fix these two files:
- /app/src/com/example/config/ExposureCache.kt
- /app/src/com/example/config/MobileConfig.kt

Do not modify Main.kt, SessionTracker.kt, or ExposureEvent.kt.

The verifier compiles and runs your fixed code automatically; just edit the two files so the simulator produces the correct exposure log.

# Reference build command (for local debugging only)

  cd /app
  kotlinc src/com/example/config/*.kt -include-runtime -d /app/sim.jar
  java -jar /app/sim.jar

The driver reads /app/scenario.txt and writes /app/output.txt.
