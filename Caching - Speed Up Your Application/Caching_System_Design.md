# Caching - Speed Up Your Application 100x

## 1. What is Caching?

**Caching** is storing frequently accessed data in fast storage (memory) to avoid slow operations like database queries, API calls, or computations.

### Why Caching is Needed:

- ✅ Faster response times (milliseconds vs seconds)
- ✅ Reduced database load
- ✅ Lower costs (fewer database queries)
- ✅ Better scalability
- ✅ Improved user experience
- ✅ Handle traffic spikes

### Visual: With vs Without Cache

```
┌────────────────────────────────────────────────────────────────────────┐
│                  WITHOUT CACHING (SLOW)                                │
└────────────────────────────────────────────────────────────────────────┘

Every request hits the database:

User Request: "Get product details for ID 12345"
     │
     ↓
┌──────────────────┐
│  Web Server      │
│                  │
│  1. Receive req  │
│  2. Query DB     │  ← Every time!
└────────┬─────────┘
         │
         │ SELECT * FROM products WHERE id = 12345
         ↓
┌──────────────────┐
│  Database        │
│                  │
│  • Search index  │
│  • Read disk     │
│  • Return data   │
│                  │
│  Time: 500ms ❌  │
└────────┬─────────┘
         │
         ↓
    Response to user (SLOW)

Problems:
❌ High database load
❌ Slow response (500ms per request)
❌ Database becomes bottleneck
❌ Expensive (more DB resources needed)
❌ Poor scalability

If 10,000 users request same product:
→ 10,000 identical database queries! 🤯
→ Total time wasted: 5,000 seconds!


WITH CACHING (FAST)
───────────────────

First request (Cache MISS):

User Request: "Get product details for ID 12345"
     │
     ↓
┌──────────────────┐
│  Web Server      │
│                  │
│  1. Check cache  │
│  2. MISS ❌      │
│  3. Query DB     │
└────────┬─────────┘
         │
         ↓
┌──────────────────┐
│  Database        │
│  Time: 500ms     │
└────────┬─────────┘
         │
         ↓
┌──────────────────┐
│  Store in cache  │
│  Key: prod:12345 │
│  Value: {...}    │
└──────────────────┘
         │
         ↓
    Response (500ms first time)


Subsequent requests (Cache HIT):

User Request: "Get product details for ID 12345"
     │
     ↓
┌──────────────────┐
│  Web Server      │
│                  │
│  1. Check cache  │
│  2. HIT! ✅      │
│  3. Return data  │
│     (Skip DB!)   │
└────────┬─────────┘
         │
         │ Get from Redis (in-memory)
         ↓
┌──────────────────┐
│  CACHE (Redis)   │
│                  │
│  Key: prod:12345 │
│  Value: {...}    │
│                  │
│  Time: 5ms ✅    │
└────────┬─────────┘
         │
         ↓
    Response (5ms - 100x faster!)

Benefits:
✅ 100x faster (5ms vs 500ms)
✅ Database not hit
✅ Can handle high traffic
✅ Better user experience
✅ Lower costs

If 10,000 users request same product:
→ 1 database query + 9,999 cache hits!
→ Total time saved: 4,955 seconds! 🎉
```

## 2. Cache Hierarchy (Multiple Layers)

### Visual: Multi-Layer Caching

