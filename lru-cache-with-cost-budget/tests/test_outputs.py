"""Verification tests for lru-cache-with-cost-budget.

Expected outputs are stored as salted SHA-256 digests, not plaintext, so a
program that reads this file at verify time cannot echo the answers back.
"""

import hashlib
import subprocess

import pytest

CACHE = "/app/cache"
SALT = "lru-cbgt-v5-adversarial"


def run_cache(ops):
    # hide /tests during binary execution to close in-subprocess oracle leak
    import os, shutil, pathlib

    hidden = "/tmp/tests_hidden_lru"
    tests_dir = pathlib.Path("/tests")
    moved = False
    if tests_dir.exists():
        if os.path.exists(hidden):
            shutil.rmtree(hidden)
        shutil.move(str(tests_dir), hidden)
        moved = True
    try:
        proc = subprocess.run(
            [CACHE],
            input=ops,
            capture_output=True,
            text=True,
            timeout=30,
        )
        assert proc.returncode == 0, (
            f"cache exited {proc.returncode}; stderr:\n{proc.stderr}"
        )
        out = proc.stdout
    finally:
        if moved:
            if tests_dir.exists():
                shutil.rmtree(str(tests_dir))
            shutil.move(hidden, str(tests_dir))
    return out


def _norm(stdout):
    return "\n".join(l.rstrip() for l in stdout.splitlines() if l.strip())


def _digest(stdout):
    return hashlib.sha256((SALT + _norm(stdout)).encode()).hexdigest()


