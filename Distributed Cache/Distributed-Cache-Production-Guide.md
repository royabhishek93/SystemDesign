# Distributed Cache - Production Implementation Guide

> **Target**: 10+ Years Experienced Developer
> **Updated**: March 2026
> **Interview Ready**: Complete guide with Redis cluster and production patterns

---

## 📊 Problem Statement (Already in Overview)

This content supplements the existing **00-Distributed-Cache-Overview.md** file with production implementation details.

---

## 🚀 Redis Cluster Setup (Production)

### Spring Boot Redis Configuration

```java
@Configuration
@EnableCaching
public class RedisConfig {

    @Value("${redis.cluster.nodes}")
    private List<String> clusterNodes;

    @Value("${redis.password}")
    private String password;

    @Bean
    public RedisConnectionFactory redisConnectionFactory() {
        // Parse cluster nodes
        List<RedisNode> nodes = clusterNodes.stream()
            .map(node -> {
                String[] parts = node.split(":");
                return new RedisNode(parts[0], Integer.parseInt(parts[1]));
            })
            .collect(Collectors.toList());

        // Configure cluster
        RedisClusterConfiguration clusterConfig = new RedisClusterConfiguration();
        clusterConfig.setClusterNodes(new HashSet<>(nodes));
        clusterConfig.setPassword(RedisPassword.of(password));
        clusterConfig.setMaxRedirects(3);

        // Connection pool settings
        LettuceClientConfiguration clientConfig = LettuceClientConfiguration.builder()
            .commandTimeout(Duration.ofSeconds(2))
            .shutdownTimeout(Duration.ZERO)
            .build();

        return new LettuceConnectionFactory(clusterConfig, clientConfig);
    }

    @Bean
    public RedisTemplate<String, Object> redisTemplate() {
        RedisTemplate<String, Object> template = new RedisTemplate<>();
        template.setConnectionFactory(redisConnectionFactory());

        // Serializers
        template.setKeySerializer(new StringRedisSerializer());
        template.setHashKeySerializer(new StringRedisSerializer());

        // Use JSON for values
        template.setValueSerializer(new GenericJackson2JsonRedisSerializer());
        template.setHashValueSerializer(new GenericJackson2JsonRedisSerializer());

        return template;
    }

    @Bean
    public CacheManager cacheManager() {
        RedisCacheConfiguration cacheConfig = RedisCacheConfiguration.defaultCacheConfig()
            .entryTtl(Duration.ofMinutes(10))
            .disableCachingNullValues()
            .serializeKeysWith(RedisSerializationContext.SerializationPair
                .fromSerializer(new StringRedisSerializer()))
            .serializeValuesWith(RedisSerializationContext.SerializationPair
                .fromSerializer(new GenericJackson2JsonRedisSerializer()));

        return RedisCacheManager.builder(redisConnectionFactory())
            .cacheDefaults(cacheConfig)
            .build();
    }
}
```

**application.yml:**

```yaml
spring:
  redis:
    cluster:
      nodes:
        - redis-node-1:6379
        - redis-node-2:6379
        - redis-node-3:6379
        - redis-node-4:6379
        - redis-node-5:6379
        - redis-node-6:6379
      max-redirects: 3
    password: ${REDIS_PASSWORD}
    timeout: 2000ms
    lettuce:
      pool:
        max-active: 20
        max-idle: 10
        min-idle: 5
        max-wait: 2000ms
```

---

## ⚡ Cache Stampede Protection (Mutex Pattern)

### Problem: Thundering Herd

```
Cache Expired
      │
      ▼
1000 requests hit cache miss simultaneously
      │
      ▼
1000 database queries execute (overload!)
```

### Solution: Mutex Lock Pattern

