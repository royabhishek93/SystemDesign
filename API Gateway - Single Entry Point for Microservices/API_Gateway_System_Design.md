# API Gateway - Single Entry Point for Microservices

## 1. What is an API Gateway?

**API Gateway** is a server that acts as a single entry point for all client requests to backend microservices. It routes requests, handles authentication, rate limiting, and more.

### Why API Gateway is Needed:

- ✅ Single entry point for all APIs
- ✅ Request routing to microservices
- ✅ Authentication & authorization
- ✅ Rate limiting & throttling
- ✅ Request/response transformation
- ✅ Load balancing
- ✅ Caching
- ✅ Monitoring & logging
- ✅ Protocol translation (REST → gRPC)

### Visual: Without vs With API Gateway

```
┌────────────────────────────────────────────────────────────────────────┐
│                WITHOUT API GATEWAY (MESSY)                             │
└────────────────────────────────────────────────────────────────────────┘

Clients directly call multiple services:

┌─────────────┐
│   Mobile    │
│   App       │
└──┬──┬──┬──┬─┘
   │  │  │  │
   │  │  │  └─────────→ Auth Service (auth.api.com)
   │  │  └────────────→ Payment Service (payment.api.com)
   │  └───────────────→ Order Service (order.api.com)
   └──────────────────→ User Service (user.api.com)

Problems:
❌ Client needs to know all service URLs
❌ Different auth for each service
❌ No rate limiting
❌ CORS issues
❌ Tight coupling
❌ Hard to change service locations
❌ Security concerns (services exposed)
❌ No central monitoring


WITH API GATEWAY (CLEAN)
─────────────────────────

All clients call single gateway:

┌─────────────┐
│   Mobile    │
│   App       │
└──────┬──────┘
       │
       │ All requests: api.example.com
       ↓
┌──────────────────────────────────────┐
│        API GATEWAY                   │
│        (api.example.com)             │
│                                      │
│  • Authentication                    │
│  • Rate limiting                     │
│  • Request routing                   │
│  • Load balancing                    │
│  • Caching                           │
│  • Monitoring                        │
└────┬────────┬────────┬────────┬──────┘
     │        │        │        │
     │        │        │        │
     ↓        ↓        ↓        ↓
┌─────────┐ ┌────────┐ ┌───────┐ ┌─────────┐
│  Auth   │ │Payment │ │ Order │ │  User   │
│ Service │ │Service │ │Service│ │ Service │
│         │ │        │ │       │ │         │
│ Private │ │Private │ │Private│ │ Private │
│ Network │ │Network │ │Network│ │ Network │
└─────────┘ └────────┘ └───────┘ └─────────┘

Benefits:
✅ Single endpoint for clients
✅ Centralized authentication
✅ Centralized rate limiting
✅ Services hidden (private network)
✅ Easy to add/remove services
✅ Client doesn't know internal architecture
✅ Central monitoring & logging
```

## 2. API Gateway Architecture

### Visual: Complete API Gateway System

