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
        self._budget_frac_num = 0
        self.last_now = 0

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
        if self.budgeted:
            dt = now - self.last_now
            if dt > 0:
                total_num = self._budget_frac_num + dt * self.refill_num
                add = total_num // self.refill_den
                self._budget_frac_num = total_num % self.refill_den
                self.budget += add
                if self.budget > self.cap:
                    self.budget = self.cap
        self.last_now = now

        due = [p for p in self.pending if p.due_at <= now]
        due.sort(key=lambda x: (x.due_at, x.seq, x.node_id))

        processed = []
        for load in due:
            node = self.pool.get_node(load.node_id)
            is_valid = (node.binding_token == load.expected_token and node.is_bound)
            if not is_valid:
                # stale consumes resolution
                q = self.resolutions.get(load.item_id)
                _ = q.popleft() if q and len(q) > 0 else f"auto:{load.item_id}"
                processed.append(load)
                continue
            if self.budgeted and self.budget < 1:
                break
            q = self.resolutions.get(load.item_id)
            url = q.popleft() if q and len(q) > 0 else f"auto:{load.item_id}"
            applied = node.apply_image(url, load.expected_token)
            if applied and self.budgeted:
                self.budget -= 1
            processed.append(load)

        for p in processed:
            if p in self.pending:
                self.pending.remove(p)
