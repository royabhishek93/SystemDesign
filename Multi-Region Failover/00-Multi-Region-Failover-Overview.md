# Multi-Region Failover - Overview (Senior Level, Easy English)

Target level: Senior (5-7 years)

## 1) What is Multi-Region Failover?
It means your system can keep serving traffic even if an entire region goes down. Traffic is shifted to another region automatically or manually.

## 2) Clarifying Questions (Interview Warm-up)
- Required downtime (RTO) and data loss (RPO)?
- Is the system read-heavy or write-heavy?
- Do we need active-active or active-passive?
- Can users tolerate stale data during failover?
- Any data residency constraints?

## 3) Approaches to Implement Multi-Region Failover

### Approach A: Active-Active
What it is:
- Multiple regions serve traffic at the same time.

Pros:
- Lowest latency
- Highest availability

Cons:
- Data consistency is hard
- More expensive

### Approach B: Active-Passive
What it is:
- One region is primary, one is standby.

Pros:
- Simpler data consistency
- Lower cost

Cons:
- Failover takes time
- Idle capacity

### Approach C: Global Load Balancer + Health Checks
What it is:
- A global LB routes to healthy regions.

Pros:
- Automated failover
- Simple for stateless services

Cons:
- Data layer still needs replication

### Approach D: DNS Failover
What it is:
- DNS switches traffic to another region when health checks fail.

Pros:
- Easy to set up
- Works across clouds

Cons:
- DNS cache delays
- Slow failover

### Approach E: Warm Standby
What it is:
- Secondary region runs at reduced capacity.

Pros:
- Faster recovery than cold standby
- Lower cost than active-active

Cons:
- Still not instant
- Needs pre-planned scaling

### Approach F: Cold Standby
What it is:
- Secondary region is mostly off until failure.

Pros:
- Lowest cost

Cons:
- Slowest recovery
- Risky for critical systems

### Approach G: Data Layer Active-Active
What it is:
- Multi-region database writes.

Pros:
- No single data region

Cons:
- Conflict resolution required
- Complex to operate

### Approach H: Queue-Based Failover
What it is:
- Queue stores writes when a region is down; replays later.

Pros:
- Protects against data loss

Cons:
- Delayed consistency
- Extra complexity

## 4) Common Technologies
- Global routing: Route 53, CloudFront, Azure Front Door
- Databases: Aurora Global, Cosmos DB, Spanner
- Replication: Kafka MirrorMaker, Debezium

## 5) Key Concepts (Interview Must-Know)
- RTO (Recovery Time Objective)
- RPO (Recovery Point Objective)
- Split-brain prevention
- Data replication lag

## 6) Production Checklist
- Regular failover drills
- Automated health checks + alerting
- Runbooks for manual failover
- Data consistency validation

## 7) Quick Interview Answer (30 seconds)
"Multi-region failover keeps the system up if a region goes down. Options include active-active, active-passive, and warm/cold standby. A global load balancer or DNS can shift traffic, but the data layer must also replicate. The right choice depends on RTO/RPO, consistency, and cost."
