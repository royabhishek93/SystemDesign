# Kubernetes Leader Election in Production

**Target Level**: Senior (5-7 years) to Staff+ (7+ years)  
**Focus**: Production Kubernetes deployments, leader election coordination  
**Interview Context**: System design for distributed scheduling on Kubernetes  
**Last Updated**: February 2026

---

## 🎯 Senior-Level Context

When running distributed jobs on Kubernetes, you need **one pod to lead the coordination** while others remain passive. This document covers production-grade approaches for any scale.

### Key Interview Insight
> "Leader election is not about speed—it's about **consistency guarantees** and **failure recovery**. A 2-second delay is fine; a split-brain is catastrophic."

---

## 📊 The Core Challenge in Kubernetes

```
Pod 1 (replica-1)          Pod 2 (replica-2)          Pod 3 (replica-3)
    ├─ Scheduler                ├─ Scheduler                ├─ Scheduler
    ├─ Job Executor             ├─ Job Executor             ├─ Job Executor
    └─ Status: running          └─ Status: running          └─ Status: running

Problem: All 3 run the same job at 2:00 AM → Duplicate processing
Solution: ELECT ONE LEADER to coordinate the job
```

---

## 🏗️ Approach 1: Kubernetes Native Leader Election (Lease API)

**Best for**: Cloud-native deployments, no external dependencies, native integration  
**Production Readiness**: ⭐⭐⭐⭐⭐  
**Complexity**: Medium

### How It Works

Kubernetes **Lease API** (built-in) allows pods to compete for leadership. The lease holder is the leader; others watch for expiry.

### Block Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                   Kubernetes Cluster                             │
├─────────────────────────────────────────────────────────────────┤
│                                                                   │
│  ┌─────────────┐      ┌─────────────┐      ┌─────────────┐      │
│  │   Pod 1     │      │   Pod 2     │      │   Pod 3     │      │
│  │ (Replica 1) │      │ (Replica 2) │      │ (Replica 3) │      │
│  └─────────────┘      └─────────────┘      └─────────────┘      │
│        ▲                    ▲                    ▲                │
│        │ WATCH              │ WATCH              │ WATCH          │
│        └────────────────────┼────────────────────┘                │
│                             │                                    │
│                    ┌────────▼────────┐                           │
│                    │  Lease Object   │                           │
│                    │  (etcd backed)  │                           │
│                    │                 │                           │
│                    │ holder: pod-1   │                           │
│                    │ exp-time: 15s   │                           │
│                    └─────────────────┘                           │
│                             ▲                                    │
│                             │ RENEW EVERY 5s                     │
│                             │ (Pod 1 as leader)                  │
│                             │                                    │
│                    ┌────────┴────────┐                           │
│                    │ Leader: Pod 1   │                           │
│                    │ Executes Job    │                           │
│                    │ Every 2:00 AM   │                           │
│                    └─────────────────┘                           │
│                                                                   │
└─────────────────────────────────────────────────────────────────┘
```

### Production Code (Spring Boot + Kubernetes Client)

**Dependencies**:
```xml
<dependency>
    <groupId>io.kubernetes</groupId>
    <artifactId>client-java</artifactId>
    <version>18.0.0</version>
</dependency>

<dependency>
    <groupId>org.springframework.integration</groupId>
    <artifactId>spring-integration-kubernetes</artifactId>
    <version>3.1.0</version>
</dependency>
```

**Implementation**:
```java
@Component
@Slf4j
public class KubernetesLeaderElection {
    
    @Autowired
    private CoreV1Api coreV1Api;
    
    @Autowired
    private CoordinationV1Api coordinationApi;
    
    @Autowired
    private DistributedJobService jobService;
    
    private static final String LEASE_NAME = "job-scheduler-lease";
    private static final String NAMESPACE = "default";
    private static final int LEASE_DURATION = 15; // seconds
    private static final int RENEW_INTERVAL = 5; // seconds
    
    private String podName;
    private V1Lease currentLease;
    private boolean isLeader = false;
    
    @PostConstruct
    public void init() throws Exception {
        this.podName = System.getenv("HOSTNAME");
        startLeaderElection();
    }
    
    private void startLeaderElection() throws Exception {
        ScheduledExecutorService executor = Executors.newScheduledThreadPool(2);
        
        // Task 1: Try to acquire lease
        executor.scheduleAtFixedRate(this::renewLease, 0, RENEW_INTERVAL, TimeUnit.SECONDS);
        
        // Task 2: Watch lease for expiry
        executor.scheduleAtFixedRate(this::watchLeaseStatus, 0, 3, TimeUnit.SECONDS);
        
        // Task 3: Run job if leader
        executor.scheduleAtFixedRate(this::executeJobIfLeader, 0, 1, TimeUnit.SECONDS);
    }
    
