# Advanced Debugging Techniques (7+ years)

**Target level**: Staff+ (7+ years), 2026

## Introduction
For 7+ year engineers, debugging is not just guessing. It is a systematic approach using evidence-driven diagnostics, profiling, and production instrumentation.

## Simple English
When you have 7+ years of experience, you know that slowness always leaves traces. You know how to find them without crashing production.

## Why this matters
- Junior engineers guess and scale blindly.
- Mid-level engineers use basic tools (logs, metrics).
- Senior engineers (7+) know which data to extract and how to correlate across systems in real-time.

## 1) Thread dump analysis (deeper)
A thread dump shows exactly what each thread is doing right now.

**What to look for**:
```
"http-nio-8080-exec-5" #45 daemon prio=5 os_prio=0 tid=0x00007f8b2c0b4000 nid=0x5c4f waiting on condition [0x00007f8b1f3df000]
   java.lang.Thread.State: WAITING (parking)
        at sun.misc.Unsafe.park(Native Method)
        - parking to wait for <0x00000000c1f2b7c0> (a java.util.concurrent.locks.ReentrantLock$NonfairSync)
```

**What this tells you**:
- Thread is waiting on a lock (parking).
- The lock is held by another thread.
- This is blocking other requests.

**How to fix**:
- Check which thread holds the lock.
- Move the blocking operation off the request thread.

**Example fix**:
```java
// Wrong: blocking lock on request thread
synchronized(sharedResource) {
    slowIO();
}

// Right: use separate executor for blocking IO
CompletableFuture.supplyAsync(() -> slowIO(), ioExecutor)
    .thenApply(result -> result)
    .join();
```

---

## 2) Flame graphs (CPU profiling)
A flame graph shows where time is being spent in code.

**How to read**:
- X-axis = time spent
- Y-axis = call stack depth
- Wide bar = time was spent there

**Example flame graph**:
```
[java] [app] [handler] [query]
          [jdbc] [postgres] [execute]
[postgres] [lock wait] <-- wide bar = time spent waiting for lock
```

**What to do**:
- Look for the widest bars.
- Investigate why that code took so long.

**How to capture**:
```bash
# Using async-profiler (safe for production)
./profiler.sh -d 30 -f flamegraph.html jps

# Or use JFR (Java Flight Recorder)
jcmd <pid> JFR.start duration=30s filename=recording.jfr
```

---

## 3) GC analysis (memory under pressure)
Every GC pause is time the app cannot respond.

**Signals of GC pressure**:
- GC pause time rising
- Allocation rate surge
- p99 latency spikes correlate with GC pauses

**How to diagnose**:
```bash
# Enable GC logs
-Xlog:gc*:file=gc.log:time,level,tags

# Then analyze with GCeasy.io
# Upload gc.log and it shows:
# - Pause time trend
# - Allocation rate
# - Heap fragmentation
```

**Example fix** (if GC is the problem):
```java
// Wrong: create many objects
List<String> result = new ArrayList<>();
for (int i = 0; i < 1_000_000; i++) {
    result.add("value_" + i);  // allocates strings
}

// Right: reuse buffers
StringBuilder sb = new StringBuilder();
for (int i = 0; i < 1_000_000; i++) {
    sb.append("value_").append(i);
}
String result = sb.toString();  // single allocation
```

---

## 4) Lock contention detection
High lock contention blocks many threads.

**Signals**:
```
"http-nio-8080-exec-1" waiting to lock <0xc1f2b7c0>
"http-nio-8080-exec-2" waiting to lock <0xc1f2b7c0>
"http-nio-8080-exec-3" waiting to lock <0xc1f2b7c0>  <-- multiple threads on same lock
```

**Fix strategies**:
```java
// Wrong: single lock for many threads
synchronized(cache) {
    return cache.get(key);
}

// Right: use lock-free or segment locks
ConcurrentHashMap<String, String> cache = new ConcurrentHashMap<>();
return cache.get(key);  // no lock needed for reads

// Or: use striped locks
List<ConcurrentHashMap> shards = new ArrayList<>();
int shard = Math.abs(key.hashCode() % SHARD_COUNT);
return shards.get(shard).get(key);  // distribute lock pressure
```

---

## 5) Database lock analysis (production query)
This is where most latency hides.

**Check active locks (PostgreSQL)**:
```sql
SELECT pid, usename, query, state, wait_event
FROM pg_stat_activity
WHERE state != 'idle';
```

**Find blocking queries**:
```sql
SELECT 
    (SELECT pid FROM pg_stat_activity WHERE pid = blocking_pid) as blocked_by,
    (SELECT query FROM pg_stat_activity WHERE pid = blocking_pid) as blocking_query,
    pid as blocked_pid,
    query as blocked_query
FROM pg_catalog.pg_locks
WHERE NOT granted;
```

