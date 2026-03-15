# Instagram Likes Feature - Production Scale System Design

> **Target**: 10+ Years Experienced Developer
> **Updated**: March 2026
> **Interview Ready**: Complete guide with ASCII diagrams

---

## 📊 Problem Statement

Design a **likes feature** for Instagram that handles:
- **500 million daily active users**
- **95 million posts per day**
- **4.2 billion likes per day** (~49,000 likes/second)
- **Peak traffic**: 150,000 likes/second (during major events)
- **Read-heavy**: 100:1 read-to-write ratio
- **Real-time updates**: Users see like count instantly
- **Consistency**: User can't like same post twice
- **Performance**: <100ms response time for like/unlike

---

## 🎯 Functional Requirements

### Core Features
1. **Like a post** - User clicks heart icon
2. **Unlike a post** - User clicks again to remove like
3. **Get like count** - Display total likes on post
4. **Check if user liked** - Show filled/unfilled heart
5. **Get list of likers** - Show "Liked by user1, user2, and 1,234 others"
6. **Prevent double-likes** - Idempotent operations

### Non-Functional Requirements
1. **High Availability** - 99.99% uptime
2. **Low Latency** - <100ms p99 response time
3. **Horizontal Scalability** - Handle traffic spikes
4. **Eventual Consistency** - Acceptable for like counts
5. **Data Durability** - Never lose likes
6. **Real-time Updates** - Users see changes immediately

---

## 🤔 Clarifying Questions (Interview Warm-up)

### Must Ask in Interview:
1. **Scale**: How many users? How many posts? How many likes per second?
2. **Consistency**: Is eventual consistency acceptable for like counts?
3. **Real-time**: Do users need to see updates instantly?
4. **Durability**: Can we afford to lose some likes during failures?
5. **Read/Write Ratio**: Are reads or writes more common?
6. **Analytics**: Do we need analytics (trending posts, like patterns)?
7. **Notification**: Do post owners get notified on every like?

---

## 📐 Back-of-the-Envelope Calculations

### Traffic Estimates
```
Daily Active Users (DAU):        500 million
Posts per day:                    95 million
Likes per day:                     4.2 billion
Average likes per second:          49,000 likes/s
Peak likes per second:            150,000 likes/s

Read-to-Write Ratio:              100:1
Read QPS:                          4.9 million reads/s
Write QPS:                         49,000 writes/s
Peak Write QPS:                   150,000 writes/s
```

### Storage Estimates
```
Like Record Size:
- user_id (8 bytes)
- post_id (8 bytes)
- created_at (8 bytes)
- Total: 24 bytes per like

Daily Storage:
4.2 billion likes × 24 bytes = 100.8 GB/day

Annual Storage:
100.8 GB × 365 = 36.8 TB/year

5-Year Storage:
36.8 TB × 5 = 184 TB
```

### Database Estimates
```
Likes Table:
- 4.2B records per day
- 1.5 trillion records per year
- Needs sharding from day 1

Cache Requirements:
- Cache hot posts (top 1% = 950K posts)
- Average 100 likes per cached post
- 950K × 100 × 24 bytes = 2.28 GB
- Add metadata: ~5 GB cache needed
```

---

## 🏗️ High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────────────┐
│                    INSTAGRAM LIKES SYSTEM ARCHITECTURE                  │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  ┌──────────────┐                                                       │
│  │   Mobile     │                                                       │
│  │     App      │                                                       │
│  └──────┬───────┘                                                       │
│         │                                                               │
│         │ HTTPS (POST /posts/{id}/like)                                │
│         ▼                                                               │
│  ┌──────────────────────────────────────────────────────┐              │
│  │              API Gateway / Load Balancer              │              │
│  │  • Rate limiting (10 likes/sec per user)             │              │
│  │  • Authentication (JWT validation)                   │              │
│  │  • Request routing                                   │              │
│  └──────────────────┬───────────────────────────────────┘              │
│                     │                                                   │
│         ┌───────────┴────────────┬──────────────┐                      │
│         ▼                        ▼              ▼                      │
│  ┌─────────────┐         ┌─────────────┐  ┌─────────────┐             │
│  │   Likes     │         │   Likes     │  │   Likes     │             │
│  │  Service 1  │         │  Service 2  │  │  Service N  │             │
│  │             │         │             │  │             │             │
│  │ • Like/     │         │ • Like/     │  │ • Like/     │             │
│  │   Unlike    │         │   Unlike    │  │   Unlike    │             │
│  │ • Get Count │         │ • Get Count │  │ • Get Count │             │
│  │ • Check     │         │ • Check     │  │ • Check     │             │
│  │   Status    │         │   Status    │  │   Status    │             │
│  └──────┬──────┘         └──────┬──────┘  └──────┬──────┘             │
│         │                       │                │                     │
│         │                       │                │                     │
│         └───────────┬───────────┴────────────────┘                     │
│                     │                                                   │
│         ┌───────────┼───────────────┬───────────────┐                  │
│         ▼           ▼               ▼               ▼                  │
│  ┌──────────┐ ┌──────────┐  ┌──────────────┐ ┌──────────────┐        │
│  │  Redis   │ │  Redis   │  │   Message    │ │   Database   │        │
│  │  Cache   │ │  Cache   │  │    Queue     │ │   (Sharded)  │        │
│  │ Cluster  │ │ Cluster  │  │   (Kafka)    │ │              │        │
│  │          │ │          │  │              │ │ • Likes      │        │
│  │ • Like   │ │ • Post   │  │ • Async      │ │   Table      │        │
│  │   Status │ │   Count  │  │   Count      │ │ • Counts     │        │
│  │   Cache  │ │   Cache  │  │   Update     │ │   Table      │        │
│  │          │ │          │  │ • Notif      │ │              │        │
│  │ TTL: 1hr │ │ TTL: 5m  │  │   Events     │ │ Cassandra/   │        │
│  └──────────┘ └──────────┘  └──────┬───────┘ │ ScyllaDB     │        │
│                                     │         └──────────────┘        │
│                                     │                                  │
│                                     ▼                                  │
│                              ┌──────────────┐                          │
│                              │   Counter    │                          │
│                              │  Aggregator  │                          │
│                              │   Service    │                          │
│                              │              │                          │
│                              │ • Batch      │                          │
│                              │   Count      │                          │
│                              │   Updates    │                          │
│                              └──────────────┘                          │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## 🗄️ Database Schema Design

