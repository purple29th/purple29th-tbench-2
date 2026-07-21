This is a simulator for a versioned config store, the kind that pushes new values to readers and notifies observers. Right now it logs the wrong state in a few cases. Fix the ConfigStore file so it matches the behavior here. Do not change the main file or observer or snapshot files. The verifier builds and runs it.

The driver reads a scenario file one operation per line. PUSH applies updates and sets current version. READ is a live read that sees current store and remembers version observed. BEGIN SNAPSHOT captures a stable view as of current version, READ FROM SNAPSHOT reads from that view, END SNAPSHOT discards it. SUBSCRIBE registers an observer for a set of keys, UNSUBSCRIBE removes it, and QUERY appends current state to output file.

A push that changes keys produces one notification per affected observer, affected means at least one of its subscribed keys appears in push. Each notification shows observer id, matching keys from that push sorted and comma separated, and new version. If push changes nothing overlapping interest, no notification.

Each QUERY appends store version and keys sorted, then readers that have done at least one live READ with version they last observed, then notifications in emission order. Store keys sorted ascending, readers sorted ascending, notifications in emission order. Each notification renders as observer id, keys, version. Unsubscribed observers get no further notifications.

For local debugging only, from app folder run kotlinc on all kt files include runtime to app jar then java jar app jar.
