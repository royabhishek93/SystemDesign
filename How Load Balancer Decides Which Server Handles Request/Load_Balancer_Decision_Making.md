# How Load Balancer Decides Which Server Handles Request?

## 1. The Decision-Making Process

When a load balancer receives a request, it must quickly decide which backend server should handle it. This decision is based on multiple factors and algorithms.

### Visual: High-Level Decision Flow

```
┌────────────────────────────────────────────────────────────────────────┐
│              LOAD BALANCER DECISION-MAKING PROCESS                     │
└────────────────────────────────────────────────────────────────────────┘

REQUEST ARRIVES
───────────────

User Request:
GET /api/users/123
     │
     │ Arrives at load balancer
     ↓
┌──────────────────────────────────────────────────────────────┐
│                   LOAD BALANCER                              │
│                                                              │
│  STEP 1: PARSE REQUEST                                       │
│  ┌────────────────────────────────────────────────────────┐ │
│  │ • Extract: Method, Path, Headers, IP                   │ │
│  │ • Identify: User, Session, API Key                     │ │
│  │ • Time: < 1ms                                          │ │
│  └────────────────────────────────────────────────────────┘ │
│                         ↓                                    │
│  STEP 2: FILTER AVAILABLE SERVERS                            │
│  ┌────────────────────────────────────────────────────────┐ │
│  │ Total Servers: 10                                      │ │
│  │ Healthy Servers: 8 ✅                                   │ │
│  │ Unhealthy Servers: 2 ❌ (excluded)                     │ │
│  │ Time: < 1ms                                            │ │
│  └────────────────────────────────────────────────────────┘ │
│                         ↓                                    │
│  STEP 3: CHECK SESSION PERSISTENCE (if configured)           │
│  ┌────────────────────────────────────────────────────────┐ │
│  │ Session cookie exists?                                 │ │
│  │ • YES → Route to same server (Server 3) ✅             │ │
│  │ • NO → Continue to algorithm                           │ │
│  │ Time: < 1ms                                            │ │
│  └────────────────────────────────────────────────────────┘ │
│                         ↓                                    │
│  STEP 4: APPLY LOAD BALANCING ALGORITHM                     │
│  ┌────────────────────────────────────────────────────────┐ │
│  │ Algorithm: Least Connections                           │ │
│  │                                                        │ │
│  │ Server 1: 50 connections                               │ │
│  │ Server 2: 45 connections                               │ │
│  │ Server 3: 38 connections ← SELECTED! ✅                │ │
│  │ Server 4: 52 connections                               │ │
│  │ Server 5: 41 connections                               │ │
│  │ Server 6: 47 connections                               │ │
│  │ Server 7: 43 connections                               │ │
│  │ Server 8: 49 connections                               │ │
│  │                                                        │ │
│  │ Winner: Server 3 (least connections)                   │ │
│  │ Time: < 1ms                                            │ │
│  └────────────────────────────────────────────────────────┘ │
│                         ↓                                    │
│  STEP 5: VERIFY SELECTION                                    │
│  ┌────────────────────────────────────────────────────────┐ │
│  │ • Server 3 healthy? ✅                                  │ │
│  │ • Not overloaded? ✅                                    │ │
│  │ • Accepting connections? ✅                             │ │
│  │ Time: < 1ms                                            │ │
│  └────────────────────────────────────────────────────────┘ │
│                         ↓                                    │
│  STEP 6: ESTABLISH CONNECTION                                │
│  ┌────────────────────────────────────────────────────────┐ │
│  │ • Open TCP connection to Server 3                      │ │
│  │ • Forward request                                      │ │
│  │ • Track connection (increment counter)                 │ │
│  │ Time: 2-5ms                                            │ │
│  └────────────────────────────────────────────────────────┘ │
└──────────────────────────────────────────────────────────────┘
                         │
                         │ Forward request
                         ↓
                  ┌──────────────┐
                  │  SERVER 3    │
                  │              │
                  │  Processes   │
                  │  request     │
                  └──────────────┘

TOTAL DECISION TIME: 5-10 milliseconds
```

## 2. Factor-Based Decision Making

### Visual: All Factors Considered

