# What Happens When Your Database Reaches 100 Million Users? (Database Sharding)

## 1. The Problem

When an application grows and starts getting millions or hundreds of millions of users, the database becomes a major bottleneck.

Initially, most applications use a single database server.

### Example architecture:

```
Users
  ↓
Application Server
  ↓
Single Database
```

In the beginning this works fine because:

- number of users is small
- number of requests is manageable

But when the system grows to 100 million users, several problems appear.

### Visual: Single Database Problem

```
┌────────────────────────────────────────────────────────────────────────┐
│              SINGLE DATABASE ARCHITECTURE (NOT SCALABLE)               │
└────────────────────────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────────────┐
│                   100 MILLION USERS                          │
└───┬──────────┬──────────┬──────────┬──────────┬──────────┬──┘
    │          │          │          │          │          │
    │ Login    │ Profile  │ Orders   │ Messages │ Payments │
    │ requests │ requests │ requests │ requests │ requests │
    │          │          │          │          │          │
    ↓          ↓          ↓          ↓          ↓          ↓
┌──────────────────────────────────────────────────────────────┐
│                 APPLICATION SERVERS                          │
│                                                              │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐   │
│  │ Server 1 │  │ Server 2 │  │ Server 3 │  │ Server N │   │
│  └────┬─────┘  └────┬─────┘  └────┬─────┘  └────┬─────┘   │
│       │             │             │             │          │
│       └─────────────┼─────────────┼─────────────┘          │
│                     │             │                        │
└─────────────────────┼─────────────┼────────────────────────┘
                      │             │
                      ↓             ↓
              ┌───────────────────────────────┐
              │    SINGLE DATABASE SERVER     │
              │    🚨 BOTTLENECK! 🚨          │
              │                               │
              │  ALL TRAFFIC HERE!            │
              │                               │
              │  ┌─────────────────────────┐  │
              │  │ Users Table             │  │
              │  │ 100,000,000 rows        │  │
              │  ├─────────────────────────┤  │
              │  │ Orders Table            │  │
              │  │ 500,000,000 rows        │  │
              │  ├─────────────────────────┤  │
              │  │ Messages Table          │  │
              │  │ 10,000,000,000 rows     │  │
              │  └─────────────────────────┘  │
              │                               │
              │  ⚠️  Overloaded!              │
              │  ⚠️  Slow queries!            │
              │  ⚠️  Hardware limit reached!  │
              └───────────────────────────────┘
```

## 2. Problems with a Single Database

### Problem 1: High Load

All read and write requests go to the same database.

Example:

- Login requests
- Profile requests
- Orders
- Payments
- Messages

All these hit one database server.

The server becomes overloaded.

### Problem 2: Slow Queries

As the data grows, tables become extremely large.

Example:

```
Users table → 100 million rows
Orders table → 500 million rows
Messages table → billions of rows
```

Even indexed queries start becoming slower.

### Problem 3: Limited Hardware (Vertical Scaling Limit)

You can increase database power by:

- adding more CPU
- adding more RAM
- using SSD storage

But this approach has a limit.

This is called **Vertical Scaling**.

Eventually you reach the maximum hardware capacity, and the database still cannot handle the traffic.

### Visual: Vertical Scaling Problem

```
┌────────────────────────────────────────────────────────────────────────┐
│                    VERTICAL SCALING LIMITATIONS                        │
└────────────────────────────────────────────────────────────────────────┘

VERTICAL SCALING (Scale UP)
───────────────────────────

Day 1: Basic Server
┌─────────────────────┐
│  Database Server    │
│                     │
│  CPU: 4 cores       │
│  RAM: 16 GB         │
│  Disk: 500 GB HDD   │
│                     │
│  Load: ✅ Fine      │
└─────────────────────┘


Day 30: Upgraded Server
┌─────────────────────┐
│  Database Server    │
│                     │
│  CPU: 16 cores      │
│  RAM: 64 GB         │
│  Disk: 2 TB SSD     │
│                     │
│  Load: ✅ Fine      │
└─────────────────────┘


Day 90: High-End Server
┌─────────────────────┐
│  Database Server    │
│                     │
│  CPU: 64 cores      │
│  RAM: 256 GB        │
│  Disk: 10 TB SSD    │
│                     │
│  Load: ⚠️ Struggling│
└─────────────────────┘


Day 180: Maximum Server
┌─────────────────────┐
│  Database Server    │
│                     │
│  CPU: 128 cores     │
│  RAM: 1 TB          │
│  Disk: 50 TB SSD    │
│                     │
│  Load: 🚨 Maxed Out │
│  Cost: 💰💰💰      │
│                     │
│  ❌ Cannot upgrade  │
│     further!        │
└─────────────────────┘

Problem:
• Hardware has physical limits
• Very expensive
• Single point of failure
• Cannot scale beyond hardware capacity
```

