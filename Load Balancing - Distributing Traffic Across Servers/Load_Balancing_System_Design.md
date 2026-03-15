# Load Balancing - Distributing Traffic Across Servers

## 1. What is Load Balancing?

**Load Balancing** is the process of distributing incoming network traffic across multiple servers to ensure no single server becomes overwhelmed.

### Why Load Balancing is Needed:

- ✅ High availability (if one server fails, others handle traffic)
- ✅ Scalability (add more servers to handle more traffic)
- ✅ Better performance (distribute load evenly)
- ✅ Fault tolerance (automatic failover)
- ✅ No single point of failure
- ✅ Maintenance without downtime

### Visual: Problem Without Load Balancer

```
┌────────────────────────────────────────────────────────────────────────┐
│                WITHOUT LOAD BALANCER (SINGLE SERVER)                   │
└────────────────────────────────────────────────────────────────────────┘

ALL USERS HITTING ONE SERVER
─────────────────────────────

┌──────────────────────────────────────────────────────────┐
│                    100,000 USERS                         │
│                                                          │
│  👤 👤 👤 👤 👤 👤 👤 👤 👤 👤                          │
│  👤 👤 👤 👤 👤 👤 👤 👤 👤 👤                          │
│  👤 👤 👤 👤 👤 👤 👤 👤 👤 👤                          │
└────┬─────┬─────┬─────┬─────┬─────┬─────┬─────┬─────┬───┘
     │     │     │     │     │     │     │     │     │
     │     │     │     │     │     │     │     │     │
     └─────┴─────┴─────┴─────┴─────┴─────┴─────┴─────┘
                            │
                            │ ALL traffic goes here!
                            ↓
              ┌──────────────────────────┐
              │    SINGLE SERVER         │
              │    🔥 OVERLOADED!        │
              │                          │
              │  CPU: 100% 🚨            │
              │  Memory: 95% 🚨          │
              │  Response time: 10s ❌   │
              │  Many requests timeout   │
              │                          │
              │  If this fails:          │
              │  💥 ENTIRE SYSTEM DOWN   │
              └──────────────────────────┘

Problems:
❌ Single point of failure
❌ Cannot handle high traffic
❌ Slow response times
❌ No scalability
❌ Downtime during maintenance


WITH LOAD BALANCER (MULTIPLE SERVERS)
──────────────────────────────────────

┌──────────────────────────────────────────────────────────┐
│                    100,000 USERS                         │
│                                                          │
│  👤 👤 👤 👤 👤 👤 👤 👤 👤 👤                          │
│  👤 👤 👤 👤 👤 👤 👤 👤 👤 👤                          │
│  👤 👤 👤 👤 👤 👤 👤 👤 👤 👤                          │
└────┬─────┬─────┬─────┬─────┬─────┬─────┬─────┬─────┬───┘
     │     │     │     │     │     │     │     │     │
     │     │     │     │     │     │     │     │     │
     └─────┴─────┴─────┴─────┴─────┴─────┴─────┴─────┘
                            │
                            ↓
              ┌──────────────────────────┐
              │    LOAD BALANCER         │
              │    🎯 Smart Router       │
              │                          │
              │  Distributes traffic     │
              │  across servers          │
              └────┬─────┬─────┬─────┬───┘
                   │     │     │     │
        ┌──────────┼─────┼─────┼──────────┐
        │          │     │     │          │
        ↓          ↓     ↓     ↓          ↓
┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐
│ Server 1 │ │ Server 2 │ │ Server 3 │ │ Server 4 │
│          │ │          │ │          │ │          │
│ 25K users│ │ 25K users│ │ 25K users│ │ 25K users│
│          │ │          │ │          │ │          │
│ CPU: 30% │ │ CPU: 30% │ │ CPU: 30% │ │ CPU: 30% │
│ Mem: 40% │ │ Mem: 40% │ │ Mem: 40% │ │ Mem: 40% │
│ Fast ✅  │ │ Fast ✅  │ │ Fast ✅  │ │ Fast ✅  │
└──────────┘ └──────────┘ └──────────┘ └──────────┘

Benefits:
✅ Load distributed evenly
✅ Fast response times
✅ High availability
✅ Can handle more traffic
✅ If one server fails, others continue
```

## 2. Load Balancer Placement

### Visual: Where Load Balancers Sit

