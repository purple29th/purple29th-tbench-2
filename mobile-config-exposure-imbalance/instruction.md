# Setting

This project simulates MetaConfig-style mobile configuration reads and exposure logging across app sessions. Each qualifying read produces an exposure event recording which variant the user was shown. The current implementation logs the wrong exposures because of bugs in the logging path.

# Input operations (/app/scenario.txt)

- SESSION_START <user> — begin a new session. Each new session for a user gets a monotonically increasing integer id (1, 2, 3, ...). A second SESSION_START while a session is already active is a no-op.
- SESSION_END <user> — end the active session.
- READ <user> <config> <param> <branch> — the app reads a config param. <branch> is one of test, control, gate. Every branch is exposure-worthy (subject to the dedup rule below).
- DEFAULT_READ <user> <config> <param> — the app reads a default value because no bucketing decision was made. This never produces an exposure.
- VARIANT_FLIP <user> <config> <new_variant> — a server-pushed variant change for that (user, config). It also invalidates the dedup entry so the next read on (user, current session, config) re-emits.
- OVERRIDE <user> <config> <variant> — an engineer override for that (user, config). Sets the rendered variant and marks subsequent exposures for that (user, config) as overridden=true.
- QUERY — append the full exposure log so far to /app/output.txt.

# Dedup semantics

Within the same (user, session, config), only the first read emits an exposure; later reads of the same (user, session, config) are suppressed. A VARIANT_FLIP invalidates that dedup entry, so the next read in the same session re-emits. Sessions are independent: the first read in a new session emits again. Dedup is keyed by session.

# Which variant gets logged

The logged variant is NOT the <branch> token. The branch only decides whether a read is exposure-worthy (every READ branch is; DEFAULT_READ is not). The variant written into an exposure is resolved, for that (user, config), in this order:

1. If an OVERRIDE is in effect for (user, config), use the override variant, and set overridden=true.
2. Otherwise, if a VARIANT_FLIP has been applied for (user, config), use the most recently flipped variant, with overridden=false.
3. Otherwise, use the default variant "control", with overridden=false.

Overrides and variant flips belong to (user, config) and persist across sessions — one set in an earlier session still applies to reads in later sessions until changed. (Dedup, by contrast, is per session.)

# Output format

On each QUERY, append the full exposure log so far. If there are no exposures yet, append exactly:

  exposures=[]

(followed by a newline). Otherwise, render the events as:

  exposures=[
    user=<u> config=<c> variant=<v> session=<n> overridden=<true|false>,
    user=<u> config=<c> variant=<v> session=<n> overridden=<true|false>
  ]

That is: a line "exposures=[", then one line per event prefixed with two spaces, events separated by a trailing comma, then a closing "]" on its own line, then a newline. Events appear in the order they were emitted. The verifier compares output byte-for-byte.

# What you need to do

Fix these two files:
- /app/src/com/example/config/ExposureCache.kt
- /app/src/com/example/config/MobileConfig.kt

Do not modify Main.kt, SessionTracker.kt, or ExposureEvent.kt.

The verifier compiles and runs your fixed code automatically. You do not need to compile or run anything yourself — just edit the two files above so the simulator produces the correct exposure log.

# Reference build command (for local debugging only)

  cd /app
  kotlinc src/com/example/config/*.kt -include-runtime -d /app/sim.jar
  java -jar /app/sim.jar

The driver reads /app/scenario.txt and writes /app/output.txt.
