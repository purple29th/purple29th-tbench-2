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
    "budget_drains_across_rounds": (
        "BUDGET 2\nSCHEDULE a 100 0 1\nSCHEDULE b 100 0 2\nSCHEDULE c 100 0 1\n"
        "FIRE_DUE 100\nFIRE_DUE 100\nFIRE_DUE 100\n",
        ["a", "b", "c"],
    ),
    "budget_front_blocks_rest": (
        "BUDGET 2\nSCHEDULE big 100 0 3\nSCHEDULE small 100 0 1\nFIRE_DUE 100\nFIRE_DUE 100\n",
        [],
    ),
    "budget_with_recurring": (
        "BUDGET 1\nSCHEDULE r 100 100 1\nSCHEDULE a 100 0 1\nFIRE_DUE 100\nFIRE_DUE 100\n",
        ["r", "a"],
    ),
    # Re-arm re-enters the pending set as the newest waiter: when a re-armed
    # recurring timer lands on the same tick as a one-shot registered before
    # the re-arm, the one-shot (older waiter) runs first.
    # Follow-ups: a callback can be chained to run a fixed delay after another
    # callback actually fires. The dependent has no time of its own until then.
    "after_basic": (
        "SCHEDULE d 100\nAFTER x d 50\nFIRE_DUE 100\nFIRE_DUE 150\n",
        ["d", "x"],
    ),
    # If the trigger is cancelled and never runs, the follow-up never fires.
    "after_dep_cancelled": (
        "SCHEDULE d 100\nAFTER x d 50\nCANCEL d\nFIRE_DUE 100\nFIRE_DUE 200\n",
        [],
    ),
    # A follow-up triggered during a wake-up is new work: even at delay 0 it
    # waits for the next wake-up rather than firing in the same one.
    "after_no_same_round": (
        "SCHEDULE d 100\nAFTER x d 0\nFIRE_DUE 100\nFIRE_DUE 100\n",
        ["d", "x"],
    ),
    # A repeating trigger re-fires its follow-up each time it runs.
    "after_recurring_dep": (
        "SCHEDULE d 100 100\nAFTER x d 10\nFIRE_DUE 100\nFIRE_DUE 110\nFIRE_DUE 200\n",
        ["d", "x", "d"],
    ),
    # Chained follow-ups run one wake-up apart.
    "after_chain": (
        "SCHEDULE a 100\nAFTER b a 50\nAFTER c b 50\nFIRE_DUE 100\nFIRE_DUE 150\nFIRE_DUE 200\n",
        ["a", "b", "c"],
    ),
    # A follow-up target that's already pending coalesces to the earlier time.
    "after_coalesces_target": (
        "SCHEDULE d 100\nAFTER x d 100\nSCHEDULE x 250\nFIRE_DUE 100\nFIRE_DUE 200\n",
        ["d", "x"],
    ),
    # A trigger blocked by the budget doesn't run, so its follow-up doesn't fire.
    "after_budget_gated_trigger": (
        "BUDGET 1\nSCHEDULE big 100 0 5\nAFTER x big 10\nFIRE_DUE 100\nFIRE_DUE 200\n",
        [],
    ),
    "recurring_rearm_loses_priority": (
        "SCHEDULE r 100 100\nSCHEDULE a 200\nFIRE_DUE 100\nFIRE_DUE 200\n",
        ["r", "a", "r"],
    ),
    "recurring_rearm_after_two": (
        "SCHEDULE r 100 100\nSCHEDULE a 200\nSCHEDULE b 200\nFIRE_DUE 100\nFIRE_DUE 200\n",
        ["r", "a", "b", "r"],
    ),
}

@pytest.mark.parametrize("name", list(CASES.keys()))
def test_scheduler(name):
    ops, expected = CASES[name]
    assert run_scheduler(ops) == expected