## 3. Solution — Database Sharding

To solve this problem, companies use **database sharding**.

Database sharding means:

**Splitting one large database into multiple smaller databases.**

Each smaller database is called a **shard**.

Instead of storing all users in one database, the data is divided.

### Example:

```
Shard 1 → Users 1 to 1 million
Shard 2 → Users 1 million to 2 million
Shard 3 → Users 2 million to 3 million
Shard 4 → Users 3 million to 4 million
```

Each shard stores only a portion of the total data.

### Visual: Sharding Architecture

```
┌────────────────────────────────────────────────────────────────────────┐
│              DATABASE SHARDING ARCHITECTURE (SCALABLE)                 │
└────────────────────────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────────────┐
│                   100 MILLION USERS                          │
└───┬──────────┬──────────┬──────────┬──────────┬──────────┬──┘
    │          │          │          │          │          │
    ↓          ↓          ↓          ↓          ↓          ↓
┌──────────────────────────────────────────────────────────────┐
│                 APPLICATION SERVERS                          │
│                                                              │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐   │
│  │ Server 1 │  │ Server 2 │  │ Server 3 │  │ Server N │   │
│  └────┬─────┘  └────┬─────┘  └────┬─────┘  └────┬─────┘   │
│       │             │             │             │          │
└───────┼─────────────┼─────────────┼─────────────┼──────────┘
        │             │             │             │
        ↓             ↓             ↓             ↓
┌──────────────────────────────────────────────────────────────┐
│              SHARD ROUTER / ROUTING LOGIC                    │
│                                                              │
│  Determines which shard to query based on:                   │
│  • User ID                                                   │
│  • Shard Key                                                 │
│  • Hashing Algorithm                                         │
│                                                              │
│  Example: UserID % Number_of_Shards                          │
└───────┬──────────────┬──────────────┬──────────────┬────────┘
        │              │              │              │
        ↓              ↓              ↓              ↓
┌──────────────┐ ┌──────────────┐ ┌──────────────┐ ┌──────────────┐
│   SHARD 1    │ │   SHARD 2    │ │   SHARD 3    │ │   SHARD 4    │
│              │ │              │ │              │ │              │
│ Users:       │ │ Users:       │ │ Users:       │ │ Users:       │
│ 1 - 1M       │ │ 1M - 2M      │ │ 2M - 3M      │ │ 3M - 4M      │
│              │ │              │ │              │ │              │
│ ┌──────────┐ │ │ ┌──────────┐ │ │ ┌──────────┐ │ │ ┌──────────┐ │
│ │Users     │ │ │ │Users     │ │ │ │Users     │ │ │ │Users     │ │
│ │1M rows   │ │ │ │1M rows   │ │ │ │1M rows   │ │ │ │1M rows   │ │
│ ├──────────┤ │ │ ├──────────┤ │ │ ├──────────┤ │ │ ├──────────┤ │
│ │Orders    │ │ │ │Orders    │ │ │ │Orders    │ │ │ │Orders    │ │
│ │5M rows   │ │ │ │5M rows   │ │ │ │5M rows   │ │ │ │5M rows   │ │
│ └──────────┘ │ │ └──────────┘ │ │ └──────────┘ │ │ └──────────┘ │
│              │ │              │ │              │ │              │
│ Load: 25%    │ │ Load: 25%    │ │ Load: 25%    │ │ Load: 25%    │
│ ✅ Fast!     │ │ ✅ Fast!     │ │ ✅ Fast!     │ │ ✅ Fast!     │
└──────────────┘ └──────────────┘ └──────────────┘ └──────────────┘

Benefits:
✅ Load distributed across multiple databases
✅ Each database handles smaller dataset
✅ Queries are faster
✅ Can add more shards as needed (Horizontal Scaling)
```

## 4. How the System Finds the Correct Database

When a request comes from a user, the system must know which shard contains the data.

This is done using a **Shard Key**.

