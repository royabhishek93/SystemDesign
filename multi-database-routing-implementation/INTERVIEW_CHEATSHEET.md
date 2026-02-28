# Interview Cheat Sheet - Runtime Database Routing

## 30-Second Answer

> "In distributed applications operating in multiple regions, you need to switch databases at runtime based on the user's location. For example, Uber needs INDIA users' data to stay in an Indian database (data residency law) while US users' data stays in the US database. We use Spring Boot's `AbstractRoutingDataSource` combined with ThreadLocal context holder (`TenantContext`) to route queries dynamically. An HTTP interceptor extracts the user's region and sets it in `TenantContext`, then `DynamicRoutingDataSource` reads this context to determine which database to use for each query."

---

## 2-Minute Complete Answer

### Problem
```
Multi-region app (Uber):
- INDIA users → must use INDIA database (law)
- US users → must use US database (compliance)
- EU users → must use EU database (GDPR)

How do you switch databases at runtime?
→ Same code, different databases based on user region
```

### Solution: 4 Key Components

#### 1️⃣ TenantContext (ThreadLocal)
```java
public class TenantContext {
    private static final ThreadLocal<String> tenantHolder = new ThreadLocal<>();
    
    public static void setTenant(String tenant) { tenantHolder.set(tenant); }
    public static String getTenant() { return tenantHolder.get(); }
    public static void clear() { tenantHolder.remove(); } // CRITICAL
}
```
**Why ThreadLocal?** 
- Each HTTP request = separate thread
- Store context per-thread = no cross-contamination
- Available everywhere without parameter passing

#### 2️⃣ DynamicRoutingDataSource
```java
public class DynamicRoutingDataSource extends AbstractRoutingDataSource {
    @Override
    protected Object determineCurrentLookupKey() {
        return TenantContext.getTenant(); // Returns "INDIA" or "US"
    }
}
```
**What it does:**
- Intercepts every database query
- Reads current tenant from ThreadLocal
- Routes query to correct database
- User doesn't see this happening

#### 3️⃣ TenantInterceptor (HTTP)
```java
@Component
public class TenantInterceptor implements HandlerInterceptor {
    @Override
    public boolean preHandle(HttpServletRequest request, ...) {
        String region = request.getHeader("X-Region"); // or from JWT
        TenantContext.setTenant(region.toUpperCase());
        return true;
    }
    
    @Override
    public void afterCompletion(...) {
        TenantContext.clear(); // ⚠️ CRITICAL: Cleanup
    }
}
```
**Flow:**
```
Request → Extract region → Set TenantContext → Process → Clear TenantContext → Response
```

#### 4️⃣ Service Layer Verification
```java
public UserDTO getUserById(Long userId) {
    String currentTenant = TenantContext.getTenant();
    User user = userRepository.findById(userId);
    
    // SECURITY: Verify region matches
    if (!user.getRegion().equals(currentTenant)) {
        throw new UnauthorizedException("Wrong region!");
    }
    return mapToDTO(user);
}
```

### How It Works (Visual)
```
POST /api/users {"name": "Rahul"} 
Header: X-Region: INDIA
            ↓
    TenantInterceptor
    TenantContext.setTenant("INDIA")
            ↓
    UserController.createUser()
            ↓
    UserService.createUser()
    Creates User object
    user.region = "INDIA"
            ↓
    userRepository.save(user)
            ↓
    DynamicRoutingDataSource
    determineCurrentLookupKey() → "INDIA"
    targetDataSources.get("INDIA") → indiaDataSource
            ↓
    INSERT INTO users ... (on INDIA database only!)
            ↓
    TenantInterceptor.afterCompletion()
    TenantContext.clear()
            ↓
    Response sent to client
```

---

## Security: 3 Layers

### ❌ Layer 1: WRONG Way
```java
// ❌ VULNERABLE: User can fake region
String region = request.getParameter("region");
TenantContext.setTenant(region);
```

### ✅ Layer 1: RIGHT Way
```java
// ✅ SECURE: From JWT (signature verified)
String region = SecurityContextHolder.getContext()
    .getAuthentication()
    .getPrincipal()
    .getRegion(); // From verified JWT token
TenantContext.setTenant(region);
```

### Layer 2: Database Routing
```
User knows their region is "INDIA"
Query routes to INDIA database only
If they're actually a US user, wrong data won't exist there
Wrong user data won't be returned
```

### Layer 3: Service Verification
```java
User user = userRepository.findById(id); // From correct DB

if (!user.getRegion().equals(TenantContext.getTenant())) {
    throw UnauthorizedException(...);
}
// Extra check: Region in record != request region = STOP
```

---

## Configuration (pom.xml)

```xml
<!-- Spring Data JPA -->
<dependency>
    <groupId>org.springframework.boot</groupId>
    <artifactId>spring-boot-starter-data-jpa</artifactId>
</dependency>

<!-- MySQL Driver -->
<dependency>
    <groupId>com.mysql</groupId>
    <artifactId>mysql-connector-java</artifactId>
    <version>8.0.33</version>
</dependency>
```

## Configuration (application.yml)

