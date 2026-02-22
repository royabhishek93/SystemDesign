# Failure Handling and Idempotency

**Target Level**: Senior+ (5-7 years)  
**Interview Focus**: Production scenarios and failure modes

## 📋 Why This Chapter Is Critical

**Senior interviews test failure thinking, not just happy path.**

In distributed systems:
- Networks fail
- Nodes crash
- Jobs time out
- Messages arrive twice

You must design for these scenarios. This chapter shows how.

## 💥 Failure Scenario 1: Node Crashes While Holding Lock

### The Problem

```
2:00 AM - Instance 1 acquires lock
2:02 AM - Processing job...
2:03 AM - Instance 1 crashes! 💥
2:04 AM - Lock still held ❌
2:05 AM - No other instance can run
Result: Deadlock - job never completes
```

### ❌ Wrong Solution

```java
// No TTL - creates deadlock!
redisTemplate.opsForValue().set("lock", "locked");
doWork();
redisTemplate.delete("lock"); // Never reaches if crash
```

### ✅ Right Solution - TTL-Based Auto-Recovery

```java
// Lock with TTL
Boolean locked = redisTemplate.opsForValue()
    .setIfAbsent("lock", instanceId, Duration.ofMinutes(10)); // TTL = max job duration

if (locked) {
    try {
        doWork(); // Takes 5 minutes normally
    } finally {
        redisTemplate.delete("lock");
    }
}

// If crash happens:
// - Lock expires after 10 minutes
// - Next instance can acquire at 2:10 AM
// - Job runs (delayed but not lost)
```

### Interview Talking Point

> "I set TTL to be greater than maximum expected job duration. If a node crashes while holding the lock, the TTL ensures automatic release so another node can take over. This provides fault tolerance without manual intervention."

---

## ⏰ Failure Scenario 2: Job Runs Longer Than TTL

### The Problem

```
2:00 AM - Instance 1 acquires lock (TTL=5 min)
2:03 AM - Still processing (needs 8 minutes total)
2:05 AM - Lock expires! ❌
2:05 AM - Instance 2 acquires lock
Result: Both instances running simultaneously! 💥
```

### ❌ Wrong Solution

"Just make TTL longer" - Not scalable, delays failover

### ✅ Right Solution A - Watchdog Pattern (Redisson)

```java
@Component
public class WatchdogScheduler {
    
    @Autowired
    private RedissonClient redissonClient;
    
    @Scheduled(cron = "0 0 2 * * *")
    public void processJob() {
        RLock lock = redissonClient.getLock("job-lock");
        
        try {
            // Wait up to 10 sec, lease time 30 sec (but auto-renewed!)
            boolean locked = lock.tryLock(10, 30, TimeUnit.SECONDS);
            
            if (locked) {
                try {
                    // Redisson's watchdog automatically renews lease every 10 seconds
                    // Job can run for hours if needed
                    doLongRunningWork(); // Takes 8 minutes - no problem!
                } finally {
                    lock.unlock();
                }
            }
        } catch (InterruptedException e) {
            Thread.currentThread().interrupt();
        }
    }
}
```

**How Watchdog Works**:
```
2:00:00 - Acquire lock (TTL=30s)
2:00:10 - Watchdog renews → TTL=30s
2:00:20 - Watchdog renews → TTL=30s
2:00:30 - Watchdog renews → TTL=30s
2:08:00 - Job completes → unlock → stops watchdog
```

### ✅ Right Solution B - Heartbeat Pattern

```java
@Component
@Slf4j
public class HeartbeatScheduler {
    
    @Scheduled(cron = "0 0 2 * * *")
    public void processJob() {
        String lockKey = "job-lock";
        String instanceId = UUID.randomUUID().toString();
        
        Boolean locked = redisTemplate.opsForValue()
            .setIfAbsent(lockKey, instanceId, Duration.ofMinutes(2));
        
        if (locked) {
            ScheduledExecutorService heartbeat = Executors.newScheduledThreadPool(1);
            
            // Renew lock every minute
            heartbeat.scheduleAtFixedRate(() -> {
                redisTemplate.expire(lockKey, Duration.ofMinutes(2));
            }, 1, 1, TimeUnit.MINUTES);
            
            try {
                doLongRunningWork();
            } finally {
                heartbeat.shutdown();
                redisTemplate.delete(lockKey);
            }
        }
    }
}
```

