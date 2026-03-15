# Database Sharding - Overview (Senior Level, Easy English)

Target level: Senior (5-7 years)

## 1) What is Sharding?
Sharding splits a large database into smaller pieces (shards) so data and traffic are distributed. It improves scale and performance.

## 2) Clarifying Questions (Interview Warm-up)
- What is the main shard key (userId, region, tenantId)?
- Are cross-shard joins required?
- Read vs write heavy?
- How fast is data growing?
- Strong consistency required?

## 3) Approaches to Implement Sharding

### Approach A: Range-Based Sharding
What it is:
- Shards own ranges (userId 1-1M).

Pros:
- Simple mapping
- Good for range queries

Cons:
- Hot shards if traffic is skewed

### Approach B: Hash-Based Sharding
What it is:
- Hash(shardKey) to choose shard.

Pros:
- Even distribution
- Reduces hotspots

Cons:
- Range queries are expensive

### Approach C: Directory-Based Sharding
What it is:
- Lookup table maps keys to shards.

Pros:
- Flexible mapping
- Easy to move tenants

Cons:
- Directory becomes a dependency

### Approach D: Geo/Region Sharding
What it is:
- Shard by region for data residency.

Pros:
- Low latency and compliance

Cons:
- Cross-region queries are hard

### Approach E: Tenant-Based Sharding
What it is:
- Each tenant gets its shard or group of shards.

Pros:
- Strong isolation
- Easy billing

Cons:
- Uneven shard sizes if tenants differ

### Approach F: Hybrid Sharding
What it is:
- Combine two strategies (region + hash).

Pros:
- Balance compliance and scale

Cons:
- More complexity

### Approach G: Sharding via Proxy
What it is:
- Proxy routes queries to shards (ShardingSphere, Vitess).

Pros:
- Transparent to app

Cons:
- Proxy adds latency and bottleneck risk

### Approach H: Application-Level Sharding
What it is:
- App code decides shard and connects directly.

Pros:
- Full control

Cons:
- App complexity and coupling

## 4) Common Technologies
- Vitess (MySQL sharding)
- Citus (Postgres sharding)
- ShardingSphere / ProxySQL
- DynamoDB partitions (managed)

## 5) Key Concepts (Interview Must-Know)
- Shard key selection
- Hot shard mitigation
- Rebalancing and resharding
- Global IDs (Snowflake, ULID)
- Cross-shard transactions

## 6) Production Checklist
- Online resharding plan
- Monitoring per shard (CPU, lag, errors)
- Backup/restore per shard
- Schema migration strategy

## 7) Architecture Diagram

### Database Sharding - Hash-Based Sharding

```
┌────────────────────────────────────────────────────────────────────────┐
│                    DATABASE SHARDING SYSTEM                            │
├────────────────────────────────────────────────────────────────────────┤
│                                                                        │
│  ┌──────────────┐     ┌──────────────┐     ┌──────────────┐          │
│  │  App Server  │     │  App Server  │     │  App Server  │          │
│  │  Instance 1  │     │  Instance 2  │     │  Instance 3  │          │
│  └──────┬───────┘     └──────┬───────┘     └──────┬───────┘          │
│         │                    │                    │                   │
│         │  userId: 12345     │                    │                   │
│         │  hash(12345) % 3 = │2                   │                   │
│         │                    │                    │                   │
│         └────────────────────┼────────────────────┘                   │
│                              │                                        │
│                              ▼                                        │
│  ┌──────────────────────────────────────────────────────┐             │
│  │         Shard Router / Query Router                  │             │
│  │         (ProxySQL / Vitess / App Logic)              │             │
│  │                                                      │             │
│  │  Logic:                                              │             │
│  │  shardId = hash(shardKey) % numShards                │             │
│  │  route query to Shard[shardId]                       │             │
│  └──────────────────┬───────────────────────────────────┘             │
│                     │                                                 │
│         ┌───────────┼───────────┐                                     │
│         │           │           │                                     │
│         ▼           ▼           ▼                                     │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐                              │
│  │ Shard 1  │ │ Shard 2  │ │ Shard 3  │                              │
│  │          │ │          │ │          │                              │
│  │ Users:   │ │ Users:   │ │ Users:   │                              │
│  │ hash % 3 │ │ hash % 3 │ │ hash % 3 │                              │
│  │ = 0      │ │ = 1      │ │ = 2      │                              │
│  │          │ │          │ │          │                              │
│  │ 1M rows  │ │ 1M rows  │ │ 1M rows  │                              │
│  └────┬─────┘ └────┬─────┘ └────┬─────┘                              │
│       │            │            │                                     │
│       │            │            │                                     │
│       ▼            ▼            ▼                                     │
│  [Replica]    [Replica]    [Replica]                                 │
│  (Read-only)  (Read-only)  (Read-only)                               │
│                                                                        │
│  ┌──────────────────────────────────────────────────────────┐         │
│  │  KEY FEATURES:                                           │         │
│  │  • Even distribution via hash function                   │         │
│  │  • Horizontal scalability (add more shards)              │         │
│  │  • Each shard handles ~33% of traffic                    │         │
│  │  • Cross-shard queries are expensive (scatter-gather)    │         │
│  │  • Shard key (userId) must be in every query             │         │
│  └──────────────────────────────────────────────────────────┘         │
│                                                                        │
└────────────────────────────────────────────────────────────────────────┘
```

