# How to Implement Leader Election in Kubernetes for Distributed Jobs

> **Interview Question**: "How do you ensure only one pod executes a scheduled job in Kubernetes?"
> **Level**: Senior Engineer (5+ Years)
> **Companies**: Google, Uber, Spotify, Airbnb (Kubernetes-heavy)

---

## 📋 Quick Navigation

### 🎯 Main Documents

1. **[06-Kubernetes-Leader-Election-Production.md](./06-Kubernetes-Leader-Election-Production.md)** ⭐ START HERE
   - Complete guide with 5 production approaches
   - Kubernetes Lease API (most common)
   - External coordination (Consul, etcd)
   - Database locks
   - Redis Pub/Sub
   - Message Queue pattern
   - Full code examples for each

2. **[07-Leader-Election-Interview-Cheat-Sheet.md](./07-Leader-Election-Interview-Cheat-Sheet.md)**
   - Perfect 2-minute answer
   - Quick comparison table
   - Minimal code snippets
   - Lightning Q&A

3. **[K8S-LEADER-ELECTION-COMPLETE-SUMMARY.md](./K8S-LEADER-ELECTION-COMPLETE-SUMMARY.md)**
   - Executive summary
   - Decision matrix
   - When to use which approach

---

## 🎯 The Interview Question

**Interviewer asks**:
> "You have a Kubernetes deployment with 10 replicas. How do you ensure a scheduled job runs only once across all pods?"

**What they're testing**:
- ✅ Understanding of distributed coordination
- ✅ Knowledge of Kubernetes primitives
- ✅ Production failure handling
- ✅ Trade-off analysis
- ✅ Scale thinking

---

## ⚡ Quick Answer (30 seconds)

> "I use **Kubernetes Lease API** for leader election. All pods compete for a lease stored in etcd. The winner becomes leader and executes jobs. The lease has a TTL (15-30 seconds). The leader continuously renews the lease while alive. If the leader crashes, the lease expires, and another pod becomes leader. This provides automatic failover with strong consistency guarantees from etcd's Raft consensus."

---

## 🏗️ Architecture Overview

```
┌──────────────────────────────────────────────────────┐
│           KUBERNETES LEADER ELECTION                 │
├──────────────────────────────────────────────────────┤
│                                                      │
│  ┌─────────┐  ┌─────────┐  ┌─────────┐             │
│  │ Pod 1   │  │ Pod 2   │  │ Pod 3   │             │
│  │ (Leader)│  │Follower │  │Follower │             │
│  └────┬────┘  └────┬────┘  └────┬────┘             │
│       │            │            │                    │
│       └────────────┼────────────┘                   │
│                    ▼                                 │
│          ┌──────────────────┐                       │
│          │  Lease Object    │                       │
│          │  (etcd-backed)   │                       │
│          │  holder: pod-1   │                       │
│          │  duration: 15s   │                       │
│          └──────────────────┘                       │
│                    ▲                                 │
│                    │ Renew every 10s                │
│                    │                                 │
│          ┌─────────┴────────┐                       │
│          │  Pod 1 (Leader)  │                       │
│          │  Runs all jobs   │                       │
│          └──────────────────┘                       │
│                                                      │
│  Failover: Pod 1 crashes → Lease expires →         │
│            Pod 2 becomes leader in ~15-30s          │
│                                                      │
└──────────────────────────────────────────────────────┘
```

---

## 🔑 5 Production Approaches

### Comparison Table

| Approach | Best For | Complexity | Consistency | Failover Time |
|----------|----------|------------|-------------|---------------|
| **K8s Lease API** | Cloud-native | Medium | Strong (etcd) | 15-30s |
| **Consul/etcd** | Multi-cluster | High | Strong (Raft) | 10-20s |
| **Database Lock** | Existing DB | Low | Strong (ACID) | 5-15s |
| **Redis Lease** | Fast failover | Medium | Weak (AP) | 5-10s |
| **Kafka Queue** | Event-driven | High | Strong | 30-60s |

### When to Use What

```
┌──────────────────────────────────────────────────┐
│         DECISION TREE                            │
├──────────────────────────────────────────────────┤
│                                                  │
│  Running on Kubernetes?                         │
│    │                                             │
│    ├─ Yes → Use K8s Lease API ✅                │
│    │        (Native, no extra infra)            │
│    │                                             │
│    └─ No → Need multi-cluster?                  │
│            │                                     │
│            ├─ Yes → Use Consul/etcd ✅          │
│            │                                     │
│            └─ No → Have existing DB?            │
│                    │                             │
│                    ├─ Yes → Use DB Lock ✅      │
│                    │                             │
│                    └─ No → Use Redis ✅         │
│                                                  │
└──────────────────────────────────────────────────┘
```

