# Setting

A simulator for a versioned configuration store with readers, snapshot readers, and observers. A pusher publishes new config versions; readers fetch values; snapshot readers hold a stable view across pushes; observers receive notifications when keys they care about change. The current ConfigStore implementation has bugs that produce wrong output across all three concerns. Fix /app/src/com/example/cfgpush/ConfigStore.kt.

# Input operations (/app/scenario.txt)

The driver reads one operation per line:

- PUSH <version> <key=value,key=value,...> — apply all listed key/value updates and set the store's current version. Observers whose subscribed keys overlap with this push's changed keys receive a single notification entry recording (observer id, intersected keys sorted, version).
- READ <reader_id> <key> — reader fetches the current live value of <key>. The reader's "observed version" is updated to the store's current version.
- BEGIN_SNAPSHOT <reader_id> — capture the store's current values and version under <reader_id>. Subsequent READ_FROM_SNAPSHOT for this id returns values from this captured view, not from the live store.
- READ_FROM_SNAPSHOT <reader_id> <key> — return the value of <key> as it was when BEGIN_SNAPSHOT was taken. Does not affect the reader's observed version.
- END_SNAPSHOT <reader_id> — drop the captured snapshot.
- SUBSCRIBE <observer_id> <key,key,...> — register an observer for the comma-separated set of keys.
- UNSUBSCRIBE <observer_id> — fully deregister the observer; subsequent pushes must not produce any further notifications for that observer.
- QUERY — append a snapshot of the simulator state to /app/output.txt.

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

Within a QUERY:
- store keys are sorted ascending by key.
- readers are sorted ascending by reader id.
- notifications are listed in the order they were emitted.

A notification entry is rendered as `<observer_id>:keys=<csv>:v<version>` where <csv> is the sorted, comma-separated list of keys included in that notification.

# What you need to do

Fix /app/src/com/example/cfgpush/ConfigStore.kt. Do not modify Main.kt, Observer.kt, or Snapshot.kt. The verifier compiles and runs your fixed code automatically.

# Reference build (for local debugging only)

  cd /app
  kotlinc src/com/example/cfgpush/*.kt -include-runtime -d /app/sim.jar
  java -jar /app/sim.jar

The driver reads /app/scenario.txt and writes /app/output.txt.
