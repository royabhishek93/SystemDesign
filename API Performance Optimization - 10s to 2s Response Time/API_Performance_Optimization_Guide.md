# How to Reduce API Response Time from 10 Seconds to 2 Seconds

> **Interview Level**: Senior Engineer (5+ Years)
> **Real Impact**: 80% faster response = Better UX + Lower costs
> **Focus**: Practical optimization techniques

---

## 📋 Table of Contents

1. [Problem Statement](#problem-statement)
2. [Performance Profiling - Find the Bottleneck](#performance-profiling)
3. [Database Optimization](#database-optimization)
4. [Caching Strategy](#caching-strategy)
5. [Code-Level Optimization](#code-level-optimization)
6. [Network & Infrastructure](#network--infrastructure)
7. [Complete Example - Before & After](#complete-example)
8. [Interview Q&A](#interview-qa)

---

## Problem Statement

**Interviewer**: "Your API is taking 10 seconds to respond. How will you reduce it to 2 seconds?"

**What They're Testing**:
- Systematic approach to performance optimization
- Understanding of bottlenecks
- Database, caching, code, and infrastructure knowledge
- Profiling and monitoring skills

---

## Performance Profiling - Find the Bottleneck

### Step 1: Measure First, Optimize Later

```
┌─────────────────────────────────────────────────────┐
│         DON'T GUESS - MEASURE THE PROBLEM!          │
├─────────────────────────────────────────────────────┤
│                                                     │
│  Total Response Time: 10 seconds                   │
│                                                     │
│  ┌──────────────────────────────────────┐          │
│  │  Database Query:       7 seconds     │ ← 70%   │
│  │  External API Call:    2 seconds     │ ← 20%   │
│  │  Business Logic:       0.8 seconds   │ ← 8%    │
│  │  Network Overhead:     0.2 seconds   │ ← 2%    │
│  └──────────────────────────────────────┘          │
│                                                     │
│  ✅ Focus on: Database (70% of time)               │
│  ✅ Then: External API (20% of time)               │
│                                                     │
└─────────────────────────────────────────────────────┘
```

### Profiling Tools

```java
// 1. Spring Boot Actuator + Micrometer
@RestController
@Timed  // Automatically tracks response time
public class UserController {

    @GetMapping("/users/{id}/profile")
    @Timed(value = "user.profile", percentiles = {0.5, 0.95, 0.99})
    public UserProfile getUserProfile(@PathVariable Long id) {
        // Your code
    }
}

// 2. Logging with timestamps
@Slf4j
@Service
public class UserService {

    public UserProfile getProfile(Long userId) {
        long start = System.currentTimeMillis();

        log.info("Fetching user: {}", userId);
        User user = userRepository.findById(userId);
        log.info("User fetched in {}ms", System.currentTimeMillis() - start);

        long orderStart = System.currentTimeMillis();
        List<Order> orders = orderRepository.findByUserId(userId);
        log.info("Orders fetched in {}ms", System.currentTimeMillis() - orderStart);

        // ... rest of code
    }
}
```

### Sample Profiling Output

```
[INFO] Fetching user: 123
[INFO] User fetched in 50ms
[INFO] Orders fetched in 6800ms          ← BOTTLENECK!
[INFO] Recommendations fetched in 2000ms  ← Secondary bottleneck
[INFO] Profile generated in 150ms
[INFO] Total time: 9000ms
```

---

## Database Optimization

### Problem 1: N+1 Query Problem

#### ❌ SLOW (10 seconds) - N+1 Queries

```java
// This executes 1 query for user + N queries for orders
@GetMapping("/users/{id}/orders")
public UserWithOrders getUserOrders(@PathVariable Long id) {

    User user = userRepository.findById(id);  // Query 1

    List<Order> orders = new ArrayList<>();
    for (OrderSummary summary : user.getOrderSummaries()) {
        Order order = orderRepository.findById(summary.getId());  // Query 2, 3, 4...
        orders.add(order);
    }

    return new UserWithOrders(user, orders);
}

// If user has 100 orders → 101 queries! (10 seconds)
```

**Visualization:**
```
┌────────────────────────────────────────────────────┐
│               N+1 QUERY PROBLEM                    │
├────────────────────────────────────────────────────┤
│                                                    │
│  Query 1: SELECT * FROM users WHERE id = 1        │
│  Query 2: SELECT * FROM orders WHERE id = 101     │
│  Query 3: SELECT * FROM orders WHERE id = 102     │
│  Query 4: SELECT * FROM orders WHERE id = 103     │
│  ...                                               │
│  Query 101: SELECT * FROM orders WHERE id = 200   │
│                                                    │
│  Total: 101 queries × 100ms = 10,100ms (10s)      │
│                                                    │
└────────────────────────────────────────────────────┘
```

#### ✅ FAST (200ms) - Single Query with JOIN

```java
// Entity with JOIN FETCH
@Entity
public class User {
    @Id
    private Long id;

    @OneToMany(mappedBy = "user")
    private List<Order> orders;
}

// Repository with optimized query
@Query("SELECT u FROM User u LEFT JOIN FETCH u.orders WHERE u.id = :id")
User findByIdWithOrders(@Param("id") Long id);

// Controller
@GetMapping("/users/{id}/orders")
public UserWithOrders getUserOrders(@PathVariable Long id) {
    User user = userRepository.findByIdWithOrders(id);  // Single query!
    return new UserWithOrders(user, user.getOrders());
}

// Single query fetches everything: 200ms
```

**Visualization:**
```
┌────────────────────────────────────────────────────┐
│           OPTIMIZED WITH JOIN FETCH                │
├────────────────────────────────────────────────────┤
│                                                    │
│  Query 1:                                          │
│    SELECT u.*, o.*                                 │
│    FROM users u                                    │
│    LEFT JOIN orders o ON u.id = o.user_id         │
│    WHERE u.id = 1                                  │
│                                                    │
│  Total: 1 query × 200ms = 200ms                    │
│                                                    │
│  ⚡ 50x FASTER!                                    │
│                                                    │
└────────────────────────────────────────────────────┘
```

---

### Problem 2: Missing Database Index

#### ❌ SLOW (7 seconds) - No Index

```sql
-- Query without index (Full table scan)
SELECT * FROM orders
WHERE user_id = 123 AND created_at > '2024-01-01';

-- Scans 10 million rows → 7 seconds
```

#### ✅ FAST (50ms) - With Composite Index

```sql
-- Create composite index
CREATE INDEX idx_user_created ON orders(user_id, created_at);

-- Same query with index
SELECT * FROM orders
WHERE user_id = 123 AND created_at > '2024-01-01';

-- Scans 100 rows → 50ms (140x faster!)
```

**Visualization:**
```
┌────────────────────────────────────────────────────┐
│        WITHOUT INDEX (Full Table Scan)             │
├────────────────────────────────────────────────────┤
│                                                    │
│  Check row 1    ✗                                  │
│  Check row 2    ✗                                  │
│  Check row 3    ✗                                  │
│  ...                                               │
│  Check row 9,999,999 ✗                             │
│  Check row 10,000,000 ✗                            │
│                                                    │
│  Time: 7,000ms                                     │
│                                                    │
└────────────────────────────────────────────────────┘

┌────────────────────────────────────────────────────┐
│         WITH INDEX (B-Tree Search)                 │
├────────────────────────────────────────────────────┤
│                                                    │
│  B-Tree lookup for user_id=123:                   │
│    Level 1 → Level 2 → Level 3 → Found            │
│  Filter by created_at > '2024-01-01'              │
│                                                    │
│  Rows scanned: 100                                 │
│  Time: 50ms                                        │
│                                                    │
│  ⚡ 140x FASTER!                                   │
│                                                    │
└────────────────────────────────────────────────────┘
```

---

### Problem 3: Large Data Fetch

#### ❌ SLOW - Fetching All Columns

```java
// Fetches all columns including BLOB (images, documents)
@Query("SELECT u FROM User u WHERE u.id = :id")
User findById(@Param("id") Long id);  // 5 seconds
```

#### ✅ FAST - DTO Projection (Only Needed Columns)

```java
// Fetch only required fields
@Query("SELECT new com.example.UserDTO(u.id, u.name, u.email) " +
       "FROM User u WHERE u.id = :id")
UserDTO findUserById(@Param("id") Long id);  // 100ms

// DTO
public class UserDTO {
    private Long id;
    private String name;
    private String email;
    // Constructor
}
```

**Time Saved**: 5 seconds → 100ms (50x faster)

---

## Caching Strategy

### 3-Layer Caching Architecture

```
┌─────────────────────────────────────────────────────┐
│              CACHING LAYERS                         │
├─────────────────────────────────────────────────────┤
│                                                     │
│  L1: Application Cache (Caffeine)                  │
│  ┌──────────────────────────────────┐              │
│  │  In-Memory, 10ms response        │              │
│  │  User Session, Static Data       │              │
│  └────────────┬─────────────────────┘              │
│               │ Cache Miss                          │
│               ▼                                     │
│  L2: Distributed Cache (Redis)                     │
│  ┌──────────────────────────────────┐              │
│  │  Network call, 50ms response     │              │
│  │  Shared across instances         │              │
│  └────────────┬─────────────────────┘              │
│               │ Cache Miss                          │
│               ▼                                     │
│  L3: Database                                       │
│  ┌──────────────────────────────────┐              │
│  │  Disk I/O, 200-500ms response    │              │
│  │  Source of truth                 │              │
│  └──────────────────────────────────┘              │
│                                                     │
└─────────────────────────────────────────────────────┘
```

### Implementation

```java
@Service
@Slf4j
public class UserService {

    @Autowired
    private UserRepository userRepository;

    @Autowired
    private RedisTemplate<String, User> redisTemplate;

    // L1 Cache: Caffeine (in-memory)
    private final LoadingCache<Long, User> localCache = Caffeine.newBuilder()
        .maximumSize(10_000)
        .expireAfterWrite(5, TimeUnit.MINUTES)
        .build(this::loadUserFromRedis);

    public User getUser(Long userId) {
        // L1: Check local cache (10ms)
        try {
            return localCache.get(userId);
        } catch (Exception e) {
            log.warn("Cache miss, fetching from database", e);
            return loadUserFromDatabase(userId);
        }
    }

    private User loadUserFromRedis(Long userId) {
        // L2: Check Redis (50ms)
        String key = "user:" + userId;
        User user = redisTemplate.opsForValue().get(key);

        if (user != null) {
            log.info("User {} found in Redis", userId);
            return user;
        }

        // L3: Fetch from database (500ms)
        log.info("User {} not in cache, fetching from DB", userId);
        user = loadUserFromDatabase(userId);

        // Store in Redis for next time
        redisTemplate.opsForValue().set(key, user, Duration.ofMinutes(10));

        return user;
    }

    private User loadUserFromDatabase(Long userId) {
        return userRepository.findById(userId)
            .orElseThrow(() -> new UserNotFoundException(userId));
    }
}
```

### Cache Performance Comparison

```
┌─────────────────────────────────────────────────────┐
│         CACHE HIT PERFORMANCE                       │
├─────────────────────────────────────────────────────┤
│                                                     │
│  No Cache:         500ms (Database query)          │
│  L2 Cache (Redis): 50ms  (10x faster)              │
│  L1 Cache (Local): 10ms  (50x faster)              │
│                                                     │
│  With 90% cache hit rate:                          │
│    90% × 10ms + 10% × 500ms = 59ms average         │
│                                                     │
│  Without cache:                                     │
│    100% × 500ms = 500ms average                    │
│                                                     │
│  ⚡ 8.5x FASTER with caching!                       │
│                                                     │
└─────────────────────────────────────────────────────┘
```

---

## Code-Level Optimization

### Problem 1: Synchronous External API Calls

#### ❌ SLOW (6 seconds) - Sequential Calls

```java
@GetMapping("/users/{id}/dashboard")
public Dashboard getDashboard(@PathVariable Long id) {

    User user = userService.getUser(id);              // 500ms
    List<Order> orders = orderService.getOrders(id);  // 2000ms
    List<Product> recommendations =
        recommendationService.getRecommendations(id); // 3000ms
    Weather weather = weatherService.getWeather();    // 500ms

    // Total: 6000ms (sequential)
    return new Dashboard(user, orders, recommendations, weather);
}
```

**Visualization:**
```
Time →
0s────────1s────────2s────────3s────────4s────────5s────────6s
│─────────│─────────│─────────│─────────│─────────│─────────│
│  User   │      Orders       │  Recommendations  │ Weather │
└─────────┴───────────────────┴───────────────────┴─────────┘
Total: 6 seconds
```

#### ✅ FAST (3 seconds) - Parallel Calls

```java
@Service
public class DashboardService {

    @Autowired
    private UserService userService;
    @Autowired
    private OrderService orderService;
    @Autowired
    private RecommendationService recommendationService;
    @Autowired
    private WeatherService weatherService;

    // Thread pool for parallel execution
    private final ExecutorService executor =
        Executors.newFixedThreadPool(10);

    public Dashboard getDashboard(Long userId) throws Exception {

        // Submit all tasks in parallel
        CompletableFuture<User> userFuture = CompletableFuture
            .supplyAsync(() -> userService.getUser(userId), executor);

        CompletableFuture<List<Order>> ordersFuture = CompletableFuture
            .supplyAsync(() -> orderService.getOrders(userId), executor);

        CompletableFuture<List<Product>> recommendationsFuture =
            CompletableFuture.supplyAsync(
                () -> recommendationService.getRecommendations(userId),
                executor
            );

        CompletableFuture<Weather> weatherFuture = CompletableFuture
            .supplyAsync(() -> weatherService.getWeather(), executor);

        // Wait for all to complete
        CompletableFuture.allOf(
            userFuture, ordersFuture, recommendationsFuture, weatherFuture
        ).join();

        // Get results
        User user = userFuture.get();
        List<Order> orders = ordersFuture.get();
        List<Product> recommendations = recommendationsFuture.get();
        Weather weather = weatherFuture.get();

        // Total: 3000ms (parallel - longest task time)
        return new Dashboard(user, orders, recommendations, weather);
    }
}
```

**Visualization:**
```
Time →
0s────────1s────────2s────────3s
│─────────│─────────│─────────│
│  User   │                   │ ← 500ms
│      Orders                 │ ← 2000ms
│  Recommendations            │ ← 3000ms (longest)
│ Weather │                   │ ← 500ms
└─────────┴─────────┴─────────┘
Total: 3 seconds (2x faster!)
```

---

### Problem 2: Unnecessary Data Processing

#### ❌ SLOW - Processing Large Dataset

```java
// Fetch 10,000 products, filter in Java
public List<Product> getActiveProducts() {
    List<Product> allProducts = productRepository.findAll();  // 10,000 products

    return allProducts.stream()
        .filter(p -> p.isActive())
        .filter(p -> p.getStock() > 0)
        .collect(Collectors.toList());

    // Fetched 10,000, returned 100 → Waste of 9,900!
}
```

#### ✅ FAST - Filter at Database Level

```java
// Filter in database, fetch only 100 products
@Query("SELECT p FROM Product p WHERE p.active = true AND p.stock > 0")
List<Product> findActiveProductsWithStock();

// Returns only 100 products → 100x less data transfer
```

---

## Network & Infrastructure

### 1. Enable HTTP Compression (Gzip)

```yaml
# application.yml
server:
  compression:
    enabled: true
    mime-types: application/json,application/xml,text/html,text/xml,text/plain
    min-response-size: 1024  # Compress if response > 1KB
```

**Impact**:
```
Without compression: 500KB response → 2 seconds (slow network)
With compression:    50KB response  → 200ms
⚡ 10x faster!
```

---

### 2. Use CDN for Static Assets

```
┌─────────────────────────────────────────────────────┐
│         WITHOUT CDN (Slow)                          │
├─────────────────────────────────────────────────────┤
│                                                     │
│  User (India) → Server (USA) → 2000ms latency      │
│                                                     │
└─────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────┐
│         WITH CDN (Fast)                             │
├─────────────────────────────────────────────────────┤
│                                                     │
│  User (India) → CDN Mumbai → 50ms latency           │
│                                                     │
│  ⚡ 40x FASTER!                                     │
│                                                     │
└─────────────────────────────────────────────────────┘
```

---

### 3. Connection Pooling

```java
// HikariCP configuration
spring.datasource.hikari.maximum-pool-size=50
spring.datasource.hikari.minimum-idle=10
spring.datasource.hikari.connection-timeout=30000
spring.datasource.hikari.idle-timeout=600000
```

**Without Pooling**:
```
Request 1: Create connection (500ms) + Query (100ms) = 600ms
Request 2: Create connection (500ms) + Query (100ms) = 600ms
```

**With Pooling**:
```
Request 1: Reuse connection (0ms) + Query (100ms) = 100ms
Request 2: Reuse connection (0ms) + Query (100ms) = 100ms
⚡ 6x faster!
```

---

## Complete Example - Before & After

### ❌ SLOW API (10 seconds)

```java
@RestController
@RequestMapping("/api/users")
public class UserController {

    @Autowired
    private UserRepository userRepository;
    @Autowired
    private OrderRepository orderRepository;
    @Autowired
    private ProductRepository productRepository;

    @GetMapping("/{id}/dashboard")
    public Dashboard getDashboard(@PathVariable Long id) {

        // Problem 1: N+1 query
        User user = userRepository.findById(id);  // 500ms

        List<Order> orders = new ArrayList<>();
        for (Long orderId : user.getOrderIds()) {
            Order order = orderRepository.findById(orderId);  // 100ms × 50 = 5000ms
            orders.add(order);
        }

        // Problem 2: No caching
        List<Product> allProducts = productRepository.findAll();  // 2000ms

        // Problem 3: Processing in Java
        List<Product> activeProducts = allProducts.stream()
            .filter(p -> p.isActive())
            .collect(Collectors.toList());

        // Problem 4: Sequential external calls
        List<Product> recommendations = getRecommendations(id);  // 2000ms

        // Total: 500 + 5000 + 2000 + 2000 = 9500ms (≈10 seconds)
        return new Dashboard(user, orders, activeProducts, recommendations);
    }
}
```

---

### ✅ FAST API (2 seconds)

```java
@RestController
@RequestMapping("/api/users")
@Slf4j
public class UserController {

    @Autowired
    private UserService userService;
    @Autowired
    private DashboardService dashboardService;

    @GetMapping("/{id}/dashboard")
    @Cacheable(value = "dashboard", key = "#id")  // Solution 1: Response caching
    public Dashboard getDashboard(@PathVariable Long id) {
        return dashboardService.getDashboardOptimized(id);
    }
}

@Service
public class DashboardService {

    @Autowired
    private UserRepository userRepository;
    @Autowired
    private OrderRepository orderRepository;
    @Autowired
    private ProductRepository productRepository;
    @Autowired
    private RecommendationService recommendationService;
    @Autowired
    private RedisTemplate<String, Object> redisTemplate;

    private final ExecutorService executor = Executors.newFixedThreadPool(10);

    public Dashboard getDashboardOptimized(Long userId) {

        // Solution 2: JOIN FETCH (eliminates N+1)
        CompletableFuture<User> userFuture = CompletableFuture.supplyAsync(
            () -> userRepository.findByIdWithOrders(userId),  // 200ms
            executor
        );

        // Solution 3: Query optimization + caching
        CompletableFuture<List<Product>> productsFuture =
            CompletableFuture.supplyAsync(
                () -> getActiveProductsCached(),  // 50ms (from cache)
                executor
            );

        // Solution 4: Parallel external call
        CompletableFuture<List<Product>> recommendationsFuture =
            CompletableFuture.supplyAsync(
                () -> recommendationService.getRecommendations(userId),  // 2000ms
                executor
            );

        // Wait for all (parallel execution)
        CompletableFuture.allOf(
            userFuture, productsFuture, recommendationsFuture
        ).join();

        try {
            User user = userFuture.get();
            List<Product> products = productsFuture.get();
            List<Product> recommendations = recommendationsFuture.get();

            // Total: max(200, 50, 2000) = 2000ms (2 seconds)
            return new Dashboard(user, user.getOrders(), products, recommendations);

        } catch (Exception e) {
            throw new RuntimeException("Dashboard generation failed", e);
        }
    }

    @Cacheable(value = "active-products", key = "'all'")
    private List<Product> getActiveProductsCached() {
        // Check Redis cache first
        String key = "products:active";
        List<Product> cached = (List<Product>) redisTemplate.opsForValue().get(key);

        if (cached != null) {
            return cached;  // 10ms
        }

        // Solution 5: Database-level filtering
        List<Product> products = productRepository
            .findActiveProductsWithStock();  // 100ms

        // Cache for 5 minutes
        redisTemplate.opsForValue().set(key, products, Duration.ofMinutes(5));

        return products;
    }
}

// Optimized repository
@Repository
public interface UserRepository extends JpaRepository<User, Long> {

    @Query("SELECT u FROM User u LEFT JOIN FETCH u.orders WHERE u.id = :id")
    User findByIdWithOrders(@Param("id") Long id);
}

@Repository
public interface ProductRepository extends JpaRepository<Product, Long> {

    @Query("SELECT p FROM Product p WHERE p.active = true AND p.stock > 0")
    List<Product> findActiveProductsWithStock();
}
```

---

## Performance Comparison

```
┌─────────────────────────────────────────────────────┐
│         BEFORE vs AFTER OPTIMIZATION                │
├─────────────────────────────────────────────────────┤
│                                                     │
│  Operation           Before    After    Improvement│
│  ─────────────────────────────────────────────────│
│  User + Orders       5500ms    200ms    27.5x     │
│  Products            2000ms    50ms     40x       │
│  Recommendations     2000ms    2000ms   1x        │
│  (Parallel)          ─────     ─────    ─────     │
│                                                     │
│  TOTAL (Sequential)  9500ms    —        —         │
│  TOTAL (Parallel)    —         2000ms   4.75x     │
│                                                     │
│  ⚡ OVERALL: 10 seconds → 2 seconds (5x faster!)   │
│                                                     │
└─────────────────────────────────────────────────────┘
```

---

## Interview Q&A

### Q1: What's your approach to optimize a slow API?

**Answer**:
```
1. Profile first - Find the bottleneck
   - Use APM tools (New Relic, Datadog)
   - Add timing logs
   - Check database query logs

2. Optimize database (usually 70% of time)
   - Fix N+1 queries → Use JOIN FETCH
   - Add indexes on WHERE/JOIN columns
   - Use DTO projections (fetch only needed fields)
   - Consider read replicas

3. Add caching
   - L1: Local cache (Caffeine)
   - L2: Distributed cache (Redis)
   - Cache static/slow-changing data

4. Parallelize operations
   - Use CompletableFuture for independent calls
   - Don't wait sequentially

5. Code optimization
   - Filter at database, not in Java
   - Reduce data transfer
   - Use pagination

6. Infrastructure
   - Enable HTTP compression
   - Use CDN for static assets
   - Connection pooling
```

### Q2: How do you decide what to cache?

**Answer**:
```
Cache if:
✅ Data is read frequently (80/20 rule)
✅ Data doesn't change often (static/slow-changing)
✅ Expensive to compute/fetch

Don't cache if:
❌ Data changes very frequently
❌ Data is user-specific and not reused
❌ Memory constrained

Examples:
✅ Cache: Product catalog, user profiles, static configs
❌ Don't cache: Real-time stock prices, user cart
```

### Q3: What if parallel calls don't help?

**Answer**:
"If the longest task still takes 8 seconds, parallelizing won't help much. In that case:

1. **Async processing**: Return immediately, process in background
   ```
   Response: "Processing... Check status at /status/{id}"
   Background: Process and send notification when done
   ```

2. **Pagination**: Don't fetch all data at once
   ```
   Page 1: 20 items (fast)
   Load more on demand
   ```

3. **Partial response**: Show what's ready, lazy-load rest
   ```
   Fast data → Show immediately
   Slow data → Show "Loading..." spinner
   ```"

### Q4: How do you handle cache invalidation?

**Answer**:
```
Strategies:

1. TTL (Time To Live):
   - Set expiry time (5 minutes, 1 hour)
   - Simple but may show stale data

2. Write-through cache:
   - Update cache when database updates
   - Always consistent

3. Cache-aside with TTL:
   - Read from cache, fallback to DB
   - Update cache on write
   - TTL as backup

Example:
@Service
public class ProductService {

    @CachePut(value = "products", key = "#product.id")
    public Product updateProduct(Product product) {
        // Updates both DB and cache
        return productRepository.save(product);
    }

    @CacheEvict(value = "products", key = "#id")
    public void deleteProduct(Long id) {
        // Removes from both DB and cache
        productRepository.deleteById(id);
    }
}
```

---

## Key Takeaways

### Performance Optimization Checklist

```
✅ Database Optimization (70% impact)
   □ Fix N+1 queries with JOIN FETCH
   □ Add indexes on frequent queries
   □ Use DTO projections (fetch only needed columns)
   □ Consider read replicas for read-heavy workloads

✅ Caching (20% impact)
   □ Local cache (Caffeine/Guava)
   □ Distributed cache (Redis/Memcached)
   □ Cache static/slow-changing data
   □ Implement cache invalidation strategy

✅ Code Optimization (5% impact)
   □ Parallelize independent operations
   □ Filter at database, not in code
   □ Use async processing for slow tasks
   □ Implement pagination

✅ Infrastructure (5% impact)
   □ Enable HTTP compression
   □ Use CDN for static assets
   □ Connection pooling
   □ Horizontal scaling (more instances)
```

### Response Time Targets

```
┌──────────────────────────────────────────┐
│  Response Time Goals                     │
├──────────────────────────────────────────┤
│  < 100ms   : Excellent                   │
│  100-300ms : Good                        │
│  300-1000ms: Acceptable                  │
│  > 1000ms  : Slow (needs optimization)   │
│  > 3000ms  : Very slow (critical issue)  │
└──────────────────────────────────────────┘
```

---

**Good luck with your interview! 🚀**