### Interview Talking Point

> "For long-running jobs, I implement a watchdog or heartbeat pattern that periodically renews the lock while the job is active. This prevents lock expiry during normal execution while still providing crash recovery through TTL."

---

## 🔄 Idempotency - The Most Important Concept

### Why Idempotency Matters

**Even with perfect coordination, jobs may run twice due to**:
- Network retry
- Timeout then success
- Split-brain scenarios
- Message redelivery

**Senior-level insight**:

> "In distributed systems we design jobs to be idempotent because exactly-once execution is impossible to guarantee. At-least-once with idempotency achieves the same result."

### ❌ Non-Idempotent Example (Dangerous!)

```java
@Scheduled(cron = "0 0 2 * * *")
public void processOrders() {
    List<Order> orders = orderRepo.findByStatus("PENDING");
    
    for (Order order : orders) {
        // ❌ Not idempotent - running twice charges customer twice!
        paymentService.charge(order.getCustomerId(), order.getAmount());
        order.setStatus("PROCESSED");
        orderRepo.save(order);
    }
}
```

**What goes wrong**:
```
2:00 AM - Instance 1 processes orders → charges $100
2:01 AM - Instance 1 crashes before updating status
2:05 AM - Lock expires, Instance 2 runs
2:05 AM - Finds same orders (still "PENDING")
2:05 AM - Charges $100 again! ❌❌
Result: Customer charged twice
```

### ✅ Idempotent Solution 1 - Unique Job Execution ID

```java
@Component
@Slf4j
public class IdempotentJobScheduler {
    
    @Autowired
    private JobExecutionRepository jobExecutionRepo;
    
    @Autowired
    private OrderService orderService;
    
    @Scheduled(cron = "0 0 2 * * *")
    public void processOrders() {
        // Generate unique execution ID based on date
        String executionId = "daily-order-process-" + LocalDate.now();
        
        // Check if already executed
        if (jobExecutionRepo.existsById(executionId)) {
            log.info("Job already executed today: {}", executionId);
            return; // Idempotent - safe to skip
        }
        
        // Record execution start
        JobExecution execution = new JobExecution();
        execution.setId(executionId);
        execution.setStatus("RUNNING");
        execution.setStartTime(Instant.now());
        
        try {
            jobExecutionRepo.save(execution);
            
            // Process orders
            orderService.processPendingOrders();
            
            // Mark success
            execution.setStatus("COMPLETED");
            execution.setEndTime(Instant.now());
            jobExecutionRepo.save(execution);
            
        } catch (Exception e) {
            execution.setStatus("FAILED");
            execution.setError(e.getMessage());
            jobExecutionRepo.save(execution);
            throw e;
        }
    }
}
```

**Database Schema**:
```sql
CREATE TABLE job_executions (
    id VARCHAR(255) PRIMARY KEY,  -- e.g., "daily-order-process-2026-02-22"
    status VARCHAR(50),            -- RUNNING, COMPLETED, FAILED
    start_time TIMESTAMP,
    end_time TIMESTAMP,
    error TEXT
);

-- Unique constraint ensures single execution
```

### ✅ Idempotent Solution 2 - Deduplication Table

```java
@Service
@Transactional
public class OrderProcessingService {
    
    public void processOrder(Order order) {
        String dedupeKey = "order-" + order.getId() + "-" + LocalDate.now();
        
        // Try to insert deduplication record
        try {
            ProcessingRecord record = new ProcessingRecord();
            record.setDedupeKey(dedupeKey);
            record.setOrderId(order.getId());
            record.setProcessedAt(Instant.now());
            
            processingRecordRepo.save(record); // Fails if already exists (unique constraint)
            
        } catch (DataIntegrityViolationException e) {
            log.warn("Order already processed: {}", order.getId());
            return; // Idempotent - already done
        }
        
        // Process order (safe - only runs once)
        paymentService.charge(order.getCustomerId(), order.getAmount());
        order.setStatus("PROCESSED");
        orderRepo.save(order);
    }
}
```

