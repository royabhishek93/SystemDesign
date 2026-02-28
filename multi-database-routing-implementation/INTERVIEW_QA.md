# Interview Q&A - Runtime Database Switching

## Basic Questions

### Q1: Why would an application need to switch databases at runtime?

**Answer:**

There are several real-world scenarios:

1. **Data Residency Compliance**
   - GDPR (Europe): User data must stay in EU
   - India Data Act: User data must stay in India
   - CCPA (California): Specific data residency rules
   - Solution: Different regional databases

2. **Multi-Tenancy SaaS**
   - Company A wants their database in US
   - Company B wants their database in EU
   - Company C wants their database in India
   - Single application serves all

3. **Performance Optimization**
   - Indian users connect to India database (less latency)
   - US users connect to US database
   - Reduces network round-trip time

4. **Disaster Recovery**
   - Each region has independent backups
   - Region failure doesn't affect others

**Example: Uber ride-booking app**
- Indian users → India MySQL (data stays in country)
- US users → US MySQL (complies with local laws)
- Same application code, different databases

---

### Q2: How does Spring Boot's AbstractRoutingDataSource work?

**Answer:**

`AbstractRoutingDataSource` is a proxy datasource that routes queries to different physical datasources at runtime.

**How it works:**

```java
// You create multiple physical datasources
DataSource indiaDS = DataSourceBuilder.create()
    .setUrl("jdbc:mysql://india-db/uber_india")
    .build();

DataSource usDS = DataSourceBuilder.create()
    .setUrl("jdbc:mysql://us-db/uber_us")
    .build();

// AbstractRoutingDataSource routes between them
public class DynamicRoutingDS extends AbstractRoutingDataSource {
    @Override
    protected Object determineCurrentLookupKey() {
        // Return "INDIA" or "US" to select datasource
        return TenantContext.getTenant();
    }
}

// Register both datasources
Map<Object, Object> targetDataSources = new HashMap<>();
targetDataSources.put("INDIA", indiaDS);
targetDataSources.put("US", usDS);
routingDS.setTargetDataSources(targetDataSources);
```

**Execution flow:**

```
Application executes: userRepository.findById(1)
    ↓
Hibernate generates: SELECT * FROM users WHERE id = 1
    ↓
DynamicRoutingDataSource intercepts
    ↓
determineCurrentLookupKey() called → "INDIA"
    ↓
targetDataSources.get("INDIA") → indiaDS
    ↓
Query executed on India database
    ↓
Result returned to application
```

---

### Q3: What is ThreadLocal and why use it here?

**Answer:**

`ThreadLocal` is a Java utility that allows you to store data per thread.

```java
public class TenantContext {
    private static final ThreadLocal<String> tenantHolder = new ThreadLocal<>();
    
    public static void setTenant(String tenant) {
        tenantHolder.set(tenant); // Store in this thread's data
    }
    
    public static String getTenant() {
        return tenantHolder.get(); // Retrieve from this thread's data
    }
}
```

**Why ThreadLocal for tenant context?**

1. **Thread Isolation**: Each request runs in its own thread (Tomcat thread pool)
   ```
   Request 1 (Thread 1) → TenantContext.setTenant("INDIA")
   Request 2 (Thread 2) → TenantContext.setTenant("US")
   
   No cross-contamination!
   ```

2. **No Parameter Passing**: Don't need to pass `tenant` through a dozen method calls
   ```java
   // Instead of:
   method1(tenant) → method2(tenant) → method3(tenant) → method4(tenant)
   
   // Just read it globally:
   String tenant = TenantContext.getTenant();
   ```

3. **Implicit Context**: Available anywhere in the request chain
   - Controller doesn't know about it
   - Service doesn't need to pass it
   - Repository implicitly uses it

**Important: Always cleanup!**
```java
@Override
public void afterCompletion(...) {
    TenantContext.clear(); // Remove from ThreadLocal
    // Without this, connection pooling reuses threads with old context!
}
```

