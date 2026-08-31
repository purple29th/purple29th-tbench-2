import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
from pool import VirtualPool
from scheduler import FetchScheduler

def main():
    pool = VirtualPool()
    scheduler = FetchScheduler(pool)
    inspections = []  # list of nodeIds in order
    out_lines = []

    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue
        parts = line.split()
        op = parts[0]
        if op == "MOUNT":
            # MOUNT <nodeId> <itemId> <title> <dueAt>
            if len(parts) < 5:
                continue
            node_id = parts[1]
            item_id = parts[2]
            title = parts[3]
            due_at = int(parts[4])
            token = pool.mount(node_id, item_id, title)
            scheduler.schedule(node_id, item_id, token, due_at)
        elif op == "UPDATE_TITLE":
            node_id = parts[1]
            new_title = parts[2] if len(parts) > 2 else ""
            pool.update_title(node_id, new_title)
        elif op == "PREFETCH":
            node_id = parts[1]
            due_at = int(parts[2])
            node = pool.get_node(node_id)
            if node.is_bound:
                scheduler.schedule(node_id, node.item_id, node.binding_token, due_at)
        elif op == "UNMOUNT":
            node_id = parts[1]
            pool.unmount(node_id)
        elif op == "BUDGET":
            num = int(parts[1]); den = int(parts[2]); cap = int(parts[3])
            scheduler.set_budget(num, den, cap)
        elif op == "RESOLVE":
            item_id = parts[1]
            url = parts[2] if len(parts) > 2 else f"auto:{item_id}"
            scheduler.queue_resolution(item_id, url)
        elif op == "ADVANCE":
            now = int(parts[1])
            scheduler.advance(now)
        elif op == "INSPECT":
            node_id = parts[1]
            inspections.append(node_id)
        else:
            # ignore unknown
            continue

    # Print all inspections
    for nid in inspections:
        print(pool.snapshot(nid))

if __name__ == "__main__":
    main()