```
┌────────────────────────────────────────────────────────────────────────┐
│                    COMPLETE API GATEWAY ARCHITECTURE                   │
└────────────────────────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────────────┐
│                      CLIENT LAYER                            │
│                                                              │
│  📱 Mobile    💻 Web     🖥️ Desktop    🤖 IoT    🔌 3rd Party│
└────┬──────────┬──────────┬──────────┬──────────┬───────────┘
     │          │          │          │          │
     │ HTTPS    │ HTTPS    │ HTTPS    │ HTTPS    │ HTTPS
     │          │          │          │          │
     └──────────┴──────────┴──────────┴──────────┘
                         │
                         ↓
┌──────────────────────────────────────────────────────────────┐
│                   LOAD BALANCER                              │
│                   (Optional Layer)                           │
└──────────────────────────────────────────────────────────────┘
                         │
                         ↓
┌──────────────────────────────────────────────────────────────┐
│                   API GATEWAY CLUSTER                        │
│                                                              │
│  ┌────────────┐  ┌────────────┐  ┌────────────┐           │
│  │ Gateway 1  │  │ Gateway 2  │  │ Gateway 3  │           │
│  │            │  │            │  │            │           │
│  │ Stateless  │  │ Stateless  │  │ Stateless  │           │
│  └────────────┘  └────────────┘  └────────────┘           │
│                                                              │
│  Each gateway has:                                           │
│  ┌────────────────────────────────────────────────────────┐ │
│  │  1. REQUEST PROCESSING                                 │ │
│  │     • Parse request                                    │ │
│  │     • Validate headers                                 │ │
│  │     • Extract metadata                                 │ │
│  │                                                        │ │
│  │  2. AUTHENTICATION & AUTHORIZATION                     │ │
│  │     • Verify API key/JWT token                         │ │
│  │     • Check permissions                                │ │
│  │     • User identification                              │ │
│  │                                                        │ │
│  │  3. RATE LIMITING                                      │ │
│  │     • Check request quota                              │ │
│  │     • Throttle if exceeded                             │ │
│  │     • Return 429 if over limit                         │ │
│  │                                                        │ │
│  │  4. REQUEST TRANSFORMATION                             │ │
│  │     • Protocol conversion                              │ │
│  │     • Header manipulation                              │ │
│  │     • Request enrichment                               │ │
│  │                                                        │ │
│  │  5. ROUTING                                            │ │
│  │     • Match URL pattern                                │ │
│  │     • Load balance                                     │ │
│  │     • Service discovery                                │ │
│  │                                                        │ │
│  │  6. CACHING                                            │ │
│  │     • Check cache                                      │ │
│  │     • Return cached response                           │ │
│  │                                                        │ │
│  │  7. RESPONSE TRANSFORMATION                            │ │
│  │     • Format response                                  │ │
│  │     • Add headers                                      │ │
│  │     • Compress                                         │ │
│  │                                                        │ │
│  │  8. MONITORING & LOGGING                               │ │
│  │     • Log requests                                     │ │
│  │     • Metrics collection                               │ │
│  │     • Distributed tracing                              │ │
│  └────────────────────────────────────────────────────────┘ │
└──────────────────────────────────────────────────────────────┘
                         │
                         ↓
┌──────────────────────────────────────────────────────────────┐
│                   SUPPORTING SERVICES                        │
│                                                              │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐   │
│  │  Redis   │  │  Auth    │  │ Service  │  │Monitoring│   │
│  │  Cache   │  │  Service │  │Discovery │  │  System  │   │
│  │          │  │          │  │(Consul)  │  │(Prometheus)│  │
│  └──────────┘  └──────────┘  └──────────┘  └──────────┘   │
└──────────────────────────────────────────────────────────────┘
                         │
                         ↓
┌──────────────────────────────────────────────────────────────┐
│                   BACKEND MICROSERVICES                      │
│                   (Private Network)                          │
│                                                              │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐   │
│  │  User    │  │  Order   │  │ Payment  │  │ Inventory│   │
│  │ Service  │  │ Service  │  │ Service  │  │ Service  │   │
│  │ :8001    │  │ :8002    │  │ :8003    │  │ :8004    │   │
│  └──────────┘  └──────────┘  └──────────┘  └──────────┘   │
│                                                              │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐   │
│  │ Shipping │  │  Email   │  │Analytics │  │ Catalog  │   │
│  │ Service  │  │ Service  │  │ Service  │  │ Service  │   │
│  │ :8005    │  │ :8006    │  │ :8007    │  │ :8008    │   │
│  └──────────┘  └──────────┘  └──────────┘  └──────────┘   │
└──────────────────────────────────────────────────────────────┘
```

## 3. Request Flow Through API Gateway

### Visual: Step-by-Step Request Processing