---

### Q4: How do you prevent cross-tenant data access?

**Answer:**

Three layers of security:

**Layer 1: Tenant Extraction - Trust Secure Sources Only**
```java
// ❌ VULNERABLE: User supplies region
String region = request.getParameter("region");
TenantContext.setTenant(region);

// ✅ SECURE: Extract from JWT (signature verified)
String region = SecurityContextHolder.getContext()
    .getAuthentication()
    .getPrincipal()
    .getRegion();
TenantContext.setTenant(region);
```

**Layer 2: Database Isolation**
```java
// User ID 1 in INDIA DB is different from User ID 1 in US DB
// By routing to correct database first, wrong users won't exist

TenantContext.setTenant("INDIA");
User user = userRepository.findById(1); // Queries INDIA database

TenantContext.setTenant("US");
User user = userRepository.findById(1); // Queries US database SAME ID DIFFERENT USER!
```

**Layer 3: Service Layer Verification**
```java
public UserDTO getUserById(Long userId) {
    String currentTenant = TenantContext.getTenant(); // "INDIA"
    
    User user = userRepository.findById(userId);
    
    // ALWAYS verify region matches
    if (!user.getRegion().equals(currentTenant)) {
        throw new UnauthorizedException("User from different region!");
    }
    
    return mapToDTO(user);
}
```

**Real attack example:**
```
Hacker tries: GET /api/users/1 with X-Region: INDIA
But they're actually a US user

Layer 1 Check:
- If X-Region from JWT: JWT.region = "US", not "INDIA" → BLOCKED
- If X-Region from header: They can set it → Goes to Layer 2

Layer 2 Check:
- User ID 1 might not exist in INDIA database
- If it does, it's different data
- Query succeeds

Layer 3 Check:
- Retrieved user.region = "INDIA"
- Current tenant = "US"
- Regions don't match → BLOCKED
```

---

## Intermediate Questions

### Q5: What happens if TenantContext is not cleared?

**Answer:**

This is a critical issue in connection pooling:

```
Scenario: TenantContext.clear() not called
══════════════════════════════════════════════════════════

Request 1 (Thread A):
┌─────────────────────────────────┐
│ Interceptor.preHandle()        │
│ TenantContext.setTenant("INDIA")│
│ TenantContext = "INDIA" ✓        │
│ (Thread A)                      │
└────────────┬────────────────────┘
             │
    ┌────────▼──────────┐
    │ Processing ...    │
    │ Database query    │
    └────────┬──────────┘
             │
┌────────────▼───────────────────────┐
│ afterCompletion()                  │
│ ❌ NOT CALLING TenantContext.clear()│
│ TenantContext = "INDIA" ✗ (LEAKED!) │
│ Connection returned to pool         │
│ ThreadLocal still contains "INDIA"  │
│ (Thread A) - reused by next request │
└────────────────────────────────────┘


Request 2 (Thread A - REUSED):
┌─────────────────────────────────┐
│ Interceptor.preHandle()        │
│ TenantContext.setTenant("US")  │
│ ❌ Actually sets "INDIA" from before!
│ (Because ThreadLocal wasn't cleared)
│ TenantContext = "INDIA" ✗ (WRONG!) │
│ (Thread A)                      │
└────────────┬────────────────────┘
             │
    ┌────────▼──────────────────────┐
    │ Routes to INDIA database       │
    │ But user is from US!           │
    │ ❌ SECURITY BREACH             │
    └────────────────────────────────┘
```

**Consequences:**
- 🔴 Users can access data from wrong region/tenant
- 🔴 GDPR/compliance violations
- 🔴 Data leakage between customers

**Solution:**
```java
@Component
public class TenantInterceptor implements HandlerInterceptor {
    
    @Override
    public void afterCompletion(HttpServletRequest request,
                               HttpServletResponse response,
                               Object handler,
                               Exception ex) {
        TenantContext.clear(); // ✅ ALWAYS cleanup
    }
}
```

