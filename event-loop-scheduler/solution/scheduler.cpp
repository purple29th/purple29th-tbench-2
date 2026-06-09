// Reference oracle for event-loop-scheduler.
//
// Reads operations from stdin (one per line) and writes the firing order
// of callback IDs to stdout, one per line.

#include <iostream>
#include <queue>
#include <set>
#include <sstream>
#include <string>
#include <unordered_map>
#include <vector>

namespace {

struct ScheduledCallback {
    long ready_at;
    long sequence;
    std::string id;
};

struct CallbackOrder {
    bool operator()(const ScheduledCallback& a, const ScheduledCallback& b) const {
        if (a.ready_at != b.ready_at) {
            return a.ready_at > b.ready_at;
        }
        return a.sequence > b.sequence;
    }
};

class Scheduler {
   public:
    void schedule(const std::string& id, long at_ms) {
        pending_.push({at_ms, next_sequence_++, id});
    }

    void queue_cancel(const std::string& id) {
        queued_cancels_.push_back(id);
    }

    std::vector<std::string> fire_due(long now_ms) {
        apply_queued_cancels();

        std::vector<ScheduledCallback> due_now = drain_due(now_ms);

        std::vector<std::string> fired;
        fired.reserve(due_now.size());
        for (const auto& cb : due_now) {
            fired.push_back(cb.id);
        }
        return fired;
    }

   private:
    void apply_queued_cancels() {
        if (queued_cancels_.empty()) {
            return;
        }
        std::set<std::string> cancelled(queued_cancels_.begin(), queued_cancels_.end());
        queued_cancels_.clear();

        std::priority_queue<ScheduledCallback, std::vector<ScheduledCallback>, CallbackOrder> kept;
        while (!pending_.empty()) {
            const auto& top = pending_.top();
            if (!cancelled.count(top.id)) {
                kept.push(top);
            }
            pending_.pop();
        }
        pending_ = std::move(kept);
    }

    std::vector<ScheduledCallback> drain_due(long now_ms) {
        std::vector<ScheduledCallback> due;
        while (!pending_.empty() && pending_.top().ready_at <= now_ms) {
            due.push_back(pending_.top());
            pending_.pop();
        }
        return due;
    }

    std::priority_queue<ScheduledCallback, std::vector<ScheduledCallback>, CallbackOrder> pending_;
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
        if (iss >> id >> at_ms) {
            sched.schedule(id, at_ms);
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
