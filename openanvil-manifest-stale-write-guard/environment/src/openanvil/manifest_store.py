# BUGGY VERSION - agent must fix
class ManifestStore:
    def __init__(self):
        self._store = {}
        self._writes = 0
        self._stale_dropped = 0
    def put(self, manifest):
        self._store[manifest["run_id"]] = manifest
        self._writes += 1
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
