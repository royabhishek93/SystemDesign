# Distributed Cache - Overview (Senior Level, Easy English)

Target level: Senior (5-7 years)

## 1) What is a Distributed Cache?
A distributed cache stores frequently used data in memory across multiple nodes. It reduces database load and improves latency.

## 2) Clarifying Questions (Interview Warm-up)
- What data is cached (hot reads, user profiles, sessions)?
- Read vs write ratio?
- Consistency needs (strong vs eventual)?
- Cache size and eviction policy?
- Multi-region or single region?

## 3) Approaches to Implement a Distributed Cache

### Approach A: Cache-Aside (Lazy Loading)
What it is:
- App checks cache first; on miss, reads DB and stores in cache.

Pros:
- Simple and common
- Works with most apps

Cons:
- Cold misses cause DB spikes
- Cache stampede risk

### Approach B: Read-Through Cache
What it is:
- Cache automatically loads from DB on miss.

Pros:
- Cleaner app code
- Centralized logic

Cons:
- Cache layer becomes more complex
- Harder to customize per request

### Approach C: Write-Through Cache
What it is:
- App writes to cache; cache writes to DB.

Pros:
- Cache and DB are consistent
- Fast reads

Cons:
- Higher write latency
- Cache is on the write path

### Approach D: Write-Back / Write-Behind Cache
What it is:
- App writes to cache; cache writes to DB asynchronously.

Pros:
- Very fast writes
- Good for high write throughput

Cons:
- Risk of data loss if cache fails
- Eventual consistency only

### Approach E: Near Cache (Client-Side Cache)
What it is:
- Cache in the application process, close to the client.

Pros:
- Lowest latency
- Reduces network calls

Cons:
- Hard to keep consistent
- Memory overhead per app instance

### Approach F: Multi-Level Cache (L1 + L2)
What it is:
- L1 in-memory in app, L2 distributed (Redis/Memcached).

Pros:
- Best latency with shared cache
- Reduced load on L2

Cons:
- More invalidation complexity

### Approach G: Partitioned / Sharded Cache
What it is:
- Cache data split across nodes with consistent hashing.

Pros:
- Scales horizontally
- No single hotspot

Cons:
- Rebalancing complexity
- Hot key issues still possible

### Approach H: Replicated Cache
What it is:
- Same data replicated across nodes for availability.

Pros:
- High availability
- Good read scalability

Cons:
- Higher memory cost
- Write amplification

## 4) Common Technologies
- Redis (most common)
- Memcached (simple, very fast)
- Hazelcast / Ignite (in-memory data grid)
- Ehcache (L1 or embedded)

## 5) Key Concepts (Interview Must-Know)
- TTL, eviction (LRU/LFU)
- Cache stampede protection (mutex, request coalescing)
- Cache penetration (negative caching)
- Cache consistency and invalidation strategies

## 6) Production Checklist
- Set clear TTLs and eviction policies
- Protect against hot keys
- Use circuit breakers to DB
- Monitor hit rate, latency, and evictions

## 7) Quick Interview Answer (30 seconds)
"A distributed cache keeps hot data in memory across nodes to reduce DB load and improve latency. The main approaches are cache-aside, read-through, write-through, write-back, and multi-level caches. Redis is the most common tech. Trade-offs depend on consistency needs, write volume, and failure tolerance."