```
┌────────────────────────────────────────────────────────────────────────┐
│                    REQUEST FLOW (DETAILED)                             │
└────────────────────────────────────────────────────────────────────────┘

Example: GET /api/v1/users/123

STEP 1: Client Request
──────────────────────
┌─────────────────────────────────────┐
│  Mobile App                         │
│                                     │
│  GET /api/v1/users/123              │
│  Host: api.example.com              │
│  Authorization: Bearer eyJhbGc...   │
│  X-API-Key: abc123                  │
└────────┬────────────────────────────┘
         │
         ↓

STEP 2: Load Balancer
─────────────────────
┌─────────────────────────────────────┐
│  Route to one of 3 gateway servers  │
│  → Gateway Server 2 selected        │
└────────┬────────────────────────────┘
         │
         ↓

STEP 3: Authentication
──────────────────────
┌─────────────────────────────────────┐
│  API Gateway                        │
│                                     │
│  1. Extract token from header       │
│     Token: eyJhbGc...                │
│                                     │
│  2. Verify JWT signature            │
│     ✅ Valid                         │
│                                     │
│  3. Decode payload                  │
│     userId: 123                     │
│     role: "admin"                   │
│     exp: 1680000000                 │
│                                     │
│  4. Check expiration                │
│     ✅ Not expired                   │
└────────┬────────────────────────────┘
         │
         ↓

STEP 4: Authorization
─────────────────────
┌─────────────────────────────────────┐
│  Check permissions                  │
│                                     │
│  User: admin (from token)           │
│  Action: GET /users/123             │
│  Required permission: read:users    │
│                                     │
│  ✅ Admin has permission            │
└────────┬────────────────────────────┘
         │
         ↓

STEP 5: Rate Limiting
─────────────────────
┌─────────────────────────────────────┐
│  Check rate limit (Redis)           │
│                                     │
│  Key: rate_limit:user:123           │
│  Limit: 1000 requests/hour          │
│  Current: 567                       │
│                                     │
│  567 < 1000 ✅ Allowed              │
│  Increment counter: 568             │
└────────┬────────────────────────────┘
         │
         ↓

STEP 6: Request Validation
──────────────────────────
┌─────────────────────────────────────┐
│  Validate request                   │
│                                     │
│  • URL format: ✅                   │
│  • Method: GET ✅                   │
│  • Headers: ✅                      │
│  • Query params: ✅                 │
└────────┬────────────────────────────┘
         │
         ↓

STEP 7: Caching Check
─────────────────────
┌─────────────────────────────────────┐
│  Check cache (Redis)                │
│                                     │
│  Key: users:123                     │
│  Result: MISS ❌                    │
│                                     │
│  Need to fetch from service         │
└────────┬────────────────────────────┘
         │
         ↓

STEP 8: Service Discovery
─────────────────────────
┌─────────────────────────────────────┐
│  Find User Service                  │
│                                     │
│  Query Consul:                      │
│  • Service: user-service            │
│  • Healthy instances: 3             │
│  • Select: user-service-2           │
│  • IP: 10.0.1.25:8001              │
└────────┬────────────────────────────┘
         │
         ↓

STEP 9: Request Transformation
──────────────────────────────
┌─────────────────────────────────────┐
│  Transform request                  │
│                                     │
│  Original: GET /api/v1/users/123    │
│  Internal: GET /users/123           │
│                                     │
│  Add headers:                       │
│  • X-User-Id: 123                   │
│  • X-User-Role: admin               │
│  • X-Request-Id: req-uuid-123       │
│  • X-Gateway: gateway-2             │
└────────┬────────────────────────────┘
         │
         ↓

STEP 10: Forward to Service
───────────────────────────
┌─────────────────────────────────────┐
│  Forward to User Service            │
│                                     │
│  GET http://10.0.1.25:8001/users/123│
│  Headers: {enriched headers}        │
└────────┬────────────────────────────┘
         │
         ↓

STEP 11: Service Response
─────────────────────────
┌─────────────────────────────────────┐
│  User Service Response              │
│                                     │
│  Status: 200 OK                     │
│  Body: {                            │
│    "id": 123,                       │
│    "name": "John Doe",              │
│    "email": "john@example.com"      │
│  }                                  │
│  Time: 45ms                         │
└────────┬────────────────────────────┘
         │
         ↓

STEP 12: Response Caching
─────────────────────────
┌─────────────────────────────────────┐
│  Store in cache (Redis)             │
│                                     │
│  Key: users:123                     │
│  Value: {response}                  │
│  TTL: 300 seconds (5 minutes)       │
│                                     │
│  Next request will be instant! ✅   │
└────────┬────────────────────────────┘
         │
         ↓

STEP 13: Response Transformation
────────────────────────────────
┌─────────────────────────────────────┐
│  Transform response                 │
│                                     │
│  Add headers:                       │
│  • X-Cache: MISS                    │
│  • X-Response-Time: 45ms            │
│  • X-RateLimit-Remaining: 432       │
│  • X-Request-Id: req-uuid-123       │
│                                     │
│  Compress: gzip                     │
└────────┬────────────────────────────┘
         │
         ↓

STEP 14: Logging & Monitoring
─────────────────────────────
┌─────────────────────────────────────┐
│  Log request                        │
│                                     │
│  • Timestamp: 2024-03-15T10:30:00   │
│  • Method: GET                      │
│  • Path: /api/v1/users/123          │
│  • User: 123                        │
│  • Status: 200                      │
│  • Latency: 45ms                    │
│  • Service: user-service            │
│                                     │
│  Send metrics to Prometheus         │
└────────┬────────────────────────────┘
         │
         ↓

STEP 15: Return to Client
─────────────────────────
┌─────────────────────────────────────┐
│  Response                           │
│                                     │
│  Status: 200 OK                     │
│  Headers: {transformed headers}     │
│  Body: {user data}                  │
│                                     │
│  Total time: 50ms ✅                │
└─────────────────────────────────────┘


TIMELINE
────────

T0:   Client sends request
T1:   Gateway receives (network: 5ms)
T2:   Auth check (JWT verify: 2ms)
T3:   Rate limit check (Redis: 2ms)
T4:   Validation (1ms)
T5:   Cache check (Redis: 2ms) → MISS
T6:   Service discovery (Consul: 3ms)
T7:   Forward to service (network: 5ms)
T8:   Service processes (30ms)
T9:   Response received (network: 5ms)
T10:  Cache response (Redis: 2ms)
T11:  Transform & log (3ms)
T12:  Return to client (network: 5ms)
───────────────────────────────────────
Total: 65ms
```

