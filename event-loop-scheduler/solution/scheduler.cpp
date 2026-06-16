// Reference oracle for event-loop-scheduler.
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
    long cost;
};

struct Trigger {
    std::string target;
    long delay;
};

class Scheduler {
   public:
    void set_budget(long b) { budget_ = b; }

    void schedule(const std::string& id, long at_ms, long interval_ms, long cost) {
        auto it = pending_.find(id);
        if (it == pending_.end()) {
            pending_[id] = {at_ms, next_sequence_++, interval_ms, cost};
            return;
        }
        it->second.ready_at = std::min(it->second.ready_at, at_ms);
        it->second.interval = interval_ms;
        it->second.cost = cost;
    }

    void after(const std::string& id, const std::string& dep, long delay) {
        triggers_[dep].push_back({id, delay});
    }

    void queue_cancel(const std::string& id) { queued_cancels_.push_back(id); }

    std::vector<std::string> fire_due(long now_ms) {
        apply_queued_cancels();

        std::vector<std::pair<std::string, Entry>> due;
        for (const auto& kv : pending_) {
            if (kv.second.ready_at <= now_ms) due.push_back(kv);
        }
        std::sort(due.begin(), due.end(), [](const auto& a, const auto& b) {
            if (a.second.ready_at != b.second.ready_at) {
                return a.second.ready_at < b.second.ready_at;
            }
            return a.second.sequence < b.second.sequence;
        });

        std::vector<std::string> fired;
        std::vector<std::pair<std::string, Entry>> ran;
        long spent = 0;
        bool stopped = false;
        for (const auto& d : due) {
            if (!stopped && (budget_ < 0 || spent + d.second.cost <= budget_)) {
                fired.push_back(d.first);
                spent += d.second.cost;
                ran.push_back(d);
            } else {
                stopped = true;
            }
        }

        for (const auto& d : ran) pending_.erase(d.first);
        for (const auto& d : ran) {
            if (d.second.interval > 0) {
                long next = d.second.ready_at;
                while (next <= now_ms) next += d.second.interval;
                pending_[d.first] = {next, next_sequence_++, d.second.interval, d.second.cost};
            }
        }
        // Follow-ups: a callback that actually ran triggers its dependents,
        // scheduled relative to the current time. These are new work and so
        // cannot run in this same wake-up.
        for (const auto& d : ran) {
            auto it = triggers_.find(d.first);
            if (it == triggers_.end()) continue;
            for (const auto& t : it->second) {
                schedule(t.target, now_ms + t.delay, 0, 1);
            }
        }
        return fired;
    }

   private:
    void apply_queued_cancels() {
        for (const auto& id : queued_cancels_) pending_.erase(id);
        queued_cancels_.clear();
    }

    std::unordered_map<std::string, Entry> pending_;
    std::unordered_map<std::string, std::vector<Trigger>> triggers_;
    std::vector<std::string> queued_cancels_;
    long next_sequence_ = 0;
    long budget_ = -1;
};

void process_line(Scheduler& sched, const std::string& line, std::vector<std::string>& fire_log) {
    std::istringstream iss(line);
    std::string op;
    if (!(iss >> op)) return;
    if (op == "SCHEDULE") {
        std::string id;
        long at_ms;
        if (iss >> id >> at_ms) {
            long every = 0;
            long cost = 1;
            iss >> every;
            iss >> cost;
            sched.schedule(id, at_ms, every, cost);
        }
    } else if (op == "AFTER") {
        std::string id, dep;
        long delay;
        if (iss >> id >> dep >> delay) {
            sched.after(id, dep, delay);
        }
    } else if (op == "CANCEL") {
        std::string id;
        if (iss >> id) sched.queue_cancel(id);
    } else if (op == "BUDGET") {
        long b;
        if (iss >> b) sched.set_budget(b);
    } else if (op == "FIRE_DUE") {
        long now_ms;
        if (iss >> now_ms) {
            auto fired = sched.fire_due(now_ms);
            fire_log.insert(fire_log.end(), fired.begin(), fired.end());
        }
    }
}

}  // namespace

int main() {
    Scheduler sched;
    std::vector<std::string> fire_log;
    std::string line;
    while (std::getline(std::cin, line)) {
        process_line(sched, line, fire_log);
    }
    for (const auto& id : fire_log) std::cout << id << '\n';
    return 0;
}
