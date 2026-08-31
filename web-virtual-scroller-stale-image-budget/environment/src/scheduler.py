# Buggy scheduler — budget accrual ignores fractional part and does not stop correctly

from collections import deque, defaultdict

class Load:
    def __init__(self, seq, node_id, item_id, expected_token, due_at):
        self.seq = seq
        self.node_id = node_id
        self.item_id = item_id
        self.expected_token = expected_token
        self.due_at = due_at

class FetchScheduler:
    def __init__(self, pool):
        self.pool = pool
        self.pending = []
        self.resolutions = defaultdict(deque)
        self._seq = 0
        self.budgeted = False
        self.refill_num = 0
        self.refill_den = 1
        self.cap = 0
        self.budget = 0
        self.last_now = 0
        self._fraction = 0  # Bug: not used correctly

    def schedule(self, node_id, item_id, expected_token, due_at):
        self._seq += 1
        self.pending.append(Load(self._seq, node_id, item_id, expected_token, due_at))

    def queue_resolution(self, item_id, url):
        self.resolutions[item_id].append(url)

    def set_budget(self, num, den, cap):
        self.budgeted = True
        self.refill_num = num
        self.refill_den = den
        self.cap = cap
        if self.budget > cap:
            self.budget = cap

    def advance(self, now):
        # Bug: budget accrual does not keep fractional part, uses integer division per tick incorrectly
        if self.budgeted:
            dt = now - self.last_now
            if dt > 0:
                # Bug: should accrue (dt * num / den) with fractional carry, but this does integer division losing fraction
                self.budget += (dt * self.refill_num) // self.refill_den
            if self.budget > self.cap:
                self.budget = self.cap
        self.last_now = now

        due = [p for p in self.pending if p.due_at <= now]
        due.sort(key=lambda x: (x.due_at, x.seq, x.node_id))

        processed = []
        for load in due:
            node = self.pool.get_node(load.node_id)
            # Bug: does not check token validity to save budget — stale loads still cost budget in buggy version
            is_valid = True  # should be node.binding_token == expected_token
            if is_valid and self.budgeted and self.budget < 1:
                break
            queue = self.resolutions.get(load.item_id)
            url = queue.popleft() if queue and len(queue) > 0 else f"auto:{load.item_id}"
            # Apply without token check (bug in pool)
            applied = node.apply_image(url, load.expected_token)
            if applied:
                if self.budgeted and is_valid:
                    self.budget -= 1
            processed.append(load)

        for p in processed:
            if p in self.pending:
                self.pending.remove(p)