```yaml
datasource:
  india:
    url: jdbc:mysql://india-db:3306/uber_india
    username: root
    password: password123
    hikari:
      maximum-pool-size: 20

  us:
    url: jdbc:mysql://us-db:3306/uber_us
    username: root
    password: password123
    hikari:
      maximum-pool-size: 20

  eu:
    url: jdbc:mysql://eu-db:3306/uber_eu
    username: root
    password: password123
    hikari:
      maximum-pool-size: 20
```

## Configuration (DataSourceConfig)

```java
@Configuration
public class DataSourceConfig {
    
    @Bean
    public DataSource routingDataSource() {
        Map<Object, Object> dataSourceMap = new HashMap<>();
        dataSourceMap.put("INDIA", indiaDataSource());
        dataSourceMap.put("US", usDataSource());
        dataSourceMap.put("EU", euDataSource());
        
        DynamicRoutingDataSource routingDS = new DynamicRoutingDataSource();
        routingDS.setTargetDataSources(dataSourceMap);
        routingDS.setDefaultTargetDataSource(indiaDataSource());
        routingDS.afterPropertiesSet(); // IMPORTANT!
        
        return routingDS;
    }
}
```

---

## Common Mistakes

| Mistake | Impact | Fix |
|--------|--------|-----|
| Not calling `TenantContext.clear()` | User data leaks to next request | Always call in `afterCompletion()` |
| Extracting region from user parameter | User can fake region | Extract from JWT (verified) |
| Not verifying region in service | Possible cross-DB access | Add check in service |
| Not calling `afterPropertiesSet()` | Routing datasource not initialized | Call in `@Bean` method |
| Missing `@ConfigurationProperties` | Datasources not created | Add annotation to each datasource |
| No transaction management | Partial updates | Configure TransactionManager |

---

## API Examples

### Create INDIA User
```bash
curl -X POST http://localhost:8080/api/users \
  -H "X-Region: INDIA" \
  -d '{"email": "rahul@example.com", "phone": "+919876543210", ...}'

# Response: 201 Created
# User stored in INDIA database
```

### Create US User (SAME endpoint, different database!)
```bash
curl -X POST http://localhost:8080/api/users \
  -H "X-Region: US" \
  -d '{"email": "john@example.com", "phone": "+14155551234", ...}'

# Response: 201 Created
# User stored in US database
```

### Try Cross-Tenant Access
```bash
# Create US user (ID 1)
# Try to fetch from INDIA context
curl http://localhost:8080/api/users/1 \
  -H "X-Region: INDIA"

# Response: 403 Forbidden
# "User does not belong to your region: US"
```

---

## Testing

```java
@SpringBootTest
public class MultiDatabaseRoutingTest {
    
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
        
        // Verify isolation
        TenantContext.setTenant("INDIA");
        assertThrows(UnauthorizedException.class,
            () → userService.getUserById(usUser.getId()));
        TenantContext.clear();
    }
    
    @Test
    public void testContextCleanup() {
        TenantContext.setTenant("US");
        TenantContext.clear();
        
        // After clear, gets default
        assertEquals("INDIA", TenantContext.getTenant());
    }
}
```

---

## When You Don't Know an Answer

**Q: "How would you handle distributed transactions across databases?"**

**A:** 
"Great question! That's complex. With separate databases, distributed transactions are hard. There are two main approaches:

1. **Saga Pattern**: Compensating transactions
   - Withdraw from INDIA DB ✓
   - Deposit to US DB - if fails, reverse withdrawal
   
2. **Don't do them**: Keep data within one database
   - Use settlements layer
   - Each transaction stays in one region
   - Settle cross-region transfers periodically

This actually aligns with business needs - most transactions are intra-region anyway."

---

## Follow-Up Questions to Expect

1. **"How do you prevent context leakage?"**
   → Always call `TenantContext.clear()` in interceptor

2. **"What if someone spoofs the X-Region header?"**
   → Extract from JWT (cryptographically signed), not headers

3. **"How do you handle scheduled jobs?"**
   → Manually set TenantContext for each tenant in loop

4. **"What about schema migrations?"**
   → Use Liquibase with region-specific change sets

5. **"How do you test this?"**
   → Use H2 in-memory databases, set TenantContext explicitly

6. **"How many databases can this handle?"**
   → Unlimited - just add to targetDataSources map

7. **"What's the performance impact?"**
   → Negligible - just a HashMap lookup per query

8. **"How do you monitor this?"**
   → Log queries per tenant, monitor connection pools, check for context leakage

---

## Practice Your Delivery

**Tone**: Confident but not arrogant
**Pace**: Medium (allow time for "hmms" and nods)
**Words to use naturally**:
- "Tenant context"
- "Abstract routing datasource"
- "Thread local storage"
- "Security layers"
- "Data isolation"
- "Compliance/GDPR"
- "Connection pooling"

**Words to avoid**:
- "Uh..." (use pause instead)
- "Basically" (too informal for interview)
- "I think..." (be confident)
- "Like..." (not technical)

---

## Last Minute Tips

✅ Draw a simple diagram (interceptor → context → routing DS → DB)
✅ Mention real companies (Uber, Netflix, Stripe) use this pattern
✅ Emphasize security (verify region in service layer)
✅ Show you know the pitfalls (context leakage, cross-tenant access)
✅ Mention alternatives (row-level filtering, sharding, separate services)
✅ Be ready to code simple version (TenantContext, DynamicRoutingDS)

---

**Print this page before your interview!** ✅