```sql
CREATE TABLE processing_records (
    dedupe_key VARCHAR(255) PRIMARY KEY,  -- Unique constraint!
    order_id BIGINT,
    processed_at TIMESTAMP
);
```

### ✅ Idempotent Solution 3 - Optimistic Locking

```java
@Entity
public class Order {
    @Id
    private Long id;
    
    private String status;
    
    @Version  // Optimistic locking
    private Long version;
    
    private BigDecimal amount;
}

@Service
public class OrderService {
    
    public void processOrder(Order order) {
        // Load order with version
        Order current = orderRepo.findById(order.getId())
            .orElseThrow();
        
        if ("PROCESSED".equals(current.getStatus())) {
            log.info("Order already processed");
            return; // Idempotent
        }
        
        // Process payment
        paymentService.charge(current.getCustomerId(), current.getAmount());
        
        // Update with version check
        current.setStatus("PROCESSED");
        
        try {
            orderRepo.save(current); // Fails if version changed
        } catch (OptimisticLockException e) {
            // Another instance already processed - idempotent!
            log.warn("Order processed by another instance: {}", order.getId());
        }
    }
}
```

**How it works**:
```sql
-- Instance 1:
UPDATE orders SET status='PROCESSED', version=2 
WHERE id=123 AND version=1;  -- SUCCESS (1 row updated)

-- Instance 2 (runs simultaneously):
UPDATE orders SET status='PROCESSED', version=2 
WHERE id=123 AND version=1;  -- FAIL (0 rows updated - version already 2)
```

### Interview Talking Point

> "I ensure idempotency using unique execution IDs, deduplication tables, or optimistic locking. This guarantees that even if a job runs twice due to network issues or retries, the business outcome is the same - payments aren't duplicated, emails aren't resent, data isn't corrupted."

---

## 🔁 Retry Strategies

### When to Retry

**Retry for transient failures**:
- Network timeout
- Database connection pool exhausted
- Rate limit exceeded
- Temporary service unavailability

**Don't retry for**:
- Business logic errors (bad data)
- Authorization failures
- Invalid input

### ✅ Exponential Backoff Pattern

```java
@Component
@Slf4j
public class RetryableScheduler {
    
    @Autowired
    private ReportService reportService;
    
    @Scheduled(cron = "0 0 2 * * *")
    @Retryable(
        value = {TransientException.class, TimeoutException.class},
        maxAttempts = 5,
        backoff = @Backoff(
            delay = 1000,      // Start with 1 second
            multiplier = 2,     // Double each time
            maxDelay = 300000   // Max 5 minutes
        )
    )
    public void generateReport() {
        reportService.generate();
    }
    
    @Recover
    public void recoverFromFailure(Exception e) {
        log.error("Report generation failed after all retries", e);
        alertService.sendAlert("Daily report failed", e.getMessage());
        
        // Store for manual retry
        failedJobRepo.save(new FailedJob("daily-report", e.getMessage()));
    }
}
```

**Retry timing**:
```
Attempt 1: Immediate failure → wait 1 sec
Attempt 2: Failure → wait 2 sec
Attempt 3: Failure → wait 4 sec
Attempt 4: Failure → wait 8 sec
Attempt 5: Failure → give up, call @Recover
```

### ✅ Circuit Breaker Pattern

```java
@Service
public class ExternalServiceClient {
    
    @CircuitBreaker(
        name = "externalService",
        fallbackMethod = "fallbackMethod"
    )
    @Retry(name = "externalService")
    public Data fetchData() {
        return restTemplate.getForObject("https://api.example.com/data", Data.class);
    }
    
    public Data fallbackMethod(Exception e) {
        log.warn("External service unavailable, using cached data");
        return cacheService.getCachedData();
    }
}
```

