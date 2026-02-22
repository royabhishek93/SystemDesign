# Implementation Approaches

**Target Level**: Senior+ (5-7 years)  
**Interview Focus**: Real production code and technology choices

## 📋 Overview

This chapter covers 5 production-grade approaches with runnable code examples. Each includes:

- ✅ Real code you can implement
- ✅ When to use it
- ✅ Pros and cons
- ✅ Interview talking points
- ✅ Production pitfalls

## 🔒 Approach 1: Redis Distributed Lock (Most Common)

**Best for**: Simple systems, moderate scale, existing Redis infrastructure

### The Concept

Before running job → acquire global lock in Redis → only one instance succeeds → execute → release lock

### Flow Diagram

```
Multiple Instances            Redis                  Job Execution
      │                         │                          │
      ├─── SETNX "lock" ────────┼──→ Success ─────────────┼──→ Execute
      │                         │                          │
      ├─── SETNX "lock" ────────┼──→ Already exists       │
      │                         │    (returns null)        │
      ├─── SETNX "lock" ────────┼──→ Already exists       │
      │                         │                          │
      │                         │    ← Job completes ──────┤
      │                         │                          │
      └─── DEL "lock" ──────────┼──→ Released             │
```

### ✅ Implementation with Spring Boot + Redis

**Dependencies** (`pom.xml`):
```xml
<dependency>
    <groupId>org.springframework.boot</groupId>
    <artifactId>spring-boot-starter-data-redis</artifactId>
</dependency>
```

**Basic Implementation**:
```java
@Component
@Slf4j
public class DistributedJobScheduler {
    
    @Autowired
    private RedisTemplate<String, String> redisTemplate;
    
    @Autowired
    private ReportService reportService;
    
    private static final String LOCK_KEY = "job:daily-report:lock";
    private static final long LOCK_TIMEOUT = 5; // minutes
    
    @Scheduled(cron = "0 0 2 * * *") // 2:00 AM daily
    public void generateDailyReport() {
        
        // Try to acquire lock atomically
        Boolean locked = redisTemplate.opsForValue()
            .setIfAbsent(
                LOCK_KEY, 
                InetAddress.getLocalHost().getHostName(),
                Duration.ofMinutes(LOCK_TIMEOUT)
            );
        
        if (Boolean.TRUE.equals(locked)) {
            try {
                log.info("Lock acquired, executing job");
                reportService.generateAndSendReport();
                log.info("Job completed successfully");
            } catch (Exception e) {
                log.error("Job execution failed", e);
                throw e; // Allow retry mechanism to handle
            } finally {
                // Release lock
                redisTemplate.delete(LOCK_KEY);
                log.info("Lock released");
            }
        } else {
            log.info("Job already running on another instance, skipping");
        }
    }
}
```

### ⭐ Production-Grade Implementation with Redisson

**Why Redisson**: Handles edge cases like lock renewal (watchdog)

```java
@Configuration
public class RedissonConfig {
    @Bean
    public RedissonClient redissonClient() {
        Config config = new Config();
        config.useSingleServer()
              .setAddress("redis://localhost:6379")
              .setConnectionPoolSize(50);
        return Redisson.create(config);
    }
}

@Component
@Slf4j
public class DistributedJobWithRedisson {
    
    @Autowired
    private RedissonClient redissonClient;
    
    @Autowired
    private ReportService reportService;
    
    @Scheduled(cron = "0 0 2 * * *")
    public void generateDailyReport() {
        
        RLock lock = redissonClient.getLock("job:daily-report");
        
        try {
            // Try to acquire lock, wait up to 10 seconds, auto-release after 5 minutes
            boolean locked = lock.tryLock(10, 300, TimeUnit.SECONDS);
            
            if (locked) {
                try {
                    log.info("Lock acquired with watchdog, executing job");
                    reportService.generateAndSendReport();
                } finally {
                    lock.unlock();
                    log.info("Lock released");
                }
            } else {
                log.info("Could not acquire lock, another instance is running");
            }
            
        } catch (InterruptedException e) {
            Thread.currentThread().interrupt();
            log.error("Lock acquisition interrupted", e);
        }
    }
}
```

### 🎯 Interview Talking Points (Critical!)

When explaining this approach, mention:

1. **Atomic operation**: "`setIfAbsent` is atomic - uses Redis `SETNX` which prevents race conditions"

2. **TTL for safety**: "TTL prevents deadlock if instance crashes while holding lock"

3. **Watchdog pattern**: "Redisson provides automatic lock renewal (watchdog) if job runs longer than TTL"

