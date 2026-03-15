# Connection Pooling - Efficient Database Connections

## What is Connection Pooling?

**Connection Pooling** is a technique of **reusing database connections** instead of creating a new connection for every request.

Think of it like a **taxi stand** - instead of calling a new taxi for each person (slow), taxis wait at the stand ready to go (fast).

```
┌─────────────────────────────────────────────────────────────────────────┐
│              WITHOUT Connection Pooling (Bad)                            │
└─────────────────────────────────────────────────────────────────────────┘

Every request creates NEW connection:

Request 1:
  │
  │ 1. Create TCP connection (100ms)
  │ 2. Authenticate (50ms)
  │ 3. Execute query (10ms)
  │ 4. Close connection (10ms)
  │
  Total: 170ms ❌ (Most time wasted on setup!)

Request 2:
  │
  │ 1. Create TCP connection (100ms) ← Waste!
  │ 2. Authenticate (50ms) ← Waste!
  │ 3. Execute query (10ms)
  │ 4. Close connection (10ms)
  │
  Total: 170ms ❌

Request 3:
  │
  │ 1. Create TCP connection (100ms) ← Waste!
  │ 2. Authenticate (50ms) ← Waste!
  │ 3. Execute query (10ms)
  │ 4. Close connection (10ms)
  │
  Total: 170ms ❌

Problems:
• 150ms wasted per request on connection setup
• Database can only handle ~1000 connections
• Hitting limit = New requests REJECTED ❌
• Creating connections is EXPENSIVE


┌─────────────────────────────────────────────────────────────────────────┐
│              WITH Connection Pooling (Good)                              │
└─────────────────────────────────────────────────────────────────────────┘

Pool of READY-TO-USE connections:

┌─────────────────────────────────────────┐
│         Connection Pool                 │
│                                         │
│  ┌────────┐  ┌────────┐  ┌────────┐   │
│  │ Conn 1 │  │ Conn 2 │  │ Conn 3 │   │  ← Pre-created,
│  │ Ready  │  │ Ready  │  │ In Use │   │    authenticated
│  └────────┘  └────────┘  └────────┘   │
│                                         │
│  ┌────────┐  ┌────────┐  ┌────────┐   │
│  │ Conn 4 │  │ Conn 5 │  │ Conn 6 │   │
│  │ Ready  │  │ Ready  │  │ Ready  │   │
│  └────────┘  └────────┘  └────────┘   │
│                                         │
│  Pool Size: 10 connections              │
└─────────────────────────────────────────┘

Request 1:
  │
  │ 1. Get connection from pool (1ms) ✓ Fast!
  │ 2. Execute query (10ms)
  │ 3. Return connection to pool (1ms)
  │
  Total: 12ms ✓ (14x faster!)

Request 2:
  │
  │ 1. Get connection from pool (1ms) ✓
  │ 2. Execute query (10ms)
  │ 3. Return connection to pool (1ms)
  │
  Total: 12ms ✓

Request 3:
  │
  │ 1. Get connection from pool (1ms) ✓
  │ 2. Execute query (10ms)
  │ 3. Return connection to pool (1ms)
  │
  Total: 12ms ✓

Benefits:
✓ Reuse connections (no setup overhead)
✓ 14x faster (12ms vs 170ms)
✓ Database handles fewer total connections
✓ Better resource utilization
```

---

## How Connection Pooling Works

