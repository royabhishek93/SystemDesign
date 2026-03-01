# Complex Incident Case Studies (7+ years)

**Target level**: Staff+ (7+ years), 2026

## Introduction
Real (anonymized) incidents that 7+ year engineers have solved using the techniques in this guide.

## Simple English
These are stories of how production issues were diagnosed and fixed by experienced teams.

---

## Case Study 1: Hidden N+1 query under load

**The incident**:
- Black Friday, 10x normal traffic
- p95 latency jumped from 150 ms to 3+ seconds
- DB CPU hit 95%

**Initial guess** (junior engineer):
- Scale up the database
- Add read replicas

**What really happened** (diagnosed in 15 minutes):
```bash
# Thread dump showed many threads waiting on DB:
jcmd <pid> Thread.print | grep "WAITING.*jdbc"

# DB slow queries revealed:
psql -c "
SELECT query, mean_time, calls
FROM pg_stat_statements
WHERE query LIKE '%SELECT%orders%'
ORDER BY mean_time DESC LIMIT 5;
"

# Output:
# Query: SELECT * FROM orders WHERE user_id = $1
# Mean time: 2300 ms
# Calls: 45000 (in 5 minutes!)
```

**Root cause**:
```java
// Wrong: N+1 query pattern
@GetMapping("/users/{id}")
public UserResponse getUser(@PathVariable Long id) {
    User user = userRepo.findById(id);  // 1 query
    
    user.orders = orderRepo.findByUserId(id);  // N queries, one per request
    user.orders.forEach(order -> {
        order.items = itemRepo.findByOrderId(order.id);  // N*M queries!
    });
    
    return toResponse(user);
}
```

Under normal traffic: 100 users/sec → 100 queries/sec (acceptable)
Under Black Friday: 1000 users/sec → 45,000 queries/sec (DB melts)

**Fix**:
```java
// Right: single query with joins
@GetMapping("/users/{id}")
public UserResponse getUser(@PathVariable Long id) {
    User user = userRepo.findByIdWithOrdersAndItems(id);  // 1 query with JOINs
    return toResponse(user);
}

// Repository with named query
@Query("""
    SELECT u FROM User u
    LEFT JOIN FETCH u.orders o
    LEFT JOIN FETCH o.items
    WHERE u.id = :id
""")
Optional<User> findByIdWithOrdersAndItems(@Param("id") Long id);
```

**Result**:
- Queries dropped from 45,000 to 500/min
- p95 latency fell from 3s to 180 ms
- DB CPU dropped to 30%

**Lesson**: N+1 patterns hide until you have real load.

---

## Case Study 2: Thread pool exhaustion + upstream dependent timeout

**The incident**:
- Analytics service crashed
- Checkout service p95 went from 400 ms to 4+ seconds
- Error rate spiked to 20%

**Initial guess** (mid-level engineer):
- Analytics service is down, increase pool size

**What really happened**:
```bash
# Thread dump showed:
jcmd <pid> Thread.print | grep "waiting to acquire lock"  # None
jcmd <pid> Thread.print | grep "waiting on condition"  # Many

# Actuator showed:
curl http://localhost:8080/actuator/metrics/jvm.threads.live | grep value
# value: 250 (max is 200, some requests queued)
```

**Root cause** (visualization):
```
Checkout service (good)
    ↓ calls Analytics service (TIMEOUT: 5s)
        Analytics service (down)
        
Checkout thread: "I will wait for Analytics"
Thread pool: 200 threads all waiting
New request comes: NO THREADS AVAILABLE → QUEUE

Queue grows → older requests timeout → retry → more queue
```

**The timeline**:
1. Analytics service crashes
2. Checkout retries with no backoff (3 retries, 5s each = 15s)
3. Thread pool full after 2 minutes
4. New requests queue
5. Load balancer health check times out
6. Instance marked as degraded
7. Other instances also have full pools
8. Cascade failure

