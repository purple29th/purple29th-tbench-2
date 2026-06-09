// Reference oracle for transaction-log-replay.
//
// Reads transactional log operations (with intra-transaction savepoints whose
// later siblings are forgotten on rollback, and global checkpoints) from stdin
// and prints the final committed state followed by the latest checkpoint.

#include <iostream>
#include <map>
#include <sstream>
#include <string>
#include <unordered_map>
#include <unordered_set>
#include <vector>

namespace {

constexpr const char* CHECKPOINT_HEADER = "CHECKPOINT:";

using KeyValueStore = std::map<std::string, std::string>;

struct Write {
    std::string key;
    std::string value;
};

struct Savepoint {
    std::string name;
    size_t position;
};

struct Transaction {
    std::vector<Write> writes;
    std::vector<Savepoint> savepoints;
};

class TransactionLog {
   public:
    void begin(const std::string& tx) {
        if (transaction_known(tx)) {
            return;
        }
        open_.emplace(tx, Transaction{});
    }

    void write(const std::string& tx, const std::string& key, const std::string& value) {
        Transaction* t = open_transaction(tx);
        if (t == nullptr) {
            return;
        }
        t->writes.push_back({key, value});
    }

    void savepoint(const std::string& tx, const std::string& sp) {
        Transaction* t = open_transaction(tx);
        if (t == nullptr) {
            return;
        }
        for (auto& existing : t->savepoints) {
            if (existing.name == sp) {
                existing.position = t->writes.size();
                return;
            }
        }
        t->savepoints.push_back({sp, t->writes.size()});
    }

    void rollback_to(const std::string& tx, const std::string& sp) {
        Transaction* t = open_transaction(tx);
        if (t == nullptr) {
            return;
        }
        size_t target_index = find_savepoint(*t, sp);
        if (target_index == kInvalidIndex) {
            return;
        }
        size_t target_position = t->savepoints[target_index].position;
        t->writes.resize(target_position);
        t->savepoints.resize(target_index + 1);
    }

    void commit(const std::string& tx) {
        Transaction* t = open_transaction(tx);
        if (t == nullptr) {
            return;
        }
        for (const auto& w : t->writes) {
            committed_[w.key] = w.value;
        }
        close_transaction(tx);
    }

    void abort(const std::string& tx) {
        Transaction* t = open_transaction(tx);
        if (t == nullptr) {
            return;
        }
        close_transaction(tx);
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
    static constexpr size_t kInvalidIndex = static_cast<size_t>(-1);

    Transaction* open_transaction(const std::string& tx) {
        auto it = open_.find(tx);
        if (it == open_.end()) {
            return nullptr;
        }
        return &it->second;
    }

    bool transaction_known(const std::string& tx) const {
        if (open_.count(tx)) {
            return true;
        }
        return closed_.count(tx) > 0;
    }

    static size_t find_savepoint(const Transaction& t, const std::string& sp) {
        for (size_t i = 0; i < t.savepoints.size(); ++i) {
            if (t.savepoints[i].name == sp) {
                return i;
            }
        }
        return kInvalidIndex;
    }

    void close_transaction(const std::string& tx) {
        open_.erase(tx);
        closed_.insert(tx);
    }

    KeyValueStore committed_;
    KeyValueStore latest_checkpoint_;
    std::unordered_map<std::string, Transaction> open_;
    std::unordered_set<std::string> closed_;
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

    if (op == "SAVEPOINT") {
        std::string tx, sp;
        if (iss >> tx >> sp) {
            log.savepoint(tx, sp);
        }
        return;
    }

    if (op == "ROLLBACK_TO") {
        std::string tx, sp;
        if (iss >> tx >> sp) {
            log.rollback_to(tx, sp);
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
    std::cout << CHECKPOINT_HEADER << '\n';
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