Or use try-finally in edge cases:
```java
try {
    TenantContext.setTenant("INDIA");
    // ... do work ...
} finally {
    TenantContext.clear(); // ✅ Guaranteed cleanup
}
```

---

### Q6: How do you handle scheduled jobs with multiple tenants?

**Answer:**

Scheduled jobs run outside HTTP context, so no interceptor. You must manually set TenantContext.

```java
@Component
@Slf4j
public class DataMigrationScheduler {
    
    @Autowired
    private UserService userService;
    
    // ❌ WRONG: Runs for INDIA only
    @Scheduled(cron = "0 0 2 * * *")
    public void dailyMigration() {
        userService.migrateOldData(); 
        // Only uses whatever default/last tenant was set
    }
    
    // ✅ CORRECT: Runs for all tenants
    @Scheduled(cron = "0 0 2 * * *")
    public void dailyMigrationForAllTenants() {
        List<String> tenants = List.of("INDIA", "US", "EU");
        
        for (String tenant : tenants) {
            try {
                TenantContext.setTenant(tenant);
                log.info("Running daily migration for {}", tenant);
                
                userService.migrateOldData();
                
                log.info("Migration completed for {}", tenant);
            } catch (Exception e) {
                log.error("Migration failed for {}", tenant, e);
            } finally {
                TenantContext.clear();
            }
        }
    }
    
    // ✅ EVEN BETTER: Use @Async for parallel processing
    @Scheduled(cron = "0 0 2 * * *")
    public void dailyMigrationParallel() {
        List<String> tenants = List.of("INDIA", "US", "EU");
        tenants.forEach(this::runMigrationAsync);
    }
    
    @Async
    private void runMigrationAsync(String tenant) {
        try {
            TenantContext.setTenant(tenant);
            userService.migrateOldData();
        } finally {
            TenantContext.clear();
        }
    }
}
```

---

### Q7: What about distributed transactions across databases?

**Answer:**

**Problem**: Distributed transactions across databases are extremely complex.

```
Scenario: Transfer money from INDIA account to US account
═════════════════════════════════════════════════════════

// Try to do this atomically:
1. Withdraw from INDIA database
2. Transfer amount
3. Deposit to US database

Issue: Two separate databases = Two separate transactions
       If step 3 fails, rollback doesn't cascade

┌─────────────────┐         ┌─────────────────┐
│  INDIA DB       │         │  US DB          │
│                 │         │                 │
│ Accounts:       │         │ Accounts:       │
│ ┌─────────────┐ │         │ ┌─────────────┐ │
│ │ Rahul: 1000 │ │         │ │ John:  500  │ │
│ └─────────────┘ │         │ └─────────────┘ │
│                 │         │                 │
│ Step 1: ✓       │         │                 │
│ Withdraw 500    │         │                 │
│ Rahul: 500      │         │ John:  500      │
│ (COMMITTED)     │         │ (UNCOMMITTED)   │
│                 │         │                 │
└─────────────────┘         │ Step 2: ✗       │
                            │ Network error!  │
                            │ Deposit fails   │
                            │ ROLLBACK        │
                            │ John:  500      │
                            │ (UNCHANGED)     │
                            └─────────────────┘

Result:
══════════════════════════════════════════════════════
INDIA: Rahul lost 500 (committed withdrawal)
US: John never received 500 (failed deposit)

Money is lost! ❌
```

**Solutions:**