```
┌────────────────────────────────────────────────────────────────────────┐
│                 FACTORS IN LOAD BALANCER DECISION                      │
└────────────────────────────────────────────────────────────────────────┘

FACTOR 1: SERVER HEALTH STATUS
───────────────────────────────

Priority: CRITICAL (Must be healthy)

┌──────────────────────────────────────────────────────────┐
│  Server Pool (10 servers):                               │
│                                                          │
│  ✅ Server 1: Healthy    (Last check: 2s ago)           │
│  ✅ Server 2: Healthy    (Last check: 1s ago)           │
│  ✅ Server 3: Healthy    (Last check: 3s ago)           │
│  ❌ Server 4: UNHEALTHY  (Failed 3 consecutive checks)  │
│  ✅ Server 5: Healthy    (Last check: 2s ago)           │
│  ✅ Server 6: Healthy    (Last check: 1s ago)           │
│  ✅ Server 7: Healthy    (Last check: 4s ago)           │
│  ❌ Server 8: UNHEALTHY  (Connection refused)           │
│  ✅ Server 9: Healthy    (Last check: 2s ago)           │
│  ⚠️  Server 10: DEGRADED (Slow responses, 80% success)  │
│                                                          │
│  Available for routing: 8 servers (1,2,3,5,6,7,9,10)    │
│  Excluded: 2 servers (4,8)                               │
└──────────────────────────────────────────────────────────┘


FACTOR 2: CURRENT CONNECTION COUNT
───────────────────────────────────

Priority: HIGH (For Least Connections algorithm)

┌──────────────────────────────────────────────────────────┐
│  Active Connections:                                     │
│                                                          │
│  Server 1: ████████████████████ 45 connections          │
│  Server 2: ███████████████████████ 52 connections       │
│  Server 3: ████████████████ 35 connections ← Best!      │
│  Server 5: ████████████████████ 48 connections          │
│  Server 6: ██████████████████████ 50 connections        │
│  Server 7: ███████████████████ 47 connections           │
│  Server 9: █████████████████████ 51 connections         │
│  Server 10: ████████████████████ 46 connections         │
│                                                          │
│  Winner: Server 3 (35 connections - lowest)              │
└──────────────────────────────────────────────────────────┘


FACTOR 3: SERVER RESPONSE TIME
───────────────────────────────

Priority: HIGH (For Least Response Time algorithm)

┌──────────────────────────────────────────────────────────┐
│  Average Response Time (last 100 requests):              │
│                                                          │
│  Server 1: ████████ 80ms                                 │
│  Server 2: ████████████████ 160ms                        │
│  Server 3: █████ 50ms ← Fastest!                         │
│  Server 5: ██████████ 100ms                              │
│  Server 6: ███████████ 110ms                             │
│  Server 7: █████████ 90ms                                │
│  Server 9: ██████████████ 140ms                          │
│  Server 10: ███████████████ 150ms                        │
│                                                          │
│  Winner: Server 3 (50ms - fastest)                       │
└──────────────────────────────────────────────────────────┘


FACTOR 4: SERVER CAPACITY/WEIGHT
─────────────────────────────────

Priority: HIGH (For Weighted algorithms)

┌──────────────────────────────────────────────────────────┐
│  Server Specifications & Weights:                        │
│                                                          │
│  Server 1: 16 cores, 32GB RAM  → Weight: 4              │
│  Server 2: 16 cores, 32GB RAM  → Weight: 4              │
│  Server 3: 8 cores, 16GB RAM   → Weight: 2              │
│  Server 5: 16 cores, 32GB RAM  → Weight: 4              │
│  Server 6: 8 cores, 16GB RAM   → Weight: 2              │
│  Server 7: 16 cores, 32GB RAM  → Weight: 4              │
│  Server 9: 4 cores, 8GB RAM    → Weight: 1              │
│  Server 10: 16 cores, 32GB RAM → Weight: 4              │
│                                                          │
│  Higher weight = More requests                           │
│  Server 1,2,5,7,10 get 4x more traffic than Server 9    │
└──────────────────────────────────────────────────────────┘


FACTOR 5: SESSION PERSISTENCE/STICKINESS
─────────────────────────────────────────

Priority: CRITICAL (If session exists)

┌──────────────────────────────────────────────────────────┐
│  Request has session cookie:                             │
│  Cookie: SERVERID=server-3-abc123                        │
│                                                          │
│  Lookup:                                                 │
│  • Session belongs to Server 3                           │
│  • Server 3 is healthy? ✅                               │
│  • Route to Server 3 (sticky session)                    │
│                                                          │
│  Why? User's session data exists on Server 3             │
│  Routing to different server = Lost session = Bad UX     │
└──────────────────────────────────────────────────────────┘


FACTOR 6: CLIENT IP ADDRESS
────────────────────────────

Priority: MEDIUM (For IP Hash algorithm)

┌──────────────────────────────────────────────────────────┐
│  Client IP: 192.168.1.100                                │
│                                                          │
│  Hash Calculation:                                       │
│  hash(192.168.1.100) = 1234567                          │
│  1234567 % 8 servers = 3                                 │
│                                                          │
│  Route to: Server 3                                      │
│                                                          │
│  Result: Same IP always goes to same server              │
└──────────────────────────────────────────────────────────┘


FACTOR 7: GEOGRAPHIC LOCATION
──────────────────────────────

Priority: HIGH (For geographic routing)

┌──────────────────────────────────────────────────────────┐
│  Client Location: Tokyo, Japan                           │
│                                                          │
│  Server Locations:                                       │
│  Server 1-3: USA (Virginia)     → 180ms latency         │
│  Server 5-7: Europe (Frankfurt) → 220ms latency         │
│  Server 9-10: Asia (Tokyo)      → 5ms latency ✅        │
│                                                          │
│  Route to: Server 9 or 10 (nearest location)             │
└──────────────────────────────────────────────────────────┘


FACTOR 8: REQUEST TYPE/PATH
────────────────────────────

Priority: HIGH (For path-based routing)

┌──────────────────────────────────────────────────────────┐
│  Request Path: /api/video/stream                         │
│                                                          │
│  Routing Rules:                                          │
│  • /api/user/*     → User Service Servers (1-3)         │
│  • /api/order/*    → Order Service Servers (4-6)        │
│  • /api/video/*    → Video Service Servers (7-10) ✅    │
│  • /api/payment/*  → Payment Service Servers (11-13)    │
│                                                          │
│  Route to: Servers 7-10 pool                             │
│  Then apply algorithm within that pool                   │
└──────────────────────────────────────────────────────────┘


FACTOR 9: SERVER CPU/MEMORY USAGE
──────────────────────────────────

Priority: MEDIUM (For dynamic load balancing)

┌──────────────────────────────────────────────────────────┐
│  Real-time Server Metrics:                               │
│                                                          │
│  Server 1: CPU: 45%, Memory: 60%  → Score: 52.5         │
│  Server 2: CPU: 85%, Memory: 70%  → Score: 77.5         │
│  Server 3: CPU: 25%, Memory: 40%  → Score: 32.5 ✅      │
│  Server 5: CPU: 60%, Memory: 55%  → Score: 57.5         │
│  Server 6: CPU: 70%, Memory: 65%  → Score: 67.5         │
│  Server 7: CPU: 50%, Memory: 50%  → Score: 50.0         │
│  Server 9: CPU: 90%, Memory: 80%  → Score: 85.0         │
│  Server 10: CPU: 55%, Memory: 60% → Score: 57.5         │
│                                                          │
│  Winner: Server 3 (lowest resource usage)                │
└──────────────────────────────────────────────────────────┘


FACTOR 10: TIME OF DAY / SCHEDULING
────────────────────────────────────

Priority: LOW (For scheduled routing)

┌──────────────────────────────────────────────────────────┐
│  Current Time: 02:00 AM (Off-peak hours)                 │
│                                                          │
│  Routing Strategy:                                       │
│  • Peak hours (9am-5pm):                                 │
│    → Use all 10 servers                                  │
│                                                          │
│  • Off-peak hours (10pm-8am):                            │
│    → Use only 3 servers (save costs) ✅                  │
│    → Route to: Servers 1, 2, 3                           │
│    → Shut down: Servers 4-10                             │
│                                                          │
│  Cost Savings: 70% during off-peak                       │
└──────────────────────────────────────────────────────────┘
```

