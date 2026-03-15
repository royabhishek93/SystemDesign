# CQRS - Command Query Responsibility Segregation

## What is CQRS?

**CQRS** stands for **Command Query Responsibility Segregation**. It's a pattern that separates **reading data** (queries) from **writing data** (commands) into different models.

**Simple Analogy:** Like having a **different door** for entering and exiting a building - optimized for different purposes.

```
┌─────────────────────────────────────────────────────────────────────────┐
│                    TRADITIONAL vs CQRS                                   │
└─────────────────────────────────────────────────────────────────────────┘

TRADITIONAL (Same Model for Read & Write):
───────────────────────────────────────────

┌──────────────┐
│   Client     │
└──────┬───────┘
       │
       ├────── Read (GET) ─────┐
       │                       │
       └────── Write (POST) ───┤
                               ▼
                     ┌──────────────────┐
                     │   Single Model   │
                     │                  │
                     │   User Entity    │
                     │   • id           │
                     │   • name         │
                     │   • email        │
                     │   • orders       │
                     └────────┬─────────┘
                              │
                              ▼
                     ┌──────────────────┐
                     │    Database      │
                     │    (one schema)  │
                     └──────────────────┘

✗ Same model for different concerns
✗ Complex queries impact writes
✗ Can't optimize separately


CQRS (Separate Models for Read & Write):
─────────────────────────────────────────

┌──────────────┐
│   Client     │
└──────┬───────┘
       │
       ├────── Read (GET) ─────────────────┐
       │                                   │
       │                                   ▼
       │                         ┌──────────────────┐
       │                         │   Query Model    │
       │                         │   (Read-only)    │
       │                         │                  │
       │                         │  • Denormalized  │
       │                         │  • Fast queries  │
       │                         │  • Multiple DBs  │
       │                         └────────┬─────────┘
       │                                  │
       │                                  ▼
       │                         ┌──────────────────┐
       │                         │  Read Database   │
       │                         │  (MongoDB,       │
       │                         │   Elasticsearch) │
       │                         └──────────────────┘
       │
       │
       └────── Write (POST) ──────────────┐
                                          │
                                          ▼
                                ┌──────────────────┐
                                │  Command Model   │
                                │  (Write-only)    │
                                │                  │
                                │  • Normalized    │
                                │  • Business      │
                                │    logic         │
                                └────────┬─────────┘
                                         │
                                         ▼
                                ┌──────────────────┐
                                │  Write Database  │
                                │  (PostgreSQL)    │
                                └──────────────────┘
                                         │
                                         │ Synchronize
                                         ▼
                                ┌──────────────────┐
                                │   Event Bus      │
                                │   (Kafka)        │
                                └──────────────────┘
                                         │
                                         └────────────▶ Update Read DB

✓ Separate models for different concerns
✓ Optimize reads independently
✓ Optimize writes independently
```

---

## Core Concepts

### Commands (Write Operations)

```
┌─────────────────────────────────────────────────────────────────────────┐
│                          COMMANDS (Write Side)                           │
└─────────────────────────────────────────────────────────────────────────┘

Commands = INTENT to change state

Characteristics:
────────────────
• Named with IMPERATIVE verbs (CreateOrder, UpdateUser)
• Contain data needed for the operation
• Validated against business rules
• Can FAIL (rejected if invalid)
• Return void or simple ACK (not data)

Examples:
─────────

Good Command Names:
✓ CreateOrderCommand
✓ UpdateUserEmailCommand
✓ CancelSubscriptionCommand
✓ WithdrawMoneyCommand

Bad Command Names:
✗ OrderCommand (vague)
✗ UserQuery (that's a query, not command)
✗ GetOrderDetails (that's a read)


Command Structure:
──────────────────

public class CreateOrderCommand {
    private String orderId;
    private String userId;
    private List<OrderItem> items;
    private BigDecimal totalAmount;
    private String shippingAddress;

    // No getters that return complex state
    // Commands are write-only
}


Command Flow:
─────────────

Client                Command Handler          Database
  │                          │                     │
  │── CreateOrderCommand ───▶│                     │
  │                          │                     │
  │                          │ 1. Validate         │
  │                          │    • User exists?   │
  │                          │    • Items in stock?│
  │                          │    • Valid address? │
  │                          │                     │
  │                          │ 2. Execute          │
  │                          │    business logic   │
  │                          │                     │
  │                          │ 3. Save             │
  │                          │────────────────────▶│
  │                          │                     │
  │                          │ 4. Publish event    │
  │                          │    OrderCreated     │
  │                          │                     │
  │◀──── ACK (success) ──────│                     │
  │                          │                     │

Commands DON'T return data:
  ✗ Wrong: Order createOrder(CreateOrderCommand cmd)
  ✓ Right: void createOrder(CreateOrderCommand cmd)
  ✓ Right: String createOrder(...) // Return only ID
```