```
┌────────────────────────────────────────────────────────────────────────┐
│                  MULTI-TIER LOAD BALANCING                             │
└────────────────────────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────────┐
│                    INTERNET USERS                        │
│                                                          │
│  👤 Mobile   👤 Desktop   👤 Tablet   👤 IoT            │
└────────────────────────┬─────────────────────────────────┘
                         │
                         │ HTTPS requests
                         ↓
┌─────────────────────────────────────────────────────────────┐
│              LAYER 1: GLOBAL LOAD BALANCER                  │
│              (DNS-based / GeoDNS)                           │
│                                                             │
│  Routes users to nearest data center:                       │
│  • US users → US data center                                │
│  • EU users → EU data center                                │
│  • Asia users → Asia data center                            │
└────┬──────────────────────┬──────────────────────┬─────────┘
     │                      │                      │
     │ US Traffic           │ EU Traffic           │ Asia Traffic
     ↓                      ↓                      ↓
┌──────────┐         ┌──────────┐         ┌──────────┐
│ US DC    │         │ EU DC    │         │ Asia DC  │
└────┬─────┘         └────┬─────┘         └────┬─────┘
     │                    │                    │
     ↓                    ↓                    ↓


┌─────────────────────────────────────────────────────────────┐
│         LAYER 2: REGIONAL LOAD BALANCER (L4/L7)             │
│         (AWS ELB / NGINX / HAProxy)                         │
│                                                             │
│  Routes traffic to healthy application servers              │
│  • Health checks                                            │
│  • SSL termination                                          │
│  • Request routing                                          │
└────┬──────────────┬──────────────┬──────────────┬──────────┘
     │              │              │              │
     ↓              ↓              ↓              ↓
┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐
│ Web      │  │ Web      │  │ Web      │  │ Web      │
│ Server 1 │  │ Server 2 │  │ Server 3 │  │ Server 4 │
│          │  │          │  │          │  │          │
│ (Healthy)│  │ (Healthy)│  │ (Failed) │  │ (Healthy)│
│    ✅    │  │    ✅    │  │    ❌    │  │    ✅    │
└────┬─────┘  └────┬─────┘  └────┬─────┘  └────┬─────┘
     │             │             │ (Skip)       │
     │             │             │              │
     └─────────────┼─────────────┘              │
                   │                            │
                   │ API calls to backend       │
                   ↓                            ↓


┌─────────────────────────────────────────────────────────────┐
│         LAYER 3: INTERNAL LOAD BALANCER                     │
│         (Service Mesh / Internal LB)                        │
│                                                             │
│  Routes internal traffic between microservices              │
└────┬──────────────┬──────────────┬──────────────┬──────────┘
     │              │              │              │
     ↓              ↓              ↓              ↓
┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐
│ Auth     │  │ Payment  │  │ Order    │  │ User     │
│ Service  │  │ Service  │  │ Service  │  │ Service  │
└────┬─────┘  └────┬─────┘  └────┬─────┘  └────┬─────┘
     │             │             │              │
     │             │             │              │
     └─────────────┼─────────────┼──────────────┘
                   │             │
                   ↓             ↓


┌─────────────────────────────────────────────────────────────┐
│         LAYER 4: DATABASE LOAD BALANCER                     │
│         (ProxySQL / MySQL Router / PgBouncer)               │
│                                                             │
│  Routes database queries:                                   │
│  • Writes → Primary DB                                      │
│  • Reads → Read Replicas                                    │
└────┬──────────────┬──────────────┬──────────────┬──────────┘
     │              │              │              │
     ↓              ↓              ↓              ↓
┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐
│ Primary  │  │ Replica  │  │ Replica  │  │ Replica  │
│ DB       │  │ DB 1     │  │ DB 2     │  │ DB 3     │
│ (Write)  │  │ (Read)   │  │ (Read)   │  │ (Read)   │
└──────────┘  └──────────┘  └──────────┘  └──────────┘
```

## 3. Load Balancing Algorithms

### Algorithm 1: Round Robin

