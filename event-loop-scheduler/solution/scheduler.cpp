// Reference oracle for event-loop-scheduler.
//
// Reads operations from stdin (one per line) and writes the firing order of
// callback ids to stdout, one per line.
//
// Time, costs and budget are integers; the refill RATE is the fraction
// num/den credits per millisecond and accrues CONTINUOUSLY -- the sub-credit
// remainder is carried across wake-ups, never discarded. Budget is tracked in
// "den-units" (den units == 1 credit) so all arithmetic stays exact.
#include <algorithm>
#include <iostream>
#include <sstream>
#include <string>
#include <unordered_map>
#include <utility>
#include <vector>

namespace {

struct Entry {
    long ready_at;
    long sequence;
    long interval;  // 0 == one-shot
    long cost;      // credits required to run, >= 1
};

class Scheduler {
   public:
    void set_budget(long num, long den, long cap) {
        budgeted_ = true;
        refill_num_ = num;
        refill_den_ = den;
        cap_units_ = cap * den;
        if (budget_units_ > cap_units_) budget_units_ = cap_units_;
    }

    void schedule(const std::string& id, long at, long interval, long cost) {
        auto it = pending_.find(id);
        if (it == pending_.end()) {
            pending_[id] = {at, next_sequence_++, interval, cost};
            return;
        }
        // Coalesce in place: take the earlier time, adopt the new period and
        // cost, and keep the original place in the running order.
        it->second.ready_at = std::min(it->second.ready_at, at);
        it->second.interval = interval;
        it->second.cost = cost;
    }

    void queue_cancel(const std::string& id) { queued_cancels_.push_back(id); }

    std::vector<std::string> fire_due(long now) {
        for (const auto& id : queued_cancels_) pending_.erase(id);
        queued_cancels_.clear();

        // Continuous accrual: add exactly dt*num den-units, carrying remainder.
        if (budgeted_) {
            long dt = now - last_fire_;
            if (dt > 0) budget_units_ += dt * refill_num_;
            if (budget_units_ > cap_units_) budget_units_ = cap_units_;
        }
        last_fire_ = now;

        // Snapshot the due set: earliest-time first, ties by registration order.
        std::vector<std::pair<std::string, Entry>> due;
        for (const auto& kv : pending_)
            if (kv.second.ready_at <= now) due.push_back(kv);
        std::sort(due.begin(), due.end(), [](const auto& a, const auto& b) {
            if (a.second.ready_at != b.second.ready_at)
                return a.second.ready_at < b.second.ready_at;
            return a.second.sequence < b.second.sequence;
        });

        // Dispatch in order. Head-of-line blocking: the first due callback that
        // cannot be afforded stops the wake-up -- we never skip past it to a
        // cheaper one. Unfired due callbacks stay pending for a later wake-up.
        std::vector<std::string> fired;
        std::vector<std::pair<std::string, Entry>> rearm;
        for (const auto& d : due) {
            if (budgeted_) {
                long need = d.second.cost * refill_den_;
                if (budget_units_ < need) break;
                budget_units_ -= need;
            }
            fired.push_back(d.first);
            pending_.erase(d.first);
            if (d.second.interval > 0) rearm.push_back(d);
        }
        // Re-anchor recurring timers to their own period grid, the first instant
        // strictly after now; each re-enters with a fresh sequence (so it loses
        // tie-break priority to anything already waiting at the same time).
        for (const auto& r : rearm) {
            long next = r.second.ready_at;
            while (next <= now) next += r.second.interval;
            pending_[r.first] = {next, next_sequence_++, r.second.interval, r.second.cost};
        }
        return fired;
    }

   private:
    std::unordered_map<std::string, Entry> pending_;
    std::vector<std::string> queued_cancels_;
    long next_sequence_ = 0;
    bool budgeted_ = false;
    long refill_num_ = 0;
    long refill_den_ = 1;
    long cap_units_ = 0;
    long budget_units_ = 0;
    long last_fire_ = 0;
};

void process_line(Scheduler& s, const std::string& line, std::vector<std::string>& out) {
    std::istringstream iss(line);
    std::string op;
    if (!(iss >> op)) return;
    if (op == "BUDGET") {
        long num, den, cap;
        if (iss >> num >> den >> cap) s.set_budget(num, den, cap);
    } else if (op == "SCHEDULE") {
        std::string id;
        long at, every = 0, cost = 1;
        if (iss >> id >> at) {
            iss >> every;
            iss >> cost;
            s.schedule(id, at, every, cost);
        }
    } else if (op == "CANCEL") {
        std::string id;
        if (iss >> id) s.queue_cancel(id);
    } else if (op == "FIRE_DUE") {
        long now;
        if (iss >> now) {
            auto fired = s.fire_due(now);
            out.insert(out.end(), fired.begin(), fired.end());
        }
    }
}

}  // namespace

int main() {
    Scheduler s;
    std::vector<std::string> out;
    std::string line;
    while (std::getline(std::cin, line)) process_line(s, line, out);
    for (const auto& id : out) std::cout << id << '\n';
    return 0;
}
