# Event Sourcing - Complete Event History as Source of Truth

## What is Event Sourcing?

**Event Sourcing** is a pattern where you store **every change** to application state as a **sequence of events**, instead of just storing the current state.

Think of it like a **bank statement**: Instead of just showing your current balance ($500), it shows every transaction (deposit $100, withdraw $50, etc.) that led to that balance.

```
┌─────────────────────────────────────────────────────────────────────────┐
│              TRADITIONAL vs EVENT SOURCING                               │
└─────────────────────────────────────────────────────────────────────────┘

TRADITIONAL (State-Based):
──────────────────────────
Store only CURRENT state

Database:
┌──────────────────────────────────────┐
│ users table                          │
├──────────────────────────────────────┤
│ user_id │ name  │ email    │ balance│
│ 1       │ Alice │ a@x.com  │ $500  │
└──────────────────────────────────────┘

✓ Simple
✗ Lost history (how did balance become $500?)
✗ Can't audit (what happened?)
✗ Can't replay (can't recreate past states)


EVENT SOURCING (Event-Based):
──────────────────────────────
Store every CHANGE (event)

Event Store:
┌──────────────────────────────────────────────────────────────┐
│ events table                                                 │
├──────────────────────────────────────────────────────────────┤
│ event_id │ user_id │ event_type        │ data       │ time  │
│ 1        │ 1       │ UserCreated       │ {name:     │ 10:00 │
│          │         │                   │  "Alice"}  │       │
│ 2        │ 1       │ EmailChanged      │ {email:    │ 10:05 │
│          │         │                   │  "a@x.com"}│       │
│ 3        │ 1       │ MoneyDeposited    │ {amount:   │ 10:10 │
│          │         │                   │  $100}     │       │
│ 4        │ 1       │ MoneyWithdrawn    │ {amount:   │ 10:15 │
│          │         │                   │  $50}      │       │
│ 5        │ 1       │ MoneyDeposited    │ {amount:   │ 10:20 │
│          │         │                   │  $450}     │       │
└──────────────────────────────────────────────────────────────┘

To get current state: Replay all events
  UserCreated → Balance: $0
  MoneyDeposited $100 → Balance: $100
  MoneyWithdrawn $50 → Balance: $50
  MoneyDeposited $450 → Balance: $500 ✓

✓ Complete history
✓ Full audit trail
✓ Can replay to any point in time
✓ Can answer "what was balance at 10:12?" (it was $100)
✗ More complex
✗ Need to replay events (can be slow)
```

---

## Core Concepts

```
┌─────────────────────────────────────────────────────────────────────────┐
│                         EVENT SOURCING FLOW                              │
└─────────────────────────────────────────────────────────────────────────┘

Step-by-step flow:

1. COMMAND
   User action: "Withdraw $50"
   │
   ▼
2. VALIDATE
   Check business rules
   • Balance >= $50?
   • Account active?
   │
   ▼
3. CREATE EVENT
   "MoneyWithdrawn" event
   │
   ▼
4. SAVE TO EVENT STORE
   Append event (never update!)
   │
   ▼
5. APPLY TO AGGREGATE
   Update in-memory state
   │
   ▼
6. PUBLISH EVENT
   Notify other systems


Visual Representation:
──────────────────────

┌──────────────┐       ┌──────────────┐       ┌──────────────┐
│   Command    │       │  Aggregate   │       │ Event Store  │
│              │       │  (Business   │       │ (Database)   │
│ "Withdraw    │──────▶│   Logic)     │──────▶│              │
│   $50"       │       │              │       │  Event #5:   │
└──────────────┘       │ - Validate   │       │  Money       │
                       │ - Create     │       │  Withdrawn   │
                       │   Event      │       │  $50         │
                       └──────┬───────┘       └──────────────┘
                              │
                              │ Publish
                              ▼
                       ┌──────────────┐
                       │ Event Bus    │
                       │ (Kafka)      │
                       └──────┬───────┘
                              │
              ┌───────────────┼───────────────┐
              │               │               │
              ▼               ▼               ▼
        ┌──────────┐    ┌──────────┐    ┌──────────┐
        │Email     │    │Analytics │    │Fraud     │
        │Service   │    │Service   │    │Detection │
        └──────────┘    └──────────┘    └──────────┘
```

---

## Key Components