### Approach 1: Relational Database (PostgreSQL/MySQL)

```sql
-- Likes table (write-heavy, needs sharding)
CREATE TABLE likes (
    user_id BIGINT NOT NULL,           -- User who liked
    post_id BIGINT NOT NULL,           -- Post that was liked
    created_at TIMESTAMP DEFAULT NOW(),
    PRIMARY KEY (user_id, post_id),    -- Composite key prevents duplicates
    INDEX idx_post_id (post_id),       -- For counting likes per post
    INDEX idx_created_at (created_at)  -- For recent likes query
) PARTITION BY HASH(post_id);          -- Shard by post_id

-- Like counts table (denormalized for fast reads)
CREATE TABLE post_like_counts (
    post_id BIGINT PRIMARY KEY,
    like_count BIGINT DEFAULT 0,
    last_updated TIMESTAMP DEFAULT NOW(),
    INDEX idx_like_count (like_count)  -- For trending posts
) PARTITION BY HASH(post_id);
```

**Pros:**
- ✅ Strong consistency
- ✅ ACID guarantees
- ✅ No duplicate likes (unique constraint)

**Cons:**
- ❌ Scaling challenges at Instagram scale
- ❌ Hot partition problem (viral posts)
- ❌ High write contention

---

### Approach 2: NoSQL Database (Cassandra/ScyllaDB) ⭐ RECOMMENDED

```sql
-- Likes by post (optimized for: "Get all users who liked post X")
CREATE TABLE likes_by_post (
    post_id BIGINT,                    -- Partition key
    user_id BIGINT,                    -- Clustering key
    created_at TIMESTAMP,
    PRIMARY KEY (post_id, user_id)
) WITH CLUSTERING ORDER BY (user_id ASC);

-- Likes by user (optimized for: "Did user X like post Y?")
CREATE TABLE likes_by_user (
    user_id BIGINT,                    -- Partition key
    post_id BIGINT,                    -- Clustering key
    created_at TIMESTAMP,
    PRIMARY KEY (user_id, post_id)
) WITH CLUSTERING ORDER BY (post_id DESC);

-- Like counts (denormalized counter)
CREATE TABLE post_like_counts (
    post_id BIGINT PRIMARY KEY,
    like_count COUNTER,                -- Cassandra counter type
    last_updated TIMESTAMP
);
```

**Why Cassandra?**
- ✅ Horizontal scaling (add nodes easily)
- ✅ Write-optimized (append-only log structure)
- ✅ No hot partition (consistent hashing)
- ✅ High availability (replication factor 3)
- ✅ Eventually consistent (acceptable for likes)

**Trade-offs:**
- ❌ Eventual consistency (like count may lag)
- ❌ No ACID transactions
- ❌ Requires duplicate data (2 tables)

---

## 🔄 API Design

### 1. Like a Post
```http
POST /api/v1/posts/{post_id}/like
Authorization: Bearer {jwt_token}

Response 200 OK:
{
  "success": true,
  "post_id": 12345,
  "like_count": 1547,
  "liked_by_user": true,
  "timestamp": "2026-03-15T10:30:00Z"
}
```