A shard key is a field used to determine which database should store or retrieve the data.

### Common shard keys:

- User ID
- Customer ID
- Region
- Order ID

### Example using User ID as shard key.

```
UserID % Number_of_shards
```

Example:

```
UserID = 1256789
Number of shards = 4
1256789 % 4 = 1
```

So the request goes to **Shard 1**.

### Visual: Shard Key Routing

```
┌────────────────────────────────────────────────────────────────────────┐
│                    SHARD KEY ROUTING MECHANISM                         │
└────────────────────────────────────────────────────────────────────────┘

METHOD 1: HASH-BASED SHARDING (Most Common)
────────────────────────────────────────────

User Request: Get profile for UserID = 1256789

Step 1: Calculate Shard
┌─────────────────────────────────────┐
│  UserID % Number_of_Shards          │
│                                     │
│  1256789 % 4 = 1                    │
│                                     │
│  Result: Shard 1                    │
└─────────────────────────────────────┘

Step 2: Route to Correct Shard
┌─────────────────────────────────────────────────────────────┐
│                  ROUTING LOGIC                              │
│                                                             │
│  IF UserID % 4 == 0  → Shard 0                              │
│  IF UserID % 4 == 1  → Shard 1  ← UserID 1256789 goes here │
│  IF UserID % 4 == 2  → Shard 2                              │
│  IF UserID % 4 == 3  → Shard 3                              │
└─────────────────────────────────────────────────────────────┘

Step 3: Query the Shard
┌──────────────┐
│   SHARD 1    │
│              │
│ SELECT *     │
│ FROM users   │
│ WHERE        │
│ user_id =    │
│ 1256789      │
│              │
│ ✅ Found!    │
└──────────────┘


EXAMPLES OF DIFFERENT USER IDs
───────────────────────────────

UserID: 1000001  →  1000001 % 4 = 1  →  Shard 1
UserID: 2500000  →  2500000 % 4 = 0  →  Shard 0
UserID: 3750000  →  3750000 % 4 = 2  →  Shard 2
UserID: 4999999  →  4999999 % 4 = 3  →  Shard 3
UserID: 5000000  →  5000000 % 4 = 0  →  Shard 0


VISUAL FLOW
───────────

Request: UserID 1256789
         │
         │ Apply hash function
         ↓
    1256789 % 4 = 1
         │
         ↓
┌────────────────────────────────────┐
│      SHARD ROUTER                  │
│                                    │
│  Shard 0 ←─────────────────┐       │
│  Shard 1 ←─────────────────┼─ Go here!
│  Shard 2                   │       │
│  Shard 3                   │       │
└────────────────────────────┼───────┘
                             │
                             ↓
                      ┌──────────────┐
                      │   SHARD 1    │
                      │              │
                      │ Users:       │
                      │ 1M - 2M      │
                      │              │
                      │ Find UserID  │
                      │ 1256789      │
                      │              │
                      │ ✅ Success   │
                      └──────────────┘


METHOD 2: RANGE-BASED SHARDING
───────────────────────────────

Shard 0: UserID 1         - 1,000,000
Shard 1: UserID 1,000,001 - 2,000,000
Shard 2: UserID 2,000,001 - 3,000,000
Shard 3: UserID 3,000,001 - 4,000,000

UserID 1,256,789 → Falls in range 1M-2M → Shard 1


METHOD 3: GEOGRAPHIC SHARDING
──────────────────────────────

Shard 0: Users in North America
Shard 1: Users in Europe
Shard 2: Users in Asia
Shard 3: Users in Rest of World

User in New York → Shard 0
User in London → Shard 1
User in Tokyo → Shard 2
```

## 5. Example Architecture

With sharding the architecture becomes:

```
Users
   ↓
Application Server
   ↓
Shard Router / Logic
   ↓
 ┌───────────┬───────────┬───────────┐
 │ Database1 │ Database2 │ Database3 │
 │ Users 1M  │ Users 2M  │ Users 3M  │
 └───────────┴───────────┴───────────┘
```

The application decides which shard to query.

### Visual: Complete Sharding Architecture

