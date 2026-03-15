# CAP Theorem - The Impossible Triangle

## What is CAP Theorem?

**CAP Theorem** states that in a **distributed system**, you can only guarantee **2 out of 3** properties:

- **C**onsistency
- **A**vailability
- **P**artition Tolerance

Think of it as: **"Pick 2, you can't have all 3"**

```
┌─────────────────────────────────────────────────────────────────────────┐
│                          THE CAP TRIANGLE                                │
└─────────────────────────────────────────────────────────────────────────┘

                         Consistency (C)
                               ●
                              /│\
                             / │ \
                            /  │  \
                           /   │   \
                          /    │    \
                         /     │     \
                        /      │      \
                       /       │       \
                      /        │        \
                     /         │         \
                    /          │          \
                   /           │           \
                  /            │            \
                 /             │             \
                /              │              \
               /               │               \
              /                │                \
             /                 │                 \
            /                  │                  \
           /                   │                   \
          ●────────────────────●────────────────────●
  Availability (A)                        Partition Tolerance (P)


  You can only pick 2:

  ┌─────────────────┬──────────────────────────────────────┐
  │ CA              │ Consistency + Availability           │
  │ (no partition   │ (Traditional RDBMS)                  │
  │  tolerance)     │ MySQL, PostgreSQL (single server)   │
  ├─────────────────┼──────────────────────────────────────┤
  │ CP              │ Consistency + Partition Tolerance    │
  │ (no             │ (Strong consistency, may be down)    │
  │  availability)  │ MongoDB, HBase, Redis                │
  ├─────────────────┼──────────────────────────────────────┤
  │ AP              │ Availability + Partition Tolerance   │
  │ (no             │ (Always available, eventual          │
  │  consistency)   │  consistency)                        │
  │                 │ Cassandra, DynamoDB, Riak            │
  └─────────────────┴──────────────────────────────────────┘
```

---

## Understanding Each Property

### 1. Consistency (C)

**Simple Explanation:** Every read gets the **most recent write**. All nodes see the same data at the same time.

```
┌─────────────────────────────────────────────────────────────────────────┐
│                            CONSISTENCY                                   │
└─────────────────────────────────────────────────────────────────────────┘

CONSISTENT SYSTEM:
──────────────────

User writes: balance = $500

  Write
    │
    ▼
┌────────┐        ┌────────┐        ┌────────┐
│ Node 1 │───────▶│ Node 2 │───────▶│ Node 3 │
│ $500   │        │ $500   │        │ $500   │
└────────┘        └────────┘        └────────┘
    ▲                 ▲                 ▲
    │                 │                 │
    │ Read: $500      │ Read: $500      │ Read: $500
    │                 │                 │
User A             User B             User C

✓ All reads return same value ($500)
✓ Strong consistency


INCONSISTENT SYSTEM:
────────────────────

User writes: balance = $500

  Write
    │
    ▼
┌────────┐        ┌────────┐        ┌────────┐
│ Node 1 │───X────│ Node 2 │───X────│ Node 3 │
│ $500   │        │ $100   │        │ $100   │
└────────┘        └────────┘        └────────┘
    ▲                 ▲                 ▲
    │                 │                 │
    │ Read: $500      │ Read: $100      │ Read: $100
    │                 │                 │
User A             User B             User C

✗ Different reads return different values
✗ Eventual consistency (will sync later)
```

### 2. Availability (A)

**Simple Explanation:** Every request gets a **response** (success or failure), even if some nodes are down.

