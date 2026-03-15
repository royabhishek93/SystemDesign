# Partitioning vs Sharding - Complete Guide

## What's the Difference?

**Simple Answer:** They're very similar concepts! Both split large datasets into smaller pieces. The main difference is **context and scope**.

```
┌─────────────────────────────────────────────────────────────────────────┐
│                    PARTITIONING vs SHARDING                              │
└─────────────────────────────────────────────────────────────────────────┘

PARTITIONING:
─────────────
Splitting data within a SINGLE database server
Usually for organization and query performance

         ┌──────────────────────────┐
         │   Single Database Server │
         │                          │
         │  ┌────────────────────┐  │
         │  │ Partition 1        │  │
         │  │ (Jan-Mar data)     │  │
         │  └────────────────────┘  │
         │  ┌────────────────────┐  │
         │  │ Partition 2        │  │
         │  │ (Apr-Jun data)     │  │
         │  └────────────────────┘  │
         │  ┌────────────────────┐  │
         │  │ Partition 3        │  │
         │  │ (Jul-Sep data)     │  │
         │  └────────────────────┘  │
         └──────────────────────────┘

✓ Same server
✓ Logical division
✓ Query optimization


SHARDING:
─────────
Splitting data across MULTIPLE database servers
For horizontal scaling and handling massive data

    ┌──────────────┐      ┌──────────────┐      ┌──────────────┐
    │   Shard 1    │      │   Shard 2    │      │   Shard 3    │
    │  Server A    │      │  Server B    │      │  Server C    │
    │              │      │              │      │              │
    │  User 1-1M   │      │ User 1M-2M   │      │ User 2M-3M   │
    └──────────────┘      └──────────────┘      └──────────────┘

✓ Different servers
✓ Physical division
✓ Horizontal scaling


SIMPLE ANALOGY:
───────────────

Partitioning = Organizing one filing cabinet with dividers
  📁 Cabinet 1
  ├─ Drawer A (A-F)
  ├─ Drawer B (G-M)
  └─ Drawer C (N-Z)

Sharding = Using multiple filing cabinets
  📁 Cabinet 1 (A-F)
  📁 Cabinet 2 (G-M)
  📁 Cabinet 3 (N-Z)
```

---

## Deep Dive: Partitioning

**Partitioning** divides a large table into smaller, more manageable pieces called **partitions**, but all partitions remain **on the same database server**.

### Types of Partitioning