```java
@Service
public class UserService {

    @Autowired
    private RedisTemplate<String, Object> redisTemplate;

    @Autowired
    private UserRepository userRepository;

    private static final String LOCK_PREFIX = "lock:";
    private static final long LOCK_TTL_SECONDS = 10;

    /**
     * Get user with cache stampede protection
     */
    public User getUser(Long userId) {
        String cacheKey = "user:" + userId;

        // 1. Try cache first
        User cached = (User) redisTemplate.opsForValue().get(cacheKey);
        if (cached != null) {
            return cached;
        }

        // 2. Cache miss: Acquire mutex lock
        String lockKey = LOCK_PREFIX + cacheKey;
        Boolean lockAcquired = redisTemplate.opsForValue()
            .setIfAbsent(lockKey, "1", LOCK_TTL_SECONDS, TimeUnit.SECONDS);

        if (Boolean.TRUE.equals(lockAcquired)) {
            try {
                // This thread won the lock: Load from DB
                log.info("Thread {} acquired lock for key {}", Thread.currentThread().getId(), cacheKey);

                User user = userRepository.findById(userId)
                    .orElseThrow(() -> new UserNotFoundException(userId));

                // Cache result (5 min TTL)
                redisTemplate.opsForValue().set(cacheKey, user, 5, TimeUnit.MINUTES);

                return user;

            } finally {
                // Release lock
                redisTemplate.delete(lockKey);
            }

        } else {
            // Lock held by another thread: Wait and retry
            log.info("Thread {} waiting for lock on key {}", Thread.currentThread().getId(), cacheKey);

            try {
                // Wait briefly, then retry reading from cache
                Thread.sleep(50);  // 50ms

                // Other thread should have populated cache by now
                User user = (User) redisTemplate.opsForValue().get(cacheKey);
                if (user != null) {
                    return user;
                }

                // Still not in cache: Load from DB (fallback)
                return userRepository.findById(userId)
                    .orElseThrow(() -> new UserNotFoundException(userId));

            } catch (InterruptedException e) {
                Thread.currentThread().interrupt();
                throw new RuntimeException("Interrupted while waiting for cache", e);
            }
        }
    }
}
```

**Result**: Only 1 request hits database, others wait for cache to populate.

---

## 🔥 Hot Key Handling

### Problem: Viral Post

```
Single cache key gets 100K requests/second
      │
      ▼
Redis single node overloaded (hot partition)
```

### Solution 1: Local Cache (Caffeine) + Redis

```java
@Service
public class PostService {

    // L1 cache: Local in-memory (Caffeine)
    private final Cache<Long, Post> localCache = Caffeine.newBuilder()
        .expireAfterWrite(1, TimeUnit.MINUTES)  // Short TTL
        .maximumSize(1000)
        .recordStats()
        .build();

    // L2 cache: Distributed (Redis)
    @Autowired
    private RedisTemplate<String, Post> redisTemplate;

    @Autowired
    private PostRepository postRepository;

    /**
     * Multi-level cache: L1 (local) + L2 (Redis)
     */
    public Post getPost(Long postId) {
        // 1. Check L1 cache (in-memory, <1ms)
        Post cached = localCache.getIfPresent(postId);
        if (cached != null) {
            return cached;
        }

        // 2. Check L2 cache (Redis, 1-5ms)
        String redisKey = "post:" + postId;
        Post fromRedis = redisTemplate.opsForValue().get(redisKey);
        if (fromRedis != null) {
            localCache.put(postId, fromRedis);  // Populate L1
            return fromRedis;
        }

        // 3. Load from database
        Post post = postRepository.findById(postId)
            .orElseThrow(() -> new PostNotFoundException(postId));

        // 4. Populate both caches
        redisTemplate.opsForValue().set(redisKey, post, 10, TimeUnit.MINUTES);
        localCache.put(postId, post);

        return post;
    }
}
```

**Benefit**: 99%+ L1 hit rate for hot keys = sub-millisecond response

---

### Solution 2: Key Sharding (Random Suffix)