```
┌─────────────────────────────────────────────────────────────────────────┐
│                 CONNECTION POOL ARCHITECTURE                             │
└─────────────────────────────────────────────────────────────────────────┘

                    ┌─────────────────────────────┐
                    │      Application Server     │
                    │                             │
                    │  ┌────────────────────────┐ │
                    │  │   Thread 1             │ │
                    │  │   (handling request)   │ │
                    │  └──────────┬─────────────┘ │
                    │             │                │
                    │             │ Request        │
                    │             │ connection     │
                    │             ▼                │
                    │  ┌──────────────────────────┐│
                    │  │   Connection Pool        ││
                    │  │   (HikariCP, C3P0)       ││
                    │  │                          ││
                    │  │  Available Connections:  ││
                    │  │  ┌────┐ ┌────┐ ┌────┐   ││
                    │  │  │ C1 │ │ C2 │ │ C3 │   ││ ← Idle
                    │  │  └────┘ └────┘ └────┘   ││
                    │  │                          ││
                    │  │  In-Use Connections:     ││
                    │  │  ┌────┐ ┌────┐           ││
                    │  │  │ C4 │ │ C5 │           ││ ← Active
                    │  │  └────┘ └────┘           ││
                    │  │                          ││
                    │  │  Total: 5/10 (50% used)  ││
                    │  └──────────┬───────────────┘│
                    └─────────────┼─────────────────┘
                                  │
                                  │ Physical
                                  │ connections
                                  ▼
                    ┌─────────────────────────────┐
                    │      Database Server        │
                    │      (PostgreSQL)           │
                    │                             │
                    │  Active connections: 5      │
                    │  Max connections: 100       │
                    └─────────────────────────────┘


LIFECYCLE OF A POOLED CONNECTION:
──────────────────────────────────

1. INITIALIZATION (App startup)
   ────────────────────────────
   • Pool creates 5 connections (minPoolSize)
   • Authenticates each connection
   • Keeps them idle, ready to use

2. REQUEST ARRIVES
   ───────────────
   Thread 1: Need connection!
   Pool: Here's Connection #3 (1ms)

3. QUERY EXECUTION
   ───────────────
   Thread 1 → Conn #3 → SELECT * FROM users WHERE id = 123
   Query executes (10ms)

4. RETURN TO POOL
   ──────────────
   Thread 1: Done with connection
   Pool: Returns Conn #3 to available pool (1ms)
   Conn #3 status: Available (ready for next request)

5. REUSE
   ─────
   Thread 2: Need connection!
   Pool: Here's Connection #3 again (1ms)
   Same connection, no overhead! ✓
```

---

## Connection Pool Configuration

```
┌─────────────────────────────────────────────────────────────────────────┐
│                  CONNECTION POOL PARAMETERS                              │
└─────────────────────────────────────────────────────────────────────────┘

1. MIN POOL SIZE (minimumIdle)
───────────────────────────────
Number of connections to keep alive even when idle

Example: minimumIdle = 5

┌──────────────────────────┐
│ Pool (low traffic)       │
│ ┌────┐ ┌────┐ ┌────┐    │
│ │ C1 │ │ C2 │ │ C3 │    │ ← Always maintained
│ └────┘ └────┘ └────┘    │
│ ┌────┐ ┌────┐           │
│ │ C4 │ │ C5 │           │
│ └────┘ └────┘           │
└──────────────────────────┘

✓ Prevents connection overhead during sudden traffic spike
✗ Wastes resources if traffic is low


2. MAX POOL SIZE (maximumPoolSize)
───────────────────────────────────
Maximum number of connections pool can create

Example: maximumPoolSize = 20

┌──────────────────────────┐
│ Pool (high traffic)      │
│ ┌────┐ ┌────┐ ... ┌────┐│ ← Up to 20
│ │ C1 │ │ C2 │     │ C20││   connections
│ └────┘ └────┘     └────┘│
└──────────────────────────┘

If 21st request comes:
• Pool is full (20/20 used)
• Request WAITS until connection available
• Or TIMEOUT after connectionTimeout (30s default)

✓ Prevents overwhelming database
✗ Requests may wait if pool exhausted


3. CONNECTION TIMEOUT
─────────────────────
How long to wait for available connection before error

Example: connectionTimeout = 30000 (30 seconds)

Scenario: Pool full (20/20 connections in use)
Request 21 arrives:
  t=0s:  Request for connection
  t=1s:  Still waiting...
  t=5s:  Still waiting...
  t=30s: TIMEOUT! Throw exception ❌

✓ Prevents indefinite waiting
✗ Users see error if pool exhausted


4. IDLE TIMEOUT
───────────────
How long a connection can be idle before being closed

Example: idleTimeout = 600000 (10 minutes)

┌──────────────────────────┐
│ Pool                     │
│ ┌────┐ ┌────┐           │
│ │ C1 │ │ C2 │ Active    │
│ └────┘ └────┘           │
│ ┌────┐                  │
│ │ C3 │ Idle for 11 min  │ ← Closed!
│ └────┘                  │
└──────────────────────────┘

✓ Frees resources during low traffic
✗ May need to recreate connection later


5. MAX LIFETIME
───────────────
Maximum age of a connection before being retired

Example: maxLifetime = 1800000 (30 minutes)

Why?
• Database may close stale connections
• Prevent connection leaks
• Refresh connections periodically

┌──────────────────────────┐
│ Connection timeline      │
│                          │
│ Created: 10:00 AM        │
│ Age: 30 minutes          │
│ Retired: 10:30 AM ✓      │
│ New connection created   │
└──────────────────────────┘


6. LEAK DETECTION THRESHOLD
───────────────────────────
Warn if connection not returned to pool

Example: leakDetectionThreshold = 60000 (60 seconds)

WARNING: Connection leak detected!
Connection has been out of pool for 60+ seconds.
Possible cause: Developer forgot to close connection.

Helps find bugs in code!
```