```
┌─────────────────────────────────────────────────────────────────────────┐
│                       1. HORIZONTAL PARTITIONING                         │
│                          (Partition by Rows)                             │
└─────────────────────────────────────────────────────────────────────────┘

Original Table: orders (10 million rows)
┌───────────────────────────────────────────────────────────────┐
│ order_id │ user_id │  date      │ amount │ status            │
├───────────────────────────────────────────────────────────────┤
│ 1        │ 101     │ 2024-01-15 │ 100    │ completed         │
│ 2        │ 102     │ 2024-02-20 │ 200    │ completed         │
│ 3        │ 103     │ 2024-03-10 │ 150    │ pending           │
│ ...      │ ...     │ ...        │ ...    │ ...               │
│ 10M      │ 505     │ 2024-12-31 │ 300    │ completed         │
└───────────────────────────────────────────────────────────────┘

After Horizontal Partitioning by Date:
───────────────────────────────────────

Partition 1 (Q1 - Jan to Mar)
┌───────────────────────────────────────────────────────────────┐
│ order_id │ user_id │  date      │ amount │ status            │
├───────────────────────────────────────────────────────────────┤
│ 1        │ 101     │ 2024-01-15 │ 100    │ completed         │
│ 3        │ 103     │ 2024-03-10 │ 150    │ pending           │
│ ...      │ ...     │ ...        │ ...    │ ...               │
└───────────────────────────────────────────────────────────────┘
                          2.5M rows

Partition 2 (Q2 - Apr to Jun)
┌───────────────────────────────────────────────────────────────┐
│ order_id │ user_id │  date      │ amount │ status            │
├───────────────────────────────────────────────────────────────┤
│ 2        │ 102     │ 2024-04-20 │ 200    │ completed         │
│ ...      │ ...     │ ...        │ ...    │ ...               │
└───────────────────────────────────────────────────────────────┘
                          2.5M rows

Partition 3 (Q3 - Jul to Sep)
┌───────────────────────────────────────────────────────────────┐
│ ...                                                           │
└───────────────────────────────────────────────────────────────┘
                          2.5M rows

Partition 4 (Q4 - Oct to Dec)
┌───────────────────────────────────────────────────────────────┐
│ ...                                                           │
└───────────────────────────────────────────────────────────────┘
                          2.5M rows

Benefits:
─────────
✓ Query on Q1 data only scans Partition 1 (faster!)
✓ Can drop old partitions easily (e.g., delete 2020 data)
✓ Index size smaller per partition
✓ Maintenance operations faster (rebuild index on one partition)


┌─────────────────────────────────────────────────────────────────────────┐
│                       2. VERTICAL PARTITIONING                           │
│                        (Partition by Columns)                            │
└─────────────────────────────────────────────────────────────────────────┘

Original Table: users (wide table with many columns)
┌─────────────────────────────────────────────────────────────────────────┐
│ user_id │ name  │ email         │ phone  │ address │ bio      │ photo  │
├─────────────────────────────────────────────────────────────────────────┤
│ 1       │ Alice │ a@example.com │ 555... │ 123 St  │ Long bio │ Binary │
│ 2       │ Bob   │ b@example.com │ 555... │ 456 Ave │ Long bio │ Binary │
└─────────────────────────────────────────────────────────────────────────┘

After Vertical Partitioning:
─────────────────────────────

Table 1: users_basic (frequently accessed)
┌────────────────────────────────────────┐
│ user_id │ name  │ email         │      │
├────────────────────────────────────────┤
│ 1       │ Alice │ a@example.com │      │
│ 2       │ Bob   │ b@example.com │      │
└────────────────────────────────────────┘

Table 2: users_contact (less frequently accessed)
┌────────────────────────────────────────┐
│ user_id │ phone  │ address          │  │
├────────────────────────────────────────┤
│ 1       │ 555... │ 123 St           │  │
│ 2       │ 555... │ 456 Ave          │  │
└────────────────────────────────────────┘

Table 3: users_profile (rarely accessed, large data)
┌────────────────────────────────────────┐
│ user_id │ bio          │ photo (BLOB) │
├────────────────────────────────────────┤
│ 1       │ Long bio...  │ Binary data  │
│ 2       │ Long bio...  │ Binary data  │
└────────────────────────────────────────┘

Benefits:
─────────
✓ Load only needed columns (save I/O)
✓ Frequently accessed data in separate table (better cache hit)
✓ Large BLOBs don't slow down other queries


┌─────────────────────────────────────────────────────────────────────────┐
│                       3. RANGE PARTITIONING                              │
└─────────────────────────────────────────────────────────────────────────┘

Partition by range of values (dates, IDs, amounts)

CREATE TABLE orders (
    order_id INT,
    user_id INT,
    order_date DATE,
    amount DECIMAL
)
PARTITION BY RANGE (order_date) (
    PARTITION p_2024_q1 VALUES LESS THAN ('2024-04-01'),
    PARTITION p_2024_q2 VALUES LESS THAN ('2024-07-01'),
    PARTITION p_2024_q3 VALUES LESS THAN ('2024-10-01'),
    PARTITION p_2024_q4 VALUES LESS THAN ('2025-01-01')
);

Query: SELECT * FROM orders WHERE order_date = '2024-02-15';
       ↓
       Only scans p_2024_q1 partition (Partition Pruning)


┌─────────────────────────────────────────────────────────────────────────┐
│                       4. LIST PARTITIONING                               │
└─────────────────────────────────────────────────────────────────────────┘

Partition by discrete list of values (regions, categories)

CREATE TABLE customers (
    customer_id INT,
    name VARCHAR(100),
    region VARCHAR(50)
)
PARTITION BY LIST (region) (
    PARTITION p_north VALUES IN ('NY', 'MA', 'CT'),
    PARTITION p_south VALUES IN ('TX', 'FL', 'GA'),
    PARTITION p_west VALUES IN ('CA', 'WA', 'OR'),
    PARTITION p_east VALUES IN ('PA', 'NJ', 'MD')
);

Query: SELECT * FROM customers WHERE region = 'CA';
       ↓
       Only scans p_west partition


┌─────────────────────────────────────────────────────────────────────────┐
│                       5. HASH PARTITIONING                               │
└─────────────────────────────────────────────────────────────────────────┘

Partition by hash of a column (even distribution)

CREATE TABLE users (
    user_id INT,
    name VARCHAR(100),
    email VARCHAR(100)
)
PARTITION BY HASH(user_id)
PARTITIONS 4;

Automatically distributes:
  user_id 1, 5, 9, 13... → Partition 0
  user_id 2, 6, 10, 14... → Partition 1
  user_id 3, 7, 11, 15... → Partition 2
  user_id 4, 8, 12, 16... → Partition 3

Benefits:
─────────
✓ Even distribution (no hot spots)
✓ Good for data without natural ranges
✗ Cannot do partition pruning easily (must scan all partitions)
```