## 3. Decision-Making Algorithms in Detail

### Algorithm 1: Round Robin with Health Checks

```
┌────────────────────────────────────────────────────────────────────────┐
│              ROUND ROBIN WITH HEALTH CHECKS                            │
└────────────────────────────────────────────────────────────────────────┘

STATE TRACKING
──────────────

Load Balancer maintains:
┌──────────────────────────────────────┐
│  Current Index: 2                    │
│  Total Servers: 10                   │
│  Healthy Servers: [1,2,3,5,6,7,9,10] │
│  Unhealthy: [4,8]                    │
└──────────────────────────────────────┘


REQUEST PROCESSING
──────────────────

Request 1 arrives:
┌──────────────────────────────────────────────────────────┐
│  STEP 1: Get current index                               │
│  currentIndex = 2                                        │
│                                                          │
│  STEP 2: Get server at index                             │
│  server = servers[2] = Server 3                          │
│                                                          │
│  STEP 3: Check if healthy                                │
│  isHealthy(Server 3)? → YES ✅                           │
│                                                          │
│  STEP 4: Route to Server 3                               │
│  forward(request, Server 3)                              │
│                                                          │
│  STEP 5: Increment index                                 │
│  currentIndex = (2 + 1) % 10 = 3                         │
└──────────────────────────────────────────────────────────┘


Request 2 arrives:
┌──────────────────────────────────────────────────────────┐
│  STEP 1: Get current index                               │
│  currentIndex = 3                                        │
│                                                          │
│  STEP 2: Get server at index                             │
│  server = servers[3] = Server 4                          │
│                                                          │
│  STEP 3: Check if healthy                                │
│  isHealthy(Server 4)? → NO ❌                            │
│                                                          │
│  STEP 4: Skip to next server                             │
│  currentIndex = (3 + 1) % 10 = 4                         │
│  server = servers[4] = Server 5                          │
│  isHealthy(Server 5)? → YES ✅                           │
│                                                          │
│  STEP 5: Route to Server 5                               │
│  forward(request, Server 5)                              │
│                                                          │
│  STEP 6: Increment index                                 │
│  currentIndex = (4 + 1) % 10 = 5                         │
└──────────────────────────────────────────────────────────┘


VISUAL FLOW
───────────

Request Sequence:
Req 1 → Server 3 ✅ (index 2)
Req 2 → Server 4 ❌ (unhealthy, skip)
     → Server 5 ✅ (index 4)
Req 3 → Server 6 ✅ (index 5)
Req 4 → Server 7 ✅ (index 6)
Req 5 → Server 8 ❌ (unhealthy, skip)
     → Server 9 ✅ (index 8)
Req 6 → Server 10 ✅ (index 9)
Req 7 → Server 1 ✅ (index 0, wrapped around)
Req 8 → Server 2 ✅ (index 1)
Req 9 → Server 3 ✅ (index 2, cycle continues)


CODE IMPLEMENTATION
───────────────────

class RoundRobinLoadBalancer {
    servers: [Server1, Server2, ..., Server10]
    currentIndex: 0
    healthStatus: Map<Server, boolean>

    function getNextServer(request) {
        attempts = 0
        maxAttempts = servers.length

        while (attempts < maxAttempts) {
            // Get server at current index
            server = servers[currentIndex]

            // Move to next index for next request
            currentIndex = (currentIndex + 1) % servers.length

            // Check if server is healthy
            if (healthStatus[server] == true) {
                return server  // Found healthy server!
            }

            attempts++
        }

        // All servers unhealthy
        throw Error("No healthy servers available")
    }

    function updateHealthStatus() {
        // Background thread checks health every 5 seconds
        for each server in servers {
            isHealthy = checkHealth(server)
            healthStatus[server] = isHealthy
        }
    }
}


DECISION FACTORS SUMMARY
────────────────────────

Priority 1: Server health (must be healthy)
Priority 2: Current index position (round-robin)
Priority 3: None (simple rotation)

Time Complexity: O(n) worst case (if checking all servers)
                 O(1) average case (healthy servers available)
```

