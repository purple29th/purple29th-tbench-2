"""Verification tests for lru-cache-with-cost-budget."""
import subprocess

import pytest

CACHE = "/app/cache"

def run_cache(ops):
    proc = subprocess.run(
        [CACHE],
        input=ops,
        capture_output=True,
        text=True,
        timeout=30,
    )
    assert proc.returncode == 0, f"cache exited {proc.returncode}; stderr:\n{proc.stderr}"
    return [line for line in proc.stdout.splitlines() if line.strip()]

CASES = {
    "basic_put_get": (
        "PUT a v1 10\nPUT b v2 20\nPUT c v3 30\n",
        ["a v1 10", "b v2 20", "c v3 30"],
    ),
    "get_promotes": (
        "PUT a v1 10\nPUT b v2 20\nPUT c v3 30\nGET a\n",
        ["b v2 20", "c v3 30", "a v1 10"],
    ),
    "evict_to_under_budget": (
        "PUT a v1 10\nPUT b v2 10\nPUT c v3 10\nEVICT_TO 100\n",
        ["a v1 10", "b v2 10", "c v3 10"],
    ),
    "evict_to_exact_budget": (
        "PUT a v1 50\nPUT b v2 50\nEVICT_TO 100\n",
        ["a v1 50", "b v2 50"],
    ),
    "evict_lru_first": (
        "PUT a v1 40\nTICK\nPUT b v2 40\nTICK\nPUT c v3 40\nEVICT_TO 80\n",
        ["b v2 40", "c v3 40"],
    ),
    "evict_cost_tie_breaks_lru": (
        "PUT a v1 10\nPUT b v2 30\nEVICT_TO 20\n",
        ["a v1 10"],
    ),
    "evict_recency_dominates_cost": (
        "PUT a v1 50\nTICK\nPUT b v2 5\nEVICT_TO 5\n",
        ["b v2 5"],
    ),
    "put_overwrites_not_appends": (
        "PUT a v1 5\nPUT a v2 10\n",
        ["a v2 10"],
    ),
    "put_promotes_to_mru": (
        "PUT a v1 10\nTICK\nPUT b v2 20\nTICK\nPUT c v3 30\nTICK\nPUT a v1 10\n",
        ["b v2 20", "c v3 30", "a v1 10"],
    ),
    "tick_separates_recency_tiers": (
        "PUT a v1 5\nPUT b v2 5\nTICK\nPUT c v3 5\n",
        ["a v1 5", "b v2 5", "c v3 5"],
    ),
    "multiple_evicts": (
        "PUT a v1 10\nTICK\nPUT b v2 10\nTICK\nPUT c v3 10\nTICK\nPUT d v4 10\nTICK\nPUT e v5 10\n"
        "EVICT_TO 30\nTICK\nPUT f v6 10\nEVICT_TO 20\n",
        ["e v5 10", "f v6 10"],
    ),
    "get_on_missing_key": (
        "PUT a v1 10\nGET nonexistent\nTICK\nPUT b v2 20\n",
        ["a v1 10", "b v2 20"],
    ),
}

@pytest.mark.parametrize("name", list(CASES.keys()))
def test_cache(name):
    ops, expected = CASES[name]
    assert run_cache(ops) == expected