### Queries (Read Operations)

```
┌─────────────────────────────────────────────────────────────────────────┐
│                          QUERIES (Read Side)                             │
└─────────────────────────────────────────────────────────────────────────┘

Queries = Request for data

Characteristics:
────────────────
• Named with GET or FIND (GetOrderDetails, FindUsersByAge)
• Never modify state (idempotent)
• Optimized for fast reads
• Can use denormalized data
• Always succeed (return empty if not found)

Examples:
─────────

Good Query Names:
✓ GetOrderDetailsQuery
✓ FindActiveUsersQuery
✓ SearchProductsQuery
✓ GetUserOrderHistoryQuery

Bad Query Names:
✗ CreateOrder (that's a command)
✗ UpdateUser (that's a command)


Query Structure:
────────────────

public class GetOrderDetailsQuery {
    private String orderId;

    // Only contains query parameters
    // No business logic
}

public class OrderDetailsDTO {
    private String orderId;
    private String userId;
    private String userName;        // Denormalized
    private List<OrderItemDTO> items;
    private BigDecimal totalAmount;
    private String status;
    private String shippingAddress;
    private String trackingNumber;

    // Rich DTO optimized for client needs
}


Query Flow:
───────────

Client                Query Handler          Read Database
  │                          │                     │
  │── GetOrderDetailsQuery ──▶│                     │
  │                          │                     │
  │                          │ 1. No validation    │
  │                          │    (read-only)      │
  │                          │                     │
  │                          │ 2. Query            │
  │                          │────────────────────▶│
  │                          │                     │
  │                          │    Fast, optimized  │
  │                          │    query            │
  │                          │                     │
  │                          │◀────────────────────│
  │                          │    OrderDetailsDTO  │
  │                          │                     │
  │◀──── OrderDetailsDTO ────│                     │
  │                          │                     │

Queries return rich data:
  ✓ Full DTOs with all needed data
  ✓ Denormalized (user name, product name, etc.)
  ✓ Optimized for display
```

---

## CQRS Architecture Patterns

### Pattern 1: Simple CQRS (Same Database)

```
┌─────────────────────────────────────────────────────────────────────────┐
│                  SIMPLE CQRS (Single Database)                           │
└─────────────────────────────────────────────────────────────────────────┘

Simplest form: Separate models, same database

┌──────────────┐
│   Client     │
└──────┬───────┘
       │
       ├────── Queries ─────────┐
       │                        │
       └────── Commands ────────┤
                                │
                      ┌─────────┴──────────┐
                      │                    │
                      ▼                    ▼
            ┌──────────────┐     ┌──────────────┐
            │ Query Service│     │Command Service│
            │              │     │               │
            │ • Simple     │     │ • Business    │
            │   queries    │     │   logic       │
            │ • No logic   │     │ • Validation  │
            └──────┬───────┘     └──────┬────────┘
                   │                    │
                   │                    │
                   └────────┬───────────┘
                            │
                            ▼
                   ┌─────────────────┐
                   │     Database    │
                   │   (PostgreSQL)  │
                   │                 │
                   │  • users        │
                   │  • orders       │
                   │  • products     │
                   └─────────────────┘

Benefits:
✓ Simple to implement
✓ No data synchronization
✓ Clear separation of concerns

When to use:
• Starting with CQRS
• Small to medium apps
• Don't need different DB technologies
```