```java
/**
 * For extremely hot keys: Shard across multiple Redis keys
 */
public Post getPostWithSharding(Long postId) {
    // Add random suffix to distribute load
    int shard = ThreadLocalRandom.current().nextInt(10);  // 0-9
    String cacheKey = "post:" + postId + ":shard:" + shard;

    Post cached = redisTemplate.opsForValue().get(cacheKey);
    if (cached != null) {
        return cached;
    }

    // Cache miss: Load from DB
    Post post = postRepository.findById(postId)
        .orElseThrow(() -> new PostNotFoundException(postId));

    // Write to ALL shards (fan-out)
    for (int i = 0; i < 10; i++) {
        String key = "post:" + postId + ":shard:" + i;
        redisTemplate.opsForValue().set(key, post, 5, TimeUnit.MINUTES);
    }

    return post;
}
```

**Benefit**: Load distributed across 10 Redis nodes instead of 1

---

## 🔄 Cache Warming Strategies

### Strategy 1: Scheduled Warm-up

```java
@Service
public class CacheWarmingService {

    @Autowired
    private PostRepository postRepository;

    @Autowired
    private RedisTemplate<String, Post> redisTemplate;

    /**
     * Warm cache for trending posts every 5 minutes
     */
    @Scheduled(fixedRate = 300000)  // 5 minutes
    public void warmTrendingPosts() {
        log.info("Starting cache warm-up for trending posts");

        // Get top 1000 trending posts
        List<Post> trendingPosts = postRepository.findTrendingPosts(1000);

        for (Post post : trendingPosts) {
            String cacheKey = "post:" + post.getId();

            // Pre-populate cache
            redisTemplate.opsForValue().set(cacheKey, post, 10, TimeUnit.MINUTES);
        }

        log.info("Cache warm-up completed: {} posts cached", trendingPosts.size());
    }

    /**
     * Warm cache for specific user (after signup, login)
     */
    public void warmUserCache(Long userId) {
        User user = userRepository.findById(userId).orElse(null);
        if (user != null) {
            redisTemplate.opsForValue().set("user:" + userId, user, 30, TimeUnit.MINUTES);

            // Pre-load user's recent posts
            List<Post> userPosts = postRepository.findByUserId(userId, 10);
            for (Post post : userPosts) {
                redisTemplate.opsForValue().set("post:" + post.getId(), post, 10, TimeUnit.MINUTES);
            }
        }
    }
}
```

---

### Strategy 2: Application Startup Warm-up

```java
@Component
public class CacheInitializer implements ApplicationListener<ContextRefreshedEvent> {

    @Autowired
    private CacheWarmingService cacheWarmingService;

    @Override
    public void onApplicationEvent(ContextRefreshedEvent event) {
        log.info("Application started: warming critical caches");

        // Pre-load most accessed data
        cacheWarmingService.warmTrendingPosts();
        cacheWarmingService.warmPopularUsers();

        log.info("Cache initialization complete");
    }
}
```

---

## 📊 Monitoring & Alerting (Prometheus + Grafana)

### Expose Redis Metrics

```java
@Component
public class RedisCacheMetrics {

    @Autowired
    private RedisTemplate<String, Object> redisTemplate;

    private final MeterRegistry meterRegistry;

    public RedisCacheMetrics(MeterRegistry meterRegistry) {
        this.meterRegistry = meterRegistry;
    }

    /**
     * Track cache hit/miss ratio
     */
    public Object getWithMetrics(String key) {
        Timer.Sample sample = Timer.start(meterRegistry);

        Object value = redisTemplate.opsForValue().get(key);

        sample.stop(Timer.builder("cache.get.latency")
            .tag("cache", "redis")
            .register(meterRegistry));

        if (value != null) {
            meterRegistry.counter("cache.hit", "cache", "redis").increment();
        } else {
            meterRegistry.counter("cache.miss", "cache", "redis").increment();
        }

        return value;
    }

    /**
     * Scheduled task: Export Redis INFO metrics
     */
    @Scheduled(fixedRate = 60000)  // Every 60 seconds
    public void exportRedisMetrics() {
        try {
            Properties info = redisTemplate.getConnectionFactory()
                .getConnection()
                .info();

            // Memory usage
            long usedMemory = Long.parseLong(info.getProperty("used_memory"));
            meterRegistry.gauge("redis.memory.used", usedMemory);

            // Connected clients
            int connectedClients = Integer.parseInt(info.getProperty("connected_clients"));
            meterRegistry.gauge("redis.clients.connected", connectedClients);

            // Operations per second
            long ops = Long.parseLong(info.getProperty("instantaneous_ops_per_sec"));
            meterRegistry.gauge("redis.ops_per_sec", ops);

            // Hit rate
            long hits = Long.parseLong(info.getProperty("keyspace_hits"));
            long misses = Long.parseLong(info.getProperty("keyspace_misses"));
            double hitRate = (double) hits / (hits + misses);
            meterRegistry.gauge("redis.hit_rate", hitRate);

        } catch (Exception e) {
            log.error("Failed to export Redis metrics", e);
        }
    }
}
```