```
┌────────────────────────────────────────────────────────────────────────┐
│                    CACHE HIERARCHY (FASTEST TO SLOWEST)                │
└────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│  LAYER 1: BROWSER/CLIENT CACHE                              │
│  Location: User's device                                    │
│  Speed: Instant (no network)                                │
│  Size: 50-200 MB                                            │
│  TTL: Hours to days                                         │
│                                                             │
│  Examples:                                                  │
│  • HTML pages                                               │
│  • CSS/JS files                                             │
│  • Images                                                   │
│  • API responses (with Cache-Control headers)               │
│                                                             │
│  User requests page → Check browser cache → Instant load ✅ │
└─────────────────────────────────────────────────────────────┘
                            ↓ (if miss)
┌─────────────────────────────────────────────────────────────┐
│  LAYER 2: CDN CACHE                                         │
│  Location: Edge servers (geographically distributed)        │
│  Speed: ~20-50ms                                            │
│  Size: TBs (per region)                                     │
│  TTL: Hours to days                                         │
│                                                             │
│  Examples:                                                  │
│  • Static assets (images, videos, CSS, JS)                  │
│  • HTML pages                                               │
│  • API responses (if cacheable)                             │
│                                                             │
│  Request → CDN edge server (nearby) → Fast delivery ✅      │
└─────────────────────────────────────────────────────────────┘
                            ↓ (if miss)
┌─────────────────────────────────────────────────────────────┐
│  LAYER 3: APPLICATION CACHE (In-Memory)                     │
│  Location: Application servers                              │
│  Speed: < 1ms                                               │
│  Size: MBs to few GBs per server                            │
│  TTL: Seconds to minutes                                    │
│                                                             │
│  Examples:                                                  │
│  • Frequently accessed objects                              │
│  • Session data                                             │
│  • Computed results                                         │
│                                                             │
│  Technologies: Java HashMap, Python Dict, Node.js Map       │
└─────────────────────────────────────────────────────────────┘
                            ↓ (if miss)
┌─────────────────────────────────────────────────────────────┐
│  LAYER 4: DISTRIBUTED CACHE (Redis/Memcached)               │
│  Location: Separate cache cluster                           │
│  Speed: 1-5ms                                               │
│  Size: GBs to TBs                                           │
│  TTL: Minutes to hours                                      │
│                                                             │
│  Examples:                                                  │
│  • Session data (shared across servers)                     │
│  • User profiles                                            │
│  • Product catalog                                          │
│  • API responses                                            │
│  • Computed results                                         │
│                                                             │
│  Technologies: Redis, Memcached                             │
└─────────────────────────────────────────────────────────────┘
                            ↓ (if miss)
┌─────────────────────────────────────────────────────────────┐
│  LAYER 5: DATABASE QUERY CACHE                              │
│  Location: Database server memory                           │
│  Speed: 10-50ms                                             │
│  Size: GBs                                                  │
│  TTL: Automatic (invalidated on writes)                     │
│                                                             │
│  Examples:                                                  │
│  • Query results                                            │
│  • Frequently accessed rows                                 │
│                                                             │
│  Technologies: MySQL Query Cache, PostgreSQL Shared Buffers │
└─────────────────────────────────────────────────────────────┘
                            ↓ (if miss)
┌─────────────────────────────────────────────────────────────┐
│  LAYER 6: DATABASE (DISK)                                   │
│  Location: Database server disk                             │
│  Speed: 50-500ms                                            │
│  Size: TBs                                                  │
│  Persistent: Yes                                            │
│                                                             │
│  Last resort - slowest but most reliable                    │
└─────────────────────────────────────────────────────────────┘


SPEED COMPARISON
────────────────

Browser Cache:     ▓ 0ms (instant)
CDN:               ▓▓ 20-50ms
App Memory:        ▓ <1ms
Redis:             ▓▓ 1-5ms
DB Query Cache:    ▓▓▓▓ 10-50ms
Database Disk:     ▓▓▓▓▓▓▓▓▓▓ 50-500ms

Goal: Serve from highest cache layer possible!
```

## 3. Cache Strategies (Read)

### Strategy 1: Cache-Aside (Lazy Loading)