### Partitioning in Action

```
┌─────────────────────────────────────────────────────────────────────────┐
│                      PARTITION PRUNING (Optimization)                    │
└─────────────────────────────────────────────────────────────────────────┘

Scenario: Find orders in March 2024

WITHOUT Partitioning:
─────────────────────
SELECT * FROM orders WHERE order_date BETWEEN '2024-03-01' AND '2024-03-31';

Database scans ALL 10 million rows
┌────────────────────────────────────────┐
│         orders table                   │
│                                        │
│  [scanning all 10M rows...]            │
│                                        │
└────────────────────────────────────────┘

Time: 5 seconds (slow!)


WITH Partitioning (by quarter):
────────────────────────────────
SELECT * FROM orders WHERE order_date BETWEEN '2024-03-01' AND '2024-03-31';

Database scans ONLY Q1 partition (2.5M rows)
┌──────────────┐  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐
│ Partition 1  │  │ Partition 2  │  │ Partition 3  │  │ Partition 4  │
│    (Q1)      │  │    (Q2)      │  │    (Q3)      │  │    (Q4)      │
│ [scanning]   │  │   skipped    │  │   skipped    │  │   skipped    │
└──────────────┘  └──────────────┘  └──────────────┘  └──────────────┘

Time: 1 second (5x faster!)

✓ This is called PARTITION PRUNING
✓ Database optimizer is smart enough to skip irrelevant partitions
```

---

## Deep Dive: Sharding

**Sharding** (also called **Horizontal Sharding**) distributes data across **multiple physical servers**. Each server is called a **shard**.

```
┌─────────────────────────────────────────────────────────────────────────┐
│                          SHARDING ARCHITECTURE                           │
└─────────────────────────────────────────────────────────────────────────┘

                            ┌─────────────────┐
                            │  Application    │
                            │    Server       │
                            └────────┬────────┘
                                     │
                                     ▼
                            ┌─────────────────┐
                            │  Shard Router   │
                            │  (knows which   │
                            │   shard to use) │
                            └────────┬────────┘
                                     │
        ┌────────────────────────────┼────────────────────────────┐
        │                            │                            │
        ▼                            ▼                            ▼
┌───────────────┐            ┌───────────────┐            ┌───────────────┐
│   Shard 1     │            │   Shard 2     │            │   Shard 3     │
│  Server A     │            │  Server B     │            │  Server C     │
│  10.0.1.1     │            │  10.0.1.2     │            │  10.0.1.3     │
│               │            │               │            │               │
│  Users:       │            │  Users:       │            │  Users:       │
│  1 - 1M       │            │  1M - 2M      │            │  2M - 3M      │
│               │            │               │            │               │
│  Storage:     │            │  Storage:     │            │  Storage:     │
│  500GB        │            │  500GB        │            │  500GB        │
└───────────────┘            └───────────────┘            └───────────────┘

Total Capacity: 1.5TB (3 × 500GB)
Total Throughput: 30k QPS (3 × 10k QPS per server)

✓ Horizontal Scaling
✓ Each shard is independent
✓ Failure of one shard doesn't affect others
```

### Sharding Strategies