4. **Lock value**: "Store instance hostname in lock value for debugging - can see which node holds lock"

### ❌ Wrong vs ✅ Right

**❌ Wrong - Non-atomic check**:
```java
// Race condition!
Boolean exists = redisTemplate.hasKey(LOCK_KEY);
if (!exists) {
    redisTemplate.opsForValue().set(LOCK_KEY, "locked"); // Too late!
    doWork();
}
```

**✅ Right - Atomic operation**:
```java
Boolean locked = redisTemplate.opsForValue()
    .setIfAbsent(LOCK_KEY, "locked", Duration.ofMinutes(5));
```

### Pros & Cons

**✅ Pros**:
- Simple to understand and implement
- Works with existing Redis infrastructure
- Minimal setup - just need shared Redis
- Good for infrequent jobs (hourly/daily)

**❌ Cons**:
- All instances attempt lock on every trigger (coordination overhead)
- Requires careful TTL tuning
- Redis becomes single point of dependency
- Potential split-brain in Redis cluster scenarios

---

## 👑 Approach 2: Leader Election (Most Scalable)

**Best for**: Large clusters, many scheduled jobs, cloud-native systems

### The Concept

One instance becomes "leader" → only leader runs scheduler → if leader fails → new leader elected automatically

### Option A: Kubernetes Leader Election ⭐ (2026 Standard)

**Dependencies** (`pom.xml`):
```xml
<dependency>
    <groupId>org.springframework.cloud</groupId>
    <artifactId>spring-cloud-kubernetes-fabric8-leader</artifactId>
</dependency>
```

**Implementation**:
```java
@Component
@Slf4j
public class LeaderAwareScheduler {
    
    @Autowired
    private LeadershipController leadershipController;
    
    @Autowired
    private ReportService reportService;
    
    @Scheduled(cron = "0 0 2 * * *")
    public void generateDailyReport() {
        
        if (leadershipController.isLeader()) {
            log.info("I am the leader, executing job");
            reportService.generateAndSendReport();
        } else {
            log.info("I am a follower, skipping job");
        }
    }
    
    // Optional: React to leadership changes
    @EventListener
    public void onLeadershipAcquired(OnGrantedEvent event) {
        log.info("🎉 Leadership acquired for role: {}", event.getRole());
    }
    
    @EventListener
    public void onLeadershipRevoked(OnRevokedEvent event) {
        log.info("Leadership revoked for role: {}", event.getRole());
    }
}
```

**Kubernetes Configuration** (`deployment.yaml`):
```yaml
apiVersion: v1
kind: ServiceAccount
metadata:
  name: scheduler-service
---
apiVersion: rbac.authorization.k8s.io/v1
kind: Role
metadata:
  name: leader-election-role
rules:
  - apiGroups: ["coordination.k8s.io"]
    resources: ["leases"]
    verbs: ["get", "create", "update"]
---
apiVersion: rbac.authorization.k8s.io/v1
kind: RoleBinding
metadata:
  name: leader-election-binding
roleRef:
  apiGroup: rbac.authorization.k8s.io
  kind: Role
  name: leader-election-role
subjects:
  - kind: ServiceAccount
    name: scheduler-service
```

**Application Properties**:
```properties
spring.cloud.kubernetes.leader.enabled=true
spring.cloud.kubernetes.leader.role=scheduler-leader
spring.cloud.kubernetes.leader.namespace=default
spring.cloud.kubernetes.leader.lease-duration=15s
spring.cloud.kubernetes.leader.renew-deadline=10s
spring.cloud.kubernetes.leader.retry-period=2s
```

### Option B: ZooKeeper Leader Election

**Dependencies**:
```xml
<dependency>
    <groupId>org.apache.curator</groupId>
    <artifactId>curator-recipes</artifactId>
    <version>5.5.0</version>
</dependency>
```