### 1. Events (Immutable Facts)

```
┌─────────────────────────────────────────────────────────────────────────┐
│                            EVENTS                                        │
└─────────────────────────────────────────────────────────────────────────┘

Events are PAST TENSE (something that happened)

Good Event Names:
─────────────────
✓ OrderPlaced
✓ PaymentProcessed
✓ ItemAddedToCart
✓ UserRegistered
✓ EmailChanged

Bad Event Names:
────────────────
✗ PlaceOrder (command, not event)
✗ ProcessPayment (action, not fact)
✗ UpdateUser (vague)


Event Structure:
────────────────

{
  "eventId": "evt_12345",
  "eventType": "MoneyWithdrawn",
  "aggregateId": "user_1",        // Which entity
  "aggregateType": "User",
  "data": {                       // Event payload
    "amount": 50.00,
    "currency": "USD",
    "reason": "ATM withdrawal"
  },
  "timestamp": "2024-03-15T10:15:00Z",
  "version": 5,                   // Event sequence number
  "metadata": {
    "userId": "user_1",
    "ipAddress": "192.168.1.1",
    "userAgent": "Mozilla/5.0"
  }
}

Events are IMMUTABLE:
─────────────────────
✗ Never update events
✗ Never delete events
✓ If mistake, create compensating event

Example:
  Wrong: DELETE FROM events WHERE event_id = 123;
  Right: INSERT INTO events (MoneyDepositedInError, -$50);
```

### 2. Event Store (Append-Only Database)

```
┌─────────────────────────────────────────────────────────────────────────┐
│                          EVENT STORE                                     │
└─────────────────────────────────────────────────────────────────────────┘

Specialized database for events

Properties:
───────────
✓ Append-only (no updates or deletes)
✓ Ordered by time
✓ Optimized for sequential reads
✓ Supports event replay

Schema:
───────

CREATE TABLE events (
    event_id        VARCHAR(36) PRIMARY KEY,
    aggregate_id    VARCHAR(36) NOT NULL,
    aggregate_type  VARCHAR(50) NOT NULL,
    event_type      VARCHAR(100) NOT NULL,
    event_data      JSONB NOT NULL,
    version         BIGINT NOT NULL,
    timestamp       TIMESTAMP NOT NULL,
    metadata        JSONB,

    -- Ensure sequential version numbers
    UNIQUE (aggregate_id, version)
);

-- Index for fast replay
CREATE INDEX idx_aggregate ON events(aggregate_id, version);


Example Data:
─────────────

aggregate_id: "order_123"
┌─────────┬──────────────────┬─────────┬───────────────────┐
│ version │ event_type       │ time    │ data              │
├─────────┼──────────────────┼─────────┼───────────────────┤
│ 1       │ OrderCreated     │ 10:00   │ {items: [...]}    │
│ 2       │ ItemAdded        │ 10:05   │ {item: "Laptop"}  │
│ 3       │ PaymentProcessed │ 10:10   │ {amount: 999}     │
│ 4       │ OrderShipped     │ 10:30   │ {tracking: "..."}│
│ 5       │ OrderDelivered   │ 12:00   │ {}                │
└─────────┴──────────────────┴─────────┴───────────────────┘

To get current state: Read events 1-5 and apply


Event Store Products:
──────────────────────
• EventStore DB (specialized)
• PostgreSQL (with append-only table)
• Apache Kafka (streaming events)
• AWS DynamoDB Streams
```

### 3. Aggregates (Business Logic)

