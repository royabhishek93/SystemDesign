# Distributed Transactions - Managing Consistency Across Services

## The Problem: Transactions Across Multiple Databases

In a **monolithic** application, we have one database and can use ACID transactions easily. But in **microservices**, each service has its own database. How do we maintain consistency across multiple databases?

```
┌─────────────────────────────────────────────────────────────────────────┐
│                MONOLITHIC vs DISTRIBUTE TRANSACTIONS                    │
└─────────────────────────────────────────────────────────────────────────┘

MONOLITHIC APPLICATION (Easy - Single Database)
────────────────────────────────────────────────

┌─────────────────────────────────────────────────┐
│          Single Application                     │
│                                                 │
│  BEGIN TRANSACTION;                             │
│    UPDATE orders SET status = 'paid';           │
│    UPDATE inventory SET stock = stock - 1;      │
│    INSERT INTO shipments (...);                 │
│  COMMIT;  ← All or nothing!                     │
│                                                 │
└────────────────┬────────────────────────────────┘
                 │
                 ▼
        ┌────────────────┐
        │ Single Database│
        │  • orders      │
        │  • inventory   │
        │  • shipments   │
        └────────────────┘

✓ ACID transactions work perfectly
✓ Simple to implement


MICROSERVICES (Complex - Multiple Databases)
─────────────────────────────────────────────

┌──────────────┐       ┌──────────────┐       ┌──────────────┐
│   Order      │       │  Inventory   │       │  Shipping    │
│   Service    │       │   Service    │       │   Service    │
└──────┬───────┘       └──────┬───────┘       └──────┬───────┘
       │                      │                      │
       ▼                      ▼                      ▼
┌──────────────┐       ┌──────────────┐       ┌──────────────┐
│   Order DB   │       │ Inventory DB │       │  Shipping DB │
└──────────────┘       └──────────────┘       └──────────────┘

❌ Cannot use single ACID transaction across multiple databases
❌ What if Order succeeds but Inventory fails?
❌ How to rollback changes across services?


EXAMPLE PROBLEM:
────────────────

User places an order:

Step 1: Order Service → Create order ✓
Step 2: Inventory Service → Reduce stock ✓
Step 3: Shipping Service → Create shipment ❌ FAILS

Problem: Order and Inventory updated, but Shipping failed!
Result: Inconsistent state - order shows "processing" but won't ship
```

---

## Solution 1: Two-Phase Commit (2PC)

**Simple Explanation:** A **coordinator** asks all services to prepare for commit. If all agree, coordinator tells everyone to commit. If anyone says no, everyone rolls back.

Think of it like a **wedding ceremony**: "Do you take this person? Yes. Do you take this person? Yes. You may now commit!"

