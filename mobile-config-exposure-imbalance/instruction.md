# Setting

This project simulates MetaConfig-style mobile configuration reads and exposure logging across app sessions. Each read should produce an exposure event recording which variant the user saw. The current implementation produces wrong exposure logs because of bugs in the logging path.

# Input operations (/app/scenario.txt)

- SESSION_START <user> — begin a new session. Each new session for a user gets a monotonically increasing integer id (1, 2, 3, ...). A second SESSION_START while a session is active is a no-op.
- SESSION_END <user> — end the active session.
- READ <user> <config> <param> <branch> — the app reads a config param. <branch> is one of test, control, gate. All branches must produce an exposure.
- DEFAULT_READ <user> <config> <param> — the app reads a default value because no bucketing decision was made. Must NOT produce an exposure.
- VARIANT_FLIP <user> <config> <new_variant> — server-pushed variant change. Must invalidate the dedup cache so the next read on (user, current session, config) re-emits.
- OVERRIDE <user> <config> <variant> — engineer override. Sets the rendered variant and marks subsequent exposures as overridden=true.
- QUERY — append the full exposure log so far to /app/output.txt.

# Dedup semantics

Within the same (user, session, config), only the first read emits. A VARIANT_FLIP invalidates that dedup so the next read in the same session re-emits with the new variant. Different sessions are independent.

# Output format

On each QUERY, append the full exposure log so far. Each event renders as:

  user=<u> config=<c> variant=<v> session=<n> overridden=<true|false>

If there are no exposures yet, append exposures=[] followed by a newline.

# Where to start

Read and fix:
- /app/src/com/example/config/ExposureCache.kt
- /app/src/com/example/config/MobileConfig.kt

Do not modify Main.kt, SessionTracker.kt, or ExposureEvent.kt.

# Build / run

  cd /app
  kotlinc src/com/example/config/*.kt -include-runtime -d /app/sim.jar
  java -jar /app/sim.jar

The driver reads /app/scenario.txt and writes /app/output.txt.