### Pattern 2: CQRS with Separate Databases

```
┌─────────────────────────────────────────────────────────────────────────┐
│              CQRS WITH SEPARATE DATABASES                                │
└─────────────────────────────────────────────────────────────────────────┘

Different databases optimized for reads vs writes

┌──────────────┐
│   Client     │
└──────┬───────┘
       │
       ├────── Queries (90% of traffic) ────┐
       │                                    │
       │                                    ▼
       │                          ┌──────────────────┐
       │                          │  Query Service   │
       │                          └────────┬─────────┘
       │                                   │
       │                                   ▼
       │                          ┌──────────────────┐
       │                          │  Read Database   │
       │                          │                  │
       │                          │  • Denormalized  │
       │                          │  • Materialized  │
       │                          │    views         │
       │                          │  • Indexes for   │
       │                          │    common queries│
       │                          │                  │
       │                          │ (MongoDB or      │
       │                          │  Elasticsearch)  │
       │                          └──────────────────┘
       │                                   ▲
       │                                   │
       │                                   │ Sync
       │                                   │
       │                          ┌────────┴─────────┐
       │                          │   Event Bus      │
       │                          │   (Kafka)        │
       │                          └────────▲─────────┘
       │                                   │
       │                                   │
       │                                   │ Publish
       └────── Commands (10% of traffic) ──┤
                                           │
                                           ▼
                                  ┌──────────────────┐
                                  │ Command Service  │
                                  └────────┬─────────┘
                                           │
                                           ▼
                                  ┌──────────────────┐
                                  │ Write Database   │
                                  │                  │
                                  │ • Normalized     │
                                  │ • ACID           │
                                  │ • Consistent     │
                                  │                  │
                                  │ (PostgreSQL)     │
                                  └──────────────────┘

Data Flow:
──────────

1. Command comes in → Write to PostgreSQL
2. Publish event to Kafka
3. Event consumer updates MongoDB (read DB)
4. Query reads from MongoDB (fast!)

Benefits:
✓ Optimize DBs separately (write vs read)
✓ Scale independently
✓ Use best DB for each purpose

Trade-offs:
✗ Eventual consistency (read lag)
✗ Data synchronization complexity
✗ More infrastructure
```

### Pattern 3: CQRS with Event Sourcing

```
┌─────────────────────────────────────────────────────────────────────────┐
│                 CQRS WITH EVENT SOURCING                                 │
└─────────────────────────────────────────────────────────────────────────┘

Most powerful: CQRS + Event Sourcing

┌──────────────┐
│   Client     │
└──────┬───────┘
       │
       ├────── Queries ──────────────────┐
       │                                 │
       │                                 ▼
       │                        ┌──────────────────┐
       │                        │  Query Service   │
       │                        └────────┬─────────┘
       │                                 │
       │                                 ▼
       │                        ┌──────────────────┐
       │                        │   Projections    │
       │                        │  (Read Models)   │
       │                        │                  │
       │                        │ • OrderList      │
       │                        │ • UserProfile    │
       │                        │ • Analytics      │
       │                        └──────────────────┘
       │                                 ▲
       │                                 │
       │                                 │ Build from events
       │                                 │
       │                        ┌────────┴─────────┐
       │                        │   Event Bus      │
       │                        └────────▲─────────┘
       │                                 │
       │                                 │
       └────── Commands ────────────────┤
                                        │
                                        ▼
                               ┌──────────────────┐
                               │ Command Handler  │
                               └────────┬─────────┘
                                        │
                                        ▼
                               ┌──────────────────┐
                               │   Event Store    │
                               │                  │
                               │  OrderCreated    │
                               │  ItemAdded       │
                               │  PaymentProcessed│
                               │  OrderShipped    │
                               └──────────────────┘

Write Side:
• Commands → Events → Event Store
• Events are source of truth

Read Side:
• Projections built from events
• Optimized for queries
• Can rebuild anytime

Benefits:
✓ Complete audit trail (event sourcing)
✓ Optimal query performance (projections)
✓ Can rebuild projections anytime
✓ Time travel queries

When to use:
• Complex domain with audit requirements
• Need historical analysis
• Event-driven architecture
```

