# How UPI Handles 4 Crore (40 Million) Transactions Per Hour Without System Failure

> **Interview Level**: Senior Engineer (5+ Years)
> **Real Stats**: UPI processes 12+ Billion transactions/month (2024)
> **Peak Load**: 4 crore (40 million) transactions/hour during festivals

---

## 📋 Table of Contents

1. [Problem Statement](#problem-statement)
2. [The Scale Challenge](#the-scale-challenge)
3. [UPI Architecture Overview](#upi-architecture-overview)
4. [Key Design Strategies](#key-design-strategies)
5. [Database Architecture](#database-architecture)
6. [Failure Handling](#failure-handling)
7. [Interview Q&A](#interview-qa)
8. [Production Code Examples](#production-code-examples)

---

## Problem Statement

**Interviewer**: "How does UPI handle 4 crore transactions per hour without system failure?"

**What They're Testing**:
- High-throughput system design
- Database scaling strategies
- Distributed system reliability
- Transaction consistency
- Failure handling

---

## The Scale Challenge

### Breaking Down 4 Crore Transactions/Hour

```
4 Crore transactions/hour = 40,000,000 transactions/hour
                          = 666,666 transactions/minute
                          = 11,111 transactions/second (TPS)

Peak load (festivals): 20,000+ TPS
```

### Why This Is Hard

```
┌─────────────────────────────────────────────────────┐
│           CHALLENGES AT THIS SCALE                  │
├─────────────────────────────────────────────────────┤
│                                                     │
│  ⚡ Speed:     Each transaction < 3 seconds        │
│  🔐 Security:  Money at stake, zero tolerance      │
│  ✅ Accuracy:  No duplicate/lost transactions      │
│  🔄 Rollback:  Failed transactions must revert     │
│  📊 Audit:     Complete transaction trail          │
│  🌐 Network:   Unreliable mobile networks          │
│                                                     │
└─────────────────────────────────────────────────────┘
```

---

## UPI Architecture Overview

### High-Level System Flow

```
┌──────────────┐
│   USER APP   │  (PhonePe, GPay, Paytm)
│   (Mobile)   │
└──────┬───────┘
       │ 1. Initiate Payment
       │
       ▼
┌─────────────────────────────────────────────────────┐
│              API GATEWAY + LOAD BALANCER            │
│        (Kong/AWS ALB - 100,000+ req/sec)            │
└──────────────────┬──────────────────────────────────┘
                   │
       ┌───────────┴───────────┐
       ▼                       ▼
┌──────────────┐        ┌──────────────┐
│  PSP Server  │        │  PSP Server  │  (Payment Service Provider)
│  (Instance1) │ ....   │  (Instance N)│  PhonePe, GPay backend
└──────┬───────┘        └──────┬───────┘
       │                       │
       └───────────┬───────────┘
                   │ 2. Validate & Route
                   ▼
┌─────────────────────────────────────────────────────┐
│              NPCI (National Payments Corp)          │
│         - Central Switch (handles routing)          │
│         - Validates VPA (abc@paytm)                 │
│         - Routes to correct bank                    │
└──────────────────┬──────────────────────────────────┘
                   │
       ┌───────────┴───────────┐
       ▼                       ▼
┌──────────────┐        ┌──────────────┐
│  HDFC Bank   │        │  SBI Bank    │
│   Backend    │  ....  │   Backend    │
└──────┬───────┘        └──────┬───────┘
       │                       │
       │ 3. Debit/Credit       │
       ▼                       ▼
┌──────────────┐        ┌──────────────┐
│   Database   │        │   Database   │
│  (Sharded)   │        │  (Sharded)   │
└──────────────┘        └──────────────┘
```

**Flow Explanation**:
1. User initiates payment on PhonePe/GPay
2. Request goes to PSP servers (PhonePe backend)
3. PSP forwards to NPCI central switch
4. NPCI routes to sender's bank (debit) and receiver's bank (credit)
5. Both banks update their databases
6. Success confirmation flows back to user

---

## Key Design Strategies

### 1. Horizontal Scaling (Microservices)

```
┌────────────────────────────────────────────────────────────┐
│                    UPI MICROSERVICES                       │
├────────────────────────────────────────────────────────────┤
│                                                            │
│  ┌────────────┐  ┌────────────┐  ┌────────────┐          │
│  │ Payment    │  │  Account   │  │  Fraud     │          │
│  │ Service    │  │  Service   │  │  Detection │          │
│  │ (100 pods) │  │  (50 pods) │  │  (30 pods) │          │
│  └────────────┘  └────────────┘  └────────────┘          │
│                                                            │
│  ┌────────────┐  ┌────────────┐  ┌────────────┐          │
│  │ Notification│  │  Audit     │  │  Reconcile │          │
│  │ Service    │  │  Service   │  │  Service   │          │
│  │ (20 pods)  │  │  (40 pods) │  │  (10 pods) │          │
│  └────────────┘  └────────────┘  └────────────┘          │
│                                                            │
└────────────────────────────────────────────────────────────┘
      ▲              ▲              ▲
      │              │              │
   Scale up during peak hours (Auto-scaling)
```

**Key Point**: Each service scales independently based on load.

---

### 2. Database Sharding (Horizontal Partitioning)

```
┌─────────────────────────────────────────────────────┐
│         SHARDING BY USER_ID / ACCOUNT_ID            │
├─────────────────────────────────────────────────────┤
│                                                     │
│  User ID: 1-10M      │  User ID: 10M-20M           │
│  ┌──────────────┐    │  ┌──────────────┐          │
│  │   Shard 1    │    │  │   Shard 2    │          │
│  │  Database    │    │  │  Database    │          │
│  │  Primary +   │    │  │  Primary +   │          │
│  │  2 Replicas  │    │  │  2 Replicas  │          │
│  └──────────────┘    │  └──────────────┘          │
│                      │                             │
│  User ID: 20M-30M    │  User ID: 30M-40M           │
│  ┌──────────────┐    │  ┌──────────────┐          │
│  │   Shard 3    │    │  │   Shard N    │          │
│  │  Database    │    │  │  Database    │          │
│  └──────────────┘    │  └──────────────┘          │
│                                                     │
└─────────────────────────────────────────────────────┘

Route Logic: shard_id = hash(user_id) % total_shards
```

**Benefits**:
- Each shard handles ~1-2 million users
- No single database bottleneck
- Easy to add more shards

---

### 3. Read Replicas (Read-Write Separation)

```
┌─────────────────────────────────────────────────────┐
│              WRITE (1 Primary)                      │
│                                                     │
│         ┌─────────────────────┐                    │
│         │   PRIMARY DATABASE  │                    │
│         │  (All Writes Here)  │                    │
│         └──────────┬──────────┘                    │
│                    │ Replication                    │
│                    │                                │
└────────────────────┼────────────────────────────────┘
                     │
        ┌────────────┼────────────┐
        │            │            │
        ▼            ▼            ▼
┌──────────────────────────────────────────────────┐
│           READ (Multiple Replicas)               │
│                                                  │
│  ┌────────────┐  ┌────────────┐  ┌────────────┐ │
│  │  Replica 1 │  │  Replica 2 │  │  Replica 3 │ │
│  │  (Balance  │  │  (Balance  │  │  (Balance  │ │
│  │   Check)   │  │   Check)   │  │   Check)   │ │
│  └────────────┘  └────────────┘  └────────────┘ │
│                                                  │
└──────────────────────────────────────────────────┘
```

**Read/Write Ratio**: 80% reads (balance check), 20% writes (transaction)

---

### 4. Caching Strategy (Redis)

```
┌─────────────────────────────────────────────────────┐
│                  CACHE LAYERS                       │
├─────────────────────────────────────────────────────┤
│                                                     │
│  L1 Cache (Application Memory)                     │
│  ┌─────────────────────────────┐                   │
│  │  User Session: 5 min TTL    │                   │
│  │  Bank Details: 1 hour TTL   │                   │
│  └─────────────────────────────┘                   │
│           │                                         │
│           ▼ Cache Miss                              │
│  L2 Cache (Redis Cluster)                          │
│  ┌─────────────────────────────┐                   │
│  │  Account Balance: 30s TTL   │                   │
│  │  User Profile: 10 min TTL   │                   │
│  │  IFSC Codes: No expiry      │                   │
│  └─────────────────────────────┘                   │
│           │                                         │
│           ▼ Cache Miss                              │
│  Database (Source of Truth)                        │
│  ┌─────────────────────────────┐                   │
│  │  Persistent Storage         │                   │
│  └─────────────────────────────┘                   │
│                                                     │
└─────────────────────────────────────────────────────┘
```

**Cache Hit Ratio**: 95%+ (saves 95% of database queries)

---

### 5. Asynchronous Processing (Message Queue)

```
┌────────────────────────────────────────────────────────┐
│           SYNCHRONOUS vs ASYNCHRONOUS                  │
├────────────────────────────────────────────────────────┤
│                                                        │
│  SYNCHRONOUS (User waits)                             │
│  ┌──────────┐                                         │
│  │  Debit   │ → Debit Account                         │
│  │  Credit  │ → Credit Account                        │
│  │  Verify  │ → Transaction Verification              │
│  └──────────┘                                         │
│  Total: 2-3 seconds                                   │
│                                                        │
│  ────────────────────────────────────────────────     │
│                                                        │
│  ASYNCHRONOUS (User gets instant response)            │
│  ┌──────────┐                                         │
│  │  Debit   │ → Debit Account  (500ms)                │
│  │  Credit  │ → Credit Account (500ms)                │
│  └────┬─────┘                                         │
│       │                                                │
│       │ Publish to Queue                              │
│       ▼                                                │
│  ┌──────────────────────────┐                        │
│  │   MESSAGE QUEUE (Kafka)  │                        │
│  └────────┬─────────────────┘                        │
│           │                                            │
│           │ Background Processing                     │
│           │                                            │
│     ┌─────┴─────┬───────────┬────────────┐           │
│     ▼           ▼           ▼            ▼           │
│  ┌──────┐  ┌──────┐  ┌──────┐  ┌──────────┐         │
│  │ SMS  │  │Email │  │ Audit│  │Analytics │         │
│  │Worker│  │Worker│  │Logger│  │ Worker   │         │
│  └──────┘  └──────┘  └──────┘  └──────────┘         │
│                                                        │
└────────────────────────────────────────────────────────┘
```

**Result**: User sees success in 1 second, rest happens in background.

---

## Database Architecture

### Transaction Table Design

```sql
-- Sharded by user_id
CREATE TABLE transactions (
    transaction_id VARCHAR(50) PRIMARY KEY,
    user_id BIGINT NOT NULL,                -- Shard key
    payer_vpa VARCHAR(100) NOT NULL,        -- abc@paytm
    payee_vpa VARCHAR(100) NOT NULL,        -- xyz@phonepe
    amount DECIMAL(15, 2) NOT NULL,
    status VARCHAR(20) NOT NULL,            -- PENDING, SUCCESS, FAILED

    -- Idempotency
    idempotency_key VARCHAR(100) UNIQUE,    -- Prevent duplicate

    -- Audit
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),

    -- Performance
    INDEX idx_user_date (user_id, created_at),
    INDEX idx_status (status),
    INDEX idx_idempotency (idempotency_key)
) PARTITION BY RANGE (created_at);

-- Monthly partitions for better performance
CREATE TABLE transactions_2024_03 PARTITION OF transactions
    FOR VALUES FROM ('2024-03-01') TO ('2024-04-01');
```

### Idempotency Pattern

```java
@Service
public class PaymentService {

    @Autowired
    private TransactionRepository transactionRepository;

    @Transactional(isolation = Isolation.READ_COMMITTED)
    public TransactionResponse processPayment(PaymentRequest request) {

        // 1. Check idempotency key (prevent duplicate processing)
        String idempotencyKey = request.getIdempotencyKey();
        Transaction existing = transactionRepository
            .findByIdempotencyKey(idempotencyKey);

        if (existing != null) {
            // Already processed - return cached result
            return new TransactionResponse(existing);
        }

        // 2. Create transaction record (status = PENDING)
        Transaction txn = new Transaction();
        txn.setTransactionId(generateTxnId());
        txn.setIdempotencyKey(idempotencyKey);
        txn.setPayerVpa(request.getPayerVpa());
        txn.setPayeeVpa(request.getPayeeVpa());
        txn.setAmount(request.getAmount());
        txn.setStatus(TransactionStatus.PENDING);

        transactionRepository.save(txn);

        try {
            // 3. Debit payer account
            accountService.debit(request.getPayerVpa(), request.getAmount());

            // 4. Credit payee account
            accountService.credit(request.getPayeeVpa(), request.getAmount());

            // 5. Update status to SUCCESS
            txn.setStatus(TransactionStatus.SUCCESS);
            transactionRepository.save(txn);

            // 6. Publish event for async processing (SMS, email, audit)
            kafkaProducer.send("payment-success", txn);

            return new TransactionResponse(txn);

        } catch (Exception e) {
            // Rollback logic
            txn.setStatus(TransactionStatus.FAILED);
            txn.setErrorMessage(e.getMessage());
            transactionRepository.save(txn);

            kafkaProducer.send("payment-failed", txn);

            throw new PaymentException("Payment failed", e);
        }
    }

    private String generateTxnId() {
        // Format: UPI2024031512345678
        return "UPI" + LocalDate.now().format(DateTimeFormatter.BASIC_ISO_DATE)
                + RandomStringUtils.randomNumeric(8);
    }
}
```

---

## Failure Handling

### 1. Network Timeout Handling

```
┌────────────────────────────────────────────────────────┐
│            NETWORK TIMEOUT SCENARIO                    │
├────────────────────────────────────────────────────────┤
│                                                        │
│  User → PSP → NPCI → Bank → [TIMEOUT]                 │
│                                                        │
│  Problem: Money deducted but confirmation not received│
│                                                        │
│  Solution: RECONCILIATION                             │
│                                                        │
│  ┌──────────────────────────────────────┐            │
│  │  1. Mark transaction as "PENDING"    │            │
│  │  2. Retry with exponential backoff   │            │
│  │     - Retry 1: After 5 seconds       │            │
│  │     - Retry 2: After 15 seconds      │            │
│  │     - Retry 3: After 45 seconds      │            │
│  │  3. If still fails → Manual review   │            │
│  │  4. Daily reconciliation job         │            │
│  └──────────────────────────────────────┘            │
│                                                        │
└────────────────────────────────────────────────────────┘
```

### 2. Database Failure (Circuit Breaker)

```java
@Service
public class PaymentService {

    @CircuitBreaker(name = "paymentDB", fallbackMethod = "paymentFallback")
    @Retry(name = "paymentDB", maxAttempts = 3)
    public TransactionResponse processPayment(PaymentRequest request) {
        // Normal payment processing
        return performPayment(request);
    }

    // Fallback method when DB is down
    public TransactionResponse paymentFallback(
            PaymentRequest request, Exception e) {

        // Store in message queue for later processing
        kafkaProducer.send("payment-retry-queue", request);

        return TransactionResponse.builder()
            .status("PENDING")
            .message("Payment queued. Will be processed shortly.")
            .build();
    }
}
```

### Circuit Breaker States

```
┌─────────────────────────────────────────────────────┐
│          CIRCUIT BREAKER STATE MACHINE              │
├─────────────────────────────────────────────────────┤
│                                                     │
│  CLOSED (Normal)                                    │
│  ┌────────────┐                                     │
│  │ All requests                                     │
│  │ go through  │                                    │
│  └──────┬──────┘                                    │
│         │ Failures > Threshold                      │
│         ▼                                           │
│  OPEN (Failing)                                     │
│  ┌────────────┐                                     │
│  │ All requests│ ← Immediate fallback               │
│  │ rejected    │                                    │
│  └──────┬──────┘                                    │
│         │ After timeout (60s)                       │
│         ▼                                           │
│  HALF-OPEN (Testing)                                │
│  ┌────────────┐                                     │
│  │ Try limited │                                    │
│  │ requests    │                                    │
│  └──────┬──────┘                                    │
│         │                                           │
│    ┌────┴────┐                                      │
│    │         │                                      │
│  Success   Failure                                  │
│    │         │                                      │
│    ▼         ▼                                      │
│  CLOSED    OPEN                                     │
│                                                     │
└─────────────────────────────────────────────────────┘
```

---

## Interview Q&A

### Q1: How do you prevent duplicate transactions?

**Answer**:
```
1. Idempotency Key: Client generates unique key for each request
   - Format: {user_id}_{timestamp}_{random}
   - Store in database with UNIQUE constraint
   - If duplicate request comes, return cached result

2. Database Constraint:
   ALTER TABLE transactions
   ADD CONSTRAINT unique_idempotency
   UNIQUE (idempotency_key);

3. Client-side check:
   - Disable "Pay" button after first click
   - Show "Processing..." state
```

### Q2: What if bank's database goes down during transaction?

**Answer**:
```
1. Transaction Status: Mark as "PENDING"

2. Retry Logic:
   - Exponential backoff (5s, 15s, 45s, 2m, 5m)
   - Max 5 retries

3. Circuit Breaker:
   - After 50% failures, stop sending requests
   - Return "Bank temporarily unavailable" to user

4. Reconciliation:
   - Daily job checks all PENDING transactions
   - Contact bank's reconciliation API
   - Update status accordingly

5. User Notification:
   - SMS: "Transaction pending, will be updated in 30 mins"
   - Push notification when resolved
```

### Q3: How do you handle 20,000 TPS during festival sales?

**Answer**:
```
1. Auto-Scaling:
   - Kubernetes HPA (Horizontal Pod Autoscaler)
   - Scale from 100 pods to 500 pods automatically
   - Trigger: CPU > 70% or Request Rate > 10K/pod

2. Database:
   - Read replicas scale from 3 to 10
   - Use read replicas for balance checks
   - Master only for writes

3. Caching:
   - Redis cluster with 50GB memory
   - Cache balance, user details
   - 95% cache hit rate

4. Rate Limiting:
   - Per user: 10 transactions/minute
   - Per IP: 100 transactions/minute
   - Prevents abuse

5. Queue-based processing:
   - Accept request → Return "Processing"
   - Async workers handle actual payment
   - User gets SMS when done (2-3 seconds)
```

### Q4: How do you ensure data consistency across shards?

**Answer**:
```
1. Single Shard Transaction:
   - Most UPI transactions involve 1 user
   - Route by sender's user_id
   - Use normal ACID transactions

2. Cross-Shard Transaction (Rare):
   - Use 2-Phase Commit (2PC)
   - Or Saga Pattern with compensating transactions

Example Saga Pattern:
┌──────────────────────────────────────┐
│ Step 1: Debit Sender (Shard 1)      │
│   Success → Continue                 │
│   Failure → Abort                    │
└──────────┬───────────────────────────┘
           │
           ▼
┌──────────────────────────────────────┐
│ Step 2: Credit Receiver (Shard 2)   │
│   Success → Commit                   │
│   Failure → Rollback Step 1          │
└──────────────────────────────────────┘
```

### Q5: What's your monitoring strategy?

**Answer**:
```
Key Metrics to Monitor:

1. Transaction Success Rate:
   - Target: 99.9%
   - Alert if < 99%

2. Response Time (P95, P99):
   - P95 < 2 seconds
   - P99 < 3 seconds

3. Database Query Time:
   - Alert if > 100ms

4. Queue Depth:
   - Kafka lag < 1000 messages
   - Alert if > 5000

5. Error Rate:
   - < 0.1%
   - Alert if > 1%

Tools:
- Prometheus + Grafana (Metrics)
- ELK Stack (Logs)
- Jaeger (Distributed Tracing)
- PagerDuty (Alerts)
```

---

## Production Code Examples

### Complete Payment Flow with All Safety Checks

```java
@Service
@Slf4j
public class UPIPaymentService {

    @Autowired private TransactionRepository transactionRepo;
    @Autowired private AccountService accountService;
    @Autowired private FraudDetectionService fraudService;
    @Autowired private KafkaTemplate<String, Transaction> kafkaProducer;
    @Autowired private RedisTemplate<String, String> redisTemplate;

    @Transactional(
        isolation = Isolation.READ_COMMITTED,
        timeout = 10,
        rollbackFor = Exception.class
    )
    public TransactionResponse initiatePayment(PaymentRequest request) {

        // 1. Validate request
        validateRequest(request);

        // 2. Check idempotency (prevent duplicate)
        String idempotencyKey = request.getIdempotencyKey();
        Transaction existing = checkIdempotency(idempotencyKey);
        if (existing != null) {
            log.info("Duplicate request detected: {}", idempotencyKey);
            return new TransactionResponse(existing);
        }

        // 3. Fraud detection (ML-based)
        FraudCheckResult fraudCheck = fraudService.checkTransaction(request);
        if (fraudCheck.isHighRisk()) {
            throw new FraudDetectedException("Transaction flagged as high risk");
        }

        // 4. Check daily limit (from cache)
        checkDailyLimit(request.getPayerVpa(), request.getAmount());

        // 5. Create transaction record
        Transaction txn = createTransaction(request);
        transactionRepo.save(txn);

        try {
            // 6. Debit sender account
            accountService.debit(
                request.getPayerVpa(),
                request.getAmount(),
                txn.getTransactionId()
            );

            // 7. Credit receiver account
            accountService.credit(
                request.getPayeeVpa(),
                request.getAmount(),
                txn.getTransactionId()
            );

            // 8. Update transaction status
            txn.setStatus(TransactionStatus.SUCCESS);
            txn.setCompletedAt(LocalDateTime.now());
            transactionRepo.save(txn);

            // 9. Update daily limit in cache
            updateDailyLimit(request.getPayerVpa(), request.getAmount());

            // 10. Publish success event (async processing)
            publishSuccessEvent(txn);

            log.info("Payment successful: {}", txn.getTransactionId());
            return new TransactionResponse(txn);

        } catch (InsufficientBalanceException e) {
            handlePaymentFailure(txn, "INSUFFICIENT_BALANCE", e);
            throw e;

        } catch (AccountNotFoundException e) {
            handlePaymentFailure(txn, "ACCOUNT_NOT_FOUND", e);
            throw e;

        } catch (Exception e) {
            handlePaymentFailure(txn, "SYSTEM_ERROR", e);
            throw new PaymentException("Payment processing failed", e);
        }
    }

    private void validateRequest(PaymentRequest request) {
        if (request.getAmount().compareTo(BigDecimal.ZERO) <= 0) {
            throw new ValidationException("Amount must be positive");
        }
        if (request.getAmount().compareTo(new BigDecimal("100000")) > 0) {
            throw new ValidationException("Amount exceeds max limit");
        }
        if (!isValidVPA(request.getPayerVpa())) {
            throw new ValidationException("Invalid payer VPA");
        }
        if (!isValidVPA(request.getPayeeVpa())) {
            throw new ValidationException("Invalid payee VPA");
        }
    }

    private Transaction checkIdempotency(String idempotencyKey) {
        // Check in cache first (fast)
        String cached = redisTemplate.opsForValue()
            .get("idempotency:" + idempotencyKey);
        if (cached != null) {
            return transactionRepo.findById(cached).orElse(null);
        }

        // Check in database
        return transactionRepo.findByIdempotencyKey(idempotencyKey);
    }

    private void checkDailyLimit(String vpa, BigDecimal amount) {
        String key = "daily_limit:" + vpa + ":" + LocalDate.now();
        String totalStr = redisTemplate.opsForValue().get(key);

        BigDecimal total = totalStr != null
            ? new BigDecimal(totalStr)
            : BigDecimal.ZERO;

        BigDecimal newTotal = total.add(amount);
        BigDecimal dailyLimit = new BigDecimal("100000"); // 1 Lakh

        if (newTotal.compareTo(dailyLimit) > 0) {
            throw new LimitExceededException("Daily limit exceeded");
        }
    }

    private void updateDailyLimit(String vpa, BigDecimal amount) {
        String key = "daily_limit:" + vpa + ":" + LocalDate.now();
        redisTemplate.opsForValue().increment(key, amount.doubleValue());
        redisTemplate.expire(key, Duration.ofHours(24));
    }

    private Transaction createTransaction(PaymentRequest request) {
        Transaction txn = new Transaction();
        txn.setTransactionId(generateTransactionId());
        txn.setIdempotencyKey(request.getIdempotencyKey());
        txn.setPayerVpa(request.getPayerVpa());
        txn.setPayeeVpa(request.getPayeeVpa());
        txn.setAmount(request.getAmount());
        txn.setStatus(TransactionStatus.PENDING);
        txn.setCreatedAt(LocalDateTime.now());
        return txn;
    }

    private void handlePaymentFailure(
            Transaction txn, String errorCode, Exception e) {
        txn.setStatus(TransactionStatus.FAILED);
        txn.setErrorCode(errorCode);
        txn.setErrorMessage(e.getMessage());
        txn.setCompletedAt(LocalDateTime.now());
        transactionRepo.save(txn);

        // Publish failure event
        kafkaProducer.send("payment-failed", txn);

        log.error("Payment failed: {} - {}",
            txn.getTransactionId(), errorCode, e);
    }

    private void publishSuccessEvent(Transaction txn) {
        kafkaProducer.send("payment-success", txn);
    }

    private String generateTransactionId() {
        return "UPI" + System.currentTimeMillis() +
               RandomStringUtils.randomNumeric(6);
    }

    private boolean isValidVPA(String vpa) {
        return vpa != null && vpa.matches("^[a-zA-Z0-9.]+@[a-zA-Z0-9]+$");
    }
}
```

### Async Workers (SMS, Email, Audit)

```java
@Service
@Slf4j
public class PaymentEventConsumer {

    @KafkaListener(
        topics = "payment-success",
        groupId = "notification-service",
        concurrency = "10"
    )
    public void handlePaymentSuccess(Transaction txn) {
        try {
            // Send SMS notification
            smsService.send(
                txn.getPayerVpa(),
                "Payment of Rs." + txn.getAmount() + " successful"
            );

            // Send push notification
            pushService.send(
                txn.getPayerVpa(),
                "Payment completed",
                "Rs." + txn.getAmount() + " sent to " + txn.getPayeeVpa()
            );

        } catch (Exception e) {
            log.error("Failed to send notification: {}",
                txn.getTransactionId(), e);
            // Don't throw - notification failure shouldn't affect payment
        }
    }

    @KafkaListener(
        topics = "payment-success",
        groupId = "audit-service",
        concurrency = "5"
    )
    public void auditPayment(Transaction txn) {
        AuditLog audit = new AuditLog();
        audit.setTransactionId(txn.getTransactionId());
        audit.setAction("PAYMENT_SUCCESS");
        audit.setAmount(txn.getAmount());
        audit.setTimestamp(LocalDateTime.now());

        auditRepository.save(audit);
    }
}
```

---

## Key Takeaways for Interview

### 1. Scalability Strategies
```
✅ Horizontal scaling (microservices + Kubernetes)
✅ Database sharding (10M users per shard)
✅ Read replicas (80% reads → replicas)
✅ Caching (Redis, 95% hit rate)
✅ Async processing (Kafka for non-critical tasks)
```

### 2. Reliability Strategies
```
✅ Idempotency (prevent duplicates)
✅ Circuit breaker (handle failures gracefully)
✅ Retry with exponential backoff
✅ Reconciliation jobs (fix stuck transactions)
✅ Health checks + auto-healing
```

### 3. Performance Optimizations
```
✅ Response time: 1-2 seconds (user waits)
✅ Background tasks: 5-10 seconds (async)
✅ Database indexing (user_id, status, date)
✅ Connection pooling (HikariCP, 50-100 connections)
✅ Partitioning (monthly partitions)
```

### 4. Security Measures
```
✅ Fraud detection (ML-based, real-time)
✅ Daily limits (cached in Redis)
✅ Rate limiting (per user, per IP)
✅ Encryption (AES-256)
✅ Audit trail (complete transaction history)
```

### 5. Monitoring & Alerts
```
✅ Success rate: 99.9%+
✅ Response time: P95 < 2s, P99 < 3s
✅ Error rate: < 0.1%
✅ Queue lag: < 1000 messages
✅ Database query time: < 100ms
```

---

## Final Interview Answer Template

**"How does UPI handle 4 crore transactions per hour?"**

**Answer**:
"UPI handles 40 million transactions/hour (11,000 TPS) using these key strategies:

1. **Horizontal Scaling**: Microservices architecture on Kubernetes with auto-scaling. Payment service runs 100+ pods during peak.

2. **Database Sharding**: User data sharded across 50+ databases. Each shard handles 1-2 million users. Primary + 2-3 read replicas per shard.

3. **Caching**: Redis cluster for balance checks, user profiles. 95% cache hit rate reduces database load by 95%.

4. **Async Processing**: Core payment takes 1 second. SMS, email, audit happen asynchronously via Kafka.

5. **Idempotency**: Unique key per transaction prevents duplicates even during network failures.

6. **Circuit Breaker**: If bank API fails, we fallback to queuing. Daily reconciliation fixes stuck transactions.

7. **Monitoring**: Real-time alerts on success rate, latency, error rate. Auto-scaling triggers at 70% CPU.

The key is separating synchronous (critical) operations from asynchronous (non-critical) ones."

---

**Good luck with your interview! 🚀**