```
┌────────────────────────────────────────────────────────────────────────┐
│                      ROUND ROBIN ALGORITHM                             │
└────────────────────────────────────────────────────────────────────────┘

CONCEPT
───────
Distribute requests sequentially to each server in order.
After reaching the last server, start from the first again.

VISUAL FLOW
───────────

Servers available:
┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐
│ Server 1 │  │ Server 2 │  │ Server 3 │  │ Server 4 │
└──────────┘  └──────────┘  └──────────┘  └──────────┘

Request sequence:
Request 1  →  Server 1
Request 2  →  Server 2
Request 3  →  Server 3
Request 4  →  Server 4
Request 5  →  Server 1  ← Back to first
Request 6  →  Server 2
Request 7  →  Server 3
Request 8  →  Server 4
Request 9  →  Server 1  ← Cycle continues


TIMELINE VIEW
─────────────

Time  Request  →  Server
T1    Req 1   →  [Server 1]
T2    Req 2   →  [Server 2]
T3    Req 3   →  [Server 3]
T4    Req 4   →  [Server 4]
T5    Req 5   →  [Server 1]  ← Loop back
T6    Req 6   →  [Server 2]
T7    Req 7   →  [Server 3]
T8    Req 8   →  [Server 4]

Result: Each server gets equal number of requests


PSEUDOCODE
──────────

class RoundRobin {
    servers: [Server1, Server2, Server3, Server4]
    currentIndex: 0

    function getNextServer() {
        server = servers[currentIndex]
        currentIndex = (currentIndex + 1) % servers.length
        return server
    }
}

// Usage
Request 1: getNextServer() → Server1 (index 0)
Request 2: getNextServer() → Server2 (index 1)
Request 3: getNextServer() → Server3 (index 2)
Request 4: getNextServer() → Server4 (index 3)
Request 5: getNextServer() → Server1 (index 0) ← wraps around


DISTRIBUTION RESULT
───────────────────

After 100 requests:

Server 1: ▓▓▓▓▓▓▓▓▓▓▓▓▓ 25 requests (25%)
Server 2: ▓▓▓▓▓▓▓▓▓▓▓▓▓ 25 requests (25%)
Server 3: ▓▓▓▓▓▓▓▓▓▓▓▓▓ 25 requests (25%)
Server 4: ▓▓▓▓▓▓▓▓▓▓▓▓▓ 25 requests (25%)

Perfect distribution! ✅


PROS & CONS
───────────

✅ PROS:
• Simple to implement
• Fair distribution
• No server state needed
• Works well when all servers equal capacity

❌ CONS:
• Doesn't consider server load
• Doesn't consider server capacity
• Treats slow requests same as fast ones
• May overload weaker servers
```

### Algorithm 2: Weighted Round Robin

```
┌────────────────────────────────────────────────────────────────────────┐
│                  WEIGHTED ROUND ROBIN ALGORITHM                        │
└────────────────────────────────────────────────────────────────────────┘

CONCEPT
───────
Like Round Robin, but servers get weight based on capacity.
Higher weight = more requests.

SERVER CONFIGURATION
────────────────────

┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐
│ Server 1 │  │ Server 2 │  │ Server 3 │  │ Server 4 │
│          │  │          │  │          │  │          │
│ Powerful │  │ Powerful │  │ Normal   │  │ Weak     │
│          │  │          │  │          │  │          │
│ Weight:4 │  │ Weight:4 │  │ Weight:2 │  │ Weight:1 │
└──────────┘  └──────────┘  └──────────┘  └──────────┘
   16 cores     16 cores      8 cores      4 cores
   32GB RAM     32GB RAM      16GB RAM     8GB RAM


REQUEST DISTRIBUTION
────────────────────

Total weight = 4 + 4 + 2 + 1 = 11

Distribution pattern (11 requests):
Request 1  →  Server 1  (weight 4, count 1)
Request 2  →  Server 1  (weight 4, count 2)
Request 3  →  Server 1  (weight 4, count 3)
Request 4  →  Server 1  (weight 4, count 4) ← Done
Request 5  →  Server 2  (weight 4, count 1)
Request 6  →  Server 2  (weight 4, count 2)
Request 7  →  Server 2  (weight 4, count 3)
Request 8  →  Server 2  (weight 4, count 4) ← Done
Request 9  →  Server 3  (weight 2, count 1)
Request 10 →  Server 3  (weight 2, count 2) ← Done
Request 11 →  Server 4  (weight 1, count 1) ← Done

Then repeat pattern...


VISUAL DISTRIBUTION
───────────────────

After 110 requests:

Server 1 (Weight 4): ▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓ 40 requests (36%)
Server 2 (Weight 4): ▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓ 40 requests (36%)
Server 3 (Weight 2): ▓▓▓▓▓▓▓▓▓▓ 20 requests (18%)
Server 4 (Weight 1): ▓▓▓▓▓ 10 requests (9%)

Matches server capacity! ✅


PSEUDOCODE
──────────

class WeightedRoundRobin {
    servers: [
        {server: Server1, weight: 4, currentWeight: 0},
        {server: Server2, weight: 4, currentWeight: 0},
        {server: Server3, weight: 2, currentWeight: 0},
        {server: Server4, weight: 1, currentWeight: 0}
    ]

    function getNextServer() {
        totalWeight = sum(all weights)

        // Find server with highest currentWeight
        maxWeightServer = null
        for each server {
            server.currentWeight += server.weight
            if (server.currentWeight > maxWeightServer.currentWeight) {
                maxWeightServer = server
            }
        }

        // Reduce selected server's weight
        maxWeightServer.currentWeight -= totalWeight

        return maxWeightServer.server
    }
}


PROS & CONS
───────────

✅ PROS:
• Respects server capacity
• Better for heterogeneous servers
• Can adjust weights dynamically
• Fair based on capability

❌ CONS:
• More complex than basic Round Robin
• Needs configuration of weights
• Doesn't consider current load
• Static weights may not reflect real-time capacity
```