---

## Real-World Example: E-commerce Order System

```
┌─────────────────────────────────────────────────────────────────────────┐
│                    E-COMMERCE WITH CQRS                                  │
└─────────────────────────────────────────────────────────────────────────┘

WRITE SIDE (Commands):
──────────────────────

1. Create Order Command
   ────────────────────
   POST /orders
   {
     "userId": "user_123",
     "items": [
       { "productId": "prod_1", "quantity": 2, "price": 999 }
     ],
     "shippingAddress": "123 Main St"
   }

   Flow:
   • Validate user exists
   • Check inventory
   • Calculate total
   • Create order in PostgreSQL
   • Publish OrderCreatedEvent

   Response: 202 Accepted
   {
     "orderId": "order_456",
     "status": "processing"
   }


2. Add Item Command
   ────────────────
   POST /orders/order_456/items
   {
     "productId": "prod_2",
     "quantity": 1
   }

   Flow:
   • Validate order exists
   • Check inventory
   • Add item to order
   • Publish ItemAddedEvent


3. Cancel Order Command
   ────────────────────
   DELETE /orders/order_456

   Flow:
   • Validate order cancellable (not shipped)
   • Cancel order
   • Restore inventory
   • Publish OrderCancelledEvent


READ SIDE (Queries):
────────────────────

1. Get Order Details
   ──────────────────
   GET /orders/order_456

   Response:
   {
     "orderId": "order_456",
     "userId": "user_123",
     "userName": "Alice Smith",         ← Denormalized
     "userEmail": "alice@example.com",  ← Denormalized
     "items": [
       {
         "productId": "prod_1",
         "productName": "Laptop",        ← Denormalized
         "imageUrl": "https://...",      ← Denormalized
         "quantity": 2,
         "price": 999,
         "subtotal": 1998
       }
     ],
     "totalAmount": 1998,
     "status": "shipped",
     "shippingAddress": "123 Main St",
     "trackingNumber": "1Z999AA1",
     "estimatedDelivery": "2024-03-20"
   }

   • Fast query (all data pre-joined)
   • No joins at query time
   • Read from MongoDB


2. Get User's Orders (with pagination)
   ────────────────────────────────────
   GET /users/user_123/orders?page=1&size=10

   Response:
   {
     "orders": [
       {
         "orderId": "order_456",
         "totalAmount": 1998,
         "status": "shipped",
         "createdAt": "2024-03-15",
         "itemCount": 2,
         "thumbnail": "https://..."  ← First product image
       },
       { ... }
     ],
     "totalPages": 5,
     "currentPage": 1
   }

   • Pre-computed counts
   • Optimized for listing


3. Search Orders
   ──────────────
   GET /orders/search?status=shipped&dateFrom=2024-03-01

   • Full-text search in Elasticsearch
   • Faceted search
   • Real-time filters


SYNCHRONIZATION:
────────────────

Event: OrderCreatedEvent
│
├──▶ Projection 1: OrderListProjection (MongoDB)
│    • Update order_list collection
│    • Add order with basic info
│
├──▶ Projection 2: OrderDetailsProjection (MongoDB)
│    • Create detailed order document
│    • Join with user, product data
│
├──▶ Projection 3: OrderSearchProjection (Elasticsearch)
│    • Index order for full-text search
│
└──▶ Projection 4: OrderAnalyticsProjection (Data Warehouse)
     • Update daily sales metrics
```

---

## Code Example: CQRS Implementation