**Fix** (tiered):
```java
// 1. Add timeout to Analytics call
HttpComponentsClientHttpRequestFactory factory = 
    new HttpComponentsClientHttpRequestFactory();
factory.setConnectTimeout(1000);  // was infinite
factory.setReadTimeout(2000);     // was infinite
restTemplate = new RestTemplate(factory);

// 2. Add circuit breaker
@CircuitBreaker(name = "analytics", fallbackMethod = "analyticsDisabledFallback")
public AnalyticsResponse callAnalytics(Request req) {
    return client.getAnalytics(req);
}

private AnalyticsResponse analyticsDisabledFallback(Request req, Exception e) {
    // Return empty analytics, do not fail checkout
    return AnalyticsResponse.empty();
}

// 3. Limit retries
RetryTemplate template = RetryTemplate.builder()
    .maxAttempts(2)  // was unbounded
    .fixedBackoff(100)  // was immediate
    .build();
```

**Result**:
- Checkout continues even if Analytics is down
- p95 latency drops to 450 ms (degraded but functional)
- Error rate 0% (users do not see errors)

**Lesson**: Timeout and circuit breaker are not optional; they are mandatory.

---

## Case Study 3: Memory leak under sustained load

**The incident**:
- App runs fine for 1 hour
- After 2–3 hours, p99 latency spikes
- After 4 hours, OutOfMemory error, crash

**Initial guess**:
- Increase heap size
- Restart app daily

**What really happened**:
```bash
# GC logs showed:
# 0h: GC pause 50 ms
# 1h: GC pause 100 ms
# 2h: GC pause 300 ms
# 3h: pause 800 ms, then crash

# Heap dump analysis showed:
jcmd <pid> GC.heap_dump /tmp/heap.hprof

# Analysis (using MAT or JProfiler):
# 5 GB of Order objects locked in HashMap
# Never removed, never garbage collected
```

**Root cause**:
```java
// Wrong: unbounded cache
public class OrderService {
    private static final HashMap<Long, Order> CACHE = new HashMap<>();  // NEVER CLEARED!
    
    public Order getOrder(Long id) {
        if (!CACHE.containsKey(id)) {
            CACHE.put(id, fetchFromDB(id));
        }
        return CACHE.get(id);
    }
}
```

Under load: 1000 requests/sec → 1000 new orders/sec → cache grows 86 GB/day

**Fix**:
```java
// Option 1: Use Spring Cache with TTL
@Cacheable(value = "orders", key = "#id", unless = "#result == null")
public Order getOrder(Long id) {
    return fetchFromDB(id);
}

// application.properties
spring.cache.type=caffeine
spring.cache.caffeine.spec=expireAfterWrite=5m,maximumSize=10000

// Option 2: Use Redis (external)
@Cacheable(value = "orders", key = "#id", cacheManager = "redisCacheManager")
public Order getOrder(Long id) {
    return fetchFromDB(id);
}
```

**Result**:
- Memory stays stable
- GC pauses stay at 50 ms
- No crashes

**Lesson**: Never use unbounded collections. Always set TTL or max size.

---

## Case Study 4: Lock contention on shared resource

**The incident**:
- Payment processing p95 is 5+ seconds
- Error rate 3% (timeouts)
- CPU is low (50%)

**Initial guess**:
- Database is slow

**What really happened**:
```bash
# Thread dump showed:
# 150 threads all waiting on same lock
jcmd <pid> Thread.print | grep "waiting to lock <0xc1f2b7c0>"

# That object is:
{
    "id": "0xc1f2b7c0",
    "type": "java.util.HashMap",
    "source": "PaymentService.EXCHANGE_RATES"
}

# Code:
private static HashMap<String, BigDecimal> EXCHANGE_RATES = ...;

public BigDecimal convert(BigDecimal amount, String from, String to) {
    synchronized(EXCHANGE_RATES) {  // LOCK!
        return amount * EXCHANGE_RATES.get(from) / EXCHANGE_RATES.get(to);
    }
}
```

Every payment request locks the same object → all threads wait.