**Configuration** (`application.yml`):
```yaml
resilience4j:
  circuitbreaker:
    instances:
      externalService:
        sliding-window-size: 10
        failure-rate-threshold: 50  # Open if 50% fail
        wait-duration-in-open-state: 60s
        permitted-number-of-calls-in-half-open-state: 3
  
  retry:
    instances:
      externalService:
        max-attempts: 3
        wait-duration: 1s
        exponential-backoff-multiplier: 2
```

---

## 📊 Observability - Critical for Production

### What to Monitor

```java
@Component
@Slf4j
public class ObservableScheduler {
    
    @Autowired
    private MeterRegistry meterRegistry;
    
    @Scheduled(cron = "0 0 2 * * *")
    public void generateReport() {
        Timer.Sample sample = Timer.start(meterRegistry);
        
        try {
            log.info("Starting daily report generation");
            
            reportService.generate();
            
            // Record success
            sample.stop(Timer.builder("job.execution.time")
                .tag("job", "daily-report")
                .tag("status", "success")
                .register(meterRegistry));
            
            meterRegistry.counter("job.execution.count", 
                "job", "daily-report", 
                "status", "success"
            ).increment();
            
            log.info("Daily report completed successfully");
            
        } catch (Exception e) {
            // Record failure
            sample.stop(Timer.builder("job.execution.time")
                .tag("job", "daily-report")
                .tag("status", "failure")
                .register(meterRegistry));
            
            meterRegistry.counter("job.execution.count",
                "job", "daily-report",
                "status", "failure"
            ).increment();
            
            log.error("Daily report failed", e);
            throw e;
        }
    }
}
```

### Metrics to Track

1. **Execution Count**: How many times job ran
2. **Success Rate**: Percentage of successful executions
3. **Execution Duration**: How long jobs take
4. **Failure Count**: How many failed
5. **Lock Acquisition Time**: How long to get lock
6. **Lock Hold Duration**: How long lock was held
7. **Retry Count**: How many retries per job

### Grafana Dashboard Queries

```promql
# Success rate
sum(rate(job_execution_count{status="success"}[5m])) / 
sum(rate(job_execution_count[5m])) * 100

# P95 execution time
histogram_quantile(0.95, 
  sum(rate(job_execution_time_bucket[5m])) by (le, job)
)

# Failed executions (alert on this)
increase(job_execution_count{status="failure"}[5m]) > 0
```

### Structured Logging

```java
log.info("Job execution started", 
    kv("jobId", executionId),
    kv("jobType", "daily-report"),
    kv("instanceId", instanceId),
    kv("scheduledTime", scheduledTime)
);

log.info("Job execution completed",
    kv("jobId", executionId),
    kv("duration", duration.toMillis()),
    kv("recordsProcessed", recordCount),
    kv("status", "SUCCESS")
);
```

---

## 🚨 Critical Pitfalls & Solutions

### Pitfall #1: Assuming Lock Guarantees Exactly-Once

**Problem**: Networks partition, clocks drift, TTL expires early

**Solution**: Always design jobs to be idempotent

### Pitfall #2: Not Handling Partial Failures

**Problem**: Job processes 1000 records, crashes at record 800

```java
// ❌ Wrong - restarts from beginning
public void process() {
    List<Record> all = fetchAll(); // 1000 records
    all.forEach(this::process);    // Crash at 800 → loses progress
}
```

**Solution**: Checkpoint progress

```java
// ✅ Right - resumes from checkpoint
public void process() {
    Long lastProcessedId = checkpointRepo.getLastProcessed("daily-job");
    
    List<Record> remaining = fetchAfter(lastProcessedId);
    
    for (Record record : remaining) {
        process(record);
        checkpointRepo.updateLastProcessed("daily-job", record.getId());
    }
}
```

### Pitfall #3: Silent Failures

**Problem**: Job fails, no one notices for days

**Solution**: Always alert on failure