```java
┌─────────────────────────────────────────────────────────────────────────┐
│                    CQRS CODE IMPLEMENTATION                              │
└─────────────────────────────────────────────────────────────────────────┘

// ============ WRITE SIDE ============

// 1. COMMAND
public class CreateOrderCommand {
    private String userId;
    private List<OrderItem> items;
    private String shippingAddress;

    // Getters only
}

// 2. COMMAND HANDLER
@Service
public class CreateOrderCommandHandler {

    @Autowired
    private OrderRepository orderRepository;

    @Autowired
    private InventoryService inventoryService;

    @Autowired
    private EventPublisher eventPublisher;

    @Transactional
    public String handle(CreateOrderCommand command) {
        // 1. Validate
        User user = userRepository.findById(command.getUserId());
        if (user == null) {
            throw new UserNotFoundException();
        }

        for (OrderItem item : command.getItems()) {
            if (!inventoryService.hasStock(item.getProductId(), item.getQuantity())) {
                throw new InsufficientStockException();
            }
        }

        // 2. Create aggregate (business logic)
        Order order = new Order(
            UUID.randomUUID().toString(),
            command.getUserId(),
            command.getItems(),
            command.getShippingAddress()
        );

        // 3. Save to write database
        orderRepository.save(order);

        // 4. Publish event
        OrderCreatedEvent event = new OrderCreatedEvent(
            order.getOrderId(),
            order.getUserId(),
            order.getItems(),
            order.getTotalAmount(),
            order.getShippingAddress(),
            Instant.now()
        );

        eventPublisher.publish(event);

        // 5. Return only ID (not full data)
        return order.getOrderId();
    }
}

// 3. WRITE MODEL (Entity)
@Entity
@Table(name = "orders")
public class Order {
    @Id
    private String orderId;

    private String userId;
    private String status;
    private BigDecimal totalAmount;

    @OneToMany(cascade = CascadeType.ALL)
    private List<OrderItem> items;

    private String shippingAddress;
    private LocalDateTime createdAt;

    // Business logic
    public void cancel() {
        if (status.equals("SHIPPED")) {
            throw new CannotCancelShippedOrderException();
        }
        this.status = "CANCELLED";
    }
}

// 4. CONTROLLER (Write)
@RestController
@RequestMapping("/orders")
public class OrderCommandController {

    @Autowired
    private CreateOrderCommandHandler createOrderHandler;

    @PostMapping
    public ResponseEntity<CreateOrderResponse> createOrder(
        @RequestBody CreateOrderCommand command
    ) {
        String orderId = createOrderHandler.handle(command);

        return ResponseEntity
            .accepted()  // 202 Accepted (async processing)
            .body(new CreateOrderResponse(orderId, "processing"));
    }
}


// ============ READ SIDE ============

// 1. QUERY
public class GetOrderDetailsQuery {
    private String orderId;

    // Getter only
}

// 2. QUERY HANDLER
@Service
public class GetOrderDetailsQueryHandler {

    @Autowired
    private MongoTemplate mongoTemplate;

    public OrderDetailsDTO handle(GetOrderDetailsQuery query) {
        // Simple query to read database
        // No business logic, just data retrieval

        return mongoTemplate.findOne(
            Query.query(Criteria.where("orderId").is(query.getOrderId())),
            OrderDetailsDTO.class,
            "order_details"
        );
    }
}

// 3. READ MODEL (DTO)
@Document(collection = "order_details")
public class OrderDetailsDTO {
    @Id
    private String orderId;

    private String userId;
    private String userName;          // Denormalized
    private String userEmail;         // Denormalized

    private List<OrderItemDTO> items; // with product names, images

    private BigDecimal totalAmount;
    private String status;
    private String shippingAddress;
    private String trackingNumber;
    private LocalDateTime estimatedDelivery;

    // Only getters (read-only)
}

// 4. CONTROLLER (Read)
@RestController
@RequestMapping("/orders")
public class OrderQueryController {

    @Autowired
    private GetOrderDetailsQueryHandler getOrderDetailsHandler;

    @GetMapping("/{orderId}")
    public ResponseEntity<OrderDetailsDTO> getOrderDetails(
        @PathVariable String orderId
    ) {
        GetOrderDetailsQuery query = new GetOrderDetailsQuery(orderId);
        OrderDetailsDTO orderDetails = getOrderDetailsHandler.handle(query);

        return ResponseEntity.ok(orderDetails);
    }
}


// ============ SYNCHRONIZATION ============

// EVENT LISTENER (Updates Read Model)
@Service
public class OrderProjectionUpdater {

    @Autowired
    private MongoTemplate mongoTemplate;

    @KafkaListener(topics = "order-events")
    public void handle(OrderCreatedEvent event) {
        // Build denormalized read model
        User user = userService.getUser(event.getUserId());

        OrderDetailsDTO dto = new OrderDetailsDTO();
        dto.setOrderId(event.getOrderId());
        dto.setUserId(event.getUserId());
        dto.setUserName(user.getName());      // Denormalize
        dto.setUserEmail(user.getEmail());    // Denormalize

        List<OrderItemDTO> itemDTOs = new ArrayList<>();
        for (OrderItem item : event.getItems()) {
            Product product = productService.getProduct(item.getProductId());

            OrderItemDTO itemDTO = new OrderItemDTO();
            itemDTO.setProductId(item.getProductId());
            itemDTO.setProductName(product.getName());  // Denormalize
            itemDTO.setImageUrl(product.getImageUrl()); // Denormalize
            itemDTO.setQuantity(item.getQuantity());
            itemDTO.setPrice(item.getPrice());

            itemDTOs.add(itemDTO);
        }
        dto.setItems(itemDTOs);

        dto.setTotalAmount(event.getTotalAmount());
        dto.setStatus("PENDING");
        dto.setShippingAddress(event.getShippingAddress());

        // Save to MongoDB (read database)
        mongoTemplate.save(dto, "order_details");
    }

    @KafkaListener(topics = "order-events")
    public void handle(OrderShippedEvent event) {
        // Update existing read model
        Query query = Query.query(Criteria.where("orderId").is(event.getOrderId()));
        Update update = new Update()
            .set("status", "SHIPPED")
            .set("trackingNumber", event.getTrackingNumber())
            .set("estimatedDelivery", event.getEstimatedDelivery());

        mongoTemplate.updateFirst(query, update, OrderDetailsDTO.class, "order_details");
    }
}
```