```
┌─────────────────────────────────────────────────────────────────────────┐
│                           AGGREGATES                                     │
└─────────────────────────────────────────────────────────────────────────┘

Aggregate = Entity + Business Rules + Event Handling

Example: BankAccount Aggregate

public class BankAccount {
    private String accountId;
    private BigDecimal balance;
    private String status;
    private List<Event> uncommittedEvents = new ArrayList<>();

    // Current state (built from events)
    private int version = 0;

    // COMMAND: Try to withdraw
    public void withdraw(BigDecimal amount) {
        // BUSINESS RULES (validation)
        if (status.equals("CLOSED")) {
            throw new AccountClosedException();
        }
        if (balance.compareTo(amount) < 0) {
            throw new InsufficientFundsException();
        }
        if (amount.compareTo(BigDecimal.ZERO) <= 0) {
            throw new InvalidAmountException();
        }

        // CREATE EVENT (if validation passes)
        MoneyWithdrawnEvent event = new MoneyWithdrawnEvent(
            accountId,
            amount,
            Instant.now()
        );

        // APPLY EVENT (update state)
        apply(event);

        // SAVE FOR PERSISTENCE
        uncommittedEvents.add(event);
    }

    // APPLY EVENT (change state)
    private void apply(MoneyWithdrawnEvent event) {
        this.balance = this.balance.subtract(event.getAmount());
        this.version++;
    }

    // LOAD FROM HISTORY
    public void loadFromHistory(List<Event> events) {
        for (Event event : events) {
            if (event instanceof AccountCreatedEvent) {
                apply((AccountCreatedEvent) event);
            } else if (event instanceof MoneyDepositedEvent) {
                apply((MoneyDepositedEvent) event);
            } else if (event instanceof MoneyWithdrawnEvent) {
                apply((MoneyWithdrawnEvent) event);
            }
            // ... handle other event types
        }
    }

    private void apply(AccountCreatedEvent event) {
        this.accountId = event.getAccountId();
        this.balance = BigDecimal.ZERO;
        this.status = "ACTIVE";
        this.version++;
    }

    private void apply(MoneyDepositedEvent event) {
        this.balance = this.balance.add(event.getAmount());
        this.version++;
    }

    // GET UNCOMMITTED EVENTS
    public List<Event> getUncommittedEvents() {
        return uncommittedEvents;
    }

    public void markEventsAsCommitted() {
        uncommittedEvents.clear();
    }
}


Flow:
─────

1. Load aggregate from events:
   List<Event> history = eventStore.getEvents("account_1");
   BankAccount account = new BankAccount();
   account.loadFromHistory(history);  // Replay events

2. Execute command:
   account.withdraw(50.00);  // Creates event internally

3. Save new events:
   List<Event> newEvents = account.getUncommittedEvents();
   eventStore.save(newEvents);
   account.markEventsAsCommitted();
```

---

## Event Sourcing in Action: E-commerce Order

```
┌─────────────────────────────────────────────────────────────────────────┐
│                    ORDER LIFECYCLE WITH EVENTS                           │
└─────────────────────────────────────────────────────────────────────────┘

Timeline of events for order_123:

t=0     Event 1: OrderCreated
        ──────────────────────────────────
        {
          "orderId": "order_123",
          "userId": "user_456",
          "items": [
            { "product": "Laptop", "price": 999, "qty": 1 }
          ],
          "total": 999
        }

        Current State:
        • Order ID: order_123
        • Status: PENDING
        • Total: $999
        • Items: 1 laptop


t=300   Event 2: ItemAddedToOrder
        ──────────────────────────────────
        {
          "orderId": "order_123",
          "item": { "product": "Mouse", "price": 25, "qty": 1 }
        }

        Current State:
        • Order ID: order_123
        • Status: PENDING
        • Total: $1024 (999 + 25)
        • Items: 1 laptop, 1 mouse


t=600   Event 3: PaymentProcessed
        ──────────────────────────────────
        {
          "orderId": "order_123",
          "amount": 1024,
          "paymentMethod": "CREDIT_CARD",
          "transactionId": "txn_789"
        }

        Current State:
        • Order ID: order_123
        • Status: PAID
        • Total: $1024
        • Payment: txn_789


t=1800  Event 4: OrderShipped
        ──────────────────────────────────
        {
          "orderId": "order_123",
          "carrier": "FedEx",
          "trackingNumber": "1Z999AA10123456784"
        }

        Current State:
        • Order ID: order_123
        • Status: SHIPPED
        • Tracking: 1Z999AA10123456784


t=86400 Event 5: OrderDelivered
        ──────────────────────────────────
        {
          "orderId": "order_123",
          "deliveredAt": "2024-03-16T10:00:00Z",
          "signedBy": "John Doe"
        }

        Current State:
        • Order ID: order_123
        • Status: DELIVERED ✓


Now you can answer questions:
─────────────────────────────
• What was the order total at t=400? → $1024 (replay events 1-2)
• When was payment processed? → t=600
• What items were originally ordered? → 1 laptop (event 1)
• Full audit trail? → All events 1-5 ✓
```

---

## Snapshots (Optimization)