## 4. Key Features of API Gateway

### Visual: Core Capabilities

```
┌────────────────────────────────────────────────────────────────────────┐
│                    API GATEWAY KEY FEATURES                            │
└────────────────────────────────────────────────────────────────────────┘

FEATURE 1: REQUEST ROUTING
──────────────────────────

Path-based routing:
┌─────────────────────────────────────┐
│  /api/users/*    → User Service     │
│  /api/orders/*   → Order Service    │
│  /api/payments/* → Payment Service  │
│  /api/products/* → Product Service  │
└─────────────────────────────────────┘

Header-based routing (A/B testing):
┌─────────────────────────────────────┐
│  X-Version: v1   → Old Service      │
│  X-Version: v2   → New Service      │
└─────────────────────────────────────┘

User-based routing (Canary deployment):
┌─────────────────────────────────────┐
│  10% of users → New version         │
│  90% of users → Old version         │
└─────────────────────────────────────┘


FEATURE 2: AUTHENTICATION METHODS
──────────────────────────────────

API Key:
GET /api/users
X-API-Key: abc123def456

JWT Bearer Token:
GET /api/users
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...

OAuth 2.0:
GET /api/users
Authorization: Bearer <access_token>

Mutual TLS (mTLS):
Client certificate + Server certificate


FEATURE 3: RATE LIMITING STRATEGIES
────────────────────────────────────

Per-User:
┌─────────────────────────────────────┐
│  User 123: 1000 requests/hour       │
│  User 456: 1000 requests/hour       │
└─────────────────────────────────────┘

Per-API-Key:
┌─────────────────────────────────────┐
│  Key abc123: 10,000 requests/hour   │
│  Key def456: 5,000 requests/hour    │
└─────────────────────────────────────┘

Tiered:
┌─────────────────────────────────────┐
│  Free tier: 100 requests/hour       │
│  Basic tier: 1,000 requests/hour    │
│  Pro tier: 10,000 requests/hour     │
│  Enterprise: Unlimited              │
└─────────────────────────────────────┘


FEATURE 4: REQUEST/RESPONSE TRANSFORMATION
───────────────────────────────────────────

Request transformation:
Client request:
{
  "userName": "john",
  "userAge": 30
}

Gateway transforms to:
{
  "user": {
    "name": "john",
    "age": 30
  },
  "metadata": {
    "requestId": "req-123",
    "timestamp": "2024-03-15T10:30:00Z"
  }
}

Response aggregation (Fan-out/Fan-in):
┌─────────────────────────────────────┐
│  Client requests: /api/dashboard    │
└────────┬────────────────────────────┘
         │
         ↓
┌─────────────────────────────────────┐
│  Gateway fans out to 3 services:    │
│  ┌─────────────┐                    │
│  │ 1. User     │                    │
│  │    Service  │                    │
│  └─────────────┘                    │
│  ┌─────────────┐                    │
│  │ 2. Order    │                    │
│  │    Service  │                    │
│  └─────────────┘                    │
│  ┌─────────────┐                    │
│  │ 3. Payment  │                    │
│  │    Service  │                    │
│  └─────────────┘                    │
└────────┬────────────────────────────┘
         │
         ↓
┌─────────────────────────────────────┐
│  Gateway aggregates responses:      │
│  {                                  │
│    "user": {...},                   │
│    "orders": [...],                 │
│    "payments": [...]                │
│  }                                  │
└─────────────────────────────────────┘


FEATURE 5: CIRCUIT BREAKER
──────────────────────────

Protects against cascading failures:

┌────────────────────────────────────────────┐
│  State Machine:                            │
│                                            │
│  CLOSED (Normal)                           │
│  → All requests pass through               │
│  → If failures exceed threshold:           │
│     → Move to OPEN                         │
│                                            │
│  OPEN (Service failing)                    │
│  → Reject requests immediately             │
│  → Return cached response or error         │
│  → After timeout:                          │
│     → Move to HALF-OPEN                    │
│                                            │
│  HALF-OPEN (Testing)                       │
│  → Allow few test requests                 │
│  → If successful:                          │
│     → Move to CLOSED                       │
│  → If fail:                                │
│     → Move to OPEN                         │
└────────────────────────────────────────────┘

Example:
Time 0s: CLOSED (normal operation)
Time 10s: Payment service starts failing
Time 11s: 10 failures detected
Time 11s: Circuit OPENS (reject requests)
Time 41s: Circuit HALF-OPEN (test)
Time 42s: Test request succeeds
Time 42s: Circuit CLOSED (back to normal)


FEATURE 6: PROTOCOL TRANSLATION
────────────────────────────────

REST to gRPC:
┌─────────────────────────────────────┐
│  Client: HTTP/REST                  │
│  GET /api/users/123                 │
└────────┬────────────────────────────┘
         │
         ↓
┌─────────────────────────────────────┐
│  Gateway translates                 │
└────────┬────────────────────────────┘
         │
         ↓
┌─────────────────────────────────────┐
│  Service: gRPC                      │
│  UserService.GetUser(id: 123)       │
└─────────────────────────────────────┘

GraphQL to REST:
Client sends GraphQL query
→ Gateway breaks into multiple REST calls
→ Aggregates responses
→ Returns GraphQL response
```