### Algorithm 2: Least Connections with Weights

```
┌────────────────────────────────────────────────────────────────────────┐
│           LEAST CONNECTIONS WITH WEIGHTS                               │
└────────────────────────────────────────────────────────────────────────┘

STATE TRACKING
──────────────

Load Balancer maintains:
┌────────────────────────────────────────────────────────────┐
│  Server 1: connections=45, weight=4                        │
│  Server 2: connections=52, weight=4                        │
│  Server 3: connections=35, weight=2                        │
│  Server 5: connections=48, weight=4                        │
│  Server 6: connections=50, weight=2                        │
│  Server 7: connections=47, weight=4                        │
│  Server 9: connections=15, weight=1                        │
│  Server 10: connections=46, weight=4                       │
└────────────────────────────────────────────────────────────┘


REQUEST PROCESSING
──────────────────

Request arrives:
┌──────────────────────────────────────────────────────────┐
│  STEP 1: Calculate weighted connections for each server  │
│                                                          │
│  Formula: weightedConnections = connections / weight     │
│                                                          │
│  Server 1:  45 / 4 = 11.25                               │
│  Server 2:  52 / 4 = 13.00                               │
│  Server 3:  35 / 2 = 17.50                               │
│  Server 5:  48 / 4 = 12.00                               │
│  Server 6:  50 / 2 = 25.00                               │
│  Server 7:  47 / 4 = 11.75                               │
│  Server 9:  15 / 1 = 15.00                               │
│  Server 10: 46 / 4 = 11.50                               │
│                                                          │
│  STEP 2: Find minimum weighted connections               │
│  Winner: Server 1 (11.25) ✅                             │
│                                                          │
│  STEP 3: Verify server is healthy                        │
│  isHealthy(Server 1)? → YES ✅                           │
│                                                          │
│  STEP 4: Route to Server 1                               │
│  forward(request, Server 1)                              │
│                                                          │
│  STEP 5: Increment connection count                      │
│  Server 1: connections = 45 + 1 = 46                     │
└──────────────────────────────────────────────────────────┘


WHY WEIGHTS MATTER
──────────────────

Scenario: Without weights
┌──────────────────────────────────────────────────────────┐
│  Server 9 (weak): 15 connections                         │
│  Server 1 (powerful): 45 connections                     │
│                                                          │
│  Simple least connections would choose Server 9          │
│  But Server 9 is already overloaded! (4 cores only)      │
└──────────────────────────────────────────────────────────┘

Scenario: With weights
┌──────────────────────────────────────────────────────────┐
│  Server 9: 15 / 1 = 15.00 (high relative load)          │
│  Server 1: 45 / 4 = 11.25 (low relative load)           │
│                                                          │
│  Weighted algorithm chooses Server 1 ✅                  │
│  Correct! Server 1 can handle more load                  │
└──────────────────────────────────────────────────────────┘


REAL-TIME EXAMPLE
─────────────────

T0: Initial state
Server 1: 45 conn, weight 4 → 11.25 ← Selected
Server 2: 52 conn, weight 4 → 13.00
Server 3: 35 conn, weight 2 → 17.50

T1: After routing request to Server 1
Server 1: 46 conn, weight 4 → 11.50
Server 2: 52 conn, weight 4 → 13.00
Server 3: 35 conn, weight 2 → 17.50

T2: Next request arrives
Server 1: 46 conn, weight 4 → 11.50 ← Selected again
Server 2: 52 conn, weight 4 → 13.00
Server 3: 35 conn, weight 2 → 17.50

T3: After routing request to Server 1
Server 1: 47 conn, weight 4 → 11.75
Server 2: 52 conn, weight 4 → 13.00
Server 3: 35 conn, weight 2 → 17.50

T4: Next request arrives
Server 1: 47 conn, weight 4 → 11.75 ← Selected again
Server 2: 52 conn, weight 4 → 13.00
Server 3: 35 conn, weight 2 → 17.50

T5: Request completes on Server 2
Server 1: 48 conn, weight 4 → 12.00
Server 2: 51 conn, weight 4 → 12.75
Server 3: 35 conn, weight 2 → 17.50

T6: Next request arrives
Server 1: 48 conn, weight 4 → 12.00 ← Selected
Server 2: 51 conn, weight 4 → 12.75
Server 3: 35 conn, weight 2 → 17.50


CODE IMPLEMENTATION
───────────────────

class WeightedLeastConnectionsLB {
    servers: [
        {server: Server1, connections: 0, weight: 4, healthy: true},
        {server: Server2, connections: 0, weight: 4, healthy: true},
        // ...
    ]

    function getNextServer(request) {
        minScore = Infinity
        selectedServer = null

        for each serverInfo in servers {
            // Skip unhealthy servers
            if (!serverInfo.healthy) {
                continue
            }

            // Calculate weighted score
            score = serverInfo.connections / serverInfo.weight

            if (score < minScore) {
                minScore = score
                selectedServer = serverInfo
            }
        }

        if (selectedServer == null) {
            throw Error("No healthy servers available")
        }

        // Increment connection count
        selectedServer.connections++

        return selectedServer.server
    }

    function onRequestComplete(server) {
        // Find server info
        serverInfo = findServerInfo(server)

        // Decrement connection count
        serverInfo.connections--
    }
}


DECISION FACTORS SUMMARY
────────────────────────

Priority 1: Server health (must be healthy)
Priority 2: Weighted connections (connections/weight)
Priority 3: Server capacity (weight value)

Time Complexity: O(n) where n = number of servers
Space Complexity: O(n) for connection tracking
```