    private synchronized void renewLease() {
        try {
            V1Lease lease = getOrCreateLease();
            
            LocalDateTime now = LocalDateTime.now();
            LocalDateTime acquireTime = now;
            LocalDateTime renewTime = now;
            LocalDateTime expireTime = now.plusSeconds(LEASE_DURATION);
            
            lease.getSpec()
                .holder(podName)
                .acquireTime(new MicroTime(acquireTime.toString()))
                .renewTime(new MicroTime(renewTime.toString()))
                .leaseTransitions(1)
                .leaseRenewalMicroseconds((long)(RENEW_INTERVAL * 1_000_000L));
            
            coordinationApi.patchNamespacedLease(
                LEASE_NAME,
                NAMESPACE,
                lease,
                "true",
                null,
                null,
                null
            );
            
            this.isLeader = true;
            log.info("✅ Renewed leadership lease for {} seconds", LEASE_DURATION);
            
        } catch (ApiException e) {
            if (e.getCode() == 409) { // Conflict - someone else has it
                this.isLeader = false;
                log.warn("❌ Lost leadership (conflict), another pod is leading");
            } else {
                log.error("Error renewing lease", e);
            }
        }
    }
    
    private V1Lease getOrCreateLease() throws ApiException {
        try {
            return coordinationApi.readNamespacedLease(LEASE_NAME, NAMESPACE);
        } catch (ApiException e) {
            if (e.getCode() == 404) {
                // Create lease if doesn't exist
                V1Lease newLease = new V1Lease()
                    .apiVersion("coordination.k8s.io/v1")
                    .kind("Lease")
                    .metadata(new V1ObjectMeta()
                        .name(LEASE_NAME)
                        .namespace(NAMESPACE)
                    )
                    .spec(new V1LeaseSpec()
                        .holder(podName)
                        .leaseTransitions(0)
                        .leaseRenewalMicroseconds((long)(RENEW_INTERVAL * 1_000_000L))
                    );
                
                return coordinationApi.createNamespacedLease(
                    NAMESPACE,
                    newLease,
                    "true",
                    null,
                    null
                );
            }
            throw e;
        }
    }
    
    private void watchLeaseStatus() {
        try {
            V1Lease lease = coordinationApi.readNamespacedLease(LEASE_NAME, NAMESPACE);
            String holder = lease.getSpec().getHolder();
            LocalDateTime renewTime = LocalDateTime.parse(lease.getSpec().getRenewTime());
            LocalDateTime now = LocalDateTime.now();
            
            if (holder == null || !holder.equals(podName)) {
                // Someone else is leader
                if (Duration.between(renewTime, now).getSeconds() > LEASE_DURATION) {
                    log.warn("⚠️  Lease expired, attempting to acquire leadership");
                    this.isLeader = false;
                }
            }
        } catch (ApiException e) {
            log.error("Error watching lease", e);
        }
    }
    
    private void executeJobIfLeader() {
        if (isLeader) {
            try {
                jobService.executeDailyScheduledJob();
            } catch (Exception e) {
                log.error("Job execution failed", e);
            }
        }
    }
}
```

### ✅ Advantages
- **Native K8s integration** - Uses etcd as backing store
- **No external dependencies** - Works in any Kubernetes cluster
- **Automatic failure recovery** - Lease timeout triggers new election
- **Multi-leader safe** - Built-in conflict detection
- **Scalable** - Works with 10 or 10,000 pods

### ❌ Disadvantages
- **API server dependency** - Requires Kubernetes API availability
- **Network latency** - Lease operations go through etcd
- **Kubernetes knowledge required** - More setup than simple Redis
- **Leader lag** - ~15-30 seconds from failure to new leader

### 🎯 Senior Interview Talking Points
```
"Kubernetes Lease API provides eventual consistency. If a leader 
crashes, it takes 15-30 seconds for the next pod to detect the lease 
expiry and acquire leadership. This is acceptable for most scheduled 
jobs but NOT for sub-second coordination."

"The key insight is that a SINGLE holding pod RENEWS the lease every 
N seconds. Others watch. If renewal fails for LEASE_DURATION seconds, 
any pod can acquire it. This prevents split-brain because renewal 
requires atomic CAS on etcd."
```

---

## 🏗️ Approach 2: External Coordination Service (etcd/Consul)

**Best for**: Multi-cluster deployments, cross-datacenter coordination  
**Production Readiness**: ⭐⭐⭐⭐⭐  
**Complexity**: High

### How It Works

Use external coordinated service (etcd, Consul) that all K8s pods trust. Leader holds a lease; failure triggers new election.

### Block Diagram

```
┌──────────────────────────────────────────────────────────────────┐
│                    Kubernetes Cluster 1                          │
│  ┌─────────┐  ┌─────────┐  ┌─────────┐                          │
│  │ Pod 1   │  │ Pod 2   │  │ Pod 3   │                          │
│  │ Watch   │  │ Watch   │  │ Watch   │                          │
│  └────┬────┘  └────┬────┘  └────┬────┘                          │
└───────┼─────────────┼─────────────┼────────────────────────────────┘
        │             │             │
        │ Register    │ Register    │ Register
        │ & Lease     │ & Lease     │ & Lease
        │             │             │
        └─────────────┼─────────────┘
                      │
        ┌─────────────▼─────────────┐
        │   External Coordination   │
        │   Service (etcd/Consul)   │
        │                           │
        │ ┌─────────────────────┐   │
        │ │ Lease Data:         │   │
        │ │ - holder: pod-1     │   │
        │ │ - ttl: 30s          │   │
        │ │ - version: 42       │   │
        │ └─────────────────────┘   │
        │                           │
        │ ┌─────────────────────┐   │
        │ │ Watch Channel:      │   │
        │ │ - All pods watching │   │
        │ │ - Notified on lease │   │
        │ │   change            │   │
        │ └─────────────────────┘   │
        └───────────────────────────┘
                      ▲
                      │ Lease Renewal
                      │ Every 10s
                      │ (from Pod 1)
                      │
        ┌─────────────┴─────────────┐
        │   Leader Pod 1            │
        │   - Renews lease every 10s│
        │   - Executes scheduled job│
        │   - On crash: lease       │
        │     expires in 30s        │
        └───────────────────────────┘