```
┌─────────────────────────────────────────────────────────────────────────┐
│                    TWO-PHASE COMMIT (2PC)                                │
└─────────────────────────────────────────────────────────────────────────┘

Participants:
  • Coordinator (orchestrator)
  • Service A (Order Service)
  • Service B (Inventory Service)
  • Service C (Shipping Service)


PHASE 1: PREPARE (Voting Phase)
────────────────────────────────

Coordinator                Service A         Service B         Service C
     │                         │                 │                 │
     │────── PREPARE ─────────▶│                 │                 │
     │                         │                 │                 │
     │                         │ Lock resources  │                 │
     │                         │ Check if can    │                 │
     │                         │ commit          │                 │
     │                         │                 │                 │
     │◀────── YES VOTE ────────│                 │                 │
     │                         │                 │                 │
     │────── PREPARE ──────────┼────────────────▶│                 │
     │                         │                 │                 │
     │                         │                 │ Lock resources  │
     │                         │                 │                 │
     │◀────── YES VOTE ────────┼─────────────────│                 │
     │                         │                 │                 │
     │────── PREPARE ──────────┼─────────────────┼────────────────▶│
     │                         │                 │                 │
     │                         │                 │                 │ Lock
     │                         │                 │                 │
     │◀────── YES VOTE ────────┼─────────────────┼─────────────────│
     │                         │                 │                 │
     │ All voted YES!          │                 │                 │


PHASE 2: COMMIT (Decision Phase)
─────────────────────────────────

Coordinator                Service A         Service B         Service C
     │                         │                 │                 │
     │────── COMMIT ──────────▶│                 │                 │
     │                         │                 │                 │
     │                         │ Commit changes  │                 │
     │                         │ Release locks   │                 │
     │                         │                 │                 │
     │◀────── ACK ─────────────│                 │                 │
     │                         │                 │                 │
     │────── COMMIT ───────────┼────────────────▶│                 │
     │                         │                 │                 │
     │                         │                 │ Commit changes  │
     │                         │                 │                 │
     │◀────── ACK ─────────────┼─────────────────│                 │
     │                         │                 │                 │
     │────── COMMIT ───────────┼─────────────────┼────────────────▶│
     │                         │                 │                 │
     │                         │                 │                 │ Commit
     │                         │                 │                 │
     │◀────── ACK ─────────────┼─────────────────┼─────────────────│
     │                         │                 │                 │
     │ All committed! ✓        │                 │                 │


FAILURE SCENARIO: Service C votes NO
─────────────────────────────────────

Coordinator                Service A         Service B         Service C
     │                         │                 │                 │
     │────── PREPARE ─────────▶│                 │                 │
     │◀────── YES ─────────────│                 │                 │
     │                         │                 │                 │
     │────── PREPARE ──────────┼────────────────▶│                 │
     │◀────── YES ─────────────┼─────────────────│                 │
     │                         │                 │                 │
     │────── PREPARE ──────────┼─────────────────┼────────────────▶│
     │                         │                 │                 │
     │                         │                 │           Check fails
     │                         │                 │           (no capacity)
     │                         │                 │                 │
     │◀────── NO VOTE ─────────┼─────────────────┼─────────────────│
     │                         │                 │                 │
     │ Someone voted NO!       │                 │                 │
     │ Must ABORT              │                 │                 │
     │                         │                 │                 │
     │────── ABORT ────────────▶│                 │                 │
     │                         │                 │                 │
     │                         │ Rollback        │                 │
     │                         │ Release locks   │                 │
     │                         │                 │                 │
     │────── ABORT ────────────┼────────────────▶│                 │
     │                         │                 │                 │
     │                         │                 │ Rollback        │
     │                         │                 │                 │
     │────── ABORT ────────────┼─────────────────┼────────────────▶│
     │                         │                 │                 │
     │                         │                 │                 │ Rollback
     │                         │                 │                 │
     │ All rolled back ✓       │                 │                 │


PROBLEMS WITH 2PC:
──────────────────

❌ BLOCKING: All services hold locks during Phase 1
   - If coordinator crashes, services are stuck waiting
   - Resources locked, can't process other requests

❌ SLOW: Requires multiple network round trips
   - Prepare phase: 1 round trip per service
   - Commit phase: 1 round trip per service
   - Total: 2N round trips (N = number of services)

❌ SINGLE POINT OF FAILURE: Coordinator
   - If coordinator crashes between Phase 1 and 2
   - Services don't know whether to commit or abort

❌ NOT SUITABLE FOR MICROSERVICES:
   - Tight coupling between services
   - Doesn't work across different organizations
   - Hard to implement in distributed systems


CODE EXAMPLE (Java XA Transactions):
────────────────────────────────────

// Coordinator
@Transactional
public void placeOrder(Order order) {
    // Phase 1: Prepare
    boolean orderPrepared = orderService.prepare(order);
    boolean inventoryPrepared = inventoryService.prepare(order);
    boolean shippingPrepared = shippingService.prepare(order);

    if (orderPrepared && inventoryPrepared && shippingPrepared) {
        // Phase 2: Commit
        orderService.commit();
        inventoryService.commit();
        shippingService.commit();
    } else {
        // Phase 2: Abort
        orderService.abort();
        inventoryService.abort();
        shippingService.abort();
    }
}

// Problem: What if coordinator crashes here? ↑
// Services are left in "prepared" state forever!
```

---