### Algorithm 3: Least Response Time

```
┌────────────────────────────────────────────────────────────────────────┐
│                    LEAST RESPONSE TIME ALGORITHM                       │
└────────────────────────────────────────────────────────────────────────┘

STATE TRACKING
──────────────

Load Balancer maintains:
┌────────────────────────────────────────────────────────────┐
│  Server 1:                                                 │
│    connections: 45                                         │
│    avgResponseTime: 80ms (rolling average)                 │
│    recentResponses: [75ms, 82ms, 85ms, 78ms, 80ms]        │
│                                                            │
│  Server 2:                                                 │
│    connections: 52                                         │
│    avgResponseTime: 160ms                                  │
│    recentResponses: [155ms, 162ms, 158ms, 165ms, 160ms]   │
│                                                            │
│  Server 3:                                                 │
│    connections: 35                                         │
│    avgResponseTime: 50ms                                   │
│    recentResponses: [48ms, 52ms, 51ms, 49ms, 50ms]        │
│                                                            │
│  // ... more servers                                       │
└────────────────────────────────────────────────────────────┘


REQUEST PROCESSING
──────────────────

Request arrives:
┌──────────────────────────────────────────────────────────┐
│  STEP 1: Calculate composite score for each server       │
│                                                          │
│  Formula:                                                │
│  score = (connections × 1.0) + (avgResponseTime × 0.1)  │
│                                                          │
│  Why this formula?                                       │
│  • connections: Direct measure of current load           │
│  • avgResponseTime: Indicates server performance         │
│  • Weight 1.0 vs 0.1: Connections more important         │
│                                                          │
│  Server 1: (45 × 1) + (80 × 0.1) = 45 + 8 = 53.0        │
│  Server 2: (52 × 1) + (160 × 0.1) = 52 + 16 = 68.0      │
│  Server 3: (35 × 1) + (50 × 0.1) = 35 + 5 = 40.0 ✅     │
│  Server 5: (48 × 1) + (100 × 0.1) = 48 + 10 = 58.0      │
│  Server 6: (50 × 1) + (110 × 0.1) = 50 + 11 = 61.0      │
│  Server 7: (47 × 1) + (90 × 0.1) = 47 + 9 = 56.0        │
│  Server 9: (51 × 1) + (140 × 0.1) = 51 + 14 = 65.0      │
│  Server 10: (46 × 1) + (150 × 0.1) = 46 + 15 = 61.0     │
│                                                          │
│  STEP 2: Find minimum score                              │
│  Winner: Server 3 (score: 40.0) ✅                       │
│                                                          │
│  Reasoning:                                              │
│  • Fewest connections (35)                               │
│  • Fastest response time (50ms)                          │
│  • Best overall performance                              │
│                                                          │
│  STEP 3: Verify server is healthy                        │
│  isHealthy(Server 3)? → YES ✅                           │
│                                                          │
│  STEP 4: Route to Server 3                               │
│  forward(request, Server 3)                              │
│  startTime = currentTime()                               │
│  Server 3: connections++ (now 36)                        │
└──────────────────────────────────────────────────────────┘


RESPONSE TIME TRACKING
──────────────────────

When response returns:
┌──────────────────────────────────────────────────────────┐
│  STEP 1: Calculate response time                         │
│  endTime = currentTime()                                 │
│  responseTime = endTime - startTime = 52ms               │
│                                                          │
│  STEP 2: Update moving average                           │
│  recentResponses = [48, 52, 51, 49, 50]                  │
│  Add new: 52ms                                           │
│  recentResponses = [52, 51, 49, 50, 52] (keep last 5)    │
│                                                          │
│  STEP 3: Recalculate average                             │
│  sum = 52 + 51 + 49 + 50 + 52 = 254ms                    │
│  avgResponseTime = 254 / 5 = 50.8ms                      │
│                                                          │
│  STEP 4: Update server metrics                           │
│  Server 3:                                               │
│    connections-- (now 35)                                │
│    avgResponseTime = 50.8ms                              │
└──────────────────────────────────────────────────────────┘


WHY THIS IS BETTER
──────────────────

Scenario: Server with low connections but slow
┌──────────────────────────────────────────────────────────┐
│  Server A:                                               │
│    connections: 10 (very low)                            │
│    avgResponseTime: 5000ms (very slow!)                  │
│    score = (10 × 1) + (5000 × 0.1) = 510                │
│                                                          │
│  Server B:                                               │
│    connections: 50 (higher)                              │
│    avgResponseTime: 100ms (fast)                         │
│    score = (50 × 1) + (100 × 0.1) = 60                  │
│                                                          │
│  Least Connections Only: Would choose Server A ❌        │
│  Least Response Time: Chooses Server B ✅                │
│                                                          │
│  Why? Server A is slow (maybe database issue)            │
│  Server B is much better choice despite more connections │
└──────────────────────────────────────────────────────────┘


ADAPTIVE BEHAVIOR
─────────────────

Timeline showing adaptation:

T0: All servers equal (100ms avg)
Server 1: score = 53.0
Server 2: score = 62.0
Server 3: score = 45.0 ← Selected

T1: Server 2 database becomes slow
Server 2: avgResponseTime increases to 500ms
Server 2: score = (52 × 1) + (500 × 0.1) = 102.0
Result: Server 2 gets less traffic ✅

T2: Server 2 recovers
Server 2: avgResponseTime drops to 100ms
Server 2: score = (52 × 1) + (100 × 0.1) = 62.0
Result: Server 2 gets normal traffic again ✅


CODE IMPLEMENTATION
───────────────────

class LeastResponseTimeLoadBalancer {
    servers: [
        {
            server: Server1,
            connections: 0,
            responseTimes: [],  // Last 100
            avgResponseTime: 0,
            healthy: true
        },
        // ...
    ]

    function getNextServer(request) {
        minScore = Infinity
        selectedServer = null

        for each serverInfo in servers {
            if (!serverInfo.healthy) {
                continue
            }

            // Calculate composite score
            score = (serverInfo.connections × 1.0) +
                    (serverInfo.avgResponseTime × 0.1)

            if (score < minScore) {
                minScore = score
                selectedServer = serverInfo
            }
        }

        if (selectedServer == null) {
            throw Error("No healthy servers")
        }

        // Track request start
        request.startTime = currentTime()
        selectedServer.connections++

        return selectedServer.server
    }

    function onRequestComplete(server, request) {
        serverInfo = findServerInfo(server)

        // Calculate response time
        responseTime = currentTime() - request.startTime

        // Update response times
        serverInfo.responseTimes.push(responseTime)
        if (serverInfo.responseTimes.length > 100) {
            serverInfo.responseTimes.shift()  // Remove oldest
        }

        // Recalculate average
        sum = serverInfo.responseTimes.reduce((a,b) => a+b, 0)
        serverInfo.avgResponseTime =
            sum / serverInfo.responseTimes.length

        // Decrement connections
        serverInfo.connections--
    }
}


DECISION FACTORS SUMMARY
────────────────────────

Priority 1: Server health (must be healthy)
Priority 2: Composite score (connections + response time)
Priority 3: Recent performance trends

Time Complexity: O(n) for selection
Space Complexity: O(n × 100) for response time history
```

