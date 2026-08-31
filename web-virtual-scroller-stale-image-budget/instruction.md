# Web Virtual Scroller – Stale Image Loads Must Not Corrupt Reused Nodes

## Setting

You have a virtual list like React Window. A small pool of DOM nodes is reused as the user scrolls. Mounting a node sets its title right away and schedules an async image load that will complete on a later tick. In production we see wrong images: a load that was scheduled for an item a node used to show sometimes lands after the node has been unmounted or rebound to another item. When several loads become due on the same tick, a superseded load can overwrite the correct image. The bug lives in the JS pool that manages binding tokens and the decode budget.

This task is inspired by `android-recycler-staleness` from your accepted portfolio, but moved to web frontend and with different operations and budget wording so it is not a replication. Your portfolio was heavy on scientific and Android, this one fills low coverage `web_frontend`.

## Input operations (stdin)

One operation per line, read from stdin:

- `MOUNT <nodeId> <itemId> <title> <dueAt>` – attach node to item, set title immediately, schedule image load for that item due at `dueAt` tick.
- `UPDATE_TITLE <nodeId> <newTitle>` – change title of currently bound node, does not schedule a load.
- `PREFETCH <nodeId> <dueAt>` – schedule another image load for the node's current binding due at `dueAt`. If node is unbound, does nothing.
- `UNMOUNT <nodeId>` – detach node from any item, it becomes unbound. Future loads for its old binding must not touch it.
- `BUDGET <num> <den> <cap>` – put the image decoder under a budget. Without this, decoding is unlimited. See expected behavior.
- `RESOLVE <itemId> <url>` – queue a deterministic URL that will be used for the next pending load of that itemId. If no queued resolution exists, use fallback `auto:<itemId>`.
- `ADVANCE <now>` – advance logical time to `now` and process all loads where `dueAt <= now`. When several are due, process in order of scheduling time, then by `nodeId` to break ties.
- `INSPECT <nodeId>` – record a snapshot of the node's state to be printed at the end, in inspection order.

## Output format

After processing all input, print one line per `INSPECT` in the order they appeared:

- Bound node: `<nodeId> item=<itemId> title=<title> image=<urlOrNONE>`
- Unbound node with no image: `<nodeId> unbound`
- Unbound node that still holds an image (bug): `<nodeId> unbound image=<url>` – correct implementation never produces this unless a stale load corrupted it.

## Expected behavior

A node must only display an image that was fetched for its current binding. Unmounting a node, or mounting it again to a different item, or remounting to the same itemId again, all start a new binding generation. Any load scheduled under an old generation must not write to the node, even if the itemId is the same. When multiple loads for the same node become due on the same tick, only the one that belongs to the binding still valid at write time may apply. Once a node has taken its image for the current binding, a later superseded result on that same tick must not overwrite it.

Pending loads that become due are consumed in scheduling order. Handling a load always consumes the next queued resolution for its item, or the `auto:<itemId>` fallback when none remain. This holds even when the load is stale: a stale result is consumed and discarded, never put back, so a later valid load does not get it.

When `BUDGET` has been set, decoding an image costs one credit. Credits accrue continuously at `num/den` credits per tick of elapsed time, as a single running quantity that keeps its fractional part across ticks, capped at `cap`. On `ADVANCE`, first add `elapsed * num / den` to budget (integer division after multiply), cap it, then process due loads in order. Each valid, non-stale load pays one credit to decode. When the next valid load in order cannot afford a credit, stop decoding for that tick and leave that load and everything behind it pending for a later tick. Stale loads never decode and cost nothing, but they still consume their queued resolution.

## Contract tests

Contract tests that capture the intended behavior live in:

  /app/test/contract.test.js

Run them with:

  npm test

Your fix should make all contract tests pass without cheating by editing test files.

## Build and run

Run the program with:

  node /app/src/index.js < /app/scenario.json > /app/output.txt

The verifier checks `output.txt` against expected snapshots.