```
┌────────────────────────────────────────────────────────────────────────┐
│                    CACHE-ASIDE PATTERN                                 │
└────────────────────────────────────────────────────────────────────────┘

CONCEPT
───────
Application is responsible for:
1. Check cache first
2. If miss, fetch from database
3. Store in cache for next time

Most common pattern!

FLOW DIAGRAM
────────────

Read Request:
     │
     ↓
┌─────────────────────────────────┐
│  1. Check Cache                 │
│     GET user:123                │
└────┬────────────────────────┬───┘
     │                        │
     │ Cache HIT              │ Cache MISS
     ↓                        ↓
┌─────────────────┐   ┌─────────────────────────┐
│  2a. Return     │   │  2b. Query Database     │
│      from cache │   │      SELECT * FROM      │
│                 │   │      users              │
│  Time: 5ms ✅   │   │      WHERE id = 123     │
│                 │   │                         │
│                 │   │  Time: 500ms            │
│                 │   └───────┬─────────────────┘
│                 │           │
│                 │           ↓
│                 │   ┌─────────────────────────┐
│                 │   │  3. Store in Cache      │
│                 │   │     SET user:123 = {...}│
│                 │   │     EXPIRE 3600         │
│                 │   └───────┬─────────────────┘
│                 │           │
│                 │           ↓
│                 │   ┌─────────────────────────┐
│                 │   │  4. Return to client    │
│                 │   └─────────────────────────┘
└─────────────────┘


CODE EXAMPLE (Pseudocode)
──────────────────────────

function getUser(userId) {
    // 1. Try cache first
    cacheKey = "user:" + userId
    userData = cache.get(cacheKey)

    // 2. Cache hit? Return immediately
    if (userData != null) {
        return userData  // Fast! ✅
    }

    // 3. Cache miss - query database
    userData = database.query(
        "SELECT * FROM users WHERE id = ?",
        userId
    )

    // 4. Store in cache (with TTL)
    cache.set(cacheKey, userData, ttl=3600)  // 1 hour

    // 5. Return data
    return userData
}


PROS & CONS
───────────

✅ PROS:
• Only cache what's needed (lazy)
• Cache miss doesn't fail (just slower)
• Good for read-heavy workloads
• Application has full control
• Most common pattern

❌ CONS:
• Cache miss penalty (initial requests slow)
• Three round trips on cache miss:
  1. Check cache
  2. Query database
  3. Update cache
• Stale data possible (needs TTL)
• Application code more complex


WRITE FLOW (Cache Invalidation)
────────────────────────────────

When data is updated:

User updates profile:
     │
     ↓
┌─────────────────────────────────┐
│  1. Update Database             │
│     UPDATE users                │
│     SET name = 'John'           │
│     WHERE id = 123              │
└────┬────────────────────────────┘
     │
     ↓
┌─────────────────────────────────┐
│  2. Invalidate Cache            │
│     DELETE user:123             │
│     (Remove stale data)         │
└─────────────────────────────────┘
     │
     ↓
Next read will fetch fresh data from DB
and populate cache again
```

### Strategy 2: Read-Through Cache

```
┌────────────────────────────────────────────────────────────────────────┐
│                    READ-THROUGH PATTERN                                │
└────────────────────────────────────────────────────────────────────────┘

CONCEPT
───────
Cache sits between application and database.
Cache is responsible for loading data.

FLOW DIAGRAM
────────────

Application                Cache Library          Database
     │                          │                     │
     │ Get user:123             │                     │
     │─────────────────────────→│                     │
     │                          │                     │
     │                     Check cache                │
     │                          │                     │
     │                      Cache MISS                │
     │                          │                     │
     │                          │  Fetch from DB      │
     │                          │────────────────────→│
     │                          │                     │
     │                          │   User data         │
     │                          │←────────────────────│
     │                          │                     │
     │                     Store in cache             │
     │                          │                     │
     │   User data              │                     │
     │←─────────────────────────│                     │
     │                          │                     │

Application doesn't know about database!
Cache handles everything.


COMPARISON WITH CACHE-ASIDE
────────────────────────────

Cache-Aside:
┌──────────────┐
│ Application  │
│ (Complex)    │
│              │
│ • Check cache│
│ • Query DB   │
│ • Update     │
│   cache      │
└──────────────┘

Read-Through:
┌──────────────┐
│ Application  │
│ (Simple)     │
│              │
│ • Just call  │
│   cache.get()│
│              │
└──────────────┘
       │
       ↓
┌──────────────┐
│ Cache        │
│ (Smart)      │
│              │
│ • Handles    │
│   everything │
└──────────────┘


CODE EXAMPLE
────────────

// Application code (simpler!)
function getUser(userId) {
    return cache.get("user:" + userId)
    // Cache handles DB fetch if needed
}

// Cache configuration
cache.configure({
    loader: function(key) {
        // This runs on cache miss
        userId = key.split(":")[1]
        return database.query(
            "SELECT * FROM users WHERE id = ?",
            userId
        )
    },
    ttl: 3600
})


PROS & CONS
───────────

✅ PROS:
• Simpler application code
• Cache library handles complexity
• Consistent caching logic
• Easier to maintain

❌ CONS:
• Tightly coupled to cache
• Less flexibility
• Cache failure = application failure
• Vendor lock-in
```