```
┌─────────────────────────────────────────────────────────────────────────┐
│                    1. HASH-BASED SHARDING (Range Hash)                   │
└─────────────────────────────────────────────────────────────────────────┘

Use hash function to determine shard

Shard = hash(user_id) % number_of_shards

Example:
  user_id = 12345
  hash(12345) = 98765
  98765 % 3 = 2
  → Store in Shard 2

┌──────────────────────────────────────────────────────────────┐
│                    Hash Function                             │
│                                                              │
│  user_id ──▶ hash() ──▶ mod ──▶ shard_number               │
│                                                              │
│  12345   ──▶ 98765  ──▶  2   ──▶ Shard 2                    │
│  67890   ──▶ 45678  ──▶  0   ──▶ Shard 0                    │
│  11111   ──▶ 33333  ──▶  0   ──▶ Shard 0                    │
└──────────────────────────────────────────────────────────────┘

Benefits:
─────────
✓ Even distribution (no hot shards)
✓ Simple to implement

Problems:
─────────
✗ Adding/removing shards requires resharding (move data)
✗ Range queries difficult (must query all shards)


┌─────────────────────────────────────────────────────────────────────────┐
│                    2. RANGE-BASED SHARDING                               │
└─────────────────────────────────────────────────────────────────────────┘

Divide data by ranges of shard key

Shard 1: user_id 1 - 1,000,000
Shard 2: user_id 1,000,001 - 2,000,000
Shard 3: user_id 2,000,001 - 3,000,000

┌────────────────────────────────────────────────────────────┐
│                   Shard Key Ranges                         │
│                                                            │
│  1 ──────────────▶ 1M  │  Shard 1                         │
│  1M+1 ───────────▶ 2M  │  Shard 2                         │
│  2M+1 ───────────▶ 3M  │  Shard 3                         │
└────────────────────────────────────────────────────────────┘

Example Query:
  SELECT * FROM users WHERE user_id BETWEEN 500000 AND 600000;
  ↓
  Only query Shard 1 (range optimization)

Benefits:
─────────
✓ Range queries efficient (only query relevant shards)
✓ Easy to understand

Problems:
─────────
✗ Uneven distribution (hot shards)
  - New users get high IDs → all traffic to latest shard
✗ Need to rebalance shards over time


┌─────────────────────────────────────────────────────────────────────────┐
│                    3. GEOGRAPHIC SHARDING                                │
└─────────────────────────────────────────────────────────────────────────┘

Shard by geographic region (latency optimization)

Shard 1 (US-East):    Users in North America
Shard 2 (EU-West):    Users in Europe
Shard 3 (Asia-Pacific): Users in Asia

                World Map
    ┌──────────────────────────────────────┐
    │                                      │
    │  🇺🇸 North America                    │
    │  └──▶ Shard 1 (us-east-1)            │
    │                                      │
    │  🇪🇺 Europe                           │
    │  └──▶ Shard 2 (eu-west-1)            │
    │                                      │
    │  🇯🇵 Asia                             │
    │  └──▶ Shard 3 (ap-southeast-1)       │
    │                                      │
    └──────────────────────────────────────┘

Benefits:
─────────
✓ Low latency (data close to users)
✓ Compliance (GDPR - EU data stays in EU)
✓ Natural distribution

Problems:
─────────
✗ Cross-region queries expensive
✗ Uneven distribution (more users in some regions)


┌─────────────────────────────────────────────────────────────────────────┐
│                    4. CONSISTENT HASHING                                 │
└─────────────────────────────────────────────────────────────────────────┘

Advanced technique to minimize data movement when adding/removing shards

                   Hash Ring (0 to 2^32)
                ┌─────────────────────────┐
             0  │                         │  2^32
                │         Shard 1         │
          Shard3│     (hash: 100M)        │
       (hash:   │           ●             │
        900M)   │                         │
           ●    │                         │
                │    ●                    │   Shard 2
                │ Shard 4                 │   (hash: 500M)
                │(hash: 200M)             │      ●
                │                         │
                └─────────────────────────┘

Key placement:
  user_id = 12345
  hash(12345) = 350M
  → Walk clockwise to next shard → Shard 2

Adding new shard:
  Only affects keys between previous and new shard
  NOT all keys (unlike simple hash % N)

Benefits:
─────────
✓ Adding/removing shards moves minimal data
✓ Even distribution with virtual nodes

Used by: Amazon DynamoDB, Apache Cassandra, Redis Cluster
```

### Sharding: Routing Strategies

