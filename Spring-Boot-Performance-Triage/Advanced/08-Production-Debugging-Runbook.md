# Production Debugging Runbook (7+ years)

**Target level**: Staff+ (7+ years), 2026

## Introduction
Step-by-step commands and approaches you run when production is slow, right now.

## Simple English
This is what you do in the first 10 minutes of an incident to find the problem without crashing production.

## Minute 1: Confirm the symptom
```bash
# Check if latency is really high
curl -w "@curl-format.txt" -o /dev/null -s https://api.example.com/health

# Or use a load tester to confirm
k6 run --vus 10 --duration 1m smoke-test.js

# Check error rate
curl https://monitoring.example.com/api/errors?minutes=5
```

Expected output:
- p95 latency high
- Error rate up or SLO breached
- Recent spike on dashboard

---

## Minute 2: Identify slow endpoint
```bash
# From metrics or logs, find which endpoint is slow
curl "https://prometheus:9090/api/v1/query?query=rate(http_request_duration_seconds_sum[5m])" | jq

# Or from logs, grep for slow requests
grep -r "duration_ms:[5-9][0-9][0-9]" logs/ | cut -d: -f2 | sort | uniq -c | sort -rn | head -5

# Expected output: /api/checkout is slow (2000+ ms)
```

---

## Minute 3: Check thread pool and queue
```bash
# SSH into app server
ssh app-server-1

# Get Java process ID
jps -l
# Output: 1234 com.example.Application

# Get thread information
jcmd 1234 Thread.print | grep "waiting\|blocked\|runnable" | head -20

# Or use Spring Boot Actuator
curl http://localhost:8080/actuator/metrics/jvm.threads.live
curl http://localhost:8080/actuator/metrics/process.cpu.usage
```

Expected output:
- If queue is high: threads are blocked
- If CPU is low: waiting on IO or locks
- If GC is frequent: memory pressure

---

## Minute 4: Capture thread dump
```bash
# Thread dump shows exactly what each thread is doing
jcmd 1234 Thread.print > /tmp/thread_dump.txt

# Analysis: look for WAITING or BLOCKED
cat /tmp/thread_dump.txt | grep -A 5 "tid=" | grep -E "WAITING|BLOCKED|waiting on"

# Expected patterns:
# - Many threads waiting on same lock → contention
# - Many threads waiting on condition → queue or sleep
# - Many threads blocked on IO → dependency or DB slow
```

---

## Minute 5: Check database
```bash
# SSH into DB
ssh postgres-primary

# Find slow queries
psql -U postgres -c "
SELECT query, mean_time, calls 
FROM pg_stat_statements 
WHERE mean_time > 100 
ORDER BY mean_time DESC 
LIMIT 10;
"

# Find locks
psql -U postgres -c "
SELECT pid, usename, query, state, wait_event
FROM pg_stat_activity
WHERE state != 'idle' AND wait_event IS NOT NULL;
"

# Find blocking queries
psql -U postgres -c "
SELECT 
    blocked_locks.pid AS blocked_pid,
    blocked_activity.query AS blocked_query,
    blocking_locks.pid AS blocking_pid,
    blocking_activity.query AS blocking_query
FROM pg_catalog.pg_locks blocked_locks
 JOIN pg_catalog.pg_stat_activity blocked_activity ON blocked_activity.pid = blocked_locks.pid
 JOIN pg_catalog.pg_locks blocking_locks ON blocking_locks.locktype = blocked_locks.locktype
  AND blocking_locks.database IS NOT DISTINCT FROM blocked_locks.database
  AND blocking_locks.relation IS NOT DISTINCT FROM blocked_locks.relation
  AND blocking_locks.page IS NOT DISTINCT FROM blocked_locks.page
  AND blocking_locks.tuple IS NOT DISTINCT FROM blocked_locks.tuple
  AND blocking_locks.virtualxid IS NOT DISTINCT FROM blocked_locks.virtualxid
  AND blocking_locks.transactionid IS NOT DISTINCT FROM blocked_locks.transactionid
  AND blocking_locks.classid IS NOT DISTINCT FROM blocked_locks.classid
  AND blocking_locks.objid IS NOT DISTINCT FROM blocked_locks.objid
  AND blocking_locks.objsubid IS NOT DISTINCT FROM blocked_locks.objsubid
  AND blocking_locks.pid != blocked_locks.pid
 JOIN pg_catalog.pg_stat_activity blocking_activity ON blocking_activity.pid = blocking_locks.pid
WHERE NOT blocked_locks.granted;
"
```

Expected output:
- Slow query with high mean_time → needs index
- Lock wait detected → transaction is too long
- Blocking query identified → kill it or optimize

---