### Strategy 3: Write-Through Cache

```
┌────────────────────────────────────────────────────────────────────────┐
│                    WRITE-THROUGH PATTERN                               │
└────────────────────────────────────────────────────────────────────────┘

CONCEPT
───────
On write:
1. Update cache first
2. Then update database (synchronously)
Both succeed or both fail.

FLOW DIAGRAM
────────────

Update request:
     │
     ↓
┌─────────────────────────────────┐
│  1. Write to Cache              │
│     SET user:123 = {new data}   │
└────┬────────────────────────────┘
     │
     ↓
┌─────────────────────────────────┐
│  2. Write to Database           │
│     UPDATE users                │
│     SET ... WHERE id = 123      │
└────┬────────────────────────────┘
     │
     ↓
┌─────────────────────────────────┐
│  3. Confirm Success             │
│     Both succeeded ✅           │
└─────────────────────────────────┘


TIMELINE VIEW
─────────────

Cache-Aside Write:
T0: Update DB       (500ms)
T1: Delete cache    (5ms)
T2: Done            (505ms total)
    Cache is empty → Next read fetches from DB

Write-Through:
T0: Update cache    (5ms)
T1: Update DB       (500ms)
T2: Done            (505ms total)
    Cache has fresh data → Next read is instant! ✅


COMPARISON
──────────

Cache-Aside:
Write → DB → Invalidate cache
Next read: Cache miss → Slow ❌

Write-Through:
Write → Cache + DB
Next read: Cache hit → Fast! ✅


CODE EXAMPLE
────────────

function updateUser(userId, newData) {
    cacheKey = "user:" + userId

    // 1. Update cache
    success1 = cache.set(cacheKey, newData, ttl=3600)

    // 2. Update database
    success2 = database.update(
        "UPDATE users SET ... WHERE id = ?",
        userId, newData
    )

    // 3. Check both succeeded
    if (success1 && success2) {
        return "Success"
    } else {
        // Rollback if either failed
        cache.delete(cacheKey)
        throw Error("Update failed")
    }
}


PROS & CONS
───────────

✅ PROS:
• Cache always fresh
• No cache miss penalty on reads
• Data consistency (cache = DB)
• Great for read-heavy after writes

❌ CONS:
• Higher write latency (write to 2 places)
• More complex error handling
• Wasted writes (what if never read?)
• Cache failure = write failure
```

### Strategy 4: Write-Behind (Write-Back)