**Implementation**:
```java
@Component
@Slf4j
public class ZookeeperLeaderScheduler implements LeaderSelectorListener {
    
    private LeaderSelector leaderSelector;
    private final ReportService reportService;
    
    @Autowired
    public ZookeeperLeaderScheduler(CuratorFramework client, ReportService reportService) {
        this.reportService = reportService;
        this.leaderSelector = new LeaderSelector(client, "/scheduler/leader", this);
        this.leaderSelector.autoRequeue(); // Auto re-enter election after leadership
    }
    
    @PostConstruct
    public void start() {
        leaderSelector.start();
    }
    
    @PreDestroy
    public void close() {
        leaderSelector.close();
    }
    
    @Override
    public void takeLeadership(CuratorFramework client) throws Exception {
        log.info("🎉 I am now the leader!");
        
        // Run scheduled job while leader
        ScheduledExecutorService scheduler = Executors.newScheduledThreadPool(1);
        scheduler.scheduleAtFixedRate(() -> {
            try {
                log.info("Executing job as leader");
                reportService.generateAndSendReport();
            } catch (Exception e) {
                log.error("Job execution failed", e);
            }
        }, 0, 24, TimeUnit.HOURS); // Run daily
        
        // Keep leadership until interrupted
        Thread.currentThread().join();
    }
    
    @Override
    public void stateChanged(CuratorFramework client, ConnectionState newState) {
        if (newState == ConnectionState.SUSPENDED || newState == ConnectionState.LOST) {
            log.warn("Connection to ZooKeeper lost, relinquishing leadership");
        }
    }
}
```

### 🎯 Interview Talking Points

**Use this golden line**:

> "Instead of acquiring locks repeatedly, we elect one leader node that is responsible for scheduling, which reduces coordination overhead and improves scalability."

Key points to mention:

1. **Zero runtime overhead**: "Only the leader runs scheduler - no coordination on every job execution"

2. **Automatic failover**: "If leader crashes, remaining nodes detect via lease expiry and elect new leader"

3. **Lease-based**: "Kubernetes uses lease API with periodic heartbeat renewal"

4. **Quorum-based**: "ZooKeeper provides strongly consistent leader election via quorum consensus"

### Pros & Cons

**✅ Pros**:
- Zero coordination overhead per job execution
- Scales to thousands of jobs
- Clear ownership model
- Automatic failover
- Works great with Kubernetes

**❌ Cons**:
- More complex to set up
- Leader can become bottleneck (limited by single node capacity)
- Requires additional infrastructure (ZooKeeper/Kubernetes)
- Leadership transition has brief downtime

---

## 📦 Approach 3: Quartz Clustered Scheduler (Enterprise Standard)

**Best for**: Enterprise systems, complex scheduling needs, persistent job requirements

### The Concept

Multiple nodes share a database → Quartz uses DB row-level locking → ensures single execution → built-in job persistence and retry

### Implementation

**Dependencies** (`pom.xml`):
```xml
<dependency>
    <groupId>org.springframework.boot</groupId>
    <artifactId>spring-boot-starter-quartz</artifactId>
</dependency>
```

**Configuration** (`application.properties`):
```properties
# Quartz Cluster Configuration
spring.quartz.job-store-type=jdbc
spring.quartz.jdbc.initialize-schema=always
spring.quartz.properties.org.quartz.jobStore.isClustered=true
spring.quartz.properties.org.quartz.jobStore.clusterCheckinInterval=5000
spring.quartz.properties.org.quartz.jobStore.driverDelegateClass=org.quartz.impl.jdbcjobstore.PostgreSQLDelegate

# Thread pool
spring.quartz.properties.org.quartz.threadPool.threadCount=10

# Instance configuration
spring.quartz.properties.org.quartz.scheduler.instanceName=ClusteredScheduler
spring.quartz.properties.org.quartz.scheduler.instanceId=AUTO
```

**Job Definition**:
```java
@Component
public class DailyReportJob extends QuartzJobBean {
    
    @Autowired
    private ReportService reportService;
    
    @Override
    protected void executeInternal(JobExecutionContext context) {
        log.info("Executing daily report job on instance: {}", 
                 context.getScheduler().getSchedulerInstanceId());
        
        reportService.generateAndSendReport();
        
        log.info("Job completed successfully");
    }
}
```

**Job Scheduling**:
```java
@Configuration
public class QuartzConfig {
    
    @Bean
    public JobDetail dailyReportJobDetail() {
        return JobBuilder.newJob(DailyReportJob.class)
            .withIdentity("dailyReportJob")
            .storeDurably()
            .build();
    }
    
    @Bean
    public Trigger dailyReportTrigger() {
        return TriggerBuilder.newTrigger()
            .forJob(dailyReportJobDetail())
            .withIdentity("dailyReportTrigger")
            .withSchedule(
                CronScheduleBuilder.cronSchedule("0 0 2 * * ?") // 2:00 AM daily
            )
            .build();
    }
}
```

### How It Works Internally

