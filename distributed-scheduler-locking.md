# Distributed Scheduler Locking - Complete Interview Guide

> **Interview Level**: 5+ Years | Spring Boot + Microservices + Cloud (AWS/K8s)  
> **Last Updated**: February 12, 2026

---

## 📋 Table of Contents

1. [Problem Statement](#problem-statement)
2. [Solution 1: Pessimistic Lock](#solution-1-pessimistic-lock-select-for-update)
3. [Solution 2: SKIP LOCKED](#solution-2-for-update-skip-locked)
4. [Solution 3: ShedLock](#solution-3-shedlock-distributed-lock)
5. [Cross Questions & Answers](#cross-questions--answers)
6. [Common Mistakes Developers Make](#common-mistakes-developers-make)
7. [Production-Ready Answer Template](#production-ready-answer-template)
8. [Advanced Topics](#advanced-topics)

---

## Page 1 - Problem Statement

### The Challenge

You have a **Spring Boot microservice** deployed on:
- **AWS**: 5 EC2 instances behind load balancer
- **Kubernetes**: 10 pods in a replica set
- **Azure**: Multiple app service instances

Your application has a `@Scheduled` job:

```java
@Scheduled(cron = "0 0 2 * * *")  // Runs at 2 AM daily
public void generateDailyReport() {
    // Generate report
    // Send emails
    // Update database
}
```

### The Problem

**Every instance will execute this job at 2 AM!**

- If you have 10 pods → Report generated 10 times
- If job sends emails → Users get 10 duplicate emails
- If job updates inventory → Data corruption

### Interview Question

**"How do you ensure the scheduled job executes ONLY ONCE across all instances?"**

---

---

## Page 2 - Solution 1: Pessimistic Lock (SELECT FOR UPDATE)

### How It Works

Use database row-level locking to ensure only one instance processes the job.

### Implementation

```java
@Service
public class SchedulerService {
    
    @Autowired
    private JdbcTemplate jdbcTemplate;
    
    @Scheduled(cron = "0 0 2 * * *")
    @Transactional
    public void generateDailyReport() {
        try {
            // Try to acquire lock
            String sql = "SELECT * FROM scheduler_lock " +
                        "WHERE job_name = 'DAILY_REPORT' " +
                        "FOR UPDATE";
            
            jdbcTemplate.queryForObject(sql, ...);
            
            // If we reach here, we have the lock
            executeReportGeneration();
            
        } catch (Exception e) {
            // Another instance has the lock
            log.info("Lock already acquired by another instance");
        }
    }
}
```

### Notes

- `FOR UPDATE` locks the selected row inside the current transaction.
- The first instance gets the lock; other instances block until commit/rollback.
- This guarantees single execution but can create contention under load.

### Database Schema

```sql
CREATE TABLE scheduler_lock (
    job_name VARCHAR(100) PRIMARY KEY,
    locked_at TIMESTAMP,
    locked_by VARCHAR(255)
);

INSERT INTO scheduler_lock (job_name) VALUES ('DAILY_REPORT');
```

### Simple Box Diagram (Beginner View)

```
+---------------------+        +-------------------------+
| Server 1            |        | Database                |
| "Try lock"           | -----> | SELECT ... FOR UPDATE   |
+---------------------+        +-------------------------+
          |
          | Lock granted
          v
+---------------------+
| Run job once         |
+---------------------+

+---------------------+        +-------------------------+
| Server 2            | -----> | SELECT ... FOR UPDATE   |
| "Try lock"           | <----- | Waits for lock          |
+---------------------+        +-------------------------+
          |
          v
      Exits later
```

### Pros
✅ Simple to implement  
✅ Works with existing RDBMS  
✅ No external dependencies  

### Cons
❌ **Other instances are blocked** (not scalable)  
❌ Wastes threads waiting  
❌ DB becomes bottleneck  
❌ Not suitable for high concurrency  

### Interviewer Objection

> "Why should other instances wait? Can you improve this?"

---

---

## Page 3 - Solution 2: FOR UPDATE SKIP LOCKED

### How It Works

Instead of waiting for lock, **skip locked rows** and process different rows in parallel.

### Use Case

Perfect for **batch processing** where multiple instances can work on different data partitions.

### Implementation

```java
@Service
public class BatchProcessorService {
    
    @Scheduled(fixedDelay = 5000)
    @Transactional
    public void processPendingOrders() {
        String sql = """
            SELECT * FROM orders 
            WHERE status = 'PENDING'
            FOR UPDATE SKIP LOCKED
            LIMIT 10
            """;
        
        List<Order> orders = jdbcTemplate.query(sql, ...);
        
        if (orders.isEmpty()) {
            return;  // No work available
        }
        
        // Process these 10 orders
        orders.forEach(this::processOrder);
    }
}
```

### Notes

- `FOR UPDATE SKIP LOCKED` returns only rows that are not locked by others.
- Rows already locked are skipped instead of waiting, so the query can return fewer rows or even none.
- This enables parallel batch work but is not intended for run-once jobs.

### Simple Box Diagram (Beginner View)

```
+---------------------+        +-------------------------+
| Worker 1            | -----> | Orders table            |
| SKIP LOCKED         | <----- | Rows 1-10               |
+---------------------+        +-------------------------+

+---------------------+        +-------------------------+
| Worker 2            | -----> | Orders table            |
| SKIP LOCKED         | <----- | Rows 11-20              |
+---------------------+        +-------------------------+

No waiting. Each worker gets different rows.
```

### Pros
✅ No blocking - truly parallel  
✅ Horizontal scalability  
✅ Efficient resource utilization  
✅ Great for batch processing  

### Cons
❌ **Starvation possible** (some rows may never get picked)  
❌ Not for "run once" jobs  
❌ Database compatibility (MySQL 8+, PostgreSQL, Oracle)  

### Interviewer Objection

> "What if ONLY ONE instance should run the job? Others should not run at all."

---

---

## Page 4 - Solution 3: ShedLock (Distributed Lock)

### How It Works

Instead of locking rows, **lock the job itself** using atomic database operations.

### The Magic: Atomic INSERT

```sql
-- Only ONE insert will succeed due to PRIMARY KEY constraint
INSERT INTO shedlock (name, lock_until, locked_at, locked_by)
VALUES ('DAILY_REPORT', NOW() + INTERVAL 10 MINUTE, NOW(), 'server-1');
```

### Implementation

#### Step 1: Add Dependency

```xml
<dependency>
    <groupId>net.javacrumbs.shedlock</groupId>
    <artifactId>shedlock-spring</artifactId>
    <version>5.10.0</version>
</dependency>
<dependency>
    <groupId>net.javacrumbs.shedlock</groupId>
    <artifactId>shedlock-provider-jdbc-template</artifactId>
    <version>5.10.0</version>
</dependency>
```

#### Step 2: Create Lock Table

```sql
CREATE TABLE shedlock (
    name VARCHAR(64) PRIMARY KEY,
    lock_until TIMESTAMP NOT NULL,
    locked_at TIMESTAMP NOT NULL,
    locked_by VARCHAR(255) NOT NULL
);
```

#### Step 3: Configure ShedLock

```java
@Configuration
@EnableScheduling
@EnableSchedulerLock(defaultLockAtMostFor = "10m")
public class SchedulerConfig {
    
    @Bean
    public LockProvider lockProvider(DataSource dataSource) {
        return new JdbcTemplateLockProvider(
            JdbcTemplateLockProvider.Configuration.builder()
                .withJdbcTemplate(new JdbcTemplate(dataSource))
                .usingDbTime() // Critical: use DB time, not app time
                .build()
        );
    }
}
```

#### Step 4: Use in Scheduled Job

```java
@Service
public class ReportService {
    
    @Scheduled(cron = "0 0 2 * * *")
    @SchedulerLock(
        name = "DAILY_REPORT",
        lockAtMostFor = "9m",   // Release lock after 9 min max
        lockAtLeastFor = "5m"   // Hold lock for at least 5 min
    )
    public void generateDailyReport() {
        log.info("Generating daily report - this runs only once!");
        // Business logic here
    }
}
```

### Simple Box Diagram (Beginner View)

```
+---------------------+        +-------------------------+
| Server A            |        | DB: shedlock table      |
| "Try lock"           | -----> | INSERT DAILY_REPORT     |
|                     |        | (only one succeeds)     |
+---------------------+        +-------------------------+
          |
          | Success -> Runs job
          v
+---------------------+
| Generate report      |
| Send emails          |
| Update database      |
+---------------------+

+---------------------+        +-------------------------+
| Server B            | -----> | INSERT DAILY_REPORT     |
| "Try lock"           | <----- | Duplicate key -> denied |
+---------------------+        +-------------------------+
          |
          v
      Exit (no work)
```

### Simple Box Diagram (Beginner View)

```
+---------------------+        +-------------------------+
| Server A             |        | DB: shedlock table       |
| "Try lock"            | -----> | INSERT DAILY_REPORT      |
|                      |        | (only one succeeds)      |
+---------------------+        +-------------------------+
          |
          | Success -> Runs job
          v
+---------------------+
| Generate report      |
| Send emails          |
| Update database      |
+---------------------+

+---------------------+        +-------------------------+
| Server B             | -----> | INSERT DAILY_REPORT      |
| "Try lock"            | <----- | Duplicate key -> denied  |
+---------------------+        +-------------------------+
          |
          v
      Exit (no work)
```

### How TTL (Time-To-Live) Prevents Deadlocks

```
+---------------------+        +-------------------------+
| Server A            | -----> | INSERT lock (10 min)     |
+---------------------+        +-------------------------+
          |
          | Crash before finish
          v
      (lock remains)

+---------------------+        +-------------------------+
| Server B            | -----> | Try lock before expiry   |
|                     | <----- | Denied                  |
+---------------------+        +-------------------------+

After lock expires:

+---------------------+        +-------------------------+
| Server B            | -----> | Try lock again           |
|                     | <----- | Success                 |
+---------------------+        +-------------------------+
```

### Pros
✅ **Only one instance executes** - perfect for "run once" jobs  
✅ No blocking - other instances exit immediately  
✅ TTL prevents deadlocks from crashes  
✅ Horizontally scalable  
✅ Works with MySQL, PostgreSQL, MongoDB, Redis  

### Cons
❌ Adds external dependency  
❌ Requires lock table maintenance  
❌ Clock skew can cause issues (solved by using DB time)  

---

## Cross Questions & Answers

### 🔥 Level 1: Pessimistic Lock Questions

#### Q1: What happens if the instance crashes after acquiring the lock?

**❌ Wrong Answer**:  
"The lock stays forever."

**✅ Correct Answer (Simple)**:  
"The lock is inside a DB transaction. If the server crashes, the DB ends the transaction and releases the lock. Another server can try again."

**Why This Matters**: Shows you know locks are tied to transactions.

---

#### Q2: What isolation level are you using?

**❌ Wrong Answer**:  
"No idea."

**✅ Correct Answer (Simple)**:  
"Usually `READ COMMITTED` is enough. It stops dirty reads and works well with `SELECT FOR UPDATE`."

**Why This Matters**: Shows you understand basic DB isolation.

---

#### Q3: What is the performance impact?

**❌ Wrong Answer**:  
"No impact."

**✅ Correct Answer (Simple)**:  
"Other servers wait. That means wasted threads and slower system when traffic is high."

**Why This Matters**: Shows you understand blocking cost.

---

### 🔥 Level 2: SKIP LOCKED Questions

#### Q4: Is SKIP LOCKED supported in all databases?

**❌ Wrong Answer**:  
"Yes, everywhere."

**✅ Correct Answer (Simple)**:  
"No. MySQL 8+ and Postgres support it. Older MySQL and SQL Server do not."

**Why This Matters**: Avoids surprises in production.

---

#### Q5: What if rows are continuously locked?

**❌ Wrong Answer**:  
"They will be fine."

**✅ Correct Answer (Simple)**:  
"Some rows might keep getting skipped forever. You need retries or alerts for old rows."

**Why This Matters**: Shows you know starvation risk.

---

#### Q6: Is this suitable for a cron job that must run once?

**❌ Wrong Answer**:  
"Yes."

**✅ Correct Answer (Simple)**:  
"No. `SKIP LOCKED` is for parallel batch work. For run-once jobs, use ShedLock or leader election."

**Why This Matters**: Shows correct tool choice.

**Easy Explanation (Workflow)**:

**Cron job (run once) goal**:
- One scheduled task should run only once at the given time, even if 10 servers are running.

**Why `SKIP LOCKED` is not for this**:
- `SKIP LOCKED` lets many workers take different rows at the same time.
- That is great for batch processing, but a cron job should run only one copy, not many.

**ShedLock workflow (simple)**:
```
Time 2:00 AM

Server A -> Try lock (DB row)
Server B -> Try lock (DB row)
Server C -> Try lock (DB row)

Only one server gets the lock
That server runs the cron job
Others exit
```

**Leader election workflow (simple)**:
```
All servers start
They elect ONE leader

Only the leader runs the cron job
If leader dies -> new leader is elected
```

---

### 🔥 Level 3: ShedLock Questions (Critical!)

#### Q7: What if server crashes after acquiring lock?

**❌ Wrong Answer**:  
"Someone must unlock it manually."

**✅ Correct Answer (Simple)**:  
"ShedLock uses a timeout. If the server dies, the lock expires and another server can run the job."

**Why This Matters**: Shows you understand TTL.

---

#### Q8: What if system clocks are different?

**❌ Wrong Answer**:  
"We ignore it."

**✅ Correct Answer (Simple)**:  
"Use database time with `usingDbTime()` so all servers use the same clock."

**Why This Matters**: Prevents clock-skew bugs.

---

#### Q9: What if job runs longer than lockAtMostFor?

**❌ Wrong Answer**:  
"Nothing happens."

**✅ Correct Answer (Simple)**:  
"The lock can expire while the job is still running, so another server may start the same job. Set `lockAtMostFor` longer than the worst case."

**Why This Matters**: Prevents duplicate runs.

---

#### Q10: What happens during database failover?

**❌ Wrong Answer**:  
"Nothing changes."

**✅ Correct Answer (Simple)**:  
"Lock requests can fail. Add retries and alerts so jobs don’t silently stop."

**Why This Matters**: Shows reliability awareness.

---

#### Q11: Is ShedLock strongly consistent?

**❌ Wrong Answer**:  
"Yes, always."

**✅ Correct Answer (Simple)**:  
"It depends on the database. If all servers use one primary DB, it is strong. If you use replicas or multi-region, it can be weaker."

**Why This Matters**: Shows you know data consistency depends on storage.

**Easy Explanation (Workflow)**:

**Case 1: Single primary DB (strong enough)**
```
Server A -> Primary DB (lock row)
Server B -> Primary DB (same lock row)

Only one server can write the lock row
So only one server runs the job
```

**Case 2: Replicas or multi-region (weaker)**
```
Server A -> DB Region 1
Server B -> DB Region 2 (replica delay)

If replicas are behind, both servers might think the lock is free
Two jobs can run by mistake
```

**Simple rule**:
- One primary DB = safest for ShedLock.
- Replicas or multi-region = add care (use primary only, monitor lag).

**How to solve Case 2 (simple)**:
- **Write locks only to the primary DB** (never to replicas).
- **Disable read replicas for lock checks**, or force the lock table to use the primary connection.
- **Monitor replication lag** and alert if it is high.
- If the system is critical, use **leader election** (etcd/ZooKeeper/K8s Lease) for stronger guarantees.

---

### 🔥 Level 4: Architecture Questions

#### Q12: Why not use Redis instead of DB?

**❌ Wrong Answer**:  
"Redis is just better."

**✅ Correct Answer (Simple)**:  
"Redis is fast but adds another system to run. DB is simpler if you already have it. Choose based on scale and ops cost."

**Why This Matters**: Shows tradeoff thinking.

---

#### Q13: What is Redlock?

**❌ Wrong Answer**:  
"No idea."

**✅ Correct Answer (Simple)**:  
"Redlock is a way to lock using multiple Redis servers so one failure does not break the lock."

**Why This Matters**: Shows you know Redis locking basics.

---

#### Q14: What if two instances acquire lock due to network partition?

**❌ Wrong Answer**:  
"That never happens."

**✅ Correct Answer (Simple)**:  
"It can happen in network splits. The safe fix is leader election or a consensus system (etcd/ZooKeeper)."

**Why This Matters**: Shows you know split-brain risk.

---

#### Q15: In Kubernetes, how would you solve this?

**❌ Wrong Answer**:  
"Just use ShedLock everywhere."

**✅ Correct Answer (Simple)**:  
"Use Kubernetes CronJob for run-once tasks. For always-on apps, use leader election."

**Why This Matters**: Shows you know the cloud-native option.

---

## Common Mistakes Developers Make

### ❌ Mistake 1: Not Handling Transaction Timeout

```java
// BAD
@Transactional
@Scheduled(cron = "0 0 2 * * *")
public void longRunningJob() {
    SELECT ... FOR UPDATE;  // Lock acquired
    // 30-minute processing
    // Transaction timeout!
}
```

**Impact**: Lock released unexpectedly, duplicate execution.

**Fix**:
```java
@Transactional(timeout = 3600)  // 1 hour
@Scheduled(cron = "0 0 2 * * *")
public void longRunningJob() {
    // ...
}
```

---

### ❌ Mistake 2: Using Application Time Instead of DB Time

```java
// BAD - Clock skew issues
LocalDateTime lockUntil = LocalDateTime.now().plusMinutes(10);
```

**Fix**:
```java
// GOOD - Use DB time
JdbcTemplateLockProvider.Configuration.builder()
    .usingDbTime()  // Critical!
    .build()
```

---

### ❌ Mistake 3: Not Setting lockAtMostFor

```java
// BAD - No automatic lock release
@SchedulerLock(name = "REPORT")
public void generate() { }
```

**Fix**:
```java
// GOOD
@SchedulerLock(
    name = "REPORT",
    lockAtMostFor = "PT10M",  // ISO-8601 duration
    lockAtLeastFor = "PT5M"
)
public void generate() { }
```

---

### ❌ Mistake 4: Forgetting Database Indexes

```sql
-- BAD - Slow lock acquisition
CREATE TABLE shedlock (
    name VARCHAR(64) PRIMARY KEY
);
```

**Fix**:
```sql
-- GOOD - Indexed properly
CREATE TABLE shedlock (
    name VARCHAR(64) PRIMARY KEY,
    lock_until TIMESTAMP NOT NULL,
    locked_at TIMESTAMP NOT NULL,
    locked_by VARCHAR(255),
    INDEX idx_lock_until (lock_until)  -- For cleanup/monitoring
);
```

---

### ❌ Mistake 5: No Monitoring/Alerting

Missing:
- Lock acquisition failures
- Lock held longer than expected
- Failed job executions

**Fix - Add Observability**:
```java
@Aspect
@Component
public class LockMonitor {
    
    @Around("@annotation(schedulerLock)")
    public Object monitor(ProceedingJoinPoint pjp, SchedulerLock lock) throws Throwable {
        String jobName = lock.name();
        long start = System.currentTimeMillis();
        
        try {
            Object result = pjp.proceed();
            long duration = System.currentTimeMillis() - start;
            
            metrics.recordJobSuccess(jobName, duration);
            
            if (duration > lock.lockAtMostFor()) {
                alerts.send("Job exceeded lock time: " + jobName);
            }
            
            return result;
        } catch (LockingException e) {
            metrics.recordLockFailure(jobName);
            throw e;
        }
    }
}
```

---

## Production-Ready Answer Template

**Use this exact structure in interviews:**

### Simple Interview Answer (1 Minute)

"If the app runs on many servers, @Scheduled runs on all of them, so the job runs many times. To stop that, I use a distributed lock. All servers try to get the lock, only one wins, and only that one runs the job. If the server crashes, the lock expires after a timeout so another server can take over. For batch work I use `SKIP LOCKED` to split rows across servers; for run-once jobs I use ShedLock."

### Opening

> "In a multi-instance deployment, @Scheduled runs on every instance. To prevent duplicate execution, I'd evaluate three approaches based on the use case."

### Solution Comparison

> "**Pessimistic Lock** works but blocks other instances, creating a bottleneck. It's simple but not scalable.
>
> **SKIP LOCKED** is excellent for parallel batch processing where instances can work on different data partitions, but it's not suitable for run-once jobs.
>
> **ShedLock** is the best solution for run-once scheduled jobs. It uses atomic database inserts with primary key constraints to ensure only one instance executes, and includes TTL-based lock expiration to handle crashes gracefully."

### Implementation Details

> "We configure ShedLock to use database server time instead of application time to avoid clock skew issues. We set lockAtMostFor slightly higher than expected job duration, and monitor lock acquisition patterns.
>
> For cloud-native deployments, I'd also consider Kubernetes CronJobs or AWS EventBridge as managed alternatives."

### Production Experience

> "In our production system with 10 Kubernetes pods, we initially used pessimistic locking, but migrated to ShedLock when we observed lock contention. We monitor lock acquisition metrics and alert if jobs exceed expected duration."

---

## Advanced Topics

### Topic 1: Redis Distributed Lock (Complete Pattern)

```java
@Service
public class RedisLockScheduler {
    
    @Autowired
    private StringRedisTemplate redisTemplate;
    
    @Scheduled(cron = "0 0 2 * * *")
    public void generateReport() {
        String lockKey = "lock:daily-report";
        String lockValue = UUID.randomUUID().toString();
        
        Boolean acquired = redisTemplate.opsForValue()
            .setIfAbsent(
                lockKey, 
                lockValue, 
                Duration.ofMinutes(10)  // TTL
            );
        
        if (Boolean.TRUE.equals(acquired)) {
            try {
                executeReport();
            } finally {
                // Atomic release with Lua script
                String script = 
                    "if redis.call('get', KEYS[1]) == ARGV[1] then " +
                    "  return redis.call('del', KEYS[1]) " +
                    "else " +
                    "  return 0 " +
                    "end";
                
                redisTemplate.execute(
                    new DefaultRedisScript<>(script, Long.class),
                    Collections.singletonList(lockKey),
                    lockValue
                );
            }
        } else {
            log.info("Lock already acquired by another instance");
        }
    }
}
```

**Why Lua Script for Release?**
- Ensures only lock holder can release
- Prevents accidental release of someone else's lock
- Atomic operation

---

### Topic 2: ZooKeeper Leader Election

```java
@Configuration
public class ZooKeeperConfig {
    
    @Bean
    public CuratorFramework curatorFramework() {
        RetryPolicy retryPolicy = new ExponentialBackoffRetry(1000, 3);
        
        CuratorFramework client = CuratorFrameworkFactory.newClient(
            "zookeeper:2181",
            retryPolicy
        );
        
        client.start();
        return client;
    }
    
    @Bean
    public LeaderSelector leaderSelector(CuratorFramework client) {
        return new LeaderSelector(
            client,
            "/scheduler/daily-report",
            new LeaderSelectorListener() {
                @Override
                public void takeLeadership(CuratorFramework client) {
                    // This instance is leader
                    executeScheduledJob();
                }
                
                @Override
                public void stateChanged(CuratorFramework client, 
                                       ConnectionState newState) {
                    // Handle connection state changes
                }
            }
        );
    }
}
```

---

### Topic 3: Database Lock Cleanup Job

```java
@Service
public class LockCleanupService {
    
    @Scheduled(cron = "0 */5 * * * *")  // Every 5 minutes
    @Transactional
    public void cleanupExpiredLocks() {
        String sql = """
            DELETE FROM shedlock 
            WHERE lock_until < NOW()
            """;
        
        int deleted = jdbcTemplate.update(sql);
        
        if (deleted > 0) {
            log.warn("Cleaned up {} expired locks", deleted);
            metrics.recordExpiredLocks(deleted);
        }
    }
}
```

---

### Topic 4: Kubernetes Leader Election

```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: scheduler-config
data:
  enable-leader-election: "true"
---
apiVersion: apps/v1
kind: Deployment
metadata:
  name: scheduler-app
spec:
  replicas: 3
  template:
    spec:
      serviceAccountName: scheduler-sa
      containers:
      - name: app
        env:
        - name: ENABLE_LEADER_ELECTION
          valueFrom:
            configMapKeyRef:
              name: scheduler-config
              key: enable-leader-election
```

```java
@Configuration
@ConditionalOnProperty(name = "enable-leader-election", havingValue = "true")
public class K8sLeaderElectionConfig {
    
    @Bean
    public LeaderElector leaderElector() {
        return new KubernetesLeaderElector(
            "scheduler-lock",
            Duration.ofSeconds(15)  // Lease duration
        );
    }
}
```

---

## Quick Reference Cheat Sheet

| Feature | Pessimistic Lock | SKIP LOCKED | ShedLock | Redis Lock | K8s CronJob |
|---------|-----------------|-------------|----------|------------|-------------|
| **Blocks Others** | ✅ Yes | ❌ No | ❌ No | ❌ No | N/A |
| **Run Once** | ✅ Yes | ❌ No | ✅ Yes | ✅ Yes | ✅ Yes |
| **Parallel Processing** | ❌ No | ✅ Yes | ❌ No | ❌ No | ⚠️ Can |
| **Auto Crash Recovery** | ✅ Yes | ✅ Yes | ✅ Yes (TTL) | ✅ Yes (TTL) | ✅ Yes |
| **DB Dependency** | ✅ Yes | ✅ Yes | ✅ Yes | ❌ No | ❌ No |
| **Cloud Native** | ⚠️ Partial | ⚠️ Partial | ✅ Yes | ✅ Yes | ✅ Yes |
| **Complexity** | Low | Medium | Medium | High | Low |
| **Best For** | Simple apps | Batch processing | Scheduled jobs | High freq | K8s deployments |

---

## Interview Scoring Matrix

| Topic Coverage | Junior (1-3yr) | Mid (3-5yr) | Senior (5-7yr) | Staff (7+yr) |
|----------------|----------------|-------------|----------------|--------------|
| **Knows Solutions** | 1-2 approaches | All 3 approaches | + Redis/ZooKeeper | + Consensus algorithms |
| **Cross Questions** | 3-5 answers | 7-10 answers | 12+ answers | All + edge cases |
| **Production Issues** | None | Lock timeout | Clock skew, TTL | Split-brain, CAP theorem |
| **Alternatives** | Just DB lock | + ShedLock | + Redis, K8s | + etcd, Consul, EventBridge |
| **Observability** | Logs | Metrics | Alerts + Dashboards | Distributed tracing |

---

## Further Learning

### Recommended Reading
1. **"Designing Data-Intensive Applications"** by Martin Kleppmann (Chapter 9: Consistency and Consensus)
2. **Redis Distributed Locks**: https://redis.io/docs/manual/patterns/distributed-locks/
3. **ShedLock Documentation**: https://github.com/lukas-krecan/ShedLock
4. **Kubernetes Leader Election**: https://kubernetes.io/blog/2016/01/simple-leader-election-with-kubernetes/

### Related LeetCode Problems
- None directly, but understand:
  - Concurrency control
  - Distributed systems
  - Transaction isolation

### Hands-On Practice
1. Set up 3 Spring Boot instances locally
2. Implement all 3 locking mechanisms
3. Use Docker Compose to simulate multi-instance
4. Induce failures (kill instance mid-job)
5. Monitor with Prometheus + Grafana

---

## Real Production Incident Story (STAR Format)

**Use this in behavioral interviews:**

> **Situation**: We had a daily report job running in a microservice deployed across 5 EC2 instances behind an AWS ALB.
>
> **Task**: After deployment, customers complained they received 5 duplicate emails every morning at 2 AM.
>
> **Action**: 
> 1. Identified @Scheduled was running on all instances
> 2. Initially implemented pessimistic locking - worked but slowed down other queries
> 3. Noticed lock contention in database metrics
> 4. Migrated to ShedLock with lockAtMostFor = 10 minutes
> 5. Configured DB time to avoid clock skew
> 6. Added CloudWatch alarms for lock acquisition failures
> 7. Implemented cleanup job for expired locks
>
> **Result**: 
> - Eliminated duplicate emails completely
> - Reduced database lock wait time by 90%
> - Improved overall application latency
> - Added monitoring that caught a partial outage later
> - Documented the pattern for other teams

---

**End of Guide** | Prepared for 2026 Senior Software Engineer Interviews | Last Updated: February 12, 2026