### Prometheus Queries

```promql
# Cache hit rate (should be >90%)
sum(rate(cache_hit_total[5m])) / (sum(rate(cache_hit_total[5m])) + sum(rate(cache_miss_total[5m])))

# Cache latency p99 (should be <10ms)
histogram_quantile(0.99, rate(cache_get_latency_bucket[5m]))

# Redis memory usage (alert if >80%)
redis_memory_used_bytes / redis_memory_max_bytes > 0.8

# Redis connections (alert if >80% of max)
redis_clients_connected / redis_maxclients > 0.8

# Evictions per second (alert if >100)
rate(redis_evicted_keys_total[1m]) > 100
```

### Grafana Dashboard

```json
{
  "dashboard": {
    "title": "Redis Cache Monitoring",
    "panels": [
      {
        "title": "Cache Hit Rate",
        "targets": [{
          "expr": "sum(rate(cache_hit_total[5m])) / (sum(rate(cache_hit_total[5m])) + sum(rate(cache_miss_total[5m])))"
        }],
        "alert": {
          "conditions": [
            {"evaluator": {"params": [0.9], "type": "lt"}}
          ]
        }
      },
      {
        "title": "Cache Latency p99",
        "targets": [{
          "expr": "histogram_quantile(0.99, rate(cache_get_latency_bucket[5m]))"
        }]
      },
      {
        "title": "Redis Memory Usage",
        "targets": [{
          "expr": "redis_memory_used_bytes"
        }]
      }
    ]
  }
}
```

---

## 🔧 Troubleshooting Guide

### Issue 1: High Cache Miss Rate

**Symptoms**: Hit rate drops from 95% → 60%

**Diagnosis**:
```bash
# Check Redis memory
redis-cli INFO memory | grep used_memory_human

# Check eviction stats
redis-cli INFO stats | grep evicted_keys

# Check TTLs
redis-cli --scan --pattern 'user:*' | head -10 | xargs -L1 redis-cli TTL
```

**Causes & Solutions**:
1. **Memory full, evicting keys**: Increase Redis memory or shorten TTLs
2. **TTLs too short**: Increase cache TTL from 5min → 15min
3. **Code deployment**: Cache cleared, will recover naturally
4. **Hot keys expired**: Implement cache warming

---

### Issue 2: High Latency Spikes

**Symptoms**: p99 latency spikes from 5ms → 500ms

**Diagnosis**:
```bash
# Check slow log
redis-cli SLOWLOG GET 10

# Check key distribution
redis-cli --bigkeys

# Check connections
redis-cli INFO clients | grep connected_clients

# Check CPU
redis-cli INFO cpu
```

**Causes & Solutions**:
1. **Large keys (>1MB)**: Break into smaller keys or compress
2. **Connection pool exhausted**: Increase max connections
3. **Network issues**: Check latency to Redis (ping)
4. **Hot key**: Implement local cache or key sharding

---

### Issue 3: Redis Cluster Split-Brain

**Symptoms**: Inconsistent data across nodes

**Diagnosis**:
```bash
# Check cluster status
redis-cli --cluster check redis-node-1:6379

# Check slot distribution
redis-cli CLUSTER SLOTS

# Check node roles
redis-cli CLUSTER NODES
```

**Solution**:
```bash
# Identify split nodes
redis-cli --cluster fix redis-node-1:6379 --cluster-fix-with-unreachable-masters

# Manual failover if needed
redis-cli -h redis-node-2 CLUSTER FAILOVER
```