### Algorithm 3: Least Connections

```
┌────────────────────────────────────────────────────────────────────────┐
│                   LEAST CONNECTIONS ALGORITHM                          │
└────────────────────────────────────────────────────────────────────────┘

CONCEPT
───────
Route new request to server with fewest active connections.
Accounts for different request processing times.

VISUAL REPRESENTATION
─────────────────────

Current state:
┌──────────────┐  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐
│  Server 1    │  │  Server 2    │  │  Server 3    │  │  Server 4    │
│              │  │              │  │              │  │              │
│ Connections: │  │ Connections: │  │ Connections: │  │ Connections: │
│    👤👤👤   │  │    👤👤👤   │  │    👤👤👤   │  │    👤       │
│    👤👤👤   │  │    👤👤     │  │    👤👤👤   │  │              │
│    👤        │  │              │  │    👤👤      │  │              │
│              │  │              │  │              │  │              │
│  Active: 7   │  │  Active: 5   │  │  Active: 8   │  │  Active: 1   │
└──────────────┘  └──────────────┘  └──────────────┘  └──────────────┘

New request arrives:
    👤 (New user)
     │
     ↓
Which server to choose?
     │
     ↓
Compare active connections:
Server 1: 7
Server 2: 5
Server 3: 8
Server 4: 1  ← Least connections!
     │
     ↓
Route to Server 4 ✅


STEP-BY-STEP FLOW
─────────────────

Initial state:
Server 1: 10 connections
Server 2: 10 connections
Server 3: 10 connections
Server 4: 10 connections

Time T1: Request 1 completes on Server 2
Server 1: 10 connections
Server 2: 9 connections  ← Least!
Server 3: 10 connections
Server 4: 10 connections
→ New request goes to Server 2

Time T2: Request 2 completes on Server 4
Server 1: 10 connections
Server 2: 10 connections (just got new request)
Server 3: 10 connections
Server 4: 9 connections  ← Least!
→ New request goes to Server 4

Time T3: Requests 3,4,5 complete on Server 1
Server 1: 7 connections  ← Least!
Server 2: 10 connections
Server 3: 10 connections
Server 4: 10 connections
→ New request goes to Server 1


WHY IT'S BETTER FOR VARYING REQUEST TIMES
──────────────────────────────────────────

Scenario: Some requests take longer than others

Round Robin (Bad for varying times):
Server 1: 👤(fast) 👤(fast) 👤(fast) = 3 connections, low load
Server 2: 👤(slow) 👤(slow) 👤(slow) = 3 connections, HIGH load ❌

Problem: Equal requests, but Server 2 is overloaded!

Least Connections (Good for varying times):
Server 1: 👤(fast) 👤(fast) 👤(fast) = 0 active (completed)
Server 2: 👤(slow) 👤(slow) = 2 active (still processing)
          ↓
      New requests go to Server 1 (0 < 2) ✅

Result: Load balanced based on actual current load!


PSEUDOCODE
──────────

class LeastConnections {
    servers: [
        {server: Server1, activeConnections: 0},
        {server: Server2, activeConnections: 0},
        {server: Server3, activeConnections: 0},
        {server: Server4, activeConnections: 0}
    ]

    function getNextServer() {
        // Find server with minimum connections
        minServer = servers[0]
        for each server in servers {
            if (server.activeConnections < minServer.activeConnections) {
                minServer = server
            }
        }
        return minServer.server
    }

    function onRequestStart(server) {
        server.activeConnections++
    }

    function onRequestEnd(server) {
        server.activeConnections--
    }
}


REAL-TIME TRACKING
──────────────────

┌─────────────────────────────────────────────────────┐
│  Load Balancer Dashboard                            │
├─────────────────────────────────────────────────────┤
│                                                     │
│  Server 1: ▓▓▓▓▓▓▓▓▓▓▓▓▓░░░░░░░ 15 connections     │
│  Server 2: ▓▓▓▓▓▓▓▓░░░░░░░░░░░░  8 connections     │
│  Server 3: ▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓ 20 connections ❌   │
│  Server 4: ▓▓▓▓░░░░░░░░░░░░░░░░  4 connections ✅   │
│                                                     │
│  Next request will go to: Server 4                  │
│                                                     │
└─────────────────────────────────────────────────────┘


PROS & CONS
───────────

✅ PROS:
• Accounts for actual current load
• Good for long-running requests
• Handles varying request times well
• Dynamic load balancing

❌ CONS:
• More complex to implement
• Requires tracking connection state
• Slightly higher overhead
• May not account for server capacity differences
```

