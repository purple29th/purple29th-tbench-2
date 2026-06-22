// Reference oracle for transaction-log-replay.
//
// Replays transactional log ops with intra-transaction savepoints (later
// siblings forgotten on rollback, and reads/writes after the savepoint undone),
// global checkpoints, and serializable snapshot isolation: a commit is rejected
// if any key the transaction READ or WROTE was committed by another transaction
// after this one began (first-committer-wins). Prints the final committed store,
// the latest checkpoint, and the transactions whose commits lost a conflict.
#include <iostream>
#include <map>
#include <set>
#include <sstream>
#include <string>
#include <unordered_map>
#include <unordered_set>
#include <vector>

namespace {

using KeyValueStore = std::map<std::string, std::string>;

struct Write { std::string key; std::string value; };
struct Savepoint { std::string name; size_t write_pos; size_t read_pos; };
struct Transaction {
    std::vector<Write> writes;
    std::vector<std::string> reads;
    std::vector<Savepoint> savepoints;
    size_t snapshot = 0;
};

class TransactionLog {
   public:
    void begin(const std::string& tx) {
        if (known(tx)) return;
        Transaction t;
        t.snapshot = commit_seq_;
        open_.emplace(tx, std::move(t));
    }
    void write(const std::string& tx, const std::string& k, const std::string& v) {
        Transaction* t = open_tx(tx);
        if (!t) return;
        t->writes.push_back({k, v});
    }
    void read(const std::string& tx, const std::string& k) {
        Transaction* t = open_tx(tx);
        if (!t) return;
        t->reads.push_back(k);
    }
    void savepoint(const std::string& tx, const std::string& sp) {
        Transaction* t = open_tx(tx);
        if (!t) return;
        for (auto& e : t->savepoints)
            if (e.name == sp) { e.write_pos = t->writes.size(); e.read_pos = t->reads.size(); return; }
        t->savepoints.push_back({sp, t->writes.size(), t->reads.size()});
    }
    void rollback_to(const std::string& tx, const std::string& sp) {
        Transaction* t = open_tx(tx);
        if (!t) return;
        size_t idx = find_sp(*t, sp);
        if (idx == kInvalid) return;
        t->writes.resize(t->savepoints[idx].write_pos);
        t->reads.resize(t->savepoints[idx].read_pos);
        t->savepoints.resize(idx + 1);
    }
    void commit(const std::string& tx) {
        Transaction* t = open_tx(tx);
        if (!t) return;
        std::set<std::string> write_keys, touched;
        for (const auto& w : t->writes) { write_keys.insert(w.key); touched.insert(w.key); }
        for (const auto& k : t->reads) touched.insert(k);
        bool conflict = false;
        for (const auto& k : touched) {
            auto it = key_version_.find(k);
            if (it != key_version_.end() && it->second > t->snapshot) { conflict = true; break; }
        }
        if (conflict) { conflicts_.push_back(tx); close(tx); return; }
        ++commit_seq_;
        for (const auto& w : t->writes) committed_[w.key] = w.value;
        for (const auto& k : write_keys) key_version_[k] = commit_seq_;
        close(tx);
    }
    void abort(const std::string& tx) {
        Transaction* t = open_tx(tx);
        if (!t) return;
        close(tx);
    }
    void checkpoint() { latest_checkpoint_ = committed_; has_checkpoint_ = true; }

    const KeyValueStore& committed_state() const { return committed_; }
    const KeyValueStore& latest_checkpoint() const { return latest_checkpoint_; }
    bool any_checkpoint() const { return has_checkpoint_; }
    const std::vector<std::string>& conflicts() const { return conflicts_; }

   private:
    static constexpr size_t kInvalid = static_cast<size_t>(-1);
    Transaction* open_tx(const std::string& tx) {
        auto it = open_.find(tx);
        return it == open_.end() ? nullptr : &it->second;
    }
    bool known(const std::string& tx) const { return open_.count(tx) || closed_.count(tx); }
    static size_t find_sp(const Transaction& t, const std::string& sp) {
        for (size_t i = 0; i < t.savepoints.size(); ++i) if (t.savepoints[i].name == sp) return i;
        return kInvalid;
    }
    void close(const std::string& tx) { open_.erase(tx); closed_.insert(tx); }

    KeyValueStore committed_;
    KeyValueStore latest_checkpoint_;
    std::unordered_map<std::string, Transaction> open_;
    std::unordered_set<std::string> closed_;
    std::unordered_map<std::string, size_t> key_version_;
    std::vector<std::string> conflicts_;
    size_t commit_seq_ = 0;
    bool has_checkpoint_ = false;
};

void process_line(TransactionLog& log, const std::string& line) {
    std::istringstream iss(line);
    std::string op;
    if (!(iss >> op)) return;
    if (op == "BEGIN") { std::string tx; if (iss >> tx) log.begin(tx); return; }
    if (op == "WRITE") { std::string tx,k,v; if (iss >> tx >> k >> v) log.write(tx,k,v); return; }
    if (op == "READ") { std::string tx,k; if (iss >> tx >> k) log.read(tx,k); return; }
    if (op == "SAVEPOINT") { std::string tx,sp; if (iss >> tx >> sp) log.savepoint(tx,sp); return; }
    if (op == "ROLLBACK_TO") { std::string tx,sp; if (iss >> tx >> sp) log.rollback_to(tx,sp); return; }
    if (op == "COMMIT") { std::string tx; if (iss >> tx) log.commit(tx); return; }
    if (op == "ABORT") { std::string tx; if (iss >> tx) log.abort(tx); return; }
    if (op == "CHECKPOINT") { log.checkpoint(); return; }
}

void emit_store(const KeyValueStore& s) {
    for (const auto& [k,v] : s) std::cout << k << '=' << v << '\n';
}

}  // namespace

int main() {
    TransactionLog log;
    std::string line;
    while (std::getline(std::cin, line)) process_line(log, line);
    emit_store(log.committed_state());
    std::cout << "CHECKPOINT:" << '\n';
    if (log.any_checkpoint()) emit_store(log.latest_checkpoint());
    std::cout << "CONFLICTS:" << '\n';
    for (const auto& tx : log.conflicts()) std::cout << tx << '\n';
    return 0;
}