### 2. Unlike a Post
```http
DELETE /api/v1/posts/{post_id}/like
Authorization: Bearer {jwt_token}

Response 200 OK:
{
  "success": true,
  "post_id": 12345,
  "like_count": 1546,
  "liked_by_user": false,
  "timestamp": "2026-03-15T10:31:00Z"
}
```

### 3. Get Like Count
```http
GET /api/v1/posts/{post_id}/likes/count

Response 200 OK:
{
  "post_id": 12345,
  "like_count": 1547,
  "cached": true,
  "last_updated": "2026-03-15T10:30:00Z"
}
```

### 4. Check if User Liked Post
```http
GET /api/v1/posts/{post_id}/likes/status
Authorization: Bearer {jwt_token}

Response 200 OK:
{
  "post_id": 12345,
  "liked_by_user": true,
  "liked_at": "2026-03-15T10:30:00Z"
}
```

### 5. Get List of Likers
```http
GET /api/v1/posts/{post_id}/likes?limit=20&offset=0

Response 200 OK:
{
  "post_id": 12345,
  "total_likes": 1547,
  "likers": [
    {"user_id": 101, "username": "alice", "avatar": "..."},
    {"user_id": 102, "username": "bob", "avatar": "..."}
  ],
  "has_more": true
}
```

---

## 🚀 Implementation Approaches

### Approach A: Write-Through Cache (Simple)

```
User clicks Like
    ↓
1. Write to DB (Cassandra)
2. Update cache (Redis)
3. Return response
```

```java
@Service
public class LikeServiceWriteThrough {

    @Autowired
    private CassandraTemplate cassandraTemplate;

    @Autowired
    private RedisTemplate<String, String> redisTemplate;

    @Autowired
    private KafkaTemplate<String, LikeEvent> kafkaTemplate;

    public LikeResponse likePost(Long userId, Long postId) {
        // 1. Check if already liked (Redis cache first)
        String cacheKey = "like:" + userId + ":" + postId;
        Boolean alreadyLiked = redisTemplate.hasKey(cacheKey);

        if (Boolean.TRUE.equals(alreadyLiked)) {
            return LikeResponse.alreadyLiked();
        }

        // 2. Write to database (Cassandra)
        Like like = new Like(userId, postId, Instant.now());

        try {
            // Insert into likes_by_post
            cassandraTemplate.insert(like);

            // Insert into likes_by_user
            cassandraTemplate.insert(like.copyForUserPartition());

            // 3. Update cache (like status)
            redisTemplate.opsForValue().set(cacheKey, "1", 1, TimeUnit.HOURS);

            // 4. Increment count in cache (if exists)
            String countKey = "post:count:" + postId;
            redisTemplate.opsForValue().increment(countKey);

            // 5. Publish event for async processing
            LikeEvent event = new LikeEvent(userId, postId, "LIKE");
            kafkaTemplate.send("likes-events", event);

            // 6. Return response
            Long likeCount = getLikeCount(postId);
            return LikeResponse.success(postId, likeCount, true);

        } catch (Exception e) {
            // Rollback cache on failure
            redisTemplate.delete(cacheKey);
            throw new LikeException("Failed to like post", e);
        }
    }

    private Long getLikeCount(Long postId) {
        String countKey = "post:count:" + postId;
        String cached = redisTemplate.opsForValue().get(countKey);

        if (cached != null) {
            return Long.parseLong(cached);
        }

        // Cache miss: query database and cache result
        Long count = cassandraTemplate.selectOne(
            "SELECT count(*) FROM likes_by_post WHERE post_id = ?",
            Long.class,
            postId
        );

        redisTemplate.opsForValue().set(countKey, count.toString(), 5, TimeUnit.MINUTES);
        return count;
    }
}
```

**Pros:**
- ✅ Simple to implement
- ✅ Cache always consistent with DB

**Cons:**
- ❌ Higher latency (wait for DB write)
- ❌ Cache becomes bottleneck
- ❌ DB write on critical path

---

### Approach B: Write-Behind Cache (Async) ⭐ RECOMMENDED

```
User clicks Like
    ↓
1. Write to Redis immediately
2. Return response (fast!)
3. Async worker writes to DB
```