### Algorithm 4: Least Response Time

```
┌────────────────────────────────────────────────────────────────────────┐
│                  LEAST RESPONSE TIME ALGORITHM                         │
└────────────────────────────────────────────────────────────────────────┘

CONCEPT
───────
Route to server with:
1. Fewest active connections
2. Lowest average response time
Combination of both factors.

FORMULA
───────
Score = (Active Connections × Weight) + (Avg Response Time × Weight)
→ Route to server with LOWEST score


VISUAL REPRESENTATION
─────────────────────

Current metrics:
┌───────────────────────────────────────────────────────┐
│  Server 1                                             │
│  Active Connections: 5                                │
│  Avg Response Time: 200ms                             │
│  Score: (5 × 1) + (200 × 0.1) = 5 + 20 = 25         │
└───────────────────────────────────────────────────────┘

┌───────────────────────────────────────────────────────┐
│  Server 2                                             │
│  Active Connections: 3                                │
│  Avg Response Time: 500ms                             │
│  Score: (3 × 1) + (500 × 0.1) = 3 + 50 = 53         │
└───────────────────────────────────────────────────────┘

┌───────────────────────────────────────────────────────┐
│  Server 3                                             │
│  Active Connections: 8                                │
│  Avg Response Time: 100ms                             │
│  Score: (8 × 1) + (100 × 0.1) = 8 + 10 = 18  ← Best!│
└───────────────────────────────────────────────────────┘

┌───────────────────────────────────────────────────────┐
│  Server 4                                             │
│  Active Connections: 2                                │
│  Avg Response Time: 800ms                             │
│  Score: (2 × 1) + (800 × 0.1) = 2 + 80 = 82         │
└───────────────────────────────────────────────────────┘

Winner: Server 3 (Score: 18) ✅


WHY IT'S BETTER
───────────────

Scenario: Server with few connections but slow performance

Least Connections Only:
Server A: 2 connections, 5000ms avg  ← Would choose (fewer connections)
Server B: 5 connections, 100ms avg   ← Should choose (faster!)

Problem: Server A is slow! ❌

Least Response Time:
Server A: Score = (2 × 1) + (5000 × 0.1) = 502
Server B: Score = (5 × 1) + (100 × 0.1) = 15  ← Choose this! ✅

Result: Better choice considering both load and speed!


RESPONSE TIME TRACKING
───────────────────────

Moving average of last 100 requests:

Server 1 Response Times:
┌────────────────────────────────────────┐
│ Request 1: 150ms                       │
│ Request 2: 200ms                       │
│ Request 3: 180ms                       │
│ ...                                    │
│ Request 100: 210ms                     │
│                                        │
│ Average: 190ms                         │
└────────────────────────────────────────┘

Update on each request completion:
New response time: 220ms
Remove oldest: 150ms
Add newest: 220ms
New average: 195ms


PSEUDOCODE
──────────

class LeastResponseTime {
    servers: [
        {
            server: Server1,
            activeConnections: 0,
            responseTimes: [],  // Last 100
            avgResponseTime: 0
        },
        // ... more servers
    ]

    function getNextServer() {
        minScore = Infinity
        selectedServer = null

        for each server in servers {
            score = (server.activeConnections × 1) +
                    (server.avgResponseTime × 0.1)

            if (score < minScore) {
                minScore = score
                selectedServer = server
            }
        }

        return selectedServer.server
    }

    function onRequestComplete(server, responseTime) {
        server.activeConnections--

        // Update moving average
        server.responseTimes.push(responseTime)
        if (server.responseTimes.length > 100) {
            server.responseTimes.shift()  // Remove oldest
        }

        // Recalculate average
        sum = server.responseTimes.reduce((a, b) => a + b, 0)
        server.avgResponseTime = sum / server.responseTimes.length
    }
}


PROS & CONS
───────────

✅ PROS:
• Most intelligent algorithm
• Considers both load and performance
• Adapts to server performance
• Best for heterogeneous environments

❌ CONS:
• Most complex to implement
• Higher overhead (tracking response times)
• Requires more memory
• May oscillate if not tuned properly
```

