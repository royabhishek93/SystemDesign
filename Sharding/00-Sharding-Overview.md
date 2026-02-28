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

## 7) Quick Interview Answer (30 seconds)
"Sharding splits a large database into smaller shards to scale. Common approaches are range, hash, directory, and geo/tenant-based sharding. Proxy-based sharding hides complexity, while app-level sharding gives more control. The right choice depends on query patterns, hot keys, and data residency needs."