```
┌────────────────────────────────────────────────────────────────────────┐
│              COMPLETE SHARDING ARCHITECTURE                            │
└────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────┐
│                    CLIENT LAYER                         │
│                                                         │
│  ┌──────┐  ┌──────┐  ┌──────┐  ┌──────┐  ┌──────┐    │
│  │User 1│  │User 2│  │User 3│  │User 4│  │User N│    │
│  └───┬──┘  └───┬──┘  └───┬──┘  └───┬──┘  └───┬──┘    │
└──────┼─────────┼─────────┼─────────┼─────────┼────────┘
       │         │         │         │         │
       │         │         │         │         │
       ↓         ↓         ↓         ↓         ↓
┌─────────────────────────────────────────────────────────┐
│                 LOAD BALANCER                           │
└───────┬─────────────┬─────────────┬─────────────┬───────┘
        │             │             │             │
        ↓             ↓             ↓             ↓
┌─────────────────────────────────────────────────────────┐
│              APPLICATION SERVERS                        │
│                                                         │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐            │
│  │  App     │  │  App     │  │  App     │            │
│  │ Server 1 │  │ Server 2 │  │ Server N │            │
│  │          │  │          │  │          │            │
│  │ Contains │  │ Contains │  │ Contains │            │
│  │ Sharding │  │ Sharding │  │ Sharding │            │
│  │ Logic    │  │ Logic    │  │ Logic    │            │
│  └────┬─────┘  └────┬─────┘  └────┬─────┘            │
└───────┼─────────────┼─────────────┼────────────────────┘
        │             │             │
        │             │             │
        ↓             ↓             ↓
┌─────────────────────────────────────────────────────────┐
│              SHARD ROUTING LAYER                        │
│                                                         │
│  Function: route(userID) {                              │
│    shardID = userID % numShards                         │
│    return shards[shardID]                               │
│  }                                                      │
└────┬──────────┬──────────┬──────────┬──────────┬───────┘
     │          │          │          │          │
     │          │          │          │          │
     ↓          ↓          ↓          ↓          ↓
┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐
│ SHARD 0  │ │ SHARD 1  │ │ SHARD 2  │ │ SHARD 3  │ │ SHARD N  │
│          │ │          │ │          │ │          │ │          │
│ Users:   │ │ Users:   │ │ Users:   │ │ Users:   │ │ Users:   │
│ 0-999K   │ │ 1M-2M    │ │ 2M-3M    │ │ 3M-4M    │ │ NM-XM    │
│          │ │          │ │          │ │          │ │          │
│ Primary  │ │ Primary  │ │ Primary  │ │ Primary  │ │ Primary  │
│ DB       │ │ DB       │ │ DB       │ │ DB       │ │ DB       │
│    │     │ │    │     │ │    │     │ │    │     │ │    │     │
│    ↓     │ │    ↓     │ │    ↓     │ │    ↓     │ │    ↓     │
│ Replica  │ │ Replica  │ │ Replica  │ │ Replica  │ │ Replica  │
│ (Backup) │ │ (Backup) │ │ (Backup) │ │ (Backup) │ │ (Backup) │
│          │ │          │ │          │ │          │ │          │
└──────────┘ └──────────┘ └──────────┘ └──────────┘ └──────────┘

Each Shard can have:
• Primary database (read/write)
• Replica databases (read-only, backup)
```

## 6. Benefits of Sharding

### 1. Better Performance

Each database contains less data, so queries become faster.

Example:

Instead of searching **100 million rows**, the database searches only **1 million rows**.

### 2. Load Distribution

Traffic is spread across multiple servers.

Example:

```
Shard 1 → handles users 1M
Shard 2 → handles users 2M
Shard 3 → handles users 3M
```

No single database becomes overloaded.

### 3. Scalability (Horizontal Scaling)

You can add new shards as your user base grows.

Example:

```
Shard 1 → 1M users
Shard 2 → 1M users
Shard 3 → 1M users
Shard 4 → 1M users
```

Later you can add:

```
Shard 5
Shard 6
Shard 7
```

### Visual: Benefits Comparison