```
┌─────────────────────────────────────────────────────────────────────────┐
│                    HOW TO ROUTE QUERIES TO SHARDS?                       │
└─────────────────────────────────────────────────────────────────────────┘

1. APPLICATION-LEVEL ROUTING (Client-side)
───────────────────────────────────────────

Application has logic to determine shard

┌──────────────────┐
│   Application    │
│                  │
│  ShardRouter {   │
│    getShard() {  │
│      shard =     │
│      hash(id)%N  │
│    }             │
│  }               │
└────────┬─────────┘
         │
    ┌────┴─────┬──────────┐
    ▼          ▼          ▼
Shard 1    Shard 2    Shard 3

Java Example:
─────────────
public class ShardRouter {
    private List<DataSource> shards;

    public DataSource getShard(Long userId) {
        int shardIndex = Math.abs(userId.hashCode()) % shards.size();
        return shards.get(shardIndex);
    }
}

// In service
public User getUser(Long userId) {
    DataSource shard = shardRouter.getShard(userId);
    return shard.query("SELECT * FROM users WHERE id = ?", userId);
}

Benefits:
✓ Full control
✓ No extra infrastructure

Problems:
✗ Logic in every application
✗ Hard to change sharding strategy


2. PROXY-LEVEL ROUTING (Middleware)
────────────────────────────────────

Dedicated proxy routes queries

┌──────────────────┐
│   Application    │
└────────┬─────────┘
         │
         ▼
┌──────────────────┐
│  Shard Proxy     │  ← Vitess, ProxySQL, MySQL Router
│  (knows routing) │
└────────┬─────────┘
         │
    ┌────┴─────┬──────────┐
    ▼          ▼          ▼
Shard 1    Shard 2    Shard 3

Application code:
─────────────────
// Application doesn't know about sharding
DataSource ds = getDataSource(); // Points to proxy
User user = ds.query("SELECT * FROM users WHERE id = ?", userId);
// Proxy automatically routes to correct shard

Benefits:
✓ Application doesn't know about sharding
✓ Easy to change routing logic

Problems:
✗ Extra network hop (latency)
✗ Single point of failure (need HA proxy)


3. QUERY ROUTER (Database-level)
─────────────────────────────────

Database itself handles routing

Example: MongoDB with sharded cluster

┌──────────────────┐
│   Application    │
└────────┬─────────┘
         │
         ▼
┌──────────────────┐
│  mongos (router) │  ← Built into MongoDB
└────────┬─────────┘
         │
    ┌────┴─────┬──────────┐
    ▼          ▼          ▼
Shard 1    Shard 2    Shard 3

Application code:
─────────────────
// Connects to mongos (looks like single database)
MongoClient client = new MongoClient("mongos-host");
db.users.find({ userId: 12345 });
// mongos routes to correct shard automatically

Benefits:
✓ Native to database
✓ Optimized routing
✓ Application agnostic

Problems:
✗ Locked into specific database
```

---

## Challenges with Sharding

```
┌─────────────────────────────────────────────────────────────────────────┐
│                      SHARDING CHALLENGES                                 │
└─────────────────────────────────────────────────────────────────────────┘

1. JOINS ACROSS SHARDS
──────────────────────

Problem: User (Shard 1) places Order (Shard 2)

┌─────────────┐              ┌─────────────┐
│  Shard 1    │              │  Shard 2    │
│  users      │              │  orders     │
│             │              │             │
│  user_id: 5 │              │ order_id: 1 │
│  name: Alice│              │ user_id: 5  │
└─────────────┘              └─────────────┘

Query: SELECT users.name, orders.total
       FROM users
       JOIN orders ON users.id = orders.user_id
       WHERE users.id = 5;

❌ Cannot do efficient JOIN across shards

Solutions:
──────────

Option 1: Denormalize (duplicate data)
  orders table also stores user_name
  ✓ No cross-shard query needed
  ✗ Data duplication, consistency issues

Option 2: Application-level join
  1. Query Shard 1 for user
  2. Query Shard 2 for orders
  3. Join in application memory
  ✓ Works
  ✗ Two network calls, not efficient

Option 3: Co-locate related data
  Shard by user_id for BOTH tables
  User 5's data (users + orders) all in Shard 1
  ✓ Can do local joins
  ✓ This is the recommended approach


2. GLOBAL QUERIES (Scatter-Gather)
───────────────────────────────────

Query: SELECT * FROM users WHERE age > 25;

No user_id in WHERE clause → Must query ALL shards!

┌──────────────┐      ┌──────────────┐      ┌──────────────┐
│   Shard 1    │      │   Shard 2    │      │   Shard 3    │
│   Query ✓    │      │   Query ✓    │      │   Query ✓    │
│   10k rows   │      │   8k rows    │      │   12k rows   │
└──────┬───────┘      └──────┬───────┘      └──────┬───────┘
       │                     │                     │
       └─────────────────────┴─────────────────────┘
                             ▼
                    Application merges
                    Sort + Paginate
                    Return 30k rows

Problems:
✗ Slow (network latency to all shards)
✗ Application must merge/sort results
✗ Cannot use database optimizations

Solutions:
──────────
• Avoid global queries (always filter by shard key)
• Use read replicas for analytics
• Use separate data warehouse for reporting


3. DISTRIBUTED TRANSACTIONS
────────────────────────────

Problem: Transfer money between users on different shards

User A (Shard 1): balance = $500
User B (Shard 2): balance = $300

Transfer $100 from A to B:
  Shard 1: UPDATE users SET balance = 400 WHERE id = A;
  Shard 2: UPDATE users SET balance = 400 WHERE id = B;

What if Shard 1 succeeds but Shard 2 fails?
❌ Money lost!

Solutions:
──────────
• Use distributed transactions (2PC) - slow, complex
• Use Saga pattern - eventual consistency
• Avoid cross-shard transactions (shard by account, not user)


4. HOTSPOTS (Unbalanced Load)
──────────────────────────────

Problem: One shard gets more traffic

┌──────────────┐      ┌──────────────┐      ┌──────────────┐
│   Shard 1    │      │   Shard 2    │      │   Shard 3    │
│              │      │              │      │              │
│   10k QPS    │      │   50k QPS 🔥 │      │   12k QPS    │
│   (normal)   │      │   (HOT!)     │      │   (normal)   │
└──────────────┘      └──────────────┘      └──────────────┘

Causes:
• Celebrity user (millions of followers)
• New product launch (everyone accessing)
• Poor shard key choice (recent data gets all traffic)

Solutions:
──────────
• Better shard key (avoid time-based keys)
• Split hot shard into multiple shards
• Cache hot data (Redis)
• Use read replicas for hot shards


5. RESHARDING (Adding/Removing Shards)
───────────────────────────────────────

Problem: Database growing, need to add more shards

Before: 3 shards
  user_id % 3
  User 10 → Shard 1

After: 4 shards
  user_id % 4
  User 10 → Shard 2 (different!)

❌ Must move data!

Solutions:
──────────
• Consistent hashing (minimizes data movement)
• Virtual shards (logical → physical mapping)
• Gradual migration (move data slowly)
• Plan ahead (over-provision initially)
```