```

### Production Code (Consul Example)

```java
@Component
@Slf4j
public class ConsulLeaderElection {
    
    @Autowired
    private ConsulClient consulClient;
    
    @Autowired
    private DistributedJobService jobService;
    
    private static final String CONSUL_KEY = "job-scheduler/leader";
    private static final String SESSION_DESCRIPTION = "distributed-job-scheduler";
    private static final long SESSION_TTL = 30; // seconds
    private static final long RENEW_INTERVAL = 10; // seconds
    
    private String sessionId;
    private String podName;
    private boolean isLeader = false;
    
    @PostConstruct
    public void init() {
        this.podName = System.getenv("HOSTNAME");
        startLeaderElection();
    }
    
    private void startLeaderElection() {
        ScheduledExecutorService executor = Executors.newScheduledThreadPool(2);
        
        // Create session
        sessionId = createConsulSession();
        
        // Renew leadership lease
        executor.scheduleAtFixedRate(this::acquireLeadership, 0, RENEW_INTERVAL, TimeUnit.SECONDS);
        
        // Watch for leader changes
        executor.scheduleAtFixedRate(this::watchLeadershipStatus, 0, 5, TimeUnit.SECONDS);
        
        // Execute job if leader
        executor.scheduleAtFixedRate(this::executeJobIfLeader, 0, 2, TimeUnit.SECONDS);
    }
    
    private String createConsulSession() {
        NewSession session = new NewSession();
        session.setName(SESSION_DESCRIPTION);
        session.setTtl(SESSION_TTL + "s");
        session.setBehavior(Behavior.DELETE); // Delete key on session expiry
        
        String sessionId = consulClient.sessionCreate(session, QueryParams.BLANK).getValue();
        log.info("Created Consul session: {}", sessionId);
        return sessionId;
    }
    
    private void acquireLeadership() {
        try {
            String leadershipValue = String.format("%s:%d", podName, System.currentTimeMillis());
            
            // Atomic Compare-And-Set operation
            PutParams params = PutParams.BLANK;
            params = params.setAcquireSession(sessionId);
            
            boolean acquired = consulClient.setKVValue(CONSUL_KEY, leadershipValue, params);
            
            if (acquired) {
                this.isLeader = true;
                log.info("✅ Acquired leadership in Consul");
            } else {
                this.isLeader = false;
                log.debug("❌ Failed to acquire leadership (another pod has it)");
            }
        } catch (Exception e) {
            log.error("Error acquiring leadership", e);
            this.isLeader = false;
        }
    }
    
    private void watchLeadershipStatus() {
        try {
            Response<GetValue> response = consulClient.getKVValue(CONSUL_KEY);
            GetValue value = response.getValue();
            
            if (value != null) {
                String currentLeader = value.getDecodedValue();
                String currentHolder = currentLeader.split(":")[0];
                
                if (!currentHolder.equals(podName)) {
                    this.isLeader = false;
                    log.debug("Another pod is leading: {}", currentHolder);
                }
            } else {
                // Key doesn't exist - try to acquire
                this.isLeader = false;
            }
        } catch (Exception e) {
            log.error("Error watching leadership", e);
        }
    }
    
    private void executeJobIfLeader() {
        if (isLeader) {
            try {
                jobService.executeDailyScheduledJob();
            } catch (Exception e) {
                log.error("Job execution failed", e);
            }
        }
    }
}
```

### ✅ Advantages
- **Multi-cluster capable** - Single coordination point across clusters
- **Stronger consistency** - Consul/etcd provide stronger guarantees
- **Flexible policies** - Custom session behavior, health checks
- **Rich API** - Watch notifications, blocking queries

### ❌ Disadvantages
- **External dependency** - Requires running Consul/etcd
- **Additional operational burden** - Monitoring, backup, recovery
- **Network overhead** - Extra hop from K8s to external service
- **Cross-cluster complexity** - Network security, firewalls

---

## 🏗️ Approach 3: Database-Backed Leader Lock

**Best for**: Existing database infrastructure, simple single-cluster  
**Production Readiness**: ⭐⭐⭐⭐  
**Complexity**: Low

### How It Works

Store leader information in your primary database. Pods race to acquire a row lock; holder is the leader.

### Block Diagram

```
┌────────────────────────────────────────────────────────────┐
│              Kubernetes Pod Deployment (3 replicas)         │
├────────────────────────────────────────────────────────────┤
│                                                              │
│  Pod 1          Pod 2           Pod 3                       │
│  ┌────────┐     ┌────────┐      ┌────────┐                 │
│  │LeaderDB│     │LeaderDB│      │LeaderDB│                 │
│  │Client  │     │Client  │      │Client  │                 │
│  └───┬────┘     └───┬────┘      └───┬────┘                 │
│      │              │               │                       │
│      │ SELECT..FOR  │ SELECT..FOR   │ SELECT..FOR           │
│      │ UPDATE       │ UPDATE        │ UPDATE                │
│      │              │               │                       │
│      └──────────────┼───────────────┘                       │
│                     │                                       │
│          ┌──────────▼────────────┐                           │
│          │   PostgreSQL DB       │                           │
│          │                       │                           │
│          │ ┌───────────────────┐ │                           │
│          │ │ leader_lock table │ │                           │
│          │ ├───────────────────┤ │                           │
│          │ │ id: 1             │ │                           │
│          │ │ holder: pod-1     │ │                           │
│          │ │ acquired_at: T1   │ │                           │
│          │ │ last_updated: T2  │ │                           │
│          │ │ version: 5        │ │                           │
│          │ └───────────────────┘ │                           │
│          │                       │                           │
│          │ [Row locked by T1]    │                           │
│          │ [Others wait...]      │                           │
│          └───────────────────────┘                           │
│                                                              │
└────────────────────────────────────────────────────────────┘