```
┌────────────────────────────────────────────────────────────────────────┐
│                    WRITE-BEHIND PATTERN                                │
└────────────────────────────────────────────────────────────────────────┘

CONCEPT
───────
On write:
1. Update cache immediately
2. Queue DB update (asynchronously)
3. DB updated in background

Fastest writes, but eventual consistency!

FLOW DIAGRAM
────────────

Update request:
     │
     ↓
┌─────────────────────────────────┐
│  1. Write to Cache              │
│     SET user:123 = {new data}   │
│     Time: 5ms                   │
└────┬────────────────────────────┘
     │
     ↓
┌─────────────────────────────────┐
│  2. Queue DB Update             │
│     Add to write queue          │
│     Time: 1ms                   │
└────┬────────────────────────────┘
     │
     ↓
┌─────────────────────────────────┐
│  3. Return Success Immediately  │
│     Total: 6ms ✅ (Very fast!)  │
└─────────────────────────────────┘
     │
     │ (Background process)
     ↓
┌─────────────────────────────────┐
│  4. Background Writer           │
│     Process queue               │
│     UPDATE database             │
│     Time: 500ms (async)         │
└─────────────────────────────────┘


WRITE QUEUE
───────────

┌──────────────────────────────────────────┐
│  Write Queue (In-Memory)                 │
├──────────────────────────────────────────┤
│                                          │
│  [Update user:123]                       │
│  [Update user:456]                       │
│  [Update user:789]                       │
│  [Update user:101]                       │
│                                          │
│  Background worker processes queue:      │
│  • Batch updates                         │
│  • Coalesce duplicate updates            │
│  • Retry on failure                      │
└──────────────────────────────────────────┘


BATCHING EXAMPLE
────────────────

Without Write-Behind:
Update user:123 → DB (500ms)
Update user:456 → DB (500ms)
Update user:789 → DB (500ms)
Total: 1500ms ❌

With Write-Behind:
Update user:123 → Cache (5ms) → Queue
Update user:456 → Cache (5ms) → Queue
Update user:789 → Cache (5ms) → Queue
User sees: 5ms each ✅

Background:
Batch update all 3 users → DB (600ms)
Total DB time: 600ms (vs 1500ms)


COALESCING
──────────

Multiple updates to same key:

T0: user:123 = {v1} → Queue
T1: user:123 = {v2} → Queue
T2: user:123 = {v3} → Queue

Background worker:
Only write latest: user:123 = {v3}
Saves 2 DB writes! ✅


RISKS
─────

Cache crash before DB update:
┌─────────────────────────────────┐
│  1. Write to cache ✅           │
│  2. Queue update ✅             │
│  3. Return success ✅           │
└─────────────────────────────────┘
     │
     │ 💥 Cache crashes!
     ↓
┌─────────────────────────────────┐
│  Queue lost!                    │
│  DB never updated! ❌           │
│  Data loss!                     │
└─────────────────────────────────┘

Mitigation:
• Persistent queue (disk-backed)
• Replication
• Periodic snapshots


PROS & CONS
───────────

✅ PROS:
• Fastest writes (5-10ms)
• Reduced DB load
• Can batch updates
• Can coalesce duplicates
• Best for write-heavy workloads

❌ CONS:
• Eventual consistency (not immediate)
• Risk of data loss (cache failure)
• Complex implementation
• Harder to debug
• Not suitable for critical data
```

## 4. Cache Eviction Policies

### Visual: When Cache is Full

