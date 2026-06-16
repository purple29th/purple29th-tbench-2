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
    "basic": (
        "SCHEDULE a 100\nFIRE_DUE 100\n",
        ["a"],
    ),
    "cancel_before_fire": (
        "SCHEDULE a 100\nCANCEL a\nFIRE_DUE 100\n",
        [],
    ),
    "cancel_after_fire": (
        "SCHEDULE a 100\nFIRE_DUE 100\nCANCEL a\n",
        ["a"],
    ),
    "multiple_due": (
        "SCHEDULE a 200\nSCHEDULE b 100\nSCHEDULE c 150\nFIRE_DUE 200\n",
        ["b", "c", "a"],
    ),
    "tie_breaking": (
        "SCHEDULE a 100\nSCHEDULE b 100\nSCHEDULE c 100\nFIRE_DUE 100\n",
        ["a", "b", "c"],
    ),
    "cancel_in_window": (
        "SCHEDULE a 100\nSCHEDULE b 100\nCANCEL a\nFIRE_DUE 100\n",
        ["b"],
    ),
    "not_yet_due": (
        "SCHEDULE a 200\nFIRE_DUE 100\n",
        [],
    ),
    "cancel_unknown": (
        "CANCEL nonexistent\nSCHEDULE a 100\nFIRE_DUE 100\n",
        ["a"],
    ),
    "cancel_across_rounds": (
        "SCHEDULE a 100\nSCHEDULE b 200\nFIRE_DUE 100\nCANCEL b\nFIRE_DUE 200\n",
        ["a"],
    ),
    "cancel_queued_for_next_round": (
        "SCHEDULE a 100\nSCHEDULE b 100\nFIRE_DUE 100\nCANCEL c\nSCHEDULE c 100\nFIRE_DUE 100\n",
        ["a", "b"],
    ),
    "schedule_after_fire_due": (
        "SCHEDULE a 100\nFIRE_DUE 100\nSCHEDULE b 100\nFIRE_DUE 100\n",
        ["a", "b"],
    ),
    "cancel_then_reschedule_same_id": (
        "SCHEDULE a 100\nCANCEL a\nSCHEDULE a 100\nFIRE_DUE 100\n",
        [],
    ),
    # --- recurring timers ---
    "recurring_basic": (
        "SCHEDULE r 100 50\nFIRE_DUE 100\n",
        ["r"],
    ),
    "recurring_fires_once_when_overdue": (
        "SCHEDULE r 100 50\nFIRE_DUE 250\n",
        ["r"],
    ),
    "recurring_realigns_after_overdue": (
        "SCHEDULE r 100 50\nFIRE_DUE 250\nFIRE_DUE 280\n",
        ["r"],
    ),
    "recurring_next_round": (
        "SCHEDULE r 100 50\nFIRE_DUE 100\nFIRE_DUE 150\n",
        ["r", "r"],
    ),
    "recurring_multi_period": (
        "SCHEDULE r 100 100\nFIRE_DUE 100\nFIRE_DUE 250\n",
        ["r", "r"],
    ),
    "recurring_cancelled_stops": (
        "SCHEDULE r 100 50\nFIRE_DUE 100\nCANCEL r\nFIRE_DUE 200\n",
        ["r"],
    ),
    "recurring_with_oneshot_order": (
        "SCHEDULE r 100 100\nSCHEDULE a 150\nFIRE_DUE 200\n",
        ["r", "a"],
    ),
    "two_recurring_interleaved": (
        "SCHEDULE x 100 100\nSCHEDULE y 150 100\nFIRE_DUE 320\nFIRE_DUE 360\n",
        ["x", "y", "y"],
    ),
    # --- coalescing: at most one pending timer per id ---
    # Scheduling the same id twice does not create two runs.
    "coalesce_no_duplicate": (
        "SCHEDULE a 100\nSCHEDULE a 100\nFIRE_DUE 100\n",
        ["a"],
    ),
    # Re-scheduling retargets to the earlier time.
    "coalesce_earlier_time_wins": (
        "SCHEDULE a 100\nSCHEDULE a 200\nFIRE_DUE 150\n",
        ["a"],
    ),
    # A coalesced timer keeps its original place in the running order.
    "coalesce_keeps_order": (
        "SCHEDULE a 100\nSCHEDULE b 100\nSCHEDULE a 100\nFIRE_DUE 100\n",
        ["a", "b"],
    ),
    # Cancel clears the single coalesced timer.
    "coalesce_then_cancel": (
        "SCHEDULE a 100\nSCHEDULE a 50\nCANCEL a\nFIRE_DUE 100\n",
        [],
    ),
    # A plain re-schedule drops a previously-set period (back to one-shot).
    "coalesce_recurring_to_oneshot": (
        "SCHEDULE r 100 50\nSCHEDULE r 100\nFIRE_DUE 100\nFIRE_DUE 200\n",
        ["r"],
    ),
    # A re-schedule with a period turns a one-shot into a repeater.
    "coalesce_oneshot_to_recurring": (
        "SCHEDULE r 100\nSCHEDULE r 100 50\nFIRE_DUE 100\nFIRE_DUE 150\n",
        ["r", "r"],
    ),
}

@pytest.mark.parametrize("name", list(CASES.keys()))
def test_scheduler(name):
    ops, expected = CASES[name]
    assert run_scheduler(ops) == expected