```
┌────────────────────────────────────────────────────────────────────────┐
│                  BENEFITS OF SHARDING                                  │
└────────────────────────────────────────────────────────────────────────┘

BENEFIT 1: BETTER PERFORMANCE
──────────────────────────────

Without Sharding:
┌─────────────────────────┐
│  Single Database        │
│                         │
│  Query: Find user 1234  │
│  Search: 100M rows      │
│  Time: 5 seconds ❌     │
└─────────────────────────┘

With Sharding:
┌─────────────────────────┐
│  Shard 1                │
│                         │
│  Query: Find user 1234  │
│  Search: 1M rows        │
│  Time: 50ms ✅          │
└─────────────────────────┘

Result: 100x faster!


BENEFIT 2: LOAD DISTRIBUTION
─────────────────────────────

Without Sharding:
┌─────────────────────────┐
│  Single Database        │
│  Load: 100% 🚨          │
│  CPU: 95%               │
│  Memory: 90%            │
│  Disk I/O: Maxed out    │
└─────────────────────────┘

With Sharding (4 shards):
┌────────┐ ┌────────┐ ┌────────┐ ┌────────┐
│Shard 1 │ │Shard 2 │ │Shard 3 │ │Shard 4 │
│Load:25%│ │Load:25%│ │Load:25%│ │Load:25%│
│CPU: 30%│ │CPU: 30%│ │CPU: 30%│ │CPU: 30%│
│Mem: 35%│ │Mem: 35%│ │Mem: 35%│ │Mem: 35%│
│✅ Healthy│ │✅ Healthy│ │✅ Healthy│ │✅ Healthy│
└────────┘ └────────┘ └────────┘ └────────┘


BENEFIT 3: HORIZONTAL SCALABILITY
──────────────────────────────────

Day 1: Start with 2 shards
┌────────┐ ┌────────┐
│Shard 1 │ │Shard 2 │
│ 1M     │ │ 1M     │
│ users  │ │ users  │
└────────┘ └────────┘

Day 30: Add 2 more shards
┌────────┐ ┌────────┐ ┌────────┐ ┌────────┐
│Shard 1 │ │Shard 2 │ │Shard 3 │ │Shard 4 │
│ 1M     │ │ 1M     │ │ 1M     │ │ 1M     │
└────────┘ └────────┘ └────────┘ └────────┘

Day 90: Add more as needed
┌────────┐ ┌────────┐ ┌────────┐ ┌────────┐ ┌────────┐ ┌────────┐
│Shard 1 │ │Shard 2 │ │Shard 3 │ │Shard 4 │ │Shard 5 │ │Shard 6 │
└────────┘ └────────┘ └────────┘ └────────┘ └────────┘ └────────┘

✅ Can scale infinitely by adding more shards!


BENEFIT 4: FAULT ISOLATION
───────────────────────────

Without Sharding:
┌─────────────────────────┐
│  Single Database        │
│         │               │
│         ↓               │
│      💥 CRASH           │
│                         │
│  ❌ ALL USERS AFFECTED  │
│  ❌ ENTIRE SYSTEM DOWN  │
└─────────────────────────┘

With Sharding:
┌────────┐ ┌────────┐ ┌────────┐ ┌────────┐
│Shard 1 │ │Shard 2 │ │Shard 3 │ │Shard 4 │
│   ✅   │ │   💥   │ │   ✅   │ │   ✅   │
│Working │ │ Crashed│ │Working │ │Working │
└────────┘ └────────┘ └────────┘ └────────┘

✅ Only 25% of users affected
✅ Other shards continue working
✅ Better fault tolerance
```

## 7. Real Companies Using Sharding

Large tech companies use database sharding to scale their systems.

### Examples include:

#### Instagram
- Shards data by User ID
- Uses PostgreSQL with custom sharding logic
- Stores photos and user data across thousands of shards

#### Uber
- Shards data by geographic region
- Each city/region has its own database shard
- Reduces latency for location-based queries

#### Amazon
- Shards product catalog by category
- Orders sharded by customer ID
- Handles billions of transactions

#### Facebook
- One of the pioneers of database sharding
- Uses MySQL with custom sharding
- Stores user data across thousands of database servers

#### Netflix
- Shards viewing history by user
- Uses Cassandra (which has built-in sharding)
- Handles petabytes of data

### Visual: Real-World Scale Examples

