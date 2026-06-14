# Setting

A simulator for a versioned configuration store. A pusher publishes new config versions; live readers fetch current values; snapshot readers hold a stable view across pushes; observers receive notifications when keys they care about change. The current ConfigStore in /app/src/com/example/cfgpush/ConfigStore.kt produces wrong output for several scenarios. Fix it.

# Operations (/app/scenario.txt)

- PUSH <version> <key=value,key=value,...> — apply the listed updates and set the store's current version to <version>. Each push is one unit of change.
- READ <reader_id> <key> — a live reader fetches a value. Live reads see the current store state and the reader observes the current version.
- BEGIN_SNAPSHOT <reader_id> — the reader captures a stable view of the store as of the current version.
- READ_FROM_SNAPSHOT <reader_id> <key> — the reader fetches a value from its captured view. A snapshot read is a separate read mode from a live read.
- END_SNAPSHOT <reader_id> — the reader discards its captured view.
- SUBSCRIBE <observer_id> <key,key,...> — register the observer for a set of keys.
- UNSUBSCRIBE <observer_id> — the observer is gone; subsequent pushes do not affect it.
- QUERY — append the simulator's current state to /app/output.txt.

# Notification semantics

A push that changes one or more keys produces a single notification entry per affected observer, where "affected" means at least one of the observer's subscribed keys appears in the push. The entry records the observer id, the keys from the push that the observer cares about (sorted, comma-separated), and the new version.

# State each QUERY shows

- The current store contents and version.
- For each reader that has done at least one live READ, the version it observed on its most recent live read.
- The full notification log emitted so far.

# QUERY output format

For each QUERY, append:

  store version=<n>
    <key>=<value>
    ...
  readers:
    <reader_id> version=<n>
    ...
  notifications:
    <entry>
    ...

Within a QUERY: store keys sorted ascending by key, readers sorted ascending by id, notifications in emission order. Each notification entry is rendered as `<observer_id>:keys=<csv>:v<version>`.

# What you need to do

Fix /app/src/com/example/cfgpush/ConfigStore.kt. Do not modify Main.kt, Observer.kt, or Snapshot.kt. The verifier compiles and runs your fixed code automatically.

# Reference build (for local debugging only)

  cd /app
  kotlinc src/com/example/cfgpush/*.kt -include-runtime -d /app/sim.jar
  java -jar /app/sim.jar

The driver reads /app/scenario.txt and writes /app/output.txt.