**Fix**:
- Kill long-running transaction: `SELECT pg_terminate_backend(pid);`
- Add index if lock is on a slow query
- Reduce transaction time

---

## 6) Dependency timeout tracing
When external services are slow, trace to confirm.

**Distributed trace with headers**:
```java
// In your client
String traceId = MDC.get("trace-id");

HttpHeaders headers = new HttpHeaders();
headers.set("X-Trace-ID", traceId);

RestTemplate template = new RestTemplate();
ResponseEntity<PaymentResponse> response = 
    template.exchange(
        url,
        HttpMethod.POST,
        new HttpEntity<>(request, headers),
        PaymentResponse.class
    );

// Payment service logs also use X-Trace-ID
// Now you can grep for that trace ID across all services
```

**Correlation in logs**:
```bash
# In ELK or Loki
{trace_id="abc-123"}

# Shows all operations for that request across all services
```

---

## 7) Live debugging without profilers
Sometimes you cannot use profilers. You use instrumentation.

**Add lightweight metrics**:
```java
@Component
public class PerformanceInterceptor extends HandlerInterceptorAdapter {
    @Override
    public boolean preHandle(HttpServletRequest req, 
                             HttpServletResponse res, 
                             Object handler) {
        req.setAttribute("startTime", System.nanoTime());
        return true;
    }

    @Override
    public void afterCompletion(HttpServletRequest req,
                                HttpServletResponse res,
                                Object handler,
                                Exception ex) {
        long duration = (System.nanoTime() - 
                        (long) req.getAttribute("startTime")) / 1_000_000;
        String endpoint = req.getRequestURI();
        
        // Don't log all; sample high latencies
        if (duration > 500) {  // 500 ms threshold
            logger.warn("SLOW: {} took {} ms", endpoint, duration);
        }
        
        meterRegistry.timer("http.latency", 
            "endpoint", endpoint).record(duration, TimeUnit.MILLISECONDS);
    }
}
```

**Benefits**:
- No profiler overhead
- Captures real production latency
- Can be tuned dynamically

---

## 8) Correlation without full tracing
Full tracing is expensive. Smart engineers use correlation tricks.

**Approach**:
```java
// In app logs, log timing and key info
logger.info("checkout_start order_id={} user_id={}", orderId, userId);
long dbStart = System.nanoTime();
Order order = db.getOrder(orderId);
long dbTime = (System.nanoTime() - dbStart) / 1_000_000;
logger.info("checkout_db order_id={} duration_ms={}", orderId, dbTime);

logger.info("checkout_payment order_id={} user_id={}", orderId, userId);
long payStart = System.nanoTime();
Payment payment = paymentClient.charge(amount);
long payTime = (System.nanoTime() - payStart) / 1_000_000;
logger.info("checkout_payment order_id={} duration_ms={} status={}", 
    orderId, payTime, payment.status());
```

**Grep for slow requests**:
```bash
# Find slow checkouts
grep "checkout_start order_id=123" logs | head -1
grep "checkout_start\|checkout_db\|checkout_payment" logs | grep "order_id=123"

# Shows: start -> db (50ms) -> payment (2000ms) <- payment is slow
```

---

## Wrong vs Right (debugging approach)
❌ **Wrong**: "It is slow, restart the app"
✅ **Correct**: "I will capture thread dumps, GC logs, and DB lock waits to find the exact bottleneck."

❌ **Wrong**: "Increase CPU and connections"
✅ **Correct**: "I will profile to confirm the bottleneck before scaling."

❌ **Wrong**: "Log everything"
✅ **Correct**: "I will sample high-latency requests and correlate with metrics."

---

## Interview tip
"As a 7+ year engineer, I do not guess. I capture evidence: thread dumps for blocking, flame graphs for CPU, GC logs for pauses, DB locks for contention, and distributed traces for dependencies. Then I fix the exact bottleneck."

---

## Quick checklist
- Thread dumps when latency is high
- Flame graphs for CPU-intensive workloads
- GC logs for pause time anomalies
- DB lock query for contention
- Distributed trace headers for dependency latency
- Lightweight metrics without profiler overhead

---

## Critical pitfalls and follow-up Q&A
**Pitfalls**:
- Running heavy profilers on production without sampling
- Enabling all logging without limits (log spam kills performance)
- Not understanding what thread dumps actually show

**Follow-up Q&A**:
**Q**: How do you profile production safely?
**A**: Use async-profiler with sampling, JFR with bounded duration, or lightweight instrumentation. Never enable CPU profiling 100% of the time.

**Q**: What if you cannot get thread dumps during the incident?
**A**: Replay the workload in staging with the same config, capture dumps, and apply fixes. Or use continuous lightweight metrics to correlate after the fact.

**Q**: How do you correlate logs across microservices without a tracing platform?
**A**: Pass trace IDs in request headers, log them strategically in each service, and grep across logs using a common trace ID pattern.