---

## Connection Pool Configuration Examples

```
┌─────────────────────────────────────────────────────────────────────────┐
│                    HIKARICP CONFIGURATION                                │
└─────────────────────────────────────────────────────────────────────────┘

HikariCP is the fastest, most popular Java connection pool

Spring Boot (application.properties):
──────────────────────────────────────

# Database connection
spring.datasource.url=jdbc:postgresql://localhost:5432/mydb
spring.datasource.username=admin
spring.datasource.password=secret

# HikariCP settings
spring.datasource.hikari.minimum-idle=5           # Keep 5 idle connections
spring.datasource.hikari.maximum-pool-size=20     # Max 20 connections
spring.datasource.hikari.connection-timeout=30000 # Wait 30s for connection
spring.datasource.hikari.idle-timeout=600000      # Close idle after 10 min
spring.datasource.hikari.max-lifetime=1800000     # Retire after 30 min
spring.datasource.hikari.leak-detection-threshold=60000  # Warn after 60s


Java Configuration:
───────────────────

HikariConfig config = new HikariConfig();
config.setJdbcUrl("jdbc:postgresql://localhost:5432/mydb");
config.setUsername("admin");
config.setPassword("secret");

// Pool settings
config.setMinimumIdle(5);              // Min connections
config.setMaximumPoolSize(20);         // Max connections
config.setConnectionTimeout(30000);    // 30 seconds
config.setIdleTimeout(600000);         // 10 minutes
config.setMaxLifetime(1800000);        // 30 minutes
config.setLeakDetectionThreshold(60000); // 60 seconds

HikariDataSource dataSource = new HikariDataSource(config);


┌─────────────────────────────────────────────────────────────────────────┐
│                    SIZING YOUR CONNECTION POOL                           │
└─────────────────────────────────────────────────────────────────────────┘

TOO SMALL:
──────────
Pool size: 5
Concurrent requests: 50

Result:
• 5 requests execute
• 45 requests WAIT
• Users experience delays ❌

Symptoms:
• High wait times
• Frequent timeouts
• Poor response time


TOO LARGE:
──────────
Pool size: 500
Database max connections: 100

Result:
• Database overwhelmed
• Out of memory
• Poor performance ❌

Symptoms:
• Database CPU 100%
• "Too many connections" errors
• Database crashes


OPTIMAL:
────────

Formula:
connections = ((core_count * 2) + effective_spindle_count)

Example:
• Server: 4 CPU cores
• Database: SSD (effective_spindle_count ≈ 1-2)
• Optimal: (4 * 2) + 2 = 10 connections per app server

Multiple app servers?
• 5 app servers × 10 connections = 50 total database connections
• Database limit: 100 connections
• 50% utilization ✓ (room for growth)


REAL-WORLD GUIDELINES:
──────────────────────

Small app (< 1000 users):
  minimumIdle: 5
  maximumPoolSize: 10

Medium app (1000-10k users):
  minimumIdle: 10
  maximumPoolSize: 20

Large app (10k-100k users):
  minimumIdle: 20
  maximumPoolSize: 50

Very large (100k+ users):
  • Use multiple app servers
  • Each with maximumPoolSize: 20-50
  • Total: Depends on database capacity


MONITORING:
───────────

Track these metrics:
• Active connections (should be < 80% of pool size)
• Idle connections (should have some idle connections)
• Wait time (should be < 1ms)
• Connection creation rate (should be low after startup)

HikariCP metrics:
──────────────────
Pool: mypool
Total connections: 20
Active: 15 (75%)
Idle: 5 (25%)
Waiting threads: 0 ✓
Connection creation: 0.1/second (after warmup)

✓ Healthy pool!
```

---

## Connection Pool in Action

