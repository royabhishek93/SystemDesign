# Interview Cheat Sheet

**Target level**: Senior (5-7 years), 2026

## 30-second answer
"I start by confirming impact and narrowing scope by endpoint and tenant. I check leading signals in threads, DB, GC, and downstream services to classify the bottleneck, then validate with thread dumps, slow query logs, and dependency metrics. I apply the smallest safe fix, like a query index or pool adjustment, and then add monitoring and load tests to prevent recurrence."

## 60-second answer
"First I confirm the symptom with p95/p99 latency and error rates, then isolate which endpoints and tenants are affected. I look for correlated signals: thread pool saturation, DB lock waits, GC pauses, or dependency latency. I validate with a thread dump and slow query logs, then apply the least risky fix (index, cache, timeout, bulkhead) and monitor the impact. Finally I add alerts and capacity tests so the issue does not reappear during the next peak."

## 2-minute answer (structured)
1. **Confirm and scope**: SLO breach, which endpoints, which tenants
2. **Classify bottleneck**: threads, DB, GC, dependency, cache
3. **Validate evidence**: thread dumps, slow query logs, p95 dashboards
4. **Fix safely**: minimal change first, feature flag if needed
5. **Prevent**: alerts, load tests, capacity plan

## Closing line (interview gold)
"Instead of scaling blindly, I identify whether the slowdown is from threads, database, or dependencies, then optimize the exact bottleneck and prevent recurrence with observability and capacity gates."

## Simple English
Say what is slow, prove it with data, fix only that part, then add alerts so it does not happen again.

## Real example
"We saw DB lock waits correlate with p95, added a missing index, and p95 dropped from 2.2 s to 240 ms."

## Why it happens
Tail latency grows when queues build up. One slow component can make every request wait.

## Wrong vs Right (code)
❌ **Wrong**: unlimited thread pool growth
```java
Executors.newCachedThreadPool();
```

✅ **Right**: bounded pool with queue
```java
new ThreadPoolExecutor(32, 32, 0L, TimeUnit.MILLISECONDS,
	new LinkedBlockingQueue<>(1000));
```

## Quick checklist
- p95/p99 and error rate
- Slow endpoint and tenant
- Threads, DB, GC, dependency signals
- Minimal fix and rollback plan
- Preventive alerts

## Critical pitfalls and follow-up Q&A
**Pitfalls**:
- Treating all latency as CPU-bound
- Ignoring dependency timeouts

**Follow-up Q&A**:
**Q**: What if CPU is low but latency is high?
**A**: That points to waiting (IO, locks, dependency), not compute. Check threads and DB locks.

**Q**: Why not just increase timeouts?
**A**: Longer timeouts increase tail latency and thread starvation; fix the cause instead.