```java
@Service
public class LikeServiceWriteBehind {

    @Autowired
    private RedisTemplate<String, String> redisTemplate;

    @Autowired
    private KafkaTemplate<String, LikeEvent> kafkaTemplate;

    public LikeResponse likePost(Long userId, Long postId) {
        String cacheKey = "like:" + userId + ":" + postId;

        // 1. Check if already liked (Redis SETNX - atomic operation)
        Boolean success = redisTemplate.opsForValue()
            .setIfAbsent(cacheKey, "1", 1, TimeUnit.HOURS);

        if (Boolean.FALSE.equals(success)) {
            return LikeResponse.alreadyLiked();
        }

        // 2. Increment count in Redis (atomic)
        String countKey = "post:count:" + postId;
        Long newCount = redisTemplate.opsForValue().increment(countKey);

        // 3. Publish event to Kafka (async DB write)
        LikeEvent event = new LikeEvent(userId, postId, "LIKE", Instant.now());
        kafkaTemplate.send("likes-events", event);

        // 4. Return immediately (no DB wait!)
        return LikeResponse.success(postId, newCount, true);
    }

    public LikeResponse unlikePost(Long userId, Long postId) {
        String cacheKey = "like:" + userId + ":" + postId;

        // 1. Delete from Redis
        Boolean deleted = redisTemplate.delete(cacheKey);

        if (Boolean.FALSE.equals(deleted)) {
            return LikeResponse.notLiked();
        }

        // 2. Decrement count
        String countKey = "post:count:" + postId;
        Long newCount = redisTemplate.opsForValue().decrement(countKey);

        // 3. Publish event
        LikeEvent event = new LikeEvent(userId, postId, "UNLIKE", Instant.now());
        kafkaTemplate.send("likes-events", event);

        return LikeResponse.success(postId, newCount, false);
    }
}
```

**Kafka Consumer (Async DB Writer):**

```java
@Service
public class LikeEventConsumer {

    @Autowired
    private CassandraTemplate cassandraTemplate;

    @KafkaListener(topics = "likes-events", groupId = "likes-writer")
    public void consumeLikeEvent(LikeEvent event) {
        try {
            if ("LIKE".equals(event.getAction())) {
                // Write to Cassandra
                Like like = new Like(event.getUserId(), event.getPostId(), event.getTimestamp());
                cassandraTemplate.insert(like);
                cassandraTemplate.insert(like.copyForUserPartition());

                // Update counter table
                cassandraTemplate.execute(
                    "UPDATE post_like_counts SET like_count = like_count + 1 WHERE post_id = ?",
                    event.getPostId()
                );

            } else if ("UNLIKE".equals(event.getAction())) {
                cassandraTemplate.delete(
                    "DELETE FROM likes_by_post WHERE post_id = ? AND user_id = ?",
                    event.getPostId(),
                    event.getUserId()
                );
                cassandraTemplate.delete(
                    "DELETE FROM likes_by_user WHERE user_id = ? AND post_id = ?",
                    event.getUserId(),
                    event.getPostId()
                );

                cassandraTemplate.execute(
                    "UPDATE post_like_counts SET like_count = like_count - 1 WHERE post_id = ?",
                    event.getPostId()
                );
            }

        } catch (Exception e) {
            // Retry or DLQ
            log.error("Failed to process like event", e);
        }
    }
}
```

**Pros:**
- ✅ **Very fast response** (<10ms)
- ✅ DB not on critical path
- ✅ Can batch writes for efficiency
- ✅ Redis provides atomicity (SETNX)

**Cons:**
- ❌ Risk of data loss (if Redis fails)
- ❌ Eventual consistency
- ❌ Need reconciliation job

---

### Approach C: Hybrid (Read from Cache, Write to Both)

```
Read Flow:
1. Check Redis cache
2. If miss, read from DB and cache

Write Flow:
1. Write to Redis (fast response)
2. Write to DB synchronously (durability)
3. If DB fails, rollback Redis
```

```java
@Service
public class LikeServiceHybrid {

    @Autowired
    private RedisTemplate<String, String> redisTemplate;

    @Autowired
    private CassandraTemplate cassandraTemplate;

    @Transactional
    public LikeResponse likePost(Long userId, Long postId) {
        String cacheKey = "like:" + userId + ":" + postId;

        // 1. Check Redis first (fast)
        Boolean alreadyInCache = redisTemplate.hasKey(cacheKey);
        if (Boolean.TRUE.equals(alreadyInCache)) {
            return LikeResponse.alreadyLiked();
        }

        try {
            // 2. Write to DB (durability)
            Like like = new Like(userId, postId, Instant.now());
            cassandraTemplate.insert(like);
            cassandraTemplate.insert(like.copyForUserPartition());

            // 3. Write to Redis (cache)
            redisTemplate.opsForValue().set(cacheKey, "1", 1, TimeUnit.HOURS);

            // 4. Update count
            String countKey = "post:count:" + postId;
            redisTemplate.opsForValue().increment(countKey);

            Long likeCount = getLikeCount(postId);
            return LikeResponse.success(postId, likeCount, true);

        } catch (Exception e) {
            // Rollback Redis on DB failure
            redisTemplate.delete(cacheKey);
            throw new LikeException("Failed to like post", e);
        }
    }
}
```

**Pros:**
- ✅ Balance of speed and durability
- ✅ Cache failure doesn't lose data
- ✅ DB failure prevents inconsistency

**Cons:**
- ❌ Higher latency than write-behind
- ❌ DB still on critical path

---

## 🎨 Detailed Component Architecture

### 1. Redis Cache Layer