```
┌────────────────────────────────────────────────────────────────────────┐
│                    CACHE EVICTION POLICIES                             │
└────────────────────────────────────────────────────────────────────────┘

PROBLEM
───────
Cache has limited space (e.g., 1GB)
What happens when it's full?
Need to remove (evict) old entries to make room.

┌──────────────────────────────────────────┐
│  Cache (1GB - FULL)                      │
├──────────────────────────────────────────┤
│  [Entry 1] [Entry 2] [Entry 3] ...       │
│  [Entry 98] [Entry 99] [Entry 100]       │
│                                          │
│  New entry needs space! ❌               │
│  Which entry to remove?                  │
└──────────────────────────────────────────┘


POLICY 1: LRU (Least Recently Used)
────────────────────────────────────

Remove the entry that hasn't been accessed longest.

Timeline:
T0: Access A
T1: Access B
T2: Access C
T3: Access A  ← A becomes recent again
T4: Access B  ← B becomes recent
T5: Need to evict → Remove C (least recently used)

Visual:
┌──────────────────────────────────────────┐
│  Cache (Ordered by access time)          │
├──────────────────────────────────────────┤
│  Most Recent:                            │
│  [B] ← Accessed T4                       │
│  [A] ← Accessed T3                       │
│  [C] ← Accessed T2  ← Evict this! ❌     │
│  Least Recent                            │
└──────────────────────────────────────────┘

Implementation: Doubly linked list + HashMap
Time: O(1) for access and eviction


POLICY 2: LFU (Least Frequently Used)
──────────────────────────────────────

Remove the entry accessed least number of times.

Access counts:
Entry A: ████████ (8 times)
Entry B: ███████████ (11 times)
Entry C: ██ (2 times)  ← Evict this!
Entry D: ████████████████ (16 times)

Best for: Data with consistent access patterns


POLICY 3: FIFO (First In First Out)
────────────────────────────────────

Remove the oldest entry (like a queue).

┌──────────────────────────────────────────┐
│  Cache (Queue)                           │
├──────────────────────────────────────────┤
│  Oldest:   [A] ← Added T0  ← Evict! ❌   │
│            [B] ← Added T1                │
│            [C] ← Added T2                │
│  Newest:   [D] ← Added T3                │
└──────────────────────────────────────────┘

Simple but not optimal (may evict popular items)


POLICY 4: TTL (Time To Live)
─────────────────────────────

Entries auto-expire after fixed time.

┌──────────────────────────────────────────┐
│  Entry A: Created T0, TTL 60s            │
│  Entry B: Created T10, TTL 60s           │
│  Entry C: Created T20, TTL 60s           │
│                                          │
│  At T65:                                 │
│  • Entry A expired (T0 + 60 < T65) ❌    │
│  • Entry B expired (T10 + 60 < T65) ❌   │
│  • Entry C alive (T20 + 60 > T65) ✅     │
└──────────────────────────────────────────┘

Best for: Time-sensitive data


COMPARISON
──────────

┌──────────────┬────────────┬────────────┬────────────┐
│  Policy      │  Complexity│  Use Case  │  Pros      │
├──────────────┼────────────┼────────────┼────────────┤
│  LRU         │  O(1)      │  General   │  Most      │
│              │            │  purpose   │  popular   │
├──────────────┼────────────┼────────────┼────────────┤
│  LFU         │  O(log n)  │  Consistent│  Keeps hot │
│              │            │  patterns  │  data      │
├──────────────┼────────────┼────────────┼────────────┤
│  FIFO        │  O(1)      │  Simple    │  Easy to   │
│              │            │  needs     │  implement │
├──────────────┼────────────┼────────────┼────────────┤
│  TTL         │  O(1)      │  Time-     │  Automatic │
│              │            │  sensitive │  expiry    │
└──────────────┴────────────┴────────────┴────────────┘
```

## 5. Cache Invalidation Strategies

### Visual: Keeping Cache Fresh

```
┌────────────────────────────────────────────────────────────────────────┐
│                    CACHE INVALIDATION                                  │
└────────────────────────────────────────────────────────────────────────┘

"There are only two hard things in Computer Science:
 cache invalidation and naming things."
 - Phil Karlton


STRATEGY 1: TTL (Time-Based)
─────────────────────────────

Set expiration time on cache entries.

┌──────────────────────────────────────────┐
│  Redis:                                  │
│  SET user:123 {data} EX 3600             │
│      (expires in 1 hour)                 │
└──────────────────────────────────────────┘

Timeline:
T0: Cache entry created (TTL: 3600s)
T1800: Entry still valid (1800s remaining)
T3600: Entry expires ❌ (automatically removed)
T3601: Next access → Cache miss → Fetch from DB

Pros: Simple, automatic
Cons: Data may be stale before expiry


STRATEGY 2: Event-Based Invalidation
─────────────────────────────────────

Invalidate cache when data changes.

┌──────────────────────────────────────────┐
│  1. User updates profile                 │
└────┬─────────────────────────────────────┘
     │
     ↓
┌──────────────────────────────────────────┐
│  2. Update database                      │
│     UPDATE users SET name='John'         │
│     WHERE id=123                         │
└────┬─────────────────────────────────────┘
     │
     ↓
┌──────────────────────────────────────────┐
│  3. Invalidate cache                     │
│     DELETE user:123                      │
│     (Remove stale data)                  │
└──────────────────────────────────────────┘

Pros: Data always fresh
Cons: More complex, requires event handling


STRATEGY 3: Write-Through (Update on Write)
────────────────────────────────────────────

Update cache AND database on write.

┌──────────────────────────────────────────┐
│  1. User updates profile                 │
└────┬─────────────────────────────────────┘
     │
     ├────────────────┬────────────────────┐
     ↓                ↓                    ↓
┌─────────────┐  ┌─────────────┐   ┌─────────────┐
│  Update     │  │  Update     │   │  Publish    │
│  Cache      │  │  Database   │   │  Event      │
│  user:123   │  │  users      │   │  "user      │
│             │  │  table      │   │  updated"   │
└─────────────┘  └─────────────┘   └─────────────┘

Pros: Cache always fresh, fast reads
Cons: Slower writes, more complex


STRATEGY 4: Cache-Aside (Lazy Invalidation)
────────────────────────────────────────────

Only invalidate, don't update.

┌──────────────────────────────────────────┐
│  1. User updates profile                 │
└────┬─────────────────────────────────────┘
     │
     ↓
┌──────────────────────────────────────────┐
│  2. Update database                      │
└────┬─────────────────────────────────────┘
     │
     ↓
┌──────────────────────────────────────────┐
│  3. DELETE cache entry                   │
│     (Don't update, just remove)          │
└────┬─────────────────────────────────────┘
     │
     ↓
┌──────────────────────────────────────────┐
│  4. Next read:                           │
│     → Cache miss                         │
│     → Fetch from DB                      │
│     → Store in cache                     │
└──────────────────────────────────────────┘

Pros: Simple, consistent
Cons: Next read is slow (cache miss)


STRATEGY 5: Pub/Sub for Distributed Invalidation
─────────────────────────────────────────────────

Multiple app servers need to invalidate:

┌──────────────────────────────────────────┐
│  App Server 1                            │
│  Updates user:123                        │
└────┬─────────────────────────────────────┘
     │
     │ Publish "user:123 updated"
     ↓
┌──────────────────────────────────────────┐
│  Message Broker (Redis Pub/Sub)          │
└────┬────────────┬────────────┬───────────┘
     │            │            │
     │ Broadcast  │ Broadcast  │ Broadcast
     ↓            ↓            ↓
┌─────────┐  ┌─────────┐  ┌─────────┐
│ Server 1│  │ Server 2│  │ Server 3│
│ Delete  │  │ Delete  │  │ Delete  │
│ user:123│  │ user:123│  │ user:123│
└─────────┘  └─────────┘  └─────────┘

All servers invalidate their local cache!
```