### Algorithm 5: IP Hash

```
┌────────────────────────────────────────────────────────────────────────┐
│                       IP HASH ALGORITHM                                │
└────────────────────────────────────────────────────────────────────────┘

CONCEPT
───────
Route requests based on client IP address hash.
Same IP → Always same server (session persistence).

HASH FUNCTION
─────────────

hash(clientIP) % numberOfServers = serverIndex

Example:
Client IP: 192.168.1.100
hash("192.168.1.100") = 1234567
1234567 % 4 = 3
→ Route to Server 3


VISUAL FLOW
───────────

User 1 (IP: 192.168.1.100)
    │
    │ hash("192.168.1.100") % 4 = 3
    ↓
┌──────────────────────────────────────┐
│  Load Balancer                       │
│                                      │
│  Calculate hash:                     │
│  IP: 192.168.1.100                   │
│  Hash: 1234567                       │
│  Server: 1234567 % 4 = 3             │
└────────┬─────────────────────────────┘
         │
         ↓
    [Server 3] ✅

Next request from same user:
    │
    │ Same IP → Same hash → Same server
    ↓
    [Server 3] ✅ (Consistent!)


SESSION PERSISTENCE
───────────────────

Problem without IP hash:

User logs in:
Request 1 → Server 1 (creates session)
Request 2 → Server 2 (no session! ❌)
Request 3 → Server 3 (no session! ❌)

User has to login multiple times! Bad experience!

With IP hash:

User logs in:
Request 1 → Server 2 (creates session)
Request 2 → Server 2 (same session ✅)
Request 3 → Server 2 (same session ✅)

User stays logged in! Good experience!


DISTRIBUTION EXAMPLE
────────────────────

4 users with different IPs:

User A (IP: 10.0.0.1)   → hash % 4 = 1 → Server 1
User B (IP: 10.0.0.2)   → hash % 4 = 2 → Server 2
User C (IP: 10.0.0.3)   → hash % 4 = 3 → Server 3
User D (IP: 10.0.0.4)   → hash % 4 = 0 → Server 4
User E (IP: 10.0.0.5)   → hash % 4 = 1 → Server 1
User F (IP: 10.0.0.6)   → hash % 4 = 2 → Server 2

All requests from User A always go to Server 1
All requests from User B always go to Server 2
And so on...


PROBLEM: ADDING/REMOVING SERVERS
─────────────────────────────────

Initial: 4 servers

User A → hash % 4 = 1 → Server 1

Add 1 server (now 5 servers):

User A → hash % 5 = 3 → Server 3  ← Changed!
Session lost! ❌

Solution: Consistent Hashing (advanced topic)


PSEUDOCODE
──────────

class IPHash {
    servers: [Server1, Server2, Server3, Server4]

    function getNextServer(clientIP) {
        hashValue = hash(clientIP)
        serverIndex = hashValue % servers.length
        return servers[serverIndex]
    }

    function hash(ip) {
        // Simple hash function
        parts = ip.split('.')
        return (parts[0] × 256³) +
               (parts[1] × 256²) +
               (parts[2] × 256) +
               (parts[3])
    }
}


USE CASES
─────────

✅ When to use IP Hash:
• Stateful applications
• Session-based apps
• WebSocket connections
• Shopping carts
• Video streaming (buffering)

❌ When NOT to use:
• Stateless applications
• Need even distribution
• Servers frequently change
• Users behind NAT (same IP)


PROS & CONS
───────────

✅ PROS:
• Session persistence
• No session storage needed
• Simple to implement
• Predictable routing

❌ CONS:
• Uneven distribution (some IPs more common)
• Problems when adding/removing servers
• Users behind NAT get same server
• Doesn't consider server load
```