```
┌─────────────────────────────────────────────────────────────────────────┐
│                           AVAILABILITY                                   │
└─────────────────────────────────────────────────────────────────────────┘

AVAILABLE SYSTEM:
─────────────────

┌────────┐        ┌────────┐        ┌────────┐
│ Node 1 │        │ Node 2 │        │ Node 3 │
│   ✓    │        │   ✓    │        │   💥   │
└────────┘        └────────┘        └────────┘
    ▲                 ▲              (crashed)
    │                 │
    │ Request         │ Request
    │                 │
User A             User B
  │                   │
  │ Response ✓        │ Response ✓

✓ System still responds (uses Node 1 or 2)
✓ No downtime from user perspective


NOT AVAILABLE SYSTEM:
─────────────────────

┌────────┐        ┌────────┐        ┌────────┐
│ Node 1 │        │ Node 2 │        │ Node 3 │
│   💥   │        │   💥   │        │   💥   │
└────────┘        └────────┘        └────────┘
                                   (all crashed)
    ▲
    │ Request
    │
  User
    │
    │ Error: Service Unavailable ❌

✗ System cannot respond
✗ Downtime
```

### 3. Partition Tolerance (P)

**Simple Explanation:** System continues to work even if **network fails** between nodes (network partition).

```
┌─────────────────────────────────────────────────────────────────────────┐
│                      PARTITION TOLERANCE                                 │
└─────────────────────────────────────────────────────────────────────────┘

NETWORK PARTITION (Split Brain):
─────────────────────────────────

Normal state:
┌────────┐ ═══════ ┌────────┐ ═══════ ┌────────┐
│ Node 1 │         │ Node 2 │         │ Node 3 │
│  USA   │         │  USA   │         │ Europe │
└────────┘         └────────┘         └────────┘


Network failure between USA and Europe:
┌────────┐ ═══════ ┌────────┐    X    ┌────────┐
│ Node 1 │         │ Node 2 │         │ Node 3 │
│  USA   │         │  USA   │         │ Europe │
└────────┘         └────────┘         └────────┘
      ╲               ╱                    │
       ╲             ╱                     │
        ╲           ╱                      │
         Partition A                  Partition B
         (can talk)                   (isolated)


PARTITION TOLERANT:
───────────────────
System continues working in both partitions
  • Partition A: Node 1, 2 serve requests
  • Partition B: Node 3 serves requests
  ✓ No downtime

BUT: Must sacrifice either Consistency OR Availability
  • If you want Consistency → Reject requests to Partition B
  • If you want Availability → Allow requests (may be stale data)


NOT PARTITION TOLERANT:
───────────────────────
System stops working when partition happens
  ✗ Entire system goes down
  ✗ Not suitable for distributed systems
```

---

## The Trade-offs: CA, CP, AP

### CA: Consistency + Availability (No Partition Tolerance)

**Simple Explanation:** Works perfectly until network fails. Then the whole system goes down.

```
┌─────────────────────────────────────────────────────────────────────────┐
│                    CA SYSTEM (Traditional Databases)                     │
└─────────────────────────────────────────────────────────────────────────┘

Example: Single-server PostgreSQL, MySQL

┌──────────────────────────────────┐
│      Application Server          │
└────────────┬─────────────────────┘
             │
             ▼
    ┌────────────────┐
    │   Database     │  ← Single server
    │   (Master)     │
    └────────────────┘

Normal operation:
──────────────────
✓ Consistent (single source of truth)
✓ Available (server responds)
✗ No partition tolerance (if server fails, all down)

When server crashes:
────────────────────
┌──────────────────────────────────┐
│      Application Server          │
└────────────┬─────────────────────┘
             │
             ▼
    ┌────────────────┐
    │   Database     │
    │      💥        │  ← Crashed!
    └────────────────┘

✗ Entire system down
✗ Not suitable for distributed systems

Use When:
─────────
• Single data center
• Downtime acceptable
• Don't need geographic distribution
• Traditional enterprise apps

Examples:
─────────
• PostgreSQL (single master)
• MySQL (single master)
• Oracle (single instance)
```

### CP: Consistency + Partition Tolerance (No Availability)

**Simple Explanation:** Data is always consistent, but system may **refuse requests** during network partition.