---

### Issue 4: Cache Stampede

**Symptoms**: 1000 DB queries at same time (cache expired)

**Diagnosis**:
```bash
# Check DB query count spike
SELECT COUNT(*) FROM pg_stat_activity WHERE state = 'active';

# Check cache miss spike in metrics
```

**Solution**: Implement mutex lock pattern (see above section)

---

### Issue 5: Memory Leak

**Symptoms**: Redis memory grows unbounded

**Diagnosis**:
```bash
# Find keys without TTL
redis-cli --scan --pattern '*' | xargs -L1 redis-cli TTL | grep -c -- '-1'

# Find largest keys
redis-cli --bigkeys

# Sample random keys
redis-cli --scan --pattern 'user:*' | head -20 | xargs -L1 redis-cli DEBUG OBJECT
```

**Solution**:
```bash
# Set default TTL policy
redis-cli CONFIG SET maxmemory-policy allkeys-lru

# Add TTL to keys without expiry
redis-cli SCAN 0 MATCH 'user:*' | xargs -L1 redis-cli EXPIRE 3600
```

---

## 📋 Interview Q&A

### Q11: How do you prevent cache stampede?

**Answer:**
```
Mutex Lock Pattern:
1. Cache miss: Try to acquire lock (SETNX with TTL)
2. If lock acquired: Load from DB, cache result, release lock
3. If lock held by another thread: Wait 50ms, retry reading cache
4. Result: Only 1 DB query instead of 1000

Alternative: Probabilistic early expiration (refresh before TTL expires)
```

### Q12: How do you handle hot keys?

**Answer:**
```
Solution 1: Multi-level cache (L1 local + L2 Redis)
- L1: Caffeine in-memory (1-min TTL)
- L2: Redis (10-min TTL)
- 99% hit rate on L1 = <1ms latency

Solution 2: Key sharding (random suffix)
- post:123:shard:0 through post:123:shard:9
- Distribute load across 10 Redis nodes
- Write to all shards, read from random shard
```

### Q13: How do you warm the cache?

**Answer:**
```
Strategy 1: Scheduled warm-up
- Cron job every 5 minutes
- Pre-load trending posts (top 1000)
- Query: SELECT * FROM posts ORDER BY views DESC LIMIT 1000

Strategy 2: On-demand warm-up
- After user signup/login: Pre-load user data
- After post creation: Cache new post immediately

Strategy 3: Application startup
- ApplicationListener<ContextRefreshedEvent>
- Load critical data on boot
```

### Q14: What Redis eviction policy do you use?

**Answer:**
```
For cache use case: allkeys-lru
- Evicts least recently used keys when memory full
- Works across all keys (not just those with TTL)

Alternative policies:
- volatile-lru: Only evict keys with TTL
- allkeys-lfu: Least frequently used (better for some workloads)
- noeviction: Return errors when full (not recommended)

Set with:
redis-cli CONFIG SET maxmemory-policy allkeys-lru
```

### Q15: How do you monitor cache performance?

**Answer:**
```
Key Metrics:
1. Hit rate: >95% (hits / (hits + misses))
2. Latency: <10ms p99
3. Memory usage: <80% of max
4. Evictions: <100/sec
5. Connection count: <80% of max

Tools:
- Prometheus + Grafana dashboard
- Spring Boot Actuator (/actuator/metrics)
- Redis INFO command
- CloudWatch (if using AWS ElastiCache)
```

### Q16: How do you handle cache invalidation?

**Answer:**
```
Pattern 1: Time-based (TTL)
- Set expiry on write: 5-10 minutes
- Simplest, eventual consistency

Pattern 2: Write-through
- Update cache on every write
- Cache always fresh, higher write latency

Pattern 3: Write-behind
- Write to cache, async update DB
- Lowest latency, risk of data loss

Pattern 4: Event-based
- Publish event on write (Kafka)
- Consumers invalidate cache
- Good for distributed systems
```

### Q17: What's your cache sizing strategy?

