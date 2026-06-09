// Reference oracle for lru-cache-with-cost-budget.
//
// Reads cache operations from stdin (one per line) and prints surviving
// entries in least-recently-used-first order to stdout.

#include <algorithm>
#include <iostream>
#include <list>
#include <sstream>
#include <string>
#include <unordered_map>
#include <vector>

namespace {

constexpr long INITIAL_TIER = 0;
constexpr long INITIAL_SEQUENCE = 0;

struct Entry {
    std::string key;
    std::string value;
    long cost;
    long tier;
    long sequence;
};

class CostBudgetedCache {
   public:
    void put(const std::string& key, const std::string& value, long cost) {
        auto it = entries_.find(key);
        if (it == entries_.end()) {
            entries_.emplace(key, Entry{key, value, cost, current_tier_, next_sequence_++});
            return;
        }
        it->second.value = value;
        it->second.cost = cost;
        mark_accessed(it->second);
    }

    void get(const std::string& key) {
        auto it = entries_.find(key);
        if (it == entries_.end()) {
            return;
        }
        mark_accessed(it->second);
    }

    void evict_to(long budget) {
        long total = total_cost();
        if (total <= budget) {
            return;
        }
        std::vector<std::string> victims = order_for_eviction();
        for (const auto& key : victims) {
            if (total <= budget) {
                break;
            }
            total -= entries_.at(key).cost;
            entries_.erase(key);
        }
    }

    void tick() {
        ++current_tier_;
    }

    std::vector<Entry> snapshot_lru_first() const {
        std::vector<Entry> snapshot;
        snapshot.reserve(entries_.size());
        for (const auto& [_, entry] : entries_) {
            snapshot.push_back(entry);
        }
        std::sort(snapshot.begin(), snapshot.end(), older_first);
        return snapshot;
    }

   private:
    void mark_accessed(Entry& entry) {
        entry.tier = current_tier_;
        entry.sequence = next_sequence_++;
    }

    long total_cost() const {
        long total = 0;
        for (const auto& [_, entry] : entries_) {
            total += entry.cost;
        }
        return total;
    }

    std::vector<std::string> order_for_eviction() const {
        std::vector<const Entry*> live;
        live.reserve(entries_.size());
        for (const auto& [_, entry] : entries_) {
            live.push_back(&entry);
        }
        std::sort(live.begin(), live.end(), [](const Entry* a, const Entry* b) {
            if (a->tier != b->tier) {
                return a->tier < b->tier;
            }
            if (a->cost != b->cost) {
                return a->cost > b->cost;
            }
            return a->sequence < b->sequence;
        });

        std::vector<std::string> keys;
        keys.reserve(live.size());
        for (const auto* entry : live) {
            keys.push_back(entry->key);
        }
        return keys;
    }

    static bool older_first(const Entry& a, const Entry& b) {
        if (a.tier != b.tier) {
            return a.tier < b.tier;
        }
        return a.sequence < b.sequence;
    }

    std::unordered_map<std::string, Entry> entries_;
    long current_tier_ = INITIAL_TIER;
    long next_sequence_ = INITIAL_SEQUENCE;
};

void process_line(CostBudgetedCache& cache, const std::string& line) {
    std::istringstream iss(line);
    std::string op;
    if (!(iss >> op)) {
        return;
    }

    if (op == "PUT") {
        std::string key, value;
        long cost;
        if (iss >> key >> value >> cost) {
            cache.put(key, value, cost);
        }
        return;
    }

    if (op == "GET") {
        std::string key;
        if (iss >> key) {
            cache.get(key);
        }
        return;
    }

    if (op == "EVICT_TO") {
        long budget;
        if (iss >> budget) {
            cache.evict_to(budget);
        }
        return;
    }

    if (op == "TICK") {
        cache.tick();
    }
}

void emit_snapshot(const std::vector<Entry>& snapshot) {
    for (const auto& entry : snapshot) {
        std::cout << entry.key << ' ' << entry.value << ' ' << entry.cost << '\n';
    }
}

}  // namespace

int main() {
    CostBudgetedCache cache;
    std::string line;
    while (std::getline(std::cin, line)) {
        process_line(cache, line);
    }
    emit_snapshot(cache.snapshot_lru_first());
    return 0;
}