Pod 1 wins the lock → executes job → releases lock
Others wait for lock availability
```

### Production Code (Spring Boot + JPA)

**Database schema**:
```sql
CREATE TABLE leader_lock (
    id BIGINT PRIMARY KEY,
    holder VARCHAR(255) NOT NULL,
    acquired_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    last_updated TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    version INT DEFAULT 0
);

-- Insert single row (by convention, always id = 1)
INSERT INTO leader_lock (id, holder) VALUES (1, 'unknown') ON CONFLICT DO NOTHING;
```

**Spring Data JPA Entity**:
```java
@Entity
@Table(name = "leader_lock")
@Getter
@Setter
@NoArgsConstructor
public class LeaderLockEntity {
    
    @Id
    private Long id = 1L; // Always use single row
    
    @Column(nullable = false)
    private String holder;
    
    @Column(name = "acquired_at", nullable = false, updatable = false)
    private LocalDateTime acquiredAt;
    
    @Column(name = "last_updated", nullable = false)
    private LocalDateTime lastUpdated;
    
    @Version
    @Column(name = "version")
    private Integer version;
}
```

**Repository**:
```java
@Repository
public interface LeaderLockRepository extends JpaRepository<LeaderLockEntity, Long> {
    
    @Lock(LockModeType.PESSIMISTIC_WRITE)
    @Query("SELECT l FROM LeaderLockEntity l WHERE l.id = 1")
    Optional<LeaderLockEntity> acquireLeaderLock();
}
```

**Service**:
```java
@Component
@Slf4j
public class DatabaseLeaderElection {
    
    @Autowired
    private LeaderLockRepository leaderLockRepository;
    
    @Autowired
    private DistributedJobService jobService;
    
    private String podName;
    private boolean isLeader = false;
    private static final long LEASE_DURATION = 30 * 1000; // 30 seconds in ms
    private static final long RENEW_INTERVAL = 10 * 1000; // 10 seconds in ms
    
    @PostConstruct
    public void init() {
        this.podName = System.getenv("HOSTNAME");
        startLeaderElection();
    }
    
    private void startLeaderElection() {
        ScheduledExecutorService executor = Executors.newScheduledThreadPool(2);
        
        // Try to renew leadership every RENEW_INTERVAL
        executor.scheduleAtFixedRate(
            this::renewLeadershipLease,
            0,
            RENEW_INTERVAL,
            TimeUnit.MILLISECONDS
        );
        
        // Execute job if still leader
        executor.scheduleAtFixedRate(
            this::executeJobIfLeader,
            0,
            2,
            TimeUnit.SECONDS
        );
    }
    
    @Transactional
    private void renewLeadershipLease() {
        try {
            // Pessimistic lock: Only one pod can hold this at a time
            Optional<LeaderLockEntity> lockOpt = leaderLockRepository.acquireLeaderLock();
            
            if (lockOpt.isPresent()) {
                LeaderLockEntity lock = lockOpt.get();
                
                // Check if we're the current holder or if lease expired
                LocalDateTime now = LocalDateTime.now();
                long timeSinceLastUpdate = Duration
                    .between(lock.getLastUpdated(), now)
                    .toMillis();
                
                if (lock.getHolder().equals(podName) || timeSinceLastUpdate > LEASE_DURATION) {
                    // We can renew/acquire the lease
                    lock.setHolder(podName);
                    lock.setLastUpdated(now);
                    lock.setAcquiredAt(LocalDateTime.now());
                    
                    leaderLockRepository.save(lock);
                    this.isLeader = true;
                    
                    log.info("✅ Acquired/renewed leadership lease");
                } else {
                    // Another pod still holds valid lease
                    this.isLeader = false;
                    log.debug("❌ Another pod ({}) still holds leadership", lock.getHolder());
                }
            } else {
                this.isLeader = false;
                log.debug("Failed to acquire leader lock");
            }
        } catch (PessimisticLockException e) {
            this.isLeader = false;
            log.debug("Lock is held by another pod, will retry");
        } catch (Exception e) {
            this.isLeader = false;
            log.error("Error renewing leadership", e);
        }
    }
    
