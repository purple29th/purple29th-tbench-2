import tempfile
from pathlib import Path
import sys
# Add possible src locations
for p in ["/app/src", str(Path(__file__).parent.parent / "src"), "/tmp/web_oracle/app/src", str(Path(__file__).parent / ".." / "src"), str(Path(__file__).parent / "../environment/src"), "environment/src", "src"]:
    try:
        if Path(p).exists():
            sys.path.insert(0, p)
    except:
        pass
sys.path.insert(0, str(Path(__file__).parent / ".." / "environment" / "src"))
from pool import VirtualPool
from scheduler import FetchScheduler
import json
import shutil
from unittest import mock

def test_basic_mount_and_resolve():
    pool = VirtualPool()
    sched = FetchScheduler(pool)
    token = pool.mount("n1", "item1", "FirstTitle")
    sched.schedule("n1", "item1", token, 10)
    sched.queue_resolution("item1", "https://img.com/1.jpg")
    sched.advance(10)
    snap = pool.snapshot("n1")
    assert snap == "n1 item=item1 title=FirstTitle image=https://img.com/1.jpg"

def test_stale_after_unmount():
    pool = VirtualPool()
    sched = FetchScheduler(pool)
    token1 = pool.mount("n1", "item1", "Title1")
    sched.schedule("n1", "item1", token1, 10)
    sched.queue_resolution("item1", "https://img.com/1.jpg")
    pool.unmount("n1")
    sched.advance(10)
    snap = pool.snapshot("n1")
    assert snap == "n1 unbound", f"stale corrupted unbound: {snap}"

def test_stale_after_rebind_different_item():
    pool = VirtualPool()
    sched = FetchScheduler(pool)
    token1 = pool.mount("n1", "item1", "Title1")
    sched.schedule("n1", "item1", token1, 10)
    sched.queue_resolution("item1", "https://img.com/item1.jpg")
    token2 = pool.mount("n1", "item2", "Title2")
    sched.schedule("n1", "item2", token2, 10)
    sched.queue_resolution("item2", "https://img.com/item2.jpg")
    sched.advance(10)
    snap = pool.snapshot("n1")
    assert "item=item2" in snap
    assert "https://img.com/item2.jpg" in snap
    assert "item1" not in snap

def test_same_tick_superseded_not_overwrite():
    pool = VirtualPool()
    sched = FetchScheduler(pool)
    t1 = pool.mount("n1", "item1", "T1")
    sched.schedule("n1", "item1", t1, 10)
    sched.queue_resolution("item1", "https://img.com/1.jpg")
    t2 = pool.mount("n1", "item1", "T1")
    sched.schedule("n1", "item1", t2, 10)
    sched.queue_resolution("item1", "https://img.com/2.jpg")
    sched.advance(10)
    snap = pool.snapshot("n1")
    assert "https://img.com/2.jpg" in snap

def test_budget_accrual_fractional_and_cap():
    pool = VirtualPool()
    sched = FetchScheduler(pool)
    sched.set_budget(1, 2, 1)
    token = pool.mount("n1", "item1", "T1")
    sched.schedule("n1", "item1", token, 1)
    sched.queue_resolution("item1", "https://img.com/1.jpg")
    sched.advance(1)
    assert pool.snapshot("n1") == "n1 item=item1 title=T1 image=NONE"
    sched.advance(2)
    snap = pool.snapshot("n1")
    assert "https://img.com/1.jpg" in snap

def test_stale_consumes_resolution_not_put_back():
    pool = VirtualPool()
    sched = FetchScheduler(pool)
    t1 = pool.mount("n1", "item1", "T1")
    sched.schedule("n1", "item1", t1, 10)
    sched.queue_resolution("item1", "https://img.com/stale.jpg")
    sched.queue_resolution("item1", "https://img.com/valid.jpg")
    t2 = pool.mount("n1", "item1", "T1")
    sched.schedule("n1", "item1", t2, 10)
    sched.advance(10)
    snap = pool.snapshot("n1")
    assert "https://img.com/valid.jpg" in snap
    assert "stale" not in snap

def test_title_update_and_prefetch():
    pool = VirtualPool()
    sched = FetchScheduler(pool)
    t1 = pool.mount("n1", "item1", "OldTitle")
    pool.update_title("n1", "NewTitle")
    sched.schedule("n1", "item1", t1, 10)
    sched.queue_resolution("item1", "https://img.com/1.jpg")
    sched.advance(10)
    snap = pool.snapshot("n1")
    assert "title=NewTitle" in snap

def test_unbound_image_never_produced():
    pool = VirtualPool()
    sched = FetchScheduler(pool)
    t1 = pool.mount("n1", "item1", "T1")
    sched.schedule("n1", "item1", t1, 5)
    sched.queue_resolution("item1", "https://img.com/1.jpg")
    sched.advance(5)
    pool.unmount("n1")
    snap = pool.snapshot("n1")
    assert snap == "n1 unbound"
