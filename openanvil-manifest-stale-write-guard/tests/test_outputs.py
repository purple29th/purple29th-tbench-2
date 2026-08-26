import sys, os, ast

sys.path.insert(0, "/app/src")
sys.path.insert(0, "/app")
from openanvil.manifest_store import ManifestStore

ALLOWED_MODULES = {"typing", "collections", "dataclasses"}
# we allow stdlib only, but not enforce strict here as this is not from-scratch binary task


def test_replay_example_1():
    store = ManifestStore()
    # replay from instruction
    store.put(
        {
            "run_id": "runA",
            "gen": 1,
            "last_heartbeat_ms": 100,
            "state": "running",
            "ec2_instance_id": "i-1",
        }
    )
    store.put(
        {
            "run_id": "runA",
            "gen": 2,
            "last_heartbeat_ms": 200,
            "state": "running",
            "ec2_instance_id": "i-2",
        }
    )
    store.put(
        {
            "run_id": "runA",
            "gen": 1,
            "last_heartbeat_ms": 150,
            "state": "running",
            "ec2_instance_id": "i-1",
        }
    )  # stale
    store.put(
        {
            "run_id": "runA",
            "gen": 3,
            "last_heartbeat_ms": 250,
            "state": "succeeded",
            "ec2_instance_id": "i-3",
        }
    )
    store.put(
        {
            "run_id": "runA",
            "gen": 2,
            "last_heartbeat_ms": 210,
            "state": "running",
            "ec2_instance_id": "i-2",
        }
    )  # stale
    final = store.get("runA")
    assert final is not None
    assert final["gen"] == 3
    assert final["state"] == "succeeded"
    assert final["last_heartbeat_ms"] == 250
    assert store.stale_dropped == 2, (
        f"expected 2 stale dropped got {store.stale_dropped}"
    )
    assert store.writes == 5
    assert store.list_active() == []


def test_replay_example_2():
    store = ManifestStore()
    store.put(
        {
            "run_id": "runB",
            "gen": 1,
            "last_heartbeat_ms": 100,
            "state": "running",
            "ec2_instance_id": "i-1",
        }
    )
    store.put(
        {
            "run_id": "runB",
            "gen": 1,
            "last_heartbeat_ms": 150,
            "state": "running",
            "ec2_instance_id": "i-1",
        }
    )
    store.put(
        {
            "run_id": "runB",
            "gen": 1,
            "last_heartbeat_ms": 120,
            "state": "running",
            "ec2_instance_id": "i-1",
        }
    )
    final = store.get("runB")
    assert final["last_heartbeat_ms"] == 150
    assert store.stale_dropped == 1
    assert store.writes == 3
    assert len(store.list_active()) == 1


def test_terminal_guard():
    store = ManifestStore()
    store.put(
        {
            "run_id": "runC",
            "gen": 1,
            "last_heartbeat_ms": 100,
            "state": "running",
            "ec2_instance_id": "i-1",
        }
    )
    store.put(
        {
            "run_id": "runC",
            "gen": 1,
            "last_heartbeat_ms": 200,
            "state": "succeeded",
            "ec2_instance_id": "i-1",
        }
    )
    store.put(
        {
            "run_id": "runC",
            "gen": 1,
            "last_heartbeat_ms": 250,
            "state": "running",
            "ec2_instance_id": "i-1",
        }
    )  # should not overwrite terminal
    final = store.get("runC")
    assert final["state"] == "succeeded"
    assert final["last_heartbeat_ms"] == 200
    assert store.stale_dropped == 1
    assert store.writes == 3
    assert store.list_active() == []


def test_gen_authoritative():
    store = ManifestStore()
    store.put(
        {
            "run_id": "runD",
            "gen": 5,
            "last_heartbeat_ms": 1000,
            "state": "running",
            "ec2_instance_id": "i-10",
        }
    )
    store.put(
        {
            "run_id": "runD",
            "gen": 6,
            "last_heartbeat_ms": 100,
            "state": "running",
            "ec2_instance_id": "i-11",
        }
    )  # higher gen wins even if hb older
    final = store.get("runD")
    assert final["gen"] == 6
    assert final["last_heartbeat_ms"] == 100
    assert store.stale_dropped == 0