```sql
-- Quartz creates these tables:
-- QRTZ_LOCKS - Row-level locks for coordination
-- QRTZ_TRIGGERS - Trigger definitions
-- QRTZ_JOB_DETAILS - Job metadata
-- QRTZ_FIRED_TRIGGERS - Currently executing jobs

-- When job triggers, Quartz executes:
BEGIN TRANSACTION;
SELECT * FROM QRTZ_LOCKS WHERE LOCK_NAME = 'TRIGGER_ACCESS' FOR UPDATE;
-- Only one node succeeds in acquiring row lock
INSERT INTO QRTZ_FIRED_TRIGGERS (...);
-- Execute job
DELETE FROM QRTZ_FIRED_TRIGGERS ...;
COMMIT;
```

### 🎯 Interview Talking Points

> "For enterprise scheduling with persistence, retry guarantees, and complex trigger patterns, I prefer Quartz clustered mode. It uses database row-level locking for coordination and provides out-of-the-box features like misfire handling, job persistence, and cluster failure recovery."

Key benefits to mention:

1. **Battle-tested**: "Quartz is the de facto standard for Java scheduling - proven in production for 20+ years"

2. **Rich features**: "Supports complex cron expressions, calendar exclusions, job chains, priority queues"

3. **Persistence**: "Jobs survive application restarts - stored in database"

4. **Misfire handling**: "If job misses schedule (e.g., all nodes down), Quartz can catch up or skip"

### Pros & Cons

**✅ Pros**:
- Production-ready, enterprise-grade
- No external coordination service needed (uses existing DB)
- Rich scheduling features
- Job persistence and history
- Built-in retry and misfire handling
- Works with any database

**❌ Cons**:
- Database becomes coordination bottleneck
- All nodes poll database (less efficient than event-driven)
- Heavier than simple Redis lock
- Requires Quartz-specific configuration and learning curve

---

## 🚀 Approach 4: Queue-Based Scheduling (Modern & Scalable)

**Best for**: High scale, decoupled architecture, event-driven systems, variable workload

### The Concept

Scheduler → Publishes job message to queue → Workers consume and process → Natural single execution via queue semantics

### Architecture

```
┌─────────────────┐
│   Lightweight   │
│    Scheduler    │ (Only enqueues, doesn't process)
└────────┬────────┘
         │
         ↓  Publish
   ┌─────────────┐
   │    Kafka    │
   │   / SQS /   │
   │  RabbitMQ   │
   └──────┬──────┘
          │
          └──→ Consume (automatically distributed)
                 ↓
         ┌───────────────────┐
         │  Worker Pool      │
         │  (Auto-scaling)   │
         │  ┌──┐ ┌──┐ ┌──┐  │
         │  │W1│ │W2│ │W3│  │
         │  └──┘ └──┘ └──┘  │
         └───────────────────┘
```

### Option A: Kafka-Based Implementation

**Producer (Scheduler)**:
```java
@Component
@Slf4j
public class JobSchedulerProducer {
    
    @Autowired
    private KafkaTemplate<String, JobMessage> kafkaTemplate;
    
    private static final String TOPIC = "scheduled-jobs";
    
    @Scheduled(cron = "0 0 2 * * *") // 2:00 AM daily
    public void scheduleDaily Report() {
        JobMessage message = JobMessage.builder()
            .jobId(UUID.randomUUID().toString())
            .jobType("DAILY_REPORT")
            .scheduledTime(Instant.now())
            .build();
        
        log.info("Publishing job to Kafka: {}", message.getJobId());
        kafkaTemplate.send(TOPIC, message.getJobId(), message);
    }
}
```

**Consumer (Worker)**:
```java
@Component
@Slf4j
public class JobWorkerConsumer {
    
    @Autowired
    private ReportService reportService;
    
    @KafkaListener(
        topics = "scheduled-jobs",
        groupId = "job-workers",
        concurrency = "3" // 3 parallel consumers
    )
    public void processJob(JobMessage message) {
        log.info("Processing job: {} on instance: {}", 
                 message.getJobId(), 
                 InetAddress.getLocalHost().getHostName());
        
        try {
            reportService.generateAndSendReport();
            log.info("Job completed: {}", message.getJobId());
        } catch (Exception e) {
            log.error("Job failed: {}", message.getJobId(), e);
            throw e; // Kafka will retry based on configuration
        }
    }
}

@Data
@Builder
class JobMessage {
    private String jobId;
    private String jobType;
    private Instant scheduledTime;
}
```

### Option B: AWS SQS Implementation

