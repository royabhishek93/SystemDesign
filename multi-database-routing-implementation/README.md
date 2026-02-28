# Runtime Database Switching in Spring Boot
**Multi-Tenancy Pattern for Regional Data Isolation**

## 🎯 Problem Statement

In a globally distributed application (like Uber), users from different regions need to access data from their respective regional databases:
- **Indian users** → Indian database
- **US users** → US database
- **European users** → European database

The application must dynamically switch database connections **at runtime** based on the user's region/tenant context.

## 🏗️ Architecture Overview

```
User Request (with region info)
        ↓
  HTTPInterceptor
  (Extract region)
        ↓
  TenantContext
  (Store in ThreadLocal)
        ↓
  DynamicRoutingDataSource
  (Route to correct DB)
        ↓
  Regional Database
  (Execute query)
```

## 📁 Project Structure

```
multi-database-routing-implementation/
├── pom.xml                              # Maven dependencies
├── src/main/java/
│   └── com/uber/booking/
│       ├── config/
│       │   ├── DataSourceConfig.java             # Multiple datasource config
│       │   └── WebConfig.java                    # Interceptor registration
│       ├── context/
│       │   └── TenantContext.java                # ThreadLocal tenant holder
│       ├── routing/
│       │   └── DynamicRoutingDataSource.java     # Custom routing logic
│       ├── entity/
│       │   └── User.java                         # JPA Entity
│       ├── repository/
│       │   └── UserRepository.java               # Spring Data JPA
│       ├── service/
│       │   └── UserService.java                  # Business logic
│       ├── controller/
│       │   └── UserController.java               # REST endpoints
│       ├── interceptor/
│       │   └── TenantInterceptor.java            # Request interceptor
│       └── Application.java                      # Main class
├── src/main/resources/
│   ├── application.yml                  # Main configuration
│   ├── application-dev.yml              # Development profile
│   └── application-prod.yml             # Production profile
└── sql/
    ├── india-schema.sql                 # India DB schema
    └── us-schema.sql                    # US DB schema
```

## 🔑 Key Components

### 1. **TenantContext** (ThreadLocal Holder)
Stores the current region/tenant in thread-local storage so any component can access it:

```java
public class TenantContext {
    private static final ThreadLocal<String> tenantHolder = new ThreadLocal<>();
    
    public static void setTenant(String tenant) {
        tenantHolder.set(tenant);
    }
    
    public static String getTenant() {
        return tenantHolder.get();
    }
    
    public static void clear() {
        tenantHolder.remove();
    }
}
```

### 2. **DynamicRoutingDataSource** (Custom DataSource)
Extends `AbstractRoutingDataSource` to dynamically select datasource based on context:

```java
public class DynamicRoutingDataSource extends AbstractRoutingDataSource {
    @Override
    protected Object determineCurrentLookupKey() {
        return TenantContext.getTenant(); // Returns "INDIA" or "US"
    }
}
```

### 3. **DataSourceConfig** (Spring Configuration)
Defines multiple datasources and configures the routing:

```java
@Configuration
public class DataSourceConfig {
    
    @Bean
    @ConfigurationProperties(prefix = "datasource.india")
    public DataSource indiaDataSource() {
        return DataSourceBuilder.create().build();
    }
    
    @Bean
    @ConfigurationProperties(prefix = "datasource.us")
    public DataSource usDataSource() {
        return DataSourceBuilder.create().build();
    }
    
    @Bean
    public DataSource routingDataSource() {
        DynamicRoutingDataSource routingDataSource = new DynamicRoutingDataSource();
        
        Map<Object, Object> dataSourceMap = new HashMap<>();
        dataSourceMap.put("INDIA", indiaDataSource());
        dataSourceMap.put("US", usDataSource());
        
        routingDataSource.setTargetDataSources(dataSourceMap);
        routingDataSource.setDefaultTargetDataSource(indiaDataSource());
        
        return routingDataSource;
    }
}
```

### 4. **TenantInterceptor** (HTTP Interceptor)
Extracts region from request and sets it in context:

```java
@Component
public class TenantInterceptor implements HandlerInterceptor {
    
    @Override
    public boolean preHandle(HttpServletRequest request, 
                            HttpServletResponse response, 
                            Object handler) {
        String region = request.getHeader("X-Region");
        // or from JWT token claim
        // or from URL parameter
        
        if ("INDIA".equalsIgnoreCase(region) || "US".equalsIgnoreCase(region)) {
            TenantContext.setTenant(region);
        } else {
            TenantContext.setTenant("INDIA"); // default
        }
        return true;
    }
    
    @Override
    public void afterCompletion(HttpServletRequest request,
                               HttpServletResponse response,
                               Object handler,
                               Exception ex) {
        TenantContext.clear(); // Always cleanup
    }
}
```

## 🚀 How It Works

### Step-by-Step Flow

1. **User Request Arrives**
   ```
   GET /api/users/profile
   Headers: X-Region: INDIA
   ```

2. **Interceptor Extracts Region**
   - Reads `X-Region` header
   - Calls `TenantContext.setTenant("INDIA")`

3. **Controller Receives Request**
   ```java
   @GetMapping("/profile")
   public UserDTO getProfile() {
       return userService.getCurrentUserData();
   }
   ```

4. **Service Layer (BusinessLogic)**
   ```java
   @Service
   public class UserService {
       @Autowired
       private UserRepository userRepository;
       
       public UserDTO getCurrentUserData() {
           // TenantContext.getTenant() returns "INDIA"
           return userRepository.findByUserId(userId);
       }
   }
   ```

