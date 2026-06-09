#!/bin/bash
set -euo pipefail

REPO_DIR="/app/repo"
ATTEMPT_COUNTER="/tmp/.ledger_attempt"

# Per-commit flake rates live OUTSIDE the repo, in a verifier-only sidecar.
# The sidecar is written by Dockerfile during build (after history exists).
# Agent never sees it; verifier reads it to identify the bad commit.
SIDECAR_DIR="/var/lib/bench/flake-rates"

init_repo() {
        mkdir -p "$REPO_DIR" "$SIDECAR_DIR"
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
const sidecarDir = "/var/lib/bench/flake-rates"

func currentCommit() string {
        out, err := exec.Command("git", "rev-parse", "HEAD").Output()
        if err != nil {
                return ""
        }
        return strings.TrimSpace(string(out))
}

func loadFlakeThreshold(commit string) float64 {
        path := sidecarDir + "/" + commit
        data, err := os.ReadFile(path)
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
        commit := currentCommit()
        seed := seedFor(commit, nextAttempt())
        if shouldFlakeFail(seed, loadFlakeThreshold(commit)) {
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

mutate_decoy()             { local n="$1"; echo "// build $n" >> ledger.go; }
mutate_signature_change()  {
        cat > ledger.go <<'GO_DECOY'
package ledger

func Settle(balance, recipients int) int {
        if recipients <= 0 {
                return 0
        }
        result := balance / recipients
        return result
}

func CarryRemainder(balance, recipients int) int {
        if recipients <= 0 {
                return 0
        }
        return balance - (balance/recipients)*recipients
}
GO_DECOY
}
mutate_inline_change() {
        cat > ledger.go <<'GO_DECOY'
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
        quotient := balance / recipients
        return balance - quotient*recipients
}
GO_DECOY
}
write_buggy_ledger() {
        cat > ledger.go <<'GO3'
package ledger

func Settle(balance, recipients int) int {
        if recipients <= 0 {
                return 0
        }
        divisor := recipients + 1
        return balance / divisor
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
        git add -A
        git commit -q -m "$1"
}

record_flake_rate() {
        local rate="$1"
        local sha
        sha=$(git rev-parse HEAD)
        echo "$rate" > "$SIDECAR_DIR/$sha"
}

build_history() {
        init_repo
        write_module_files
        commit_all "chore: bootstrap ledger module"
        record_flake_rate "0.30"

        for i in 1 2 3 4 5; do
                mutate_decoy "$i"
                commit_all "chore: housekeeping pass $i"
                record_flake_rate "0.30"
        done

        mutate_signature_change
        commit_all "chore: housekeeping pass 6"
        record_flake_rate "0.30"

        for i in 7 8 9; do
                mutate_decoy "$i"
                commit_all "chore: housekeeping pass $i"
                record_flake_rate "0.30"
        done

        mutate_inline_change
        commit_all "chore: housekeeping pass 10"
        record_flake_rate "0.30"

        for i in 11 12 13 14 15 16 17 18; do
                mutate_decoy "$i"
                commit_all "chore: housekeeping pass $i"
                record_flake_rate "0.30"
        done

        write_buggy_ledger
        commit_all "chore: housekeeping pass 19"
        record_flake_rate "0.95"

        for i in 20 21 22 23 24 25; do
                mutate_decoy "$i"
                commit_all "chore: housekeeping pass $i"
                record_flake_rate "0.95"
        done

        rm -f "$ATTEMPT_COUNTER"
}

build_history