    private void executeJobIfLeader() {
        if (isLeader) {
            try {
                jobService.executeDailyScheduledJob();
            } catch (Exception e) {
                log.error("Job execution failed", e);
            }
        }
    }
}
```

### ✅ Advantages
- **Simplest to understand** - Just database locking
- **Existing infrastructure** - Use your primary DB
- **Easy debugging** - Query the lock table directly
- **Strong consistency** - Database provides ACID guarantees
- **Cost-effective** - No extra services to maintain

### ❌ Disadvantages
- **Database becomes bottleneck** - Every pod hitting DB constantly
- **Latency** - Round-trip to DB slows election
- **Single point of failure** - If DB is down, no leader election
- **Not ideal for scale** - N pods = N lock attempts per cycle

---

## 🏗️ Approach 4: Redis Pub/Sub with Lease

**Best for**: High-speed coordination, in-memory state  
**Production Readiness**: ⭐⭐⭐⭐  
**Complexity**: Medium

### How It Works

Use Redis SET with TTL + Pub/Sub channels for notifications. Fast + observable.

### Block Diagram

```
┌────────────────────────────────────────────────────────┐
│     Kubernetes Pods (3 replicas)                       │
├────────────────────────────────────────────────────────┤
│                                                         │
│  Pod 1              Pod 2              Pod 3            │
│  ┌────────┐         ┌────────┐         ┌────────┐      │
│  │SETNX   │         │SETNX   │         │SETNX   │      │
│  │Lock    │         │Lock    │         │Lock    │      │
│  │EX 30   │         │EX 30   │         │EX 30   │      │
│  │        │         │        │         │        │      │
│  │SUB     │         │SUB     │         │SUB     │      │
│  │election│         │election│         │election│      │
│  └───┬────┘         └───┬────┘         └───┬────┘      │
│      │                  │                  │            │
│      │   TCP connect    │  TCP connect    │            │
│      └──────────────────┼──────────────────┘            │
│                         │                              │
│          ┌──────────────▼────────────────┐             │
│          │       Redis Instance          │             │
│          │                               │             │
│          │ ┌─────────────────────────┐   │             │
│          │ │ KEY: job:leader:lock    │   │             │
│          │ │ VALUE: pod-1            │   │             │
│          │ │ TTL: 30s                │   │             │
│          │ │ (auto-deletes)          │   │             │
│          │ └─────────────────────────┘   │             │
│          │                               │             │
│          │ ┌─────────────────────────┐   │             │
│          │ │ CHANNEL: election       │   │             │
│          │ │ SUBSCRIBERS: 3          │   │             │
│          │ └─────────────────────────┘   │             │
│          │                               │             │
│          │ PUBLISH: leader=pod-1         │             │
│          │ → Pods 2,3 notified instantly │             │
│          └───────────────────────────────┘             │
│                                                         │
└────────────────────────────────────────────────────────┘

Pod 1 holds lock (TTL 30s) + publishes election message
Others listen & wait for expiry (faster than polling)
```

### Production Code

```java
@Component
@Slf4j
public class RedisLeaderElectionWithPubSub {
    
    @Autowired
    private RedisTemplate<String, String> redisTemplate;
    
    @Autowired
    private RedisConnectionFactory connectionFactory;
    
    @Autowired
    private DistributedJobService jobService;
    
    private static final String LOCK_KEY = "job:leader:lock";
    private static final String ELECTION_CHANNEL = "job:election:events";
    private static final long LOCK_DURATION = 30; // seconds
    private static final long RENEW_INTERVAL = 10; // seconds
    
    private String podName;
    private boolean isLeader = false;
    
    @PostConstruct
    public void init() {
        this.podName = System.getenv("HOSTNAME");
        
        // Subscribe to election events
        subscribeToElectionChannel();
        
        // Start leadership renewal
        ScheduledExecutorService executor = Executors.newScheduledThreadPool(2);
        executor.scheduleAtFixedRate(
            this::renewLeadership,
            0,
            RENEW_INTERVAL,
            TimeUnit.SECONDS
        );
        
        executor.scheduleAtFixedRate(
            this::executeJobIfLeader,
            0,
            2,
            TimeUnit.SECONDS
        );
    }
    
    private void subscribeToElectionChannel() {
        Thread subThread = new Thread(() -> {
            try {
                RedisConnection connection = connectionFactory.getConnection();
                connection.subscribe((message, pattern) -> {
                    String event = new String(message);
                    log.info("📬 Election event: {}", event);
                    
                    // Parse: format = "leader=pod-1,version=5"
                    String[] parts = event.split(",");
                    String newLeader = parts[0].split("=")[1];
                    
                    if (!newLeader.equals(podName)) {
                        this.isLeader = false;
                        log.info("✅ New leader elected: {}", newLeader);
                    }
                },
                ELECTION_CHANNEL.getBytes()
                );
            } catch (Exception e) {
                log.error("Error subscribing to election channel", e);
            }
        });
        
        subThread.setDaemon(true);
        subThread.setName("redis-subscription-thread");
        subThread.start();
    }
    
    private void renewLeadership() {
        try {
            String leaderValue = String.format("%s:%d", podName, System.currentTimeMillis());
            
            // Atomic SET with NX (only if not exists) + expiry
            Boolean acquired = redisTemplate.opsForValue().setIfAbsent(
                LOCK_KEY,
                leaderValue,
                Duration.ofSeconds(LOCK_DURATION)
            );
            
            if (Boolean.TRUE.equals(acquired)) {
                this.isLeader = true;
                log.info("✅ Acquired leadership");
                
                // Publish election event
                publishElectionEvent();
                
            } else {
                // Check who's leading
                String currentLeader = redisTemplate.opsForValue().get(LOCK_KEY);
                if (currentLeader != null) {
                    String leaderPodName = currentLeader.split(":")[0];
                    this.isLeader = podName.equals(leaderPodName);
                    log.debug("Current leader: {}", leaderPodName);
                }
            }
        } catch (Exception e) {
            log.error("Error renewing leadership", e);
            this.isLeader = false;
        }
    }
    
