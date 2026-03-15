# Spring Boot Transaction Propagation

## Overview
Transaction propagation defines how transactions relate to each other when one transactional method calls another. Spring supports 7 propagation types defined in the `@Transactional` annotation.

## Propagation Types

### 1. REQUIRED (Default)
- **Behavior**: Uses existing transaction if available, creates new one if not
- **Use Case**: Most common, standard CRUD operations

```java
@Service
public class UserService {

    @Transactional(propagation = Propagation.REQUIRED)
    public void createUser(User user) {
        userRepository.save(user);
        // If caller has transaction, uses it
        // If no transaction exists, creates new one
    }

    @Transactional
    public void registerUser(User user) {
        createUser(user); // Uses same transaction
        sendWelcomeEmail(user); // All in one transaction
    }
}
```

**Result**: Single transaction for all operations. If any fails, all rollback.

---

### 2. REQUIRES_NEW
- **Behavior**: Always creates a NEW transaction, suspends existing one
- **Use Case**: Audit logging, independent operations that must succeed even if parent fails

```java
@Service
public class OrderService {
    @Autowired
    private AuditService auditService;

    @Transactional
    public void processOrder(Order order) {
        orderRepository.save(order);
        auditService.logActivity("Order created"); // New transaction

        if (order.getAmount() > 10000) {
            throw new RuntimeException("Amount too high");
        }
        // Order rolls back, but audit log is COMMITTED
    }
}

@Service
public class AuditService {
    @Transactional(propagation = Propagation.REQUIRES_NEW)
    public void logActivity(String message) {
        auditRepository.save(new AuditLog(message));
        // This commits independently
    }
}
```

**Result**: Audit log saved even if order processing fails.

---

### 3. SUPPORTS
- **Behavior**: Uses transaction if exists, runs non-transactionally otherwise
- **Use Case**: Read-only operations, optional transactional behavior

```java
@Service
public class ReportService {

    @Transactional(propagation = Propagation.SUPPORTS, readOnly = true)
    public List<User> getUsers() {
        return userRepository.findAll();
        // Joins transaction if caller has one
        // Runs without transaction if no caller transaction
    }
}
```

---

### 4. NOT_SUPPORTED
- **Behavior**: Always runs non-transactionally, suspends existing transaction
- **Use Case**: Performance-critical reads, operations that shouldn't be in transactions

```java
@Service
public class CacheService {

    @Transactional(propagation = Propagation.NOT_SUPPORTED)
    public void updateCache(String key, Object value) {
        // Suspends any existing transaction
        // Runs without transaction overhead
        cache.put(key, value);
    }
}
```

---

### 5. MANDATORY
- **Behavior**: Requires existing transaction, throws exception if none exists
- **Use Case**: Internal service methods that should only be called within transactions

```java
@Service
public class PaymentService {

    @Transactional(propagation = Propagation.MANDATORY)
    public void processPayment(Payment payment) {
        // Throws IllegalTransactionStateException if no transaction
        paymentRepository.save(payment);
    }

    @Transactional
    public void completeOrder(Order order) {
        processPayment(order.getPayment()); // OK, transaction exists
    }
}
```

---

### 6. NEVER
- **Behavior**: Must run non-transactionally, throws exception if transaction exists
- **Use Case**: Operations that must not be in transactions (rare)

```java
@Service
public class ExternalApiService {

    @Transactional(propagation = Propagation.NEVER)
    public void callExternalAPI() {
        // Throws IllegalTransactionStateException if transaction exists
        // Ensures no transaction overhead for external calls
        restTemplate.getForObject("https://api.example.com", String.class);
    }
}
```

---

### 7. NESTED
- **Behavior**: Creates nested transaction (savepoint) if transaction exists
- **Use Case**: Partial rollback scenarios
- **Note**: Requires JDBC 3.0+ and database support for savepoints

```java
@Service
public class OrderService {
    @Autowired
    private InventoryService inventoryService;

    @Transactional
    public void processOrder(Order order) {
        orderRepository.save(order);

        try {
            inventoryService.reserveItems(order.getItems());
        } catch (Exception e) {
            // Only nested transaction rolls back
            // Parent transaction can still commit
        }

        notificationService.sendConfirmation(order);
    }
}

@Service
public class InventoryService {
    @Transactional(propagation = Propagation.NESTED)
    public void reserveItems(List<Item> items) {
        // Creates savepoint
        // Can rollback to savepoint without affecting parent
        items.forEach(item -> inventoryRepository.updateStock(item));
    }
}
```

---

## Complete REST API Example

### 1. Dependencies (pom.xml)
```xml
<dependencies>
    <dependency>
        <groupId>org.springframework.boot</groupId>
        <artifactId>spring-boot-starter-web</artifactId>
    </dependency>
    <dependency>
        <groupId>org.springframework.boot</groupId>
        <artifactId>spring-boot-starter-data-jpa</artifactId>
    </dependency>
    <dependency>
        <groupId>com.h2database</groupId>
        <artifactId>h2</artifactId>
        <scope>runtime</scope>
    </dependency>
    <dependency>
        <groupId>org.springframework.boot</groupId>
        <artifactId>spring-boot-starter-validation</artifactId>
    </dependency>
</dependencies>
```

