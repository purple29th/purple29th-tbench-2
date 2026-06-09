"""Verification tests for event-loop-scheduler.

Each case feeds a sequence of operations into the agent's program
(/app/scheduler, reading stdin) and checks the firing order printed to stdout.
"""
import subprocess

import pytest

SCHEDULER = "/app/scheduler"

def run_scheduler(ops):
    proc = subprocess.run(
        [SCHEDULER],
        input=ops,
        capture_output=True,
        text=True,
        timeout=30,
    )
    assert proc.returncode == 0, f"scheduler exited {proc.returncode}; stderr:\n{proc.stderr}"
    return [line for line in proc.stdout.splitlines() if line.strip()]

CASES = {
    # Single schedule, single fire — callback fires.
    "basic": (
        "SCHEDULE a 100\nFIRE_DUE 100\n",
        ["a"],
    ),
    # Cancel before fire — nothing fires.
    "cancel_before_fire": (
        "SCHEDULE a 100\nCANCEL a\nFIRE_DUE 100\n",
        [],
    ),
    # Cancel after fire — already fired, cancel is a no-op.
    "cancel_after_fire": (
        "SCHEDULE a 100\nFIRE_DUE 100\nCANCEL a\n",
        ["a"],
    ),
    # Multiple due — fire in time order.
    "multiple_due": (
        "SCHEDULE a 200\nSCHEDULE b 100\nSCHEDULE c 150\nFIRE_DUE 200\n",
        ["b", "c", "a"],
    ),
    # Same ready time — FIFO on insertion order.
    "tie_breaking": (
        "SCHEDULE a 100\nSCHEDULE b 100\nSCHEDULE c 100\nFIRE_DUE 100\n",
        ["a", "b", "c"],
    ),
    # Cancel inside a window — only the non-cancelled fires.
    "cancel_in_window": (
        "SCHEDULE a 100\nSCHEDULE b 100\nCANCEL a\nFIRE_DUE 100\n",
        ["b"],
    ),
    # Not yet due — nothing fires.
    "not_yet_due": (
        "SCHEDULE a 200\nFIRE_DUE 100\n",
        [],
    ),
    # Cancel of unknown id — silent no-op.
    "cancel_unknown": (
        "CANCEL nonexistent\nSCHEDULE a 100\nFIRE_DUE 100\n",
        ["a"],
    ),
    # Across multiple FIRE_DUE rounds — cancel in first window applies to second.
    "cancel_across_rounds": (
        "SCHEDULE a 100\nSCHEDULE b 200\nFIRE_DUE 100\nCANCEL b\nFIRE_DUE 200\n",
        ["a"],
    ),
    # CANCEL queued during the same round it would have applied — cancel applies
    # at the START of the next FIRE_DUE, so a callback already in the
    # "ready set" when FIRE_DUE begins still fires this round.
    "cancel_queued_for_next_round": (
        "SCHEDULE a 100\nSCHEDULE b 100\nFIRE_DUE 100\nCANCEL c\nSCHEDULE c 100\nFIRE_DUE 100\n",
        ["a", "b"],
    ),
    # Schedule "for now" between FIRE_DUEs — the new schedule fires in the
    # next FIRE_DUE, not retroactively in a previous one.
    "schedule_after_fire_due": (
        "SCHEDULE a 100\nFIRE_DUE 100\nSCHEDULE b 100\nFIRE_DUE 100\n",
        ["a", "b"],
    ),
    # Re-schedule after cancel: cancel is queued, takes effect at next FIRE_DUE.
    # If the same id is re-scheduled before that FIRE_DUE, both the cancel and
    # the new schedule are pending; the queued cancel removes ALL pending
    # entries for that id, including the freshly-scheduled one.
    "cancel_then_reschedule_same_id": (
        "SCHEDULE a 100\nCANCEL a\nSCHEDULE a 100\nFIRE_DUE 100\n",
        [],
    ),
}

@pytest.mark.parametrize("name", list(CASES.keys()))
def test_scheduler(name):
    ops, expected = CASES[name]
    assert run_scheduler(ops) == expected