**Fix**:
```java
// Option 1: Use ConcurrentHashMap (no lock for reads)
private static ConcurrentHashMap<String, BigDecimal> exchangeRates = ...;

public BigDecimal convert(BigDecimal amount, String from, String to) {
    // No lock needed for reads
    return amount * exchangeRates.get(from) / exchangeRates.get(to);
}

// Option 2: Segment the lock (striped locking)
private static final Object[] LOCKS = new Object[16];

public BigDecimal convert(BigDecimal amount, String from, String to) {
    int hashCode = Math.abs(from.hashCode() % 16);
    synchronized(LOCKS[hashCode]) {
        return amount * exchangeRates.get(from) / exchangeRates.get(to);
    }
}

// Option 3: Use read-write lock
private static final ReadWriteLock lock = new ReentrantReadWriteLock();

public BigDecimal convert(BigDecimal amount, String from, String to) {
    lock.readLock().lock();
    try {
        return amount * exchangeRates.get(from) / exchangeRates.get(to);
    } finally {
        lock.readLock().unlock();
    }
}
```

**Result**:
- p95 dropped from 5s to 200 ms
- CPU rose slightly (now actually doing work)
- Throughput 50x higher

**Lesson**: Use ConcurrentHashMap for concurrent reads. Reduce lock scope.

---

## Case Study 5: Cascading timeout and retry storm

**The incident**:
- One region had network blip (5 seconds of 500 ms latency)
- Then entire platform went down for 30 minutes

**Root cause** (domino effect):
```
Network blip (5s)
    ↓
Service A timeout on Service B (5s retry loop × 3 = 15s)
    ↓
Service A exhausts thread pool (100 threads × 15s each = 1500 threads needed)
    ↓
Service A crashes / slow
    ↓
Service C (depends on Service A) times out
    ↓
Service C also exhausts threads
    ↓
Service D (depends on C) times out
    ↓
Cascade: D → E → F → all down
```

**Fix** (resilience at each level):
```java
// Service A calling Service B:
@CircuitBreaker(name = "serviceB", fallbackMethod = "fallback")
@Retry(name = "serviceB")
@Bulkhead(name = "serviceB")
@Timeout(name = "serviceB")
public Response callServiceB(Request req) {
    return clientB.call(req);
}

public Response fallback(Request req, Exception e) {
    return Response.cached();  // Return cached result instead of failing
}

// resilience4j configuration:
resilience4j:
  circuitbreaker:
    configs:
      default:
        failure-rate-threshold: 50
        wait-duration-in-open-state: 10s
  retry:
    configs:
      default:
        max-attempts: 2
        wait-duration: 100
  bulkhead:
    configs:
      default:
        max-concurrent-calls: 10
  timeout:
    configs:
      default:
        timeout-duration: 2s
```

**Result**:
- Service A degrades gracefully (returns cache)
- Service C degrades separately (does not wait for A)
- Platform stays up with reduced functionality
- 5-minute recovery instead of 30 minutes

**Lesson**: Timeouts, circuit breakers, bulkheads, and fallbacks are mandatory at every boundary.

---

## Interview tip
"Complex incidents are caused by cascading failures and hidden bottlenecks. I diagnose by correlating metrics, thread dumps, and query logs. I fix by adding timeout/circuit breaker boundaries, optimizing the exact bottleneck, and preventing retry amplification. The key is discipline: assume production will fail in unexpected ways and build resilience systematically."

---

## Critical pitfalls and follow-up Q&A
**Pitfalls**:
- Focusing on one metric (like CPU) and missing the real bottleneck
- Increasing pools and caches to mask problems
- Not implementing circuit breakers and timeouts

**Follow-up Q&A**:
**Q**: How do you distinguish between a bug and an architectural problem?
**A**: Bug = happens once, reproducible; Architectural = happens under load, cascades. Architecture requires resilience patterns. Bugs require code fixes.

**Q**: Should you always have circuit breakers?
**A**: Yes. Every external dependency call needs timeout + circuit breaker. It is not optional.

**Q**: How do you test for cascade failures?
**A**: Chaos testing: simulate latency/failure of one service, measure blast radius on others. Use gremlin or similar tools.