    private void publishElectionEvent() {
        try {
            String event = String.format("leader=%s,timestamp=%d,version=%d",
                podName,
                System.currentTimeMillis(),
                1
            );
            
            Long subscribers = redisTemplate.convertAndSend(ELECTION_CHANNEL, event);
            log.info("📤 Published election event to {} subscribers", subscribers);
        } catch (Exception e) {
            log.error("Error publishing election event", e);
        }
    }
    
    private void executeJobIfLeader() {
        if (isLeader) {
            try {
                jobService.executeDailyScheduledJob();
            } catch (Exception e) {
                log.error("Job execution failed", e);
            }
        }
    }
}
```

### ✅ Advantages
- **Fast** - In-memory operations, microsecond latency
- **Observable** - Pub/Sub shows exact election moments
- **Simple** - Build on existing Redis infrastructure
- **Responsive** - Pub/Sub = instant notification vs polling

### ❌ Disadvantages
- **Redis dependency** - Another critical service
- **Memory overhead** - Stores lock for all jobs
- **Expiry timing** - Depends on Redis TTL accuracy
- **No durability** - Loss of Redis = loss of leadership state

---

## 🏗️ Approach 5: Message Queue-Based Coordination (Kafka/SQS)

**Best for**: Loosely coupled systems, event-driven architecture  
**Production Readiness**: ⭐⭐⭐  
**Complexity**: High

### How It Works

Submit job to queue; single consumer (pod) processes it. Queue itself enforces "only once".

### Block Diagram

```
┌────────────────────────────────────────────────────────────┐
│             Kubernetes Pods (3 replicas)                   │
├────────────────────────────────────────────────────────────┤
│                                                              │
│  Pod 1          Pod 2           Pod 3                       │
│  ┌────────┐     ┌────────┐      ┌────────┐                 │
│  │Consumer│     │Consumer│      │Consumer│                 │
│  │Group:  │     │Group:  │      │Group:  │                 │
│  │job-job │     │job-job │      │job-job │                 │
│  └───┬────┘     └───┬────┘      └───┬────┘                 │
│      │              │               │                       │
│      │ POLL         │ POLL          │ POLL                  │
│      │ MESSAGES     │ MESSAGES      │ MESSAGES              │
│      └──────────────┼───────────────┘                       │
│                     │                                       │
│          ┌──────────▼────────────────┐                       │
│          │   Kafka Cluster           │                       │
│          │   (or SQS Queue)          │                       │
│          │                           │                       │
│          │ ┌─────────────────────┐   │                       │
│          │ │ TOPIC: daily-job    │   │                       │
│          │ │ Partitions: 1       │   │   ← KEY: only 1       │
│          │ │                     │   │     partition per job  │
│          │ │ Message:            │   │     guarantees order   │
│          │ │ {                   │   │     & single consumer  │
│          │ │   id: job-123,      │   │                       │
│          │ │   type: daily-rep   │   │                       │
│          │ │   timestamp: T1,    │   │                       │
│          │ │   idempotency_key   │   │                       │
│          │ │ }                   │   │                       │
│          │ └─────────────────────┘   │                       │
│          │                           │                       │
│          │ Consumer offset: [Pol-1] │                       │
│          │ Only 1 pod reads offset  │                       │
│          └───────────────────────────┘                       │
│                                                              │
└────────────────────────────────────────────────────────────┘

Job queued → One pod consumes → Offset tracked
If pod crashes → Another pod reads from offset → Retry
Parallelism via multiple topics/partitions
```

### Production Code (Spring Boot + Kafka)

```java
@Component
@Slf4j
public class KafkaJobSchedulingCoordinator {
    
    @Autowired
    private KafkaTemplate<String, JobMessage> kafkaTemplate;
    
    @Autowired
    private DistributedJobService jobService;
    
    private static final String DAILY_JOB_TOPIC = "daily-job-scheduler";
    private static final String CONSUMER_GROUP = "job-scheduler-group";
    
    @Scheduled(cron = "0 0 2 * * *") // 2:00 AM daily
    public void scheduleDailyJob() {
        try {
            String jobId = UUID.randomUUID().toString();
            JobMessage message = JobMessage.builder()
                .jobId(jobId)
                .jobType(JobType.DAILY_REPORT)
                .timestamp(LocalDateTime.now())
                .idempotencyKey(jobId + ":" + LocalDate.now()) // For deduplication
                .build();
            
            // Send to single partition (ensures order + single consumer)
            kafkaTemplate.send(DAILY_JOB_TOPIC, "daily-report", message);
            log.info("📤 Scheduled job to Kafka: {}", jobId);
            
        } catch (Exception e) {
            log.error("Error scheduling job to Kafka", e);
        }
    }
    