```
┌─────────────────────────────────────────────────────────────┐
│                  REDIS CACHE ARCHITECTURE                   │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  Cache Strategy 1: Like Status (Did User X like Post Y?)   │
│  ┌───────────────────────────────────────────────────────┐ │
│  │  Key Pattern: "like:{user_id}:{post_id}"              │ │
│  │  Value: "1" (existence means liked)                   │ │
│  │  TTL: 1 hour                                           │ │
│  │  Data Structure: String                                │ │
│  │                                                         │ │
│  │  Example:                                              │ │
│  │    like:101:12345 = "1"  (user 101 liked post 12345)  │ │
│  └───────────────────────────────────────────────────────┘ │
│                                                             │
│  Cache Strategy 2: Like Count (Total likes per post)       │
│  ┌───────────────────────────────────────────────────────┐ │
│  │  Key Pattern: "post:count:{post_id}"                  │ │
│  │  Value: Counter (integer)                             │ │
│  │  TTL: 5 minutes                                        │ │
│  │  Data Structure: String (INCR/DECR operations)        │ │
│  │                                                         │ │
│  │  Example:                                              │ │
│  │    post:count:12345 = "1547"                          │ │
│  └───────────────────────────────────────────────────────┘ │
│                                                             │
│  Cache Strategy 3: Recent Likers (First 100 likers)        │
│  ┌───────────────────────────────────────────────────────┐ │
│  │  Key Pattern: "post:likers:{post_id}"                 │ │
│  │  Value: List of user IDs                              │ │
│  │  TTL: 10 minutes                                       │ │
│  │  Data Structure: Redis List (LPUSH/LRANGE)            │ │
│  │                                                         │ │
│  │  Example:                                              │ │
│  │    post:likers:12345 = [101, 102, 103, ...]          │ │
│  │    (stores first 100, rest from DB)                   │ │
│  └───────────────────────────────────────────────────────┘ │
│                                                             │
│  Operations:                                               │
│  • SETNX for atomic like (prevent duplicates)             │
│  • INCR/DECR for atomic count updates                     │
│  • LPUSH for adding recent likers                         │
│  • Multi-key operations with Redis Pipeline               │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

### 2. Database Sharding Strategy

```
┌─────────────────────────────────────────────────────────────┐
│              DATABASE SHARDING FOR LIKES TABLE              │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  Shard Key: post_id (consistent hashing)                   │
│                                                             │
│         post_id hash % 16 = Shard Number                    │
│                                                             │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  Request: Like post 12345                            │  │
│  │           User 101 likes post 12345                  │  │
│  └──────────────────┬───────────────────────────────────┘  │
│                     │                                       │
│                     ▼                                       │
│         Hash(12345) % 16 = Shard 5                          │
│                     │                                       │
│        ┌────────────┴────────────┬─────────────┐           │
│        ▼                         ▼             ▼           │
│  ┌──────────┐             ┌──────────┐   ┌──────────┐     │
│  │ Shard 0  │             │ Shard 5  │   │ Shard 15 │     │
│  │          │             │          │   │          │     │
│  │ Posts    │             │ Posts    │   │ Posts    │     │
│  │ 0, 16,   │    ...      │ 5, 21,   │   │ 15, 31,  │     │
│  │ 32...    │             │ 37...    │   │ 47...    │     │
│  │          │             │          │   │          │     │
│  │ Cassandra│             │ Cassandra│   │ Cassandra│     │
│  │ Node     │             │ Node     │   │ Node     │     │
│  └──────────┘             └──────────┘   └──────────┘     │
│                                                             │
│  Replication Factor: 3 (each shard replicated 3x)          │
│  Consistency Level: QUORUM (2 out of 3 must ack)           │
│                                                             │
│  Hot Partition Mitigation:                                 │
│  • Viral posts cached heavily in Redis                     │
│  • Use Redis for real-time counts                          │
│  • DB only for durability, not real-time reads             │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

### 3. Message Queue Architecture (Kafka)