```
┌─────────────────────────────────────────────────────────────────────────┐
│                         CP SYSTEM (MongoDB, HBase)                       │
└─────────────────────────────────────────────────────────────────────────┘

Example: MongoDB with majority writes

┌────────┐        ┌────────┐        ┌────────┐
│ Node 1 │════════│ Node 2 │════════│ Node 3 │
│ Mongo  │        │ Mongo  │        │ Mongo  │
│ Primary│        │Secondary│       │Secondary│
└────────┘        └────────┘        └────────┘

Write operation:
────────────────
1. Write to Primary (Node 1)
2. Replicate to Node 2 ✓
3. Replicate to Node 3 ✓
4. Acknowledge to client only after majority (2/3) confirm

✓ Consistency guaranteed (majority writes)


Network Partition Occurs:
──────────────────────────

┌────────┐        ┌────────┐    X    ┌────────┐
│ Node 1 │════════│ Node 2 │         │ Node 3 │
│ Primary│        │Secondary│        │Secondary│
└────────┘        └────────┘         └────────┘
     ╲               ╱                    │
      ╲             ╱                     │
       Partition A                   Partition B
       (2 nodes)                     (1 node)
       Can reach                     Cannot reach
       majority ✓                    majority ✗

Partition A (Node 1, 2):
  • Has majority (2/3)
  • Can accept writes ✓
  • Remains available ✓

Partition B (Node 3):
  • No majority (1/3)
  • Rejects writes ❌
  • NOT available ✗

User connected to Node 3:
  Request → "Error: Cannot reach majority" ❌

✓ Consistency maintained (no stale data)
✗ Availability sacrificed (Node 3 unavailable)

Use When:
─────────
• Data correctness critical (financial)
• Can tolerate downtime during partition
• Need strong consistency

Examples:
─────────
• MongoDB (with majority write concern)
• HBase
• Redis (with wait command)
• Consul
• Zookeeper
```

### AP: Availability + Partition Tolerance (No Consistency)

**Simple Explanation:** System is always available, but may return **stale data** during partition.

```
┌─────────────────────────────────────────────────────────────────────────┐
│                  AP SYSTEM (Cassandra, DynamoDB)                         │
└─────────────────────────────────────────────────────────────────────────┘

Example: Cassandra cluster

┌────────┐        ┌────────┐        ┌────────┐
│ Node 1 │════════│ Node 2 │════════│ Node 3 │
│Cassandra│       │Cassandra│       │Cassandra│
└────────┘        └────────┘        └────────┘

Write operation (eventual consistency):
───────────────────────────────────────
1. Write to Node 1 ✓
2. Acknowledge to client immediately
3. Replicate to Node 2, 3 in background

✓ Fast writes (don't wait for replication)


Network Partition Occurs:
──────────────────────────

┌────────┐        ┌────────┐    X    ┌────────┐
│ Node 1 │════════│ Node 2 │         │ Node 3 │
│  $500  │        │  $500  │         │  $500  │
└────────┘        └────────┘         └────────┘
     ╲               ╱                    │
      ╲             ╱                     │
       Partition A                   Partition B
       (Node 1, 2)                   (Node 3)

User A writes to Partition A: balance = $1000
─────────────────────────────────────────────
┌────────┐        ┌────────┐    X    ┌────────┐
│ Node 1 │════════│ Node 2 │         │ Node 3 │
│ $1000  │        │ $1000  │         │  $500  │ ← Still old value
└────────┘        └────────┘         └────────┘

User B reads from Partition B:
───────────────────────────────
  Reads from Node 3 → Returns $500 (stale data!)

✓ Availability maintained (all nodes respond)
✗ Consistency sacrificed (Node 3 has old data)

When partition heals:
─────────────────────
┌────────┐        ┌────────┐        ┌────────┐
│ Node 1 │════════│ Node 2 │════════│ Node 3 │
│ $1000  │        │ $1000  │        │ $1000  │
└────────┘        └────────┘        └────────┘
                                        ▲
                                        │
                    Resolves conflict (last-write-wins)
                    Eventually consistent ✓

Use When:
─────────
• High availability required (99.999%)
• Can tolerate stale data temporarily
• Need to scale globally
• Social media, shopping carts

Examples:
─────────
• Cassandra
• DynamoDB
• Riak
• CouchDB
```