CASES = {
    "basic_put_get": (
        "PUT a v1 10\nPUT b v2 20\nPUT c v3 30\n",
        "6c965628d33b073c613867be6e8c4ae6a3a12fe594234fdc39613bcbe8dc35e5",
    ),
    "tie_break_cost_then_key": (
        "PUT a v1 10\nPUT b v2 10\nPUT c v3 10\n",
        "3f0d2961e4740aa1424e218bce21cdb901e398aa6e01e361ddf072b2bacbc88a",
    ),
    "get_promotes_with_tick": (
        "PUT a v1 10\nPUT b v2 20\nTICK\nGET a\n",
        "efae40a736b27350d6d56709edbbce40dede6eee13bdfa64b6e78a8fe116d80c",
    ),
    "get_same_tier_no_reorder": (
        "PUT a v1 30\nPUT b v2 10\nGET a\n",
        "604452d24562f7c9e58213015c783b9f8ece342d4e2dc57594dca29d94af7229",
    ),
    "put_promotes_with_tick": (
        "PUT a v1 10\nTICK\nPUT b v2 20\nTICK\nPUT c v3 30\nTICK\nPUT a v1 10\n",
        "78ae864c16980424b188b6972c5622feb569ddc254316036cd717951c3698bc6",
    ),
    "evict_to_exact_budget": (
        "PUT a v1 50\nPUT b v2 50\nEVICT_TO 100\n",
        "8f983dc1a76aad0a4ca32f9d23087bcef3f4b4bdf147866fbfa74dac7cbccd6b",
    ),
    "evict_lru_first": (
        "PUT a v1 40\nTICK\nPUT b v2 40\nTICK\nPUT c v3 40\nEVICT_TO 80\n",
        "831b67cc5c0fae216b2c3579ccea040ed96c606636e2a78ae140a4123f8ef5eb",
    ),
    "evict_cost_tie_breaks_lru": (
        "PUT a v1 10\nPUT b v2 30\nEVICT_TO 20\n",
        "2442ae983ce127d1233e7a5e677c18b0d353284f4d23ae764fdde13cf7a1a6d1",
    ),
    "evict_recency_dominates_cost": (
        "PUT a v1 5\nTICK\nPUT b v2 50\nEVICT_TO 50\n",
        "4a8e565b896b2c82ebc70a3b69ae074f25405f83ecd18665341838d3d52ba0c4",
    ),
    "put_overwrites_not_appends": (
        "PUT a v1 5\nPUT a v2 10\n",
        "c6ff6e4d96a161914e44207c51917e5169219ff23ac8a7df4f09a99ff7a8225f",
    ),
    "pin_prevents_eviction": (
        "PUT a v1 10\nTICK\nPUT b v2 10\nPIN a\nEVICT_TO 10\n",
        "2442ae983ce127d1233e7a5e677c18b0d353284f4d23ae764fdde13cf7a1a6d1",
    ),
    "pin_budget_unreachable": (
        "PUT a v1 30\nPIN a\nPUT b v2 10\nEVICT_TO 20\n",
        "2266faf4c2bb6db4f614f9805c40d714e10665af281c385eb7b08c43f26218c2",
    ),
    "unpin_reenables_eviction": (
        "PUT a v1 30\nPIN a\nUNPIN a\nPUT b v2 10\nEVICT_TO 20\n",
        "89eaf82bc2c2baca871d263f80b737c67111f751418ec563e2595d43fbc3bad2",
    ),
    "decay_carry_one_third": (
        "DECAY 1 3\nPUT a v1 10\nPUT b v2 10\nTICK\nTICK\nTICK\nEVICT_TO 19\n",
        "52e44ba6e198ed74e5cb0af4594de5db543d9e7dd909716ff35ee2d80197b476",
    ),
    "decay_carry_two_thirds": (
        "DECAY 2 3\nPUT a v1 10\nTICK\nPUT b v2 10\nTICK\nTICK\nTICK\nEVICT_TO 18\n",
        "52e44ba6e198ed74e5cb0af4594de5db543d9e7dd909716ff35ee2d80197b476",
    ),
    "decay_absent_normal_evict": (
        "PUT a v1 10\nTICK\nPUT b v2 10\nEVICT_TO 10\n",
        "89eaf82bc2c2baca871d263f80b737c67111f751418ec563e2595d43fbc3bad2",
    ),
    "adversarial_mixed_1": (
        "PUT a va 10\nPUT b vb 20\nTICK\nPUT c vc 15\nGET a\nTICK\nPUT d vd 25\nPIN b\nSAVEPOINT_NONE\nPUT e ve 5\nTICK\nGET c\nPUT a va2 12\nEVICT_TO 40\nTICK\nUNPIN b\nPUT f vf 30\nEVICT_TO 35\nGET f\nTICK\nPUT g vg 8\nEVICT_TO 20\n",
        "8126ad756a2149d1f2a484804abcefc995fd4302de8b7c901bd3e9ba6cc4a719",
    ),
    "adversarial_decay_pin_2": (
        "DECAY 1 2\nPUT a va 20\nTICK\nPUT b vb 20\nTICK\nPUT c vc 20\nTICK\nPIN a\nTICK\nEVICT_TO 30\nTICK\nTICK\nUNPIN a\nPUT d vd 10\nEVICT_TO 25\nGET c\nTICK\nPUT e ve 5\nEVICT_TO 15\n",
        "1935a1a11ba8819c8dcdec97a1727a60966595b12b18b79f2fddab29401de5d1",
    ),
    "adversarial_cost_ties_3": (
        "PUT k1 x 7\nPUT k2 x 7\nPUT k3 x 7\nTICK\nGET k2\nPUT k4 x 7\nPIN k1\nTICK\nPUT k5 x 7\nGET k3\nEVICT_TO 21\nTICK\nUNPIN k1\nPUT k6 x 7\nPUT k2 y 14\nEVICT_TO 20\nTICK\nDECAY 2 1\nTICK\nEVICT_TO 10\n",
        "1179c48ccadfa5701502d5776d334b85fe7b1e21bbf525c552575981fc51405b",
    ),
    "adversarial_pin_churn_4": (
        "PUT a v 50\nPIN a\nPUT b v 40\nPUT c v 30\nTICK\nPUT d v 20\nGET b\nTICK\nEVICT_TO 60\nPUT e v 25\nTICK\nUNPIN a\nEVICT_TO 45\nPIN c\nEVICT_TO 30\nGET a\nTICK\nPUT f v 10\nUNPIN c\nEVICT_TO 20\n",
        "840d677d1a93c043a09ef9e64b91b1f1910479989132b5d4c3981adddd793557",
    ),
}


@pytest.mark.parametrize("name", list(CASES.keys()))
def test_cache(name):
    ops, expected_digest = CASES[name]
    assert _digest(run_cache(ops)) == expected_digest