---

## Benefits of CQRS

```
┌─────────────────────────────────────────────────────────────────────────┐
│                        BENEFITS OF CQRS                                  │
└─────────────────────────────────────────────────────────────────────────┘

1. PERFORMANCE
──────────────
• Read model optimized for queries (denormalized, indexes)
• Write model optimized for writes (normalized, constraints)
• Can scale reads and writes independently

Example:
  Write: 1,000 orders/sec → PostgreSQL
  Read: 100,000 queries/sec → MongoDB + Elasticsearch


2. SCALABILITY
──────────────
• Scale read replicas (90% of traffic)
• Keep write database smaller
• Use CDN for read-heavy data

Example:
  1 write server + 10 read replicas


3. FLEXIBILITY
──────────────
• Different databases for different purposes
• Write: PostgreSQL (ACID)
• Read: MongoDB (fast queries)
• Search: Elasticsearch (full-text)


4. SIMPLICITY
─────────────
• Query handlers simple (no business logic)
• Command handlers focused (business logic only)
• Clear separation of concerns


5. MULTIPLE READ MODELS
────────────────────────
• Same data, different views
• Order list projection (for listing)
• Order details projection (for single order)
• Order analytics projection (for reporting)


6. EVENTUAL CONSISTENCY (Acceptable)
─────────────────────────────────────
• User places order → "Order processing" (immediate)
• User refreshes → "Order confirmed" (100ms later)
• Most users won't notice!
```

---

## When to Use CQRS?