---

## Partitioning vs Sharding: Side by Side

```
┌─────────────────────────────────────────────────────────────────────────┐
│                    PARTITIONING vs SHARDING                              │
└─────────────────────────────────────────────────────────────────────────┘

╔═══════════════════╦════════════════════════╦════════════════════════╗
║    Feature        ║     Partitioning       ║       Sharding         ║
╠═══════════════════╬════════════════════════╬════════════════════════╣
║ Scope             ║ Single database server ║ Multiple servers       ║
╠═══════════════════╬════════════════════════╬════════════════════════╣
║ Purpose           ║ Query optimization     ║ Horizontal scaling     ║
║                   ║ Maintenance            ║ Handle massive data    ║
╠═══════════════════╬════════════════════════╬════════════════════════╣
║ Scale Limit       ║ Single server capacity ║ Almost unlimited       ║
║                   ║ (TB)                   ║ (PB)                   ║
╠═══════════════════╬════════════════════════╬════════════════════════╣
║ Complexity        ║ Low                    ║ High                   ║
╠═══════════════════╬════════════════════════╬════════════════════════╣
║ Joins             ║ Easy (same server)     ║ Hard (cross-shard)     ║
╠═══════════════════╬════════════════════════╬════════════════════════╣
║ Transactions      ║ ACID (easy)            ║ Distributed (complex)  ║
╠═══════════════════╬════════════════════════╬════════════════════════╣
║ Failure Impact    ║ Entire database down   ║ Only one shard down    ║
╠═══════════════════╬════════════════════════╬════════════════════════╣
║ Cost              ║ Lower (one server)     ║ Higher (many servers)  ║
╠═══════════════════╬════════════════════════╬════════════════════════╣
║ Examples          ║ PostgreSQL partitions  ║ MongoDB sharding       ║
║                   ║ MySQL partitions       ║ Cassandra clusters     ║
║                   ║ Oracle partitions      ║ Instagram (Postgres)   ║
╠═══════════════════╬════════════════════════╬════════════════════════╣
║ When to Use       ║ • <10TB data           ║ • >10TB data           ║
║                   ║ • Time-series data     ║ • >100k QPS            ║
║                   ║ • Archive old data     ║ • High availability    ║
║                   ║ • Single DC            ║ • Global distribution  ║
╚═══════════════════╩════════════════════════╩════════════════════════╝
```

---

## Real-World Examples

