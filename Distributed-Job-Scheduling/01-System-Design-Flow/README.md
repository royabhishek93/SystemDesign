# 🎯 System Design Flow: Real-World Job Scheduling

**Purpose**: Learn how companies like Netflix, Google, and Uber design distributed job schedulers step-by-step

---

## 📋 Table of Contents

1. [Netflix-Style Job Scheduling](#netflix-style-job-scheduling)
2. [Google-Style Distributed Cron](#google-style-distributed-cron)
3. [Uber's Time-Based Job Processor](#ubers-time-based-job-processor)
4. [Generic Flow: Job Creation → Execution](#generic-flow)
5. [Decision Points in Design](#decision-points-in-design)

---

## 🎬 Netflix-Style Job Scheduling

### Business Context
Netflix needs to process **millions of video encoding jobs** daily:
- User uploads video → job created
- Video needs encoding in multiple resolutions: 4K, 1080p, 720p, 480p
- Each resolution is a separate job
- Jobs must execute exactly once (duplicate encoding wastes $$$)

### High-Level Flow

```
┌──────────────┐
│ Upload API   │  User uploads raw video
│              │
└──────┬───────┘
       │
       ▼
┌──────────────────┐
│ Job Creator      │  Creates encoding jobs (1 video → 4 jobs)
│ Service          │  Job metadata: videoId, resolution, priority
└──────┬───────────┘
       │
       │ Publishes to
       ▼
┌──────────────────┐
│ Kafka Topic      │  Topic: "encoding-jobs"
│ "encoding-jobs"  │  Partitioned by videoId
└──────┬───────────┘
       │
       │ Consumed by
       ▼
┌──────────────────────────────────────┐
│ Worker Pool (Auto-scaling)           │
│                                      │
│  Worker-1  Worker-2  ...  Worker-N  │
│  [Busy]    [Idle]          [Busy]   │
└──────┬───────────────────────────────┘
       │
       │ Execute
       ▼
┌──────────────────┐
│ Encoding Engine  │  FFmpeg, AWS MediaConvert
│                  │
└──────┬───────────┘
       │
       │ Store result
       ▼
┌──────────────────┐
│ S3 Bucket        │  Encoded videos
│ + Database       │  Job status: COMPLETED
└──────────────────┘
```

### Step-by-Step Execution

#### Step 1: Job Creation
```java
@Service
public class EncodingJobCreator {
    
    @Autowired
    private KafkaTemplate<String, EncodingJob> kafkaTemplate;
    
    public void createEncodingJobs(String videoId, String rawVideoUrl) {
        List<String> resolutions = List.of("4K", "1080p", "720p", "480p");
        
        for (String resolution : resolutions) {
            EncodingJob job = EncodingJob.builder()
                .jobId(UUID.randomUUID().toString())
                .videoId(videoId)
                .resolution(resolution)
                .inputUrl(rawVideoUrl)
                .status("PENDING")
                .createdAt(Instant.now())
                .priority(calculatePriority(resolution))
                .build();
            
            // Publish to Kafka (partition by videoId for ordering)
            kafkaTemplate.send("encoding-jobs", videoId, job);
            
            log.info("Created encoding job: {}", job.getJobId());
        }
    }
    
    private int calculatePriority(String resolution) {
        // Higher paying customers get 4K first
        return switch (resolution) {
            case "4K" -> 1;
            case "1080p" -> 2;
            case "720p" -> 3;
            case "480p" -> 4;
            default -> 5;
        };
    }
}
```

#### Step 2: Worker Consumes Job
```java
@Service
public class EncodingWorker {
    
    @Autowired
    private EncodingService encodingService;
    
    @Autowired
    private JobRepository jobRepository;
    
    @KafkaListener(
        topics = "encoding-jobs",
        groupId = "encoding-workers",
        concurrency = "10"  // 10 parallel consumers
    )
    public void processEncodingJob(EncodingJob job) {
        log.info("Worker {} picked up job: {}", 
            Thread.currentThread().getName(), job.getJobId());
        
        try {
            // Mark as IN_PROGRESS (idempotency check)
            boolean claimed = jobRepository.claimJob(job.getJobId(), "IN_PROGRESS");
            if (!claimed) {
                log.warn("Job already claimed by another worker");
                return;
            }
            
            // Execute encoding
            String outputUrl = encodingService.encode(
                job.getInputUrl(), 
                job.getResolution()
            );
            
            // Update job status
            jobRepository.updateJob(
                job.getJobId(), 
                "COMPLETED", 
                outputUrl
            );
            
            log.info("Successfully encoded: {}", job.getJobId());
            
        } catch (Exception e) {
            log.error("Encoding failed for job: {}", job.getJobId(), e);
            
            // Retry logic (exponential backoff)
            jobRepository.updateJob(
                job.getJobId(), 
                "FAILED", 
                null, 
                job.getRetryCount() + 1
            );
        }
    }
}
```

#### Step 3: Idempotency & Retry
```java
@Repository
public class JobRepository {
    
    @Autowired
    private JdbcTemplate jdbcTemplate;
    
    public boolean claimJob(String jobId, String newStatus) {
        String sql = """
            UPDATE encoding_jobs
            SET status = ?, 
                worker_id = ?,
                updated_at = NOW()
            WHERE job_id = ? 
              AND status = 'PENDING'
            """;
        
        int updated = jdbcTemplate.update(
            sql, 
            newStatus, 
            getWorkerId(), 
            jobId
        );
        
        // Returns true only if status was PENDING (not already claimed)
        return updated == 1;
    }
    
    public void updateJob(String jobId, String status, String outputUrl) {
        updateJob(jobId, status, outputUrl, 0);
    }
    
    public void updateJob(String jobId, String status, 
                          String outputUrl, int retryCount) {
        String sql = """
            UPDATE encoding_jobs
            SET status = ?, 
                output_url = ?,
                retry_count = ?,
                updated_at = NOW()
            WHERE job_id = ?
            """;
        
        jdbcTemplate.update(sql, status, outputUrl, retryCount, jobId);
    }
    
    private String getWorkerId() {
        // Unique worker identifier (pod name + thread)
        return System.getenv("HOSTNAME") + "-" + 
               Thread.currentThread().getId();
    }
}
```

### Key Design Decisions

#### 1. Why Kafka?
- **High throughput**: Can handle millions of jobs/day
- **Partitioning**: Jobs for same video stay in order
- **Consumer groups**: Auto-distributes work across workers
- **Durability**: Jobs persist even if workers crash

#### 2. Why Database for Status?
- **Source of truth**: Kafka messages are ephemeral, DB persists
- **Idempotency**: Prevents duplicate execution via status check
- **Monitoring**: Query job status, retry counts, failure rates
- **Debugging**: Full audit trail of job lifecycle

#### 3. Auto-Scaling Workers
```yaml
# Kubernetes HorizontalPodAutoscaler
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: encoding-worker-hpa
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: encoding-worker
  minReplicas: 10
  maxReplicas: 100
  metrics:
  - type: External
    external:
      metric:
        name: kafka_consumer_lag
        selector:
          matchLabels:
            topic: encoding-jobs
      target:
        type: AverageValue
        averageValue: "5000"  # Scale up if lag > 5000 messages
```

**Scaling Behavior**:
- **Low load** (midnight): 10 workers
- **Peak hours** (evening uploads): 80-100 workers
- **Cost savings**: Only pay for what you use
- **SLA maintained**: Jobs complete within 5 minutes

---

## 🌐 Google-Style Distributed Cron

### Business Context
Google needs to run **scheduled maintenance tasks** across thousands of services:
- Clear cache every hour
- Send metrics every 5 minutes
- Garbage collection every day
- Must run in **multiple data centers** (geo-distributed)
- Must handle **zone failures** gracefully

### Architecture: Leader-Follower Pattern

```
┌─────────────────────────────────────────────────────────────┐
│                    Centralized Control Plane                │
│                                                             │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  Leader Election (etcd/ZooKeeper)                    │  │
│  │                                                       │  │
│  │  Controller-1  Controller-2  Controller-3            │  │
│  │  [LEADER ✓]    [Standby]     [Standby]               │  │
│  └──────────────────────────────────────────────────────┘  │
│                            │                               │
│                            │ Only leader schedules jobs    │
│                            ▼                               │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  Job Scheduler (Quartz/Internal)                     │  │
│  │  - Load cron definitions from config                 │  │
│  │  - Enqueue jobs at scheduled time                    │  │
│  └──────────────────────────────────────────────────────┘  │
└─────────────────┬───────────────────────────────────────────┘
                  │
                  │ Dispatch to
                  ▼
┌─────────────────────────────────────────────────────────────┐
│                    Distributed Data Plane                   │
│                                                             │
│  Data Center US-EAST      Data Center US-WEST              │
│  ┌──────────────────┐    ┌──────────────────┐              │
│  │ Worker Pool      │    │ Worker Pool      │              │
│  │ - 100 replicas   │    │ - 100 replicas   │              │
│  └──────────────────┘    └──────────────────┘              │
│                                                             │
│  Data Center EU           Data Center ASIA                 │
│  ┌──────────────────┐    ┌──────────────────┐              │
│  │ Worker Pool      │    │ Worker Pool      │              │
│  └──────────────────┘    └──────────────────┘              │
└─────────────────────────────────────────────────────────────┘
```

### Flow: Leader-Driven Scheduling

#### Step 1: Leader Election
```java
@Service
public class CronController {
    
    @Autowired
    private LeaderElectionService leaderElection;
    
    @Autowired
    private JobScheduler scheduler;
    
    @PostConstruct
    public void init() {
        leaderElection.runForLeader(
            this::onBecomeLeader,
            this::onLoseLeadership
        );
    }
    
    private void onBecomeLeader() {
        log.info("🎖️  I am the LEADER! Starting scheduler...");
        
        // Load all cron jobs from config
        List<CronJob> jobs = loadCronJobs();
        
        // Schedule each job
        for (CronJob job : jobs) {
            scheduler.schedule(job.getCronExpression(), () -> {
                executeJob(job);
            });
        }
    }
    
    private void onLoseLeadership() {
        log.warn("Lost leadership, shutting down scheduler");
        scheduler.shutdown();
    }
    
    private void executeJob(CronJob job) {
        log.info("Executing scheduled job: {}", job.getName());
        
        // Publish job to all data centers
        for (String dataCenter : job.getTargetDataCenters()) {
            publishJobToQueue(dataCenter, job);
        }
    }
}
```

#### Step 2: Leader Election with etcd
```java
@Service
public class LeaderElectionService {
    
    private final Client etcdClient;
    private final String leasePath = "/cron/leader";
    private volatile boolean isLeader = false;
    
    public void runForLeader(Runnable onBecome, Runnable onLose) {
        ExecutorService executor = Executors.newSingleThreadExecutor();
        
        executor.submit(() -> {
            while (true) {
                try {
                    // Try to acquire lease
                    long leaseId = etcdClient.getLeaseClient()
                        .grant(10) // 10 second TTL
                        .get()
                        .getID();
                    
                    // Try to set /cron/leader key with lease
                    PutResponse response = etcdClient.getKVClient()
                        .put(
                            ByteSequence.from(leasePath, UTF_8),
                            ByteSequence.from(getInstanceId(), UTF_8),
                            PutOption.newBuilder()
                                .withLeaseId(leaseId)
                                .build()
                        )
                        .get();
                    
                    if (!isLeader) {
                        isLeader = true;
                        onBecome.run();
                    }
                    
                    // Keep renewing lease
                    etcdClient.getLeaseClient()
                        .keepAlive(leaseId, Observers.observer());
                    
                    Thread.sleep(5000); // Renew every 5 seconds
                    
                } catch (Exception e) {
                    if (isLeader) {
                        isLeader = false;
                        onLose.run();
                    }
                    log.error("Leader election failed, retrying...", e);
                    Thread.sleep(2000);
                }
            }
        });
    }
    
    private String getInstanceId() {
        return System.getenv("HOSTNAME");
    }
}
```

#### Step 3: Workers Execute Jobs
```java
@Service
public class GlobalWorker {
    
    @KafkaListener(topics = "cron-jobs-${datacenter.name}")
    public void executeJob(CronJob job) {
        String datacenter = System.getenv("DATACENTER");
        log.info("[{}] Executing job: {}", datacenter, job.getName());
        
        try {
            switch (job.getType()) {
                case "CACHE_CLEAR":
                    cacheService.clearAll();
                    break;
                case "METRICS_EXPORT":
                    metricsService.exportToMonitoring();
                    break;
                case "GARBAGE_COLLECTION":
                    gcService.triggerGC();
                    break;
                default:
                    log.warn("Unknown job type: {}", job.getType());
            }
            
            reportSuccess(job, datacenter);
            
        } catch (Exception e) {
            log.error("Job execution failed", e);
            reportFailure(job, datacenter, e);
        }
    }
}
```

### Key Design Decisions

#### 1. Why Leader-Follower?
- **Single source of truth**: Only one controller schedules jobs
- **No duplicate execution**: Only leader triggers cron
- **Fast failover**: Followers ready to take over instantly
- **Consistency**: All data centers get same jobs

#### 2. Why Separate Control & Data Planes?
- **Scalability**: Add workers without affecting scheduling
- **Isolation**: Worker failures don't break scheduling
- **Geo-distribution**: Workers in each region, controller centralized
- **Cost**: Small control plane (3 replicas), large data plane (1000s)

#### 3. Handling Zone Failures
```
Scenario: US-EAST data center goes down

Before:
  Leader (US-EAST) ──┬──> Workers (US-EAST) ❌ DOWN
                     ├──> Workers (US-WEST) ✓
                     ├──> Workers (EU) ✓
                     └──> Workers (ASIA) ✓

After (Leader Fails):
  Leader (US-WEST) ───┬──> Workers (US-WEST) ✓
                      ├──> Workers (EU) ✓
                      └──> Workers (ASIA) ✓
  
  New leader elected in < 2 seconds
  Jobs continue without interruption
```

---

## 🚗 Uber's Time-Based Job Processor

### Business Context
Uber processes **time-sensitive jobs**:
- Driver payouts every Monday 9 AM
- Weekly promotional emails
- Surge pricing recalculation every 30 seconds
- Must handle **100M+ jobs per day**
- Jobs have **deadlines** (must complete within 5 minutes)

### Architecture: Priority Queue + Worker Pool

```
┌────────────────────────────────────────────────────────────┐
│                    Job Submission Layer                    │
│                                                            │
│  Payment Service  Promo Service  Pricing Service          │
│       │                │                │                  │
│       └────────────────┴────────────────┘                  │
│                        │                                   │
│                        ▼                                   │
│               ┌──────────────────┐                         │
│               │ Job API Gateway  │                         │
│               │ - Validation     │                         │
│               │ - Rate limiting  │                         │
│               └────────┬─────────┘                         │
└─────────────────────────┼─────────────────────────────────┘
                          │
                          ▼
┌────────────────────────────────────────────────────────────┐
│                  Job Scheduling Layer                      │
│                                                            │
│              ┌──────────────────────┐                      │
│              │  Time-Wheel Scheduler │                      │
│              │  - Buckets by minute  │                      │
│              │  - Scan & dispatch    │                      │
│              └──────────┬───────────┘                      │
│                         │                                  │
│                         ▼                                  │
│              ┌──────────────────────┐                      │
│              │  Priority Queue      │                      │
│              │  (RabbitMQ Priority) │                      │
│              │                      │                      │
│              │  P1 │ P2 │ P3 │ P4  │                      │
│              └──────────┬───────────┘                      │
└──────────────────────────┼─────────────────────────────────┘
                           │
                           ▼
┌────────────────────────────────────────────────────────────┐
│                   Execution Layer                          │
│                                                            │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐    │
│  │ Worker Pool  │  │ Worker Pool  │  │ Worker Pool  │    │
│  │ (Priority 1) │  │ (Priority 2) │  │ (Priority 3) │    │
│  │ 100 workers  │  │ 50 workers   │  │ 20 workers   │    │
│  └──────────────┘  └──────────────┘  └──────────────┘    │
│                                                            │
│            Execute → Update Status → Metrics               │
└────────────────────────────────────────────────────────────┘
```

### Flow: Time-Wheel Scheduling

#### Step 1: Submit Job with Execution Time
```java
@RestController
@RequestMapping("/api/jobs")
public class JobSubmissionController {
    
    @Autowired
    private JobSchedulingService scheduler;
    
    @PostMapping("/schedule")
    public ResponseEntity<JobResponse> scheduleJob(
            @RequestBody JobRequest request) {
        
        // Validate execution time
        if (request.getExecuteAt().isBefore(Instant.now())) {
            return ResponseEntity.badRequest()
                .body(new JobResponse("Execution time in past"));
        }
        
        // Create job
        Job job = Job.builder()
            .jobId(UUID.randomUUID().toString())
            .type(request.getType())
            .priority(request.getPriority())
            .executeAt(request.getExecuteAt())
            .payload(request.getPayload())
            .status(JobStatus.SCHEDULED)
            .createdAt(Instant.now())
            .build();
        
        // Save to DB
        jobRepository.save(job);
        
        // Schedule in time-wheel
        scheduler.schedule(job);
        
        return ResponseEntity.ok(new JobResponse(job.getJobId()));
    }
}
```

#### Step 2: Time-Wheel Scans & Dispatches
```java
@Service
public class TimeWheelScheduler {
    
    // Time wheel: Map of minute → List of jobs
    private final Map<Integer, List<Job>> timeWheel = new ConcurrentHashMap<>();
    
    @Autowired
    private RabbitTemplate rabbitTemplate;
    
    @Scheduled(fixedRate = 1000) // Every second
    public void scanAndDispatch() {
        int currentMinute = getCurrentMinuteBucket();
        
        List<Job> dueJobs = timeWheel.getOrDefault(currentMinute, List.of());
        
        for (Job job : dueJobs) {
            if (job.getExecuteAt().isBefore(Instant.now())) {
                dispatchJob(job);
                dueJobs.remove(job);
            }
        }
    }
    
    private void dispatchJob(Job job) {
        // Route to priority queue
        String queueName = "jobs.priority." + job.getPriority();
        
        rabbitTemplate.convertAndSend(
            queueName, 
            job,
            message -> {
                message.getMessageProperties()
                    .setPriority(job.getPriority());
                return message;
            }
        );
        
        log.info("Dispatched job {} to queue {}", 
            job.getJobId(), queueName);
    }
    
    public void schedule(Job job) {
        int bucket = calculateBucket(job.getExecuteAt());
        timeWheel.computeIfAbsent(bucket, k -> new CopyOnWriteArrayList<>())
            .add(job);
    }
    
    private int calculateBucket(Instant executeAt) {
        // Bucket = minute of day (0-1439)
        return (int) (executeAt.toEpochMilli() / 60000) % 1440;
    }
    
    private int getCurrentMinuteBucket() {
        return (int) (Instant.now().toEpochMilli() / 60000) % 1440;
    }
}
```

#### Step 3: Priority-Based Execution
```java
@Service
public class PriorityWorker {
    
    @Autowired
    private JobExecutor executor;
    
    // High priority queue (P1): Driver payouts
    @RabbitListener(
        queues = "jobs.priority.1",
        concurrency = "100" // 100 parallel workers
    )
    public void processHighPriority(Job job) {
        executeWithDeadline(job, Duration.ofMinutes(1));
    }
    
    // Medium priority queue (P2): Promotional emails
    @RabbitListener(
        queues = "jobs.priority.2",
        concurrency = "50"
    )
    public void processMediumPriority(Job job) {
        executeWithDeadline(job, Duration.ofMinutes(5));
    }
    
    // Low priority queue (P3): Analytics jobs
    @RabbitListener(
        queues = "jobs.priority.3",
        concurrency = "20"
    )
    public void processLowPriority(Job job) {
        executeWithDeadline(job, Duration.ofMinutes(30));
    }
    
    private void executeWithDeadline(Job job, Duration deadline) {
        Instant start = Instant.now();
        
        try {
            // Execute with timeout
            CompletableFuture<Void> future = CompletableFuture.runAsync(
                () -> executor.execute(job)
            );
            
            future.get(deadline.toMillis(), TimeUnit.MILLISECONDS);
            
            Duration elapsed = Duration.between(start, Instant.now());
            log.info("Job {} completed in {}", job.getJobId(), elapsed);
            
            jobRepository.updateStatus(job.getJobId(), JobStatus.COMPLETED);
            
        } catch (TimeoutException e) {
            log.error("Job {} exceeded deadline of {}", 
                job.getJobId(), deadline);
            jobRepository.updateStatus(job.getJobId(), JobStatus.FAILED);
            
        } catch (Exception e) {
            log.error("Job {} execution failed", job.getJobId(), e);
            jobRepository.updateStatus(job.getJobId(), JobStatus.FAILED);
        }
    }
}
```

### Key Design Decisions

#### 1. Why Time-Wheel?
- **Efficiency**: O(1) insertion and dispatch
- **Scalability**: Can handle millions of jobs
- **Precision**: Minute-level accuracy sufficient
- **Memory**: Fixed size (1440 buckets for 24 hours)

#### 2. Why Priority Queues?
- **Business value**: Critical jobs (payouts) complete first
- **Resource allocation**: More workers for high priority
- **SLA guarantees**: P1 jobs within 1 minute, P3 within 30 minutes
- **Fairness**: Low priority jobs still execute (no starvation)

#### 3. Deadline Enforcement
```
Scenario: Payout job must complete in 1 minute

Without deadline:
  Job starts → DB connection hangs → 30 mins later still running ❌
  
With deadline:
  Job starts → 1 minute timeout → Kill job → Retry ✓
  Prevents resource exhaustion
```

---

## 🔄 Generic Flow: Job Creation → Execution

### Universal Pattern (All Systems)

```
┌─────────────┐
│  1. CREATE  │  Business logic creates job
│             │  - Generate unique jobId
│             │  - Set execution time
│             │  - Store in database
└──────┬──────┘
       │
       ▼
┌─────────────┐
│  2. QUEUE   │  Job placed in queue/scheduler
│             │  - Waiting for execution time
│             │  - May be delayed for future
└──────┬──────┘
       │
       ▼
┌─────────────┐
│ 3. DISPATCH │  Scheduler triggers execution
│             │  - Check if time reached
│             │  - Send to worker pool
│             │  - Mark as IN_PROGRESS
└──────┬──────┘
       │
       ▼
┌─────────────┐
│ 4. CLAIM    │  Worker claims job (idempotency)
│             │  - CAS update: PENDING → IN_PROGRESS
│             │  - Only one worker succeeds
└──────┬──────┘
       │
       ▼
┌─────────────┐
│ 5. EXECUTE  │  Business logic runs
│             │  - API calls, DB updates, etc.
│             │  - May take seconds to hours
└──────┬──────┘
       │
       ▼
┌─────────────┐
│ 6. COMPLETE │  Update final status
│             │  - Mark COMPLETED or FAILED
│             │  - Store result/error
│             │  - Trigger retry if needed
└─────────────┘
```

### Code: Complete Flow
```java
// 1. CREATE
public String createPayoutJob(String driverId, BigDecimal amount) {
    PayoutJob job = PayoutJob.builder()
        .jobId(UUID.randomUUID().toString())
        .driverId(driverId)
        .amount(amount)
        .executeAt(nextMonday9AM())
        .status(JobStatus.PENDING)
        .build();
    
    jobRepository.save(job);
    return job.getJobId();
}

// 2. QUEUE (Scheduler decides when to dispatch)
@Scheduled(fixedRate = 60000) // Every minute
public void dispatchDueJobs() {
    List<PayoutJob> dueJobs = jobRepository.findDueJobs(Instant.now());
    
    for (PayoutJob job : dueJobs) {
        kafkaTemplate.send("payout-jobs", job);
    }
}

// 3. DISPATCH + 4. CLAIM + 5. EXECUTE + 6. COMPLETE
@KafkaListener(topics = "payout-jobs")
public void processPayoutJob(PayoutJob job) {
    // 4. CLAIM (idempotency via CAS)
    boolean claimed = jobRepository.claimJob(
        job.getJobId(), 
        JobStatus.PENDING, 
        JobStatus.IN_PROGRESS
    );
    
    if (!claimed) {
        log.warn("Job already being processed");
        return;
    }
    
    // 5. EXECUTE
    try {
        paymentGateway.transfer(job.getDriverId(), job.getAmount());
        
        // 6. COMPLETE
        jobRepository.updateStatus(
            job.getJobId(), 
            JobStatus.COMPLETED
        );
        
    } catch (Exception e) {
        jobRepository.updateStatus(
            job.getJobId(), 
            JobStatus.FAILED
        );
        
        // Retry logic
        if (job.getRetryCount() < 3) {
            job.setRetryCount(job.getRetryCount() + 1);
            job.setExecuteAt(Instant.now().plus(5, ChronoUnit.MINUTES));
            kafkaTemplate.send("payout-jobs", job);
        }
    }
}
```

---

## 🎯 Decision Points in Design

### Question 1: Immediate vs Delayed Execution?

| Immediate (seconds) | Delayed (minutes/hours) |
|---------------------|-------------------------|
| Kafka/SQS direct | Time-wheel scheduler |
| Simple queue | Database + cron scan |
| Low latency | High throughput |
| Example: Video encoding | Example: Weekly reports |

### Question 2: Single Instance vs Distributed?

| Single Instance | Distributed |
|-----------------|-------------|
| Cron job | Redis lock / Leader election |
| Simple deployment | Complex coordination |
| Single point of failure | High availability |
| Example: Personal blog | Example: Production service |

### Question 3: Push vs Pull?

| Push (Queue) | Pull (Polling) |
|--------------|----------------|
| Workers listen to queue | Workers poll database |
| Event-driven | Resource intensive |
| Real-time | Batch processing |
| Example: Kafka consumer | Example: Cron job |

### Question 4: Priority vs FIFO?

| Priority Queue | FIFO Queue |
|----------------|------------|
| High-value jobs first | Fair ordering |
| Complex routing | Simple implementation |
| SLA guarantees | Best-effort |
| Example: Payment > Analytics | Example: Log processing |

### Decision Tree
```
Start: Need to schedule jobs?
  │
  ├─ Single instance? → Use @Scheduled annotation
  │
  ├─ Multiple instances?
  │   │
  │   ├─ Low volume (< 1000/day)? → Redis distributed lock
  │   │
  │   ├─ Medium volume (< 100k/day)?
  │   │   ├─ Complex cron? → Quartz cluster
  │   │   └─ Simple schedule? → Kubernetes CronJob
  │   │
  │   └─ High volume (> 100k/day)?
  │       ├─ Immediate execution? → Kafka/SQS queue
  │       └─ Delayed execution? → Time-wheel + priority queue
  │
  └─ Ultra-scale (> 10M/day)? 
      → Leader-follower + Kafka + Worker pool + Auto-scaling
```

---

## 📊 Comparison Table

| Company | Approach | Scale | Latency | Complexity |
|---------|----------|-------|---------|------------|
| Netflix | Kafka queue | 10M jobs/day | < 1 minute | Medium |
| Google | Leader-follower | 1B tasks/day | < 10 seconds | High |
| Uber | Time-wheel + priority | 100M jobs/day | < 5 minutes | High |
| Airbnb | Quartz cluster | 100k jobs/day | < 1 minute | Low |
| Stripe | Redis lock | 10k jobs/day | < 30 seconds | Low |

---

**Next**: [Component Roles →](../02-Component-Roles/)