## Solution 2: Saga Pattern (Better for Microservices)

**Simple Explanation:** Instead of one big transaction, break it into **multiple small local transactions**. Each service commits immediately. If something fails later, **compensate** (undo) previous steps.

Think of it like **booking a trip**: Book flight → Book hotel → Book car. If car booking fails, cancel hotel and flight.

```
┌─────────────────────────────────────────────────────────────────────────┐
│                       SAGA PATTERN - CHOREOGRAPHY                        │
└─────────────────────────────────────────────────────────────────────────┘

Each service:
  1. Performs local transaction
  2. Publishes event
  3. Listens for events from other services
  4. Implements compensation logic


SUCCESS FLOW:
─────────────

Order Service         Inventory Service      Payment Service       Shipping Service
      │                       │                     │                     │
      │ 1. Create Order       │                     │                     │
      │    (Local txn)        │                     │                     │
      │    COMMIT ✓           │                     │                     │
      │                       │                     │                     │
      │─── OrderCreated ─────▶│                     │                     │
      │    Event              │                     │                     │
      │                       │                     │                     │
      │                       │ 2. Reserve Stock    │                     │
      │                       │    (Local txn)      │                     │
      │                       │    COMMIT ✓         │                     │
      │                       │                     │                     │
      │                       │─── StockReserved ──▶│                     │
      │                       │    Event            │                     │
      │                       │                     │                     │
      │                       │                     │ 3. Charge Customer  │
      │                       │                     │    (Local txn)      │
      │                       │                     │    COMMIT ✓         │
      │                       │                     │                     │
      │                       │                     │─── PaymentSuccess ─▶│
      │                       │                     │    Event            │
      │                       │                     │                     │
      │                       │                     │                     │ 4. Ship Order
      │                       │                     │                     │    (Local txn)
      │                       │                     │                     │    COMMIT ✓
      │                       │                     │                     │
      │◀─────────────────────────────────────────────── OrderShipped ─────│
      │                       │                     │    Event            │
      │                       │                     │                     │
      │ Update order status   │                     │                     │
      │ COMMIT ✓              │                     │                     │

✓ All steps succeeded
✓ Each service committed independently
✓ No locks held across services


FAILURE FLOW (Payment Fails):
──────────────────────────────

Order Service         Inventory Service      Payment Service       Shipping Service
      │                       │                     │
      │ 1. Create Order       │                     │
      │    COMMIT ✓           │                     │
      │                       │                     │
      │─── OrderCreated ─────▶│                     │
      │                       │                     │
      │                       │ 2. Reserve Stock    │
      │                       │    COMMIT ✓         │
      │                       │                     │
      │                       │─── StockReserved ──▶│
      │                       │                     │
      │                       │                     │ 3. Charge Customer
      │                       │                     │    ❌ FAILED
      │                       │                     │    (Insufficient funds)
      │                       │                     │
      │                       │◀─── PaymentFailed ──│
      │                       │    Event            │
      │                       │                     │
      │                       │ COMPENSATE:         │
      │                       │ Unreserve Stock     │
      │                       │ COMMIT ✓            │
      │                       │                     │
      │◀─── StockUnreserved ──│                     │
      │    Event              │                     │
      │                       │                     │
      │ COMPENSATE:           │                     │
      │ Cancel Order          │                     │
      │ COMMIT ✓              │                     │
      │                       │                     │

✓ Compensating transactions undid the work
✓ System is consistent again


CODE EXAMPLE (Spring Boot + Kafka):
───────────────────────────────────

// Order Service
@Service
public class OrderService {

    @KafkaListener(topics = "order-created")
    public void createOrder(OrderCreatedEvent event) {
        // Local transaction
        Order order = new Order(event.getUserId(), event.getItems());
        order.setStatus("PENDING");
        orderRepo.save(order);  // COMMIT

        // Publish event
        kafkaTemplate.send("order-created", new OrderCreatedEvent(order));
    }

    // Compensation logic
    @KafkaListener(topics = "payment-failed")
    public void cancelOrder(PaymentFailedEvent event) {
        // Compensating transaction
        Order order = orderRepo.findById(event.getOrderId());
        order.setStatus("CANCELLED");
        orderRepo.save(order);  // COMMIT

        kafkaTemplate.send("order-cancelled", new OrderCancelledEvent(order));
    }
}

// Inventory Service
@Service
public class InventoryService {

    @KafkaListener(topics = "order-created")
    public void reserveStock(OrderCreatedEvent event) {
        try {
            // Local transaction
            for (Item item : event.getItems()) {
                Inventory inv = inventoryRepo.findByProductId(item.getProductId());

                if (inv.getStock() < item.getQuantity()) {
                    throw new InsufficientStockException();
                }

                inv.setStock(inv.getStock() - item.getQuantity());
                inventoryRepo.save(inv);  // COMMIT
            }

            // Publish success event
            kafkaTemplate.send("stock-reserved",
                new StockReservedEvent(event.getOrderId()));

        } catch (InsufficientStockException e) {
            // Publish failure event
            kafkaTemplate.send("stock-reservation-failed",
                new StockReservationFailedEvent(event.getOrderId()));
        }
    }

    // Compensation logic
    @KafkaListener(topics = "payment-failed")
    public void unreserveStock(PaymentFailedEvent event) {
        // Compensating transaction
        Order order = getOrder(event.getOrderId());

        for (Item item : order.getItems()) {
            Inventory inv = inventoryRepo.findByProductId(item.getProductId());
            inv.setStock(inv.getStock() + item.getQuantity());  // Restore stock
            inventoryRepo.save(inv);  // COMMIT
        }

        kafkaTemplate.send("stock-unreserved",
            new StockUnreservedEvent(event.getOrderId()));
    }
}

// Payment Service
@Service
public class PaymentService {

    @KafkaListener(topics = "stock-reserved")
    public void chargePayment(StockReservedEvent event) {
        try {
            // Local transaction
            Order order = getOrder(event.getOrderId());
            User user = userRepo.findById(order.getUserId());

            if (user.getBalance().compareTo(order.getTotal()) < 0) {
                throw new InsufficientFundsException();
            }

            user.setBalance(user.getBalance().subtract(order.getTotal()));
            userRepo.save(user);  // COMMIT

            Payment payment = new Payment(order.getId(), order.getTotal());
            paymentRepo.save(payment);  // COMMIT

            // Publish success event
            kafkaTemplate.send("payment-success",
                new PaymentSuccessEvent(event.getOrderId()));

        } catch (InsufficientFundsException e) {
            // Publish failure event
            kafkaTemplate.send("payment-failed",
                new PaymentFailedEvent(event.getOrderId()));
        }
    }
}
```

