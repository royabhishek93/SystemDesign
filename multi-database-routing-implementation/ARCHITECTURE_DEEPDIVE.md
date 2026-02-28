# Architecture Deep Dive

## System Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                        Client Applications                           │
│  (Web App, Mobile App, Microservice A, Microservice B)              │
└────────────────────────────┬────────────────────────────────────────┘
                             │
                    HTTP Request + Headers
                    (X-Region: INDIA/US/EU)
                             │
          ┌──────────────────▼──────────────────┐
          │   Spring Boot Application Server     │
          │     (Port 8080)                      │
          └──────────────────┬──────────────────┘
                             │
       ┌─────────────────────▼─────────────────────┐
       │                                             │
       │  ┌──────────────────────────────────────┐  │
       │  │ TenantInterceptor                    │  │
       │  │ - Extract region from headers       │  │
       │  │ - Set TenantContext                 │  │
       │  │ - Clear after response              │  │
       │  └────────────┬─────────────────────────┘  │
       │               │                             │
       │  ┌────────────▼──────────────────────────┐ │
       │  │ REST Controller                       │ │
       │  │ @GetMapping("/api/users/{id}")        │ │
       │  │ @PostMapping("/api/users")            │ │
       │  │ @DeleteMapping("/api/users/{id}")     │ │
       │  └────────────┬──────────────────────────┘ │
       │               │                             │
       │  ┌────────────▼──────────────────────────┐ │
       │  │ Service Layer (UserService)           │ │
       │  │ - Business logic                      │ │
       │  │ - Security checks                     │ │
       │  │ - Verify region matches               │ │
       │  └────────────┬──────────────────────────┘ │
       │               │                             │
       │  ┌────────────▼──────────────────────────┐ │
       │  │ Repository Layer (JPA)                │ │
       │  │ - Data access                         │ │
       │  └────────────┬──────────────────────────┘ │
       │               │                             │
       │  ┌────────────▼──────────────────────────┐ │
       │  │ DynamicRoutingDataSource              │ │
       │  │ - determineCurrentLookupKey()         │ │
       │  │ - Read TenantContext                  │ │
       │  │ - Route to correct database           │ │
       │  └────────────┬──────────────────────────┘ │
       │               │                             │
       └───────────────┼─────────────────────────────┘
                       │
        ┌──────────────┼──────────────┐
        │              │              │
   ┌────▼───┐  ┌──────▼─────┐  ┌────▼──────┐
   │ INDIA  │  │    US      │  │    EU     │
   │ MySQL  │  │   MySQL    │  │  MySQL    │
   │        │  │            │  │           │
   │ 3306   │  │   3307     │  │  3308     │
   └────────┘  └────────────┘  └───────────┘
   
   Indian Users:     US Users:          EU Users:
   - Rahul Kumar     - John Smith       - Hans Mueller
   - Priya Sharma    - Sarah Johnson    - Marie Dubois
   - Amit Patel      - Mike Wilson      - Klaus Weber
```

## Data Flow: Creating a User in INDIA

```
Step 1: HTTP Request
════════════════════════════════════════════════════════
POST /api/users
Headers:
  X-Region: INDIA
  Content-Type: application/json

Body:
{
  "email": "rahul@example.com",
  "phone": "+919876543210",
  "firstName": "Rahul",
  "lastName": "Kumar",
  "city": "Bangalore",
  "address": "123 Tech Park"
}

Step 2: TenantInterceptor.preHandle()
════════════════════════════════════════════════════════
extractTenantFromRequest(request)
  → Reads X-Region header
  → Returns "INDIA"

TenantContext.setTenant("INDIA")
  → Stores in ThreadLocal<String>
  → Available to current thread

Step 3: UserController.createUser()
════════════════════════════════════════════════════════
@PostMapping
public ResponseEntity<UserDTO> createUser(@RequestBody UserDTO userDTO) {
    UserDTO created = userService.createUser(userDTO);
    return ResponseEntity.status(HttpStatus.CREATED).body(created);
}

Step 4: UserService.createUser()
════════════════════════════════════════════════════════
// Get current tenant from ThreadLocal
String currentTenant = TenantContext.getTenant(); // "INDIA"

// Create User entity with region set
User user = User.builder()
    .email("rahul@example.com")
    .firstName("Rahul")
    .lastName("Kumar")
    .region("INDIA")  // ← IMPORTANT: Set region
    .city("Bangalore")
    .build();

// Save to database
User saved = userRepository.save(user);

Step 5: UserRepository.save() → Hibernate
════════════════════════════════════════════════════════
// Hibernate generates INSERT SQL
INSERT INTO users (email, first_name, last_name, region, city, ...)
VALUES ('rahul@example.com', 'Rahul', 'Kumar', 'INDIA', 'Bangalore', ...)