```
┌─────────────────────────────────────────────────────────────────────────┐
│                  REQUEST FLOW WITH CONNECTION POOL                       │
└─────────────────────────────────────────────────────────────────────────┘

SCENARIO: E-commerce checkout
User clicks "Place Order" button


Step 1: Request arrives at application
───────────────────────────────────────

HTTP POST /orders
Thread: tomcat-http-1
Time: t=0ms


Step 2: Application needs database connection
──────────────────────────────────────────────

Code:
@Transactional
public Order createOrder(OrderRequest request) {
    // Get connection from pool (automatic via Spring/Hibernate)
    Order order = new Order();
    orderRepository.save(order);  // Uses pooled connection
    return order;
}

Pool state:
┌──────────────────────────┐
│ Available: [C1, C2, C3]  │ ← Pick C1
│ In-Use: [C4, C5]         │
└──────────────────────────┘

Action: Assign C1 to thread tomcat-http-1
Time: t=1ms (instant!)


Step 3: Execute database query
───────────────────────────────

SQL: INSERT INTO orders (user_id, total, status) VALUES (123, 99.99, 'pending')
Connection: C1
Time: t=1ms → t=11ms (10ms query)


Step 4: Return connection to pool
──────────────────────────────────

Transaction commits → Connection released
Connection C1 returned to pool

Pool state:
┌──────────────────────────┐
│ Available: [C1, C2, C3]  │ ← C1 back!
│ In-Use: [C4, C5]         │
└──────────────────────────┘

Time: t=12ms


Step 5: Response sent to user
──────────────────────────────

HTTP 201 Created
{ "orderId": 123, "status": "pending" }

Total time: 12ms ✓


CONCURRENT REQUESTS:
────────────────────

10 requests arrive simultaneously:

t=0ms:
  Requests: [R1, R2, R3, R4, R5, R6, R7, R8, R9, R10]
  Pool: 5 connections available

t=1ms:
  R1 → C1
  R2 → C2
  R3 → C3
  R4 → C4
  R5 → C5
  R6, R7, R8, R9, R10 → WAITING (pool exhausted)

t=11ms:
  R1 completes → C1 returned
  R6 → C1 (immediately reused)

t=12ms:
  R2 completes → C2 returned
  R7 → C2

t=13ms:
  R3 completes → C3 returned
  R8 → C3

... and so on

Result:
✓ All requests served
✓ No connection creation overhead
✓ Efficient resource usage
```

---

## Common Issues & Solutions