```
┌────────────────────────────────────────────────────────────────────────┐
│                  REAL-WORLD SHARDING EXAMPLES                          │
└────────────────────────────────────────────────────────────────────────┘

INSTAGRAM
─────────
Users: 2+ Billion
Sharding Strategy: User ID based
Database: PostgreSQL

Shard Allocation:
┌─────────┐ ┌─────────┐ ┌─────────┐     ┌─────────┐
│Shard 1  │ │Shard 2  │ │Shard 3  │ ... │Shard N  │
│Users    │ │Users    │ │Users    │     │Users    │
│0-10M    │ │10M-20M  │ │20M-30M  │     │NM-XM    │
│         │ │         │ │         │     │         │
│Photos   │ │Photos   │ │Photos   │     │Photos   │
│Posts    │ │Posts    │ │Posts    │     │Posts    │
│Comments │ │Comments │ │Comments │     │Comments │
└─────────┘ └─────────┘ └─────────┘     └─────────┘


UBER
────
Users: 130+ Million
Sharding Strategy: Geographic (City-based)
Database: MySQL, PostgreSQL

Shard Allocation:
┌─────────────┐ ┌─────────────┐ ┌─────────────┐ ┌─────────────┐
│  Shard:     │ │  Shard:     │ │  Shard:     │ │  Shard:     │
│  New York   │ │  London     │ │  Tokyo      │ │  Mumbai     │
│             │ │             │ │             │ │             │
│  Riders     │ │  Riders     │ │  Riders     │ │  Riders     │
│  Drivers    │ │  Drivers    │ │  Drivers    │ │  Drivers    │
│  Trips      │ │  Trips      │ │  Trips      │ │  Trips      │
│  Payments   │ │  Payments   │ │  Payments   │ │  Payments   │
└─────────────┘ └─────────────┘ └─────────────┘ └─────────────┘

Benefit: Low latency (data stored close to users)


AMAZON
──────
Products: 350+ Million
Orders: Billions per year
Sharding Strategy: Customer ID + Product Category

Customer Data Shards:
┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐
│Customer  │ │Customer  │ │Customer  │ │Customer  │
│Shard 1   │ │Shard 2   │ │Shard 3   │ │Shard N   │
│          │ │          │ │          │ │          │
│Profiles  │ │Profiles  │ │Profiles  │ │Profiles  │
│Orders    │ │Orders    │ │Orders    │ │Orders    │
│Payments  │ │Payments  │ │Payments  │ │Payments  │
└──────────┘ └──────────┘ └──────────┘ └──────────┘

Product Catalog Shards:
┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐
│Electronics│ │Books     │ │Clothing  │ │Grocery   │
│           │ │          │ │          │ │          │
│Products   │ │Products  │ │Products  │ │Products  │
│Reviews    │ │Reviews   │ │Reviews   │ │Reviews   │
│Inventory  │ │Inventory │ │Inventory │ │Inventory │
└──────────┘ └──────────┘ └──────────┘ └──────────┘


WHY THEY USE SHARDING
─────────────────────

Without Sharding:
┌───────────────────────────────────┐
│  Single Database                  │
│                                   │
│  100M+ users                      │
│  Billions of records              │
│  Terabytes of data                │
│                                   │
│  Result:                          │
│  ❌ Slow queries                  │
│  ❌ Overloaded server             │
│  ❌ Cannot scale                  │
│  ❌ Frequent outages              │
└───────────────────────────────────┘

With Sharding:
┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐
│ Shard 1 │ │ Shard 2 │ │ Shard N │ │ Shard M │
│         │ │         │ │   ...   │ │         │
│ 1M users│ │ 1M users│ │         │ │ 1M users│
│ Small   │ │ Small   │ │         │ │ Small   │
│ dataset │ │ dataset │ │         │ │ dataset │
│         │ │         │ │         │ │         │
│ Result: │ │ Result: │ │ Result: │ │ Result: │
│ ✅ Fast │ │ ✅ Fast │ │ ✅ Fast │ │ ✅ Fast │
│ ✅ Scalable│ ✅ Scalable│ ✅ Scalable│ ✅ Scalable│
└─────────┘ └─────────┘ └─────────┘ └─────────┘

Can add more shards infinitely!
```

Because they handle millions or billions of users, a single database cannot handle that load.

## 8. Challenges of Sharding

Sharding also introduces some complexity.

### 1. Cross-Shard Queries

If a query needs data from multiple shards, it becomes more complex.

Example:

```
Find total orders across all users
```

Now the system must query all shards.

### 2. Rebalancing

When new shards are added, some data must be moved between shards.

This process is called **re-sharding**.

### 3. Joins Become Difficult

If related data exists in different shards, database joins become harder.

### Visual: Sharding Challenges