## 6. System Design Interview Answer

### Short Answer (3-4 minutes):

> **Caching** stores frequently accessed data in fast memory (RAM) to avoid expensive operations like database queries or API calls, improving response times from 500ms to 5ms (100x faster).
>
> **Cache hierarchy** typically includes multiple layers:
> 1. Browser cache (instant, no network)
> 2. CDN (20-50ms, static assets)
> 3. Application memory (<1ms, in-process)
> 4. Redis/Memcached (1-5ms, distributed)
> 5. Database query cache (10-50ms)
>
> **Common caching strategies**:
> - **Cache-Aside** (most common): App checks cache → if miss, fetch from DB → store in cache
> - **Read-Through**: Cache handles DB fetching automatically
> - **Write-Through**: Update cache AND database synchronously
> - **Write-Behind**: Update cache immediately, queue DB update asynchronously (fastest writes)
>
> **Cache eviction** policies include:
> - **LRU** (Least Recently Used) - most popular, O(1) operations
> - **LFU** (Least Frequently Used) - keeps frequently accessed data
> - **TTL** (Time To Live) - automatic expiration
>
> **Cache invalidation** is one of the hardest problems in computer science. Common approaches:
> - **TTL-based**: Auto-expire after time (simple but may serve stale data)
> - **Event-based**: Invalidate when data changes (fresh data but complex)
> - **Write-through**: Update cache on writes (always fresh but slower writes)
>
> **Redis** is the most popular distributed cache due to:
> - In-memory speed (< 5ms)
> - Rich data structures (strings, lists, sets, sorted sets, hashes)
> - Persistence options
> - Pub/Sub for invalidation
> - High availability with replication
>
> Key metrics to monitor: **cache hit ratio** (aim for >80%), latency, memory usage, and eviction rate.

---

## Key Technologies:
- **Redis**: Most popular distributed cache
- **Memcached**: Simple, fast key-value cache
- **CDN**: Cloudflare, AWS CloudFront, Akamai
- **Browser Cache**: HTTP Cache-Control headers
- **Application Cache**: Caffeine (Java), node-cache (Node.js)
