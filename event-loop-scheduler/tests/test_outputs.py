"""Verification tests for event-loop-scheduler."""

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
    "basic": ("SCHEDULE a 100\nFIRE_DUE 100\n", ["a"]),
    "cancel_before_fire": ("SCHEDULE a 100\nCANCEL a\nFIRE_DUE 100\n", []),
    "cancel_after_fire": ("SCHEDULE a 100\nFIRE_DUE 100\nCANCEL a\n", ["a"]),
    "multiple_due": ("SCHEDULE a 200\nSCHEDULE b 100\nSCHEDULE c 150\nFIRE_DUE 200\n", ["b", "c", "a"]),
    "tie_breaking": ("SCHEDULE a 100\nSCHEDULE b 100\nSCHEDULE c 100\nFIRE_DUE 100\n", ["a", "b", "c"]),
    "cancel_in_window": ("SCHEDULE a 100\nSCHEDULE b 100\nCANCEL a\nFIRE_DUE 100\n", ["b"]),
    "not_yet_due": ("SCHEDULE a 200\nFIRE_DUE 100\n", []),
    "cancel_unknown": ("CANCEL nonexistent\nSCHEDULE a 100\nFIRE_DUE 100\n", ["a"]),
    "cancel_across_rounds": ("SCHEDULE a 100\nSCHEDULE b 200\nFIRE_DUE 100\nCANCEL b\nFIRE_DUE 200\n", ["a"]),
    "cancel_queued_for_next_round": ("SCHEDULE a 100\nSCHEDULE b 100\nFIRE_DUE 100\nCANCEL c\nSCHEDULE c 100\nFIRE_DUE 100\n", ["a", "b"]),
    "schedule_after_fire_due": ("SCHEDULE a 100\nFIRE_DUE 100\nSCHEDULE b 100\nFIRE_DUE 100\n", ["a", "b"]),
    "cancel_then_reschedule_same_id": ("SCHEDULE a 100\nCANCEL a\nSCHEDULE a 100\nFIRE_DUE 100\n", []),
    "recurring_basic": ("SCHEDULE r 100 50\nFIRE_DUE 100\n", ["r"]),
    "recurring_fires_once_when_overdue": ("SCHEDULE r 100 50\nFIRE_DUE 250\n", ["r"]),
    "recurring_realigns_after_overdue": ("SCHEDULE r 100 50\nFIRE_DUE 250\nFIRE_DUE 280\n", ["r"]),
    "recurring_next_round": ("SCHEDULE r 100 50\nFIRE_DUE 100\nFIRE_DUE 150\n", ["r", "r"]),
    "recurring_multi_period": ("SCHEDULE r 100 100\nFIRE_DUE 100\nFIRE_DUE 250\n", ["r", "r"]),
    "recurring_cancelled_stops": ("SCHEDULE r 100 50\nFIRE_DUE 100\nCANCEL r\nFIRE_DUE 200\n", ["r"]),
    "recurring_with_oneshot_order": ("SCHEDULE r 100 100\nSCHEDULE a 150\nFIRE_DUE 200\n", ["r", "a"]),
    "two_recurring_interleaved": ("SCHEDULE x 100 100\nSCHEDULE y 150 100\nFIRE_DUE 320\nFIRE_DUE 360\n", ["x", "y", "y"]),
    "coalesce_no_duplicate": ("SCHEDULE a 100\nSCHEDULE a 100\nFIRE_DUE 100\n", ["a"]),
    "coalesce_earlier_time_wins": ("SCHEDULE a 100\nSCHEDULE a 200\nFIRE_DUE 150\n", ["a"]),
    "coalesce_keeps_order": ("SCHEDULE a 100\nSCHEDULE b 100\nSCHEDULE a 100\nFIRE_DUE 100\n", ["a", "b"]),
    "coalesce_then_cancel": ("SCHEDULE a 100\nSCHEDULE a 50\nCANCEL a\nFIRE_DUE 100\n", []),
    "coalesce_recurring_to_oneshot": ("SCHEDULE r 100 50\nSCHEDULE r 100\nFIRE_DUE 100\nFIRE_DUE 200\n", ["r"]),
    "coalesce_oneshot_to_recurring": ("SCHEDULE r 100\nSCHEDULE r 100 50\nFIRE_DUE 100\nFIRE_DUE 150\n", ["r", "r"]),
    # --- per-round cost budget ---
    # Budget drains the due set across rounds in order.
    "budget_drains_across_rounds": (
        "BUDGET 2\nSCHEDULE a 100 0 1\nSCHEDULE b 100 0 2\nSCHEDULE c 100 0 1\n"
        "FIRE_DUE 100\nFIRE_DUE 100\nFIRE_DUE 100\n",
        ["a", "b", "c"],
    ),
    # A too-expensive callback at the front blocks cheaper ones behind it.
    "budget_front_blocks_rest": (
        "BUDGET 2\nSCHEDULE big 100 0 3\nSCHEDULE small 100 0 1\n"
        "FIRE_DUE 100\nFIRE_DUE 100\n",
        [],
    ),
    # Budget interacts with recurrence: r fits, a spills to next round.
    "budget_with_recurring": (
        "BUDGET 1\nSCHEDULE r 100 100 1\nSCHEDULE a 100 0 1\n"
        "FIRE_DUE 100\nFIRE_DUE 100\n",
        ["r", "a"],
    ),
}

@pytest.mark.parametrize("name", list(CASES.keys()))
def test_scheduler(name):
    ops, expected = CASES[name]
    assert run_scheduler(ops) == expected
