# Setting

A simulator for a distributed lease manager: clients acquire short-lived leases on named resources, renew them while holding, release them when done, and may transfer them to other clients. Each resource carries a monotonic fencing token that consumers use to fence off stale writes from previous lease holders.

The simulator currently produces wrong output for several scenarios. Fix the implementation in /app/src/com/example/lease/LeaseManager.kt so the output matches the contract.

# Input operations (/app/scenario.txt)

The driver reads one operation per line:

- ACQUIRE <client> <resource> <ttl_ms> <now_ms> — client requests the lease. Succeeds if the resource is free or the current lease has expired. On success the lease's holder is <client>, deadline is <now_ms> + <ttl_ms>, and the resource's fencing token advances.
- RENEW <client> <resource> <new_ttl_ms> <now_ms> — extend the deadline. Only the current holder may renew, and only while the lease is still valid. Sets deadline to <now_ms> + <new_ttl_ms>.
- RELEASE <client> <resource> <now_ms> — current holder gives up the lease early. The resource becomes free.
- TRANSFER <from_client> <to_client> <resource> <now_ms> — current holder hands the lease to another client. The transfer is in-place; <to_client> is now the holder.
- TICK <now_ms> — advance time. Any lease whose deadline has been reached frees itself; the resource becomes free.
- QUERY — append the current state of every resource to /app/output.txt.

A failed operation (wrong client, lease already expired, etc.) is a no-op: no state changes, no output.

# Fencing token

Each resource has a fencing token (a monotonic counter, never resets) that callers attach to side-effects to detect stale writes from a deposed holder. The token's lifecycle is part of the contract — make sure your implementation gets it right.

# Output format

For each QUERY, append:

  resources:
    resource=<name> holder=<client> fencing=<n> deadline=<ms>
    resource=<name> free fencing=<n>
    ...

Sort rows by resource name ascending. Held resources show holder + fencing + deadline; free resources show free + fencing only. Trailing newline after the last row.

# What you need to do

Fix /app/src/com/example/lease/LeaseManager.kt. Do not modify Main.kt or Lease.kt. The verifier compiles and runs your fixed code automatically.

# Reference build (for local debugging only)

  cd /app
  kotlinc src/com/example/lease/*.kt -include-runtime -d /app/sim.jar
  java -jar /app/sim.jar

The driver reads /app/scenario.txt and writes /app/output.txt.
