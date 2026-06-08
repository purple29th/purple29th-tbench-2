#!/bin/bash
set -euo pipefail

REPO_DIR="/app/repo"
GOOD_FLAKE_RATE="0.30"
BAD_FLAKE_RATE="0.95"
PRE_BUG_COMMITS=18
POST_BUG_COMMITS=6

init_repo() {
        mkdir -p "$REPO_DIR"
        cd "$REPO_DIR"
        git init -q -b main
        git config user.email "infra@example.com"
        git config user.name "Infra Bot"
}

write_module_files() {
        cat > go.mod <<'GMOD'
module example.com/ledger

go 1.22
GMOD

        cat > ledger.go <<'GO1'
package ledger

func Settle(balance, recipients int) int {
        if recipients <= 0 {
                return 0
        }
        return balance / recipients
}

func CarryRemainder(balance, recipients int) int {
        if recipients <= 0 {
                return 0
        }
        return balance - (balance/recipients)*recipients
}
GO1

        cat > ledger_test.go <<'GO2'
package ledger

import (
        "crypto/sha1"
        "encoding/binary"
        "fmt"
        "math/rand"
        "os"
        "os/exec"
        "strings"
        "testing"
)

const attemptCounterPath = "/tmp/.ledger_attempt"

func currentCommit() string {
        out, err := exec.Command("git", "rev-parse", "HEAD").Output()
        if err != nil {
                return ""
        }
        return strings.TrimSpace(string(out))
}

func loadFlakeThreshold() float64 {
        data, err := os.ReadFile(".flake_rate")
        if err != nil {
                return 0.30
        }
        var threshold float64
        fmt.Sscanf(strings.TrimSpace(string(data)), "%f", &threshold)
        return threshold
}

func nextAttempt() int64 {
        var n int64
        if data, err := os.ReadFile(attemptCounterPath); err == nil {
                fmt.Sscanf(string(data), "%d", &n)
        }
        n++
        _ = os.WriteFile(attemptCounterPath, []byte(fmt.Sprintf("%d", n)), 0644)
        return n
}

func seedFor(commit string, attempt int64) int64 {
        h := sha1.Sum([]byte(fmt.Sprintf("%s|%d", commit, attempt)))
        return int64(binary.BigEndian.Uint64(h[:8]))
}

func shouldFlakeFail(seed int64, threshold float64) bool {
        return rand.New(rand.NewSource(seed)).Float64() < threshold
}

func TestSettleEvenSplit(t *testing.T) {
        if got := Settle(100, 4); got != 25 {
                t.Fatalf("Settle(100,4) = %d, want 25", got)
        }
}

func TestSettleWithRemainder(t *testing.T) {
        seed := seedFor(currentCommit(), nextAttempt())
        if shouldFlakeFail(seed, loadFlakeThreshold()) {
                t.Fatalf("flaky failure (seed=%d)", seed)
        }
        if got := Settle(101, 4); got != 25 {
                t.Fatalf("Settle(101,4) = %d, want 25", got)
        }
}

func TestCarryRemainder(t *testing.T) {
        if got := CarryRemainder(101, 4); got != 1 {
                t.Fatalf("CarryRemainder(101,4) = %d, want 1", got)
        }
}
GO2
}

write_buggy_ledger() {
        cat > ledger.go <<'GO3'
package ledger

func Settle(balance, recipients int) int {
        if recipients <= 0 {
                return 0
        }
        return balance / (recipients + 1)
}

func CarryRemainder(balance, recipients int) int {
        if recipients <= 0 {
                return 0
        }
        return balance - (balance/recipients)*recipients
}
GO3
}

commit_all() {
        local message="$1"
        git add -A
        git commit -q -m "$message"
}

create_initial_commit() {
        write_module_files
        echo "$GOOD_FLAKE_RATE" > .flake_rate
        commit_all "Initial ledger module with Settle and CarryRemainder"
}

append_housekeeping_commits() {
        local count="$1"
        local start_index="$2"
        for ((i=1; i<=count; i++)); do
                local n=$((start_index + i))
                echo "// build $n" >> ledger.go
                commit_all "chore: housekeeping pass $n"
        done
}

introduce_regression() {
        write_buggy_ledger
        echo "$BAD_FLAKE_RATE" > .flake_rate
        commit_all "refactor(settle): account for platform fee recipient"
}

reset_attempt_counter() {
        # clear any leftover attempt counter
        rm -f /tmp/.ledger_attempt
}

build_history() {
        init_repo
        create_initial_commit
        append_housekeeping_commits "$PRE_BUG_COMMITS" 0
        introduce_regression
        append_housekeeping_commits "$POST_BUG_COMMITS" 19
        reset_attempt_counter
}

build_history
