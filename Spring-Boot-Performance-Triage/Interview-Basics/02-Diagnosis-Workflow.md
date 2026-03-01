# Diagnosis Workflow (Production-First)

**Target level**: Senior (5-7 years), 2026

## Step 0: Confirm the symptom
- Confirm **user-facing** latency and error rates
- Identify **which endpoints** and **which tenants** are affected

## Step 1: Classify the bottleneck domain
Use the fastest available signals:
- **CPU saturated**: high CPU, low IO wait, request time rises across endpoints
- **Thread starvation**: high request queue, low CPU, blocked threads
- **GC pressure**: rising GC time, long pauses, allocation spikes
- **DB bottleneck**: slow queries, lock waits, connection pool exhaustion
- **Downstream dependency**: latency spikes align with external service

## Step 2: Validate with evidence
- Check metrics for **correlated spikes**: latency, queue depth, thread usage
- Pull **thread dumps** when latency is high
- Check **DB slow query logs** and active locks
- Review **dependency dashboards** for elevated latency

## Step 3: Reproduce safely (if possible)
- Use a **staging-like environment** and replay production traffic
- Establish the **failure threshold** (e.g., 800 RPS)

```bash
# Example: basic load test with k6
k6 run --vus 200 --duration 5m smoke.js
```

## Step 4: Apply minimal safe fix
- Prefer **configuration-level** changes first (timeouts, pool size)
- Use **feature flags** or **traffic shifting** for risky changes

## Step 5: Prevent regression
- Add **alerts** for leading indicators
- Codify **capacity tests** in CI or pre-prod

## Evidence checklist
- **Latency percentiles** (p50/p95/p99)
- **Thread pool**: active, queued, rejected
- **GC**: pause time and frequency
- **DB**: slow queries, lock waits, pool usage
- **Downstream**: timeouts, retries, error rate

## Simple English
Find what is slow first, then prove it with data, then fix it in the smallest safe way.

## Real example
You see a latency spike and thread pool queue growth. A thread dump shows many threads waiting on the same DB call. You check DB slow queries, add an index, and the queue drops.

## Why it happens
When one part is slow, requests pile up. The queue hides the real cause unless you trace it to threads, DB, GC, or dependency latency.

## Wrong vs Right (code)
❌ **Wrong**: aggressive retries without limits
```java
retryTemplate.execute(ctx -> callDownstream());
```

✅ **Right**: bounded retries with backoff
```java
RetryTemplate template = RetryTemplate.builder()
	.maxAttempts(3)
	.fixedBackoff(200)
	.build();
template.execute(ctx -> callDownstream());
```

## Interview tip
Mention that you always correlate latency with saturation signals (threads, DB locks, GC) before changing configs.

## Quick checklist
- Confirm p95/p99 and error rate
- Identify slow endpoint and tenant
- Check thread dumps and pool usage
- Check DB slow queries and lock waits
- Check dependency p95 and timeouts

## Critical pitfalls and follow-up Q&A
**Pitfalls**:
- Tuning thread pools without evidence
- Running heavy profilers directly in production

**Follow-up Q&A**:
**Q**: What if you cannot reproduce the issue in staging?
**A**: Use production metrics, safe traffic sampling, and lightweight diagnostics to confirm the cause.

**Q**: What if all signals look normal but latency is high?
**A**: Check network, load balancer limits, and request payload sizes for hidden bottlenecks.
