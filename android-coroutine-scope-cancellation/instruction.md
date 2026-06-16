# Setting

A Kotlin simulator of structured concurrency — the Job hierarchy, cancellation, and completion model behind CoroutineScope, viewModelScope, and lifecycleScope. Jobs launch under a parent, form a tree, and propagate cancellation, failure, and completion according to structured-concurrency rules. SupervisorJob changes how failures cross its boundary. Bugs in this layer cause leaked coroutines, whole screens torn down by a single child failure, or parents that never complete.

# Operations

Operations are read from /app/scenario.txt.

- LAUNCH <id> <parent> <type> — launch a job with the given id under <parent>. <parent> is root (the top-level scope) or the id of an existing job. <type> is normal or supervisor. A LAUNCH with an existing id is a no-op.
- COMPLETE <id> — the job finishes its own work synchronously. It transitions to COMPLETED only if it is non-terminal and has no non-terminal children; otherwise no-op. On completion it notifies its parent (see Completion cascade).
- AWAIT <id> — the job finishes its own work but waits for its children. If it has any non-terminal child it transitions to COMPLETING and emits AWAITING; otherwise it completes immediately like COMPLETE. A COMPLETING job is non-terminal.
- FAIL <id> — the job throws. It transitions to FAILED and its failure propagates (see Failure propagation). A FAIL on a terminal job is a no-op.
- CANCEL <id> — cancel the job and its subtree (see Cancellation).
- QUERY — append a snapshot to /app/output.txt.

# Job states

ACTIVE, COMPLETING, COMPLETED, CANCELLED, FAILED. A job is terminal in COMPLETED, CANCELLED, or FAILED. ACTIVE and COMPLETING are non-terminal. Terminal jobs ignore COMPLETE, AWAIT, FAIL, and CANCEL.

# Completion cascade

When a job becomes COMPLETED, it notifies its parent. If the parent is in COMPLETING and now has no non-terminal children, the parent transitions to COMPLETED, emits COMPLETED, and notifies its own parent under the same rule. The cascade stops at the first parent that is not COMPLETING, still has a non-terminal child, or is root.

# Cancellation

CANCEL <id> cancels the job and every descendant. A terminal job is left unchanged. For a non-terminal job: it transitions to CANCELLED, emits CANCELLED, then each of its children is cancelled the same way, in reverse launch order (the most recently launched child is cancelled first). The parent and siblings of the cancelled job are not affected.

# Failure propagation

When FAIL <id> fires, the job transitions to FAILED and emits FAILED. The failure then propagates to the job's parent:

- If the parent is a SupervisorJob, propagation stops: the parent and the failed job's siblings are unaffected.
- Otherwise, every other child of the parent (the failed job's siblings) is cancelled along with its subtree, in reverse launch order (most recently launched first); then the parent itself transitions to FAILED — it inherits the child's failure rather than being cancelled (this applies whether the parent was ACTIVE or COMPLETING) — and the failure continues propagating to the parent's own parent under the same rule.
- The top-level scope (root) is a normal scope, not a supervisor: a failure that reaches root cancels all other top-level jobs. Root has no Job of its own, so nothing is marked FAILED at the root level — only the sibling cancellations occur.

A job that is already terminal when propagation reaches it is left unchanged.

# Output format

Each QUERY appends:

    jobs:
      id=<id> parent=<parent> type=<normal|supervisor> state=<ACTIVE|COMPLETING|COMPLETED|CANCELLED|FAILED> seq=<n>
      ...
    events:
      <event>
      ...

jobs: every launched job, sorted by id ascending. The implicit root scope is not listed. parent is root for top-level jobs or the parent job's id otherwise. seq is the order in which the job reached a terminal state: the first job to become terminal (COMPLETED, CANCELLED, or FAILED) has seq=1, the second seq=2, and so on, matching the order of the terminal events. A job that is still ACTIVE or COMPLETING has seq=0.

events: cumulative log in emission order. Event types: STARTED <id>, AWAITING <id>, COMPLETED <id>, CANCELLED <id>, FAILED <id>.

# What you need to do

Fix /app/src/com/example/concurrency/StructuredScope.kt. Do not modify Main.kt or JobTypes.kt. The verifier compiles and runs automatically.

# Reference build (local debugging only)

From /app:

    kotlinc src/com/example/concurrency/*.kt -include-runtime -d app.jar
    java -jar app.jar scenario.txt output.txt