## Minute 6: Check GC
```bash
# Enable GC logging if not already enabled
jcmd 1234 JFR.start duration=30s filename=/tmp/recording.jfr

# Or check existing GC logs
tail -100 /var/log/app/gc.log | grep -E "GC|pause"

# Analysis: look for long pauses
grep "GC \|pause" /var/log/app/gc.log | tail -20
```

Expected output:
- If pauses are frequent and long: memory pressure
- If pauses correlate with latency spike: GC is the problem

---

## Minute 7: Check dependency latency
```bash
# Check if dependency calls are slow
curl http://localhost:8080/actuator/metrics | grep http.client

# Or check timeout/retry rate
grep -E "timeout|retry|circuit.breaker" logs/ | tail -20

# If available, check dependency dashboard
curl https://monitoring.example.com/dashboards/payment-service?minutes=5
```

Expected output:
- If dependency p95 is high: external service is slow
- If timeouts/retries are rising: circuit breaker activated

---

## Minute 8: Decide and act
Based on evidence, pick the narrowest fix:

### If threads are blocked:
```bash
# Check what they are waiting for
grep "waiting on" /tmp/thread_dump.txt | head -5

# If waiting on DB: optimize the slow query (add index)
# If waiting on lock: reduce lock scope (use ConcurrentHashMap instead of synchronized)
# If waiting on external service: add timeout or circuit breaker
```

### If DB is slow:
```bash
# Add missing index
psql -U postgres -d mydb -c "
CREATE INDEX CONCURRENTLY idx_orders_status_created
ON orders (status, created_at)
WHERE status = 'PENDING';
"

# Or kill long-running transaction
psql -U postgres -c "SELECT pg_terminate_backend(12345);"
```

### If GC is high:
```bash
# Tune JVM (be conservative)
# Increase heap: -Xmx8g
# Switch GC: -XX:+UseG1GC
# Tune pause time: -XX:MaxGCPauseMillis=200

# Then restart and monitor
systemctl restart app
tail -f /var/log/app/gc.log
```

### If dependency is slow:
```bash
# Add timeout
# Start circuit breaker
# Use fallback or do partial request

# Temporary: throttle requests to that endpoint
# Then fix it properly
```

---

## Monitoring during fix
```bash
# Watch p95 latency in real-time
watch -n 1 'curl -s http://localhost:8080/actuator/metrics/http.request.duration | grep p95'

# Watch thread pool
watch -n 1 'jcmd 1234 Thread.print | grep "tid=" | wc -l'

# Watch GC
watch -n 1 'tail -5 /var/log/app/gc.log'
```

---

## Rollback if needed
```bash
# If fix makes it worse, rollback immediately
kubectl rollout undo deployment/api-server

# Or revert config change
git revert <commit>
git push
```

---

## Post-incident tasks
```bash
# Collect all diagnostics
tar -czf incident-$(date +%s).tar.gz \
    /tmp/thread_dump.txt \
    /tmp/recording.jfr \
    /var/log/app/gc.log \
    /var/log/postgresql/postgresql.log

# Add alert so it does not happen again
# Add index or cache so query is faster

# Load test to confirm fix
k6 run --vus 200 --duration 5m load-test.js
```

---

## Quick reference: Common issues and immediate fixes
| Symptom | Diagnosis | Immediate Fix |
| --- | --- | --- |
| High latency, low CPU, high queue | Thread starvation | Reduce thread timeout, offload IO |
| High latency, high DB wait_event | DB lock contention | Kill long transaction, add index |
| p99 spikes every 30s | GC pause | Increase heap or change GC |
| Increasing timeouts on one endpoint | External service slow | Add circuit breaker, reduce retries |
| CPU 100%, many objects | Memory allocation spike | Reduce allocations, reuse buffers |

---

## Interview tip
"In production, I follow a diagnostic checklist: confirm the symptom, identify the slow endpoint, check thread pool and dumps, check DB locks and slow queries, check GC, then check dependencies. Each step takes 1–2 minutes. Once I have evidence, I apply the smallest safe fix and monitor the impact."

---

## Critical pitfalls and follow-up Q&A
**Pitfalls**:
- Restarting the app without understanding the problem
- Running heavy profilers without sampling bounds
- Not backing up diagnostics before making changes

**Follow-up Q&A**:
**Q**: What if the issue is intermittent and you cannot reproduce it?
**A**: Use continuous lightweight metrics and dashboarding; capture diagnostics during the next spike, not after.

**Q**: What if you cannot SSH into the server?
**A**: Use JMX remote or Spring Boot Actuator endpoints to access diagnostics remotely.

**Q**: What if restarting the app fixes it but then it comes back?
**A**: The fix is temporary (memory leak, connection pool exhaustion). Debug properly and add guardrails.