---

## Real-World Scenarios

```
┌─────────────────────────────────────────────────────────────────────────┐
│                       SCENARIO 1: BANK ACCOUNT                           │
└─────────────────────────────────────────────────────────────────────────┘

Requirement: User balance must always be accurate

Choice: CP (Consistency + Partition Tolerance)

Why?
────
• Balance must be correct (consistency critical)
• Can tolerate being unavailable briefly during network issues
• Better to show error than wrong balance

Implementation: MongoDB with majority writes
──────────────────────────────────────────────
writeConcern: { w: "majority" }

Behavior:
─────────
• Network partition → Some nodes unavailable
• User sees: "Service temporarily unavailable"
• Better than: "Your balance is $1000" (when it's actually $500)


┌─────────────────────────────────────────────────────────────────────────┐
│                    SCENARIO 2: SHOPPING CART                             │
└─────────────────────────────────────────────────────────────────────────┘

Requirement: Users can always add items to cart

Choice: AP (Availability + Partition Tolerance)

Why?
────
• Availability critical (users can't wait)
• Temporary inconsistency OK (cart syncs eventually)
• If user adds item, it should succeed

Implementation: DynamoDB
────────────────────────

Behavior:
─────────
• Network partition → Both partitions accept writes
• User A adds "Laptop" → Partition A records it
• User B adds "Mouse" → Partition B records it
• When partition heals → Merge both (Laptop + Mouse)
• Eventual consistency achieved ✓


┌─────────────────────────────────────────────────────────────────────────┐
│                    SCENARIO 3: STOCK TRADING                             │
└─────────────────────────────────────────────────────────────────────────┘

Requirement: Execute trades at exact price

Choice: CP (Consistency + Partition Tolerance)

Why?
────
• Price must be consistent across all nodes
• Wrong price = lost money
• Better to halt trading than trade at wrong price

Implementation: Strongly consistent database + Consensus
─────────────────────────────────────────────────────────

Behavior:
─────────
• Network partition → Trading halted on isolated partition
• User sees: "Trading temporarily unavailable"
• Prevents: Buying at $100 when real price is $150


┌─────────────────────────────────────────────────────────────────────────┐
│                    SCENARIO 4: SOCIAL MEDIA LIKES                        │
└─────────────────────────────────────────────────────────────────────────┘

Requirement: Users can always like posts

Choice: AP (Availability + Partition Tolerance)

Why?
────
• Availability critical (users expect instant feedback)
• Like count can be eventually consistent
• User won't notice if count is 1000 or 1001 temporarily

Implementation: Cassandra
─────────────────────────

Behavior:
─────────
• Network partition → Both partitions accept likes
• Partition A: 500 new likes
• Partition B: 300 new likes
• When heals → Merge: 800 new likes total ✓
• Count may be off by few seconds (acceptable)
```

---

## CAP Theorem in Practice