```
┌─────────────────────────────────────────────────────────────────────────┐
│                         INSTAGRAM (Sharding)                             │
└─────────────────────────────────────────────────────────────────────────┘

Challenge: 2+ billion users, can't fit in single database

Solution: Shard by user_id

Shard Key: user_id
Strategy: Hash-based + Consistent hashing

┌────────────────┐  ┌────────────────┐  ┌────────────────┐
│   Shard 1      │  │   Shard 2      │  │   Shard 3      │
│                │  │                │  │                │
│ Users:         │  │ Users:         │  │ Users:         │
│  1-100M        │  │  100M-200M     │  │  200M-300M     │
│                │  │                │  │                │
│ Posts:         │  │ Posts:         │  │ Posts:         │
│  by users 1-   │  │  by users 100M-│  │  by users 200M-│
│  100M          │  │  200M          │  │  300M          │
└────────────────┘  └────────────────┘  └────────────────┘

Co-location:
  User 5's profile, posts, followers → all in Shard 1
  ✓ No cross-shard queries for user timeline

Total: 1000+ PostgreSQL shards


┌─────────────────────────────────────────────────────────────────────────┐
│                     UBER (Geographic Sharding)                           │
└─────────────────────────────────────────────────────────────────────────┘

Challenge: Drivers and riders in different cities

Solution: Shard by city/region

┌────────────────┐  ┌────────────────┐  ┌────────────────┐
│ San Francisco  │  │  New York      │  │  London        │
│   Shard        │  │   Shard        │  │   Shard        │
│                │  │                │  │                │
│ Drivers: 10k   │  │ Drivers: 20k   │  │ Drivers: 15k   │
│ Riders: 100k   │  │ Riders: 200k   │  │ Riders: 150k   │
└────────────────┘  └────────────────┘  └────────────────┘

Benefits:
✓ Low latency (data close to users)
✓ Natural isolation (SF trips don't affect NY)
✓ Can scale cities independently


┌─────────────────────────────────────────────────────────────────────────┐
│                    YOUTUBE (Partitioning + Sharding)                     │
└─────────────────────────────────────────────────────────────────────────┘

Partitioning: Within each shard, partition by date
  Recent videos (hot) → SSD
  Old videos (cold) → HDD

Sharding: Multiple database servers by video_id

┌─────────────────────────────────────────────────┐
│              Shard 1 (videos 1-1M)              │
│  ┌──────────────┐  ┌──────────────┐            │
│  │ Partition 1  │  │ Partition 2  │            │
│  │ 2024 videos  │  │ 2023 videos  │            │
│  │ (SSD)        │  │ (HDD)        │            │
│  └──────────────┘  └──────────────┘            │
└─────────────────────────────────────────────────┘

Both techniques together!
```

---

## Code Examples

```java
┌─────────────────────────────────────────────────────────────────────────┐
│                      PARTITIONING - SQL Example                          │
└─────────────────────────────────────────────────────────────────────────┘

-- PostgreSQL Table Partitioning
CREATE TABLE orders (
    order_id BIGSERIAL,
    user_id BIGINT NOT NULL,
    order_date DATE NOT NULL,
    total_amount DECIMAL(10,2),
    status VARCHAR(50)
) PARTITION BY RANGE (order_date);

-- Create partitions (one per quarter)
CREATE TABLE orders_2024_q1 PARTITION OF orders
    FOR VALUES FROM ('2024-01-01') TO ('2024-04-01');

CREATE TABLE orders_2024_q2 PARTITION OF orders
    FOR VALUES FROM ('2024-04-01') TO ('2024-07-01');

CREATE TABLE orders_2024_q3 PARTITION OF orders
    FOR VALUES FROM ('2024-07-01') TO ('2024-10-01');

CREATE TABLE orders_2024_q4 PARTITION OF orders
    FOR VALUES FROM ('2024-10-01') TO ('2025-01-01');

-- Insert (automatically goes to correct partition)
INSERT INTO orders (user_id, order_date, total_amount, status)
VALUES (123, '2024-03-15', 99.99, 'completed');
-- Goes to orders_2024_q1

-- Query (automatic partition pruning)
SELECT * FROM orders WHERE order_date = '2024-03-15';
-- Only scans orders_2024_q1

-- Drop old partition (archive)
DROP TABLE orders_2023_q1;


┌─────────────────────────────────────────────────────────────────────────┐
│                   SHARDING - Java Application Example                    │
└─────────────────────────────────────────────────────────────────────────┘

// Shard Router
@Component
public class ShardRouter {

    private final Map<Integer, DataSource> shards = new HashMap<>();

    @PostConstruct
    public void init() {
        // Initialize connections to different database servers
        shards.put(0, createDataSource("jdbc:postgresql://db1:5432/shard0"));
        shards.put(1, createDataSource("jdbc:postgresql://db2:5432/shard1"));
        shards.put(2, createDataSource("jdbc:postgresql://db3:5432/shard2"));
    }

    public DataSource getShard(Long userId) {
        // Hash-based sharding
        int shardId = Math.abs(userId.hashCode()) % shards.size();
        return shards.get(shardId);
    }

    public List<DataSource> getAllShards() {
        return new ArrayList<>(shards.values());
    }
}

// User Repository with Sharding
@Repository
public class ShardedUserRepository {

    @Autowired
    private ShardRouter shardRouter;

    public User findById(Long userId) {
        // Route to correct shard
        DataSource shard = shardRouter.getShard(userId);
        JdbcTemplate jdbc = new JdbcTemplate(shard);

        return jdbc.queryForObject(
            "SELECT * FROM users WHERE user_id = ?",
            new Object[]{userId},
            new UserRowMapper()
        );
    }

    public List<User> findByAgeGreaterThan(int age) {
        // Global query - must query all shards (scatter-gather)
        List<User> allUsers = new ArrayList<>();

        for (DataSource shard : shardRouter.getAllShards()) {
            JdbcTemplate jdbc = new JdbcTemplate(shard);
            List<User> users = jdbc.query(
                "SELECT * FROM users WHERE age > ?",
                new Object[]{age},
                new UserRowMapper()
            );
            allUsers.addAll(users);
        }

        return allUsers;
    }

    public void save(User user) {
        // Route to correct shard
        DataSource shard = shardRouter.getShard(user.getUserId());
        JdbcTemplate jdbc = new JdbcTemplate(shard);

        jdbc.update(
            "INSERT INTO users (user_id, name, email, age) VALUES (?, ?, ?, ?)",
            user.getUserId(), user.getName(), user.getEmail(), user.getAge()
        );
    }
}

// Service Layer (transparent to sharding)
@Service
public class UserService {

    @Autowired
    private ShardedUserRepository userRepo;

    public User getUser(Long userId) {
        // Application doesn't care about sharding
        return userRepo.findById(userId);
    }
}
```