## 4. Health Checks

### Visual: Health Check Mechanism

```
┌────────────────────────────────────────────────────────────────────────┐
│                      HEALTH CHECK SYSTEM                               │
└────────────────────────────────────────────────────────────────────────┘

ACTIVE HEALTH CHECKS
────────────────────

Load Balancer continuously checks server health:

┌──────────────────────────────────────┐
│  Load Balancer                       │
│                                      │
│  Every 5 seconds:                    │
│  • Send HTTP GET /health             │
│  • Expect 200 OK response            │
│  • Timeout: 2 seconds                │
└────┬─────┬─────┬─────┬───────────────┘
     │     │     │     │
     │ Check every 5s
     ↓     ↓     ↓     ↓
┌────────┐ ┌────────┐ ┌────────┐ ┌────────┐
│Server 1│ │Server 2│ │Server 3│ │Server 4│
│        │ │        │ │        │ │        │
│ GET    │ │ GET    │ │ GET    │ │ GET    │
│ /health│ │ /health│ │ /health│ │ /health│
│        │ │        │ │        │ │        │
│ 200 OK │ │ 200 OK │ │Timeout!│ │ 200 OK │
│   ✅   │ │   ✅   │ │   ❌   │ │   ✅   │
│        │ │        │ │        │ │        │
│Healthy │ │Healthy │ │Unhealthy││Healthy │
└────────┘ └────────┘ └────────┘ └────────┘
                          │
                          │ Mark as unhealthy
                          ↓
                    Stop routing traffic
                    to Server 3


HEALTH CHECK ENDPOINT
─────────────────────

Server implements /health endpoint:

GET /health HTTP/1.1
Host: server1.example.com

Response (Healthy):
HTTP/1.1 200 OK
Content-Type: application/json

{
  "status": "healthy",
  "timestamp": "2024-03-15T10:30:00Z",
  "checks": {
    "database": "ok",
    "cache": "ok",
    "disk_space": "ok",
    "cpu": "ok"
  }
}

Response (Unhealthy):
HTTP/1.1 503 Service Unavailable
Content-Type: application/json

{
  "status": "unhealthy",
  "timestamp": "2024-03-15T10:30:00Z",
  "checks": {
    "database": "error",  ← Problem!
    "cache": "ok",
    "disk_space": "ok",
    "cpu": "ok"
  }
}


FAILURE DETECTION
─────────────────

Timeline of Server 3 failure:

T0: Server 3 healthy
    Health check: ✅ 200 OK
    Status: HEALTHY
    Traffic: Receiving

T1 (5s): Server 3 healthy
    Health check: ✅ 200 OK
    Status: HEALTHY
    Traffic: Receiving

T2 (10s): Server 3 database fails
    Health check: ❌ 503 Error
    Status: UNHEALTHY (1st failure)
    Traffic: Still receiving (grace period)

T3 (15s): Server 3 still unhealthy
    Health check: ❌ 503 Error
    Status: UNHEALTHY (2nd failure)
    Traffic: Still receiving (grace period)

T4 (20s): Server 3 still unhealthy
    Health check: ❌ 503 Error
    Status: UNHEALTHY (3rd failure)
    Traffic: STOPPED ❌ (threshold reached)

T5 (25s): Server 3 still unhealthy
    Health check: ❌ 503 Error
    Status: UNHEALTHY
    Traffic: No traffic

T6 (30s): Server 3 recovered!
    Health check: ✅ 200 OK
    Status: RECOVERING (1st success)
    Traffic: Still stopped (waiting for confirmation)

T7 (35s): Server 3 still healthy
    Health check: ✅ 200 OK
    Status: RECOVERING (2nd success)
    Traffic: Still stopped

T8 (40s): Server 3 still healthy
    Health check: ✅ 200 OK
    Status: HEALTHY ✅ (3rd success, threshold met)
    Traffic: RESUMED ✅


CONFIGURATION
─────────────

Typical health check config:

healthCheck:
  interval: 5s              # Check every 5 seconds
  timeout: 2s               # Wait max 2 seconds for response
  unhealthyThreshold: 3     # 3 failures → mark unhealthy
  healthyThreshold: 3       # 3 successes → mark healthy
  path: /health             # Endpoint to check
  expectedStatus: 200       # Expected HTTP status

Why thresholds?
• Avoid false positives (network blip)
• Avoid flapping (healthy ↔ unhealthy rapidly)
• Give servers time to recover
• Prevent unnecessary traffic shifts


PASSIVE HEALTH CHECKS
──────────────────────

Monitor actual request failures:

┌──────────────────────────────────────┐
│  Load Balancer                       │
│                                      │
│  Track real request errors:          │
│  • Connection refused                │
│  • Timeout                           │
│  • 5xx errors                        │
│                                      │
│  If error rate > 50% for 30s:        │
│  → Mark server unhealthy             │
└────┬─────────────────────────────────┘
     │
     │ Real user requests
     ↓
┌────────────────┐
│  Server 3      │
│                │
│  Errors: 45/100│  ← 45% error rate
│  Status: ⚠️    │     (approaching threshold)
└────────────────┘


DASHBOARD VIEW
──────────────

┌──────────────────────────────────────────────────────┐
│  Load Balancer Health Dashboard                     │
├──────────────────────────────────────────────────────┤
│                                                      │
│  ┌────────────────────────────────────────────────┐ │
│  │ Server 1: ✅ HEALTHY                           │ │
│  │ Last check: 2s ago                             │ │
│  │ Uptime: 99.9%                                  │ │
│  │ Requests: 1,250 active                         │ │
│  └────────────────────────────────────────────────┘ │
│                                                      │
│  ┌────────────────────────────────────────────────┐ │
│  │ Server 2: ✅ HEALTHY                           │ │
│  │ Last check: 1s ago                             │ │
│  │ Uptime: 100%                                   │ │
│  │ Requests: 980 active                           │ │
│  └────────────────────────────────────────────────┘ │
│                                                      │
│  ┌────────────────────────────────────────────────┐ │
│  │ Server 3: ❌ UNHEALTHY                         │ │
│  │ Last check: Failed (Timeout)                   │ │
│  │ Failed checks: 5                               │ │
│  │ Requests: 0 (removed from pool)                │ │
│  └────────────────────────────────────────────────┘ │
│                                                      │
│  ┌────────────────────────────────────────────────┐ │
│  │ Server 4: ✅ HEALTHY                           │ │
│  │ Last check: 3s ago                             │ │
│  │ Uptime: 99.8%                                  │ │
│  │ Requests: 1,150 active                         │ │
│  └────────────────────────────────────────────────┘ │
│                                                      │
│  Active Servers: 3/4                                 │
│  Traffic Distribution: Adjusted (Server 3 excluded)  │
└──────────────────────────────────────────────────────┘
```

