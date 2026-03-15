# Kubernetes Leader Election Approaches: Visual Reference

This page contains all diagrams for Kubernetes leader election in production.

## 1️⃣ Kubernetes Native Lease API

Best for: Cloud-native teams, K8s-only infrastructure

```
┌────────────────────────────────────────────────────────────────────────┐
│                      KUBERNETES NATIVE LEASE API                       │
├────────────────────────────────────────────────────────────────────────┤
│                                                                        │
│     ┌─────────────┐        ┌─────────────┐        ┌─────────────┐   │
│     │   Pod 1     │        │   Pod 2     │        │   Pod 3     │   │
│     │ Watch Lease │        │ Watch Lease │        │ Watch Lease │   │
│     └──────┬──────┘        └──────┬──────┘        └──────┬──────┘   │
│            │                      │                       │           │
│            └──────────────────────┼───────────────────────┘           │
│                                   │                                   │
│                                   ▼                                   │
│                     ┌──────────────────────────────┐                  │
│                     │   Kubernetes Lease API       │                  │
│                     │      (etcd Backed)           │                  │
│                     └──────────────┬───────────────┘                  │
│                                    │                                  │
│                                    ▼                                  │
│                     ┌──────────────────────────────┐                  │
│                     │      Lease State:            │                  │
│                     │  holder: Pod 1               │                  │
│                     │  ttl: 15s                    │                  │
│                     │  version: 42                 │                  │
│                     └──────────────┬───────────────┘                  │
│                                    │                                  │
│                                    ▼                                  │
│                     ┌──────────────────────────────┐                  │
│                     │   Pod 1 Renews Every 5s      │                  │
│                     └──────────────┬───────────────┘                  │
│                                    │                                  │
│                                    ▼                                  │
│                     ┌──────────────────────────────┐                  │
│                     │ ✅ Pod 1 Holds Leadership    │                  │
│                     └──────────────┬───────────────┘                  │
│                                    │                                  │
│                                    ▼                                  │
│                     ┌──────────────────────────────┐                  │
│                     │  Executes Scheduled Job      │                  │
│                     └──────────────────────────────┘                  │
│                                                                        │
└────────────────────────────────────────────────────────────────────────┘
```

**Key Points:**
- Uses etcd (built-in with K8s)
- Lease renewal = automatic re-election trigger
- 15-30s failover time
- Only 1 pod can hold lease (atomic CAS)

---

## 2️⃣ Consul/etcd (External Coordination)

Best for: Multi-cluster deployments, cross-datacenter failover

```
┌────────────────────────────────────────────────────────────────────────┐
│              CONSUL/ETCD EXTERNAL COORDINATION                         │
├────────────────────────────────────────────────────────────────────────┤
│                                                                        │
│   ┌─────────────────────────────────────────────────────────────┐    │
│   │         Kubernetes Clusters (Cluster 1 & 2)                 │    │
│   │                                                             │    │
│   │  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐  │    │
│   │  │ Pod 1-1  │  │ Pod 1-2  │  │ Pod 2-1  │  │ Pod 2-2  │  │    │
│   │  └─────┬────┘  └─────┬────┘  └─────┬────┘  └─────┬────┘  │    │
│   └────────┼─────────────┼─────────────┼─────────────┼────────┘    │
│            │             │             │             │              │
│            └─────────────┼─────────────┼─────────────┘              │
│                          │             │                            │
│                          ▼             ▼                            │
│              ┌──────────────────────────────────┐                   │
│              │      ConsulClient                │                   │
│              │  Register + Lease Management     │                   │
│              └──────────────┬───────────────────┘                   │
│                             │                                       │
│                             ▼                                       │
│              ┌──────────────────────────────────┐                   │
│              │      Consul Cluster              │                   │
│              │   (Cross-Datacenter)             │                   │
│              └──────────────┬───────────────────┘                   │
│                             │                                       │
│                             ▼                                       │
│              ┌──────────────────────────────────┐                   │
│              │  Distributed Leadership:         │                   │
│              │  Single Leader Across All        │                   │
│              │  Clusters                        │                   │
│              └──────────────┬───────────────────┘                   │
│                             │                                       │
│                             ▼                                       │
│              ┌──────────────────────────────────┐                   │
│              │   Leader Pod Executes Job        │                   │
│              └──────────────────────────────────┘                   │
│                                                                      │
│  ┌───────────────────────────────────────────────┐                  │
│  │  Other Pods: Watch Consul, Wait for Expiry   │                  │
│  └───────────────────────────────────────────────┘                  │
│                                                                      │
└──────────────────────────────────────────────────────────────────────┘
```