```
┌─────────────────────────────────────────────────────────────┐
│                KAFKA MESSAGE QUEUE ARCHITECTURE             │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  Topic: likes-events                                        │
│  Partitions: 16 (matches DB shards)                         │
│  Replication Factor: 3                                      │
│  Retention: 7 days                                          │
│                                                             │
│  ┌───────────────────────────────────────────────────────┐ │
│  │  Likes Service (Producer)                             │ │
│  │  • Publishes LikeEvent to Kafka                       │ │
│  │  • Partition by post_id (same as DB shard)            │ │
│  └──────────────────┬────────────────────────────────────┘ │
│                     │                                       │
│                     ▼                                       │
│  ┌───────────────────────────────────────────────────────┐ │
│  │  Kafka Topic: likes-events                            │ │
│  │  ┌──────────┐ ┌──────────┐ ┌──────────┐             │ │
│  │  │Partition │ │Partition │ │Partition │   ...       │ │
│  │  │    0     │ │    1     │ │    15    │             │ │
│  │  └──────────┘ └──────────┘ └──────────┘             │ │
│  │                                                       │ │
│  │  Event Schema:                                        │ │
│  │  {                                                    │ │
│  │    "user_id": 101,                                    │ │
│  │    "post_id": 12345,                                  │ │
│  │    "action": "LIKE" | "UNLIKE",                       │ │
│  │    "timestamp": "2026-03-15T10:30:00Z"                │ │
│  │  }                                                    │ │
│  └──────────────────┬────────────────────────────────────┘ │
│                     │                                       │
│         ┌───────────┼────────────┬──────────────┐          │
│         ▼           ▼            ▼              ▼          │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐     │
│  │Consumer  │ │Consumer  │ │Consumer  │ │Consumer  │     │
│  │ Group 1  │ │ Group 2  │ │ Group 3  │ │ Group 4  │     │
│  │          │ │          │ │          │ │          │     │
│  │DB Writer │ │Counter   │ │Notif     │ │Analytics │     │
│  │Service   │ │Aggregator│ │Service   │ │Service   │     │
│  │          │ │          │ │          │ │          │     │
│  │Writes to │ │Updates   │ │Sends push│ │Tracks    │     │
│  │Cassandra │ │counts in │ │notif to  │ │trending  │     │
│  │          │ │batch     │ │post owner│ │posts     │     │
│  └──────────┘ └──────────┘ └──────────┘ └──────────┘     │
│                                                             │
│  Benefits:                                                 │
│  • Decouples services (loose coupling)                     │
│  • Async processing (fast API response)                    │
│  • Multiple consumers for different tasks                  │
│  • Replay events for recovery                              │
│  • Ordered processing per partition                        │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## ⚠️ Edge Cases & Failure Scenarios

### 1. Double-Like Prevention

**Problem**: User rapidly clicks like button multiple times

**Solution**:
```java
// Use Redis SETNX (atomic SET if Not eXists)
Boolean success = redisTemplate.opsForValue()
    .setIfAbsent("like:" + userId + ":" + postId, "1", 1, TimeUnit.HOURS);

if (Boolean.FALSE.equals(success)) {
    return "Already liked";
}
```

### 2. Redis Failure Scenario

**Problem**: Redis cluster goes down

**Solution**:
```java
public LikeResponse likePost(Long userId, Long postId) {
    try {
        // Try Redis first
        return likeWithCache(userId, postId);
    } catch (RedisConnectionException e) {
        // Fallback to direct DB write
        log.warn("Redis unavailable, falling back to DB");
        return likeWithoutCache(userId, postId);
    }
}
```

### 3. Kafka Lag / Consumer Slowness

**Problem**: Kafka consumers fall behind, like counts in DB are stale

**Solution**:
- **Scale consumers**: Add more consumer instances
- **Batch writes**: Group 100 likes into single batch write
- **Monitoring**: Alert if lag > 10,000 messages
- **Eventual consistency**: Accept stale counts for non-critical features

### 4. Hot Partition (Viral Post)

**Problem**: Celebrity post gets 1M likes in 1 hour, overloading single shard

**Solution**:
```java
// Cache hot posts aggressively
String countKey = "post:count:" + postId;

// Use Redis for ALL reads (don't touch DB)
Long count = redisTemplate.opsForValue().increment(countKey);

// Batch DB writes every 1000 likes
if (count % 1000 == 0) {
    kafkaTemplate.send("likes-batch-update", new BatchUpdate(postId, 1000));
}
```

### 5. Like Count Drift (Cache vs DB Mismatch)

**Problem**: Redis shows 1547 likes, DB shows 1545 likes

**Solution**:
```java
@Scheduled(fixedRate = 3600000) // Every 1 hour
public void reconcileCounts() {
    // Get all cached post counts
    Set<String> keys = redisTemplate.keys("post:count:*");

    for (String key : keys) {
        Long postId = extractPostId(key);
        Long cachedCount = Long.parseLong(redisTemplate.opsForValue().get(key));

        // Query actual count from DB
        Long dbCount = cassandraTemplate.selectOne(
            "SELECT COUNT(*) FROM likes_by_post WHERE post_id = ?",
            Long.class,
            postId
        );

        // If drift > 5%, update cache to DB value
        if (Math.abs(cachedCount - dbCount) > dbCount * 0.05) {
            log.warn("Count drift detected for post {}: cache={}, db={}",
                     postId, cachedCount, dbCount);
            redisTemplate.opsForValue().set(key, dbCount.toString());
        }
    }
}
```

### 6. User Deletes Account

**Problem**: User deletes account, need to remove all their likes

**Solution**:
```java
// Query likes_by_user partition
List<Like> userLikes = cassandraTemplate.select(
    "SELECT * FROM likes_by_user WHERE user_id = ?",
    Like.class,
    userId
);