```
┌─────────────────────────────────────────────────────────────────────────┐
│                 CONNECTION POOL PROBLEMS                                 │
└─────────────────────────────────────────────────────────────────────────┘

❌ PROBLEM 1: Connection Pool Exhausted
────────────────────────────────────────

Error:
HikariPool-1 - Connection is not available, request timed out after 30000ms

Cause:
• Too many concurrent requests
• Pool size too small
• Connections not being returned (leak)

Solution:
──────────

1. Check pool size:
   maximumPoolSize = 20  ← Too small?
   Increase to: 50

2. Check for connection leaks:
   @Transactional  ← Missing?
   public void createOrder() {
       // Without @Transactional, connection may not be returned!
   }

   Fix: Add @Transactional

3. Check slow queries:
   Query taking 10 seconds → Blocks connection
   Fix: Optimize query, add indexes


❌ PROBLEM 2: Too Many Connections to Database
───────────────────────────────────────────────

Error:
ERROR: sorry, too many clients already
PostgreSQL max_connections = 100

Cause:
• Multiple app servers each with large pools
• App1: 50 connections
• App2: 50 connections
• App3: 50 connections
• Total: 150 connections > Database limit (100)

Solution:
──────────

1. Reduce pool size per app:
   Before: maximumPoolSize = 50
   After:  maximumPoolSize = 20
   Total: 3 × 20 = 60 connections ✓

2. Or increase database limit:
   PostgreSQL config:
   max_connections = 200

3. Or use connection pooler (PgBouncer):
   Apps → PgBouncer → Database
   PgBouncer maintains fewer database connections


❌ PROBLEM 3: Connection Leaks
───────────────────────────────

Leak: Connection borrowed but never returned

Code with leak:
───────────────

Connection conn = dataSource.getConnection();
Statement stmt = conn.createStatement();
ResultSet rs = stmt.executeQuery("SELECT * FROM users");
// ... process results ...
// ❌ Never closed! Connection stuck "in use"

Pool state after 10 requests:
┌──────────────────────────┐
│ Available: []            │ ← Empty!
│ In-Use: [C1...C10]       │ ← All stuck!
└──────────────────────────┘

New requests → Timeout! ❌


Fix:
────

try-with-resources (auto-closes):

try (Connection conn = dataSource.getConnection();
     Statement stmt = conn.createStatement();
     ResultSet rs = stmt.executeQuery("SELECT * FROM users")) {
    // ... process results ...
}  // ← Automatically closed ✓

Or use Spring JDBC Template:

@Autowired
private JdbcTemplate jdbcTemplate;

public List<User> getUsers() {
    return jdbcTemplate.query("SELECT * FROM users", new UserRowMapper());
}  // ← Connection automatically returned ✓


❌ PROBLEM 4: Stale Connections
────────────────────────────────

Issue: Database closes idle connections, but pool thinks they're still open

Error:
Connection is closed
No operations allowed after connection closed

Cause:
• Database idle timeout (5 minutes)
• Pool idle timeout longer (10 minutes)
• Connection closed by database, but pool doesn't know

Solution:
──────────

1. Set pool maxLifetime < database timeout:
   Database timeout: 5 minutes (300s)
   Pool maxLifetime: 4 minutes (240s)

   spring.datasource.hikari.max-lifetime=240000

2. Enable connection test:
   spring.datasource.hikari.connection-test-query=SELECT 1

   Pool tests connection before giving to application


❌ PROBLEM 5: Performance Degradation
───────────────────────────────────────

Issue: Queries slow down over time

Cause:
• Pool exhausted → Requests wait
• Database overloaded → Queries slow
• Connection creation spike → Overhead

Diagnosis:
──────────

Check HikariCP metrics:
• Active connections: 20/20 (100%) ❌
• Waiting threads: 50 ❌
• Connection acquisition time: 5000ms ❌

Solution:
──────────

1. Scale horizontally:
   Add more app servers

2. Optimize queries:
   Add database indexes

3. Increase pool size (if database can handle):
   maximumPoolSize: 20 → 30

4. Use caching:
   Cache hot data in Redis → Reduce database load
```

---

## Connection Pooling Best Practices

```
┌─────────────────────────────────────────────────────────────────────────┐
│                    BEST PRACTICES                                        │
└─────────────────────────────────────────────────────────────────────────┘

1. ALWAYS USE @Transactional
─────────────────────────────

@Transactional  ← Ensures connection returned!
public void createOrder(Order order) {
    orderRepository.save(order);
}

Without @Transactional:
• Must manually manage connection
• Risk of connection leaks


2. USE PREPARED STATEMENTS
──────────────────────────

✗ Bad:
String sql = "SELECT * FROM users WHERE id = " + userId;
// SQL injection risk + No prepared statement caching

✓ Good:
String sql = "SELECT * FROM users WHERE id = ?";
PreparedStatement stmt = conn.prepareStatement(sql);
stmt.setLong(1, userId);
// Safe + Prepared statement cached by pool


3. CLOSE RESOURCES (or use try-with-resources)
───────────────────────────────────────────────

✓ Good (auto-close):
try (Connection conn = dataSource.getConnection();
     PreparedStatement stmt = conn.prepareStatement(sql);
     ResultSet rs = stmt.executeQuery()) {
    // Process results
}  // Auto-closed

Or use Spring JDBC/JPA (handles automatically)


4. SET APPROPRIATE TIMEOUTS
───────────────────────────

connection-timeout: 30s (wait for connection)
idle-timeout: 10 minutes (close idle)
max-lifetime: 30 minutes (recycle)

Don't set too high:
• connection-timeout: 5 minutes ❌ (users wait too long)
• max-lifetime: 24 hours ❌ (stale connections)


5. MONITOR POOL METRICS
───────────────────────

Track:
• Active connections (< 80% of pool size)
• Idle connections (> 0, indicates capacity)
• Wait time (< 10ms)
• Connection creation rate (low after startup)

Use monitoring tools:
• Prometheus + Grafana
• Spring Boot Actuator
• HikariCP JMX metrics


6. SIZE POOL CORRECTLY
──────────────────────

Start with formula:
  pool_size = (CPU_cores × 2) + effective_spindle_count

Example:
  4 cores × 2 + 2 = 10 connections

Load test and adjust:
• If wait time high → Increase pool size
• If database CPU high → Decrease pool size or optimize queries


7. USE SINGLE POOL PER DATABASE
────────────────────────────────

✗ Bad: Multiple pools to same database
DataSource pool1 = createPool();  // 20 connections
DataSource pool2 = createPool();  // 20 connections
Total: 40 connections (wasteful!)

✓ Good: Single pool shared by all threads
DataSource pool = createPool();  // 20 connections
All threads use same pool ✓


8. ENABLE LEAK DETECTION IN DEV
────────────────────────────────

Development:
spring.datasource.hikari.leak-detection-threshold=10000  # 10 seconds

Production:
spring.datasource.hikari.leak-detection-threshold=60000  # 60 seconds

Helps catch connection leaks early!


9. TEST CONNECTION ON BORROW (Optional)
────────────────────────────────────────

spring.datasource.hikari.connection-test-query=SELECT 1

Pros:
✓ Catches stale connections
✓ Prevents errors

Cons:
✗ Extra query per connection (overhead)

Only enable if seeing stale connection errors


10. USE LATEST HIKARICP VERSION
───────────────────────────────

HikariCP is actively maintained and optimized

Update regularly:
<dependency>
    <groupId>com.zaxxer</groupId>
    <artifactId>HikariCP</artifactId>
    <version>5.0.1</version>
</dependency>
```