### 2. Application Properties
```properties
spring.application.name=transaction-demo
spring.datasource.url=jdbc:h2:mem:testdb
spring.datasource.driver-class-name=org.h2.Driver
spring.jpa.hibernate.ddl-auto=create-drop
spring.jpa.show-sql=true
spring.h2.console.enabled=true
```

### 3. Entity Classes
```java
@Entity
@Table(name = "orders")
public class Order {
    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    private String customerName;
    private BigDecimal amount;
    private LocalDateTime orderDate;

    @Enumerated(EnumType.STRING)
    private OrderStatus status;

    // Getters and setters
}

@Entity
@Table(name = "audit_logs")
public class AuditLog {
    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    private String action;
    private String entity;
    private LocalDateTime timestamp;

    // Getters and setters
}

@Entity
@Table(name = "payments")
public class Payment {
    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    private Long orderId;
    private BigDecimal amount;
    private String method;

    // Getters and setters
}

enum OrderStatus {
    PENDING, CONFIRMED, CANCELLED
}
```

### 4. Repository Layer
```java
@Repository
public interface OrderRepository extends JpaRepository<Order, Long> {
    List<Order> findByCustomerName(String customerName);
}

@Repository
public interface AuditLogRepository extends JpaRepository<AuditLog, Long> {
}

@Repository
public interface PaymentRepository extends JpaRepository<Payment, Long> {
}
```

### 5. Service Layer with Propagation Examples
```java
@Service
@Slf4j
public class OrderService {

    @Autowired
    private OrderRepository orderRepository;

    @Autowired
    private AuditService auditService;

    @Autowired
    private PaymentService paymentService;

    // REQUIRED - Standard operation
    @Transactional
    public Order createOrder(Order order) {
        log.info("Creating order in transaction");
        order.setOrderDate(LocalDateTime.now());
        order.setStatus(OrderStatus.PENDING);
        Order saved = orderRepository.save(order);

        // Audit uses REQUIRES_NEW - independent transaction
        auditService.logOrderCreation(saved.getId());

        return saved;
    }

    // Demonstrates rollback behavior
    @Transactional
    public Order createOrderWithPayment(Order order, Payment payment) {
        Order saved = createOrder(order); // Uses same transaction

        payment.setOrderId(saved.getId());
        paymentService.processPayment(payment); // MANDATORY - needs transaction

        // If payment fails, entire operation rolls back (except audit)
        saved.setStatus(OrderStatus.CONFIRMED);
        return orderRepository.save(saved);
    }

    // SUPPORTS - works with or without transaction
    @Transactional(propagation = Propagation.SUPPORTS, readOnly = true)
    public Order getOrder(Long id) {
        return orderRepository.findById(id)
            .orElseThrow(() -> new RuntimeException("Order not found"));
    }

    @Transactional(propagation = Propagation.SUPPORTS, readOnly = true)
    public List<Order> getAllOrders() {
        return orderRepository.findAll();
    }

    @Transactional
    public void cancelOrder(Long id) {
        Order order = getOrder(id);
        order.setStatus(OrderStatus.CANCELLED);
        orderRepository.save(order);
        auditService.logOrderCancellation(id);
    }
}

@Service
@Slf4j
public class AuditService {

    @Autowired
    private AuditLogRepository auditRepository;

    // REQUIRES_NEW - always creates new transaction
    @Transactional(propagation = Propagation.REQUIRES_NEW)
    public void logOrderCreation(Long orderId) {
        log.info("Logging in NEW transaction");
        AuditLog log = new AuditLog();
        log.setAction("ORDER_CREATED");
        log.setEntity("Order:" + orderId);
        log.setTimestamp(LocalDateTime.now());
        auditRepository.save(log);
        // Commits immediately, independent of caller
    }

    @Transactional(propagation = Propagation.REQUIRES_NEW)
    public void logOrderCancellation(Long orderId) {
        AuditLog log = new AuditLog();
        log.setAction("ORDER_CANCELLED");
        log.setEntity("Order:" + orderId);
        log.setTimestamp(LocalDateTime.now());
        auditRepository.save(log);
    }

    // SUPPORTS - read operation
    @Transactional(propagation = Propagation.SUPPORTS, readOnly = true)
    public List<AuditLog> getAllLogs() {
        return auditRepository.findAll();
    }
}

@Service
@Slf4j
public class PaymentService {

    @Autowired
    private PaymentRepository paymentRepository;

    // MANDATORY - requires existing transaction
    @Transactional(propagation = Propagation.MANDATORY)
    public Payment processPayment(Payment payment) {
        log.info("Processing payment in MANDATORY transaction");

        if (payment.getAmount().compareTo(BigDecimal.ZERO) <= 0) {
            throw new RuntimeException("Invalid payment amount");
        }

        return paymentRepository.save(payment);
    }

    // NOT_SUPPORTED - runs without transaction
    @Transactional(propagation = Propagation.NOT_SUPPORTED)
    public void logPaymentToExternalSystem(Payment payment) {
        log.info("Logging to external system (no transaction)");
        // Simulate external API call
    }
}
```