```
┌─────────────────────────────────────────────────────────────────────────┐
│                      WHEN TO USE CQRS?                                   │
└─────────────────────────────────────────────────────────────────────────┘

✓ USE WHEN:
───────────

1. Different read/write performance needs
   • 100 writes/sec, 10k reads/sec

2. Complex queries that slow down writes
   • Reporting queries lock tables

3. Different scaling needs
   • Scale reads (add replicas)
   • Keep writes small

4. Multiple client types with different needs
   • Mobile app: simple DTO
   • Web app: rich DTO with images
   • Admin panel: detailed DTO with audit info

5. Domain complexity
   • Order processing with complex validation
   • But simple order listing

6. Event-driven architecture
   • Already using events
   • CQRS natural fit

7. Read-heavy system
   • Social media (lots of views, few posts)
   • E-commerce (lots of browsing, few purchases)


✗ DON'T USE WHEN:
─────────────────

1. Simple CRUD application
   • Basic blog, todo list

2. Small team unfamiliar with pattern
   • Learning curve high

3. Real-time consistency required
   • Stock trading (need immediate consistency)

4. Simple domain
   • No complex business logic
   • Traditional MVC sufficient

5. Low traffic
   • 100 users, simple queries
   • Over-engineering


ALTERNATIVES:
─────────────

• Traditional CRUD (for simple apps)
• Read replicas (for read-heavy without CQRS)
• Caching (Redis) (simple performance boost)
• Database views (denormalize without separate DB)
```

---

## Common Challenges & Solutions

```
┌─────────────────────────────────────────────────────────────────────────┐
│                    CQRS CHALLENGES & SOLUTIONS                           │
└─────────────────────────────────────────────────────────────────────────┘

1. EVENTUAL CONSISTENCY
───────────────────────

Challenge: User creates order, immediately queries → not found yet!

Solutions:
──────────

A) Return order ID immediately
   POST /orders → { orderId: "order_123", status: "processing" }
   Client polls: GET /orders/order_123

B) WebSocket notification
   POST /orders → 202 Accepted
   WebSocket → "Order order_123 ready!"

C) Optimistic UI
   Show "Order processing..." immediately
   Update when confirmed

D) Command includes read model update
   Before returning, ensure read model updated


2. DATA SYNCHRONIZATION FAILURE
────────────────────────────────

Challenge: Event published, but read model update fails

Solutions:
──────────

A) Retry with exponential backoff
   @Retryable(maxAttempts = 5, backoff = @Backoff(delay = 1000))

B) Dead letter queue
   Failed events → DLQ → Manual investigation

C) Idempotent event handlers
   Check if already processed (by event ID)

D) Event store as source of truth
   Can rebuild read model anytime from events


3. READ MODEL CORRUPTION
────────────────────────

Challenge: Bug in event handler corrupted read model

Solution:
─────────

A) Rebuild from events
   1. Delete read model data
   2. Replay all events
   3. Read model rebuilt correctly ✓

Code:
─────
public void rebuildProjection() {
    // Delete projection
    mongoTemplate.dropCollection("order_details");

    // Replay all events
    List<Event> events = eventStore.getAllEvents("OrderCreatedEvent");
    for (Event event : events) {
        orderProjectionUpdater.handle(event);
    }
}


4. QUERY PERFORMANCE
────────────────────

Challenge: Complex query still slow on read model

Solutions:
──────────

A) Better indexes
   CREATE INDEX idx_user_orders ON order_details(userId, createdAt DESC);

B) Materialized views
   Pre-compute expensive aggregations

C) Separate projection per query type
   • OrderListProjection (simple, fast)
   • OrderAnalyticsProjection (complex aggregations)

D) Caching
   Redis cache for hot data


5. DEBUGGING COMPLEXITY
───────────────────────

Challenge: Hard to trace command → event → projection

Solutions:
──────────

A) Correlation ID
   Track ID through entire flow
   Command (correlation_id: 123)
   → Event (correlation_id: 123)
   → Projection update (correlation_id: 123)

B) Distributed tracing
   Use Zipkin, Jaeger

C) Event versioning
   Track which event version updated which projection
```

---