### Range-Based Sharding

```
┌────────────────────────────────────────────────────────────────────────┐
│                    RANGE-BASED SHARDING                                │
├────────────────────────────────────────────────────────────────────────┤
│                                                                        │
│  ┌──────────────────────────────────────────────────────────┐         │
│  │              Shard Router                                │         │
│  │                                                          │         │
│  │  Query: userId = 2,500,000                               │         │
│  │  Logic: Find range containing userId                     │         │
│  │  Result: Route to Shard 3                                │         │
│  └──────────────────┬───────────────────────────────────────┘         │
│                     │                                                 │
│         ┌───────────┼───────────┬───────────────┐                     │
│         │           │           │               │                     │
│         ▼           ▼           ▼               ▼                     │
│  ┌────────────┐ ┌────────────┐ ┌────────────┐ ┌────────────┐         │
│  │  Shard 1   │ │  Shard 2   │ │  Shard 3   │ │  Shard 4   │         │
│  │            │ │            │ │            │ │            │         │
│  │ Users:     │ │ Users:     │ │ Users:     │ │ Users:     │         │
│  │ 1-1M       │ │ 1M-2M      │ │ 2M-3M      │ │ 3M-4M      │         │
│  │            │ │            │ │            │ │            │         │
│  │ Pros:      │ │            │ │            │ │ Cons:      │         │
│  │ • Range    │ │            │ │            │ │ • Hot      │         │
│  │   queries  │ │            │ │            │ │   shards   │         │
│  │   easy     │ │            │ │            │ │ • Skewed   │         │
│  │            │ │            │ │            │ │   load     │         │
│  └────────────┘ └────────────┘ └────────────┘ └────────────┘         │
│                                                                        │
│  Example: Most new users → Shard 4 becomes hotspot                    │
│                                                                        │
└────────────────────────────────────────────────────────────────────────┘
```

### Directory-Based Sharding

```
┌────────────────────────────────────────────────────────────────────────┐
│                    DIRECTORY-BASED SHARDING                            │
├────────────────────────────────────────────────────────────────────────┤
│                                                                        │
│  ┌──────────────────────────────────────────────────────────┐         │
│  │              Shard Router                                │         │
│  │                                                          │         │
│  │  Query: tenantId = "acme-corp"                           │         │
│  │                                                          │         │
│  │  1. Lookup tenantId in Directory                         │         │
│  └──────────────────┬───────────────────────────────────────┘         │
│                     │                                                 │
│                     ▼                                                 │
│  ┌──────────────────────────────────────────────────────────┐         │
│  │          Shard Directory (Lookup Table)                  │         │
│  │          (Redis / SQL / ZooKeeper)                       │         │
│  │  ┌────────────────────────────────────────┐              │         │
│  │  │ tenantId        →  shardId             │              │         │
│  │  ├────────────────────────────────────────┤              │         │
│  │  │ acme-corp       →  shard-2             │              │         │
│  │  │ startup-xyz     →  shard-1             │              │         │
│  │  │ big-enterprise  →  shard-3 (dedicated) │              │         │
│  │  └────────────────────────────────────────┘              │         │
│  └──────────────────┬───────────────────────────────────────┘         │
│                     │                                                 │
│                     │ 2. Route to shard-2                             │
│         ┌───────────┼───────────┐                                     │
│         │           │           │                                     │
│         ▼           ▼           ▼                                     │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐                              │
│  │ Shard 1  │ │ Shard 2  │ │ Shard 3  │                              │
│  │          │ │          │ │          │                              │
│  │ 20 small │ │ 50 mid   │ │ 5 large  │                              │
│  │ tenants  │ │ tenants  │ │ tenants  │                              │
│  │          │ │ (acme-   │ │ (VIP)    │                              │
│  │          │ │  corp)   │ │          │                              │
│  └──────────┘ └──────────┘ └──────────┘                              │
│                                                                        │
│  BENEFITS:                                                            │
│  • Flexible tenant placement (can move tenants easily)                │
│  │  Dedicated shards for large customers                              │
│  • Easy rebalancing without changing hash function                    │
│                                                                        │
│  CONS:                                                                │
│  • Directory becomes a dependency (SPOF if not replicated)            │
│  • Extra lookup on every query                                        │
│                                                                        │
└────────────────────────────────────────────────────────────────────────┘
```

## 8) Quick Interview Answer (30 seconds)
"Sharding splits a large database into smaller shards to scale. Common approaches are range, hash, directory, and geo/tenant-based sharding. Proxy-based sharding hides complexity, while app-level sharding gives more control. The right choice depends on query patterns, hot keys, and data residency needs."