### 6. REST Controller
```java
@RestController
@RequestMapping("/api/orders")
@Slf4j
public class OrderController {

    @Autowired
    private OrderService orderService;

    @Autowired
    private AuditService auditService;

    @PostMapping
    public ResponseEntity<Order> createOrder(@RequestBody Order order) {
        log.info("POST /api/orders - Creating order");
        Order created = orderService.createOrder(order);
        return ResponseEntity.ok(created);
    }

    @PostMapping("/with-payment")
    public ResponseEntity<Order> createOrderWithPayment(
            @RequestBody OrderPaymentRequest request) {
        log.info("POST /api/orders/with-payment");
        Order created = orderService.createOrderWithPayment(
            request.getOrder(),
            request.getPayment()
        );
        return ResponseEntity.ok(created);
    }

    @GetMapping("/{id}")
    public ResponseEntity<Order> getOrder(@PathVariable Long id) {
        Order order = orderService.getOrder(id);
        return ResponseEntity.ok(order);
    }

    @GetMapping
    public ResponseEntity<List<Order>> getAllOrders() {
        List<Order> orders = orderService.getAllOrders();
        return ResponseEntity.ok(orders);
    }

    @DeleteMapping("/{id}")
    public ResponseEntity<Void> cancelOrder(@PathVariable Long id) {
        orderService.cancelOrder(id);
        return ResponseEntity.noContent().build();
    }

    @GetMapping("/audit-logs")
    public ResponseEntity<List<AuditLog>> getAuditLogs() {
        List<AuditLog> logs = auditService.getAllLogs();
        return ResponseEntity.ok(logs);
    }
}

// DTO for request
class OrderPaymentRequest {
    private Order order;
    private Payment payment;

    // Getters and setters
}
```

### 7. Exception Handling
```java
@RestControllerAdvice
public class GlobalExceptionHandler {

    @ExceptionHandler(IllegalTransactionStateException.class)
    public ResponseEntity<ErrorResponse> handleTransactionException(
            IllegalTransactionStateException ex) {
        return ResponseEntity
            .status(HttpStatus.INTERNAL_SERVER_ERROR)
            .body(new ErrorResponse("Transaction error: " + ex.getMessage()));
    }

    @ExceptionHandler(RuntimeException.class)
    public ResponseEntity<ErrorResponse> handleRuntimeException(
            RuntimeException ex) {
        return ResponseEntity
            .status(HttpStatus.BAD_REQUEST)
            .body(new ErrorResponse(ex.getMessage()));
    }
}

class ErrorResponse {
    private String message;
    private LocalDateTime timestamp;

    public ErrorResponse(String message) {
        this.message = message;
        this.timestamp = LocalDateTime.now();
    }

    // Getters
}
```

### 8. Main Application
```java
@SpringBootApplication
public class TransactionDemoApplication {
    public static void main(String[] args) {
        SpringApplication.run(TransactionDemoApplication.class, args);
    }
}
```

## Testing Transaction Propagation

### Test with cURL:

```bash
# Create order (REQUIRED + REQUIRES_NEW for audit)
curl -X POST http://localhost:8080/api/orders \
  -H "Content-Type: application/json" \
  -d '{
    "customerName": "John Doe",
    "amount": 100.00
  }'

# Create order with payment (demonstrates MANDATORY)
curl -X POST http://localhost:8080/api/orders/with-payment \
  -H "Content-Type: application/json" \
  -d '{
    "order": {
      "customerName": "Jane Smith",
      "amount": 250.00
    },
    "payment": {
      "amount": 250.00,
      "method": "CREDIT_CARD"
    }
  }'

# Get all orders
curl http://localhost:8080/api/orders

# Get audit logs
curl http://localhost:8080/api/orders/audit-logs

# Cancel order
curl -X DELETE http://localhost:8080/api/orders/1
```

## Key Takeaways

1. **REQUIRED**: Default, most common - join or create
2. **REQUIRES_NEW**: Independent operations (audit logs, notifications)
3. **MANDATORY**: Enforce transactional context for critical operations
4. **SUPPORTS**: Flexible read operations
5. **NOT_SUPPORTED**: Avoid transaction overhead
6. **NESTED**: Partial rollback with savepoints
7. **NEVER**: Ensure non-transactional execution

## Transaction Propagation Matrix

| Propagation | Existing TX | No TX | Suspends TX | Creates New | Savepoint |
|-------------|-------------|-------|-------------|-------------|-----------|
| REQUIRED    | Uses it     | Creates | No | Yes (if needed) | No |
| REQUIRES_NEW | Suspends | Creates | Yes | Always | No |
| SUPPORTS | Uses it | None | No | No | No |
| NOT_SUPPORTED | Suspends | None | Yes | No | No |
| MANDATORY | Uses it | Exception | No | No | No |
| NEVER | Exception | None | N/A | No | No |
| NESTED | Savepoint | Creates | No | Yes (if needed) | Yes |