    @KafkaListener(
        topics = DAILY_JOB_TOPIC,
        groupId = CONSUMER_GROUP,
        concurrency = "1" // Only 1 consumer processes messages
    )
    public void consumeJobMessage(JobMessage message) {
        try {
            String idempotencyKey = message.getIdempotencyKey();
            
            // Check if already processed (database deduplication)
            if (jobService.isJobAlreadyProcessed(idempotencyKey)) {
                log.info("⏭️  Job already processed (idempotency): {}", idempotencyKey);
                return;
            }
            
            log.info("▶️  Processing job: {}", message.getJobId());
            jobService.executeDailyScheduledJob();
            
            // Mark as processed
            jobService.recordJobExecution(idempotencyKey);
            
            log.info("✅ Job completed: {}", message.getJobId());
            
        } catch (Exception e) {
            log.error("Error processing job message", e);
            // Kafka will retry with exponential backoff
            throw new RuntimeException("Job processing failed", e);
        }
    }
}

// Kafka Configuration
@Configuration
public class KafkaConfig {
    
    @Bean
    public AdminClient kafkaAdminClient(KafkaProperties properties) {
        return AdminClient.create(properties.buildAdminProperties());
    }
    
    @Bean
    public NewTopic dailyJobTopic() {
        return TopicBuilder.name("daily-job-scheduler")
            .partitions(1)           // ← CRITICAL: 1 partition ensures single consumer
            .replicas(3)             // For HA
            .compact()               // Clean up old messages
            .build();
    }
    
    @Bean
    public ConsumerFactory<String, JobMessage> consumerFactory() {
        Map<String, Object> configProps = new HashMap<>();
        configProps.put(ConsumerConfig.BOOTSTRAP_SERVERS_CONFIG, "kafka:9092");
        configProps.put(ConsumerConfig.GROUP_ID_CONFIG, "job-scheduler-group");
        configProps.put(ConsumerConfig.AUTO_OFFSET_RESET_CONFIG, "earliest");
        configProps.put(ConsumerConfig.ENABLE_AUTO_COMMIT_CONFIG, true);
        configProps.put(ConsumerConfig.AUTO_COMMIT_INTERVAL_MS_CONFIG, 1000);
        configProps.put(ConsumerConfig.MAX_POLL_RECORDS_CONFIG, 1);
        
        return new DefaultKafkaConsumerFactory<>(configProps);
    }
    
    @Bean
    public ConcurrentKafkaListenerContainerFactory<String, JobMessage> kafkaListenerContainerFactory() {
        ConcurrentKafkaListenerContainerFactory<String, JobMessage> factory =
            new ConcurrentKafkaListenerContainerFactory<>();
        factory.setCommonErrorHandler(errorHandler());
        return factory;
    }
    
    private CommonErrorHandler errorHandler() {
        ExponentialBackoffWithMaxRetriesStrategy strategy = 
            new ExponentialBackoffWithMaxRetriesStrategy(3);
        
        DefaultErrorHandler errorHandler = new DefaultErrorHandler(strategy);
        errorHandler.addNotRetryableExceptions(DatabaseConstraintException.class);
        
        return errorHandler;
    }
}
```

**Job message DTO**:
```java
@Data
@Builder
@NoArgsConstructor
@AllArgsConstructor
public class JobMessage {
    private String jobId;
    private JobType jobType;
    private LocalDateTime timestamp;
    private String idempotencyKey; // For at-least-once → exactly-once
    private Map<String, String> metadata;
}

public enum JobType {
    DAILY_REPORT,
    HOURLY_CLEANUP,
    WEEKLY_RECONCILIATION
}
```

### ✅ Advantages
- **Decoupled** - Jobs exist independently of pods
- **Scalable** - Add more partitions for parallelism
- **Observable** - Kafka UI shows exactly what's happening
- **Resilient** - Broker replication + consumer offset tracking
- **Ordering** - Single partition guarantees order

### ❌ Disadvantages
- **Complex** - Requires Kafka infrastructure & knowledge
- **Overhead** - Message serialization/deserialization
- **Not immediate** - Message latency (milliseconds) vs in-memory
- **Consumer lag monitoring** - Need extra observability

---

## 📊 Comparison Matrix

| Aspect | K8s Lease | Consul/etcd | Database Lock | Redis Lease | Kafka |
|--------|-----------|------------|---------------|-------------|-------|
| **Native K8s** | ⭐⭐⭐⭐⭐ | ⭐ | ⭐⭐ | ⭐⭐ | ⭐ |
| **Learning Curve** | Medium | Hard | Easy | Medium | Hard |
| **Latency** | 100-500ms | 50-200ms | 50-300ms | <10ms | 1-100ms |
| **Failure Recovery** | 15-30s | 5-15s | 10-30s | 10-30s | Offset tracking |
| **Scalability** | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ |
| **Dependencies** | K8s API | Consul/etcd | DB | Redis | Kafka |
| **Multi-cluster** | ⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐ | ⭐⭐ | ⭐⭐⭐⭐ |
| **Cost** | Free | Medium | Free | Low | Medium |
| **Production Ready** | ✅ | ✅ | ✅ | ✅ | ✅ |

---

## 🎯 Senior-Level Interview Talking Points

### Key Insight #1: Consistency vs. Availability Trade-off
```
❌ WRONG: "We just use K8s Lease—it's the best"

✅ CORRECT: "We chose K8s Lease because our organization 
is cloud-native on K8s. It trades 15-30s failover time 
for built-in integration. If we needed multi-cluster 
coordination, we'd use Consul."
```

### Key Insight #2: Failure Scenarios
```
Q: "What if the leader pod crashes mid-job?"