## 5. System Design Interview Answer

### Short Answer (3-4 minutes):

> **Load balancing** distributes incoming traffic across multiple servers to ensure high availability, scalability, and fault tolerance.
>
> Load balancers can be placed at multiple layers:
> - **L4 (Transport Layer)**: Routes based on IP/Port (fast, simple)
> - **L7 (Application Layer)**: Routes based on HTTP headers, URLs, cookies (more intelligent)
>
> Common algorithms include:
> 1. **Round Robin**: Distributes sequentially, simple and fair
> 2. **Weighted Round Robin**: Assigns more traffic to powerful servers
> 3. **Least Connections**: Routes to server with fewest active connections
> 4. **Least Response Time**: Considers both connections and response times
> 5. **IP Hash**: Ensures session persistence by routing same IP to same server
>
> **Health checks** are critical - the load balancer continuously monitors servers (every 5-10 seconds) and removes unhealthy ones from the pool. Typically requires 3 consecutive failures to mark unhealthy and 3 successes to mark healthy again, preventing false positives.
>
> In production, load balancers are often deployed in pairs (active-passive or active-active) to avoid single point of failure. Technologies include:
> - Software: NGINX, HAProxy, Envoy
> - Cloud: AWS ELB/ALB, Google Cloud Load Balancing, Azure Load Balancer
> - Hardware: F5, Citrix ADC
>
> Modern architectures often use multiple load balancer layers: global (DNS-based) → regional (L4/L7) → internal (service mesh) → database (read/write splitting).

---

## Key Technologies:
- **NGINX**: Popular open-source load balancer
- **HAProxy**: High-performance TCP/HTTP load balancer
- **AWS ELB/ALB**: Managed cloud load balancers
- **Envoy**: Modern cloud-native proxy
- **F5**: Enterprise hardware load balancer
- **Kubernetes Ingress**: Container orchestration load balancing