```
┌─────────────────────────────────────────────────────────────────────────┐
│                      SNAPSHOTS (Performance)                             │
└─────────────────────────────────────────────────────────────────────────┘

Problem: Replaying 1 million events is SLOW!

Solution: Periodically save SNAPSHOTS (current state)

Without Snapshot:
─────────────────
Load aggregate → Replay 1,000,000 events → Get current state
Time: 10 seconds ❌

With Snapshot:
──────────────
Load snapshot (event #999,000) → Replay last 1,000 events → Current state
Time: 100ms ✓


Snapshot Structure:
───────────────────

┌──────────────────────────────────────────────────────────┐
│ Event Store                                              │
├──────────────────────────────────────────────────────────┤
│ Events 1-999,000 ─────────────┐                         │
│                               │                         │
│                               ▼                         │
│                         ┌─────────────┐                 │
│                         │ Snapshot    │                 │
│                         │ at v999,000 │                 │
│                         │             │                 │
│                         │ balance:    │                 │
│                         │  $50,000    │                 │
│                         │ status:     │                 │
│                         │  ACTIVE     │                 │
│                         └─────────────┘                 │
│                               │                         │
│ Events 999,001-1,000,000 ◀────┘                         │
│ (only need to replay these)                             │
└──────────────────────────────────────────────────────────┘

Loading Process:
────────────────
1. Load latest snapshot (if exists)
2. Load events AFTER snapshot
3. Apply events to snapshot state

Code:
─────
public BankAccount load(String accountId) {
    // Try to load snapshot
    Snapshot snapshot = snapshotStore.getLatest(accountId);

    BankAccount account;
    int fromVersion;

    if (snapshot != null) {
        account = snapshot.getState();  // Deserialize
        fromVersion = snapshot.getVersion() + 1;
    } else {
        account = new BankAccount(accountId);
        fromVersion = 1;
    }

    // Load events after snapshot
    List<Event> events = eventStore.getEvents(
        accountId,
        fromVersion,
        Integer.MAX_VALUE
    );

    // Apply remaining events
    account.loadFromHistory(events);

    return account;
}

Snapshot Strategy:
──────────────────
• Every N events (e.g., every 100 events)
• Time-based (e.g., daily)
• On-demand (when aggregate loads slowly)

Snapshots are OPTIONAL (events are still source of truth)
```

---

## Projections (Read Models)

```
┌─────────────────────────────────────────────────────────────────────────┐
│                    PROJECTIONS (Query Optimization)                      │
└─────────────────────────────────────────────────────────────────────────┘

Problem: Event store optimized for WRITES, not complex QUERIES

Solution: Build PROJECTIONS (read-optimized views)

Architecture:
─────────────

┌──────────────┐         ┌──────────────┐
│ Event Store  │────────▶│ Event Bus    │
│ (Write)      │ publish │              │
└──────────────┘         └──────┬───────┘
                                │
                    ┌───────────┼───────────┐
                    │           │           │
                    ▼           ▼           ▼
            ┌──────────┐ ┌──────────┐ ┌──────────┐
            │OrderList │ │UserProfile│ │Analytics │
            │Projection│ │Projection │ │Projection│
            └──────────┘ └──────────┘ └──────────┘
                 │            │            │
                 ▼            ▼            ▼
            ┌──────────┐ ┌──────────┐ ┌──────────┐
            │PostgreSQL│ │ MongoDB  │ │Elasticsearch│
            └──────────┘ └──────────┘ └──────────┘


Example: OrderListProjection
─────────────────────────────

Purpose: Show user's orders (optimized for queries)

Event Handlers:
───────────────

@EventHandler
public void on(OrderCreatedEvent event) {
    OrderListItem item = new OrderListItem();
    item.setOrderId(event.getOrderId());
    item.setUserId(event.getUserId());
    item.setTotal(event.getTotal());
    item.setStatus("PENDING");
    item.setCreatedAt(event.getTimestamp());

    orderListRepo.save(item);
}

@EventHandler
public void on(OrderShippedEvent event) {
    OrderListItem item = orderListRepo.findById(event.getOrderId());
    item.setStatus("SHIPPED");
    item.setTrackingNumber(event.getTrackingNumber());

    orderListRepo.save(item);
}

@EventHandler
public void on(OrderDeliveredEvent event) {
    OrderListItem item = orderListRepo.findById(event.getOrderId());
    item.setStatus("DELIVERED");

    orderListRepo.save(item);
}


Projection Table (PostgreSQL):
───────────────────────────────

CREATE TABLE order_list (
    order_id VARCHAR(36) PRIMARY KEY,
    user_id VARCHAR(36) NOT NULL,
    total DECIMAL(10,2),
    status VARCHAR(50),
    tracking_number VARCHAR(100),
    created_at TIMESTAMP,
    updated_at TIMESTAMP
);

CREATE INDEX idx_user ON order_list(user_id);


Now queries are FAST:
──────────────────────

// Get user's orders (fast query on projection)
SELECT * FROM order_list WHERE user_id = 'user_456' ORDER BY created_at DESC;

// No need to replay events!


Multiple Projections:
─────────────────────

Same events → Different projections

Event: OrderPlaced
│
├──▶ OrderListProjection (table view)
├──▶ OrderAnalyticsProjection (metrics)
├──▶ OrderSearchProjection (Elasticsearch)
└──▶ UserActivityProjection (user timeline)

Each projection optimized for different query patterns!


Rebuilding Projections:
───────────────────────

If projection corrupted or schema changes:
1. Delete projection data
2. Replay ALL events from event store
3. Projection rebuilds automatically

DROP TABLE order_list;
CREATE TABLE order_list (...);

// Replay events
replayAllEvents(OrderCreatedEvent, OrderShippedEvent, ...);
```