// Async deletion via Kafka
for (Like like : userLikes) {
    kafkaTemplate.send("likes-events",
        new LikeEvent(userId, like.getPostId(), "DELETE"));
}
```

---

## 📊 Monitoring & Metrics

### Key Metrics to Track

```yaml
Latency Metrics:
  - like_api_latency_p50: 20ms
  - like_api_latency_p99: 100ms
  - unlike_api_latency_p50: 15ms
  - unlike_api_latency_p99: 80ms
  - get_count_latency_p99: 10ms

Throughput Metrics:
  - likes_per_second: 49,000 (avg), 150,000 (peak)
  - unlikes_per_second: 5,000 (avg)
  - get_count_per_second: 4.9 million

Error Metrics:
  - like_api_error_rate: <0.1%
  - duplicate_like_attempts: ~2% (expected)
  - redis_failures_per_minute: <10

Cache Metrics:
  - like_status_cache_hit_rate: >95%
  - like_count_cache_hit_rate: >98%
  - redis_memory_usage: <80%
  - redis_evictions_per_second: <100

Database Metrics:
  - cassandra_write_latency_p99: 50ms
  - cassandra_read_latency_p99: 30ms
  - cassandra_disk_usage: <70% per node

Message Queue Metrics:
  - kafka_consumer_lag: <10,000 messages
  - kafka_throughput: 50,000 events/sec
  - failed_event_processing: <0.01%
```

### Alerts to Configure

```yaml
Critical Alerts:
  - Like API error rate > 1% for 5 minutes
  - Redis cluster down
  - Cassandra node down
  - Kafka consumer lag > 100,000

Warning Alerts:
  - Like API p99 latency > 200ms
  - Cache hit rate < 90%
  - Kafka consumer lag > 10,000
  - Count drift > 5% for top posts
```

---

## 🔒 Security Considerations

### 1. Rate Limiting
```java
@RateLimiter(name = "likePost", fallbackMethod = "rateLimitFallback")
public LikeResponse likePost(Long userId, Long postId) {
    // Max 10 likes per second per user
}
```

### 2. Bot Detection
```java
// Detect suspicious patterns
if (likesInLastMinute(userId) > 60) {
    log.warn("Possible bot detected: user {}", userId);
    return LikeResponse.rateLimited();
}
```

### 3. Authentication
```java
@PreAuthorize("isAuthenticated()")
public LikeResponse likePost(Long userId, Long postId) {
    // Verify JWT token
    // Verify userId matches token
}
```

---

## 🎯 Trade-offs & Design Decisions

| Decision | Choice | Reason |
|----------|--------|--------|
| **Database** | Cassandra over MySQL | Better write scalability, no hot partition issues |
| **Consistency** | Eventual over Strong | Like counts can be slightly stale for better performance |
| **Cache Strategy** | Write-behind over Write-through | Faster response time (<10ms vs 50ms) |
| **Sharding Key** | post_id over user_id | Read pattern: "Show likes for post X" |
| **Message Queue** | Kafka over RabbitMQ | Better throughput, replay capability |
| **Counter Storage** | Redis over DB | Atomic operations, sub-millisecond latency |

---

## 📋 Interview Q&A

### Q1: How do you handle 150,000 likes per second during peak?

**Answer:**
```
1. Redis handles writes (in-memory, <1ms)
2. Kafka buffers events (millions of events)
3. Consumers batch writes to DB (1000 likes/batch)
4. Horizontal scaling: Add more Redis nodes + Kafka partitions
5. Hot posts cached heavily (never hit DB for reads)
```

### Q2: What if Redis goes down?

**Answer:**
```
1. Circuit breaker detects Redis failure
2. Fall back to direct DB writes (slower but works)
3. Accept higher latency temporarily (50ms vs 10ms)
4. Cache warming job rebuilds cache when Redis recovers
5. No data loss (Kafka has events for recovery)
```

### Q3: How do you prevent users from liking same post twice?

**Answer:**
```
1. Redis SETNX (atomic SET if Not eXists)
   - Returns false if key already exists
2. Composite primary key in DB (user_id, post_id)
   - Prevents duplicate rows
3. Idempotent API: Multiple calls = same result
```

### Q4: How do you handle count drift between cache and DB?

**Answer:**
```
1. Accept eventual consistency (counts can lag 1-5 seconds)
2. Reconciliation job runs hourly
3. If drift > 5%, update cache from DB
4. For critical posts (homepage feed), force DB read
5. Cache TTL of 5 minutes prevents infinite staleness
```

### Q5: How would you optimize for a viral post with 10M likes?

**Answer:**
```
1. Cache count in Redis with no TTL (permanent)
2. Batch DB writes (every 10,000 likes)
3. Use Redis HyperLogLog for approximate count
4. Rate limit individual users (10 likes/sec)
5. Add read replicas for DB if needed
6. Pre-aggregate counts (e.g., show "10M+" instead of exact)
```

### Q6: How do you scale reads vs writes?

**Answer:**
```
Reads (4.9M QPS):
- Redis cache (100:1 read/write ratio)
- Read replicas in Cassandra
- CDN for static like counts

