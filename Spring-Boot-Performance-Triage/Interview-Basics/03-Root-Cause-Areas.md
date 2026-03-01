# Root Cause Areas and Signals

**Target level**: Senior (5-7 years), 2026

## Simple English
There are only a few places where slowness starts: threads, database, garbage collection, dependencies, cache, or network. Find which one is blocking requests.

## Why it happens
Under load, a slow component makes every request wait. Even small delays can create a large queue and explode tail latency.

## 1) Thread starvation (Tomcat / servlet)
**Signals**:
- High request queue, active threads at max
- Thread dumps show many threads waiting on the same lock

**Actions**:
- Reduce blocking, move IO to async or separate pool
- Tune `server.tomcat.max-threads` and `accept-count`

```java
// Example: isolate blocking IO to a dedicated executor
@Bean
public Executor ioExecutor() {
    return Executors.newFixedThreadPool(64);
}
```

## 2) Database bottleneck
**Signals**:
- DB latency and lock waits increase
- Connection pool near exhaustion (Hikari)

**Actions**:
- Add missing indexes, reduce scans, fix N+1
- Increase pool only if DB has headroom

```sql
-- Example: add an index for a hot filter
CREATE INDEX CONCURRENTLY idx_orders_status_created
ON orders (status, created_at);

-- Inspect query plan
EXPLAIN (ANALYZE, BUFFERS) SELECT * FROM orders WHERE status = 'PENDING';
```

## 3) Garbage collection pressure
**Signals**:
- Long GC pauses, high allocation rate
- Latency spikes correlate with GC

**Actions**:
- Reduce allocations, reuse buffers, tune JVM

```bash
# Example: JVM flags for G1 tuning (adjust with evidence)
-XX:+UseG1GC -XX:MaxGCPauseMillis=200 -Xms4g -Xmx4g
```

## 4) Downstream dependency latency
**Signals**:
- Request latency tracks external API p95
- Increased retry rate and timeout errors

**Actions**:
- Add circuit breaker and bulkhead
- Cache read-heavy responses

```java
// Example: Resilience4j circuit breaker
@CircuitBreaker(name = "payments", fallbackMethod = "fallback")
public PaymentResponse pay(PaymentRequest request) { ... }
```

## 5) Cache inefficiency or stampede
**Signals**:
- Cache hit rate drops during peak
- DB traffic spikes on cache misses

**Actions**:
- Add request coalescing, jittered TTL
- Improve cache key design

## 6) Network and LB constraints
**Signals**:
- SYN backlog, connection reuse issues
- LB health checks slow, uneven traffic

**Actions**:
- Tune keep-alive, LB timeouts
- Enable connection pooling

## 7) Configuration regressions
**Signals**:
- Performance drop after deploy
- Config change on pool sizes, timeouts

**Actions**:
- Roll back to known baseline
- Add config validation and diff alerts

## Diagnostic table (quick reference)
| Area | Leading Signal | Confirming Evidence | First Fix |
| --- | --- | --- | --- |
| Threads | Queue size spikes | Thread dump shows blocked state | Offload blocking IO |
| DB | Slow query logs | High lock wait time | Index or query rewrite |
| GC | Pause time spikes | Allocation rate surge | Reduce allocations |
| Dependency | Timeout retries | External p95 aligned | Circuit breaker |
| Cache | Hit rate drops | DB reads spike | Cache warming |

## Wrong vs Right (code)
❌ **Wrong**: blocking call on request thread
```java
@GetMapping("/report")
public Report report() {
    return externalClient.fetchReport();
}
```

✅ **Right**: isolate blocking call to a dedicated executor
```java
@GetMapping("/report")
public Report report() {
    return CompletableFuture
        .supplyAsync(externalClient::fetchReport, ioExecutor)
        .join();
}
```

## Interview tip
Say you map symptoms to root-cause domains before proposing fixes.

## Quick checklist
- Thread pool saturation and dumps
- DB slow queries and lock waits
- GC pause time and allocation rate
- Dependency p95 and timeout rate
- Cache hit rate and stampede risk

## Critical pitfalls and follow-up Q&A
**Pitfalls**:
- Increasing pools without fixing the slow operation
- Ignoring lock waits and focusing only on query time

**Follow-up Q&A**:
**Q**: How do you know it is thread starvation vs DB slowness?
**A**: Thread starvation shows queued requests and blocked threads; DB slowness shows high query time or lock waits that correlate with p95.

**Q**: When does reactive actually help?
**A**: When IO wait dominates and you can reduce blocking; otherwise it is a risky rewrite with little gain.