---

## Benefits of Event Sourcing

```
┌─────────────────────────────────────────────────────────────────────────┐
│                    BENEFITS OF EVENT SOURCING                            │
└─────────────────────────────────────────────────────────────────────────┘

1. COMPLETE AUDIT TRAIL
───────────────────────
Every change is recorded with timestamp, user, reason

Example: "Who changed the price from $100 to $90?"
  → Event: PriceChanged by user_123 at 2024-03-15T10:00:00Z


2. TIME TRAVEL (Temporal Queries)
──────────────────────────────────
Answer "What was the state at time X?"

Example: "What was user's balance on March 1?"
  → Replay events up to March 1


3. BUG FIX RECOVERY
───────────────────
If bug corrupted data, fix code and replay events

Example: Bug calculated tax wrong
  → Fix tax calculation logic
  → Replay all OrderCreated events
  → Projections rebuilt with correct tax ✓


4. BUSINESS INTELLIGENCE
────────────────────────
Analyze historical trends

Example: "How many orders were cancelled in last 6 months?"
  → Query OrderCancelled events


5. EVENT-DRIVEN INTEGRATION
────────────────────────────
Other systems listen to events

Example: OrderShipped event
  → Email service sends notification
  → Analytics tracks shipment
  → Fraud detection checks pattern


6. DEBUG & TROUBLESHOOT
───────────────────────
Reproduce exact state that caused bug

Example: "Why did payment fail for order_123?"
  → Replay events for order_123
  → See exact sequence that led to failure


7. COMPLIANCE (GDPR, SOX, HIPAA)
────────────────────────────────
Immutable audit log for regulatory requirements

Example: "Prove we deleted user data"
  → Event: UserDataDeleted at 2024-03-15T10:00:00Z ✓
```

---

## Challenges & Solutions