Step 6: DynamicRoutingDataSource Routing
════════════════════════════════════════════════════════
DynamicRoutingDataSource.determineCurrentLookupKey()
{
    String tenant = TenantContext.getTenant(); // "INDIA"
    System.out.println("🔀 Routing to datasource: INDIA");
    return tenant;
}

// Look up in targetDataSources map
targetDataSources.get("INDIA") 
    → Returns indiaDataSource (jdbc:mysql://india-db:3306/uber_india)

// Execute INSERT on India database
Connection conn = indiaDataSource.getConnection();
conn.executeUpdate(insertSQL);

Step 7: Database Execution
════════════════════════════════════════════════════════
India MySQL Server (Port 3306):
  Database: uber_india
  
  users table:
  ┌─────┬──────────────────────┬───────────────┬────────┬────────────┐
  │ id  │ email                │ first_name    │ region │ city       │
  ├─────┼──────────────────────┼───────────────┼────────┼────────────┤
  │ 1   │ rahul@example.com    │ Rahul         │ INDIA  │ Bangalore  │
  └─────┴──────────────────────┴───────────────┴────────┴────────────┘

Step 8: Response Sent
════════════════════════════════════════════════════════
HTTP 201 Created
{
  "id": 1,
  "email": "rahul@example.com",
  "firstName": "Rahul",
  "lastName": "Kumar",
  "region": "INDIA",
  "city": "Bangalore",
  ...
}

Step 9: TenantInterceptor.afterCompletion()
════════════════════════════════════════════════════════
TenantContext.clear()
  → Removes "INDIA" from ThreadLocal
  → Prevents context leakage to next request
  → Connection returned to pool
```

## Security: Cross-Tenant Access Prevention

```
Scenario: US Request tries to access INDIA User

Step 1: HTTP Request
════════════════════════════════════════════════════════
GET /api/users/1
Headers: X-Region: US

Step 2: TenantInterceptor Sets Context
════════════════════════════════════════════════════════
TenantContext.setTenant("US")

Step 3: UserController Receives
════════════════════════════════════════════════════════
@GetMapping("/{id}")
public UserDTO getUser(@PathVariable Long id) {
    return userService.getUserById(id);
}

Step 4: Query Routed to US Database
════════════════════════════════════════════════════════
DynamicRoutingDataSource.determineCurrentLookupKey()
    → Returns "US"
    → Selects usDataSource
    
SELECT * FROM users WHERE id = 1;

// But wait! User ID 1 doesn't exist in US database
// (It exists in INDIA database)
// Query returns nothing found

Step 5: Exception Thrown
════════════════════════════════════════════════════════
userRepository.findById(1)
    → Optional.empty()
    
if (!optional.isPresent()) {
    throw new RuntimeException("User not found");
}

// But if User ID 1 ALSO existed in US database with different data:

Step 6: Service Layer Verification
════════════════════════════════════════════════════════
User user = userRepository.findById(1); // From US database
String currentTenant = TenantContext.getTenant(); // "US"

// CRITICAL SECURITY CHECK
if (!user.getRegion().equals(currentTenant)) {
    // user.region = "INDIA" (wrong!)
    // currentTenant = "US" (current)
    
    throw new UnauthorizedException(
        "User does not belong to your region: INDIA"
    );
}

Step 7: User Blocked
════════════════════════════════════════════════════════
HTTP 403 Forbidden
{
  "error": "User does not belong to your region: INDIA"
}
```

## Tenant Context Lifecycle

```
Request Enters
    │
    ▼
TenantInterceptor.preHandle()
    │
    ├── Extract tenant from:
    │   ├── X-Region header
    │   ├── X-Tenant-Id header
    │   ├── JWT claim
    │   ├── URL path parameter
    │   └── Query parameter
    │
    └── TenantContext.setTenant(tenant)
        └── Stored in ThreadLocal<String>
    
    ▼
Request Processed
    │
    ├── Controller
    ├── Service
    ├── Repository
    └── Database Query
        └── DynamicRoutingDataSource reads TenantContext
            └── Routes to correct database
    
    ▼
TenantInterceptor.afterCompletion()
    │
    ├── Log completion
    │
    └── TenantContext.clear()
        └── Remove from ThreadLocal
            └── Prevent leakage to next request

Response Sent
```

## Connection Pool Management

```
Spring Boot Connection Pools
════════════════════════════════════════════════════════

┌─────────────────────────────────────────┐
│ HikariCP - India DataSource             │
│ Maximum Pool Size: 20                   │
│                                         │
│ ┌────┐ ┌────┐ ┌────┐ ┌────┐ ┌────┐   │
│ │ ✓  │ │ ✓  │ │ ✓  │ │ ✓  │ │ ✗  │   │
│ └────┘ └────┘ └────┘ └────┘ └────┘   │
└─────────────────────────────────────────┘
  active  active  active  active  idle
  (4/20 active, 1 waiting)

┌─────────────────────────────────────────┐
│ HikariCP - US DataSource                │
│ Maximum Pool Size: 20                   │
│                                         │
│ ┌────┐ ┌────┐ ┌────┐ ┌────┐           │
│ │ ✓  │ │ ✓  │ │ ✓  │ │ ✗  │           │
│ └────┘ └────┘ └────┘ └────┘           │
└─────────────────────────────────────────┘
  active  active  active  idle
  (3/20 active)

Important:
════════════════════════════════════════════════════════
⚠️  If TenantContext.clear() is NOT called:
    - Connection stays "checked out"
    - Returned to pool for NEXT request
    - But TenantContext is EMPTY
    - Next request gets NULL TenantContext
    - Routing fails or uses default

✅ Always call TenantContext.clear():
   - In TenantInterceptor.afterCompletion()
   - Or in @ControllerAdvice error handlers
   - Or with try-finally block
```

## Multi-Tenancy vs Data Isolation Patterns

```
PATTERN 1: Separate Databases (This Implementation)
════════════════════════════════════════════════════════
┌──────────────┐  ┌──────────────┐  ┌──────────────┐
│  INDIA DB    │  │    US DB     │  │    EU DB     │
│              │  │              │  │              │
│ users        │  │ users        │  │ users        │
│ rides        │  │ rides        │  │ rides        │
│ payments     │  │ payments     │  │ payments     │
└──────────────┘  └──────────────┘  └──────────────┘

Pros:
  ✅ Complete data isolation
  ✅ Regional compliance (GDPR, India Act)
  ✅ Independent scaling
  ✅ Database catastrophe only affects one region

Cons:
  ❌ No cross-region joins
  ❌ Operational overhead (monitor 3 DBs)
  ❌ Schema sync required
  ❌ Distributed transactions complex


PATTERN 2: Single Database, Row-Level Isolation
════════════════════════════════════════════════════════
┌────────────────────────┐
│  Shared Database       │
│                        │
│ users:                 │
│ ┌─────┬────────┬──────┐│
│ │ id  │ name   │region││
│ ├─────┼────────┼──────┤│
│ │ 1   │ Rahul  │INDIA ││ ← Filter: region = INDIA
│ │ 2   │ Priya  │INDIA ││ ← Filter: region = INDIA
│ │ 3   │ John   │ US   ││ ← Filter: region = US
│ │ 4   │ Sarah  │ US   ││ ← Filter: region = US
│ └─────┴────────┴──────┘│
└────────────────────────┘

Pros:
  ✅ Single database to manage
  ✅ Cross-region joins possible
  ✅ Lower cost
  ✅ Simple disaster recovery

Cons:
  ❌ Data not geographically isolated
  ❌ Regulatory risk
  ❌ Harder to scale independently
  ❌ Accidental data access risk


PATTERN 3: Sharding (Hybrid)
════════════════════════════════════════════════════════
┌─────────────────┐  ┌─────────────────┐
│  Shard 1        │  │  Shard 2        │
│  (US Customers) │  │(India Customers)│
│                 │  │                 │
│ users (A-M)     │  │ users (N-Z)     │
│ rides (A-M)     │  │ rides (N-Z)     │
└─────────────────┘  └─────────────────┘

Uses: Hash-based routing, range-based routing, directory-based

This Implementation: Tenant-based routing (not sharding)
```

## Interview Talking Points

### "Walk me through how a user creation works"
```
✅ 1. User sends POST request with X-Region header
✅ 2. Interceptor extracts region and sets TenantContext
✅ 3. Controller receives request
✅ 4. Service creates User entity with region field
✅ 5. Repository.save() triggers JPA
✅ 6. Hibernate generates INSERT  SQL
✅ 7. DynamicRoutingDataSource intercepts
✅ 8. determineCurrentLookupKey() reads TenantContext
✅ 9. Query routed to correct regional database
✅ 10. User inserted into INDIA or US database only
✅ 11. Service layer returns DTO
✅ 12. Response sent to client
✅ 13. Interceptor calls TenantContext.clear()
✅ 14. Next request starts fresh
```

### "How do you prevent cross-customer access?"
```
✅ Layer 1: Extract from secure source (JWT, not user param)
✅ Layer 2: DynamicRoutingDataSource routes to correct DB
           (user from wrong region won't exist there)
✅ Layer 3: Service verifies region matches
           (if somehow querying wrong DB)
✅ Layer 4: TenantContext never manually set by user
✅ Layer 5: Logging/monitoring for suspicious access
```

### "What if someone tampers with X-Region header?"
```
✅ If reading from user parameter:
   ❌ VULNERABLE: User can set X-Region: INDIA to access India data

✅ If reading from JWT token:
   ✅ SECURE: JWT signature verified, cannot tamper
   ✅ User can only access their own region

Implementation:
// Extract from JWT (secure)
Authentication auth = SecurityContextHolder.getContext()
    .getAuthentication();
String region = auth.getPrincipal().getRegion();
TenantContext.setTenant(region);

// NOT: 
// String region = request.getHeader("X-Region"); // ❌ Vulnerable
```

