"""Verification tests for lru-cache-with-cost-budget.

Expected outputs are stored as salted SHA-256 digests, not plaintext, so a
program that reads this file at verify time cannot echo the answers back.
"""

import hashlib
import subprocess

import pytest

CACHE = "/app/cache"
SALT = 'lru-cbgt-v4-3b9d'


def run_cache(ops):
    proc = subprocess.run(
        [CACHE], input=ops, capture_output=True, text=True, timeout=30,
    )
    assert proc.returncode == 0, f"cache exited {proc.returncode}; stderr:\n{proc.stderr}"
    return proc.stdout


def _norm(stdout):
    return "\n".join(l.rstrip() for l in stdout.splitlines() if l.strip())


def _digest(stdout):
    return hashlib.sha256((SALT + _norm(stdout)).encode()).hexdigest()


CASES = {
    "basic_put_get": ("PUT a v1 10\nPUT b v2 20\nPUT c v3 30\n", "00d62647577a04ae2e686c9b2b756f98af28a0660586b3e8a7114d0f511d5867"),
    "tie_break_cost_then_key": ("PUT a v1 10\nPUT b v2 10\nPUT c v3 10\n", "f1bb05feaff915d6fac3cbc80ddbfdd9731398ac9bee02ac0abcf2d85390ecdc"),
    "get_promotes_with_tick": ("PUT a v1 10\nPUT b v2 20\nTICK\nGET a\n", "f5dbfd0bff8e286950b89f561f29cc973ad78bd52afd03ce264f4abe1b974b21"),
    "get_same_tier_no_reorder": ("PUT a v1 30\nPUT b v2 10\nGET a\n", "d08655b850ad44180467d6a72d16ae9c09cb963117034b187456c22fc3fcfd24"),
    "put_promotes_with_tick": ("PUT a v1 10\nTICK\nPUT b v2 20\nTICK\nPUT c v3 30\nTICK\nPUT a v1 10\n", "da6ffe9afcfdb48b59dfe1052c6b18e713ed76f8773014ba6d4f479813e4a69e"),
    "evict_to_under_budget": ("PUT a v1 10\nPUT b v2 10\nPUT c v3 10\nEVICT_TO 100\n", "f1bb05feaff915d6fac3cbc80ddbfdd9731398ac9bee02ac0abcf2d85390ecdc"),
    "evict_to_exact_budget": ("PUT a v1 50\nPUT b v2 50\nEVICT_TO 100\n", "8e3daa6f532eecc873b94f66d556bdb47130728a43f610d7858a101554fdbb97"),
    "evict_lru_first": ("PUT a v1 40\nTICK\nPUT b v2 40\nTICK\nPUT c v3 40\nEVICT_TO 80\n", "a17c3f9efab10f629cb2ad725baa4e77df63c99cd64b59c256094f18217eda68"),
    "evict_cost_tie_breaks_lru": ("PUT a v1 10\nPUT b v2 30\nEVICT_TO 20\n", "8bfc9cb88be0c3e7f95ecf9aa90e933d6a99119a6ea59028e72ae914dee8495b"),
    "evict_recency_dominates_cost": ("PUT a v1 5\nTICK\nPUT b v2 50\nEVICT_TO 50\n", "d2c4c66330a4dc38020f006d89ed94c6b9fab33d1ee61fad4b5608d4d047d720"),
    "put_overwrites_not_appends": ("PUT a v1 5\nPUT a v2 10\n", "e0668c479d9451c80fe5f0f11809dffa94953d4da1afb250763e6f4c042b4659"),
    "multiple_evicts": ("PUT a v1 10\nTICK\nPUT b v2 10\nTICK\nPUT c v3 10\nTICK\nPUT d v4 10\nTICK\nPUT e v5 10\nEVICT_TO 30\nTICK\nPUT f v6 10\nEVICT_TO 20\n", "f402a74ce9b617bcdb7c7b67a5c94b4789efd9edfcac45b6b4037fb3746ae207"),
    "get_on_missing_key": ("PUT a v1 10\nGET nonexistent\nTICK\nPUT b v2 20\n", "21b2471cc557c095b88641c9520f6a82eb69783f905a9d6a2e422207591af85f"),
    "pin_prevents_eviction": ("PUT a v1 10\nTICK\nPUT b v2 10\nPIN a\nEVICT_TO 10\n", "8bfc9cb88be0c3e7f95ecf9aa90e933d6a99119a6ea59028e72ae914dee8495b"),
    "pin_budget_unreachable": ("PUT a v1 30\nPIN a\nPUT b v2 10\nEVICT_TO 20\n", "d9d1455e8e0712e7ff8d13f271eba3bd5b01e2e009a8fad7fe9a4afbaecc0557"),
    "unpin_reenables_eviction": ("PUT a v1 30\nPIN a\nUNPIN a\nPUT b v2 10\nEVICT_TO 20\n", "3032455c3268d78e706f404e037d6f98dc047c22a6ce5cd0e993c981663ecd98"),
    "pin_is_not_an_access": ("PUT a v1 10\nTICK\nPUT b v2 20\nPIN a\nUNPIN a\nEVICT_TO 20\n", "1fae1ba956a5a72ad4ffae7b485014a2bcd8732120aa960397627cefa0738d3b"),
    "pin_missing_key_noop": ("PUT a v1 10\nPIN ghost\nEVICT_TO 100\n", "8bfc9cb88be0c3e7f95ecf9aa90e933d6a99119a6ea59028e72ae914dee8495b"),
    "multiple_pins_budget_unreachable": ("PUT a v1 10\nTICK\nPUT b v2 10\nTICK\nPUT c v3 10\nPIN a\nPIN c\nEVICT_TO 10\n", "094fba510ad071f6b580a526ec550ae4e16666815e43a6bd34c539091f28b0cc"),
    "decay_carry_one_third": ("DECAY 1 3\nPUT a v1 10\nPUT b v2 10\nTICK\nTICK\nTICK\nEVICT_TO 19\n", "4af468172a7ed368ab8146f7101f2871457b7389163b80aebb648d107bdd3b2b"),
    "decay_carry_two_thirds": ("DECAY 2 3\nPUT a v1 10\nTICK\nPUT b v2 10\nTICK\nTICK\nTICK\nEVICT_TO 18\n", "4af468172a7ed368ab8146f7101f2871457b7389163b80aebb648d107bdd3b2b"),
    "decay_relieves_pressure": ("DECAY 1 2\nPUT a v1 20\nTICK\nTICK\nEVICT_TO 19\n", "aa25484c5b7ecc9ce7997644fb54c3282f79d79adff8ca5480265f500fb0e7e8"),
    "decay_absent_normal_evict": ("PUT a v1 10\nTICK\nPUT b v2 10\nEVICT_TO 10\n", "3032455c3268d78e706f404e037d6f98dc047c22a6ce5cd0e993c981663ecd98"),
}


@pytest.mark.parametrize("name", list(CASES.keys()))
def test_cache(name):
    ops, expected_digest = CASES[name]
    assert _digest(run_cache(ops)) == expected_digest