```java
@Recover
public void handleFailure(Exception e) {
    // Send alert
    slackService.sendAlert("#ops-alerts", "Daily report job failed: " + e.getMessage());
    
    // Page on-call
    pagerDutyService.trigger("daily-report-failure");
    
    // Store for investigation
    failedJobRepo.save(new FailedJob(jobId, e));
}
```

### Pitfall #4: Not Testing Failure Scenarios

**Test these scenarios**:

```java
@Test
public void testJobFailureAndRetry() {
    // Simulate failure then success
    when(reportService.generate())
        .thenThrow(new TransientException())
        .thenReturn(report);
    
    scheduler.generateReport();
    
    verify(reportService, times(2)).generate(); // Retried once
}

@Test
public void testIdempotency() {
    // Run job twice
    scheduler.generateReport();
    scheduler.generateReport();
    
    // Verify executed only once
    verify(paymentService, times(1)).charge(any(), any());
}

@Test
public void testLockExpiry() throws InterruptedException {
    // Acquire lock
    scheduler.generateReport();
    
    // Wait for TTL
    Thread.sleep(TTL_MILLIS + 1000);
    
    // Another instance should acquire
    scheduler.generateReport();
    
    verify(reportService, times(2)).generate(); // Both ran
}
```

---

## 🔥 Follow-Up Questions & Master Answers

### Q1: "How do you handle jobs that run longer than expected?"

**✅ Answer**:
"I implement a watchdog pattern that periodically renews the lock while the job is active, preventing premature expiry. Additionally, I set alerts for jobs exceeding their SLA and implement timeout mechanisms with graceful shutdown to prevent resource leaks."

### Q2: "What if the database goes down during job execution?"

**✅ Answer**:
"I implement circuit breaker pattern to detect database unavailability quickly and fail fast rather than hanging. I also use retry with exponential backoff for transient failures. For critical jobs, I persist job state externally so recovery can resume from the last checkpoint rather than restarting completely."

### Q3: "How do you prevent thundering herd when lock is released?"

**✅ Answer**:
"Instead of all instances attempting simultaneously, I implement jittered backoff where each instance waits a random duration before retry. Alternatively, I use queue-based scheduling where only one consumer processes the job, eliminating competition entirely."

### Q4: "How do you test distributed job scheduling?"

**✅ Answer**:
"I write integration tests that simulate multiple instances using different ports or threads. I test scenarios like simultaneous execution attempts, mid-job crashes, lock expiry, and idempotency by running the job twice. I use test containers for Redis/database to ensure realistic testing. I also implement chaos engineering in staging to randomly kill instances during execution and verify failover."

### Q5: "What metrics indicate your distributed job scheduling is unhealthy?"

**✅ Answer**:
"Key metrics: 1) Execution frequency dropping below expected rate indicates all instances failing to acquire lock. 2) Multiple concurrent executions indicate lock mechanism failure. 3) Increasing execution duration suggests resource contention or data growth. 4) Increasing failure rate needs investigation. 5) Lock acquisition time increasing suggests coordination bottleneck. I alert on all of these and have runbooks for each scenario."

---

## ✅ Checklist for Production-Ready Jobs

Before deploying:

- [ ] **Idempotent**: Job can run twice safely
- [ ] **Timeout**: Maximum execution time set
- [ ] **TTL**: Lock expires if holder crashes
- [ ] **Retry**: Transient failures retry automatically
- [ ] **Logging**: Structured logs with job ID, duration, status
- [ ] **Metrics**: Track success rate, duration, failure count
- [ ] **Alerts**: Notify on-call when job fails
- [ ] **Monitoring**: Dashboard shows job health
- [ ] **Dead letter queue**: Failed messages preserved
- [ ] **Runbook**: Document recovery procedures
- [ ] **Tests**: Unit + integration tests for failure scenarios
- [ ] **Checkpointing**: Long jobs can resume on failure

---

**Next**: [04-Production-Tradeoffs.md](04-Production-Tradeoffs.md) - Decision matrix for choosing the right approach

**Previous**: [02-Implementation-Approaches.md](02-Implementation-Approaches.md)
