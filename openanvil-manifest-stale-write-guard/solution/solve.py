# Reference correct implementation
class ManifestStore:
    def __init__(self):
        self._store = {}
        self._writes = 0
        self._stale_dropped = 0

    def put(self, manifest):
        run_id = manifest["run_id"]
        self._writes += 1
        if run_id not in self._store:
            self._store[run_id] = manifest
            return
        stored = self._store[run_id]
        # gen check: authoritative
        if manifest["gen"] < stored["gen"]:
            self._stale_dropped += 1
            return
        if manifest["gen"] > stored["gen"]:
            self._store[run_id] = manifest
            return
        # same gen
        # heartbeat recency
        if manifest["last_heartbeat_ms"] < stored["last_heartbeat_ms"]:
            self._stale_dropped += 1
            return
        # terminal guard: terminal must never be overwritten by running
        terminal = {"succeeded", "failed"}
        if stored["state"] in terminal and manifest["state"] == "running":
            self._stale_dropped += 1
            return
        # allow overwrite (running->terminal, terminal->terminal with newer hb, running->running newer hb)
        self._store[run_id] = manifest

    def get(self, run_id):
        return self._store.get(run_id)

    def list_active(self):
        return [m for m in self._store.values() if m.get("state") == "running"]

    @property
    def writes(self):
        return self._writes

    @property
    def stale_dropped(self):
        return self._stale_dropped