5. **DynamicRoutingDataSource Routes Query**
   - Calls `determineCurrentLookupKey()` → Returns "INDIA"
   - Selects India datasource from map
   - Executes query on India database

6. **Interceptor Cleanup**
   - After response, `TenantContext.clear()` is called
   - Prevents context leakage in connection pools

## 💡 Real-World Scenario

### User Login Flow

```
POST /api/auth/login
{
  "email": "user@example.com",
  "password": "...",
  "region": "INDIA"
}
↓
Interceptor: TenantContext.setTenant("INDIA")
↓
AuthService: validates against India DB
↓
JWT Token issued with region claim: { region: "INDIA" }
↓
Subsequent requests include token
↓
Interceptor extracts region from JWT
↓
Rest of session uses India DB
```

## 🔐 Security Considerations

### 1. **Prevent Tenant Switching Attacks**
```java
// ❌ Don't trust user input directly
@GetMapping("/users/{userId}")
public UserDTO getUser(@PathVariable String userId,
                       @RequestParam String region) {
    // SECURITY RISK: User can request US DB while being Indian
    TenantContext.setTenant(region);
}

// ✅ Extract from secure source
@GetMapping("/users/{userId}")
public UserDTO getUser(@PathVariable String userId) {
    // Extract from JWT token (verified signature)
    String region = SecurityContextHolder.getContext()
                       .getAuthentication()
                       .getPrincipal()
                       .getRegion();
    TenantContext.setTenant(region);
}
```

### 2. **Validate Tenant Membership**
```java
@Service
public class UserService {
    
    @Autowired
    private UserRepository userRepository;
    
    public UserDTO getUser(String userId) {
        String currentTenant = TenantContext.getTenant();
        
        // Verify user belongs to this tenant
        User user = userRepository.findById(userId);
        if (!user.getRegion().equals(currentTenant)) {
            throw new UnauthorizedException(
                "User does not belong to this region"
            );
        }
        return mapToDTO(user);
    }
}
```

## 📊 Trade-offs & When to Use

### ✅ Pros
- **Data Residency Compliance** - Keep data in specific regions (GDPR, India data localization)
- **Latency Optimization** - Users connect to nearest database
- **Multi-Tenancy** - Perfect for SaaS with tenant-specific databases
- **Scalability** - Each database scaled independently

### ❌ Cons
- **No Cross-Region Joins** - Complex queries across regions fail
- **Testing Complexity** - Need multiple test databases
- **Transaction Coordination** - Distributed transactions are hard
- **Operational Overhead** - Monitor multiple databases

## 🎯 Alternative Approaches

### 1. **Hibernate Multi-Tenancy** (For single schema, multiple tenants)
```
Use if: Many small tenants, cost optimization
Don't use if: Separate managed databases
```

### 2. **Database Proxy** (Sharding Proxy)
```
ProxySQL / Apache ShardingSphere
Use if: Transparent routing needed
Don't use if: Non-standard SQL
```

### 3. **Dual Write Pattern** (Eventual Consistency)
```
Write to all, read from local
Use if: Can tolerate replication lag
Don't use if: Strong consistency required
```

## 🧪 Testing Strategy

### 1. **Unit Tests** (Mock DataSource)
```java
@Test
public void testIndiaUserFetchesFromIndiaDB() {
    TenantContext.setTenant("INDIA");
    
    User user = userRepository.findById(1L);
    
    assertEquals("India", user.getRegion());
    TenantContext.clear();
}
```

### 2. **Integration Tests** (Embedded databases)
```java
@SpringBootTest(
    properties = {
        "spring.datasource.india.url=jdbc:h2:mem:india",
        "spring.datasource.us.url=jdbc:h2:mem:us"
    }
)
public class DatabaseRoutingIntegrationTest {
    // Test against real Spring context
}
```

### 3. **Contract Tests** (Verify DB schemas match)
```
Both databses must have identical schemas
Use schema migration tools to keep in sync
```

## 🚦 Common Pitfalls & Solutions

| Pitfall | Cause | Solution |
|---------|-------|----------|
| **Tenant not set** | Forgot to set in interceptor | Use `@Aspect` for logging |
| **Context leakage** | Using thread pool without cleanup | Always call `TenantContext.clear()` |
| **Wrong datasource selected** | Null TenantContext | Set default datasource |
| **Connection pool exhaustion** | Too many concurrent requests | Increase pool size per region |
| **Data inconsistency** | Different schema versions | Use schema versioning |

## 📚 External Resources

- **Spring AbstractRoutingDataSource**: https://docs.spring.io/spring-framework/reference/data-access/jdbc/core.html
- **Liquibase Multi-Tenancy**: https://docs.liquibase.com/
- **GDPR Data Residency**: https://gdpr-info.eu/
- **OWASP Multi-Tenancy Security**: https://owasp.org/www-community/attacks/Insecure_Direct_Object_References

## 📋 Interview Checklist

When answering this question in interviews:

- ✅ Start with the **problem**: Multiple regions, data residency
- ✅ Draw the **architecture** with interceptor → context → routing DS
- ✅ Explain **ThreadLocal** for context isolation
- ✅ Show **code** for each component
- ✅ Discuss **security** (prevent tenant switching attacks)
- ✅ Mention **operational** concerns (monitoring, schema sync)
- ✅ Compare with **alternatives** (Hibernate multi-tenancy, proxies)
- ✅ Ask **clarifying questions**: Scale? GDPR? Cross-region joins?

