# ⚠️ Failure Scenarios: What Can Go Wrong and How to Handle It

**Purpose**: Deep dive into every possible failure mode in distributed job scheduling and proven solutions

---

## 📋 Table of Contents

1. [Node/Pod Failure During Execution](#1-nodepod-failure-during-execution)
2. [Lock Expiry While Job Running](#2-lock-expiry-while-job-running)
3. [Network Partition (Split-Brain)](#3-network-partition-split-brain)
4. [Database Connection Loss](#4-database-connection-loss)
5. [Message Queue Unavailable](#5-message-queue-unavailable)
6. [Duplicate Job Execution](#6-duplicate-job-execution)
7. [Leader Node Crashes](#7-leader-node-crashes)
8. [Worker Overload (Cascading Failure)](#8-worker-overload-cascading-failure)
9. [Clock Skew Across Instances](#9-clock-skew-across-instances)
10. [Zombie Jobs (Stuck Forever)](#10-zombie-jobs-stuck-forever)

---

## 1. Node/Pod Failure During Execution

### 💥 Failure Scenario

```
Timeline:
10:00:00  Worker-1 claims job: UPDATE jobs SET status='IN_PROGRESS'
10:00:05  Worker-1 starts processing (API call to payment gateway)
10:00:10  💀 Worker-1 crashes (OutOfMemoryError / Pod eviction)
10:00:11  Job stuck in IN_PROGRESS state forever
          Payment gateway call may or may not have succeeded
```

### 🧨 Impact
- **Job never completes**: Status stuck as IN_PROGRESS
- **Resource leak**: Database rows never cleaned up
- **Business impact**: Payment not processed, customer angry

### ✅ Solution 1: Heartbeat + Timeout Monitor

```java
@Service
public class JobHeartbeatMonitor {
    
    @Autowired
    private JobRepository jobRepository;
    
    @Autowired
    private KafkaTemplate<String, Job> kafkaTemplate;
    
    /**
     * Background thread: Check for jobs stuck IN_PROGRESS
     */
    @Scheduled(fixedRate = 30000) // Every 30 seconds
    public void detectStalledJobs() {
        // Find jobs IN_PROGRESS for > 5 minutes
        Instant staleThreshold = Instant.now().minus(5, ChronoUnit.MINUTES);
        
        List<Job> staleJobs = jobRepository.findByStatusAndUpdatedAtBefore(
            JobStatus.IN_PROGRESS,
            staleThreshold
        );
        
        for (Job job : staleJobs) {
            log.warn("Detected stale job: {} (last update: {})", 
                job.getJobId(), job.getUpdatedAt());
            
            // Mark as FAILED and retry
            jobRepository.updateStatus(job.getJobId(), JobStatus.FAILED);
            
            // Requeue for retry
            kafkaTemplate.send("job-retry-queue", job);
            
            // Alert on-call
            alertService.sendAlert(
                "Job " + job.getJobId() + " stalled, initiating retry"
            );
        }
    }
}
```

**Database Schema**:
```sql
CREATE TABLE jobs (
    job_id VARCHAR(36) PRIMARY KEY,
    status VARCHAR(20),
    updated_at TIMESTAMP DEFAULT NOW(),
    worker_id VARCHAR(100),
    heartbeat_at TIMESTAMP,
    
    INDEX idx_stale_jobs (status, updated_at)
);
```

### ✅ Solution 2: Worker Heartbeat Loop

```java
@Service
public class ResilientWorker {
    
    @Autowired
    private JobRepository jobRepository;
    
    @KafkaListener(topics = "job-queue")
    public void processJob(Job job) {
        String workerId = getWorkerId();
        
        // Claim job
        if (!jobRepository.claimJob(job.getJobId(), workerId)) {
            return;
        }
        
        // Start heartbeat thread
        ScheduledExecutorService heartbeat = Executors.newScheduledThreadPool(1);
        heartbeat.scheduleAtFixedRate(
            () -> jobRepository.updateHeartbeat(job.getJobId(), workerId),
            0,
            10,
            TimeUnit.SECONDS
        );
        
        try {
            // Execute long-running job
            processPayment(job);
            
            // Mark complete
            jobRepository.updateStatus(job.getJobId(), JobStatus.COMPLETED);
            
        } catch (Exception e) {
            jobRepository.updateStatus(job.getJobId(), JobStatus.FAILED);
        } finally {
            // Stop heartbeat
            heartbeat.shutdown();
        }
    }
}
```

**Heartbeat Update**:
```java
@Repository
public class JobRepository {
    
    @Transactional
    public void updateHeartbeat(String jobId, String workerId) {
        String sql = """
            UPDATE jobs
            SET heartbeat_at = NOW()
            WHERE job_id = ?
              AND worker_id = ?
              AND status = 'IN_PROGRESS'
            """;
        
        jdbcTemplate.update(sql, jobId, workerId);
    }
}
```

### ✅ Solution 3: Kubernetes Job with Timeout

```yaml
apiVersion: batch/v1
kind: Job
metadata:
  name: payment-processor
spec:
  activeDeadlineSeconds: 300  # Kill after 5 minutes
  backoffLimit: 3  # Retry up to 3 times
  template:
    spec:
      restartPolicy: OnFailure
      containers:
      - name: processor
        image: payment-processor:v1
        resources:
          requests:
            memory: "2Gi"
            cpu: "1"
          limits:
            memory: "4Gi"  # OOMKill if exceeded
            cpu: "2"
```

---

## 2. Lock Expiry While Job Running

### 💥 Failure Scenario

```
Timeline:
10:00:00  Worker-1 acquires Redis lock (TTL=30s)
10:00:05  Worker-1 starts long payment reconciliation (takes 60s)
10:00:30  🔓 Redis lock expires (TTL timeout)
10:00:31  Worker-2 acquires same lock (thinks it's safe)
10:00:32  Worker-2 starts same job
10:01:00  Both workers complete → DUPLICATE EXECUTION ❌
```

### 🧨 Impact
- **Duplicate execution**: Customer charged twice
- **Data corruption**: Multiple workers modify same row
- **Inconsistent state**: Half from Worker-1, half from Worker-2

### ✅ Solution 1: Lock Extension (Heartbeat)

```java
@Service
public class ExtendableLockWorker {
    
    @Autowired
    private RedisLock redisLock;
    
    @Scheduled(cron = "0 0 2 * * ?")
    public void longRunningJob() {
        String jobName = "payment-reconciliation";
        String workerId = getWorkerId();
        
        // Initial lock acquisition (30s TTL)
        if (!redisLock.tryAcquire(jobName, workerId, 30)) {
            log.info("Another worker is running, skipping");
            return;
        }
        
        // Start background thread to extend lock
        ScheduledExecutorService lockExtender = Executors.newScheduledThreadPool(1);
        AtomicBoolean jobComplete = new AtomicBoolean(false);
        
        lockExtender.scheduleAtFixedRate(() -> {
            if (!jobComplete.get()) {
                boolean extended = redisLock.extendLock(jobName, workerId, 30);
                if (!extended) {
                    log.error("Failed to extend lock! Another worker may take over!");
                }
            }
        }, 15, 15, TimeUnit.SECONDS); // Extend every 15s
        
        try {
            // Execute long job (60 seconds)
            reconcilePayments();
            
        } finally {
            jobComplete.set(true);
            lockExtender.shutdown();
            redisLock.release(jobName, workerId);
        }
    }
}
```

**Redis Lock Extension**:
```java
public class RedisLock {
    
    /**
     * Extend lock TTL (only if we still own it)
     */
    public boolean extendLock(String lockKey, String workerId, int ttl) {
        String luaScript = """
            if redis.call('get', KEYS[1]) == ARGV[1] then
                return redis.call('expire', KEYS[1], ARGV[2])
            else
                return 0
            end
            """;
        
        Long result = redisTemplate.execute(
            new DefaultRedisScript<>(luaScript, Long.class),
            Collections.singletonList(lockKey),
            workerId,
            String.valueOf(ttl)
        );
        
        return result != null && result == 1;
    }
}
```

### ✅ Solution 2: Database-Level Optimistic Locking

```java
@Entity
@Table(name = "payment_reconciliation")
public class PaymentReconciliation {
    
    @Id
    private String id;
    
    @Version // Optimistic lock
    private Long version;
    
    private BigDecimal amount;
    private String status;
}

@Service
public class ReconciliationService {
    
    @Transactional
    public void reconcile(String paymentId) {
        // Load with version
        PaymentReconciliation payment = repository.findById(paymentId)
            .orElseThrow();
        
        // Process
        payment.setStatus("RECONCILED");
        payment.setAmount(calculateAmount());
        
        try {
            // Save (will fail if version changed)
            repository.save(payment);
            
        } catch (OptimisticLockingFailureException e) {
            log.error("Another worker already processed this payment!");
            throw new DuplicateProcessingException();
        }
    }
}
```

### ✅ Solution 3: Use Fencing Tokens

```java
/**
 * Generate monotonically increasing token with each lock acquisition
 */
public class FencedLock {
    
    private final AtomicLong tokenCounter = new AtomicLong(0);
    
    public LockToken acquireLock(String lockKey, String workerId) {
        long token = tokenCounter.incrementAndGet(); // 1, 2, 3, ...
        
        boolean acquired = redis.setNX(lockKey, workerId + ":" + token, 30);
        
        if (acquired) {
            return new LockToken(token, workerId);
        }
        return null;
    }
}

@Service
public class FencedWorker {
    
    public void processJob(Job job) {
        LockToken token = fencedLock.acquireLock("job:" + job.getId(), workerId);
        
        if (token == null) {
            return;
        }
        
        try {
            // Include token in all external calls
            paymentGateway.processPayment(
                job.getPaymentId(),
                token.getValue() // Gateway rejects if sees older token
            );
            
        } finally {
            fencedLock.release("job:" + job.getId(), token);
        }
    }
}
```

---

## 3. Network Partition (Split-Brain)

### 💥 Failure Scenario

```
Datacenter Setup:
  Redis Master: us-east-1a
  Worker-1: us-east-1a
  Worker-2: us-east-1b

Timeline:
10:00:00  Network partition: us-east-1a isolated from us-east-1b
10:00:01  Worker-1 (in 1a) thinks it has lock (can reach Redis)
10:00:01  Worker-2 (in 1b) can't reach Redis → timeout
10:00:05  Worker-2 starts backup mode: assumes lock available
10:00:06  ⚠️ BOTH workers executing same job! (split-brain)
```

### 🧨 Impact
- **Duplicate execution**: Both workers succeed
- **Data corruption**: Conflicting updates to database
- **Financial loss**: Double payment processing

### ✅ Solution 1: Require Quorum (Redis Cluster)

```java
@Configuration
public class RedisClusterConfig {
    
    @Bean
    public RedissonClient redissonClient() {
        Config config = new Config();
        
        config.useClusterServers()
            .addNodeAddress(
                "redis://node1.us-east-1a:6379",
                "redis://node2.us-east-1b:6379",
                "redis://node3.us-east-1c:6379"
            )
            // Majority must confirm lock acquisition
            .setReadMode(ReadMode.MASTER_SLAVE)
            .setSubscriptionMode(SubscriptionMode.MASTER);
        
        return Redisson.create(config);
    }
    
    @Bean
    public RLock distributedLock(RedissonClient redisson) {
        // RedLock: Requires majority (2/3) to acquire lock
        return redisson.getRedLock(
            redisson.getLock("lock:1"),
            redisson.getLock("lock:2"),
            redisson.getLock("lock:3")
        );
    }
}
```

### ✅ Solution 2: Use Consensus System (ZooKeeper/etcd)

```java
@Service
public class ZooKeeperLock {
    
    @Autowired
    private CuratorFramework zkClient;
    
    public void executeWithLock(String jobName, Runnable task) {
        InterProcessMutex lock = new InterProcessMutex(
            zkClient, 
            "/locks/" + jobName
        );
        
        try {
            // Acquire lock (blocks until available or timeout)
            boolean acquired = lock.acquire(10, TimeUnit.SECONDS);
            
            if (!acquired) {
                log.warn("Failed to acquire lock for {}", jobName);
                return;
            }
            
            log.info("Acquired ZK lock for {}", jobName);
            
            // Execute critical section
            task.run();
            
        } catch (Exception e) {
            log.error("ZooKeeper lock error", e);
        } finally {
            try {
                lock.release();
            } catch (Exception e) {
                log.error("Failed to release lock", e);
            }
        }
    }
}
```

**Why ZooKeeper Prevents Split-Brain**:
- Uses **Raft/Paxos consensus**: Majority must agree
- If network partition, only partition with majority leader can grant locks
- Minority partition blocks (can't acquire locks)
- Strong consistency guarantee

### ✅ Solution 3: Idempotency + Reconciliation

```java
/**
 * Accept that duplicates may occur, handle idempotently
 */
@Service
public class IdempotentPaymentService {
    
    @Transactional
    public void processPayment(PaymentRequest request) {
        String idempotencyKey = request.getIdempotencyKey();
        
        // Check if already processed
        Optional<Payment> existing = paymentRepository
            .findByIdempotencyKey(idempotencyKey);
        
        if (existing.isPresent()) {
            log.warn("Payment already processed: {}", idempotencyKey);
            return; // Silently skip duplicate
        }
        
        // Process payment
        Payment payment = new Payment();
        payment.setIdempotencyKey(idempotencyKey);
        payment.setAmount(request.getAmount());
        payment.setStatus("COMPLETED");
        
        // Atomic insert (unique constraint on idempotency_key)
        try {
            paymentRepository.save(payment);
            
            // Call external gateway
            gatewayClient.charge(request);
            
        } catch (DataIntegrityViolationException e) {
            // Another worker inserted first
            log.warn("Duplicate detected via DB constraint");
        }
    }
}
```

**Database Constraint**:
```sql
CREATE TABLE payments (
    id BIGSERIAL PRIMARY KEY,
    idempotency_key VARCHAR(64) NOT NULL UNIQUE, -- Prevents duplicates
    amount DECIMAL(10, 2),
    status VARCHAR(20),
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE UNIQUE INDEX idx_idempotency ON payments(idempotency_key);
```

---

## 4. Database Connection Loss

### 💥 Failure Scenario

```
Timeline:
10:00:00  Worker claims job: UPDATE jobs SET status='IN_PROGRESS'
10:00:05  Database connection pool exhausted (all 10 connections busy)
10:00:10  Worker tries to update status → ConnectionTimeoutException
10:00:15  Job executes successfully (payment processed)
10:00:16  Worker tries to mark COMPLETED → SQLException
10:00:17  Job stuck in IN_PROGRESS, but payment already sent ⚠️
```

### 🧨 Impact
- **Lost updates**: Job status never updated
- **Monitoring blind**: Job appears stuck but actually completed
- **Retry risk**: System may retry already-completed job

### ✅ Solution 1: Connection Pool Tuning

```yaml
# application.yml
spring:
  datasource:
    hikari:
      maximum-pool-size: 50  # Increase pool size
      minimum-idle: 10
      connection-timeout: 10000  # 10s timeout
      idle-timeout: 300000  # 5 min idle
      max-lifetime: 1800000  # 30 min max connection age
      leak-detection-threshold: 60000  # Detect leaks after 60s
      
      # Health check
      connection-test-query: SELECT 1
      validation-timeout: 3000
```

### ✅ Solution 2: Retry with Exponential Backoff

```java
@Service
public class ResilientJobRepository {
    
    @Autowired
    private JdbcTemplate jdbcTemplate;
    
    @Retryable(
        value = {DataAccessException.class},
        maxAttempts = 5,
        backoff = @Backoff(
            delay = 1000,
            multiplier = 2,
            maxDelay = 30000
        )
    )
    public void updateJobStatus(String jobId, JobStatus status) {
        String sql = """
            UPDATE jobs
            SET status = ?,
                updated_at = NOW()
            WHERE job_id = ?
            """;
        
        try {
            jdbcTemplate.update(sql, status.name(), jobId);
            log.info("Updated job {} to {}", jobId, status);
            
        } catch (DataAccessException e) {
            log.error("Failed to update job status, will retry", e);
            throw e; // Trigger @Retryable
        }
    }
}
```

### ✅ Solution 3: Write-Ahead Log (Queue Final State)

```java
@Service
public class EventuallyConsistentWorker {
    
    @Autowired
    private KafkaTemplate<String, JobStatusUpdate> statusQueue;
    
    @Autowired
    private JobRepository jobRepository;
    
    public void processJob(Job job) {
        try {
            // Execute business logic
            Result result = executePayment(job);
            
            // Try to update database
            try {
                jobRepository.updateStatus(job.getJobId(), JobStatus.COMPLETED);
            } catch (DataAccessException e) {
                log.error("DB update failed, publishing to queue for retry");
                
                // Publish status update to queue (durable)
                statusQueue.send("job-status-updates", new JobStatusUpdate(
                    job.getJobId(),
                    JobStatus.COMPLETED,
                    result
                ));
            }
            
        } catch (Exception e) {
            // Same for failure
            statusQueue.send("job-status-updates", new JobStatusUpdate(
                job.getJobId(),
                JobStatus.FAILED,
                e.getMessage()
            ));
        }
    }
}

/**
 * Background consumer: Process status updates from queue
 */
@Service
public class JobStatusUpdater {
    
    @KafkaListener(topics = "job-status-updates")
    @Retryable(maxAttempts = 10)
    public void updateStatus(JobStatusUpdate update) {
        jobRepository.updateStatus(
            update.getJobId(),
            update.getStatus()
        );
    }
}
```

---

## 5. Message Queue Unavailable

### 💥 Failure Scenario

```
Timeline:
10:00:00  Kafka cluster undergoing rolling restart
10:00:05  Producer tries to send job → TimeoutException
10:00:10  Job lost, never queued ❌
10:00:15  Customer reports: "My job never ran!"
```

### ✅ Solution: Dual Write (DB + Queue)

```java
@Service
public class ResilientJobSubmitter {
    
    @Autowired
    private JobRepository jobRepository;
    
    @Autowired
    private KafkaTemplate<String, Job> kafkaTemplate;
    
    @Transactional
    public String submitJob(Job job) {
        job.setJobId(UUID.randomUUID().toString());
        job.setStatus(JobStatus.PENDING);
        job.setCreatedAt(Instant.now());
        
        // 1. Write to database first (durable)
        jobRepository.save(job);
        
        // 2. Try to publish to queue
        try {
            kafkaTemplate.send("job-queue", job).get(5, TimeUnit.SECONDS);
            log.info("Job queued: {}", job.getJobId());
            
        } catch (Exception e) {
            log.error("Kafka unavailable, job saved to DB only", e);
            // Job will be picked up by polling fallback
        }
        
        return job.getJobId();
    }
}

/**
 * Fallback: Poll database for unqueued jobs
 */
@Service
public class JobQueueFallback {
    
    @Scheduled(fixedRate = 60000) // Every minute
    public void pollUnqueuedJobs() {
        // Find jobs created > 2 min ago but still PENDING
        Instant threshold = Instant.now().minus(2, ChronoUnit.MINUTES);
        
        List<Job> unqueued = jobRepository.findByStatusAndCreatedAtBefore(
            JobStatus.PENDING,
            threshold
        );
        
        for (Job job : unqueued) {
            log.warn("Found unqueued job: {}, publishing now", job.getJobId());
            
            try {
                kafkaTemplate.send("job-queue", job);
            } catch (Exception e) {
                log.error("Still can't queue job: {}", job.getJobId(), e);
            }
        }
    }
}
```

---

## 6. Duplicate Job Execution

### 💥 All Causes

1. **Lock expiry** (see #2 above)
2. **Network partition** (see #3 above)
3. **Message redelivery** (Kafka/SQS retries)
4. **Database transaction rollback** (status update failed)
5. **At-least-once semantics** (queue guarantees)

### ✅ Universal Solution: Idempotency Token

```java
@Service
public class IdempotentJobExecutor {
    
    @Autowired
    private JobRepository jobRepository;
    
    @KafkaListener(topics = "job-queue")
    public void processJob(Job job) {
        String jobId = job.getJobId();
        String workerId = getWorkerId();
        
        // Claim job atomically (CAS operation)
        boolean claimed = jobRepository.claim(jobId, workerId);
        
        if (!claimed) {
            log.info("Job {} already claimed, skipping", jobId);
            return; // ← Idempotency: Safe to receive message multiple times
        }
        
        try {
            // Execute with idempotency key
            paymentService.processPayment(
                job.getPaymentId(),
                job.getIdempotencyKey() // ← Passed to external systems
            );
            
            jobRepository.updateStatus(jobId, JobStatus.COMPLETED);
            
        } catch (Exception e) {
            jobRepository.updateStatus(jobId, JobStatus.FAILED);
        }
    }
}
```

**Idempotency in External API Calls**:
```java
@Service
public class PaymentGatewayClient {
    
    public PaymentResponse charge(String paymentId, String idempotencyKey) {
        HttpHeaders headers = new HttpHeaders();
        headers.set("Idempotency-Key", idempotencyKey);
        
        // Stripe, PayPal, etc. use idempotency keys
        // If they receive same key twice, return original response
        PaymentRequest request = new PaymentRequest(paymentId, amount);
        
        return restTemplate.postForObject(
            "https://api.gateway.com/charge",
            new HttpEntity<>(request, headers),
            PaymentResponse.class
        );
    }
}
```

---

## 7. Leader Node Crashes

### 💥 Failure Scenario

```
Timeline:
10:00:00  Controller-1 is leader (scheduling jobs)
10:00:30  💀 Controller-1 crashes (OOMKilled)
10:00:35  Controller-2 detects leader loss
10:00:40  Controller-2 becomes new leader
10:00:41  Resumes scheduling jobs
          
Downtime: 11 seconds
```

### ✅ Solution: Fast Failover with Health Checks

```java
@Service
public class HighAvailabilityLeader {
    
    @Autowired
    private LeaderElectionService leaderElection;
    
    @Autowired
    private JobScheduler scheduler;
    
 @PostConstruct
    public void init() {
        leaderElection.run(
            this::onBecomeLeader,
            this::onLoseLeadership,
            Duration.ofSeconds(5) // Check leadership every 5s
        );
    }
    
    private void onBecomeLeader() {
        log.info("Elected as leader, starting scheduler");
        scheduler.start();
        
        // Start health reporter
        reportHealthToCentralMonitor();
    }
    
    private void onLoseLeadership() {
        log.warn("Lost leadership, shutting down");
        scheduler.stop();
    }
}
```

**Kubernetes Liveness/Readiness Probes**:
```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: job-controller
spec:
  replicas: 3
  template:
    spec:
      containers:
      - name: controller
        livenessProbe:
          httpGet:
            path: /health/liveness
            port: 8080
          initialDelaySeconds: 30
          periodSeconds: 10
          failureThreshold: 3  # Kill after 3 failures
        readinessProbe:
          httpGet:
            path: /health/readiness
            port: 8080
          periodSeconds: 5
          failureThreshold: 2
```

---

## 8. Worker Overload (Cascading Failure)

### 💥 Failure Scenario

```
Timeline:
10:00:00  Normal load: 100 jobs/min, 10 workers (10 jobs/worker/min)
10:05:00  Traffic spike: 1000 jobs/min (10x increase)
10:05:30  Workers overwhelmed: CPU 100%, memory high
10:06:00  Workers start crashing (OOM, timeouts)
10:06:30  Only 3 workers left → Even higher load per worker
10:07:00  All workers crash → Complete outage ❌
```

### ✅ Solution 1: Circuit Breaker

```java
@Service
public class CircuitBreakerWorker {
    
    @CircuitBreaker(
        name = "jobProcessor",
        fallbackMethod = "jobProcessorFallback"
    )
    @RateLimiter(name = "jobProcessor") // Max 10 jobs/sec per worker
    @Bulkhead(name = "jobProcessor", type = Bulkhead.Type.THREADPOOL) // Max 20 concurrent
    @KafkaListener(topics = "job-queue")
    public void processJob(Job job) {
        // Execute job
        heavyComputation(job);
    }
    
    /**
     * Fallback: Reject job if system overloaded
     */
    public void jobProcessorFallback(Job job, Exception e) {
        log.error("System overloaded, rejecting job: {}", job.getJobId());
        
        // Put job back in queue with delay
        kafkaTemplate.send(
            "job-queue-delayed",
            job,
            ProducerRecord.builder()
                .timestamp(System.currentTimeMillis() + 60000) // 1 min delay
                .build()
        );
    }
}
```

**Resilience4j Configuration**:
```yaml
resilience4j:
  circuitbreaker:
    instances:
      jobProcessor:
        sliding-window-size: 100
        failure-rate-threshold: 50  # Open if > 50% failures
        wait-duration-in-open-state: 60s
  ratelimiter:
    instances:
      jobProcessor:
        limit-for-period: 10  # Max 10 jobs
        limit-refresh-period: 1s  # Per second
  bulkhead:
    instances:
      jobProcessor:
        max-concurrent-calls: 20
        max-wait-duration: 10s
```

### ✅ Solution 2: Auto-Scaling

```yaml
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: job-worker-hpa
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: job-worker
  minReplicas: 10
  maxReplicas: 100
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 70
  - type: External
    external:
      metric:
        name: kafka_consumer_lag
      target:
        type: AverageValue
        averageValue: "1000"  # 1000 messages per worker
  behavior:
    scaleUp:
      stabilizationWindowSeconds: 30
      policies:
      - type: Percent
        value: 100  # Double capacity immediately
        periodSeconds: 30
```

---

## 9. Clock Skew Across Instances

### 💥 Failure Scenario

```
Instances:
  Worker-1 time: 10:00:00
  Worker-2 time: 10:00:45 (45 seconds ahead due to NTP drift)
  
Job scheduled for: 10:00:30

Worker-1: 10:00:30 arrives → executes job ✓
Worker-2: Already 10:00:45 → sees job as "due" → also executes ❌
```

### ✅ Solution: Use External Time Source (Database)

```java
@Repository
public class ClockSkewResilientRepository {
    
    /**
     * Use database time, not application time
     */
    public List<Job> findDueJobs() {
        String sql = """
            SELECT * FROM jobs
            WHERE status = 'PENDING'
              AND execute_at <= NOW()  -- ← Database time
            ORDER BY execute_at
            LIMIT 100
            """;
        
        return jdbcTemplate.query(sql, jobRowMapper);
    }
    
    /**
     * Create job with database timestamp
     */
    @Transactional
    public void createJob(Job job) {
        String sql = """
            INSERT INTO jobs (job_id, execute_at, status, created_at)
            VALUES (?, ?, ?, NOW())  -- ← Database generates timestamp
            """;
        
        jdbcTemplate.update(
            sql,
            job.getJobId(),
            job.getExecuteAt(),
            JobStatus.PENDING.name()
        );
    }
}
```

---

## 10. Zombie Jobs (Stuck Forever)

### 💥 Failure Scenario

Job stuck in IN_PROGRESS for days/weeks, never completing or timing out.

### ✅ Solution: Comprehensive Monitoring

```java
@Service
public class ZombieJobKiller {
    
    @Scheduled(cron = "0 0 * * * ?") // Every hour
    public void killZombieJobs() {
        // Jobs IN_PROGRESS for > 24 hours
        Instant zombie Threshold = Instant.now().minus(24, ChronoUnit.HOURS);
        
        List<Job> zombies = jobRepository.findByStatusAndStartedAtBefore(
            JobStatus.IN_PROGRESS,
            zombieThreshold
        );
        
        for (Job job : zombies) {
            log.error("ZOMBIE JOB DETECTED: {} (started: {})",
                job.getJobId(), job.getStartedAt());
            
            // Force mark as FAILED
            jobRepository.updateStatus(job.getJobId(), JobStatus.FAILED);
            
            // Alert on-call immediately
            alertService.sendPagerDutyAlert(
                "CRITICAL: Zombie job detected: " + job.getJobId()
            );
        }
    }
}
```

---

**Next**: [Code Examples →](../05-Code-Examples/)