## CQRS vs Traditional Architecture

```
┌─────────────────────────────────────────────────────────────────────────┐
│                 CQRS vs TRADITIONAL COMPARISON                           │
└─────────────────────────────────────────────────────────────────────────┘

╔═══════════════════╦═════════════════════╦══════════════════════╗
║   Feature         ║   Traditional       ║       CQRS           ║
╠═══════════════════╬═════════════════════╬══════════════════════╣
║ Model             ║ Single model        ║ Separate models      ║
║                   ║ (read & write)      ║ (command & query)    ║
╠═══════════════════╬═════════════════════╬══════════════════════╣
║ Database          ║ One database        ║ Can use different DBs║
║                   ║                     ║ (write: PG, read: MG)║
╠═══════════════════╬═════════════════════╬══════════════════════╣
║ Consistency       ║ Immediate           ║ Eventual             ║
║                   ║ (ACID)              ║ (100ms lag typical)  ║
╠═══════════════════╬═════════════════════╬══════════════════════╣
║ Complexity        ║ Low                 ║ High                 ║
╠═══════════════════╬═════════════════════╬══════════════════════╣
║ Scalability       ║ Vertical            ║ Horizontal           ║
║                   ║ (bigger server)     ║ (more servers)       ║
╠═══════════════════╬═════════════════════╬══════════════════════╣
║ Performance       ║ Good for small      ║ Excellent for large  ║
║ (Reads)           ║ scale               ║ scale                ║
╠═══════════════════╬═════════════════════╬══════════════════════╣
║ Performance       ║ Good                ║ Good                 ║
║ (Writes)          ║                     ║                      ║
╠═══════════════════╬═════════════════════╬══════════════════════╣
║ Use Case          ║ Most apps           ║ High-scale,          ║
║                   ║                     ║ complex domains      ║
╚═══════════════════╩═════════════════════╩══════════════════════╝
```

---

## System Design Interview Answer

**Question: "What is CQRS and when would you use it?"**

**Answer:**

"CQRS stands for Command Query Responsibility Segregation. It's a pattern that separates **write operations** (commands) from **read operations** (queries) into different models.

**How it works:**
- **Command side**: Handles writes, enforces business rules, saves to write database (PostgreSQL)
- **Query side**: Handles reads, optimized for fast queries, reads from read database (MongoDB/Elasticsearch)
- **Synchronization**: Events published to Kafka, update read models asynchronously

**Key Concepts:**
- **Commands**: CreateOrder, UpdateUser (intent to change state)
- **Queries**: GetOrderDetails, FindUsers (request for data)
- **Eventual Consistency**: Read model lags behind writes (typically 50-100ms)

**Benefits:**
- Scale reads and writes independently (10x read replicas)
- Use different databases optimized for each purpose
- Denormalized read models for fast queries
- Clear separation of concerns

**Use When:**
- High read-to-write ratio (e-commerce: lots of browsing, few purchases)
- Complex queries slow down writes
- Need different scaling for reads vs writes
- Already using event-driven architecture

**Don't Use When:**
- Simple CRUD app
- Immediate consistency required
- Small scale (over-engineering)

**Real Example:**
In an e-commerce system:
- Write side: Order validation, payment processing (PostgreSQL)
- Read side: Product catalog, order history (MongoDB + Elasticsearch)
- 90% traffic goes to read side → can scale independently

**Trade-off:**
Accept eventual consistency (user may not see order immediately) for better performance and scalability."

---

## Key Takeaways

✓ **Separate concerns**: Commands (write) vs Queries (read)

✓ **Different models**: Optimized for different purposes

✓ **Different databases**: Can use best tool for each job

✓ **Scale independently**: Scale reads (90% traffic) more than writes

✓ **Denormalize reads**: Fast queries, no joins

✓ **Eventual consistency**: Acceptable delay (50-100ms typical)

✓ **Event-driven**: Often combined with Event Sourcing

✓ **Not for everything**: Use when complexity justified

✓ **Multiple read models**: Same data, different views