```
┌─────────────────────────────────────────────────────────────────────────┐
│                   EVENT SOURCING CHALLENGES                              │
└─────────────────────────────────────────────────────────────────────────┘

1. EVENTUAL CONSISTENCY
───────────────────────

Challenge: Projections lag behind events

Event: OrderCreated (t=0)
  ↓
Event stored ✓ (t=5ms)
  ↓
Projection updated (t=100ms) ← Delay!

User queries immediately: "Where's my order?" → Not found yet!

Solution:
• Return 202 Accepted (not 201 Created)
• Provide order ID immediately
• Poll or WebSocket for updates
• Show "Processing..." state


2. EVENT SCHEMA EVOLUTION
──────────────────────────

Challenge: Event structure changes over time

Version 1 (old):
{
  "eventType": "UserRegistered",
  "data": {
    "name": "Alice"
  }
}

Version 2 (new):
{
  "eventType": "UserRegistered",
  "data": {
    "firstName": "Alice",
    "lastName": "Smith"
  }
}

Old events don't have firstName/lastName!

Solutions:
──────────

A) UPCASTING (convert old events on read)
public UserRegisteredEvent upcast(Event oldEvent) {
    if (oldEvent.version == 1) {
        String[] parts = oldEvent.data.name.split(" ");
        return new UserRegisteredEvent(
            parts[0],  // firstName
            parts[1]   // lastName
        );
    }
    return oldEvent;
}

B) VERSIONED EVENT TYPES
• UserRegisteredV1
• UserRegisteredV2
Handle both versions in event handler

C) WEAK SCHEMA (use optional fields)
{
  "name": "Alice",           // optional (v1)
  "firstName": "Alice",      // optional (v2)
  "lastName": "Smith"        // optional (v2)
}


3. QUERYING EVENTS
──────────────────

Challenge: Complex queries slow on event store

Query: "Show all users with balance > $1000"
  → Must replay events for ALL users ❌ Slow!

Solution: Use PROJECTIONS
  → Maintain "UserBalanceProjection" table
  → Query projection (fast) ✓


4. EVENT STORE SIZE
───────────────────

Challenge: Events grow forever (TBs of data)

Solution A: SNAPSHOTS
  → Reduce replay time

Solution B: ARCHIVING
  → Move old events to cold storage
  → Keep recent events (e.g., last 1 year)

Solution C: AGGREGATE LIFESPAN
  → Delete events for closed accounts after N years
  → Keep final snapshot


5. GDPR (Right to be Forgotten)
───────────────────────────────

Challenge: Events are immutable, can't delete user data

Problem: User requests data deletion
  → But events contain their data!

Solutions:
──────────

A) CRYPTO SHREDDING
• Store sensitive data encrypted
• Delete encryption key
• Events remain, but data unreadable

{
  "eventType": "UserRegistered",
  "data": {
    "encryptedData": "xyz...",  // encrypted with user's key
    "keyId": "key_123"           // store key separately
  }
}

Delete key_123 → Data irretrievable ✓

B) FORGET EVENT
{
  "eventType": "UserDataForgotten",
  "userId": "user_123",
  "timestamp": "2024-03-15T10:00:00Z"
}

Projections handle this event:
• Delete user from all projections
• Mark user as forgotten in event store


6. DEBUGGING COMPLEXITY
───────────────────────

Challenge: Hard to understand system state

Problem: "Why is order status = CANCELLED?"
  → Must trace through 20 events

Solution:
• Good logging
• Event visualization tools
• Replay events in debugger
```

---

## Real-World Examples

```
┌─────────────────────────────────────────────────────────────────────────┐
│                    COMPANIES USING EVENT SOURCING                        │
└─────────────────────────────────────────────────────────────────────────┘

1. BANKING / FINANCE
────────────────────
Why: Complete audit trail, compliance

Events:
• MoneyDeposited
• MoneyWithdrawn
• InterestApplied
• AccountClosed

Benefit: Can prove exact balance at any time


2. E-COMMERCE (AMAZON)
──────────────────────
Why: Order lifecycle tracking

Events:
• OrderPlaced
• PaymentProcessed
• OrderShipped
• OrderDelivered
• OrderReturned

Benefit: Full order history for customer support


3. RIDE SHARING (UBER)
──────────────────────
Why: Track trip lifecycle, surge pricing

Events:
• RideRequested
• DriverAssigned
• RideStarted
• RideCompleted
• PaymentProcessed

Benefit: Dispute resolution (replay trip events)


4. HEALTHCARE
─────────────
Why: Patient treatment history, compliance

Events:
• PatientAdmitted
• MedicationAdministered
• TestOrdered
• DiagnosisRecorded
• PatientDischarged

Benefit: Complete medical history, audit trail


5. SUPPLY CHAIN
───────────────
Why: Track product movement

Events:
• ProductManufactured
• ProductShipped
• ProductReceivedAtWarehouse
• ProductSoldToCustomer

Benefit: Full traceability (food safety, recalls)
```

---

## Code Example: Complete Implementation

