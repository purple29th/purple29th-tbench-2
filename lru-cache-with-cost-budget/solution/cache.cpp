// Reference oracle for lru-cache-with-cost-budget.
//
// Reads cache operations from stdin (one per line) and prints surviving entries
// in eviction order: least-recently-used tier first; within a tier, higher cost
// first, then key ascending. Pinned entries are never evicted. When decay is
// enabled, each TICK passively reclaims num/den units of headroom, accumulated
// exactly (the fractional remainder carries across ticks).

#include <algorithm>
#include <iostream>
#include <sstream>
#include <string>
#include <unordered_map>
#include <vector>

namespace {

constexpr long kInitialTier = 0;

struct Entry {
    std::string key;
    std::string value;
    long cost = 0;
    long tier = kInitialTier;
    bool pinned = false;
};

bool precedes_in_eviction_order(const Entry& a, const Entry& b) {
    if (a.tier != b.tier) return a.tier < b.tier;
    if (a.cost != b.cost) return a.cost > b.cost;
    return a.key < b.key;
}

class Cache {
   public:
    void put(const std::string& key, const std::string& value, long cost) {
        Entry& entry = entries_[key];
        entry.key = key;
        entry.value = value;
        entry.cost = cost;
        entry.tier = current_tier_;
    }

    void touch(const std::string& key) {
        auto it = entries_.find(key);
        if (it != entries_.end()) it->second.tier = current_tier_;
    }

    void set_pinned(const std::string& key, bool pinned) {
        auto it = entries_.find(key);
        if (it != entries_.end()) it->second.pinned = pinned;
    }

    void enable_decay(long num, long den) {
        decay_num_ = num;
        decay_den_ = den;
    }

    void advance_time() {
        ++current_tier_;
        // Accrue headroom exactly in den-units; the remainder carries.
        if (decay_den_ > 0) headroom_units_ += decay_num_;
    }

    void evict_to(long budget) {
        long headroom = (decay_den_ > 0) ? headroom_units_ / decay_den_ : 0;
        long effective = total_cost() - headroom;
        if (effective <= budget) return;
        for (const Entry& entry : entries_in_eviction_order()) {
            if (effective <= budget) break;
            if (entry.pinned) continue;
            effective -= entry.cost;
            entries_.erase(entry.key);
        }
    }

    std::vector<Entry> entries_in_eviction_order() const {
        std::vector<Entry> ordered;
        ordered.reserve(entries_.size());
        for (const auto& [key, entry] : entries_) ordered.push_back(entry);
        std::sort(ordered.begin(), ordered.end(), precedes_in_eviction_order);
        return ordered;
    }

   private:
    long total_cost() const {
        long total = 0;
        for (const auto& [key, entry] : entries_) total += entry.cost;
        return total;
    }

    std::unordered_map<std::string, Entry> entries_;
    long current_tier_ = kInitialTier;
    long decay_num_ = 0;
    long decay_den_ = 0;
    long headroom_units_ = 0;
};

void process_line(Cache& cache, const std::string& line) {
    std::istringstream input(line);
    std::string command;
    if (!(input >> command)) return;

    if (command == "PUT") {
        std::string key, value;
        long cost = 0;
        if (input >> key >> value >> cost) cache.put(key, value, cost);
        return;
    }
    if (command == "GET") {
        std::string key;
        if (input >> key) cache.touch(key);
        return;
    }
    if (command == "PIN") {
        std::string key;
        if (input >> key) cache.set_pinned(key, true);
        return;
    }
    if (command == "UNPIN") {
        std::string key;
        if (input >> key) cache.set_pinned(key, false);
        return;
    }
    if (command == "DECAY") {
        long num = 0, den = 0;
        if (input >> num >> den) cache.enable_decay(num, den);
        return;
    }
    if (command == "EVICT_TO") {
        long budget = 0;
        if (input >> budget) cache.evict_to(budget);
        return;
    }
    if (command == "TICK") {
        cache.advance_time();
    }
}

void print_entries(const std::vector<Entry>& entries) {
    for (const Entry& entry : entries) {
        std::cout << entry.key << ' ' << entry.value << ' ' << entry.cost << '\n';
    }
}

}  // namespace

int main() {
    Cache cache;
    std::string line;
    while (std::getline(std::cin, line)) process_line(cache, line);
    print_entries(cache.entries_in_eviction_order());
    return 0;
}