```
┌────────────────────────────────────────────────────────────────────────┐
│                  SHARDING CHALLENGES                                   │
└────────────────────────────────────────────────────────────────────────┘

CHALLENGE 1: CROSS-SHARD QUERIES
─────────────────────────────────

Problem: Get total sales across ALL users

Without Sharding (Simple):
┌─────────────────────────┐
│  Single Database        │
│                         │
│  SELECT SUM(amount)     │
│  FROM orders            │
│                         │
│  Result: $1,000,000     │
│  Time: 1 query          │
└─────────────────────────┘

With Sharding (Complex):
┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐
│ Shard 1  │ │ Shard 2  │ │ Shard 3  │ │ Shard 4  │
│ Query    │ │ Query    │ │ Query    │ │ Query    │
│ SUM()    │ │ SUM()    │ │ SUM()    │ │ SUM()    │
│          │ │          │ │          │ │          │
│ $250K    │ │ $250K    │ │ $250K    │ │ $250K    │
└────┬─────┘ └────┬─────┘ └────┬─────┘ └────┬─────┘
     │            │            │            │
     └────────────┼────────────┼────────────┘
                  │            │
                  ↓            ↓
         ┌───────────────────────────┐
         │  Application Layer        │
         │  Aggregate Results:       │
         │  $250K + $250K + $250K +  │
         │  $250K = $1,000,000       │
         │                           │
         │  Time: 4 queries          │
         │  Complexity: High         │
         └───────────────────────────┘


CHALLENGE 2: RE-SHARDING / DATA REBALANCING
────────────────────────────────────────────

Problem: Adding new shards requires moving data

Initial Setup (2 shards):
┌──────────────┐ ┌──────────────┐
│  Shard 1     │ │  Shard 2     │
│  Users: 50M  │ │  Users: 50M  │
│  Load: 90%   │ │  Load: 90%   │
│  🚨 Overload │ │  🚨 Overload │
└──────────────┘ └──────────────┘

Decision: Add 2 more shards

Migration Process:
┌──────────────┐ ┌──────────────┐ ┌──────────────┐ ┌──────────────┐
│  Shard 1     │ │  Shard 2     │ │  Shard 3     │ │  Shard 4     │
│              │ │              │ │  (New)       │ │  (New)       │
│  Move 25M ───┼─┼──────────────┼→│ Receive      │ │              │
│  users       │ │  Move 25M ───┼─┼──────────────┼→│ Receive      │
│              │ │  users       │ │              │ │              │
│  Remaining:  │ │  Remaining:  │ │  New:        │ │  New:        │
│  25M users   │ │  25M users   │ │  25M users   │ │  25M users   │
│  Load: 40%   │ │  Load: 40%   │ │  Load: 40%   │ │  Load: 40%   │
└──────────────┘ └──────────────┘ └──────────────┘ └──────────────┘

Challenges:
• Data migration takes time (hours/days)
• Must maintain availability during migration
• Hash function changes (UserID % 2 → UserID % 4)
• Potential downtime or data inconsistency


CHALLENGE 3: JOINS ACROSS SHARDS
─────────────────────────────────

Problem: Get user profile + orders from different shards

User Data:
┌──────────────┐
│  Shard 1     │
│  (User       │
│   Shard)     │
│              │
│  user_id:    │
│  1001        │
│  name: John  │
│  email: ...  │
└──────────────┘

Order Data:
┌──────────────┐
│  Shard 2     │
│  (Order      │
│   Shard)     │
│              │
│  order_id:   │
│  5001        │
│  user_id:    │
│  1001        │
│  amount: $50 │
└──────────────┘

Without Sharding (Simple):
┌─────────────────────────────────┐
│  SELECT *                       │
│  FROM users u                   │
│  JOIN orders o                  │
│    ON u.user_id = o.user_id     │
│  WHERE u.user_id = 1001         │
│                                 │
│  ✅ Single query                │
└─────────────────────────────────┘

With Sharding (Complex):
┌─────────────────────────────────┐
│  Step 1: Query Shard 1          │
│    SELECT * FROM users          │
│    WHERE user_id = 1001         │
│                                 │
│  Step 2: Query Shard 2          │
│    SELECT * FROM orders         │
│    WHERE user_id = 1001         │
│                                 │
│  Step 3: Join in Application    │
│    Merge results in code        │
│                                 │
│  ❌ Multiple queries             │
│  ❌ Application-level join       │
│  ❌ More complex                 │
└─────────────────────────────────┘


CHALLENGE 4: DISTRIBUTED TRANSACTIONS
──────────────────────────────────────

Problem: Update data across multiple shards atomically

Scenario: Transfer money between two users

User A (Shard 1):
┌──────────────┐
│  Balance:    │
│  $1000       │
└──────────────┘
       │
       │ Transfer $100
       ↓
    $900

User B (Shard 2):
┌──────────────┐
│  Balance:    │
│  $500        │
└──────────────┘
       │
       │ Receive $100
       ↓
    $600

Challenge:
• Must update both shards
• Either both succeed or both fail (atomicity)
• Complex distributed transaction protocols needed
• Two-Phase Commit (2PC) or Saga pattern


MITIGATION STRATEGIES
──────────────────────

For Cross-Shard Queries:
✅ Denormalize data (duplicate across shards)
✅ Use caching layer (Redis)
✅ Materialized views

For Re-sharding:
✅ Plan shard count ahead of time
✅ Use consistent hashing
✅ Zero-downtime migration strategies

For Joins:
✅ Keep related data in same shard
✅ Denormalize when possible
✅ Use application-level joins

For Transactions:
✅ Use distributed transaction protocols
✅ Event-driven architecture
✅ Eventual consistency models
```