✅ CORRECT ANSWER:
- Lease expires in 15-30s
- Another pod detects expiry
- That pod acquires lease and becomes new leader
- NEW LEADER DOES NOT RE-EXECUTE the job (idempotency!)
- Use database idempotency key + version to track what ran

IMPLEMENTATION:
1. Before job starts → write idempotency record to DB
2. Run job
3. Mark idempotency record as completed
4. Next leader checks: "Was this already done?" → YES → skip
```

### Key Insight #3: Split-Brain Prevention
```
Q: "How do we prevent two pods thinking they're both leaders?"

✅ CORRECT ANSWER:
- Kubernetes Lease uses ETCD Compare-And-Set (CAS)
- Only one pod can successfully WRITE the lease at a time
- Others get "Conflict" (409) on write
- Polling leader = no refresh = lease expires
- New leader = atomic acquisition via CAS

Split-brain CANNOT happen because etcd enforces atomicity.
```

### Key Insight #4: Observability
```
What to monitor:
1. Who is currently the leader?
   SELECT * FROM leader_lock; (DB approach)
   kubectl get lease job-scheduler-lease (K8s approach)

2. How often does leadership change?
   > 1 per hour = network instability
   < 1 per week = good stability

3. How long from failure to new leader?
   Target: < 30 seconds
   > 2 min = investigate why
```

---

## 🏆 Production Checklist

Before using any approach in production:

- [ ] **Idempotency**: Job can safely run twice without issues
- [ ] **Monitoring**: Track who's leading and election frequency
- [ ] **Testing**: Simulate pod crashes every hour
- [ ] **Documentation**: New team members understand the approach
- [ ] **Backup**: If leader gets stuck, manual override exists
- [ ] **Timeout**: Job has a maximum execution time
- [ ] **Alerting**: Team notified if leader not electing
- [ ] **Disaster Recovery**: What happens if coordination service dies?

---

## 🎓 Follow-Up Questions You'll Face

### Q1: "What if the leader pod goes into a long garbage collection (GC pause)? Can it still hold the lease?

**Answer**:
```
YES - this is actually a problem. During GC pause (milliseconds to seconds):
- Pod is frozen (can't run code)
- Redis/etcd lease still valid
- Next pod thinks leader is running (but it's paused)

SOLUTION: Implement a "watchdog" thread that monitors if the pod is responsive.
If GC pause > threshold, intentionally release the lease.

Spring Boot + micrometer example:
metrics.timer.jvm.gc.pause (captures GC pause time)
if gc_pause > 5s: release_lease()
```

### Q2: "How do you ensure a job doesn't run twice if leadership changes mid-execution?"

**Answer**:
```
Idempotency key + database deduplication.

FLOW:
1. Pod 1 acquires lease
2. Writes: INSERT report_execution(date=2026-02-28, status=RUNNING, pod=pod-1)
3. Executes job
4. Updates: status=COMPLETED

5. IF Pod 1 crashes here → Lease expires
6. Pod 2 acquires lease
7. Queries: SELECT * FROM report_execution WHERE date=2026-02-28
8. Finds COMPLETED status → SKIPS re-execution

KEY: Idempotency key = (date, job_type, version)
Ensures exactly-once-like behavior even with retries.
```

### Q3: "Should we use a single pod (Deployment replicas=1) instead of leader election?"

**Answer**:
```
❌ NO - this defeats the purpose of Kubernetes.

Reasons:
1. Single pod = single point of failure
2. Pod restarts = job skipped that interval
3. No rolling updates possible
4. Violates cloud-native principles

Leader election with replicas=3:
- If 1 pod dies → 2 others + auto-restart
- New leader elected in 20s
- Scheduling continues uninterrupted
```

### Q4: "How does this scale to thousands of jobs?"

**Answer**:
```
Different jobs → different lock keys/leases.

ARCHITECTURE:
- Job 1 (daily-report) → leader-election for Job 1
- Job 2 (hourly-cleanup) → leader-election for Job 2
- Job N → separate coordination

Redis: O(1) per job → scales linearly
K8s Lease: N leases in etcd → still scales well

Monitoring becomes critical:
- Which jobs have elected leaders?
- Which jobs are stuck in election?
```

---

## 📚 Key Takeaway for Interviews

When asked about distributed scheduling on Kubernetes:

1. **Start with the problem**: "Multiple pods would execute the same job"
2. **Present 3+ approaches**: Lease API, Redis, Database, Kafka
3. **Compare tradeoffs**: Consistency vs. Availability vs. Complexity
4. **Pick one confidently**: "I'd use K8s Lease because..."
5. **Explain failure recovery**: "If leader crashes, here's exactly what happens..."
6. **Show idempotency**: "Even if job runs twice, it's safe because..."
7. **Discuss monitoring**: "We track leadership elections and alert on anomalies"

This demonstrates **production thinking** and **architectural maturity** expected at senior levels.

---

## 🔗 Related Topics to Deep Dive

- [Distributed Transactions & Consensus](../distributed-scheduler-locking.md)
- [Kubernetes StatefulSets vs. Deployments](../eks-security-guide.md)
- [Idempotency Patterns](./03-Failure-Handling-and-Idempotency.md)
- [Observability for Distributed Systems](#)

---

**Last Updated**: February 2026  
**Author**: System Design Interview Prep  
**Level**: Senior+ (5+ years)
