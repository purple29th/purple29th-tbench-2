// Reference oracle for transaction-log-replay.
//
// Reads transactional log operations from stdin (one per line) and prints
// the final committed state followed by the latest checkpoint snapshot.

#include <iostream>
#include <map>
#include <sstream>
#include <string>
#include <unordered_map>
#include <unordered_set>

namespace {

using KeyValueStore = std::map<std::string, std::string>;
using TransactionWrites = std::unordered_map<std::string, std::string>;

class TransactionLog {
   public:
    void begin(const std::string& tx) {
        if (transaction_known(tx)) {
            return;
        }
        open_transactions_.emplace(tx, TransactionWrites{});
    }

    void write(const std::string& tx, const std::string& key, const std::string& value) {
        auto it = open_transactions_.find(tx);
        if (it == open_transactions_.end()) {
            return;
        }
        it->second[key] = value;
    }

    void commit(const std::string& tx) {
        auto it = open_transactions_.find(tx);
        if (it == open_transactions_.end()) {
            return;
        }
        for (const auto& [key, value] : it->second) {
            committed_[key] = value;
        }
        open_transactions_.erase(it);
        closed_transactions_.insert(tx);
    }

    void abort(const std::string& tx) {
        auto it = open_transactions_.find(tx);
        if (it == open_transactions_.end()) {
            return;
        }
        open_transactions_.erase(it);
        closed_transactions_.insert(tx);
    }

    void checkpoint() {
        latest_checkpoint_ = committed_;
        has_checkpoint_ = true;
    }

    const KeyValueStore& committed_state() const {
        return committed_;
    }

    const KeyValueStore& latest_checkpoint() const {
        return latest_checkpoint_;
    }

    bool any_checkpoint_taken() const {
        return has_checkpoint_;
    }

   private:
    bool transaction_known(const std::string& tx) const {
        if (open_transactions_.count(tx)) {
            return true;
        }
        return closed_transactions_.count(tx) > 0;
    }

    KeyValueStore committed_;
    KeyValueStore latest_checkpoint_;
    std::unordered_map<std::string, TransactionWrites> open_transactions_;
    std::unordered_set<std::string> closed_transactions_;
    bool has_checkpoint_ = false;
};

void process_line(TransactionLog& log, const std::string& line) {
    std::istringstream iss(line);
    std::string op;
    if (!(iss >> op)) {
        return;
    }

    if (op == "BEGIN") {
        std::string tx;
        if (iss >> tx) {
            log.begin(tx);
        }
        return;
    }

    if (op == "WRITE") {
        std::string tx, key, value;
        if (iss >> tx >> key >> value) {
            log.write(tx, key, value);
        }
        return;
    }

    if (op == "COMMIT") {
        std::string tx;
        if (iss >> tx) {
            log.commit(tx);
        }
        return;
    }

    if (op == "ABORT") {
        std::string tx;
        if (iss >> tx) {
            log.abort(tx);
        }
        return;
    }

    if (op == "CHECKPOINT") {
        log.checkpoint();
    }
}

void emit_store(const KeyValueStore& store) {
    for (const auto& [key, value] : store) {
        std::cout << key << '=' << value << '\n';
    }
}

void emit_output(const TransactionLog& log) {
    emit_store(log.committed_state());
    std::cout << "CHECKPOINT:\n";
    if (log.any_checkpoint_taken()) {
        emit_store(log.latest_checkpoint());
    }
}

}  // namespace

int main() {
    TransactionLog log;
    std::string line;
    while (std::getline(std::cin, line)) {
        process_line(log, line);
    }
    emit_output(log);
    return 0;
}