**Producer**:
```java
@Component
@Slf4j
public class SQSJobScheduler {
    
    @Autowired
    private SqsTemplate sqsTemplate;
    
    @Scheduled(cron = "0 0 2 * * *")
    public void scheduleDailyReport() {
        JobMessage message = JobMessage.builder()
            .jobId(UUID.randomUUID().toString())
            .jobType("DAILY_REPORT")
            .build();
        
        sqsTemplate.send(to -> to
            .queue("scheduled-jobs-queue")
            .payload(message)
            .header("jobId", message.getJobId())
        );
        
        log.info("Job published to SQS: {}", message.getJobId());
    }
}
```

**Consumer**:
```java
@Component
@Slf4f
public class SQSJobWorker {
    
    @Autowired
    private ReportService reportService;
    
    @SqsListener("scheduled-jobs-queue")
    public void processJob(JobMessage message) {
        log.info("Processing job from SQS: {}", message.getJobId());
        reportService.generateAndSendReport();
    }
}
```

### 🎯 Interview Talking Points (Very Impressive!)

**Golden statement**:

> "Instead of scheduling execution, we schedule job creation and let workers consume asynchronously. This decouples scheduling from execution, enabling independent scaling, built-in retry, backpressure handling, and eliminates coordination complexity."

Key advantages to emphasize:

1. **Decoupling**: "Scheduler is lightweight - just publishes messages. Heavy processing happens in workers."

2. **Auto-scaling**: "Workers can scale independently based on queue depth - if 1000 jobs queued, scale to 50 workers automatically."

3. **Natural deduplication**: "Queue consumers guarantee single delivery per partition/consumer group."

4. **Retry built-in**: "Failed messages automatically retry with exponential backoff."

5. **Observability**: "Queue depth metrics show backlog - easy to monitor and alert."

### Pros & Cons

**✅ Pros**:
- Highest scalability (horizontal scaling of workers)
- Decoupled architecture
- Built-in retry and dead-letter queues
- Backpressure handling
- Easy to add new job types
- Natural observability (queue metrics)
- Works great for variable workloads

**❌ Cons**:
- Requires message broker infrastructure (Kafka/SQS)
- Eventually consistent
- Slight delay between schedule and execution
- Complexity of message-driven architecture
- Need to handle duplicate messages (at-least-once guarantee)

---

## ☸️ Approach 5: Kubernetes CronJob (Cloud-Native Standard)

**Best for**: Cloud-native systems, containerized workloads, Kubernetes platforms

### The Concept

Kubernetes manages job execution → Spawns dedicated pod → Runs job → Terminates pod → Built-in retry and history

### Implementation

**CronJob Definition** (`k8s/daily-report-cronjob.yaml`):
```yaml
apiVersion: batch/v1
kind: CronJob
metadata:
  name: daily-report-job
  namespace: production
spec:
  # Schedule in UTC
  schedule: "0 2 * * *"  # 2:00 AM daily
  
  # Timezone (Kubernetes 1.25+)
  timeZone: "UTC"
  
  # Concurrency policy - prevent overlapping runs
  concurrencyPolicy: Forbid  # Options: Allow, Forbid, Replace
  
  # Keep last 3 successful and 1 failed job for debugging
  successfulJobsHistoryLimit: 3
  failedJobsHistoryLimit: 1
  
  # Job template
  jobTemplate:
    spec:
      # Retry on failure
      backoffLimit: 3
      
      # Max time to complete (2 hours)
      activeDeadlineSeconds: 7200
      
      template:
        metadata:
          labels:
            app: daily-report
            job-type: scheduled
        spec:
          restartPolicy: OnFailure
          
          containers:
          - name: report-generator
            image: mycompany/report-service:1.0.0
            imagePullPolicy: IfNotPresent
            
            command: ["java"]
            args: [
              "-jar",
              "/app/report-service.jar",
              "--job.type=daily-report",
              "--spring.profiles.active=production"
            ]
            
            env:
            - name: DB_HOST
              valueFrom:
                secretKeyRef:
                  name: db-credentials
                  key: host
            
            resources:
            requests:
                memory: "512Mi"
                cpu: "500m"
              limits:
                memory: "1Gi"
                cpu: "1000m"
          
          # Service account for accessing other resources
          serviceAccountName: report-service
```

**Application Code** (simpler - no scheduling needed):
```java
@SpringBootApplication
public class ReportJobApplication implements CommandLineRunner {
    
    @Autowired
    private ReportService reportService;
    
    public static void main(String[] args) {
        SpringApplication.run(ReportJobApplication.class, args);
    }
    
    @Override
    public void run(String... args) throws Exception {
        log.info("Starting scheduled job execution");
        reportService.generateAndSendReport();
        log.info("Job completed successfully");
        System.exit(0); // Exit after completion
    }
}
```