**Key Points:**
- External single source of truth
- Survives Kubernetes cluster failure
- Single leader across multiple clusters
- 5-15s failover (faster than K8s)

---

## 3️⃣ Database-Backed Leader Lock

Best for: Teams with strong DB infrastructure (PostgreSQL, MySQL)

```
┌────────────────────────────────────────────────────────────────────────┐
│                  DATABASE-BACKED LEADER LOCK                           │
├────────────────────────────────────────────────────────────────────────┤
│                                                                        │
│     ┌──────────┐        ┌──────────┐        ┌──────────┐             │
│     │  Pod 1   │        │  Pod 2   │        │  Pod 3   │             │
│     └─────┬────┘        └─────┬────┘        └─────┬────┘             │
│           │                   │                   │                   │
│           │                   │                   │                   │
│           │  SELECT...FOR UPDATE                  │                   │
│           └───────────────────┼───────────────────┘                   │
│                               │                                       │
│                               ▼                                       │
│                   ┌────────────────────────┐                          │
│                   │   PostgreSQL           │                          │
│                   │   leader_lock Table    │                          │
│                   └───────────┬────────────┘                          │
│                               │                                       │
│                               ▼                                       │
│                   ┌────────────────────────┐                          │
│                   │   Row Lock:            │                          │
│                   │   Pod 1 Holds Lock     │                          │
│                   └───────────┬────────────┘                          │
│                               │                                       │
│      ┌────────────────────────┴────────────────────────┐             │
│      │  Pod 2, Pod 3: Wait for Lock (blocked)          │             │
│      └──────────────────────────────────────────────────┘             │
│                               │                                       │
│                               ▼                                       │
│                   ┌────────────────────────┐                          │
│                   │   Pod 1: Leader        │                          │
│                   │   • Executes Job       │                          │
│                   │   • Updates            │                          │
│                   │     last_updated       │                          │
│                   └───────────┬────────────┘                          │
│                               │                                       │
│                               ▼                                       │
│                   ┌────────────────────────┐                          │
│                   │   Release Lock         │                          │
│                   │   (COMMIT)             │                          │
│                   └───────────┬────────────┘                          │
│                               │                                       │
│                               ▼                                       │
│                   ┌────────────────────────┐                          │
│                   │   Pod 2 or 3 Acquires  │                          │
│                   │   Lock - Now Leader    │                          │
│                   └────────────────────────┘                          │
│                                                                        │
└────────────────────────────────────────────────────────────────────────┘
```

**Key Points:**
- Uses ACID guarantees of your DB
- Pessimistic locking (blocks others)
- 10-30s failover via TTL polling
- Simplest to debug (query the lock table)

---

## 4️⃣ Redis Pub/Sub with Lease

Best for: High-speed coordination, existing Redis infrastructure

```
┌────────────────────────────────────────────────────────────────────────┐
│                    REDIS PUB/SUB WITH LEASE                            │
├────────────────────────────────────────────────────────────────────────┤
│                                                                        │
│     ┌──────────┐        ┌──────────┐        ┌──────────┐             │
│     │  Pod 1   │        │  Pod 2   │        │  Pod 3   │             │
│     └─────┬────┘        └─────┬────┘        └─────┬────┘             │
│           │                   │                   │                   │
│           │ SETNX Lock        │ SUB election      │ SUB election      │
│           │ EX 30s            │ channel           │ channel           │
│           │                   │                   │                   │
│           ▼                   ▼                   ▼                   │
│     ┌─────────────────────────────────────────────────────┐           │
│     │              Redis Instance                         │           │
│     │  ┌──────────────────────────────────────┐           │           │
│     │  │  Key: job:lock                       │           │           │
│     │  │  Value: pod-1                        │           │           │
│     │  │  TTL: 30s                            │           │           │
│     │  └──────────────────────────────────────┘           │           │
│     │                                                     │           │
│     │  ┌──────────────────────────────────────┐           │           │
│     │  │  Channel: election                   │           │           │
│     │  │  Watchers: Pod2, Pod3                │           │           │
│     │  └──────────────────────────────────────┘           │           │
│     └─────────────────────────────────────────────────────┘           │
│                                                                        │
│           │                   │                   │                   │
│      ✅ SUCCESS          ❌ FAIL             ❌ FAIL                   │
│           │                   │                   │                   │
│           ▼                   ▼                   ▼                   │
│     ┌──────────┐        ┌──────────┐        ┌──────────┐             │
│     │  Pod 1:  │        │  Pod 2:  │        │  Pod 3:  │             │
│     │  Leader  │        │  Standby │        │  Standby │             │
│     └─────┬────┘        └──────────┘        └──────────┘             │
│           │                                                           │
│           ▼                                                           │
│     ┌──────────┐                                                      │
│     │ Executes │                                                      │
│     │   Job    │                                                      │
│     └─────┬────┘                                                      │
│           │                                                           │
│           ▼                                                           │
│     ┌────────────────────────┐                                        │
│     │ PUBLISH                │                                        │
│     │ election event         │ ──────▶ Pods 2,3 Notified            │
│     │ leader=pod-1           │         (know Pod 1 is leading)       │
│     └────────────────────────┘                                        │
│                                                                        │
└────────────────────────────────────────────────────────────────────────┘
```