**Answer:**
```
Formula:
Cache Size = (Hot Dataset Size) * (Replication Factor) * (Overhead)

Example:
- Hot dataset: 10GB (most accessed 20% of data)
- Replication: 3x (for availability)
- Overhead: 1.2x (Redis metadata)
Total: 10GB * 3 * 1.2 = 36GB

Sizing by hit rate:
- Cache 20% of data → 80% hit rate
- Cache 50% of data → 95% hit rate
- Cache 80% of data → 99% hit rate

Budget: $1,000/month → 50GB Redis cluster
```

### Q18: How do you handle Redis failures?

**Answer:**
```
High Availability Setup:
- Redis Sentinel (auto-failover for master)
- Redis Cluster (sharding + replication)
- AWS ElastiCache (managed, auto-failover)

Failure Handling in Code:
1. Circuit breaker: Stop hitting Redis after 5 failures
2. Fallback to DB: If Redis down, read from DB
3. Retry with exponential backoff: 100ms, 500ms, 1s
4. Cache-aside pattern: App continues if cache unavailable

Monitoring:
- Alert if Redis down (PagerDuty)
- Alert if hit rate drops <80%
```

### Q19: How do you test cache logic?

**Answer:**
```
Unit Tests:
- Mock RedisTemplate
- Test cache hit/miss logic
- Test TTL expiration
- Test mutex lock acquisition

Integration Tests:
- Embedded Redis (testcontainers)
- Test cache stampede prevention
- Test cache invalidation
- Test failover scenarios

Load Tests:
- Gatling/JMeter: 10K req/sec
- Monitor hit rate, latency
- Test hot key scenarios
- Test memory limits (eviction)
```

### Q20: What's the difference between Redis Cluster and Sentinel?

**Answer:**
```
Redis Sentinel:
- High availability (auto-failover)
- Single master, multiple replicas
- No sharding (all data on master)
- Good for: <50GB data, HA required

Redis Cluster:
- Sharding + High availability
- Data split across multiple masters
- Each master has replicas
- Good for: >50GB data, need horizontal scaling

When to use:
- <50GB, HA: Use Sentinel
- >50GB, scale: Use Cluster
- AWS: Use ElastiCache (managed)
```

---

## 🎯 The Perfect 2-Minute Interview Answer

> **Interviewer:** "How do you implement distributed caching at scale?"

**Your Answer:**

"I'll design a distributed cache using **Redis Cluster** with **multi-level caching** and **cache stampede protection**.

**Architecture:**

**L1 Cache (Local)**: Caffeine in-memory
- 1-minute TTL, 1000 keys max
- <0.1ms latency
- 99%+ hit rate for hot keys

**L2 Cache (Distributed)**: Redis Cluster
- 6 nodes (3 masters + 3 replicas)
- 10-minute TTL
- 1-5ms latency
- Consistent hashing for sharding

**Key Patterns:**

**Cache Stampede Protection**: Mutex lock (SETNX)
- Only 1 request loads from DB on cache miss
- Others wait and read from cache

**Hot Key Handling**: Key sharding + Local cache
- post:123:shard:0 through post:123:shard:9
- L1 cache absorbs 99% of hot key traffic

**Cache Warming**: Scheduled job every 5 minutes
- Pre-load trending posts (top 1000)
- Pre-load user data after login

**Monitoring**:
- Hit rate: >95% (alert if <90%)
- Latency p99: <10ms
- Memory usage: <80%
- Evictions: <100/sec

**Failure Handling**:
- Circuit breaker if Redis down
- Fallback to DB
- Retry with exponential backoff

**Redis Config**:
- Eviction policy: allkeys-lru
- Persistence: AOF + RDB snapshots
- Maxmemory: 80% of RAM

**Trade-offs:**
- Eventual consistency (10-min TTL)
- Memory cost (~$500/month for 50GB cluster)
- Complexity (L1 + L2 invalidation)

This design handles 100K requests/sec with <10ms latency and 95%+ hit rate."

---

**Last Updated**: March 2026
**Status**: ✅ Production Ready
**For**: 10+ Years Experienced Developer