---

## System Design Interview Answer

**Question: "What is connection pooling and why is it important?"**

**Answer:**

"Connection pooling is a technique where we maintain a **pool of reusable database connections** instead of creating a new connection for every request.

**Why it's important:**

**Problem without pooling:**
Creating a database connection is expensive:
- TCP handshake: ~100ms
- Authentication: ~50ms
- Query execution: ~10ms
- Total: 170ms per request

For 100 concurrent requests, that's 17 seconds of pure overhead!

**Solution with pooling:**
- Pre-create 10-20 connections at startup
- Requests **borrow** connections from pool (1ms)
- Execute query (10ms)
- **Return** connection to pool (1ms)
- Total: 12ms per request

That's **14x faster** (12ms vs 170ms)!

**How it works:**
1. **Initialization**: Create minimum connections (e.g., 5) at startup
2. **Borrow**: Request arrives → Get connection from pool (instant)
3. **Execute**: Run query using pooled connection
4. **Return**: Transaction ends → Connection returned to pool (reused)
5. **Scale**: Create more connections if needed (up to max, e.g., 20)

**Configuration example (HikariCP):**
```
minimumIdle: 5          # Keep 5 idle connections
maximumPoolSize: 20     # Max 20 connections
connectionTimeout: 30s  # Wait 30s for connection
idleTimeout: 10m        # Close idle after 10 min
maxLifetime: 30m        # Recycle every 30 min
```

**Sizing:**
Formula: `pool_size = (CPU_cores × 2) + spindle_count`

For 4-core server: (4 × 2) + 2 = **10 connections**

With 5 app servers: 5 × 10 = 50 total database connections

**Common issues:**
1. **Pool exhausted**: Too many concurrent requests
   - Solution: Increase pool size or add more app servers
2. **Connection leaks**: Connections not returned
   - Solution: Use `@Transactional` or try-with-resources
3. **Too many connections**: Database overwhelmed
   - Solution: Reduce pool size per app server

**Monitoring:**
Track active connections (should be < 80%), wait time (should be < 10ms), and connection creation rate (should be low).

In production, I typically use **HikariCP** (fastest Java pool) with pool size 10-20 per app server, which handles thousands of requests per second efficiently."

---

## Key Takeaways

✓ **Reuse connections**: 10-20x faster than creating new ones

✓ **HikariCP**: Fastest, most popular Java connection pool

✓ **Size correctly**: Start with `(cores × 2) + spindles`

✓ **Set timeouts**: Connection timeout (30s), idle (10m), max lifetime (30m)

✓ **Use @Transactional**: Ensures connections returned to pool

✓ **Monitor metrics**: Active connections, wait time, creation rate

✓ **Avoid leaks**: Use try-with-resources or Spring JDBC/JPA

✓ **Balance pools**: Total connections < database max_connections

✓ **Scale horizontally**: Add app servers, not just pool size

✓ **Test on borrow**: Optional, catches stale connections (overhead)