## 5. API Gateway Patterns

### Visual: Common Patterns

```
┌────────────────────────────────────────────────────────────────────────┐
│                    API GATEWAY PATTERNS                                │
└────────────────────────────────────────────────────────────────────────┘

PATTERN 1: BACKENDS FOR FRONTENDS (BFF)
────────────────────────────────────────

Different gateways for different clients:

┌──────────┐      ┌──────────────────────┐
│  Mobile  │─────→│  Mobile API Gateway  │
│   App    │      │  • Optimized payloads │
└──────────┘      │  • Image compression  │
                  │  • Less data         │
                  └───────────┬──────────┘
                              │
┌──────────┐      ┌──────────────────────┐
│   Web    │─────→│  Web API Gateway     │
│  Browser │      │  • Full responses     │
└──────────┘      │  • More features      │
                  └───────────┬──────────┘
                              │
┌──────────┐      ┌──────────────────────┐
│   IoT    │─────→│  IoT API Gateway     │
│  Device  │      │  • Minimal payloads   │
└──────────┘      │  • MQTT support       │
                  └───────────┬──────────┘
                              │
                              ↓
                  ┌───────────────────────┐
                  │   Backend Services    │
                  └───────────────────────┘


PATTERN 2: API COMPOSITION
──────────────────────────

Gateway aggregates multiple service calls:

Client request: GET /api/user-dashboard
         │
         ↓
┌─────────────────────────────────────┐
│  API Gateway                        │
│                                     │
│  Parallel calls:                    │
│  ┌─────────────────┐                │
│  │ 1. GET /users/1 │ → User details │
│  │ 2. GET /orders  │ → Order list   │
│  │ 3. GET /wallet  │ → Balance      │
│  └─────────────────┘                │
│                                     │
│  Wait for all responses             │
│  Aggregate into single response     │
└────────┬────────────────────────────┘
         │
         ↓
Client receives:
{
  "user": {...},
  "orders": [...],
  "wallet": {...}
}


PATTERN 3: AUTHENTICATION GATEWAY
──────────────────────────────────

Gateway handles all authentication:

┌──────────┐
│  Client  │
└────┬─────┘
     │
     │ POST /login
     │ {username, password}
     ↓
┌─────────────────────────────────────┐
│  Authentication Gateway             │
│                                     │
│  1. Validate credentials            │
│  2. Generate JWT token              │
│  3. Return token                    │
└────┬────────────────────────────────┘
     │
     │ Response: {token: "eyJhbGc..."}
     ↓
┌──────────┐
│  Client  │
│  Stores  │
│  token   │
└────┬─────┘
     │
     │ Subsequent requests:
     │ GET /api/orders
     │ Authorization: Bearer eyJhbGc...
     ↓
┌─────────────────────────────────────┐
│  API Gateway                        │
│                                     │
│  1. Verify JWT token                │
│  2. Extract user info               │
│  3. Forward to service              │
│     (with user context)             │
└─────────────────────────────────────┘


PATTERN 4: RATE LIMITING GATEWAY
─────────────────────────────────

Gateway enforces rate limits:

┌──────────┐
│  Client  │
│  (Free)  │
└────┬─────┘
     │
     │ 100 requests/hour limit
     ↓
┌─────────────────────────────────────┐
│  Rate Limiting Gateway              │
│                                     │
│  Check: requests_this_hour          │
│  • 99 requests: ✅ Allow            │
│  • 100 requests: ✅ Allow           │
│  • 101 requests: ❌ Reject (429)    │
│                                     │
│  Response:                          │
│  {                                  │
│    "error": "Rate limit exceeded",  │
│    "retry_after": 3600              │
│  }                                  │
└─────────────────────────────────────┘
```