```java
┌─────────────────────────────────────────────────────────────────────────┐
│                    FULL EVENT SOURCING EXAMPLE                           │
└─────────────────────────────────────────────────────────────────────────┘

// 1. EVENTS
public class Event {
    private String eventId;
    private String aggregateId;
    private String eventType;
    private Instant timestamp;
    private int version;
}

public class AccountCreatedEvent extends Event {
    private String accountId;
    private String ownerName;
}

public class MoneyDepositedEvent extends Event {
    private BigDecimal amount;
}

public class MoneyWithdrawnEvent extends Event {
    private BigDecimal amount;
}

// 2. AGGREGATE
public class BankAccount {
    private String accountId;
    private BigDecimal balance = BigDecimal.ZERO;
    private String status = "ACTIVE";
    private int version = 0;
    private List<Event> uncommittedEvents = new ArrayList<>();

    // COMMAND
    public void createAccount(String accountId, String ownerName) {
        if (this.accountId != null) {
            throw new AccountAlreadyExistsException();
        }

        AccountCreatedEvent event = new AccountCreatedEvent(
            UUID.randomUUID().toString(),
            accountId,
            ownerName,
            Instant.now(),
            ++version
        );

        apply(event);
        uncommittedEvents.add(event);
    }

    public void deposit(BigDecimal amount) {
        if (amount.compareTo(BigDecimal.ZERO) <= 0) {
            throw new InvalidAmountException();
        }

        MoneyDepositedEvent event = new MoneyDepositedEvent(
            UUID.randomUUID().toString(),
            accountId,
            amount,
            Instant.now(),
            ++version
        );

        apply(event);
        uncommittedEvents.add(event);
    }

    public void withdraw(BigDecimal amount) {
        if (balance.compareTo(amount) < 0) {
            throw new InsufficientFundsException();
        }

        MoneyWithdrawnEvent event = new MoneyWithdrawnEvent(
            UUID.randomUUID().toString(),
            accountId,
            amount,
            Instant.now(),
            ++version
        );

        apply(event);
        uncommittedEvents.add(event);
    }

    // APPLY EVENTS (update state)
    private void apply(AccountCreatedEvent event) {
        this.accountId = event.getAccountId();
        this.status = "ACTIVE";
    }

    private void apply(MoneyDepositedEvent event) {
        this.balance = this.balance.add(event.getAmount());
    }

    private void apply(MoneyWithdrawnEvent event) {
        this.balance = this.balance.subtract(event.getAmount());
    }

    // LOAD FROM HISTORY
    public void loadFromHistory(List<Event> events) {
        for (Event event : events) {
            if (event instanceof AccountCreatedEvent) {
                apply((AccountCreatedEvent) event);
            } else if (event instanceof MoneyDepositedEvent) {
                apply((MoneyDepositedEvent) event);
            } else if (event instanceof MoneyWithdrawnEvent) {
                apply((MoneyWithdrawnEvent) event);
            }
            this.version = event.getVersion();
        }
    }

    public List<Event> getUncommittedEvents() {
        return uncommittedEvents;
    }

    public void markEventsAsCommitted() {
        uncommittedEvents.clear();
    }

    // Getters
    public BigDecimal getBalance() { return balance; }
    public int getVersion() { return version; }
}

// 3. EVENT STORE (Repository)
@Repository
public class EventStore {

    @Autowired
    private JdbcTemplate jdbcTemplate;

    public void save(List<Event> events) {
        for (Event event : events) {
            jdbcTemplate.update(
                "INSERT INTO events (event_id, aggregate_id, event_type, " +
                "event_data, version, timestamp) VALUES (?, ?, ?, ?, ?, ?)",
                event.getEventId(),
                event.getAggregateId(),
                event.getClass().getSimpleName(),
                serializeToJson(event),
                event.getVersion(),
                event.getTimestamp()
            );
        }
    }

    public List<Event> getEvents(String aggregateId) {
        return jdbcTemplate.query(
            "SELECT * FROM events WHERE aggregate_id = ? ORDER BY version",
            new Object[]{aggregateId},
            (rs, rowNum) -> deserializeEvent(
                rs.getString("event_type"),
                rs.getString("event_data")
            )
        );
    }

    private String serializeToJson(Event event) {
        // Jackson or Gson
        return new ObjectMapper().writeValueAsString(event);
    }

    private Event deserializeEvent(String eventType, String eventData) {
        // Deserialize based on event type
        Class<?> eventClass = Class.forName("com.example.events." + eventType);
        return (Event) new ObjectMapper().readValue(eventData, eventClass);
    }
}

// 4. APPLICATION SERVICE
@Service
public class BankAccountService {

    @Autowired
    private EventStore eventStore;

    @Transactional
    public void createAccount(String accountId, String ownerName) {
        BankAccount account = new BankAccount();
        account.createAccount(accountId, ownerName);

        // Save events
        eventStore.save(account.getUncommittedEvents());
        account.markEventsAsCommitted();
    }

    @Transactional
    public void deposit(String accountId, BigDecimal amount) {
        // Load aggregate from events
        BankAccount account = loadAccount(accountId);

        // Execute command
        account.deposit(amount);

        // Save new events
        eventStore.save(account.getUncommittedEvents());
        account.markEventsAsCommitted();
    }

    @Transactional
    public void withdraw(String accountId, BigDecimal amount) {
        BankAccount account = loadAccount(accountId);
        account.withdraw(amount);
        eventStore.save(account.getUncommittedEvents());
        account.markEventsAsCommitted();
    }

    public BankAccount loadAccount(String accountId) {
        List<Event> events = eventStore.getEvents(accountId);
        BankAccount account = new BankAccount();
        account.loadFromHistory(events);
        return account;
    }

    public BigDecimal getBalance(String accountId) {
        BankAccount account = loadAccount(accountId);
        return account.getBalance();
    }
}

// 5. CONTROLLER
@RestController
@RequestMapping("/accounts")
public class BankAccountController {

    @Autowired
    private BankAccountService accountService;

    @PostMapping
    public ResponseEntity<Void> createAccount(@RequestBody CreateAccountRequest req) {
        accountService.createAccount(req.getAccountId(), req.getOwnerName());
        return ResponseEntity.status(201).build();
    }

    @PostMapping("/{accountId}/deposit")
    public ResponseEntity<Void> deposit(
        @PathVariable String accountId,
        @RequestBody DepositRequest req
    ) {
        accountService.deposit(accountId, req.getAmount());
        return ResponseEntity.ok().build();
    }

    @PostMapping("/{accountId}/withdraw")
    public ResponseEntity<Void> withdraw(
        @PathVariable String accountId,
        @RequestBody WithdrawRequest req
    ) {
        accountService.withdraw(accountId, req.getAmount());
        return ResponseEntity.ok().build();
    }

    @GetMapping("/{accountId}/balance")
    public ResponseEntity<BalanceResponse> getBalance(@PathVariable String accountId) {
        BigDecimal balance = accountService.getBalance(accountId);
        return ResponseEntity.ok(new BalanceResponse(balance));
    }
}
```