## 4. Complete Decision Flow Diagram

### Visual: End-to-End Decision Process

```
┌────────────────────────────────────────────────────────────────────────┐
│              COMPLETE LOAD BALANCER DECISION FLOW                      │
└────────────────────────────────────────────────────────────────────────┘

                        REQUEST ARRIVES
                              │
                              ↓
                    ┌──────────────────┐
                    │  Parse Request   │
                    │  • Extract data  │
                    │  • Identify user │
                    └────────┬─────────┘
                             │
                             ↓
                    ┌──────────────────┐
                    │  Check Session   │
                    │  Persistence     │
                    └────┬─────────┬───┘
                         │         │
              Session    │         │  No Session
              Exists     │         │
                         ↓         ↓
            ┌─────────────────┐  ┌────────────────────┐
            │ Get Existing    │  │ Select Algorithm   │
            │ Server from     │  │ • Round Robin?     │
            │ Session         │  │ • Least Conn?      │
            └────┬────────────┘  │ • Least RT?        │
                 │               │ • IP Hash?         │
                 │               │ • Weighted?        │
                 │               └────┬───────────────┘
                 │                    │
                 │                    ↓
                 │          ┌──────────────────┐
                 │          │ Filter Servers   │
                 │          │ • Healthy only   │
                 │          │ • 8 of 10 healthy│
                 │          └────┬─────────────┘
                 │               │
                 │               ↓
                 │          ┌──────────────────┐
                 │          │ Apply Algorithm  │
                 │          │ • Calculate      │
                 │          │ • Compare        │
                 │          │ • Select Best    │
                 │          └────┬─────────────┘
                 │               │
                 └───────────────┴─────────────┐
                                               │
                                               ↓
                                  ┌──────────────────────┐
                                  │ Verify Selection     │
                                  │ • Server healthy?    │
                                  │ • Not overloaded?    │
                                  │ • Accepting?         │
                                  └────┬─────────────────┘
                                       │
                        ┌──────────────┴──────────────┐
                        │                             │
                   YES  ↓                        NO   ↓
          ┌──────────────────┐         ┌──────────────────┐
          │ Route to Server  │         │ Select Different │
          │                  │         │ Server (retry)   │
          └────┬─────────────┘         └────┬─────────────┘
               │                            │
               ↓                            │
     ┌──────────────────┐                  │
     │ Track Connection │←─────────────────┘
     │ • Increment cnt  │
     │ • Start timer    │
     │ • Update metrics │
     └────┬─────────────┘
          │
          ↓
     ┌──────────────────┐
     │ Forward Request  │
     │ to Selected      │
     │ Server           │
     └────┬─────────────┘
          │
          ↓
     ┌──────────────────┐
     │ Wait for Response│
     └────┬─────────────┘
          │
          ↓
     ┌──────────────────┐
     │ Update Metrics   │
     │ • Response time  │
     │ • Decrement cnt  │
     │ • Success/fail   │
     └────┬─────────────┘
          │
          ↓
     ┌──────────────────┐
     │ Return Response  │
     │ to Client        │
     └──────────────────┘


DECISION TIME BREAKDOWN
───────────────────────

Total time for decision: 5-10ms

┌────────────────────────────────────────┐
│ Step                      │ Time       │
├────────────────────────────────────────┤
│ Parse request             │ 0.5ms      │
│ Check session             │ 1ms (Redis)│
│ Filter healthy servers    │ 0.5ms      │
│ Apply algorithm           │ 1ms        │
│ Verify selection          │ 0.5ms      │
│ Track connection          │ 1ms (Redis)│
│ Forward request (network) │ 2-5ms      │
├────────────────────────────────────────┤
│ Total                     │ 5-10ms     │
└────────────────────────────────────────┘
```

