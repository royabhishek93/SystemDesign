# 💻 Code Examples: Production-Ready Implementations

**Purpose**: Copy-paste friendly code examples for every major approach in distributed job scheduling

---

## 📋 Table of Contents

1. [Spring Boot + Redis Lock](#1-spring-boot--redis-lock)
2. [Kubernetes Leader Election](#2-kubernetes-leader-election)
3. [Quartz Clustered Scheduler](#3-quartz-clustered-scheduler)
4. [Kafka Queue-Based Workers](#4-kafka-queue-based-workers)
5. [Kubernetes CronJob (YAML)](#5-kubernetes-cronjob)
6. [PostgreSQL Pessimistic Lock](#6-postgresql-pessimistic-lock)
7. [Idempotency Key Handling](#7-idempotency-key-handling)

---

## 1. Spring Boot + Redis Lock

### Maven Dependencies
```xml
<dependencies>
    <dependency>
        <groupId>org.springframework.boot</groupId>
        <artifactId>spring-boot-starter-web</artifactId>
    </dependency>
    <dependency>
        <groupId>org.springframework.boot</groupId>
        <artifactId>spring-boot-starter-data-redis</artifactId>
    </dependency>
    <dependency>
        <groupId>org.springframework.boot</groupId>
        <artifactId>spring-boot-starter-actuator</artifactId>
    </dependency>
    <dependency>
        <groupId>io.lettuce</groupId>
        <artifactId>lettuce-core</artifactId>
    </dependency>
</dependencies>
```

### Redis Lock Service
```java
@Service
public class RedisLockService {
    
    private static final String LOCK_PREFIX = "lock:";
    private static final long LOCK_TTL_SECONDS = 30;
    
    @Autowired
    private StringRedisTemplate redisTemplate;
    
    public boolean acquireLock(String lockName, String ownerId) {
        String key = LOCK_PREFIX + lockName;
        
        Boolean acquired = redisTemplate.opsForValue().setIfAbsent(
            key,
            ownerId,
            Duration.ofSeconds(LOCK_TTL_SECONDS)
        );
        
        return Boolean.TRUE.equals(acquired);
    }
    
    public void releaseLock(String lockName, String ownerId) {
        String key = LOCK_PREFIX + lockName;
        
        String luaScript = """
            if redis.call('get', KEYS[1]) == ARGV[1] then
                return redis.call('del', KEYS[1])
            else
                return 0
            end
            """;
        
        redisTemplate.execute(
            new DefaultRedisScript<>(luaScript, Long.class),
            Collections.singletonList(key),
            ownerId
        );
    }
    
    public boolean extendLock(String lockName, String ownerId) {
        String key = LOCK_PREFIX + lockName;
        
        String luaScript = """
            if redis.call('get', KEYS[1]) == ARGV[1] then
                return redis.call('expire', KEYS[1], ARGV[2])
            else
                return 0
            end
            """;
        
        Long result = redisTemplate.execute(
            new DefaultRedisScript<>(luaScript, Long.class),
            Collections.singletonList(key),
            ownerId,
            String.valueOf(LOCK_TTL_SECONDS)
        );
        
        return result != null && result == 1;
    }
}
```

### Scheduled Job with Redis Lock
```java
@Component
public class DailyBillingJob {
    
    @Autowired
    private RedisLockService lockService;
    
    @Autowired
    private BillingService billingService;
    
    @Scheduled(cron = "0 0 1 * * ?") // 1 AM daily
    public void runBilling() {
        String lockName = "daily-billing";
        String ownerId = getInstanceId();
        
        if (!lockService.acquireLock(lockName, ownerId)) {
            log.info("Another instance running billing, skipping");
            return;
        }
        
        // Start lock renewal thread
        ScheduledExecutorService renewer = Executors.newScheduledThreadPool(1);
        renewer.scheduleAtFixedRate(
            () -> lockService.extendLock(lockName, ownerId),
            10,
            10,
            TimeUnit.SECONDS
        );
        
        try {
            billingService.processDailyBilling();
            
        } finally {
            renewer.shutdown();
            lockService.releaseLock(lockName, ownerId);
        }
    }
    
    private String getInstanceId() {
        return System.getenv("HOSTNAME");
    }
}
```

---

## 2. Kubernetes Leader Election

### Maven Dependencies
```xml
<dependency>
    <groupId>org.springframework.cloud</groupId>
    <artifactId>spring-cloud-starter-kubernetes-fabric8</artifactId>
    <version>3.0.4</version>
</dependency>
```

### Configuration
```yaml
spring:
  cloud:
    kubernetes:
      leader:
        enabled: true
        namespace: default
        role: scheduler
        config-map-name: scheduler-leader
```

### Leader-Aware Scheduler
```java
@Component
public class LeaderAwareScheduler {
    
    @Autowired
    private LeaderInitiator leaderInitiator;
    
    @Autowired
    private JobScheduler jobScheduler;
    
    @PostConstruct
    public void init() {
        leaderInitiator.addEventHandler(new LeaderEventHandler() {
            @Override
            public void onGranted(Context context) {
                log.info("I am the leader, starting scheduler");
                jobScheduler.start();
            }
            
            @Override
            public void onRevoked(Context context) {
                log.warn("Leadership revoked, stopping scheduler");
                jobScheduler.stop();
            }
        });
    }
}
```

---

## 3. Quartz Clustered Scheduler

### Maven Dependencies
```xml
<dependency>
    <groupId>org.springframework.boot</groupId>
    <artifactId>spring-boot-starter-quartz</artifactId>
</dependency>
<dependency>
    <groupId>org.postgresql</groupId>
    <artifactId>postgresql</artifactId>
</dependency>
```

### Quartz Configuration
```yaml
spring:
  quartz:
    job-store-type: jdbc
    jdbc:
      initialize-schema: always
    properties:
      org:
        quartz:
          scheduler:
            instanceId: AUTO
          jobStore:
            class: org.quartz.impl.jdbcjobstore.JobStoreTX
            driverDelegateClass: org.quartz.impl.jdbcjobstore.PostgreSQLDelegate
            tablePrefix: QRTZ_
            isClustered: true
            clusterCheckinInterval: 20000
          threadPool:
            threadCount: 10
```

### Quartz Job
```java
@Component
public class ReportJob implements Job {
    
    @Override
    public void execute(JobExecutionContext context) {
        log.info("Generating weekly report");
        reportService.generate();
    }
}
```

### Quartz Scheduler Setup
```java
@Configuration
public class QuartzConfig {
    
    @Bean
    public JobDetail reportJobDetail() {
        return JobBuilder.newJob(ReportJob.class)
            .withIdentity("weeklyReport")
            .storeDurably()
            .build();
    }
    
    @Bean
    public Trigger reportTrigger() {
        return TriggerBuilder.newTrigger()
            .forJob(reportJobDetail())
            .withSchedule(CronScheduleBuilder.cronSchedule("0 0 9 ? * MON"))
            .build();
    }
}
```

---

## 4. Kafka Queue-Based Workers

### Producer: Submit Jobs
```java
@Service
public class JobProducer {
    
    @Autowired
    private KafkaTemplate<String, Job> kafkaTemplate;
    
    public void submitJob(Job job) {
        kafkaTemplate.send("job-queue", job.getJobId(), job)
            .addCallback(
                success -> log.info("Job queued: {}", job.getJobId()),
                failure -> log.error("Failed to queue job", failure)
            );
    }
}
```

### Consumer: Execute Jobs
```java
@Service
public class JobConsumer {
    
    @KafkaListener(
        topics = "job-queue",
        groupId = "job-workers",
        concurrency = "20"
    )
    public void processJob(Job job) {
        String workerId = getWorkerId();
        
        try {
            executeJob(job);
            jobRepository.updateStatus(job.getJobId(), JobStatus.COMPLETED);
            
        } catch (Exception e) {
            jobRepository.updateStatus(job.getJobId(), JobStatus.FAILED);
            throw e; // Trigger retry
        }
    }
}
```

### Kafka Configuration
```yaml
spring:
  kafka:
    bootstrap-servers: kafka-cluster:9092
    consumer:
      enable-auto-commit: false
      max-poll-records: 50
      fetch-max-wait: 500
    listener:
      ack-mode: record
      concurrency: 20
    producer:
      retries: 3
      acks: all
```

---

## 5. Kubernetes CronJob

```yaml
apiVersion: batch/v1
kind: CronJob
metadata:
  name: daily-report
spec:
  schedule: "0 1 * * *"  # 1 AM daily
  jobTemplate:
    spec:
      template:
        spec:
          containers:
          - name: report
            image: report-generator:v1
            env:
            - name: REPORT_TYPE
              value: "daily"
          restartPolicy: OnFailure
```

---

## 6. PostgreSQL Pessimistic Lock

```sql
BEGIN;

-- Lock row for update (blocks other workers)
SELECT * FROM scheduled_jobs
WHERE status = 'PENDING'
ORDER BY execute_at
LIMIT 1
FOR UPDATE SKIP LOCKED;

-- Mark as IN_PROGRESS
UPDATE scheduled_jobs
SET status = 'IN_PROGRESS',
    worker_id = 'worker-1',
    updated_at = NOW()
WHERE job_id = 'job-123';

COMMIT;
```

### Java Implementation
```java
@Repository
public class PostgresLockRepository {
    
    @Transactional
    public Optional<Job> claimNextJob() {
        String selectSql = """
            SELECT * FROM scheduled_jobs
            WHERE status = 'PENDING'
            ORDER BY execute_at
            LIMIT 1
            FOR UPDATE SKIP LOCKED
            """;
        
        List<Job> jobs = jdbcTemplate.query(selectSql, jobMapper);
        
        if (jobs.isEmpty()) {
            return Optional.empty();
        }
        
        Job job = jobs.get(0);
        
        String updateSql = """
            UPDATE scheduled_jobs
            SET status = 'IN_PROGRESS',
                worker_id = ?,
                updated_at = NOW()
            WHERE job_id = ?
            """;
        
        jdbcTemplate.update(updateSql, getWorkerId(), job.getJobId());
        
        return Optional.of(job);
    }
}
```

---

## 7. Idempotency Key Handling

### API Idempotency
```java
@RestController
@RequestMapping("/payments")
public class PaymentController {
    
    @PostMapping
    public ResponseEntity<PaymentResponse> createPayment(
            @RequestHeader("Idempotency-Key") String key,
            @RequestBody PaymentRequest request) {
        
        PaymentResponse response = paymentService.processPayment(request, key);
        return ResponseEntity.ok(response);
    }
}
```

### Service with Idempotency
```java
@Service
public class PaymentService {
    
    @Autowired
    private PaymentRepository paymentRepository;
    
    @Transactional
    public PaymentResponse processPayment(PaymentRequest request, String key) {
        // Check if payment already processed
        Optional<Payment> existing = paymentRepository.findByIdempotencyKey(key);
        
        if (existing.isPresent()) {
            return new PaymentResponse(existing.get()); // Return previous result
        }
        
        // Process new payment
        Payment payment = new Payment();
        payment.setIdempotencyKey(key);
        payment.setAmount(request.getAmount());
        payment.setStatus("COMPLETED");
        
        paymentRepository.save(payment);
        
        return new PaymentResponse(payment);
    }
}
```

### Database Constraint
```sql
CREATE TABLE payments (
    id BIGSERIAL PRIMARY KEY,
    idempotency_key VARCHAR(64) UNIQUE NOT NULL,
    amount DECIMAL(10, 2),
    status VARCHAR(20),
    created_at TIMESTAMP DEFAULT NOW()
);
```

---

**Next**: [Back to Overview →](../README.md)