---

## Saga Pattern: Choreography vs Orchestration

```
┌─────────────────────────────────────────────────────────────────────────┐
│                   CHOREOGRAPHY (Decentralized)                           │
└─────────────────────────────────────────────────────────────────────────┘

No central coordinator. Each service knows what to do when it receives an event.

        ┌────────────┐
        │   Order    │───┐
        │  Service   │   │ OrderCreated
        └────────────┘   │
                         ▼
        ┌────────────┐   │    ┌────────────┐
        │ Inventory  │◀──┘───▶│  Payment   │
        │  Service   │         │  Service   │
        └────────────┘         └────────────┘
                │                     │
                │ StockReserved       │ PaymentSuccess
                ▼                     ▼
        ┌────────────┐         ┌────────────┐
        │  Shipping  │         │   Email    │
        │  Service   │         │  Service   │
        └────────────┘         └────────────┘

✓ Loose coupling
✓ No single point of failure
✓ Services independent

✗ Hard to understand full flow
✗ Difficult to debug
✗ No central view of saga state


┌─────────────────────────────────────────────────────────────────────────┐
│                    ORCHESTRATION (Centralized)                           │
└─────────────────────────────────────────────────────────────────────────┘

Central orchestrator controls the flow. Tells each service what to do.

                    ┌──────────────────────┐
                    │  Saga Orchestrator   │
                    │  (Order Coordinator) │
                    └──────────┬───────────┘
                               │
        ┌──────────────────────┼──────────────────────┐
        │                      │                      │
        ▼                      ▼                      ▼
┌────────────┐         ┌────────────┐         ┌────────────┐
│  Inventory │         │  Payment   │         │  Shipping  │
│   Service  │         │  Service   │         │  Service   │
└────────────┘         └────────────┘         └────────────┘
        │                      │                      │
        └──────────────────────┴──────────────────────┘
           All respond to orchestrator

✓ Central view of saga state
✓ Easy to understand flow
✓ Easy to monitor and debug

✗ Single point of failure (orchestrator)
✗ Tighter coupling
✗ Orchestrator can become complex


CODE EXAMPLE (Orchestration with Spring Boot):
──────────────────────────────────────────────

@Service
public class OrderSagaOrchestrator {

    @Autowired
    private InventoryService inventoryService;

    @Autowired
    private PaymentService paymentService;

    @Autowired
    private ShippingService shippingService;

    public void executeOrderSaga(Order order) {
        SagaState state = new SagaState(order);

        try {
            // Step 1: Reserve inventory
            state.setCurrentStep("INVENTORY");
            inventoryService.reserveStock(order);
            state.addCompletedStep("INVENTORY");

            // Step 2: Charge payment
            state.setCurrentStep("PAYMENT");
            paymentService.charge(order);
            state.addCompletedStep("PAYMENT");

            // Step 3: Create shipment
            state.setCurrentStep("SHIPPING");
            shippingService.createShipment(order);
            state.addCompletedStep("SHIPPING");

            // All steps succeeded
            state.setStatus("COMPLETED");

        } catch (Exception e) {
            // Compensate in reverse order
            state.setStatus("COMPENSATING");

            if (state.hasCompleted("PAYMENT")) {
                paymentService.refund(order);
            }

            if (state.hasCompleted("INVENTORY")) {
                inventoryService.unreserveStock(order);
            }

            state.setStatus("FAILED");
            throw new SagaFailedException("Order saga failed", e);
        }
    }
}

// Saga State (stored in database for durability)
@Entity
public class SagaState {
    @Id
    private String sagaId;

    private String orderId;
    private String status;  // RUNNING, COMPLETED, COMPENSATING, FAILED
    private String currentStep;
    private List<String> completedSteps;
    private LocalDateTime createdAt;
}
```