### Advanced: Handling Long-Running Jobs

```yaml
# For jobs that might overlap, use Replace strategy
apiVersion: batch/v1
kind: CronJob
metadata:
  name: long-running-job
spec:
  schedule: "0 */1 * * *"  # Every hour
  concurrencyPolicy: Replace  # Kill old job if still running
  
  # Suspend if needed (for maintenance)
  suspend: false
  
  jobTemplate:
    spec:
      parallelism: 1  # Run single pod
      completions: 1  # Consider success after 1 completion
      
      template:
        spec:
          containers:
          - name: worker
            image: mycompany/worker:latest
            
            # Graceful shutdown handling
            lifecycle:
              preStop:
                exec:
                  command: ["/bin/sh", "-c", "sleep 30"]
```

### 🎯 Interview Talking Points

**Strategic statement**:

> "In cloud-native systems, I prefer Kubernetes CronJobs instead of application-level scheduling. Kubernetes handles scheduling, execution, retry, and cleanup. The job itself is stateless - just runs and exits - which simplifies code and enables independent versioning and rollback."

Key benefits:

1. **Infrastructure-level**: "Scheduling is platform concern, not application concern"

2. **Isolation**: "Each execution runs in fresh pod - no state contamination"

3. **Resource management**: "Can specify CPU/memory per job, different from main service"

4. **History**: "Kubernetes keeps job history - can see logs of previous runs"

5. **Easy rollback**: "Can run different job versions without redeploying main service"

### Pros & Cons

**✅ Pros**:
- Perfect for Kubernetes environments
- Complete isolation per execution
- Built-in retry, history, monitoring
- Simpler application code (no scheduling logic)
- Independent resource allocation
- Easy to version and rollback jobs
- Natural fit for cloud-native architecture

**❌ Cons**:
- Requires Kubernetes
- Cold start overhead (pod creation ~5-10 seconds)
- Limited to cron expressions (no complex triggers)
- Not suitable for very frequent jobs (every second)
- Versioning jobs separately from main app adds complexity

---

## 📊 Comparison Matrix

| Aspect | Redis Lock | Leader Election | Quartz | Queue-Based | K8s CronJob |
|--------|-----------|----------------|---------|-------------|-------------|
| **Setup Complexity** | ⭐ Low | ⭐⭐⭐ Medium | ⭐⭐ Low-Medium | ⭐⭐⭐ Medium | ⭐⭐ Low (if K8s exists) |
| **Coordination Overhead** | ⭐⭐⭐ Every execution | ⭐⭐⭐⭐⭐ Zero | ⭐⭐ DB polling | ⭐⭐⭐⭐ Low | ⭐⭐⭐⭐⭐ Zero |
| **Scalability** | ⭐⭐ Moderate | ⭐⭐⭐⭐⭐ Excellent | ⭐⭐⭐ Good | ⭐⭐⭐⭐⭐ Excellent | ⭐⭐⭐⭐ Good |
| **External Dependencies** | Redis | K8s/ZK/etcd | Database | Kafka/SQS | Kubernetes |
| **Failure Recovery** | Auto (TTL) | Auto (election) | Auto (cluster) | Auto (retry) | Auto (K8s) |
| **Best For** | Simple systems | Many jobs | Enterprise | High scale | Cloud-native |

## ✅ Quick Decision Guide

**Use Redis Lock when**:
- Small/medium scale (5-20 instances)
- Infrequent jobs (hourly/daily)
- Already using Redis
- Simple requirements

**Use Leader Election when**:
- Large clusters (50+ instances)
- Many scheduled jobs
- Running on Kubernetes
- Need minimal overhead

**Use Quartz when**:
- Enterprise environment
- Complex scheduling needs (calendars, job chains)
- Need job persistence and history
- Using traditional architecture

**Use Queue-Based when**:
- Very high scale
- Variable workload
- Need independent worker scaling
- Event-driven architecture

**Use Kubernetes CronJob when**:
- Running on Kubernetes
- Jobs are containerized
- Want isolation per execution
- Cloud-native approach

---

**Next**: [03-Failure-Handling-and-Idempotency.md](03-Failure-Handling-and-Idempotency.md) - Master failure scenarios and idempotent design

**Previous**: [01-Core-Problem-and-Architecture.md](01-Core-Problem-and-Architecture.md)