Writes (49K QPS):
- Redis handles all writes in-memory
- Kafka buffers for DB persistence
- Cassandra scales horizontally (add nodes)
```

### Q7: What metrics would you monitor in production?

**Answer:**
```
1. API latency (p50, p99, p999)
2. Error rate (4xx, 5xx)
3. Cache hit rate (>95%)
4. Kafka consumer lag (<10K messages)
5. DB write latency (<50ms p99)
6. Redis memory usage (<80%)
7. Count drift percentage
```

### Q8: How do you test this system?

**Answer:**
```
1. Unit tests: Like/unlike logic with mocks
2. Integration tests: Redis + DB + Kafka locally
3. Load tests: Simulate 150K likes/sec (Gatling)
4. Chaos tests: Kill Redis, Kafka, DB nodes
5. Shadow testing: Dual-write to old + new system
6. Canary deployment: 1% traffic → 10% → 100%
```

---

## 🚀 The Perfect 2-Minute Interview Answer

> **Interviewer:** "Design Instagram's likes feature for production scale."

**Your Answer:**

"Instagram handles **4.2 billion likes per day**, which is about **49,000 likes per second** on average, with peaks of **150,000 likes/sec**.

The system has three layers:

**1. API Layer**
- Likes Service handles POST /like, DELETE /unlike, GET /count
- Rate limiting: 10 likes/sec per user
- Authentication via JWT

**2. Cache Layer (Redis)**
- Write-behind pattern for fast writes (<10ms)
- Key `like:user:post` for status (TTL 1hr)
- Key `post:count:123` for counts (TTL 5min)
- SETNX prevents duplicate likes (atomic operation)

**3. Database Layer (Cassandra)**
- Two tables: `likes_by_post` and `likes_by_user`
- Sharded by `post_id` (16 shards)
- Replication factor 3, quorum writes

**Write Flow:**
1. User clicks like → Write to Redis (immediate response)
2. Publish event to Kafka
3. Async consumer writes to Cassandra

**Trade-offs:**
- Eventual consistency (counts may lag 1-5 seconds)
- Redis failure → Fall back to direct DB writes
- Hot posts cached permanently (no DB reads)

**Scaling:**
- Horizontal: Add Redis nodes, Kafka partitions, Cassandra nodes
- Monitoring: p99 latency <100ms, cache hit rate >95%, Kafka lag <10K

This design handles Instagram's scale with low latency and high availability."

---

## 🎓 Advanced Topics (Staff+ Level)

### 1. Count Approximation (HyperLogLog)

For viral posts with millions of likes, exact counts are expensive:

```java
// Use Redis HyperLogLog for approximate counting
redisTemplate.opsForHyperLogLog().add("post:likers:" + postId, userId);

Long approximateCount = redisTemplate.opsForHyperLogLog()
    .size("post:likers:" + postId);

// Error rate: ~0.81% (acceptable for "10M likes" display)
```

### 2. Multi-Region Deployment

```
US-East:  Primary writes, Redis, Cassandra
EU-West:  Read replicas, local cache
Asia:     Read replicas, local cache

Cross-region sync: Cassandra multi-DC replication
```

### 3. Real-Time Updates (WebSocket)

```java
// Notify users of new likes in real-time
@KafkaListener(topics = "likes-events")
public void broadcastLikeUpdate(LikeEvent event) {
    // Send WebSocket message to post owner
    webSocketService.send(event.getPostOwnerId(),
        new LikeNotification(event.getUserId(), event.getPostId()));
}
```

---

## 📚 References & Further Reading

- **Cassandra Data Modeling**: [DataStax Docs](https://docs.datastax.com/)
- **Redis Best Practices**: [Redis.io](https://redis.io/topics/introduction)
- **Kafka Architecture**: [Confluent Docs](https://docs.confluent.io/)
- **Instagram Engineering Blog**: [engineering.instagram.com](https://engineering.instagram.com/)

---

## ✅ Interview Checklist

Before your interview, make sure you can:

- [ ] Explain the scale (4.2B likes/day, 49K likes/sec)
- [ ] Draw high-level architecture diagram
- [ ] Explain write-behind cache pattern
- [ ] Describe Redis data structures used
- [ ] Explain Cassandra sharding strategy
- [ ] Handle edge cases (duplicate likes, Redis failure)
- [ ] Calculate storage requirements
- [ ] Discuss monitoring metrics
- [ ] Explain trade-offs (eventual consistency)
- [ ] Give the perfect 2-minute answer

---

**Last Updated**: March 2026
**Status**: ✅ Production Ready
**For**: 10+ Years Experienced Developer