---

## 💻 Code Example (Kubernetes Lease API)

```java
@Component
@Slf4j
public class KubernetesLeaderElection {

    private final LeaderElectionConfig config = new LeaderElectionConfigBuilder()
        .withName("job-scheduler-leader")
        .withNamespace("default")
        .withLeaseDuration(Duration.ofSeconds(15))
        .withRenewDeadline(Duration.ofSeconds(10))
        .withRetryPeriod(Duration.ofSeconds(2))
        .build();

    private volatile boolean isLeader = false;

    @PostConstruct
    public void startLeaderElection() {
        LeaderElector elector = new LeaderElector(config);

        elector.run(
            () -> {
                log.info("Became leader");
                isLeader = true;
            },
            () -> {
                log.info("Lost leadership");
                isLeader = false;
            }
        );
    }

    @Scheduled(cron = "0 0 2 * * *")
    public void runJob() {
        if (!isLeader) {
            log.info("Not leader, skipping");
            return;
        }

        log.info("Leader executing job");
        // Execute job
    }
}
```

---

## 🎓 Interview Q&A

### Q1: What if the leader pod crashes?

**A**: "The lease has a TTL of 15-30 seconds. When the leader crashes, it stops renewing the lease. After TTL expires, another pod acquires the lease and becomes leader. Failover is automatic, no manual intervention needed."

### Q2: Can two pods think they're leader simultaneously (split-brain)?

**A**: "No, etcd uses Raft consensus for strong consistency. Lease acquisition is atomic. Only one pod can hold the lease at any time. This is guaranteed by etcd's CP (Consistent + Partition-tolerant) properties."

### Q3: Why not just use Redis for this?

**A**: "Redis is AP (Available + Partition-tolerant), prioritizing availability over consistency. In network partitions, Redis can have split-brain. For critical jobs, I prefer Kubernetes Lease API backed by etcd which is CP. However, Redis works fine if you design jobs to be idempotent."

### Q4: How do you test leader election?

**A**: "Integration tests using Kind (Kubernetes in Docker). Create deployment with 3 replicas, verify only one pod executes jobs. Then kill the leader pod with `kubectl delete pod`, verify failover happens within expected time, and new leader takes over."

### Q5: What metrics do you monitor?

**A**:
- Leadership transitions (should be rare)
- Time to elect new leader (target: <30s)
- Job execution count (should be 1 per trigger)
- Failed lease renewals (indicates issues)

---

## ✅ Interview Success Checklist

Before your interview, make sure you can:

- [ ] Explain leader election in 30 seconds
- [ ] Draw architecture diagram
- [ ] List pros/cons of K8s Lease vs Redis vs Database
- [ ] Explain how failover works
- [ ] Describe split-brain prevention
- [ ] Write basic leader election code
- [ ] Answer "What if leader crashes?"
- [ ] Discuss when NOT to use leader election

---

## 📚 Study Plan

### 30-Minute Prep (Interview Tomorrow)
1. Read this README (5 min)
2. Skim main document sections on K8s Lease API (10 min)
3. Memorize code example (5 min)
4. Review cheat sheet Q&A (10 min)

### 2-Hour Deep Prep
1. Read complete main document (45 min)
2. Understand all 5 approaches (30 min)
3. Practice drawing diagrams (15 min)
4. Review failure scenarios (15 min)
5. Practice explaining out loud (15 min)

---

## 🚀 Key Takeaways

1. **K8s Lease API** is the standard for Kubernetes deployments
2. **etcd** provides strong consistency guarantees
3. **TTL-based** failover is automatic (no heartbeat needed)
4. **Idempotency** is still required (distributed systems can't guarantee exactly-once)
5. **Failover time** is 15-30 seconds (acceptable for most jobs)

---

## 📖 Related Topics

- [Distributed Job Scheduling](../Distributed-Job-Scheduling/) - General distributed scheduling (parent topic)
- Database sharding
- Distributed locks
- CAP theorem

---

**Start Reading**: [06-Kubernetes-Leader-Election-Production.md](./06-Kubernetes-Leader-Election-Production.md)

**Quick Reference**: [07-Leader-Election-Interview-Cheat-Sheet.md](./07-Leader-Election-Interview-Cheat-Sheet.md)

---

**Good luck with your interview!** 🎉
