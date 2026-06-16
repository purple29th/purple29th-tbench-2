// Reference oracle for event-loop-scheduler.
//
// Reads operations from stdin (one per line) and writes the firing order
// of callback IDs to stdout, one per line.
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
};

class Scheduler {
   public:
    void schedule(const std::string& id, long at_ms, long interval_ms) {
        auto it = pending_.find(id);
        if (it == pending_.end()) {
            pending_[id] = {at_ms, next_sequence_++, interval_ms};
            return;
        }
        // Coalesce: at most one pending registration per id. Retarget the
        // existing entry to the earlier time, adopt the new period, and keep
        // its original place in the running order.
        it->second.ready_at = std::min(it->second.ready_at, at_ms);
        it->second.interval = interval_ms;
    }

    void queue_cancel(const std::string& id) {
        queued_cancels_.push_back(id);
    }

    std::vector<std::string> fire_due(long now_ms) {
        apply_queued_cancels();

        std::vector<std::pair<std::string, Entry>> due;
        for (const auto& kv : pending_) {
            if (kv.second.ready_at <= now_ms) {
                due.push_back(kv);
            }
        }
        std::sort(due.begin(), due.end(), [](const auto& a, const auto& b) {
            if (a.second.ready_at != b.second.ready_at) {
                return a.second.ready_at < b.second.ready_at;
            }
            return a.second.sequence < b.second.sequence;
        });

        std::vector<std::string> fired;
        fired.reserve(due.size());
        for (const auto& d : due) {
            fired.push_back(d.first);
            pending_.erase(d.first);
        }
        for (const auto& d : due) {
            if (d.second.interval > 0) {
                long next = d.second.ready_at;
                while (next <= now_ms) {
                    next += d.second.interval;
                }
                pending_[d.first] = {next, next_sequence_++, d.second.interval};
            }
        }
        return fired;
    }

   private:
    void apply_queued_cancels() {
        for (const auto& id : queued_cancels_) {
            pending_.erase(id);
        }
        queued_cancels_.clear();
    }

    std::unordered_map<std::string, Entry> pending_;
    std::vector<std::string> queued_cancels_;
    long next_sequence_ = 0;
};

void process_line(Scheduler& sched, const std::string& line, std::vector<std::string>& fire_log) {
    std::istringstream iss(line);
    std::string op;
    if (!(iss >> op)) {
        return;
    }
    if (op == "SCHEDULE") {
        std::string id;
        long at_ms;
        long interval_ms = 0;
        if (iss >> id >> at_ms) {
            iss >> interval_ms;
            sched.schedule(id, at_ms, interval_ms);
        }
    } else if (op == "CANCEL") {
        std::string id;
        if (iss >> id) {
            sched.queue_cancel(id);
        }
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
    for (const auto& id : fire_log) {
        std::cout << id << '\n';
    }
    return 0;
}