```
┌─────────────────────────────────────────────────────────────────────────┐
│                    REALITY: P is Not Optional                            │
└─────────────────────────────────────────────────────────────────────────┘

"You can't have CA in a distributed system"

Why? Because network partitions WILL happen:
────────────────────────────────────────────
• Router failure
• Cable cut
• DNS issues
• Firewall misconfiguration
• Data center network issue

So the real choice is: CP or AP?
─────────────────────────────────

When partition happens, choose:

CP → Reject requests (maintain consistency)
  ✓ Data always correct
  ✗ Some users can't access

AP → Accept requests (maintain availability)
  ✓ All users can access
  ✗ Data may be stale temporarily


┌─────────────────────────────────────────────────────────────────────────┐
│                      TUNABLE CONSISTENCY                                 │
└─────────────────────────────────────────────────────────────────────────┘

Modern databases let you CHOOSE per operation!

Cassandra Example:
──────────────────

// Strong consistency (CP behavior)
SELECT * FROM users WHERE id = 123
CONSISTENCY QUORUM;  // Read from majority of nodes

// High availability (AP behavior)
SELECT * FROM users WHERE id = 123
CONSISTENCY ONE;  // Read from any node (may be stale)


DynamoDB Example:
─────────────────

// Strong consistency
getItem({
  TableName: 'Users',
  Key: { userId: 123 },
  ConsistentRead: true  // CP behavior
});

// Eventual consistency
getItem({
  TableName: 'Users',
  Key: { userId: 123 },
  ConsistentRead: false  // AP behavior (default, faster)
});


You can choose per operation:
──────────────────────────────
• Critical operation (payment) → Strong consistency (CP)
• Non-critical operation (profile view) → Eventual consistency (AP)
```

---

## CAP Theorem Visualization: E-commerce System

```
┌─────────────────────────────────────────────────────────────────────────┐
│              E-COMMERCE SYSTEM WITH MIXED CAP CHOICES                    │
└─────────────────────────────────────────────────────────────────────────┘

                    ┌─────────────────┐
                    │  Application    │
                    └────────┬────────┘
                             │
         ┌───────────────────┼───────────────────┐
         │                   │                   │
         ▼                   ▼                   ▼
┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐
│  User Service   │  │ Payment Service │  │  Product Service│
│  (AP - Cassandra)│ │ (CP - PostgreSQL)│ │ (AP - DynamoDB) │
└─────────────────┘  └─────────────────┘  └─────────────────┘

Why different choices?
──────────────────────

User Service (AP):
  • Profile updates non-critical
  • High availability important
  • Stale profile OK temporarily
  Example: "John's email updated to new@example.com"
           → May take 100ms to propagate (acceptable)

Payment Service (CP):
  • Money must be accurate
  • Better to be unavailable than wrong
  • Strong consistency critical
  Example: "Charge $100 to user"
           → Must be exactly $100, no inconsistency allowed

Product Service (AP):
  • Catalog should always load
  • Product info can be stale briefly
  • Availability critical for UX
  Example: "Laptop price: $999"
           → If price changes to $899, OK to show $999 for 1 second


Each service chooses based on business requirements!
```

---

## Database Examples with CAP Classification

```
┌─────────────────────────────────────────────────────────────────────────┐
│                     DATABASE CAP CLASSIFICATION                          │
└─────────────────────────────────────────────────────────────────────────┘

╔════════════════╦═══════════╦══════════════════════════════════════╗
║   Database     ║ CAP Type  ║         Characteristics              ║
╠════════════════╬═══════════╬══════════════════════════════════════╣
║ PostgreSQL     ║ CA        ║ • Single master                      ║
║ (single)       ║           ║ • ACID transactions                  ║
║                ║           ║ • Not partition tolerant             ║
╠════════════════╬═══════════╬══════════════════════════════════════╣
║ MongoDB        ║ CP        ║ • Majority writes                    ║
║                ║           ║ • May reject requests during split   ║
║                ║           ║ • Strong consistency                 ║
╠════════════════╬═══════════╬══════════════════════════════════════╣
║ Redis          ║ CP        ║ • With WAIT command                  ║
║                ║           ║ • Master-replica                     ║
║                ║           ║ • Can ensure replication             ║
╠════════════════╬═══════════╬══════════════════════════════════════╣
║ HBase          ║ CP        ║ • Single master per region           ║
║                ║           ║ • Strong consistency                 ║
║                ║           ║ • May be unavailable during failure  ║
╠════════════════╬═══════════╬══════════════════════════════════════╣
║ Cassandra      ║ AP        ║ • Multi-master                       ║
║                ║           ║ • Tunable consistency                ║
║                ║           ║ • Always available                   ║
╠════════════════╬═══════════╬══════════════════════════════════════╣
║ DynamoDB       ║ AP        ║ • Multi-master                       ║
║                ║           ║ • Eventual consistency default       ║
║                ║           ║ • 99.99% availability                ║
╠════════════════╬═══════════╬══════════════════════════════════════╣
║ Riak           ║ AP        ║ • Masterless                         ║
║                ║           ║ • Always accepts writes              ║
║                ║           ║ • Conflict resolution                ║
╠════════════════╬═══════════╬══════════════════════════════════════╣
║ CouchDB        ║ AP        ║ • Multi-master replication           ║
║                ║           ║ • Offline-first                      ║
║                ║           ║ • Eventual consistency               ║
╚════════════════╩═══════════╩══════════════════════════════════════╝


Note: Many databases are TUNABLE
────────────────────────────────
• Cassandra can behave as CP with QUORUM reads/writes
• MongoDB can behave as AP with eventual consistency reads
• Choice is often per-operation, not database-wide
```