def test_multi_run_isolation():
    store = ManifestStore()
    store.put(
        {
            "run_id": "a",
            "gen": 1,
            "last_heartbeat_ms": 100,
            "state": "running",
            "ec2_instance_id": "i-1",
        }
    )
    store.put(
        {
            "run_id": "b",
            "gen": 1,
            "last_heartbeat_ms": 100,
            "state": "running",
            "ec2_instance_id": "i-2",
        }
    )
    store.put(
        {
            "run_id": "a",
            "gen": 1,
            "last_heartbeat_ms": 50,
            "state": "running",
            "ec2_instance_id": "i-1",
        }
    )  # stale for a
    assert store.get("a")["last_heartbeat_ms"] == 100
    assert store.get("b")["last_heartbeat_ms"] == 100
    assert store.stale_dropped == 1
    assert len(store.list_active()) == 2


def test_randomized_replay():
    # deterministic randomized similar to jitter
    store = ManifestStore()
    # 3 runs, mixed
    seq = [
        {
            "run_id": "r1",
            "gen": 1,
            "last_heartbeat_ms": 10,
            "state": "running",
            "ec2_instance_id": "i-1",
        },
        {
            "run_id": "r2",
            "gen": 1,
            "last_heartbeat_ms": 20,
            "state": "running",
            "ec2_instance_id": "i-2",
        },
        {
            "run_id": "r1",
            "gen": 2,
            "last_heartbeat_ms": 30,
            "state": "running",
            "ec2_instance_id": "i-3",
        },
        {
            "run_id": "r1",
            "gen": 1,
            "last_heartbeat_ms": 15,
            "state": "running",
            "ec2_instance_id": "i-1",
        },  # stale
        {
            "run_id": "r2",
            "gen": 1,
            "last_heartbeat_ms": 25,
            "state": "succeeded",
            "ec2_instance_id": "i-2",
        },
        {
            "run_id": "r2",
            "gen": 1,
            "last_heartbeat_ms": 30,
            "state": "running",
            "ec2_instance_id": "i-2",
        },  # terminal guard
        {
            "run_id": "r3",
            "gen": 1,
            "last_heartbeat_ms": 5,
            "state": "running",
            "ec2_instance_id": "i-4",
        },
    ]
    for m in seq:
        store.put(m)
    assert store.get("r1")["gen"] == 2 and store.get("r1")["state"] == "running"
    assert store.get("r2")["state"] == "succeeded"
    assert store.get("r3")["state"] == "running"
    assert store.stale_dropped == 2  # r1 gen1 old + r2 running after succeeded
    assert store.writes == 7
    active_ids = set(x["run_id"] for x in store.list_active())
    assert active_ids == {"r1", "r3"}


def test_writes_consume_even_when_dropped():
    # inspired by android-recycler: stale must consume RESOLVE token
    store = ManifestStore()
    store.put(
        {
            "run_id": "runX",
            "gen": 1,
            "last_heartbeat_ms": 100,
            "state": "running",
            "ec2_instance_id": "i-1",
        }
    )
    for i in range(1, 5):
        store.put(
            {
                "run_id": "runX",
                "gen": 1,
                "last_heartbeat_ms": 100 + i,
                "state": "running",
                "ec2_instance_id": "i-1",
            }
        )
        store.put(
            {
                "run_id": "runX",
                "gen": 1,
                "last_heartbeat_ms": 100,
                "state": "running",
                "ec2_instance_id": "i-1",
            }
        )  # stale older hb
    # writes = 9, dropped =4 (first put not dropped)
    assert store.writes == 9
    assert store.stale_dropped == 4
    assert store.get("runX")["last_heartbeat_ms"] == 104
