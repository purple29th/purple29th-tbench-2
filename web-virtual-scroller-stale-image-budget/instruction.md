web virtual scroller stale image with decode budget

my web perf lab has a virtual list like react window. small pool of dom nodes reused while scrolling. mounting a node sets its title right away and schedules an async image load due on a later tick. in prod we see wrong image, a load scheduled for an item the node used to show lands after node was unmounted or rebound to another item, and when several loads land on same tick a superseded one overwrites correct image. bug lives in pool that handles binding token and decode budget.

this is inspired by android-recycler-staleness from my accepted portfolio, that one was kotlin recyclerview cell pool with similar staleness and budget, but this time it is web frontend, different operations and numbers, not a copy, to fill low coverage web_frontend which is red in taxonomy dashboard.

input operations are one per line from stdin.

MOUNT nodeId itemId title dueAt - attach node to item, set title now, schedule image load for that item due at dueAt.
UPDATE_TITLE nodeId newTitle - change title of bound node, no load.
PREFETCH nodeId dueAt - schedule another load for node's current binding due at dueAt. if node unbound does nothing.
UNMOUNT nodeId - detach node, becomes unbound. future loads for old binding must not touch it.
BUDGET num den cap - put decoder under budget. without this decoding is unlimited. see expected.
RESOLVE itemId url - queue deterministic url for next pending load of that item. if no queued resolution, use auto:itemId fallback.
ADVANCE now - advance logical time to now and process loads where dueAt <= now. when several due, process in scheduling order then by nodeId.
INSPECT nodeId - record snapshot to print at end in inspection order.

output after all input, one line per INSPECT in order.

bound node: nodeId item=itemId title=title image=urlOrNONE
unbound with no image: nodeId unbound
unbound that still holds image (bug): nodeId unbound image=url - correct code never produces this unless stale corrupted it.

expected

a node must only ever display image fetched for its current binding. unmounting a node or mounting it again to different item or same itemId again all start new binding generation. any load scheduled under old generation must not write to node even if itemId same. when multiple loads for same node due on same tick, only the one belonging to binding still valid at write time may apply, once node has taken its image for current binding, later superseded result on same tick must not overwrite it.

pending loads are consumed in scheduling order. handling a load always consumes next queued resolution for its item or auto:itemId fallback when none remain. this holds even when load is stale, stale result is consumed and discarded never put back, so later valid load does not get it.

when BUDGET set, decoding costs one credit. loader accrues credits continuously at num/den per tick of elapsed time, single running quantity that keeps fractional part across ticks rather than recomputed per tick, capped at cap. on ADVANCE after crediting elapsed time, due loads are taken in usual order and each valid non stale pays one credit to decode, when next valid in order cannot afford credit, stop decoding for that tick and that load and everything behind it stays pending for later tick. stale never decodes and costs nothing but still consumes queued resolution. with no BUDGET op budget is unlimited.

contract tests live in /app/tests/test_outputs.py, run with pytest -v or npm test. we also have /app/src/main.py which reads scenario.json.

run with python src/main.py < scenario.json > output.txt, verifier checks output and pytest.

do not hardcode any urls from sample, hidden grading uses other items and ticks.