---

## System Design Interview Answer

**Question: "What is Event Sourcing and when would you use it?"**

**Answer:**

"Event Sourcing is a pattern where instead of storing just the current state, we store **every change** as an immutable event in an append-only log.

**How it works:**
Think of a bank statement - instead of just showing your balance ($500), it shows every transaction: deposited $100, withdrew $50, etc. The balance is calculated by replaying all transactions.

**Key Components:**
1. **Events**: Immutable facts (OrderCreated, MoneyWithdrawn)
2. **Event Store**: Append-only database storing events
3. **Aggregates**: Business logic that validates and creates events
4. **Projections**: Read-optimized views built from events

**Benefits:**
- Complete audit trail (who, what, when, why)
- Time travel (what was balance on March 1?)
- Event-driven architecture (other systems listen to events)
- Bug recovery (fix code, replay events)

**Use When:**
- Need complete audit trail (banking, healthcare)
- Compliance requirements (GDPR, SOX)
- Complex domains with rich history
- Event-driven integration

**Don't Use When:**
- Simple CRUD app
- No audit requirements
- Team not familiar with pattern
- Current state is sufficient

**Trade-offs:**
- More complex than traditional CRUD
- Need to handle event schema evolution
- Projections eventually consistent
- More storage (all events kept)

In my experience, I'd use it for order processing systems where knowing the complete order lifecycle is critical for customer support and business analytics."

---

## Key Takeaways

✓ **Store events, not state**: Every change is an immutable event

✓ **Append-only**: Never update or delete events

✓ **Replay to get state**: Current state = apply all events

✓ **Complete audit trail**: Know who, what, when, why

✓ **Time travel**: Query historical state

✓ **Projections**: Build read-optimized views from events

✓ **Snapshots**: Optimize replay performance

✓ **Event-driven**: Other systems react to events

✓ **Not for everything**: Use when audit/history matters