## 5. System Design Interview Answer

### Short Answer (3-4 minutes):

> When a load balancer receives a request, it follows a multi-step decision process to select the best backend server:
>
> **Step 1: Request Parsing** (< 1ms)
> - Extract method, path, headers, client IP
> - Identify user, session, API key
>
> **Step 2: Health Filtering** (< 1ms)
> - Filter out unhealthy servers from pool
> - Only consider servers that passed recent health checks
> - Example: 8 out of 10 servers healthy → work with 8
>
> **Step 3: Session Persistence Check** (1ms)
> - If session cookie exists → route to same server (sticky session)
> - Critical for stateful applications
> - Skip algorithm if session found
>
> **Step 4: Apply Load Balancing Algorithm** (1-2ms)
> - **Round Robin**: Current index → select server → increment index
> - **Least Connections**: Calculate connections/weight for each → select minimum
> - **Least Response Time**: Calculate (connections × 1.0) + (avgResponseTime × 0.1) → select minimum
> - **IP Hash**: hash(clientIP) % serverCount → consistent routing
> - **Weighted**: Assign more requests to powerful servers
>
> **Step 5: Verification** (< 1ms)
> - Double-check selected server is healthy
> - Verify not overloaded
> - Confirm accepting connections
>
> **Step 6: Connection Tracking** (1ms)
> - Increment connection counter
> - Start response timer
> - Update metrics in Redis
>
> **Step 7: Forward Request** (2-5ms)
> - Establish TCP connection
> - Forward request to selected server
>
> **Total decision time**: 5-10ms overhead
>
> **Key factors considered**:
> 1. Server health (critical - must be healthy)
> 2. Current connections (for load distribution)
> 3. Response time (for performance-based routing)
> 4. Server capacity/weight (respect hardware differences)
> 5. Session persistence (sticky sessions)
> 6. Geographic location (minimize latency)
> 7. Request type/path (route based on URL patterns)
>
> The load balancer maintains real-time state in memory/Redis tracking active connections, response times, and health status for intelligent decision-making.

---

## Key Takeaways:
- **Decision time**: 5-10ms total overhead
- **Health checks**: Run every 5-10 seconds
- **State tracking**: Redis for distributed state
- **Fallback**: If selected server fails, immediately try next
- **Adaptive**: Metrics updated in real-time for dynamic decisions