---

## Eventual Consistency

**Simple Explanation:** In distributed systems, we accept that data may be **temporarily inconsistent** across services, but will **eventually become consistent**.

```
┌─────────────────────────────────────────────────────────────────────────┐
│                      EVENTUAL CONSISTENCY                                │
└─────────────────────────────────────────────────────────────────────────┘

Example: User changes email address

t=0     User updates email in User Service
        ├─▶ User Service DB: email = "new@example.com" ✓
        └─▶ Publishes UserEmailChanged event

t=10    Order Service hasn't processed event yet
        ├─▶ User Service: email = "new@example.com"
        └─▶ Order Service: email = "old@example.com"  ← INCONSISTENT!

t=50    Order Service processes event
        ├─▶ User Service: email = "new@example.com"
        └─▶ Order Service: email = "new@example.com"  ✓ CONSISTENT!

Timeline:
─────────
     │
t=0  │ Update       ┌─ Inconsistent Period ─┐
     │──────────────┤                        ├──────────────▶
     │              │                        │
     User Service   Event                    Order Service
     updates        published                processes event

✓ Eventually consistent
✓ Inconsistency window: 50ms (acceptable for most use cases)


WHEN IS THIS ACCEPTABLE?
─────────────────────────

✓ Social media (likes, comments count)
  - Few seconds delay is fine

✓ Product reviews
  - Rating updates can be delayed

✓ Analytics dashboards
  - Reporting data doesn't need to be real-time

✓ Email address updates
  - Non-critical data


WHEN IS THIS NOT ACCEPTABLE?
─────────────────────────────

✗ Financial transactions (bank balance)
  - Must be immediately consistent

✗ Inventory (last item in stock)
  - Can't oversell

✗ Authentication (password changes)
  - Security risk if delayed
```