## 6. Popular API Gateway Solutions

### Visual: Technology Comparison

```
┌────────────────────────────────────────────────────────────────────────┐
│                    API GATEWAY SOLUTIONS                               │
└────────────────────────────────────────────────────────────────────────┘

KONG
────
┌─────────────────────────────────────┐
│  • Type: Open-source + Enterprise   │
│  • Base: NGINX                      │
│  • Language: Lua                    │
│  • Features: Rich plugin ecosystem  │
│  • Performance: Very fast           │
│  • Scalability: Excellent           │
│                                     │
│  Best for:                          │
│  • Microservices                    │
│  • High traffic                     │
│  • Custom plugins needed            │
└─────────────────────────────────────┘

AWS API GATEWAY
───────────────
┌─────────────────────────────────────┐
│  • Type: Fully managed (AWS)        │
│  • Integration: AWS services        │
│  • Features: Complete               │
│  • Pricing: Pay-per-request         │
│  • Scalability: Auto-scaling        │
│                                     │
│  Best for:                          │
│  • AWS ecosystem                    │
│  • Serverless (Lambda)              │
│  • Quick setup                      │
└─────────────────────────────────────┘

NGINX
─────
┌─────────────────────────────────────┐
│  • Type: Open-source                │
│  • Lightweight: Yes                 │
│  • Performance: Very fast           │
│  • Flexibility: High                │
│  • Learning curve: Medium           │
│                                     │
│  Best for:                          │
│  • Simple routing                   │
│  • Load balancing                   │
│  • Custom configurations            │
└─────────────────────────────────────┘

APIGEE (Google)
───────────────
┌─────────────────────────────────────┐
│  • Type: Enterprise (Google Cloud)  │
│  • Features: Comprehensive          │
│  • Analytics: Advanced              │
│  • Developer portal: Excellent      │
│  • Pricing: Enterprise              │
│                                     │
│  Best for:                          │
│  • Large enterprises                │
│  • API monetization                 │
│  • Developer ecosystem              │
└─────────────────────────────────────┘

ZUUL (Netflix)
──────────────
┌─────────────────────────────────────┐
│  • Type: Open-source (Java)         │
│  • Spring integration: Excellent    │
│  • Features: Good                   │
│  • Learning curve: Medium           │
│  • Community: Spring Cloud          │
│                                     │
│  Best for:                          │
│  • Java/Spring applications         │
│  • Netflix OSS stack                │
│  • Microservices                    │
└─────────────────────────────────────┘

COMPARISON TABLE
────────────────

┌──────────┬────────┬──────────┬──────────┬────────┐
│ Feature  │  Kong  │   AWS    │   NGINX  │  Zuul  │
├──────────┼────────┼──────────┼──────────┼────────┤
│ Cost     │  Free/ │  Pay-per │   Free   │  Free  │
│          │  Paid  │  request │          │        │
├──────────┼────────┼──────────┼──────────┼────────┤
│ Perf     │   ⭐⭐⭐⭐⭐│   ⭐⭐⭐⭐ │   ⭐⭐⭐⭐⭐│   ⭐⭐⭐ │
├──────────┼────────┼──────────┼──────────┼────────┤
│ Features │   ⭐⭐⭐⭐⭐│   ⭐⭐⭐⭐⭐│   ⭐⭐⭐  │   ⭐⭐⭐⭐│
├──────────┼────────┼──────────┼──────────┼────────┤
│ Setup    │  Medium│   Easy   │  Medium  │ Medium │
├──────────┼────────┼──────────┼──────────┼────────┤
│ Scale    │Excellent│Excellent │   Good   │  Good  │
└──────────┴────────┴──────────┴──────────┴────────┘
```