**Key Points:**
- Fast (in-memory operations)
- Pub/Sub = instant notifications
- 10-30s failover via TTL
- Observable via event stream

---

## 5️⃣ Message Queue (Kafka) Pattern

Best for: Event-driven architectures, decoupled systems

```
┌────────────────────────────────────────────────────────────────────────┐
│                   MESSAGE QUEUE (KAFKA) PATTERN                        │
├────────────────────────────────────────────────────────────────────────┤
│                                                                        │
│  ┌──────────────────────────────┐                                     │
│  │  Scheduler @ 2:00 AM          │                                     │
│  │  (Spring Boot Pod)            │                                     │
│  └───────────┬───────────────────┘                                     │
│              │                                                         │
│              │ SEND Job to Kafka Queue                                │
│              ▼                                                         │
│  ┌───────────────────────────────────────┐                            │
│  │      Kafka Topic                      │                            │
│  │  daily-job-scheduler                  │                            │
│  │  Partitions: 1                        │                            │
│  └───────────────┬───────────────────────┘                            │
│                  │                                                     │
│                  ▼                                                     │
│  ┌───────────────────────────────────────┐                            │
│  │    Consumer Group:                    │                            │
│  │    job-scheduler-group                │                            │
│  └───────────────┬───────────────────────┘                            │
│                  │                                                     │
│      ┌───────────┼───────────┐                                        │
│      │           │           │                                        │
│      ▼           ▼           ▼                                        │
│  ┌────────┐ ┌────────┐ ┌────────┐                                    │
│  │ Pod 1  │ │ Pod 2  │ │ Pod 3  │                                    │
│  └────────┘ └────────┘ └────────┘                                    │
│                                                                        │
│  ┌──────────────────────────────────────────────────┐                 │
│  │  KEY: Only 1 Consumer Polls from Single Partition│                 │
│  └───────────────────────┬──────────────────────────┘                 │
│                          │                                            │
│                          ▼                                            │
│              ┌────────────────────────┐                               │
│              │   Consumer Pulls       │                               │
│              │   Message              │                               │
│              └───────┬────────────────┘                               │
│                      │                                                │
│          ┌───────────┴───────────┐                                    │
│          │                       │                                    │
│          ▼                       ▼                                    │
│  ┌────────────────┐      ┌────────────────┐                          │
│  │ Currently:     │      │ If Pod 1       │                          │
│  │ Pod 1 Executes │      │ Crashes:       │                          │
│  │ Job            │      │ Pod 2 Continues│                          │
│  └───────┬────────┘      │ from Offset    │                          │
│          │               └───────┬────────┘                          │
│          │                       │                                    │
│          └───────────┬───────────┘                                    │
│                      │                                                │
│                      ▼                                                │
│          ┌────────────────────────┐                                   │
│          │  Mark Offset           │                                   │
│          │  Commit to Broker      │                                   │
│          └───────────┬────────────┘                                   │
│                      │                                                │
│                      ▼                                                │
│          ┌────────────────────────┐                                   │
│          │  ✅ Exactly-Once-Like  │                                   │
│          │     Behavior           │                                   │
│          └────────────────────────┘                                   │
│                                                                        │
└────────────────────────────────────────────────────────────────────────┘
```

**Key Points:**
- Decoupled producer/consumer
- Single partition enforces ordering
- Only 1 consumer reads per partition
- Offset tracking enables recovery

---