---

## Handling Failures in Distributed Transactions

```
┌─────────────────────────────────────────────────────────────────────────┐
│                       FAILURE SCENARIOS                                  │
└─────────────────────────────────────────────────────────────────────────┘

1. SERVICE TIMEOUT
──────────────────

Order Service ───(timeout)──X──▶ Inventory Service
                                 (not responding)

Solution:
  • Retry with exponential backoff
  • Use circuit breaker (fail fast after N failures)
  • Implement timeout on all remote calls


2. DUPLICATE MESSAGES (Event published twice)
──────────────────────────────────────────────

Event Bus ───OrderCreated───▶ Inventory Service
Event Bus ───OrderCreated───▶ Inventory Service (duplicate!)

Result: Stock reduced twice! ❌

Solution: IDEMPOTENCY
  • Each event has unique ID
  • Service checks if already processed

@Service
public class InventoryService {

    @Autowired
    private ProcessedEventRepository processedEvents;

    @KafkaListener(topics = "order-created")
    @Transactional
    public void reserveStock(OrderCreatedEvent event) {
        // Check if already processed
        if (processedEvents.existsById(event.getEventId())) {
            return;  // Skip duplicate
        }

        // Process event
        reserveStock(event.getItems());

        // Mark as processed
        processedEvents.save(new ProcessedEvent(event.getEventId()));
    }
}


3. OUT-OF-ORDER MESSAGES
────────────────────────

Event Bus ───OrderShipped────▶ Order Service (arrives first)
Event Bus ───OrderCreated────▶ Order Service (arrives late!)

Result: Ship event processed before create event! ❌

Solution:
  • Add sequence number or timestamp to events
  • Queue out-of-order events until dependencies arrive
  • Use message ordering guarantees (Kafka partitions)


4. COMPENSATING TRANSACTION FAILS
──────────────────────────────────

Order created ✓
Stock reserved ✓
Payment fails ❌
Unreserve stock ❌ FAILS (Inventory Service down!)

Result: Stock permanently reserved! ❌

Solution:
  • Retry compensating transaction with exponential backoff
  • Dead letter queue for failed compensations
  • Manual intervention (alerts to operations team)
  • Store compensation state in database (durable)

@Service
public class CompensationService {

    @Retryable(
        value = {Exception.class},
        maxAttempts = 5,
        backoff = @Backoff(delay = 1000, multiplier = 2)
    )
    public void compensate(String sagaId, String step) {
        // Retry up to 5 times with exponential backoff
        // 1s, 2s, 4s, 8s, 16s
    }
}


5. SAGA STATE LOST (Orchestrator crashes)
──────────────────────────────────────────

Orchestrator crashes after Step 2 (Payment succeeded)
Step 3 (Shipping) never executes

Result: Payment taken but order never ships! ❌

Solution: DURABLE SAGA STATE
  • Store saga state in database (not memory)
  • On restart, orchestrator resumes incomplete sagas

@Entity
@Table(name = "saga_state")
public class SagaState {
    @Id
    private String sagaId;

    private String status;  // RUNNING, COMPLETED, FAILED
    private String currentStep;
    private List<String> completedSteps;

    // When orchestrator restarts, it queries database
    // and resumes all RUNNING sagas
}

@Service
public class SagaRecoveryService {

    @PostConstruct
    public void recoverIncomplete Sagas() {
        List<SagaState> running = sagaStateRepo.findByStatus("RUNNING");

        for (SagaState state : running) {
            // Resume saga from last completed step
            sagaOrchestrator.resume(state);
        }
    }
}
```

---

## Comparison: 2PC vs Saga