---

## Common Misconceptions

```
┌─────────────────────────────────────────────────────────────────────────┐
│                       CAP THEOREM MISCONCEPTIONS                         │
└─────────────────────────────────────────────────────────────────────────┘

❌ MYTH 1: "You must choose 2 permanently"
✓ TRUTH: You can choose per operation
  Example: Strong consistency for payments (CP)
           Eventual consistency for likes (AP)


❌ MYTH 2: "CA systems exist in distributed environment"
✓ TRUTH: In distributed systems, partitions WILL happen
  You can't avoid P (partition tolerance)
  Real choice: CP or AP


❌ MYTH 3: "AP means inconsistent data forever"
✓ TRUTH: AP means EVENTUAL consistency
  Data becomes consistent after partition heals
  Usually takes milliseconds to seconds


❌ MYTH 4: "CP means always unavailable"
✓ TRUTH: CP means unavailable ONLY during partition
  99.9% of time, network is fine → CP system is available
  It's a trade-off for when things go wrong


❌ MYTH 5: "CAP is binary (all or nothing)"
✓ TRUTH: Modern systems are tunable
  You can choose consistency level per request
  Example: QUORUM vs ONE in Cassandra
```

---

## System Design Interview Answer

**Question: "Explain CAP theorem and how would you apply it?"**

**Answer:**

"CAP theorem states that in a distributed system, you can only guarantee 2 out of 3 properties: Consistency, Availability, and Partition tolerance.

**The 3 Properties:**
- **Consistency**: All nodes see the same data at the same time
- **Availability**: Every request gets a response (no timeouts)
- **Partition Tolerance**: System works even if network fails between nodes

**The Trade-off:**
In reality, partitions WILL happen in distributed systems (network failures are inevitable), so we can't ignore P. The real choice is between CP and AP:

- **CP (Consistency + Partition Tolerance)**: MongoDB, HBase
  - Choose when data correctness is critical
  - Example: Banking, stock trading
  - During partition: Reject requests to maintain consistency

- **AP (Availability + Partition Tolerance)**: Cassandra, DynamoDB
  - Choose when high availability is critical
  - Example: Shopping cart, social media likes
  - During partition: Accept requests, sync data later (eventual consistency)

**My Approach:**
I choose based on business requirements per service:
- Payment service: CP (money must be exact)
- User profile: AP (can tolerate brief staleness)
- Product catalog: AP (availability more important than perfect sync)

Modern databases like Cassandra let you tune consistency per operation, giving you flexibility to choose CP or AP behavior as needed."

---

## Key Takeaways

✓ **CAP is a trade-off**: You can only pick 2 out of 3

✓ **P is mandatory**: In distributed systems, partitions will happen

✓ **Real choice: CP or AP**: Consistency vs Availability during partition

✓ **Context matters**: Choose based on business requirements

✓ **Tunable**: Modern databases let you choose per operation

✓ **Not permanent**: System behavior can change based on operation type

✓ **Eventual consistency**: AP systems become consistent after partition heals (usually fast)