## 🎯 Decision Tree: Choose Your Approach

```
┌────────────────────────────────────────────────────────────────────────┐
│           5 PRODUCTION APPROACHES FOR K8S LEADER ELECTION              │
├────────────────────────────────────────────────────────────────────────┤
│                                                                        │
│                      ┌──────────────────┐                             │
│                      │  Choose Based On │                             │
│                      └────────┬─────────┘                             │
│                               │                                       │
│           ┌───────────────────┼───────────────────┐                   │
│           │         │         │         │         │                   │
│           ▼         ▼         ▼         ▼         ▼                   │
│      ┌────────┐ ┌────────┐ ┌────────┐ ┌────────┐ ┌────────┐         │
│      │  K8s   │ │External│ │Database│ │ Redis  │ │Message │         │
│      │ Native │ │ Consul │ │  Lock  │ │Pub/Sub │ │ Queue  │         │
│      │ Lease  │ │ /etcd  │ │        │ │        │ │ Kafka  │         │
│      └───┬────┘ └───┬────┘ └───┬────┘ └───┬────┘ └───┬────┘         │
│          │          │          │          │          │               │
│          ▼          ▼          ▼          ▼          ▼               │
│  ┌────────────┐┌────────────┐┌────────────┐┌────────────┐┌──────────┐│
│  │✅ Native   ││✅ Multi-   ││✅ Simplest ││✅ Fast -  ││✅Decoupled││
│  │  Integration││  Cluster  ││✅ Existing ││  In Memory││✅Scalable ││
│  │✅ No New   ││✅ Strong   ││  DB        ││✅Observable││❌Complex  ││
│  │  Services  ││  Consist.  ││❌Bottleneck││  Events   ││  Setup    ││
│  │❌ 15-30s   ││❌ Extra    ││  at Scale  ││❌Another  ││           ││
│  │  Failover  ││  Service   ││            ││ Dependency││           ││
│  └────────────┘└────────────┘└────────────┘└────────────┘└──────────┘│
│                                                                        │
│  ┌──────────────────────────────────────────────────────────┐         │
│  │         CHOOSE BASED ON:                                 │         │
│  │         • Cluster Topology (Single vs Multi-cluster)     │         │
│  │         • Scale Requirements (100 vs 10K pods)           │         │
│  │         • Existing Infrastructure (What you already have)│         │
│  │         • Failure Recovery Time (5s vs 30s acceptable?)  │         │
│  └──────────────────────────────────────────────────────────┘         │
│                                                                        │
└────────────────────────────────────────────────────────────────────────┘
```

---

## ⚠️ Critical Failure Scenario: Leader Crash