```
┌─────────────────────────────────────────────────────────────────────────┐
│                     2PC vs SAGA COMPARISON                               │
└─────────────────────────────────────────────────────────────────────────┘

╔════════════════════╦════════════════════╦════════════════════════╗
║     Feature        ║        2PC         ║         Saga           ║
╠════════════════════╬════════════════════╬════════════════════════╣
║ Consistency        ║ Strong (ACID)      ║ Eventual               ║
║                    ║ Immediate          ║ Delayed (ms to seconds)║
╠════════════════════╬════════════════════╬════════════════════════╣
║ Coordination       ║ Synchronous        ║ Asynchronous           ║
║                    ║ (blocking)         ║ (non-blocking)         ║
╠════════════════════╬════════════════════╬════════════════════════╣
║ Performance        ║ Slow               ║ Fast                   ║
║                    ║ (locks held)       ║ (no locks)             ║
╠════════════════════╬════════════════════╬════════════════════════╣
║ Failure Handling   ║ Automatic rollback ║ Manual compensation    ║
╠════════════════════╬════════════════════╬════════════════════════╣
║ Coupling           ║ Tight              ║ Loose                  ║
╠════════════════════╬════════════════════╬════════════════════════╣
║ Scalability        ║ Poor               ║ Excellent              ║
╠════════════════════╬════════════════════╬════════════════════════╣
║ Complexity         ║ Simple to implement║ Complex (compensation) ║
╠════════════════════╬════════════════════╬════════════════════════╣
║ Use Case           ║ Monoliths          ║ Microservices          ║
║                    ║ Single data center ║ Distributed systems    ║
╠════════════════════╬════════════════════╬════════════════════════╣
║ Real-World Example ║ Banking (ATM)      ║ E-commerce (Amazon)    ║
║                    ║ Traditional DBs    ║ Booking (Uber, Airbnb) ║
╚════════════════════╩════════════════════╩════════════════════════╝


WHEN TO USE 2PC:
────────────────
✓ Within single organization
✓ Strong consistency required
✓ Small number of participants (2-3)
✓ Can tolerate blocking
✗ NOT suitable for microservices


WHEN TO USE SAGA:
─────────────────
✓ Microservices architecture
✓ Across organizational boundaries
✓ Many participants
✓ High availability required
✓ Can tolerate eventual consistency
✗ NOT suitable when immediate consistency required
```

---

## System Design Interview Answer

**Question: "How do you handle transactions across multiple microservices?"**

**Answer:**

"In microservices, we can't use traditional ACID transactions because each service has its own database. I use the **Saga pattern** to maintain consistency across services.

Here's how it works:

**1. Break into Local Transactions**
Instead of one big transaction, each service performs its own local transaction and commits immediately. For example, when placing an order:
- Order Service creates the order (commits)
- Inventory Service reserves stock (commits)
- Payment Service charges the user (commits)
- Shipping Service creates shipment (commits)

**2. Event-Driven Communication**
Each service publishes an event after completing its transaction. Other services listen and react. I typically use Kafka for this.

**3. Compensating Transactions**
If any step fails, we execute compensating transactions to undo previous steps. For example, if payment fails, we:
- Unreserve the stock (compensate Inventory)
- Cancel the order (compensate Order)

**4. Handling Failures**
I implement several safeguards:
- **Idempotency**: Each service checks if it already processed an event (prevents duplicate processing)
- **Retries**: Failed compensations retry with exponential backoff
- **Durable State**: Store saga state in database so we can recover if orchestrator crashes

**5. Trade-offs**
The Saga pattern gives us **eventual consistency** instead of immediate consistency. There's a brief window where data might be inconsistent across services. For most business cases like e-commerce, this is acceptable - users don't notice a 50ms delay. But for critical operations like financial transactions, I might use a different approach or keep those operations in a single service.

I prefer **choreography** for simple flows and **orchestration** when I need centralized control and monitoring."

---

## Key Takeaways

✓ **2PC (Two-Phase Commit)**: Strong consistency but blocking, slow, not suitable for microservices

✓ **Saga Pattern**: Eventual consistency, non-blocking, perfect for microservices

✓ **Choreography**: Decentralized, services react to events

✓ **Orchestration**: Centralized coordinator controls flow

✓ **Idempotency**: Critical for handling duplicate messages

✓ **Compensating Transactions**: Undo previous steps when failure occurs

✓ **Trade-off**: Performance and availability vs immediate consistency

✓ **Eventual Consistency**: Acceptable for most business operations