## 7. System Design Interview Answer

### Short Answer (3-4 minutes):

> **API Gateway** is a server that acts as a single entry point for all client requests to backend microservices, handling routing, authentication, rate limiting, and more.
>
> **Core responsibilities**:
> 1. **Request routing**: Routes `/api/users/*` to User Service, `/api/orders/*` to Order Service
> 2. **Authentication & Authorization**: Verifies JWT tokens, checks permissions
> 3. **Rate limiting**: Enforces request quotas (e.g., 1000 requests/hour per user)
> 4. **Request/Response transformation**: Protocol conversion, header manipulation, response aggregation
> 5. **Caching**: Stores frequently accessed responses in Redis
> 6. **Load balancing**: Distributes requests across service instances
> 7. **Circuit breaking**: Prevents cascading failures by stopping requests to failing services
> 8. **Monitoring & Logging**: Centralized logging, metrics collection, distributed tracing
>
> **Request flow**: Client → Load Balancer → API Gateway (auth, rate limit, cache check, route) → Service Discovery → Backend Service → Response (cache, transform, log) → Client
>
> **Common patterns**:
> - **BFF (Backends for Frontends)**: Separate gateways for mobile, web, IoT optimized for each client
> - **API Composition**: Gateway aggregates multiple service calls into single response
> - **Authentication Gateway**: Handles all auth, issues JWT tokens, verifies on subsequent requests
>
> **Popular solutions**: Kong (NGINX-based, plugin ecosystem), AWS API Gateway (managed, serverless integration), NGINX (lightweight, fast), Apigee (enterprise, Google), Zuul (Java, Spring Cloud)
>
> **Benefits**: Simplified client code, centralized security, reduced coupling, easier monitoring, and ability to change backend services without affecting clients.
>
> **Challenges**: Single point of failure (mitigate with clustering), added latency (5-10ms overhead), and complexity in configuration management.

---

## Key Technologies:
- **Kong**: Most popular open-source gateway
- **AWS API Gateway**: Best for serverless/AWS
- **NGINX**: Lightweight, high-performance
- **Apigee**: Enterprise features
- **Zuul**: Java/Spring ecosystem
- **Redis**: Caching and rate limiting
- **Consul**: Service discovery