---

## Decision Tree: Which Should You Use?

```
┌─────────────────────────────────────────────────────────────────────────┐
│                   PARTITIONING vs SHARDING DECISION                      │
└─────────────────────────────────────────────────────────────────────────┘

Start
  │
  ├─▶ Data size < 1TB?
  │   │
  │   ├─▶ YES → Use PARTITIONING (or nothing)
  │   │          ✓ Keep it simple
  │   │          ✓ Single server is fine
  │   │
  │   └─▶ NO ────────────────────────┐
  │                                  │
  ├─▶ Need to query across all data?│
  │   │                              │
  │   ├─▶ YES (Analytics) ──────────┤
  │   │   • Use partitioning        │
  │   │   • Or separate data warehouse (Snowflake, BigQuery)
  │   │                              │
  │   └─▶ NO (Transactional) ───────┤
  │       • Can isolate by key      │
  │       • Use SHARDING ✓          │
  │                                  │
  ├─▶ Need global distribution?     │
  │   │                              │
  │   ├─▶ YES → Geographic SHARDING │
  │   │          ✓ Low latency      │
  │   │          ✓ Compliance (GDPR)│
  │   │                              │
  │   └─▶ NO → Hash SHARDING        │
  │              ✓ Even distribution │
  │                                  │
  └─▶ Budget constraints?            │
      │                              │
      ├─▶ Limited → PARTITIONING     │
      │             ✓ Cheaper        │
      │                              │
      └─▶ Flexible → SHARDING        │
                    ✓ Better scaling │
```

---

## Key Takeaways for Interview

**Question: "What's the difference between partitioning and sharding?"**

**Answer:**

"Both split large datasets into smaller pieces, but with different scope:

**Partitioning** divides data within a **single database server**:
- Purpose: Query optimization and maintenance
- Example: Partition orders table by date (Q1, Q2, Q3, Q4)
- Benefit: Queries only scan relevant partition (faster)
- Limit: Still constrained by single server capacity

**Sharding** distributes data across **multiple servers**:
- Purpose: Horizontal scaling for massive data
- Example: Shard users by user_id across 100 servers
- Benefit: Can scale to petabytes by adding more servers
- Complexity: Joins across shards difficult, need routing logic

**Real-world**: Instagram uses sharding (billions of users across 1000+ PostgreSQL servers). A typical e-commerce site might just use partitioning (archive old orders).

Choose partitioning when data fits one server. Choose sharding when you need to scale beyond one server's capacity."

**Follow-up: "What are sharding challenges?"**

"Main challenges:
1. **Joins** - Can't efficiently join across shards. Solution: Co-locate related data on same shard.
2. **Distributed transactions** - Maintain consistency across shards. Solution: Use Saga pattern.
3. **Hotspots** - One shard gets more traffic. Solution: Better shard key or split hot shard.
4. **Global queries** - Must query all shards. Solution: Avoid when possible, or use read replicas for analytics.
5. **Resharding** - Adding shards requires data migration. Solution: Use consistent hashing or plan ahead."