## 9. Sharding Strategies Deep Dive

### Strategy 1: Hash-Based Sharding

```
shard_id = hash(shard_key) % num_shards
```

**Pros:**
- Even data distribution
- Simple to implement

**Cons:**
- Re-sharding is difficult
- Cannot easily add/remove shards

### Strategy 2: Range-Based Sharding

```
Shard 1: user_id 1 - 1,000,000
Shard 2: user_id 1,000,001 - 2,000,000
```

**Pros:**
- Easy to add new shards
- Range queries are efficient

**Cons:**
- Uneven distribution (hotspots)
- Older shards may have more data

### Strategy 3: Geographic Sharding

```
Shard 1: North America
Shard 2: Europe
Shard 3: Asia
```

**Pros:**
- Low latency (data close to users)
- Compliance with data regulations

**Cons:**
- Uneven distribution
- Geographic hotspots

### Strategy 4: Entity-Based Sharding

```
Shard 1: User data
Shard 2: Order data
Shard 3: Product data
```

**Pros:**
- Logical separation
- Easy to understand

**Cons:**
- Not true sharding (partitioning)
- Doesn't distribute load evenly

## 10. Short Interview Answer (Best Version)

You can say this in an interview:

> When a database grows to millions or hundreds of millions of users, a single database server becomes a bottleneck because all requests hit the same server. To solve this, companies use **database sharding**, which means splitting the data into multiple smaller databases called **shards**.
>
> Each shard stores a subset of the data, for example users 1–1 million in shard 1 and 1–2 million in shard 2.
>
> When a request comes in, the system uses a **shard key** like user ID to determine which shard contains the data. This is typically done using a hash function like `UserID % Number_of_Shards`.
>
> This distributes the load across multiple database servers and allows the system to scale horizontally. However, sharding introduces challenges like cross-shard queries, re-sharding when adding new databases, and difficulty with joins across shards.
>
> Companies like Instagram, Uber, and Amazon use sharding to handle billions of users.

## 11. Key Takeaways

```
┌────────────────────────────────────────────────────────────────────────┐
│                        KEY TAKEAWAYS                                   │
└────────────────────────────────────────────────────────────────────────┘

✅ WHEN TO USE SHARDING
  • Single database cannot handle load
  • Millions/billions of users
  • Vertical scaling limit reached
  • Need horizontal scalability

✅ HOW SHARDING WORKS
  • Split data across multiple databases
  • Use shard key to route requests
  • Each shard handles subset of data
  • Load distributed evenly

✅ BENEFITS
  • Better performance (smaller datasets)
  • Horizontal scalability (add more shards)
  • Load distribution
  • Fault isolation

✅ CHALLENGES
  • Cross-shard queries
  • Re-sharding complexity
  • Joins across shards
  • Distributed transactions

✅ REAL-WORLD USAGE
  • Instagram: User ID based
  • Uber: Geographic based
  • Amazon: Customer ID + Category
  • Facebook: User ID based
  • Netflix: User ID based

✅ ALTERNATIVES
  • Read replicas (for read-heavy workloads)
  • Caching (Redis, Memcached)
  • NoSQL databases (built-in sharding)
  • Database partitioning (logical split)
```

---

This is a critical system design concept for scaling databases to handle massive user bases!