**Solution 1: Saga Pattern (Eventual Consistency)**
```java
@Service
public class TransferService {
    
    @Transactional
    public void transferMoney(Long fromUserId, Long toUserId, BigDecimal amount) {
        // Step 1: Withdraw with compensation
        try {
            TenantContext.setTenant("INDIA");
            userService.withdrawMoney(fromUserId, amount);
            // Committed
        } catch (Exception e) {
            throw e; // Fail fast
        } finally {
            TenantContext.clear();
        }
        
        // Step 2: Deposit with retry/compensation
        try {
            TenantContext.setTenant("US");
            userService.depositMoney(toUserId, amount);
            // Committed
        } catch (Exception e) {
            // COMPENSATE: Reverse withdrawal
            try {
                TenantContext.setTenant("INDIA");
                userService.depositMoney(fromUserId, amount);
            } catch (Exception compensateError) {
                log.error("CRITICAL: Compensation failed", compensateError);
                // Notify ops team - manual intervention needed
                alertOps("Transfer failed with unrecoverable error");
            }
            throw e;
        } finally {
            TenantContext.clear();
        }
    }
}

// Flow:
// 1. Withdraw from INDIA ✓
// 2. Try to deposit to US
//    - If succeeds: Done ✓
//    - If fails: Compensate (deposit back in INDIA)
```

**Solution 2: Don't Do Cross-Tenant Transactions**
```
Instead: Settlements Layer
═════════════════════════════════════════════════════════

INDIA User:
┌─────────────────────────────────┐
│ Users:                          │
│ - Account balance: 1000         │
│ - Pending transfer: -500 (US)   │ ← Marked but not removed
└─────────────────────────────────┘

US User:
┌─────────────────────────────────┐
│ Users:                          │
│ - Account balance: 500          │
│ - Pending receipt: +500 (INDIA) │ ← Marked but not added
└─────────────────────────────────┘

Settlement Service (runs daily):
1. Check all pending transfers
2. Retry failed transfers
3. Mark as completed

Advantage: Each transaction stays within one database
```

---

### Q8: How do you test multi-database routing?

**Answer:**

```java
@SpringBootTest
@TestPropertySource(locations = "classpath:application-dev.yml")
public class TenantRoutingTest {
    
    @Autowired
    private UserService userService;
    
    // Use H2 in-memory databases
    // application-dev.yml has:
    // datasource.india.url=jdbc:h2:mem:india
    // datasource.us.url=jdbc:h2:mem:us
    
    @BeforeEach
    public void setup() {
        TenantContext.clear();
    }
    
    @Test
    public void testDataIsolation() {
        // Create in INDIA
        TenantContext.setTenant("INDIA");
        UserDTO indiaUser = userService.createUser(...);
        TenantContext.clear();
        
        // Create in US
        TenantContext.setTenant("US");
        UserDTO usUser = userService.createUser(...);
        TenantContext.clear();
        
        // Verify both can be fetched from correct context
        TenantContext.setTenant("INDIA");
        UserDTO fetchedIndia = userService.getUserById(indiaUser.getId());
        assertEquals("INDIA", fetchedIndia.getRegion());
        TenantContext.clear();
        
        // Verify cross-tenant access fails
        TenantContext.setTenant("INDIA");
        assertThrows(UnauthorizedException.class, 
            () -> userService.getUserById(usUser.getId()));
        TenantContext.clear();
    }
    
    @Test
    public void testContextCleanup() {
        TenantContext.setTenant("US");
        assertTrue(TenantContext.getTenant().equals("US"));
        
        TenantContext.clear();
        assertEquals("INDIA", TenantContext.getTenant()); // Default
    }
}
```

---

## Advanced Questions

### Q9: Compare this approach with other multi-tenancy patterns

| Pattern | Isolation | Cost | Scaling | Compliance |
|---------|-----------|------|---------|-----------|
| **Separate Databases** (This) | ⭐⭐⭐⭐⭐ | ❌ High | ⭐⭐⭐⭐⭐ | ✅ Full |
| **Shared DB + Row-Level** | ⭐⭐ | ✅ Low | ⭐⭐ | ⚠️ Risk |
| **Shared Schema + Tenant Filter** | ⭐⭐ | ✅ Low | ⭐⭐ | ⚠️ Risk |
| **Sharding** | ⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐ |
| **Database-per-Service** | ⭐⭐⭐⭐ | ❌ High | ⭐⭐⭐⭐⭐ | ✅ Full |