```
┌────────────────────────────────────────────────────────────────────────┐
│                     LEADER CRASH & RECOVERY SCENARIO                   │
├────────────────────────────────────────────────────────────────────────┤
│                                                                        │
│  TIME T=0 (Normal Operation)                                          │
│  ─────────────────────────────                                        │
│                                                                        │
│  Pod1                  K8s etcd              Pod2          Pod3       │
│   │                       │                   │             │         │
│   │ Renew Lease          │                   │             │         │
│   │  (Pod1 is leader)    │                   │             │         │
│   ├─────────────────────▶│                   │             │         │
│   │                      │                   │             │         │
│   │      ✅ Success      │                   │             │         │
│   │◀─────────────────────┤                   │             │         │
│   │                      │                   │             │         │
│   │                      │  Watch Lease     │             │         │
│   │                      │  (Read-only)     │             │         │
│   │                      │◀──────────────────┤             │         │
│   │                      │                   │             │         │
│   │                      │ Leader: Pod1      │             │         │
│   │                      ├───────────────────▶             │         │
│   │                      │                   │             │         │
│   │                      │ Watch Lease       │             │         │
│   │                      │ (Read-only)       │             │         │
│   │                      │◀──────────────────┼─────────────┤         │
│   │                      │                   │             │         │
│   │                      │ Leader: Pod1      │             │         │
│   │                      ├───────────────────┼─────────────▶         │
│   │                      │                   │             │         │
│   │ Execute Job          │                   │             │         │
│   │ (00:00 - 00:30)      │                   │             │         │
│   │                      │                   │             │         │
├────────────────────────────────────────────────────────────────────────┤
│  TIME T=10 (Pod1 Crashes)                                             │
│  ──────────────────────────                                           │
│   │                      │                   │             │         │
│   │ ❌ CRASH!            │                   │             │         │
│   │ Out of Memory        │                   │             │         │
│   X (connection lost)    │                   │             │         │
│                          │                   │             │         │
├────────────────────────────────────────────────────────────────────────┤
│  TIME T=15 (Lease Expires)                                            │
│  ───────────────────────────                                          │
│                          │                   │             │         │
│                   ┌──────▼──────┐            │             │         │
│                   │ Lease TTL   │            │             │         │
│                   │ = 15s       │            │             │         │
│                   │ Lease       │            │             │         │
│                   │ Expired!    │            │             │         │
│                   └──────┬──────┘            │             │         │
│                          │                   │             │         │
│                          │ 🔔 Lease Expired! │             │         │
│                          ├───────────────────▶             │         │
│                          │                   │             │         │
│                          │ 🔔 Lease Expired! │             │         │
│                          ├───────────────────┼─────────────▶         │
│                          │                   │             │         │
├────────────────────────────────────────────────────────────────────────┤
│  TIME T=16 (New Election)                                             │
│  ──────────────────────────                                           │
│                          │                   │             │         │
│                          │ Try Acquire Lease │             │         │
│                          │◀──────────────────┤             │         │
│                          │                   │             │         │
│                          │ Try Acquire Lease │             │         │
│                          │◀──────────────────┼─────────────┤         │
│                          │                   │             │         │
│                          │ ✅ Success!       │             │         │
│                          │ You are leader    │             │         │
│                          ├───────────────────▶             │         │
│                          │                   │             │         │
│                          │ ❌ Conflict       │             │         │
│                          │ (already taken)   │             │         │
│                          ├───────────────────┼─────────────▶         │
│                          │                   │             │         │
│                          │                   ▼                       │
│                          │          ┌─────────────────┐              │
│                          │          │ Pod2 is now     │              │
│                          │          │ leader          │              │
│                          │          └────────┬────────┘              │
│                          │                   │                       │
│                          │                   ▼                       │
│                          │          ┌─────────────────┐              │
│                          │          │ Execute Job     │              │
│                          │          │ (00:30 - 01:00) │              │
│                          │          └────────┬────────┘              │
│                          │                   │                       │
│                          │                   ▼                       │
│                          │          ┌─────────────────────────────┐  │
│                          │          │ KEY: Pod2 checks            │  │
│                          │          │ idempotency                 │  │
│                          │          │ Finds previous execution    │  │
│                          │          │ (by Pod1)                   │  │
│                          │          │ Does NOT re-execute         │  │
│                          │          └─────────────────────────────┘  │
│                          │                                           │
└────────────────────────────────────────────────────────────────────────┘
```

**Critical Insight:**
- Lease expires, NOT immediately
- Requires TTL enforcement
- New pod checks for duplicate execution via idempotency key
- Database prevents actual duplicate processing

---

## 📊 Quick Comparison

| Approach | Setup | Latency | Failover | Scale | Complexity |
|----------|-------|---------|----------|-------|------------|
| K8s Lease | 🟢 30m | 🟠 100-500ms | 15-30s | ⭐⭐⭐⭐⭐ | 🟡 Medium |
| Consul | 🟠 2h | 🟢 50-200ms | 5-15s | ⭐⭐⭐⭐⭐ | 🔴 Hard |
| Database | 🟢 10m | 🟠 50-300ms | 10-30s | ⭐⭐ | 🟢 Easy |
| Redis | 🟢 15m | 🟢 <10ms | 10-30s | ⭐⭐⭐⭐ | 🟡 Medium |
| Kafka | 🟠 1h | 🟡 1-100ms | Offset-based | ⭐⭐⭐⭐⭐ | 🔴 Hard |

---

## 🎓 Interview Tips

> **Pro Tip**: Draw these diagrams from memory during your interview. It shows you understand the underlying patterns, not just the code.

1. **Start simple**: K8s Lease API (most common)
2. **Show tradeoffs**: Why Consul is different
3. **Explain failure**: What happens when leader crashes
4. **Mention idempotency**: CRITICAL for senior level
5. **Reference production**: "We monitor election frequency..."

---

## 📖 Full Documentation

See parent directory for complete guides:
- [06-Kubernetes-Leader-Election-Production.md](../06-Kubernetes-Leader-Election-Production.md) - Full deep-dive
- [07-Leader-Election-Interview-Cheat-Sheet.md](../07-Leader-Election-Interview-Cheat-Sheet.md) - 2-minute answer
