Fix OpenAnvil manifest stale write bug.

Context: OpenAnvil provisions EC2 instances for each trial run, plus nested Tart VM (iOS) or Docker (Android). Each run writes a manifest JSON to S3 at `s3://bucket/prefix/runs/<run-id>/manifest.json` with fields:
- run_id: str
- gen: int monotonic generation token (incremented on each provision/recycle of same run_id, like RecyclerView bind token)
- last_heartbeat_ms: int epoch ms
- state: "running" | "succeeded" | "failed"
- ec2_instance_id: str

The web app at openanvil.ai lists active runs by reading S3 manifests. Current implementation is last-write-wins and has the bug reported in standup: "Web app runs continue to show running when instances have been shutdown. Web app relies on S3 files but files are stale."

Root cause (mirrors android-recycler-staleness):
- Run IDs are reused after recycle (like RecyclerView cells reused). Each provision bumps gen.
- Agent loop has async heartbeat PUT thread and grader final PUT race.
- Stale heartbeat with older gen or older last_heartbeat_ms overwrites terminal succeeded/failed back to running.
- Stale fetches must be discarded BUT still consume S3 write metric (RESOLVE token) for throttling/budget — exactly like recycler task: "Stale fetches must be discarded but still consume queued RESOLVE token."

Goal: Fix `/app/src/openanvil/manifest_store.py` class `ManifestStore`.

Current buggy `put(manifest)` just does `store[run_id] = manifest`.

Required correct logic (inspired by your accepted android-recycler-staleness):
1. If run_id not in store: store it, inc writes.
2. Else if incoming.gen < stored.gen: stale -> drop, inc stale_dropped and writes, do NOT overwrite.
3. Else if incoming.gen == stored.gen:
   - If incoming.last_heartbeat_ms < stored.last_heartbeat_ms: stale -> drop, inc stale_dropped + writes.
   - If stored.state in terminal ("succeeded","failed") and incoming.state == "running": stale -> drop (terminal must never be overwritten by running), inc stale_dropped + writes.
   - If incoming.state terminal and stored.state running: allow, overwrite.
   - If both terminal, higher last_heartbeat wins, but never downgrade succeeded->failed? Actually keep latest heartbeat.
   - If both running, higher last_heartbeat wins.
4. Else if incoming.gen > stored.gen: allow, overwrite (new provision wins even if heartbeat older, because gen is authoritative). Inc writes.

Other requirements:
- `stale_dropped` counts discards.
- `writes` counts ALL attempted PUTs including dropped (for RESOLVE token budgeting).
- `get(run_id)` returns current manifest or None.
- `list_active()` returns list of manifests where state=="running".
- Deterministic, no external libs, thread-safe not required (single-threaded replay).

Example replay that must work:
```
PUT gen1 running hb=100 runA
PUT gen2 running hb=200 runA (new provision, higher gen)
PUT gen1 stale running hb=150 runA -> drop (gen1 < gen2)
PUT gen3 succeeded hb=250 runA (grader terminal, gen3>gen2) -> overwrite
PUT gen2 stale running hb=210 runA -> drop (gen2 < gen3 AND terminal guard)
Final get(runA) must be gen3 succeeded hb=250, stale_dropped=2, writes=5, list_active()=[]
```

Second scenario:
```
PUT gen1 running hb=100 runB
PUT gen1 running hb=150 runB (same gen, hb newer) -> overwrite
PUT gen1 running hb=120 runB -> drop (older hb)
Final must be hb=150, stale=1, writes=3, active=[runB]
```

Hidden eval will test similar sequences with random run_ids, jittered heartbeats, mixed terminal guards, and budget token consumption.

Do not hardcode run_ids, do not list /tests. Work on /app/src/openanvil/manifest_store.py. Output not needed, tests import the class.

Allowed imports: only stdlib. Fix the file in place.

