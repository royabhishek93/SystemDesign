# Fix and Prevent (Production-Grade)

**Target level**: Senior (5-7 years), 2026

## Short-term fixes (hours)
- **Rollback or feature flag** if regression suspected
- **Tune timeouts and pools** based on observed bottlenecks
- **Throttle or shed load** for non-critical endpoints

## Medium-term fixes (days)
- **Query optimization** and index strategy
- **Asynchronous pipelines** for slow IO
- **Cache read-through** for hot paths

## Long-term prevention (weeks)
- **SLO-based alerting** with error budget
- **Load test gates** before peak events
- **Capacity planning** tied to growth
- **Chaos testing** for dependency latency

## Production story (STAR format)
- **Situation**: 6-node Spring Boot cluster, p95 latency jumped from 180 ms to 2.2 s during a seasonal sale.
- **Task**: Restore p95 under 300 ms without risky code deploys.
- **Action**: Correlated p95 with DB lock waits; identified missing composite index on a hot filter; added index concurrently and reduced retries; added dashboard alert on lock waits.
- **Result**: p95 returned to 240 ms within 45 minutes; incident rate dropped by 80% in next peak.

## Preventive checklist
- **Dashboards**: p50/p95/p99 latency, error rate, saturation
- **Alerts**: lock waits, thread pool queue size, downstream p95
- **Runbook**: top 5 query plans and thread dump patterns

## Simple English
Fix the smallest thing that removes the bottleneck, then add alerts so it does not return.

## Real example
If DB lock waits are high, add a missing index or reduce contention before adding more app servers.

## Why it happens
Teams often jump to scaling. But if the real bottleneck is a slow query or a blocked dependency, scaling only increases cost and does not fix latency.

## Wrong vs Right (code)
❌ **Wrong**: unbounded retries on a slow dependency
```java
public Response call() {
	return retryTemplate.execute(ctx -> client.call());
}
```

✅ **Right**: retry with cap and circuit breaker
```java
@CircuitBreaker(name = "orders")
public Response call() {
	return retryTemplate.execute(ctx -> client.call());
}
```

## Interview tip
Say you prefer reversible changes first (timeouts, pool tuning, feature flags) before code rewrites.

## Quick checklist
- Apply smallest safe change first
- Measure impact on p95/p99
- Add alerts for leading indicators
- Update runbook with the fix

## Critical pitfalls and follow-up Q&A
**Pitfalls**:
- Adding capacity without fixing the bottleneck
- Increasing timeouts and masking the problem

**Follow-up Q&A**:
**Q**: How do you decide between caching and indexing?
**A**: Indexing reduces DB latency for common filters; caching helps repeated reads. Use evidence from query patterns.

**Q**: What if the fix is risky in production?
**A**: Use feature flags, canary releases, or traffic shifting to reduce blast radius.
