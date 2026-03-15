# Load Balancer Decision Algorithm - Traffic Distribution

## Table of Contents
1. [Introduction to Load Balancing](#introduction-to-load-balancing)
2. [Load Balancing Algorithms](#load-balancing-algorithms)
3. [Health Checks](#health-checks)
4. [Session Affinity (Sticky Sessions)](#session-affinity-sticky-sessions)
5. [Production Code Examples](#production-code-examples)
6. [When to Use Which Algorithm](#when-to-use-which-algorithm)
7. [Interview Questions & Answers](#interview-questions--answers)

---

## Introduction to Load Balancing

Load balancing distributes incoming traffic across multiple servers to improve reliability, scalability, and performance.

### Basic Concept

```
Without Load Balancer (Single Server):
┌──────────┐
│ Client 1 │──┐
└──────────┘  │
┌──────────┐  │
│ Client 2 │──┤
└──────────┘  │    ┌────────────┐
┌──────────┐  ├───>│  Server    │
│ Client 3 │──┤    │ (Overloaded)│
└──────────┘  │    └────────────┘
┌──────────┐  │
│ Client 4 │──┤
└──────────┘  │
┌──────────┐  │
│ Client 5 │──┘
└──────────┘

Problems:
• Single point of failure
• Limited capacity
• Poor performance under load
• No redundancy

With Load Balancer (Multiple Servers):
┌──────────┐
│ Client 1 │──┐
└──────────┘  │
┌──────────┐  │     ┌────────────────┐
│ Client 2 │──┤     │ Load Balancer  │
└──────────┘  ├────>│   (Distributes │
┌──────────┐  │     │    Traffic)    │
│ Client 3 │──┤     └────────┬───────┘
└──────────┘  │              │
┌──────────┐  │     ┌────────┼────────┬────────┐
│ Client 4 │──┤     │        │        │        │
└──────────┘  │     ▼        ▼        ▼        ▼
┌──────────┐  │  ┌─────┐ ┌─────┐ ┌─────┐ ┌─────┐
│ Client 5 │──┘  │Srv 1│ │Srv 2│ │Srv 3│ │Srv 4│
└──────────┘     └─────┘ └─────┘ └─────┘ └─────┘

Benefits:
✓ High availability
✓ Horizontal scalability
✓ Better performance
✓ Fault tolerance
✓ Maintenance without downtime
```

### Load Balancer Layers

```
┌─────────────────────────────────────────────────────────┐
│             Load Balancer Layers (OSI Model)            │
└─────────────────────────────────────────────────────────┘

Layer 4 (Transport Layer):
┌────────────────────────────────────────┐
│ • Works with TCP/UDP                   │
│ • Routes based on IP + Port            │
│ • Fast (doesn't inspect payload)       │
│ • Protocol-agnostic                    │
│ • Examples: AWS NLB, HAProxy L4        │
└────────────────────────────────────────┘

    Client → [IP: 1.2.3.4, Port: 443] → Server

Layer 7 (Application Layer):
┌────────────────────────────────────────┐
│ • Works with HTTP/HTTPS                │
│ • Routes based on URL, headers, etc.   │
│ • Slower (inspects content)            │
│ • Application-aware                    │
│ • Examples: AWS ALB, NGINX, HAProxy L7 │
└────────────────────────────────────────┘

    Client → [URL: /api/users, Header: X-Version: v2] → Server

Comparison:
┌─────────────┬──────────────┬──────────────┐
│   Feature   │   Layer 4    │   Layer 7    │
├─────────────┼──────────────┼──────────────┤
│ Speed       │ Faster       │ Slower       │
│ Routing     │ IP/Port only │ URL/Headers  │
│ SSL         │ Passthrough  │ Termination  │
│ Protocols   │ Any TCP/UDP  │ HTTP(S)      │
│ Content     │ No inspect   │ Full inspect │
│ Cost        │ Lower        │ Higher       │
└─────────────┴──────────────┴──────────────┘
```

---

## Load Balancing Algorithms

### 1. Round Robin

Distributes requests sequentially across all servers.

```
┌─────────────────────────────────────────────────────────┐
│              Round Robin Algorithm                      │
└─────────────────────────────────────────────────────────┘

Server Pool:
┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐
│ Server 1│ │ Server 2│ │ Server 3│ │ Server 4│
└─────────┘ └─────────┘ └─────────┘ └─────────┘

Request Distribution:
Request 1 → Server 1
Request 2 → Server 2
Request 3 → Server 3
Request 4 → Server 4
Request 5 → Server 1  (cycle repeats)
Request 6 → Server 2
Request 7 → Server 3
Request 8 → Server 4
Request 9 → Server 1
...

Visual Timeline:
Time:    0s      1s      2s      3s      4s      5s
         │       │       │       │       │       │
Srv 1:   ●───────────────●───────────────●
Srv 2:       ●───────────────●───────────────●
Srv 3:           ●───────────────●───────────────
Srv 4:               ●───────────────●

State Management:
┌────────────────────────────────────┐
│ Current Index: 2                   │
│ Server List: [S1, S2, S3, S4]     │
│                         ▲          │
│                    Current         │
│                                    │
│ Next request → Index 3 (S4)       │
│ Then Index = (Index + 1) % 4 = 0  │
└────────────────────────────────────┘

Characteristics:
✓ Simple and fair
✓ Equal distribution (if requests same size)
✓ No state needed (just index)
✗ Doesn't consider server capacity
✗ Doesn't consider current load
✗ Problematic if servers have different specs
```

### 2. Weighted Round Robin

Distributes requests based on server capacity weights.

```
┌─────────────────────────────────────────────────────────┐
│          Weighted Round Robin Algorithm                 │
└─────────────────────────────────────────────────────────┘

Server Pool with Weights:
┌──────────────────────────────────────────────────────┐
│ Server 1: Weight = 5 (High-spec: 16 CPU, 32GB RAM)  │
│ Server 2: Weight = 3 (Medium-spec: 8 CPU, 16GB RAM) │
│ Server 3: Weight = 2 (Low-spec: 4 CPU, 8GB RAM)     │
└──────────────────────────────────────────────────────┘

Total Weight = 5 + 3 + 2 = 10

Distribution Pattern:
Request 1  → Server 1  (5/10 = 50%)
Request 2  → Server 1
Request 3  → Server 1
Request 4  → Server 1
Request 5  → Server 1
Request 6  → Server 2  (3/10 = 30%)
Request 7  → Server 2
Request 8  → Server 2
Request 9  → Server 3  (2/10 = 20%)
Request 10 → Server 3
Request 11 → Server 1  (cycle repeats)

Visual Distribution (per 10 requests):
┌─────────────────────────────────────────────┐
│ Server 1: ●●●●● (5 requests - 50%)         │
│ Server 2: ●●● (3 requests - 30%)           │
│ Server 3: ●● (2 requests - 20%)            │
└─────────────────────────────────────────────┘

Smooth Weighted Round Robin (Better):
Instead of consecutive assignments, smooth it out:

Request 1  → Server 1
Request 2  → Server 2
Request 3  → Server 1
Request 4  → Server 1
Request 5  → Server 3
Request 6  → Server 1
Request 7  → Server 2
Request 8  → Server 1
Request 9  → Server 2
Request 10 → Server 3

Visual Timeline (Smooth):
Time:    0s  1s  2s  3s  4s  5s  6s  7s  8s  9s
         │   │   │   │   │   │   │   │   │   │
Srv 1:   ●───────●───●───────●───────●─────────
Srv 2:       ●───────────────────●───────●─────
Srv 3:                   ●───────────────────●─

Benefits:
✓ Respects server capacity
✓ Better resource utilization
✓ Flexible (adjust weights dynamically)
✗ Requires capacity knowledge
✗ Slightly more complex
```

### 3. Least Connections

Routes to server with fewest active connections.

```
┌─────────────────────────────────────────────────────────┐
│           Least Connections Algorithm                   │
└─────────────────────────────────────────────────────────┘

Current State:
┌──────────────────────────────────────────────────────┐
│ Server 1: ████ (4 active connections)                │
│ Server 2: ██████ (6 active connections)              │
│ Server 3: ██ (2 active connections) ← Selected!      │
│ Server 4: █████ (5 active connections)               │
└──────────────────────────────────────────────────────┘

New Request Arrives:
┌────────────────────────────────────────┐
│ 1. Check all servers                   │
│    S1: 4 connections                   │
│    S2: 6 connections                   │
│    S3: 2 connections ← Minimum         │
│    S4: 5 connections                   │
│                                        │
│ 2. Select S3 (least connections)       │
│ 3. Route request to S3                 │
│ 4. S3 connections: 2 → 3               │
└────────────────────────────────────────┘

After Assignment:
┌──────────────────────────────────────────────────────┐
│ Server 1: ████ (4 active connections)                │
│ Server 2: ██████ (6 active connections)              │
│ Server 3: ███ (3 active connections)                 │
│ Server 4: █████ (5 active connections)               │
└──────────────────────────────────────────────────────┘

Timeline Example:
Time: 0s
S1: 5 conn
S2: 3 conn ← New req goes here (least)
S3: 7 conn
S4: 4 conn

Time: 1s (S2 gets request, now 4 conn)
S1: 5 conn
S2: 4 conn
S3: 7 conn
S4: 4 conn ← New req (tie, pick first)

Time: 2s (One connection on S3 finishes)
S1: 5 conn
S2: 4 conn
S3: 6 conn
S4: 4 conn ← New req (tie with S2)

Use Case Visualization:
┌─────────────────────────────────────────────────┐
│ Scenario: Mixed Request Durations              │
│                                                 │
│ Request A: 1 second                            │
│ Request B: 10 seconds (database query)         │
│ Request C: 1 second                            │
│                                                 │
│ Round Robin would be unfair:                   │
│ S1: Gets Request B (busy for 10s)             │
│ S2: Gets Requests A,C (done quickly)          │
│ → S1 overloaded, S2 underutilized             │
│                                                 │
│ Least Connections balances better:             │
│ S1: Gets Request B (conn count high)          │
│ S2: Gets Requests A,C (conn count updates)    │
│ → More even distribution                       │
└─────────────────────────────────────────────────┘

Characteristics:
✓ Adapts to varying request durations
✓ Better for long-lived connections
✓ Good for WebSockets, databases
✗ Requires connection tracking (state)
✗ Overhead of counting connections
```

### 4. Weighted Least Connections

Combines server capacity with connection count.

```
┌─────────────────────────────────────────────────────────┐
│       Weighted Least Connections Algorithm              │
└─────────────────────────────────────────────────────────┘

Server Configuration:
┌──────────────────────────────────────────────────┐
│ Server 1: Weight = 100, Connections = 40         │
│ Server 2: Weight = 50,  Connections = 30         │
│ Server 3: Weight = 25,  Connections = 10         │
└──────────────────────────────────────────────────┘

Formula: Score = Connections / Weight
(Lower score = less loaded)

Calculate Scores:
┌──────────────────────────────────────────────────┐
│ Server 1: 40 / 100 = 0.40                        │
│ Server 2: 30 / 50  = 0.60                        │
│ Server 3: 10 / 25  = 0.40                        │
└──────────────────────────────────────────────────┘

New request arrives:
→ S1 and S3 tied at 0.40
→ Pick S1 (first in list, or random)

After assignment:
┌──────────────────────────────────────────────────┐
│ Server 1: 41 / 100 = 0.41                        │
│ Server 2: 30 / 50  = 0.60                        │
│ Server 3: 10 / 25  = 0.40 ← Now lowest           │
└──────────────────────────────────────────────────┘

Next request goes to S3.

Visual Comparison:
Without Weights (Least Connections):
┌─────────────────────────────────────────┐
│ S1 (powerful):  ████████ (80 conn)      │
│ S2 (medium):    ████ (40 conn) ← chosen │
│ S3 (weak):      ████ (40 conn) ← chosen │
└─────────────────────────────────────────┘
Problem: S3 might be overloaded even with same count

With Weights (Weighted Least Connections):
┌─────────────────────────────────────────┐
│ S1 (w=100): 80/100 = 0.80               │
│ S2 (w=50):  40/50  = 0.80               │
│ S3 (w=25):  40/25  = 1.60 ← Overloaded! │
└─────────────────────────────────────────┘
S1 or S2 chosen (better distribution)

Characteristics:
✓ Considers both capacity and load
✓ Best for heterogeneous server pools
✓ Adapts to server performance
✗ More complex calculation
✗ Requires accurate weight configuration
```

### 5. IP Hash

Routes based on client IP hash (session affinity).

```
┌─────────────────────────────────────────────────────────┐
│               IP Hash Algorithm                         │
└─────────────────────────────────────────────────────────┘

Concept:
Client IP → Hash Function → Server Index

Example:
Client IP: 192.168.1.100
Hash: SHA256(192.168.1.100) = a7f3e8d9c2b1...
Index: Hash % ServerCount

Server Pool (4 servers):
┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐
│ Server 0│ │ Server 1│ │ Server 2│ │ Server 3│
└─────────┘ └─────────┘ └─────────┘ └─────────┘

Client Routing:
┌──────────────────────────────────────────────┐
│ Client A (IP: 192.168.1.1)                   │
│ Hash: 12345                                  │
│ Server: 12345 % 4 = 1 → Server 1            │
│                                              │
│ Client B (IP: 192.168.1.2)                   │
│ Hash: 98765                                  │
│ Server: 98765 % 4 = 1 → Server 1            │
│                                              │
│ Client C (IP: 10.0.0.1)                      │
│ Hash: 45678                                  │
│ Server: 45678 % 4 = 2 → Server 2            │
└──────────────────────────────────────────────┘

Session Affinity:
┌─────────────────────────────────────────────────┐
│ Client A always goes to Server 1                │
│                                                 │
│ Request 1 (Client A) → Server 1                │
│ Request 2 (Client A) → Server 1                │
│ Request 3 (Client A) → Server 1                │
│ ...                                             │
│                                                 │
│ Session data stays on Server 1                 │
│ No need to replicate session                   │
└─────────────────────────────────────────────────┘

Problem: Adding/Removing Servers
┌──────────────────────────────────────────────┐
│ Initial: 4 servers                           │
│ Client A → 12345 % 4 = 1 → Server 1         │
│                                              │
│ Add Server 5: Now 5 servers                 │
│ Client A → 12345 % 5 = 0 → Server 0 ✗       │
│                                              │
│ Session lost! User logged out!               │
└──────────────────────────────────────────────┘

Solution: Consistent Hashing (see next section)

Characteristics:
✓ Session affinity (sticky sessions)
✓ No session state sharing needed
✓ Simple to implement
✗ Uneven distribution
✗ Breaks when servers change
✗ Doesn't consider server load
```

### 6. Consistent Hashing

Improved version of IP Hash that handles server changes.

```
┌─────────────────────────────────────────────────────────┐
│            Consistent Hashing Algorithm                 │
└─────────────────────────────────────────────────────────┘

Concept: Hash Ring
┌────────────────────────────────────────────────┐
│             Hash Ring (0 - 2^32)               │
│                                                │
│                    0                           │
│                    ●                           │
│                   ╱ ╲                          │
│                  ╱   ╲                         │
│           S3 ●  ╱     ╲  ● S1                  │
│               ╱         ╲                      │
│              ╱           ╲                     │
│             ●─────────────●                    │
│       2^31                     2^30            │
│                                                │
│            S2 ●         ● S4                   │
│                                                │
│     Servers placed on ring using hash          │
│     Clients route to next server clockwise     │
└────────────────────────────────────────────────┘

Server Placement:
Server 1: hash("server1") = 1,234,567,890 → Position on ring
Server 2: hash("server2") = 2,345,678,901 → Position on ring
Server 3: hash("server3") = 3,456,789,012 → Position on ring
Server 4: hash("server4") = 234,567,890   → Position on ring

Client Routing:
Client A: hash("192.168.1.1") = 1,500,000,000
→ Next server clockwise: Server 1

Client B: hash("192.168.1.2") = 2,500,000,000
→ Next server clockwise: Server 2

Visual:
                    0
                    │
              S4 ●  │
                    │
         3B     ●───┼───●  1.5B
                    │       ↑
              S3 ●  │   Client A
                    │
         2.5B   ●───┼───●  1.2B
          ↑         │      Server 1
      Client B      │
                    │
              S2 ●  │   ● Server 2
                    │

Adding Server:
Before (4 servers):
Client X → hash = 1,800,000,000 → Server 1

Add Server 5: hash("server5") = 1,600,000,000

After (5 servers):
Client X → hash = 1,800,000,000 → Server 5

Only clients between S5 and old S1 are affected!
Other clients unchanged → Minimal disruption

Comparison:
┌─────────────────────────────────────────────────┐
│              Regular Hash vs Consistent Hash    │
├─────────────────────────────────────────────────┤
│                                                 │
│ Regular Hash (N=4 → N=5):                      │
│ • All clients remapped (100% disruption)       │
│ • Client A: Server 1 → Server 0                │
│ • Client B: Server 2 → Server 3                │
│ • Client C: Server 3 → Server 1                │
│                                                 │
│ Consistent Hash (N=4 → N=5):                   │
│ • Only ~20% clients remapped (1/5)             │
│ • Client A: Server 1 → Server 1 (same)         │
│ • Client B: Server 2 → Server 5 (changed)      │
│ • Client C: Server 3 → Server 3 (same)         │
└─────────────────────────────────────────────────┘

Virtual Nodes (Improved Distribution):
Instead of 1 position per server, use multiple:
┌──────────────────────────────────────────────┐
│ Server 1:                                    │
│   hash("server1#1") → Position A             │
│   hash("server1#2") → Position B             │
│   hash("server1#3") → Position C             │
│   ... (100 virtual nodes)                    │
│                                              │
│ More virtual nodes = Better distribution     │
└──────────────────────────────────────────────┘

Characteristics:
✓ Minimal disruption when servers change
✓ Good distribution (with virtual nodes)
✓ Scales well
✗ More complex than simple hash
✗ Requires hash ring implementation
✗ Virtual nodes add overhead
```

### 7. Least Response Time

Routes to server with fastest response time.

```
┌─────────────────────────────────────────────────────────┐
│          Least Response Time Algorithm                  │
└─────────────────────────────────────────────────────────┘

Current Server Metrics:
┌────────────────────────────────────────────────┐
│ Server 1: Avg Response Time = 50ms             │
│ Server 2: Avg Response Time = 120ms            │
│ Server 3: Avg Response Time = 30ms ← Fastest   │
│ Server 4: Avg Response Time = 80ms             │
└────────────────────────────────────────────────┘

Decision: Route to Server 3 (30ms)

Response Time Tracking:
┌─────────────────────────────────────────────────┐
│ Server 3 Response Times (Last 10 requests):    │
│ [28ms, 32ms, 29ms, 31ms, 30ms, 33ms, 28ms,    │
│  30ms, 31ms, 32ms]                             │
│                                                 │
│ Average = (28+32+29+31+30+33+28+30+31+32)/10  │
│         = 304/10 = 30.4ms                      │
└─────────────────────────────────────────────────┘

Weighted Response Time (Better):
Combines response time + active connections

Formula: Score = (ResponseTime * 0.7) + (Connections * 0.3)

Example:
┌──────────────────────────────────────────────────────┐
│ Server 1: 50ms, 10 conn                              │
│   Score = (50 * 0.7) + (10 * 0.3) = 35 + 3 = 38    │
│                                                      │
│ Server 2: 30ms, 50 conn                              │
│   Score = (30 * 0.7) + (50 * 0.3) = 21 + 15 = 36   │
│                                                      │
│ Server 3: 40ms, 5 conn ← Selected (lowest score)    │
│   Score = (40 * 0.7) + (5 * 0.3) = 28 + 1.5 = 29.5 │
└──────────────────────────────────────────────────────┘

Timeline Visualization:
Time:    0s      1s      2s      3s      4s      5s
         │       │       │       │       │       │
S1 (50ms): ──●────────●────────●────────●──────
S2 (120ms): ────────────────────────●──────────
S3 (30ms): ●────●────●────●────────────●────●──
S4 (80ms): ──────────●────────────●────────────

Most requests go to S3 (fastest)

Adaptive Behavior:
┌─────────────────────────────────────────────────┐
│ Scenario: Server 3 becomes slow                 │
│                                                 │
│ Time 0s: S3 = 30ms → Gets most traffic         │
│ Time 1s: S3 load increases, now 60ms           │
│ Time 2s: Algorithm detects, reduces traffic    │
│ Time 3s: S3 load decreases, back to 35ms       │
│ Time 4s: Algorithm increases traffic again      │
│                                                 │
│ Self-balancing behavior!                        │
└─────────────────────────────────────────────────┘

Health Check Integration:
┌────────────────────────────────────────────┐
│ Every 5 seconds:                           │
│ 1. Send health check request               │
│ 2. Measure response time                   │
│ 3. Update moving average                   │
│ 4. Adjust routing decisions                │
│                                            │
│ If server unresponsive:                    │
│ Response Time = ∞ (never selected)         │
└────────────────────────────────────────────┘

Characteristics:
✓ Performance-aware routing
✓ Adapts to server performance
✓ Good for varying server specs
✓ Detects degradation automatically
✗ Requires continuous monitoring
✗ Can create feedback loops (slow → less traffic → fast)
✗ Network latency affects measurements
```

---

## Health Checks

Health checks monitor server availability and health.

### Types of Health Checks

```
┌─────────────────────────────────────────────────────────┐
│                 Health Check Types                      │
└─────────────────────────────────────────────────────────┘

1. Passive Health Checks (Real Traffic):
┌────────────────────────────────────────────┐
│ Monitor actual request/response            │
│                                            │
│ Client → LB → Server                       │
│                   │                        │
│                   ├─ 200 OK → Healthy     │
│                   ├─ 500 Error → Unhealthy│
│                   └─ Timeout → Unhealthy  │
│                                            │
│ Pros:                                      │
│ • No extra traffic                         │
│ • Real user experience                     │
│                                            │
│ Cons:                                      │
│ • Only detects after failure               │
│ • Affects real users                       │
└────────────────────────────────────────────┘

2. Active Health Checks (Synthetic):
┌────────────────────────────────────────────┐
│ Send periodic test requests                │
│                                            │
│ Load Balancer sends:                       │
│ GET /health every 5 seconds                │
│                                            │
│ Server responds:                           │
│ {                                          │
│   "status": "healthy",                     │
│   "timestamp": 1710507600,                 │
│   "connections": 45,                       │
│   "cpu": 60,                              │
│   "memory": 75                            │
│ }                                          │
│                                            │
│ Pros:                                      │
│ • Proactive detection                      │
│ • Detailed health info                     │
│                                            │
│ Cons:                                      │
│ • Extra network traffic                    │
│ • May not reflect real load               │
└────────────────────────────────────────────┘

3. TCP Health Checks:
┌────────────────────────────────────────────┐
│ Check if port is open                      │
│                                            │
│ LB: Can I connect to Server:8080?         │
│ Server: Yes (TCP handshake succeeds)      │
│ LB: ✓ Healthy                             │
│                                            │
│ Fastest but least detailed                 │
└────────────────────────────────────────────┘

4. HTTP Health Checks:
┌────────────────────────────────────────────┐
│ Check HTTP endpoint                        │
│                                            │
│ LB: GET /health                           │
│ Server: 200 OK + payload                  │
│ LB: ✓ Healthy                             │
│                                            │
│ More thorough than TCP                     │
└────────────────────────────────────────────┘

5. Deep Health Checks:
┌────────────────────────────────────────────┐
│ Check dependencies                         │
│                                            │
│ Health endpoint checks:                    │
│ • Database connectivity                    │
│ • Cache availability (Redis)               │
│ • External API status                      │
│ • Disk space                              │
│ • Memory usage                            │
│                                            │
│ Most thorough but slowest                  │
└────────────────────────────────────────────┘
```

### Health Check Configuration

```
┌─────────────────────────────────────────────────────────┐
│            Health Check Configuration                   │
└─────────────────────────────────────────────────────────┘

Parameters:
┌────────────────────────────────────────────────┐
│ Interval: 5 seconds                            │
│ → How often to check                           │
│                                                │
│ Timeout: 2 seconds                             │
│ → Max wait for response                        │
│                                                │
│ Unhealthy Threshold: 3                         │
│ → Consecutive failures before marking unhealthy│
│                                                │
│ Healthy Threshold: 2                           │
│ → Consecutive successes before marking healthy │
└────────────────────────────────────────────────┘

State Machine:
┌─────────────┐
│   Healthy   │
└──────┬──────┘
       │
       │ Fail
       ▼
┌─────────────┐
│  Degraded   │  (1 failure)
└──────┬──────┘
       │
       │ Fail
       ▼
┌─────────────┐
│ Unhealthy   │  (3 consecutive failures)
└──────┬──────┘
       │
       │ Success
       ▼
┌─────────────┐
│ Recovering  │  (1 success)
└──────┬──────┘
       │
       │ Success
       ▼
┌─────────────┐
│   Healthy   │  (2 consecutive successes)
└─────────────┘

Timeline Example:
Time:  0s   5s   10s  15s  20s  25s  30s  35s  40s
Check: ✓   ✓    ✗    ✗    ✗    ✓    ✓    ✓    ✓
State: Healthy   Deg  Deg  Unhealthy    Rec  Healthy
            │         │    │        │    │    │
       First fail     │    │    First success│
                 Second    │                 │
                      Third fail      Second success
                      (marked unhealthy) (marked healthy)

Routing During Health States:
┌────────────────────────────────────────────────┐
│ Healthy:    100% traffic                       │
│ Degraded:   50% traffic (reduced)              │
│ Unhealthy:  0% traffic (removed from pool)     │
│ Recovering: 25% traffic (gradual ramp-up)      │
└────────────────────────────────────────────────┘
```

### Health Check Endpoints

```
┌─────────────────────────────────────────────────────────┐
│              Health Check Endpoint Design               │
└─────────────────────────────────────────────────────────┘

Basic Health Check:
GET /health

Response:
{
  "status": "healthy",
  "timestamp": 1710507600000
}

Detailed Health Check:
GET /health/detailed

Response:
{
  "status": "healthy",
  "timestamp": 1710507600000,
  "checks": {
    "database": {
      "status": "healthy",
      "responseTime": 5,
      "details": "Connected to primary"
    },
    "redis": {
      "status": "healthy",
      "responseTime": 2,
      "details": "Cache operational"
    },
    "disk": {
      "status": "healthy",
      "usage": 65,
      "available": "350GB"
    },
    "memory": {
      "status": "warning",
      "usage": 85,
      "available": "2GB"
    }
  },
  "metrics": {
    "activeConnections": 45,
    "cpuUsage": 60,
    "requestsPerSecond": 120
  }
}

Readiness vs Liveness:
┌────────────────────────────────────────────────┐
│ /health/liveness                               │
│ → Is the app running?                          │
│ → If fails: Restart container                  │
│                                                │
│ Example checks:                                │
│ • Process alive                                │
│ • Not deadlocked                               │
│                                                │
│────────────────────────────────────────────────│
│ /health/readiness                              │
│ → Can the app serve traffic?                   │
│ → If fails: Remove from load balancer          │
│                                                │
│ Example checks:                                │
│ • Database connected                           │
│ • Cache available                              │
│ • Dependencies ready                           │
└────────────────────────────────────────────────┘

Health Check Scenarios:
┌────────────────────────────────────────────────┐
│ Scenario 1: Database Down                      │
│                                                │
│ /health/liveness → 200 OK (app running)       │
│ /health/readiness → 503 Service Unavailable    │
│                                                │
│ Action: Remove from load balancer,             │
│         but don't restart (may recover)        │
│────────────────────────────────────────────────│
│ Scenario 2: App Deadlocked                     │
│                                                │
│ /health/liveness → Timeout (no response)      │
│ /health/readiness → Timeout                    │
│                                                │
│ Action: Restart container                      │
│────────────────────────────────────────────────│
│ Scenario 3: High Load                          │
│                                                │
│ /health/liveness → 200 OK                     │
│ /health/readiness → 200 OK (but slow)         │
│                                                │
│ Action: Continue routing (app functional)      │
│         but monitor (may need scaling)         │
└────────────────────────────────────────────────┘
```

---

## Session Affinity (Sticky Sessions)

Ensures requests from same client go to same server.

### Session Affinity Mechanisms

```
┌─────────────────────────────────────────────────────────┐
│            Session Affinity Mechanisms                  │
└─────────────────────────────────────────────────────────┘

1. Cookie-Based Affinity:
┌────────────────────────────────────────────────┐
│ First Request:                                 │
│ Client → LB → Server 2                         │
│                                                │
│ LB adds cookie:                                │
│ Set-Cookie: SERVERID=server2; Path=/           │
│                                                │
│ Subsequent Requests:                           │
│ Client → LB (Cookie: SERVERID=server2) → S2   │
└────────────────────────────────────────────────┘

Timeline:
Request 1: Client → LB → Server 2 (chosen)
           Client ← LB ← Server 2 + Cookie(server2)

Request 2: Client → LB (has cookie) → Server 2
Request 3: Client → LB (has cookie) → Server 2
Request 4: Client → LB (has cookie) → Server 2

2. IP Hash Affinity:
┌────────────────────────────────────────────────┐
│ Based on client IP address                     │
│                                                │
│ Client IP: 192.168.1.100                       │
│ Hash: 12345                                    │
│ Server: 12345 % 4 = 1 → Always Server 1       │
│                                                │
│ No cookies needed                              │
│ Same IP → Same server                          │
└────────────────────────────────────────────────┘

3. Session ID Affinity:
┌────────────────────────────────────────────────┐
│ Based on application session ID                │
│                                                │
│ Session ID: abc123xyz                          │
│ Hash(abc123xyz) % ServerCount → Server 3      │
│                                                │
│ Application-aware                              │
│ Survives IP changes (mobile/WiFi switching)    │
└────────────────────────────────────────────────┘

Comparison:
┌─────────────┬──────────────┬──────────────┬─────────────┐
│  Mechanism  │   Pros       │    Cons      │  Use Case   │
├─────────────┼──────────────┼──────────────┼─────────────┤
│ Cookie      │ Most reliable│ Cookie needed│ Web apps    │
│ IP Hash     │ No cookie    │ IP changes   │ APIs        │
│ Session ID  │ App-aware    │ Complex      │ Mobile apps │
└─────────────┴──────────────┴──────────────┴─────────────┘
```

### Session Affinity Challenges

```
┌─────────────────────────────────────────────────────────┐
│          Session Affinity Challenges                    │
└─────────────────────────────────────────────────────────┘

Challenge 1: Server Failure
┌────────────────────────────────────────────────┐
│ Client → Server 2 (session data)               │
│                                                │
│ Server 2 crashes!                              │
│                                                │
│ Client → ? (session lost)                      │
│                                                │
│ Solution: Session Replication                  │
│ ┌─────────┐  replicate  ┌─────────┐           │
│ │Server 1 │◄────────────►│Server 2 │           │
│ └─────────┘              └─────────┘           │
└────────────────────────────────────────────────┘

Challenge 2: Uneven Distribution
┌────────────────────────────────────────────────┐
│ Some users have long sessions:                 │
│                                                │
│ Server 1: 10 sessions (2 long-lived)          │
│           ████████████████████████             │
│ Server 2: 10 sessions (all short)              │
│           ████████                             │
│                                                │
│ Load imbalance even with same session count!  │
│                                                │
│ Solution: Drain connections + rebalance        │
└────────────────────────────────────────────────┘

Challenge 3: Adding/Removing Servers
┌────────────────────────────────────────────────┐
│ Initial: 3 servers                             │
│ User A → Server 1 (session stored)             │
│                                                │
│ Add Server 4:                                  │
│ User A → Server 2 (hash changed!)              │
│          Session not found → Logged out!       │
│                                                │
│ Solution: Consistent hashing or                │
│          session store (Redis/database)        │
└────────────────────────────────────────────────┘

Best Practice: Stateless Sessions
┌────────────────────────────────────────────────┐
│ Don't store session on server                  │
│                                                │
│ Instead:                                       │
│ • JWT tokens (client-side)                    │
│ • Shared session store (Redis)                │
│ • Database-backed sessions                     │
│                                                │
│ Benefits:                                      │
│ ✓ Any server can handle any request           │
│ ✓ Easy scaling                                │
│ ✓ No session loss on failure                  │
│ ✓ No affinity needed                          │
└────────────────────────────────────────────────┘

Stateless Architecture:
┌──────────┐
│  Client  │
│ (JWT)    │
└────┬─────┘
     │
     │ Request + JWT
     ▼
┌────────────┐       ┌─────────────────┐
│    LB      │       │  Redis (shared  │
│ (Round     │◄─────►│  session store) │
│  Robin)    │       └─────────────────┘
└────┬───────┘
     │
     ├───────┬────────┬────────┐
     ▼       ▼        ▼        ▼
  ┌────┐ ┌────┐  ┌────┐  ┌────┐
  │ S1 │ │ S2 │  │ S3 │  │ S4 │
  └────┘ └────┘  └────┘  └────┘
  (stateless servers)

Any server can serve any request!
```

---

## Production Code Examples

### Example 1: Round Robin Load Balancer

```java
@Component
public class RoundRobinLoadBalancer implements LoadBalancer {

    private final List<Server> servers;
    private final AtomicInteger currentIndex;

    /**
     * Round Robin Load Balancer
     *
     * Distribution:
     * Request 1 → Server 0
     * Request 2 → Server 1
     * Request 3 → Server 2
     * Request 4 → Server 0 (cycle repeats)
     */
    public RoundRobinLoadBalancer(List<Server> servers) {
        this.servers = new CopyOnWriteArrayList<>(servers);
        this.currentIndex = new AtomicInteger(0);
    }

    @Override
    public Server selectServer(Request request) {
        if (servers.isEmpty()) {
            throw new NoAvailableServerException("No servers available");
        }

        // Get available servers (healthy only)
        List<Server> availableServers = servers.stream()
            .filter(Server::isHealthy)
            .collect(Collectors.toList());

        if (availableServers.isEmpty()) {
            throw new NoAvailableServerException("No healthy servers");
        }

        // Round robin: increment and wrap around
        int index = currentIndex.getAndIncrement() % availableServers.size();

        // Handle negative values (rare, but possible with overflow)
        if (index < 0) {
            index = (index + availableServers.size()) % availableServers.size();
        }

        Server selectedServer = availableServers.get(index);

        log.debug("Selected server {} (index {})",
            selectedServer.getId(), index);

        return selectedServer;
    }

    @Override
    public void addServer(Server server) {
        servers.add(server);
        log.info("Added server: {}", server.getId());
    }

    @Override
    public void removeServer(Server server) {
        servers.remove(server);
        log.info("Removed server: {}", server.getId());
    }
}

/**
 * Server model
 */
@Data
public class Server {
    private String id;
    private String host;
    private int port;
    private boolean healthy = true;
    private long lastHealthCheck;
    private int activeConnections = 0;
    private double avgResponseTime = 0;

    public String getUrl() {
        return String.format("http://%s:%d", host, port);
    }

    public void incrementConnections() {
        activeConnections++;
    }

    public void decrementConnections() {
        activeConnections = Math.max(0, activeConnections - 1);
    }
}
```

### Example 2: Weighted Round Robin

```java
@Component
public class WeightedRoundRobinLoadBalancer implements LoadBalancer {

    private final List<WeightedServer> servers;
    private final AtomicInteger currentIndex;

    /**
     * Weighted Round Robin using Smooth Algorithm
     *
     * Example:
     * S1 (weight=5), S2 (weight=3), S3 (weight=2)
     *
     * Distribution over 10 requests:
     * S1: 5 requests (50%)
     * S2: 3 requests (30%)
     * S3: 2 requests (20%)
     *
     * But smoothly distributed, not consecutive
     */
    public WeightedRoundRobinLoadBalancer(List<WeightedServer> servers) {
        this.servers = new CopyOnWriteArrayList<>(servers);
        this.currentIndex = new AtomicInteger(0);

        // Initialize current weights
        servers.forEach(s -> s.setCurrentWeight(0));
    }

    @Override
    public synchronized Server selectServer(Request request) {
        if (servers.isEmpty()) {
            throw new NoAvailableServerException("No servers available");
        }

        List<WeightedServer> availableServers = servers.stream()
            .filter(Server::isHealthy)
            .collect(Collectors.toList());

        if (availableServers.isEmpty()) {
            throw new NoAvailableServerException("No healthy servers");
        }

        // Calculate total weight
        int totalWeight = availableServers.stream()
            .mapToInt(WeightedServer::getWeight)
            .sum();

        // Smooth weighted round robin algorithm
        WeightedServer selected = null;
        int maxWeight = Integer.MIN_VALUE;

        for (WeightedServer server : availableServers) {
            // Increase current weight by configured weight
            server.setCurrentWeight(
                server.getCurrentWeight() + server.getWeight()
            );

            // Find server with maximum current weight
            if (server.getCurrentWeight() > maxWeight) {
                maxWeight = server.getCurrentWeight();
                selected = server;
            }
        }

        // Reduce selected server's weight by total
        if (selected != null) {
            selected.setCurrentWeight(
                selected.getCurrentWeight() - totalWeight
            );
        }

        log.debug("Selected server {} (weight {})",
            selected.getId(), selected.getWeight());

        return selected;
    }

    /**
     * Example execution trace:
     *
     * Servers: S1(w=5), S2(w=3), S3(w=2), Total=10
     *
     * Initial: S1(curr=0), S2(curr=0), S3(curr=0)
     *
     * Req 1: Add weights: S1(5), S2(3), S3(2)
     *        Select max: S1(5)
     *        Reduce: S1(5-10=-5), S2(3), S3(2)
     *        → S1 selected
     *
     * Req 2: Add weights: S1(-5+5=0), S2(3+3=6), S3(2+2=4)
     *        Select max: S2(6)
     *        Reduce: S1(0), S2(6-10=-4), S3(4)
     *        → S2 selected
     *
     * Req 3: Add weights: S1(0+5=5), S2(-4+3=-1), S3(4+2=6)
     *        Select max: S3(6)
     *        Reduce: S1(5), S2(-1), S3(6-10=-4)
     *        → S3 selected
     *
     * And so on... smooth distribution!
     */
}

/**
 * Weighted Server
 */
@Data
@EqualsAndHashCode(callSuper = true)
public class WeightedServer extends Server {
    private int weight = 1;          // Configured weight
    private int currentWeight = 0;   // Runtime weight for algorithm
}
```

### Example 3: Least Connections

```java
@Component
public class LeastConnectionsLoadBalancer implements LoadBalancer {

    private final List<Server> servers;

    /**
     * Least Connections Load Balancer
     *
     * Selects server with fewest active connections
     *
     * Example:
     * S1: 10 connections
     * S2: 5 connections  ← Selected
     * S3: 8 connections
     */
    public LeastConnectionsLoadBalancer(List<Server> servers) {
        this.servers = new CopyOnWriteArrayList<>(servers);
    }

    @Override
    public Server selectServer(Request request) {
        if (servers.isEmpty()) {
            throw new NoAvailableServerException("No servers available");
        }

        List<Server> availableServers = servers.stream()
            .filter(Server::isHealthy)
            .collect(Collectors.toList());

        if (availableServers.isEmpty()) {
            throw new NoAvailableServerException("No healthy servers");
        }

        // Find server with minimum active connections
        Server selected = availableServers.stream()
            .min(Comparator.comparingInt(Server::getActiveConnections))
            .orElseThrow(() ->
                new NoAvailableServerException("No server selected")
            );

        log.debug("Selected server {} ({} connections)",
            selected.getId(), selected.getActiveConnections());

        return selected;
    }

    /**
     * Track connection lifecycle
     */
    public void onRequestStart(Server server) {
        server.incrementConnections();
    }

    public void onRequestComplete(Server server) {
        server.decrementConnections();
    }
}

/**
 * Connection tracking interceptor
 */
@Component
public class ConnectionTrackingInterceptor implements HandlerInterceptor {

    @Autowired
    private LeastConnectionsLoadBalancer loadBalancer;

    private static final String SERVER_ATTR = "selected_server";

    @Override
    public boolean preHandle(
            HttpServletRequest request,
            HttpServletResponse response,
            Object handler) {

        // Get selected server from request attribute
        Server server = (Server) request.getAttribute(SERVER_ATTR);
        if (server != null) {
            loadBalancer.onRequestStart(server);
        }

        return true;
    }

    @Override
    public void afterCompletion(
            HttpServletRequest request,
            HttpServletResponse response,
            Object handler,
            Exception ex) {

        // Decrement connection count
        Server server = (Server) request.getAttribute(SERVER_ATTR);
        if (server != null) {
            loadBalancer.onRequestComplete(server);
        }
    }
}
```

### Example 4: Weighted Least Connections

```java
@Component
public class WeightedLeastConnectionsLoadBalancer implements LoadBalancer {

    private final List<WeightedServer> servers;

    /**
     * Weighted Least Connections Load Balancer
     *
     * Formula: Score = ActiveConnections / Weight
     * Lower score = less loaded (considering capacity)
     *
     * Example:
     * S1: 40 conn, weight=100 → 40/100 = 0.40
     * S2: 30 conn, weight=50  → 30/50  = 0.60
     * S3: 10 conn, weight=25  → 10/25  = 0.40
     *
     * S1 or S3 selected (lowest score)
     */
    public WeightedLeastConnectionsLoadBalancer(List<WeightedServer> servers) {
        this.servers = new CopyOnWriteArrayList<>(servers);
    }

    @Override
    public Server selectServer(Request request) {
        if (servers.isEmpty()) {
            throw new NoAvailableServerException("No servers available");
        }

        List<WeightedServer> availableServers = servers.stream()
            .filter(Server::isHealthy)
            .collect(Collectors.toList());

        if (availableServers.isEmpty()) {
            throw new NoAvailableServerException("No healthy servers");
        }

        // Calculate scores and select minimum
        WeightedServer selected = availableServers.stream()
            .min(Comparator.comparingDouble(this::calculateScore))
            .orElseThrow(() ->
                new NoAvailableServerException("No server selected")
            );

        log.debug("Selected server {} (score: {:.2f}, conn: {}, weight: {})",
            selected.getId(),
            calculateScore(selected),
            selected.getActiveConnections(),
            selected.getWeight());

        return selected;
    }

    /**
     * Calculate load score
     * Lower score = less loaded
     */
    private double calculateScore(WeightedServer server) {
        if (server.getWeight() == 0) {
            return Double.MAX_VALUE; // Avoid division by zero
        }

        return (double) server.getActiveConnections() / server.getWeight();
    }

    /**
     * Dynamic weight adjustment based on performance
     */
    public void adjustWeights() {
        for (WeightedServer server : servers) {
            if (!server.isHealthy()) {
                continue;
            }

            // Adjust weight based on response time
            double avgResponseTime = server.getAvgResponseTime();

            if (avgResponseTime < 50) {
                // Very fast: increase weight
                server.setWeight(Math.min(100, server.getWeight() + 5));
            } else if (avgResponseTime > 200) {
                // Slow: decrease weight
                server.setWeight(Math.max(1, server.getWeight() - 5));
            }
        }
    }
}
```

### Example 5: Consistent Hashing

```java
@Component
public class ConsistentHashingLoadBalancer implements LoadBalancer {

    private final TreeMap<Long, Server> ring;
    private final List<Server> servers;
    private final int virtualNodesPerServer;
    private final HashFunction hashFunction;

    /**
     * Consistent Hashing Load Balancer
     *
     * Hash Ring:
     *              0
     *              ●
     *            ╱   ╲
     *          ╱       ╲
     *     S1-v1 ●     ● S2-v1
     *         ╱         ╲
     *        ╱           ╲
     *       ●─────────────●
     *    S3-v1          S1-v2
     *
     * Virtual nodes improve distribution
     */
    public ConsistentHashingLoadBalancer(
            List<Server> servers,
            int virtualNodesPerServer) {

        this.servers = new CopyOnWriteArrayList<>(servers);
        this.virtualNodesPerServer = virtualNodesPerServer;
        this.ring = new TreeMap<>();
        this.hashFunction = Hashing.murmur3_128();

        // Build initial ring
        servers.forEach(this::addServerToRing);
    }

    @Override
    public Server selectServer(Request request) {
        if (ring.isEmpty()) {
            throw new NoAvailableServerException("No servers available");
        }

        // Get routing key (e.g., client IP, session ID)
        String routingKey = getRoutingKey(request);

        // Hash the routing key
        long hash = hash(routingKey);

        // Find next server on ring (clockwise)
        Map.Entry<Long, Server> entry = ring.ceilingEntry(hash);

        // Wrap around if needed
        if (entry == null) {
            entry = ring.firstEntry();
        }

        Server selected = entry.getValue();

        // If server unhealthy, try next one
        if (!selected.isHealthy()) {
            return selectNextHealthyServer(hash);
        }

        log.debug("Selected server {} for key {} (hash: {})",
            selected.getId(), routingKey, hash);

        return selected;
    }

    /**
     * Add server to hash ring with virtual nodes
     */
    private void addServerToRing(Server server) {
        for (int i = 0; i < virtualNodesPerServer; i++) {
            String virtualNodeKey = server.getId() + "#" + i;
            long hash = hash(virtualNodeKey);
            ring.put(hash, server);
        }

        log.info("Added server {} with {} virtual nodes",
            server.getId(), virtualNodesPerServer);
    }

    /**
     * Remove server from hash ring
     */
    private void removeServerFromRing(Server server) {
        for (int i = 0; i < virtualNodesPerServer; i++) {
            String virtualNodeKey = server.getId() + "#" + i;
            long hash = hash(virtualNodeKey);
            ring.remove(hash);
        }

        log.info("Removed server {} from ring", server.getId());
    }

    /**
     * Find next healthy server on ring
     */
    private Server selectNextHealthyServer(long startHash) {
        // Try up to ring size times
        int attempts = 0;
        long currentHash = startHash;

        while (attempts < ring.size()) {
            Map.Entry<Long, Server> entry = ring.higherEntry(currentHash);

            if (entry == null) {
                entry = ring.firstEntry();
            }

            if (entry.getValue().isHealthy()) {
                return entry.getValue();
            }

            currentHash = entry.getKey();
            attempts++;
        }

        throw new NoAvailableServerException("No healthy servers on ring");
    }

    /**
     * Hash function
     */
    private long hash(String key) {
        return hashFunction.hashString(key, StandardCharsets.UTF_8)
            .asLong();
    }

    /**
     * Get routing key from request
     */
    private String getRoutingKey(Request request) {
        // Priority: Session ID > User ID > IP Address
        String sessionId = request.getSessionId();
        if (sessionId != null) {
            return "session:" + sessionId;
        }

        String userId = request.getUserId();
        if (userId != null) {
            return "user:" + userId;
        }

        return "ip:" + request.getClientIp();
    }

    @Override
    public void addServer(Server server) {
        servers.add(server);
        addServerToRing(server);
    }

    @Override
    public void removeServer(Server server) {
        servers.remove(server);
        removeServerFromRing(server);
    }

    /**
     * Get distribution statistics
     */
    public Map<String, Integer> getDistributionStats() {
        Map<String, Integer> stats = new HashMap<>();

        for (Server server : servers) {
            long count = ring.values().stream()
                .filter(s -> s.getId().equals(server.getId()))
                .count();
            stats.put(server.getId(), (int) count);
        }

        return stats;
    }
}
```

### Example 6: Health Check Manager

```java
@Component
public class HealthCheckManager {

    @Autowired
    private RestTemplate restTemplate;

    @Autowired
    private ApplicationEventPublisher eventPublisher;

    private final ScheduledExecutorService scheduler =
        Executors.newScheduledThreadPool(5);

    /**
     * Health Check Configuration
     */
    @Value("${healthcheck.interval:5}")
    private int intervalSeconds;

    @Value("${healthcheck.timeout:2}")
    private int timeoutSeconds;

    @Value("${healthcheck.unhealthy-threshold:3}")
    private int unhealthyThreshold;

    @Value("${healthcheck.healthy-threshold:2}")
    private int healthyThreshold;

    /**
     * Start health checks for all servers
     */
    public void startHealthChecks(List<Server> servers) {
        for (Server server : servers) {
            scheduler.scheduleAtFixedRate(
                () -> checkHealth(server),
                0,
                intervalSeconds,
                TimeUnit.SECONDS
            );
        }

        log.info("Started health checks for {} servers", servers.size());
    }

    /**
     * Perform health check
     */
    private void checkHealth(Server server) {
        try {
            long startTime = System.currentTimeMillis();

            // Send health check request
            String healthUrl = server.getUrl() + "/health";

            ResponseEntity<HealthCheckResponse> response =
                restTemplate.exchange(
                    healthUrl,
                    HttpMethod.GET,
                    null,
                    HealthCheckResponse.class
                );

            long responseTime = System.currentTimeMillis() - startTime;

            // Update server metrics
            server.setLastHealthCheck(System.currentTimeMillis());
            updateResponseTime(server, responseTime);

            // Check if response is healthy
            if (response.getStatusCode().is2xxSuccessful()) {
                handleHealthyResponse(server, response.getBody());
            } else {
                handleUnhealthyResponse(server,
                    "HTTP " + response.getStatusCode());
            }

        } catch (Exception e) {
            handleUnhealthyResponse(server, e.getMessage());
        }
    }

    /**
     * Handle healthy response
     */
    private void handleHealthyResponse(
            Server server,
            HealthCheckResponse response) {

        server.incrementConsecutiveSuccesses();
        server.resetConsecutiveFailures();

        // Mark healthy if threshold met
        if (!server.isHealthy() &&
            server.getConsecutiveSuccesses() >= healthyThreshold) {

            server.setHealthy(true);

            log.info("Server {} marked HEALTHY", server.getId());

            eventPublisher.publishEvent(
                new ServerHealthChangedEvent(server, true)
            );
        }
    }

    /**
     * Handle unhealthy response
     */
    private void handleUnhealthyResponse(Server server, String reason) {
        server.incrementConsecutiveFailures();
        server.resetConsecutiveSuccesses();

        log.warn("Health check failed for server {}: {}",
            server.getId(), reason);

        // Mark unhealthy if threshold met
        if (server.isHealthy() &&
            server.getConsecutiveFailures() >= unhealthyThreshold) {

            server.setHealthy(false);

            log.error("Server {} marked UNHEALTHY after {} failures",
                server.getId(), unhealthyThreshold);

            eventPublisher.publishEvent(
                new ServerHealthChangedEvent(server, false)
            );
        }
    }

    /**
     * Update moving average response time
     */
    private void updateResponseTime(Server server, long responseTime) {
        double currentAvg = server.getAvgResponseTime();

        // Exponential moving average (alpha = 0.3)
        double newAvg = (currentAvg * 0.7) + (responseTime * 0.3);

        server.setAvgResponseTime(newAvg);
    }

    /**
     * Shutdown health checks
     */
    @PreDestroy
    public void shutdown() {
        scheduler.shutdown();
        try {
            if (!scheduler.awaitTermination(5, TimeUnit.SECONDS)) {
                scheduler.shutdownNow();
            }
        } catch (InterruptedException e) {
            scheduler.shutdownNow();
            Thread.currentThread().interrupt();
        }
    }
}

/**
 * Health Check Response
 */
@Data
public class HealthCheckResponse {
    private String status;
    private long timestamp;
    private Map<String, Object> checks;
    private Map<String, Object> metrics;
}

/**
 * Health Check Endpoint (in backend service)
 */
@RestController
public class HealthCheckController {

    @Autowired
    private DataSource dataSource;

    @Autowired
    private RedisTemplate redisTemplate;

    /**
     * Basic health check
     */
    @GetMapping("/health")
    public ResponseEntity<HealthCheckResponse> health() {
        HealthCheckResponse response = new HealthCheckResponse();
        response.setStatus("healthy");
        response.setTimestamp(System.currentTimeMillis());

        return ResponseEntity.ok(response);
    }

    /**
     * Detailed health check
     */
    @GetMapping("/health/detailed")
    public ResponseEntity<HealthCheckResponse> detailedHealth() {
        HealthCheckResponse response = new HealthCheckResponse();
        response.setTimestamp(System.currentTimeMillis());

        Map<String, Object> checks = new HashMap<>();

        // Check database
        checks.put("database", checkDatabase());

        // Check Redis
        checks.put("redis", checkRedis());

        // Check disk space
        checks.put("disk", checkDiskSpace());

        response.setChecks(checks);

        // Add metrics
        Map<String, Object> metrics = new HashMap<>();
        metrics.put("activeConnections", getActiveConnections());
        metrics.put("cpuUsage", getCpuUsage());
        metrics.put("memoryUsage", getMemoryUsage());
        response.setMetrics(metrics);

        // Determine overall status
        boolean allHealthy = checks.values().stream()
            .allMatch(check ->
                ((Map<String, Object>) check).get("status").equals("healthy")
            );

        response.setStatus(allHealthy ? "healthy" : "unhealthy");

        HttpStatus httpStatus = allHealthy ?
            HttpStatus.OK : HttpStatus.SERVICE_UNAVAILABLE;

        return ResponseEntity.status(httpStatus).body(response);
    }

    /**
     * Readiness check (Kubernetes)
     */
    @GetMapping("/health/readiness")
    public ResponseEntity<String> readiness() {
        // Check if app is ready to serve traffic
        boolean databaseReady = checkDatabase().get("status").equals("healthy");
        boolean redisReady = checkRedis().get("status").equals("healthy");

        if (databaseReady && redisReady) {
            return ResponseEntity.ok("ready");
        } else {
            return ResponseEntity.status(503).body("not ready");
        }
    }

    /**
     * Liveness check (Kubernetes)
     */
    @GetMapping("/health/liveness")
    public ResponseEntity<String> liveness() {
        // Check if app is alive (not deadlocked)
        // Simple check: if we can respond, we're alive
        return ResponseEntity.ok("alive");
    }

    private Map<String, Object> checkDatabase() {
        Map<String, Object> check = new HashMap<>();
        try {
            long start = System.currentTimeMillis();
            dataSource.getConnection().close();
            long duration = System.currentTimeMillis() - start;

            check.put("status", "healthy");
            check.put("responseTime", duration);
            check.put("details", "Connected to database");
        } catch (Exception e) {
            check.put("status", "unhealthy");
            check.put("error", e.getMessage());
        }
        return check;
    }

    private Map<String, Object> checkRedis() {
        Map<String, Object> check = new HashMap<>();
        try {
            long start = System.currentTimeMillis();
            redisTemplate.opsForValue().get("health:check");
            long duration = System.currentTimeMillis() - start;

            check.put("status", "healthy");
            check.put("responseTime", duration);
            check.put("details", "Connected to Redis");
        } catch (Exception e) {
            check.put("status", "unhealthy");
            check.put("error", e.getMessage());
        }
        return check;
    }

    private Map<String, Object> checkDiskSpace() {
        Map<String, Object> check = new HashMap<>();
        File root = new File("/");
        long usableSpace = root.getUsableSpace();
        long totalSpace = root.getTotalSpace();
        double usagePercent = (1 - ((double) usableSpace / totalSpace)) * 100;

        check.put("usagePercent", usagePercent);
        check.put("available", usableSpace);

        if (usagePercent > 90) {
            check.put("status", "unhealthy");
            check.put("details", "Disk space critical");
        } else if (usagePercent > 80) {
            check.put("status", "warning");
            check.put("details", "Disk space high");
        } else {
            check.put("status", "healthy");
        }

        return check;
    }

    private int getActiveConnections() {
        // Implementation depends on connection pool
        return 45; // Placeholder
    }

    private double getCpuUsage() {
        OperatingSystemMXBean osBean =
            ManagementFactory.getOperatingSystemMXBean();
        return osBean.getSystemLoadAverage();
    }

    private double getMemoryUsage() {
        MemoryMXBean memoryBean = ManagementFactory.getMemoryMXBean();
        MemoryUsage heapUsage = memoryBean.getHeapMemoryUsage();
        return (double) heapUsage.getUsed() / heapUsage.getMax() * 100;
    }
}
```

---

## When to Use Which Algorithm

### Decision Matrix

```
┌─────────────────────────────────────────────────────────┐
│         Load Balancing Algorithm Selection              │
└─────────────────────────────────────────────────────────┘

┌───────────────────┬────────────────┬──────────────────┐
│    Use Case       │   Algorithm    │     Reason       │
├───────────────────┼────────────────┼──────────────────┤
│ Uniform servers   │ Round Robin    │ Simple, fair     │
│ Same request size │                │                  │
├───────────────────┼────────────────┼──────────────────┤
│ Different server  │ Weighted RR    │ Capacity-aware   │
│ capacities        │                │                  │
├───────────────────┼────────────────┼──────────────────┤
│ Long-lived        │ Least          │ Adapts to load   │
│ connections       │ Connections    │                  │
│ (WebSocket, DB)   │                │                  │
├───────────────────┼────────────────┼──────────────────┤
│ Session affinity  │ IP Hash or     │ Sticky sessions  │
│ needed            │ Consistent Hash│                  │
├───────────────────┼────────────────┼──────────────────┤
│ Frequent scaling  │ Consistent     │ Minimal          │
│ Dynamic servers   │ Hashing        │ disruption       │
├───────────────────┼────────────────┼──────────────────┤
│ Performance-aware │ Least Response │ Routes to fastest│
│ Varying latency   │ Time           │ servers          │
└───────────────────┴────────────────┴──────────────────┘

Detailed Scenarios:
┌─────────────────────────────────────────────────────┐
│ Scenario 1: E-commerce Website                     │
│                                                     │
│ Requirements:                                       │
│ • Stateless (using Redis for sessions)             │
│ • Uniform servers (AWS EC2 same instance type)     │
│ • High traffic, short requests                     │
│                                                     │
│ Recommended: Round Robin                            │
│ Reason: Simple, even distribution, no affinity      │
│         needed (stateless)                          │
└─────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────┐
│ Scenario 2: Real-time Chat Application             │
│                                                     │
│ Requirements:                                       │
│ • WebSocket connections (long-lived)                │
│ • Session affinity needed                          │
│ • Servers may have different load                  │
│                                                     │
│ Recommended: Weighted Least Connections +           │
│              Consistent Hashing                     │
│ Reason: Balances connections, maintains affinity,  │
│         handles scaling gracefully                  │
└─────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────┐
│ Scenario 3: Microservices (Internal)               │
│                                                     │
│ Requirements:                                       │
│ • Many small services                              │
│ • Frequent deployments (pods come/go)              │
│ • No session state                                 │
│                                                     │
│ Recommended: Weighted Round Robin or                │
│              Least Connections                      │
│ Reason: Adapts to pod availability, considers      │
│         resource limits (CPU/memory requests)       │
└─────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────┐
│ Scenario 4: API Gateway                            │
│                                                     │
│ Requirements:                                       │
│ • Route to different backend versions              │
│ • Some servers more powerful than others           │
│ • Need performance monitoring                      │
│                                                     │
│ Recommended: Weighted Round Robin +                 │
│              Least Response Time                    │
│ Reason: Capacity-aware, performance-based routing, │
│         version-based weighting                     │
└─────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────┐
│ Scenario 5: Database Connection Pool               │
│                                                     │
│ Requirements:                                       │
│ • Read replicas (same spec)                        │
│ • Long-running queries                             │
│ • Fair distribution                                │
│                                                     │
│ Recommended: Least Connections                      │
│ Reason: Prevents overloading replicas with slow    │
│         queries, adapts to query duration           │
└─────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────┐
│ Scenario 6: CDN / Cache Layer                      │
│                                                     │
│ Requirements:                                       │
│ • Maximize cache hits                              │
│ • Same content should hit same server              │
│ • Handle server failures gracefully                │
│                                                     │
│ Recommended: Consistent Hashing                     │
│ Reason: Sticky routing (cache locality), minimal   │
│         cache invalidation when servers change      │
└─────────────────────────────────────────────────────┘
```

---

## Interview Questions & Answers

### Q1: Explain the difference between Layer 4 and Layer 7 load balancing

**Answer:**

**Layer 4 (Transport Layer):**
- Works with TCP/UDP packets
- Routes based on IP address and port
- Cannot inspect application data
- Fast (no payload inspection)
- Protocol-agnostic

**Layer 7 (Application Layer):**
- Works with HTTP/HTTPS requests
- Routes based on URL, headers, cookies
- Can inspect and modify content
- Slower (full payload inspection)
- Application-aware

**Example:**

```
Layer 4:
Client (IP: 1.2.3.4) → Port 443 → Server A
(All HTTPS traffic goes to same server)

Layer 7:
Client → /api/users → Server A (API cluster)
Client → /images/* → Server B (CDN)
Client → Header: Version: v2 → Server C (v2 cluster)
(Routes based on content)
```

**When to use:**
- Layer 4: High performance, simple routing, non-HTTP protocols
- Layer 7: Content-based routing, SSL termination, URL rewriting

### Q2: How does Round Robin fail with different request durations?

**Answer:**

Round Robin assumes all requests take similar time. With varying durations, it creates imbalance.

**Example:**
```
Servers: S1, S2, S3
Requests:
- A: 1 second
- B: 10 seconds (slow database query)
- C: 1 second
- D: 1 second

Round Robin distribution:
Time 0s:  S1 gets Request A (1s)
Time 1s:  S2 gets Request B (10s)
Time 2s:  S3 gets Request C (1s)
Time 3s:  S1 gets Request D (1s)

Timeline:
S1: A──|D──| (done at 4s)
S2: B────────────| (done at 11s)
S3: C──| (done at 3s)

Result: S2 overloaded, S3 idle!
```

**Solution:** Use Least Connections or Least Response Time, which adapts to actual load.

### Q3: Explain consistent hashing and why it's better than simple hash

**Answer:**

**Simple Hash:**
```
Server = hash(key) % server_count

Problem when adding/removing servers:
Before (4 servers): User A → 12345 % 4 = 1 → Server 1
After (5 servers):  User A → 12345 % 5 = 0 → Server 0

All users remapped! Sessions lost!
```

**Consistent Hashing:**
```
Place servers on hash ring:
S1 at position 1,234,567
S2 at position 2,345,678
S3 at position 3,456,789

Client routes to next server clockwise.

Add Server 4 at position 1,800,000:
Only clients between S1 and S4 are affected.
~20-25% remapped instead of 100%!
```

**Virtual Nodes:**
Instead of 1 position per server, use 100-200 virtual nodes for better distribution.

**Use case:** Distributed caches (Memcached, Redis cluster), CDNs, anything needing stable routing.

### Q4: What is the weighted round robin smooth algorithm?

**Answer:**

Smooth weighted round robin distributes requests evenly over time instead of in bursts.

**Traditional (Consecutive):**
```
S1 (weight 5), S2 (weight 3), S3 (weight 2)

Requests: S1, S1, S1, S1, S1, S2, S2, S2, S3, S3
          └──── burst ────┘  └─ burst ─┘ └─burst─┘

Problem: S1 gets 5 requests in a row, causing spike
```

**Smooth Algorithm:**
```
Track current_weight for each server.

Each round:
1. Add configured weight to current_weight
2. Select server with highest current_weight
3. Subtract total_weight from selected server

Example:
Initial: S1(0), S2(0), S3(0)

Round 1: Add weights: S1(5), S2(3), S3(2)
         Select S1 (max), subtract 10: S1(-5), S2(3), S3(2)

Round 2: Add weights: S1(0), S2(6), S3(4)
         Select S2 (max), subtract 10: S1(0), S2(-4), S3(4)

Round 3: Add weights: S1(5), S2(-1), S3(6)
         Select S3 (max), subtract 10: S1(5), S2(-1), S3(-4)

Requests: S1, S2, S3, S1, S2, S1, S3, S1, S2, S1
          (evenly distributed!)
```

**Benefit:** Prevents load spikes, smoother distribution.

### Q5: How do you handle health checks without impacting performance?

**Answer:**

**Strategies:**

1. **Passive Health Checks (Preferred for production traffic):**
```
Monitor real requests:
- Track failure rate
- Track response time
- Track timeout rate

If server fails 3 consecutive requests → Mark unhealthy
No extra network calls needed
```

2. **Active Health Checks (Lightweight):**
```
Use separate health endpoint: GET /health
- Return quickly (< 50ms)
- Cache expensive checks
- Don't check dependencies every time

Example:
GET /health → 200 OK (just check if app alive)
GET /health/deep → Check DB, cache, etc. (less frequent)
```

3. **Frequency Tuning:**
```
Normal:     Check every 5 seconds
Degraded:   Check every 2 seconds
Unhealthy:  Check every 10 seconds

Reduce checks for unhealthy servers (they're already out of pool)
```

4. **Circuit Breaker Pattern:**
```
After 5 consecutive failures → Stop checking for 30s
(Assume still unhealthy, reduce wasted checks)

After 30s → Resume checking
```

**Configuration example:**
```yaml
healthCheck:
  interval: 5s
  timeout: 2s
  unhealthyThreshold: 3
  healthyThreshold: 2
  path: /health
```

### Q6: Explain the trade-offs of sticky sessions

**Answer:**

**Sticky Sessions (Session Affinity):**

**Pros:**
```
✓ Simple session management (no shared store)
✓ Better cache locality (same server = cached data)
✓ Reduced latency (no session lookup)
```

**Cons:**
```
✗ Uneven load distribution
✗ Session loss on server failure
✗ Scaling complexity
✗ Harder to drain servers (active sessions)
```

**Example problem:**
```
User A: Long session (2 hours) → Server 1
User B: Long session (2 hours) → Server 1
User C: Long session (2 hours) → Server 1
User D: Short session (5 min) → Server 2

Server 1: Overloaded
Server 2: Idle

Can't rebalance without disrupting users!
```

**Better approach: Stateless sessions**
```
Store sessions in:
- Redis (distributed cache)
- Database
- JWT tokens (client-side)

Benefits:
✓ Any server can handle any request
✓ Easy scaling
✓ No session loss
✓ Even distribution
```

**When sticky sessions are OK:**
- Small applications
- Short sessions
- Non-critical data

**When to avoid:**
- Large-scale applications
- Long sessions
- Frequent scaling

### Q7: How do you implement graceful shutdown with load balancers?

**Answer:**

**Graceful Shutdown Process:**

```
1. Stop accepting new connections
2. Wait for existing requests to complete
3. Drain all connections
4. Shutdown

Timeline:
Time 0s:  Server receives shutdown signal
         ├─ Deregister from load balancer
         └─ Stop accepting new requests

Time 5s:  Load balancer stops routing to server
         (active connections: 50 → 45 → 40 ...)

Time 30s: Most connections drained
         (active connections: 10 → 5 → 2)

Time 60s: Force close remaining connections
         Shutdown complete
```

**Implementation:**

```java
@Component
public class GracefulShutdown {

    @Autowired
    private LoadBalancer loadBalancer;

    @Autowired
    private Server currentServer;

    private volatile boolean shuttingDown = false;

    @PreDestroy
    public void shutdown() throws InterruptedException {
        log.info("Initiating graceful shutdown");

        // Step 1: Deregister from load balancer
        loadBalancer.removeServer(currentServer);
        log.info("Deregistered from load balancer");

        // Step 2: Mark as shutting down
        shuttingDown = true;

        // Step 3: Wait for connections to drain
        int waitTime = 0;
        int maxWaitTime = 60; // 60 seconds

        while (currentServer.getActiveConnections() > 0 &&
               waitTime < maxWaitTime) {

            log.info("Waiting for {} connections to drain",
                currentServer.getActiveConnections());

            Thread.sleep(1000);
            waitTime++;
        }

        // Step 4: Force close if timeout
        if (currentServer.getActiveConnections() > 0) {
            log.warn("Force closing {} remaining connections",
                currentServer.getActiveConnections());
        }

        log.info("Graceful shutdown complete");
    }

    public boolean isShuttingDown() {
        return shuttingDown;
    }
}
```

**Load Balancer Integration:**
```java
@Component
public class HealthCheckController {

    @Autowired
    private GracefulShutdown gracefulShutdown;

    @GetMapping("/health/readiness")
    public ResponseEntity<String> readiness() {
        // Return unhealthy during shutdown
        if (gracefulShutdown.isShuttingDown()) {
            return ResponseEntity.status(503).body("shutting down");
        }

        return ResponseEntity.ok("ready");
    }
}
```

### Q8: How would you implement a custom load balancing algorithm?

**Answer:**

**Interface:**
```java
public interface LoadBalancer {
    Server selectServer(Request request);
    void addServer(Server server);
    void removeServer(Server server);
}
```

**Custom Algorithm Example: Latency + Load Hybrid**

```java
@Component
public class HybridLoadBalancer implements LoadBalancer {

    /**
     * Score = (ResponseTime * 0.6) + (Connections * 0.4)
     *
     * Considers both performance and load
     */

    @Override
    public Server selectServer(Request request) {
        List<Server> available = servers.stream()
            .filter(Server::isHealthy)
            .collect(Collectors.toList());

        if (available.isEmpty()) {
            throw new NoAvailableServerException();
        }

        // Calculate score for each server
        return available.stream()
            .min(Comparator.comparingDouble(this::calculateScore))
            .orElseThrow();
    }

    private double calculateScore(Server server) {
        // Normalize metrics
        double avgResponseTime = server.getAvgResponseTime();
        double maxResponseTime = 1000.0; // 1 second

        double normalizedResponseTime =
            Math.min(avgResponseTime / maxResponseTime, 1.0);

        double activeConnections = server.getActiveConnections();
        double maxConnections = 1000.0;

        double normalizedConnections =
            Math.min(activeConnections / maxConnections, 1.0);

        // Weighted score
        return (normalizedResponseTime * 0.6) +
               (normalizedConnections * 0.4);
    }
}
```

**Custom Algorithm Example: Geographic Routing**

```java
@Component
public class GeoLoadBalancer implements LoadBalancer {

    /**
     * Route to nearest datacenter
     */

    @Override
    public Server selectServer(Request request) {
        String clientCountry = request.getCountry();

        // Find servers in same region
        List<Server> regionalServers = servers.stream()
            .filter(Server::isHealthy)
            .filter(s -> s.getRegion().equals(getRegion(clientCountry)))
            .collect(Collectors.toList());

        if (regionalServers.isEmpty()) {
            // Fallback to any healthy server
            regionalServers = servers.stream()
                .filter(Server::isHealthy)
                .collect(Collectors.toList());
        }

        // Use least connections within region
        return regionalServers.stream()
            .min(Comparator.comparingInt(Server::getActiveConnections))
            .orElseThrow();
    }

    private String getRegion(String country) {
        // Map countries to regions
        if (Arrays.asList("US", "CA", "MX").contains(country)) {
            return "north-america";
        } else if (Arrays.asList("GB", "FR", "DE").contains(country)) {
            return "europe";
        } else if (Arrays.asList("JP", "CN", "IN").contains(country)) {
            return "asia";
        }
        return "global";
    }
}
```

### Q9: What metrics should you monitor for load balancers?

**Answer:**

**Key Metrics:**

```
┌─────────────────────────────────────────────────┐
│ 1. Request Metrics                              │
│    • Requests per second (total)                │
│    • Requests per server                        │
│    • Request distribution (evenness)            │
│    • Error rate (% failed)                      │
│    • Latency (p50, p95, p99)                    │
│                                                 │
│ 2. Server Health Metrics                        │
│    • Healthy server count                       │
│    • Unhealthy server count                     │
│    • Health check success rate                  │
│    • Time since last health check               │
│                                                 │
│ 3. Connection Metrics                           │
│    • Active connections per server              │
│    • Connection rate (new/sec)                  │
│    • Connection duration (avg)                  │
│    • Connection errors                          │
│                                                 │
│ 4. Performance Metrics                          │
│    • Response time per server                   │
│    • Queue depth                                │
│    • Timeout rate                               │
│    • Retry rate                                 │
│                                                 │
│ 5. Algorithm-Specific Metrics                   │
│    • Hash distribution (consistent hashing)     │
│    • Cache hit rate (sticky sessions)           │
│    • Weight effectiveness (weighted RR)         │
└─────────────────────────────────────────────────┘
```

**Dashboard Example:**
```
┌────────────────────────────────────────────┐
│ Load Balancer Dashboard                    │
├────────────────────────────────────────────┤
│ Total Requests:    1,245,823/min          │
│ Error Rate:        0.02%                   │
│ Avg Latency:       45ms (p99: 120ms)      │
│                                            │
│ Servers:                                   │
│ ✓ Server 1: 312,000 req (25%)             │
│ ✓ Server 2: 315,000 req (25%)             │
│ ✓ Server 3: 310,000 req (25%)             │
│ ✗ Server 4: DOWN (0%)                     │
│                                            │
│ Health:                                    │
│ Healthy: 3/4 (75%)                         │
│ Degraded: 0                                │
│ Unhealthy: 1                               │
└────────────────────────────────────────────┘
```

**Alerting Rules:**
```
CRITICAL:
- Healthy servers < 50%
- Error rate > 5%
- p99 latency > 1000ms

WARNING:
- Healthy servers < 75%
- Error rate > 1%
- Uneven distribution (>20% variance)

INFO:
- Server marked unhealthy
- Server added/removed
```

### Q10: How do you test a load balancer implementation?

**Answer:**

**Testing Strategy:**

**1. Unit Tests:**
```java
@Test
public void testRoundRobinDistribution() {
    LoadBalancer lb = new RoundRobinLoadBalancer(
        Arrays.asList(server1, server2, server3)
    );

    // Send 300 requests
    Map<String, Integer> distribution = new HashMap<>();
    for (int i = 0; i < 300; i++) {
        Server selected = lb.selectServer(new Request());
        distribution.merge(selected.getId(), 1, Integer::sum);
    }

    // Each server should get 100 requests (±5)
    assertEquals(100, distribution.get("server1"), 5);
    assertEquals(100, distribution.get("server2"), 5);
    assertEquals(100, distribution.get("server3"), 5);
}

@Test
public void testHealthyServerSelection() {
    server2.setHealthy(false); // Mark unhealthy

    LoadBalancer lb = new RoundRobinLoadBalancer(
        Arrays.asList(server1, server2, server3)
    );

    // Send 100 requests
    for (int i = 0; i < 100; i++) {
        Server selected = lb.selectServer(new Request());
        assertNotEquals("server2", selected.getId());
    }
}
```

**2. Integration Tests:**
```java
@SpringBootTest
@Test
public void testLoadBalancerWithRealServers() {
    // Start 3 test servers
    TestServer server1 = startTestServer(8081);
    TestServer server2 = startTestServer(8082);
    TestServer server3 = startTestServer(8083);

    // Configure load balancer
    LoadBalancer lb = configureLoadBalancer(server1, server2, server3);

    // Send requests and verify distribution
    for (int i = 0; i < 300; i++) {
        Response response = sendRequest(lb);
        assertEquals(200, response.getStatus());
    }

    // Check each server received requests
    assertTrue(server1.getRequestCount() > 0);
    assertTrue(server2.getRequestCount() > 0);
    assertTrue(server3.getRequestCount() > 0);
}
```

**3. Load Tests:**
```java
@Test
public void testHighLoadPerformance() {
    LoadBalancer lb = setupLoadBalancer();

    // Simulate high load
    ExecutorService executor = Executors.newFixedThreadPool(100);
    CountDownLatch latch = new CountDownLatch(10000);

    long startTime = System.currentTimeMillis();

    for (int i = 0; i < 10000; i++) {
        executor.submit(() -> {
            try {
                Server server = lb.selectServer(new Request());
                assertNotNull(server);
            } finally {
                latch.countDown();
            }
        });
    }

    latch.await();
    long duration = System.currentTimeMillis() - startTime;

    // Should handle 10k requests in < 1 second
    assertTrue(duration < 1000);
}
```

**4. Chaos Testing:**
```java
@Test
public void testServerFailureDuringLoad() {
    LoadBalancer lb = setupLoadBalancer();

    // Start sending requests
    ExecutorService executor = Executors.newFixedThreadPool(10);
    AtomicInteger successCount = new AtomicInteger(0);
    AtomicInteger errorCount = new AtomicInteger(0);

    for (int i = 0; i < 1000; i++) {
        executor.submit(() -> {
            try {
                Server server = lb.selectServer(new Request());
                sendRequest(server);
                successCount.incrementAndGet();
            } catch (Exception e) {
                errorCount.incrementAndGet();
            }
        });

        // Kill a server midway
        if (i == 500) {
            server2.shutdown();
        }
    }

    executor.shutdown();
    executor.awaitTermination(30, TimeUnit.SECONDS);

    // Most requests should succeed despite failure
    assertTrue(successCount.get() > 900);
}
```

**5. Consistency Tests (Consistent Hashing):**
```java
@Test
public void testConsistentHashingStability() {
    ConsistentHashingLoadBalancer lb =
        new ConsistentHashingLoadBalancer(servers, 150);

    // Map clients to servers
    Map<String, String> clientToServer = new HashMap<>();
    for (int i = 0; i < 1000; i++) {
        String clientId = "client_" + i;
        Request request = new Request(clientId);
        Server server = lb.selectServer(request);
        clientToServer.put(clientId, server.getId());
    }

    // Add new server
    Server newServer = new Server("server5");
    lb.addServer(newServer);

    // Check how many clients remapped
    int remapped = 0;
    for (int i = 0; i < 1000; i++) {
        String clientId = "client_" + i;
        Request request = new Request(clientId);
        Server server = lb.selectServer(request);

        if (!server.getId().equals(clientToServer.get(clientId))) {
            remapped++;
        }
    }

    // Should remap < 30% (ideally ~20%)
    assertTrue(remapped < 300);
}
```

---

## Summary

**Load Balancer Decision Checklist:**

```
✓ Choose algorithm based on use case:
  - Round Robin: Simple, uniform servers
  - Weighted RR: Different capacities
  - Least Connections: Long-lived connections
  - Consistent Hashing: Session affinity + scaling
  - Least Response Time: Performance-aware

✓ Implement health checks:
  - Active monitoring (synthetic requests)
  - Passive monitoring (real traffic)
  - Proper thresholds (failure/success counts)
  - Graceful degradation

✓ Handle failures gracefully:
  - Circuit breaker pattern
  - Graceful shutdown
  - Connection draining
  - Failover strategies

✓ Monitor key metrics:
  - Request distribution
  - Server health
  - Response times
  - Error rates

✓ Test thoroughly:
  - Unit tests (algorithm correctness)
  - Integration tests (real servers)
  - Load tests (high volume)
  - Chaos tests (failure scenarios)
```

This comprehensive guide covers all major load balancing algorithms with detailed explanations, ASCII diagrams, production code examples, and interview preparation material for experienced developers.
