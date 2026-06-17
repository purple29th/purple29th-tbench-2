"""Verification tests for event-loop-scheduler.

Each case feeds operations into the agent's program (/app/scheduler,
reading stdin) and checks the firing order printed to stdout.
"""

import subprocess

import pytest

SCHEDULER = "/app/scheduler"


def run_scheduler(ops):
    proc = subprocess.run(
        [SCHEDULER], input=ops, capture_output=True, text=True, timeout=30,
    )
    assert proc.returncode == 0, f"scheduler exited {proc.returncode}; stderr:\n{proc.stderr}"
    return [line for line in proc.stdout.splitlines() if line.strip()]


CASES = {
    "basic": (
        "SCHEDULE a 100\nFIRE_DUE 100\n",
        ["a"],
    ),
    "order_by_time": (
        "SCHEDULE a 200\nSCHEDULE b 100\nFIRE_DUE 200\n",
        ["b", "a"],
    ),
    "tie_by_registration": (
        "SCHEDULE a 100\nSCHEDULE b 100\nFIRE_DUE 100\n",
        ["a", "b"],
    ),
    "queued_cancel": (
        "SCHEDULE a 100\nCANCEL a\nFIRE_DUE 100\n",
        [],
    ),
    "recurring_no_drift": (
        "SCHEDULE r 100 100\nFIRE_DUE 350\nFIRE_DUE 450\n",
        ["r", "r"],
    ),
    "recurring_rearm_loses_priority": (
        "SCHEDULE r 100 100\nSCHEDULE a 200\nFIRE_DUE 100\nFIRE_DUE 200\n",
        ["r", "a", "r"],
    ),
    "budget_carry_remainder": (
        "BUDGET 3 2 100\nSCHEDULE a 0 0 1\nSCHEDULE b 0 0 1\nSCHEDULE c 0 0 1\nFIRE_DUE 1\nFIRE_DUE 2\n",
        ["a", "b", "c"],
    ),
    "budget_head_of_line": (
        "BUDGET 2 1 100\nSCHEDULE big 0 0 3\nSCHEDULE small 0 0 1\nFIRE_DUE 1\nFIRE_DUE 2\n",
        ["big", "small"],
    ),
    "budget_cap_clamp": (
        "BUDGET 1 1 2\nSCHEDULE a 0 0 1\nSCHEDULE b 0 0 1\nSCHEDULE c 0 0 1\nFIRE_DUE 100\n",
        ["a", "b"],
    ),
    "budget_recurring_cost": (
        "BUDGET 2 3 100\nSCHEDULE r 0 10 1\nSCHEDULE a 0 0 1\nFIRE_DUE 2\nFIRE_DUE 10\n",
        ["r", "a", "r"],
    ),
    "coalesce_retarget_keeps_order": (
        "SCHEDULE a 200\nSCHEDULE b 100\nSCHEDULE a 100\nFIRE_DUE 100\n",
        ["a", "b"],
    ),
    "cancel_clears_reschedule_before_wakeup": (
        "SCHEDULE a 100\nCANCEL a\nSCHEDULE a 100\nSCHEDULE b 100\nFIRE_DUE 100\n",
        ["b"],
    ),
    "recurring_no_same_round_replay": (
        "SCHEDULE r 100 100\nFIRE_DUE 500\n",
        ["r"],
    ),
}


@pytest.mark.parametrize("name", list(CASES.keys()))
def test_firing_order(name):
    ops, expected = CASES[name]
    assert run_scheduler(ops) == expected
