# 🔧 Component Roles: Deep Dive into Each Technology

**Purpose**: Understand the specific role, responsibilities, and alternatives for each component in distributed job scheduling systems

---

## 📋 Table of Contents

1. [Redis: The Distributed Lock Manager](#redis)
2. [Message Queues: Job Distribution](#message-queues)
3. [Worker Nodes: Job Executors](#worker-nodes)
4. [Leader Election: Coordination](#leader-election)
5. [Database: State Management](#database)
6. [Scheduler: Timing Coordinator](#scheduler)
7. [Monitoring: Observability](#monitoring)

---

## 🗄️ Redis: The Distributed Lock Manager

### Primary Role
**Coordination Primitive**: Ensures only ONE instance executes a scheduled job across multiple replicas

### How It Works

#### Lock Acquisition Pattern
```java
@Service
public class RedisDistributedLock {
    
    @Autowired
    private StringRedisTemplate redisTemplate;
    
    private static final String LOCK_PREFIX = "job:lock:";
    private static final long LOCK_TTL = 30; // seconds
    
    /**
     * Try to acquire lock for job execution
     * 
     * @param jobName Unique job identifier
     * @param workerId Current instance identifier
     * @return true if lock acquired, false if another instance holds it
     */
    public boolean tryAcquireLock(String jobName, String workerId) {
        String lockKey = LOCK_PREFIX + jobName;
        
        // SETNX: SET if Not eXists (atomic operation)
        Boolean success = redisTemplate.opsForValue().setIfAbsent(
            lockKey,
            workerId,
            Duration.ofSeconds(LOCK_TTL)
        );
        
        return Boolean.TRUE.equals(success);
    }
    
    /**
     * Release lock after job completion
     * Uses Lua script for atomicity: only release if we own the lock
     */
    public void releaseLock(String jobName, String workerId) {
        String lockKey = LOCK_PREFIX + jobName;
        
        String luaScript = 
            "if redis.call('get', KEYS[1]) == ARGV[1] then " +
            "    return redis.call('del', KEYS[1]) " +
            "else " +
            "    return 0 " +
            "end";
        
        redisTemplate.execute(
            new DefaultRedisScript<>(luaScript, Long.class),
            Collections.singletonList(lockKey),
            workerId
        );
    }
    
    /**
     * Extend lock TTL during long-running jobs (heartbeat)
     */
    public boolean extendLock(String jobName, String workerId) {
        String lockKey = LOCK_PREFIX + jobName;
        
        String luaScript = 
            "if redis.call('get', KEYS[1]) == ARGV[1] then " +
            "    return redis.call('expire', KEYS[1], ARGV[2]) " +
            "else " +
            "    return 0 " +
            "end";
        
        Long result = redisTemplate.execute(
            new DefaultRedisScript<>(luaScript, Long.class),
            Collections.singletonList(lockKey),
            workerId,
            String.valueOf(LOCK_TTL)
        );
        
        return result != null && result == 1;
    }
}
```

### Usage in Scheduled Jobs
```java
@Component
public class PaymentReconciliationJob {
    
    @Autowired
    private RedisDistributedLock distributedLock;
    
    @Scheduled(cron = "0 0 2 * * ?") // Every day at 2 AM
    public void reconcilePayments() {
        String jobName = "payment-reconciliation";
        String workerId = getWorkerId();
        
        // Try to acquire lock
        if (!distributedLock.tryAcquireLock(jobName, workerId)) {
            log.info("Another instance is running reconciliation, skipping");
            return;
        }
        
        try {
            log.info("Lock acquired, starting payment reconciliation");
            
            // Execute business logic
            List<Payment> unreconciled = paymentService.findUnreconciled();
            for (Payment payment : unreconciled) {
                reconcile(payment);
            }
            
            log.info("Reconciliation completed successfully");
            
        } finally {
            // Always release lock
            distributedLock.releaseLock(jobName, workerId);
        }
    }
    
    private String getWorkerId() {
        return InetAddress.getLocalHost().getHostName() + "-" + 
               ManagementFactory.getRuntimeMXBean().getName();
    }
}
```

### Why Redis?
✅ **Fast**: Sub-millisecond latency  
✅ **Atomic**: SETNX operation is atomic  
✅ **TTL**: Auto-expires if holder crashes  
✅ **Simple**: No complex setup required  
✅ **Battle-tested**: Used by Netflix, Twitter, GitHub  

### When Redis is NOT Enough
❌ **Network partitions**: Split-brain scenarios possible  
❌ **Clock skew**: TTL depends on Redis server clock  
❌ **Single point of failure**: Without Redis Cluster/Sentinel  
❌ **Large-scale**: > 10k locks → consider ZooKeeper/etcd  

### Production Configuration
```yaml
# application.yml
spring:
  redis:
    host: redis-cluster.prod.example.com
    port: 6379
    password: ${REDIS_PASSWORD}
    timeout: 2000ms
    lettuce:
      pool:
        max-active: 20
        max-idle: 10
        min-idle: 5
      cluster:
        refresh:
          adaptive: true
          period: 30s
```

### Monitoring Redis Locks
```java
@Component
public class LockMetrics {
    
    @Autowired
    private MeterRegistry meterRegistry;
    
    public void recordLockAcquisition(String jobName, boolean success) {
        Counter.builder("job.lock.acquisition")
            .tag("job", jobName)
            .tag("success", String.valueOf(success))
            .register(meterRegistry)
            .increment();
    }
    
    public void recordLockDuration(String jobName, Duration duration) {
        Timer.builder("job.lock.duration")
            .tag("job", jobName)
            .register(meterRegistry)
            .record(duration);
    }
}
```

### Advanced: Redlock Algorithm
For **strong consistency** across Redis cluster:
```java
@Configuration
public class RedlockConfig {
    
    @Bean
    public RedissonClient redissonClient() {
        Config config = new Config();
        config.useClusterServers()
            .addNodeAddress(
                "redis://node1:6379",
                "redis://node2:6379",
                "redis://node3:6379"
            );
        
        return Redisson.create(config);
    }
    
    @Bean
    public RLock distributedLock(RedissonClient redisson, String jobName) {
        return redisson.getLock("job:lock:" + jobName);
    }
}

// Usage
@Autowired
private RedissonClient redisson;

public void executeJob() {
    RLock lock = redisson.getLock("payment-job");
    
    try {
        // Wait up to 10s to acquire, auto-release after 30s
        boolean acquired = lock.tryLock(10, 30, TimeUnit.SECONDS);
        
        if (acquired) {
            // Execute job
            processPayments();
        }
    } finally {
        if (lock.isHeldByCurrentThread()) {
            lock.unlock();
        }
    }
}
```

---

## 📨 Message Queues: Job Distribution

### Primary Role
**Job Transport**: Distribute work across multiple worker instances with guaranteed delivery

### Popular Options

#### 1. Apache Kafka (High Throughput)
```java
// Producer: Job submission
@Service
public class KafkaJobProducer {
    
    @Autowired
    private KafkaTemplate<String, JobMessage> kafkaTemplate;
    
    public void submitJob(JobMessage job) {
        // Partition by jobId for ordering
        kafkaTemplate.send("job-queue", job.getJobId(), job)
            .addCallback(
                success -> log.info("Job queued: {}", job.getJobId()),
                failure -> log.error("Failed to queue job", failure)
            );
    }
}

// Consumer: Job processing
@Service
public class KafkaJobConsumer {
    
    @KafkaListener(
        topics = "job-queue",
        groupId = "job-workers",
        concurrency = "10" // 10 parallel consumers
    )
    public void consumeJob(JobMessage job) {
        log.info("Processing job: {}", job.getJobId());
        
        try {
            executeJob(job);
            
            // Kafka auto-commits offset on success
        } catch (Exception e) {
            log.error("Job failed: {}", job.getJobId(), e);
            
            // Throw to trigger retry (Kafka will redeliver)
            throw e;
        }
    }
}
```

**Kafka Configuration for Jobs**:
```yaml
spring:
  kafka:
    bootstrap-servers: kafka-cluster:9092
    consumer:
      group-id: job-workers
      auto-offset-reset: earliest
      enable-auto-commit: false # Manual commit after processing
      max-poll-records: 100
    listener:
      ack-mode: record # Commit per message
      concurrency: 10
    producer:
      retries: 3
      acks: all # Wait for all replicas
```

#### 2. AWS SQS (Managed Service)
```java
@Service
public class SqsJobProcessor {
    
    @Autowired
    private AmazonSQS sqsClient;
    
    private static final String QUEUE_URL = 
        "https://sqs.us-east-1.amazonaws.com/123456/job-queue";
    
    @Scheduled(fixedRate = 1000)
    public void pollAndProcess() {
        // Long polling (wait up to 20s for messages)
        ReceiveMessageRequest request = new ReceiveMessageRequest()
            .withQueueUrl(QUEUE_URL)
            .withMaxNumberOfMessages(10)
            .withWaitTimeSeconds(20)
            .withVisibilityTimeout(300); // 5 min processing time
        
        ReceiveMessageResult result = sqsClient.receiveMessage(request);
        
        for (Message message : result.getMessages()) {
            try {
                JobMessage job = parseJob(message.getBody());
                executeJob(job);
                
                // Delete message on success
                sqsClient.deleteMessage(QUEUE_URL, message.getReceiptHandle());
                
            } catch (Exception e) {
                log.error("Job failed, will retry", e);
                
                // Change visibility timeout for exponential backoff
                changeVisibility(message, calculateBackoff(message));
            }
        }
    }
    
    private int calculateBackoff(Message message) {
        int attemptCount = Integer.parseInt(
            message.getAttributes()
                .getOrDefault("ApproximateReceiveCount", "1")
        );
        
        // Exponential backoff: 30s, 60s, 120s, ...
        return Math.min(30 * (int) Math.pow(2, attemptCount - 1), 900);
    }
}
```

#### 3. RabbitMQ (Feature-Rich)
```java
@Configuration
public class RabbitMQConfig {
    
    // Priority queue for different job types
    @Bean
    public Queue highPriorityQueue() {
        Map<String, Object> args = new HashMap<>();
        args.put("x-max-priority", 10); // Priority 0-10
        return new Queue("jobs.high-priority", true, false, false, args);
    }
    
    @Bean
    public Queue lowPriorityQueue() {
        return new Queue("jobs.low-priority", true);
    }
    
    // Dead letter queue for failed jobs
    @Bean
    public Queue deadLetterQueue() {
        return new Queue("jobs.dlq", true);
    }
    
    @Bean
    public DirectExchange jobExchange() {
        return new DirectExchange("job-exchange");
    }
}

@Service
public class RabbitMQJobConsumer {
    
    @RabbitListener(queues = "jobs.high-priority", concurrency = "20")
    public void processHighPriority(JobMessage job) {
        log.info("Processing HIGH priority job: {}", job.getJobId());
        executeJob(job);
    }
    
    @RabbitListener(queues = "jobs.low-priority", concurrency = "5")
    public void processLowPriority(JobMessage job) {
        log.info("Processing LOW priority job: {}", job.getJobId());
        executeJob(job);
    }
}
```

### Why Message Queues?
✅ **Decoupling**: Job submitters don't need to know about workers  
✅ **Scalability**: Add workers without code changes  
✅ **Durability**: Jobs persist even if workers crash  
✅ **Retry**: Automatic redelivery on failure  
✅ **Backpressure**: Workers pull at their own pace  

### Comparison

| Feature | Kafka | SQS | RabbitMQ |
|---------|-------|-----|----------|
| **Throughput** | 1M msgs/sec | 3k msgs/sec | 50k msgs/sec |
| **Latency** | < 10ms | 10-100ms | < 5ms |
| **Ordering** | Per partition | FIFO queue | Per queue |
| **Retention** | Days/weeks | 14 days max | Until consumed |
| **Setup** | Complex | Zero (managed) | Medium |
| **Cost** | Self-hosted | $0.40/M msgs | Self-hosted |
| **Best For** | High volume | AWS ecosystem | Complex routing |

### When to Use Which?

**Use Kafka** when:
- Processing > 100k jobs/day
- Need long retention (replay jobs)
- Already using Kafka ecosystem
- Example: Video encoding, analytics

**Use SQS** when:
- AWS infrastructure
- Want zero operational overhead
- < 100k jobs/day
- Example: Email sending, notifications

**Use RabbitMQ** when:
- Need priority queues
- Complex routing patterns
- Sub-millisecond latency
- Example: Real-time bid processing

---

## 👷 Worker Nodes: Job Executors

### Primary Role
**Job Execution**: Actually perform the business logic (API calls, DB operations, computations)

### Worker Architecture

```
┌────────────────────────────────────────────┐
│           Worker Instance (Pod)            │
│                                            │
│  ┌──────────────────────────────────────┐ │
│  │  Message Consumer Thread Pool        │ │
│  │  - Poll queue continuously            │ │
│  │  - 10-100 threads                     │ │
│  └──────────────┬───────────────────────┘ │
│                 │                          │
│                 ▼                          │
│  ┌──────────────────────────────────────┐ │
│  │  Job Executor Service                │ │
│  │  - Business logic                     │ │
│  │  - API calls, DB updates              │ │
│  └──────────────┬───────────────────────┘ │
│                 │                          │
│                 ▼                          │
│  ┌──────────────────────────────────────┐ │
│  │  Status Reporter                      │ │
│  │  - Update job status                  │ │
│  │  - Emit metrics                       │ │
│  └──────────────────────────────────────┘ │
└────────────────────────────────────────────┘
```

### Worker Implementation
```java
@Service
public class VideoEncodingWorker {
    
    @Autowired
    private JobRepository jobRepository;
    
    @Autowired
    private FFmpegService ffmpegService;
    
    @Autowired
    private S3Client s3Client;
    
    @Autowired
    private MetricsService metrics;
    
    @KafkaListener(
        topics = "encoding-jobs",
        groupId = "encoding-workers",
        concurrency = "#{@environment.getProperty('worker.concurrency', '10')}"
    )
    public void processEncodingJob(EncodingJob job) {
        String workerId = getWorkerId();
        Instant startTime = Instant.now();
        
        log.info("[Worker: {}] Started job: {}", workerId, job.getJobId());
        
        try {
            // 1. Claim job (idempotency check)
            boolean claimed = jobRepository.claimJob(
                job.getJobId(), 
                JobStatus.PENDING, 
                JobStatus.IN_PROGRESS,
                workerId
            );
            
            if (!claimed) {
                log.warn("Job already claimed by another worker");
                metrics.incrementDuplicate(job.getJobId());
                return;
            }
            
            // 2. Download input video
            File inputFile = downloadFromS3(job.getInputUrl());
            
            // 3. Encode video
            File outputFile = ffmpegService.encode(
                inputFile, 
                job.getResolution(),
                job.getCodec()
            );
            
            // 4. Upload output video
            String outputUrl = uploadToS3(outputFile, job.getJobId());
            
            // 5. Update job status
            jobRepository.updateJobCompleted(
                job.getJobId(),
                outputUrl,
                Duration.between(startTime, Instant.now())
            );
            
            // 6. Emit metrics
            metrics.recordSuccess(job, Duration.between(startTime, Instant.now()));
            
            log.info("[Worker: {}] Completed job: {} in {}", 
                workerId, job.getJobId(), 
                Duration.between(startTime, Instant.now()));
            
        } catch (Exception e) {
            log.error("[Worker: {}] Job failed: {}", workerId, job.getJobId(), e);
            
            // Handle failure
            handleFailure(job, e, startTime);
        }
    }
    
    private void handleFailure(EncodingJob job, Exception error, Instant startTime) {
        int retryCount = job.getRetryCount();
        
        if (retryCount < 3) {
            // Retry with exponential backoff
            job.setRetryCount(retryCount + 1);
            job.setNextRetryAt(
                Instant.now().plus(
                    Duration.ofMinutes((long) Math.pow(2, retryCount))
                )
            );
            
            jobRepository.updateJobForRetry(job);
            metrics.incrementRetry(job.getJobId());
            
        } else {
            // Max retries exceeded
            jobRepository.updateJobFailed(
                job.getJobId(), 
                error.getMessage()
            );
            
            metrics.recordFailure(
                job, 
                Duration.between(startTime, Instant.now())
            );
            
            // Alert on-call
            alertService.sendAlert(
                "Encoding job permanently failed: " + job.getJobId()
            );
        }
    }
    
    private String getWorkerId() {
        return System.getenv("HOSTNAME") + "-" + 
               Thread.currentThread().getId();
    }
}
```

### Worker Scaling Strategy

#### Auto-Scaling Configuration (Kubernetes)
```yaml
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: encoding-worker-hpa
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: encoding-worker
  minReplicas: 5
  maxReplicas: 100
  metrics:
  
  # Scale based on CPU
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 70
  
  # Scale based on memory
  - type: Resource
    resource:
      name: memory
      target:
        type: Utilization
        averageUtilization: 80
  
  # Scale based on queue depth (custom metric)
  - type: External
    external:
      metric:
        name: kafka_consumer_lag
        selector:
          matchLabels:
            topic: encoding-jobs
            consumer_group: encoding-workers
      target:
        type: AverageValue
        averageValue: "1000" # 1000 messages per worker
  
  behavior:
    scaleUp:
      stabilizationWindowSeconds: 60
      policies:
      - type: Percent
        value: 50  # Scale up 50% at a time
        periodSeconds: 60
    scaleDown:
      stabilizationWindowSeconds: 300
      policies:
      - type: Pods
        value: 2  # Scale down 2 pods at a time
        periodSeconds: 120
```

### Worker Health Checks
```java
@RestController
@RequestMapping("/health")
public class WorkerHealthController {
    
    @Autowired
    private KafkaListenerEndpointRegistry registry;
    
    @GetMapping("/liveness")
    public ResponseEntity<String> liveness() {
        // Am I alive? (K8s will restart if fails)
        return ResponseEntity.ok("ALIVE");
    }
    
    @GetMapping("/readiness")
    public ResponseEntity<String> readiness() {
        // Am I ready to accept work?
        
        // Check Kafka connection
        boolean kafkaHealthy = registry.getAllListenerContainers()
            .stream()
            .allMatch(container -> container.isRunning());
        
        if (!kafkaHealthy) {
            return ResponseEntity.status(503).body("Kafka listener not ready");
        }
        
        // Check database connection
        try {
            jobRepository.healthCheck();
        } catch (Exception e) {
            return ResponseEntity.status(503).body("Database not ready");
        }
        
        return ResponseEntity.ok("READY");
    }
}
```

### Resource Limits
```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: encoding-worker
spec:
  replicas: 10
  template:
    spec:
      containers:
      - name: worker
        image: encoding-worker:v1.0.0
        resources:
          requests:
            cpu: "2"       # Guaranteed CPU
            memory: "4Gi"  # Guaranteed memory
          limits:
            cpu: "4"       # Max CPU
            memory: "8Gi"  # Max memory (OOMKill if exceeded)
        env:
        - name: WORKER_CONCURRENCY
          value: "10"  # 10 parallel jobs per pod
        - name: JAVA_OPTS
          value: "-Xmx6g -XX:+UseG1GC"
```

---

## ☸️ Leader Election: Coordination

### Primary Role
**Single Scheduler**: Ensure only ONE instance schedules jobs (others are standby)

### Kubernetes Lease API (Native)
```java
@Service
public class KubernetesLeaderElection {
    
    @Autowired
    private LeaderElectionService leaderElection;
    
    @Autowired
    private JobScheduler jobScheduler;
    
    @PostConstruct
    public void init() {
        leaderElection.run(
            this::onBecomeLeader,
            this::onLoseLeadership
        );
    }
    
    private void onBecomeLeader() {
        log.info("🎖️  I AM THE LEADER! Starting job scheduler...");
        jobScheduler.start();
    }
    
    private void onLoseLeadership() {
        log.warn("⚠️  Lost leadership, shutting down scheduler");
        jobScheduler.stop();
    }
}
```

**Spring Boot Configuration**:
```yaml
spring:
  cloud:
    kubernetes:
      leader:
        enabled: true
        role: scheduler
        namespace: production
        config-map-name: scheduler-leader
```

### ZooKeeper (Traditional)
```java
@Service
public class ZooKeeperLeaderElection {
    
    private final CuratorFramework zkClient;
    private LeaderLatch leaderLatch;
    
    public ZooKeeperLeaderElection(CuratorFramework zkClient) {
        this.zkClient = zkClient;
    }
    
    @PostConstruct
    public void start() {
        leaderLatch = new LeaderLatch(
            zkClient, 
            "/scheduler/leader",
            getInstanceId()
        );
        
        leaderLatch.addListener(new LeaderLatchListener() {
            @Override
            public void isLeader() {
                log.info("Elected as leader");
                startScheduling();
            }
            
            @Override
            public void notLeader() {
                log.info("I am a follower");
                stopScheduling();
            }
        });
        
        leaderLatch.start();
    }
    
    public boolean isLeader() {
        return leaderLatch.hasLeadership();
    }
}
```

### Comparison

| Technology | Setup | Failover Time | Complexity |
|------------|-------|---------------|------------|
| Redis Lock | Simple | 1-30s (TTL) | Low |
| K8s Lease | Zero (native) | 2-5s | Low |
| ZooKeeper | Complex | < 1s | High |
| etcd | Medium | < 2s | Medium |

---

## 💾 Database: State Management

### Primary Role
**Job Persistence**: Store job metadata, status, history for auditing and idempotency

### Schema Design
```sql
CREATE TABLE scheduled_jobs (
    job_id VARCHAR(36) PRIMARY KEY,
    job_type VARCHAR(50) NOT NULL,
    payload JSONB NOT NULL,
    status VARCHAR(20) NOT NULL, -- PENDING, IN_PROGRESS, COMPLETED, FAILED
    execute_at TIMESTAMP NOT NULL,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    started_at TIMESTAMP,
    completed_at TIMESTAMP,
    worker_id VARCHAR(100),
    retry_count INTEGER DEFAULT 0,
    error_message TEXT,
    execution_duration_ms INTEGER,
    
    INDEX idx_status_execute_at (status, execute_at),
    INDEX idx_created_at (created_at DESC)
);

-- Query for due jobs
SELECT * FROM scheduled_jobs 
WHERE status = 'PENDING' 
  AND execute_at <= NOW()
ORDER BY execute_at
LIMIT 1000;
```

### Idempotency via Database
```java
@Repository
public class JobRepository {
    
    /**
     * Atomic claim: Update status only if currently PENDING
     * Returns true only for ONE worker (others get false)
     */
    @Transactional
    public boolean claimJob(String jobId, String workerId) {
        String sql = """
            UPDATE scheduled_jobs
            SET status = 'IN_PROGRESS',
                worker_id = ?,
                started_at = NOW(),
                updated_at = NOW()
            WHERE job_id = ?
              AND status = 'PENDING'
            """;
        
        int updated = jdbcTemplate.update(sql, workerId, jobId);
        
        // Only one worker gets updated = 1
        return updated == 1;
    }
}
```

---

## 🕐 Scheduler: Timing Coordinator

### Primary Role
**Cron Execution**: Trigger jobs at scheduled times (cron expressions)

See [Comparison Guide](../03-Comparisons/README.md#scheduler-comparison) for detailed comparison of Quartz, Spring @Scheduled, and Kubernetes CronJob.

---

## 📊 Monitoring: Observability

### Key Metrics
```java
@Component
public class JobMetrics {
    
    private final MeterRegistry registry;
    
    // Counter: Jobs processed
    private final Counter jobsProcessed;
    
    // Timer: Job execution duration
    private final Timer jobDuration;
    
    // Gauge: Active workers
    private final AtomicInteger activeWorkers = new AtomicInteger(0);
    
    public JobMetrics(MeterRegistry registry) {
        this.registry = registry;
        
        this.jobsProcessed = Counter.builder("jobs.processed")
            .description("Total jobs processed")
            .tag("status", "completed")
            .register(registry);
        
        this.jobDuration = Timer.builder("jobs.duration")
            .description("Job execution time")
            .publishPercentiles(0.5, 0.95, 0.99)
            .register(registry);
        
        Gauge.builder("jobs.workers.active", activeWorkers, AtomicInteger::get)
            .description("Number of active worker threads")
            .register(registry);
    }
}
```

### Grafana Dashboard Queries
```promql
# Job throughput
rate(jobs_processed_total[5m])

# Average execution time
rate(jobs_duration_sum[5m]) / rate(jobs_duration_count[5m])

# P99 latency
histogram_quantile(0.99, rate(jobs_duration_bucket[5m]))

# Failure rate
rate(jobs_processed_total{status="failed"}[5m]) / 
  rate(jobs_processed_total[5m])
```

---

**Next**: [Comparisons →](../03-Comparisons/)