**When to use which:**
-  **Separate Databases**: Enterprise, compliance-heavy (Uber, fintech)
- **Row-Level Filtering**: Cheap SaaS, non-regulated data
- **Sharding**: Very high scale, more complex
- **Database-per-Service**: Microservices, independent teams

---

### Q10: How would you monitor this in production?

**Answer:**

```java
@Component
public class TenantRoutingMonitor {
    
    private static final Logger logger = LoggerFactory.getLogger("TENANT_ROUTING");
    
    private final MeterRegistry meterRegistry;
    
    // Track queries per tenant
    private final Map<String, Long> queryCountPerTenant = 
        Collections.synchronizedMap(new HashMap<>());
    
    @BeforeEach
    public void beforeQuery() {
        String tenant = TenantContext.getTenant();
        queryCountPerTenant.merge(tenant, 1L, Long::sum);
        
        // Prometheus metric
        meterRegistry.counter(
            "database.queries",
            "tenant", tenant
        ).increment();
    }
    
    // Alert on context leakage
    @Scheduled(fixedRate = 60000)
    public void detectContextLeakage() {
        // If ThreadLocal still contains value after request completes
        // This indicates clearance issues
        
        logger.info("Query counts: {}", queryCountPerTenant);
    }
    
    // Monitor connection pool health
    @Scheduled(fixedRate = 30000)
    public void monitorConnectionPools() {
        HikariDataSource indiaPool = (HikariDataSource) indiaDataSource;
        HikariDataSource usPool = (HikariDataSource) usDataSource;
        
        logger.info("INDIA Pool: Active={}, Idle={}, Queue={}",
            indiaPool.getHikariPoolMXBean().getActiveConnections(),
            indiaPool.getHikariPoolMXBean().getIdleConnections(),
            indiaPool.getHikariPoolMXBean().getPendingThreadCount());
        
        logger.info("US Pool: Active={}, Idle={}, Queue={}",
            usPool.getHikariPoolMXBean().getActiveConnections(),
            usPool.getHikariPoolMXBean().getIdleConnections(),
            usPool.getHikariPoolMXBean().getPendingThreadCount());
    }
    
    // Alert on cross-tenant access attempts
    @Aspect
    public void logCrossTenantAccess() {
        // Log whenever UserService.UnauthorizedException is caught
        logger.warn("SECURITY: Cross-tenant access attempt detected");
        // Send alert to monitoring system
    }
}
```

---

## Follow-up Discussion Points

### If asked: "How would you handle schema migrations?"

```
Challenge: Database in India needs schema change
           But databases must stay in sync

Solution: Liquibase with region-specific change sets

liquibase/
  master.yaml
  india/
    add-column-2024-02-01.yaml
    add-index-2024-02-02.yaml
  us/
    add-column-2024-02-01.yaml
    add-index-2024-02-02.yaml
  eu/
    add-column-2024-02-01.yaml
    add-index-2024-02-02.yaml

Each region has identical change sets but separate execution.
Version tracking in DATABASECHANGELOG table per database.
```

### If asked: "How would you handle schema inconsistencies?"

```
Use schema validation tests that run against ALL databases:

@ParameterizedTest
@ValueSource(strings = {"INDIA", "US", "EU"})
public void testSchemaConsistency(String tenant) {
    TenantContext.setTenant(tenant);
    
    // Check all columns exist
    DatabaseMetaData metadata = connection.getMetaData();
    ResultSet columns = metadata.getColumns(null, null, "users", null);
    
    Set<String> columnNames = new HashSet<>();
    while (columns.next()) {
        columnNames.add(columns.getString("COLUMN_NAME"));
    }
    
    assertTrue(columnNames.contains("email"));
    assertTrue(columnNames.contains("region"));
    // ... more assertions ...
    
    TenantContext.clear();
}
```

---

