# Microservices Architecture - Complete System Design

## What are Microservices?

**Microservices** is an architectural style where an application is built as a collection of **small, independent services** that communicate over the network. Each service is:
- **Independently deployable**
- **Loosely coupled**
- **Organized around business capabilities**
- **Owned by a small team**

---

## Monolithic vs Microservices Architecture

```
┌─────────────────────────────────────────────────────────────────────────┐
│                    MONOLITHIC ARCHITECTURE                               │
└─────────────────────────────────────────────────────────────────────────┘

                    ┌───────────────────────────────┐
User Request ──────▶│      Single Application       │
                    │                               │
                    │  ┌─────────────────────────┐  │
                    │  │    UI Layer             │  │
                    │  └─────────────────────────┘  │
                    │  ┌─────────────────────────┐  │
                    │  │    Business Logic       │  │
                    │  │  • User Management      │  │
                    │  │  • Order Processing     │  │
                    │  │  • Payment              │  │
                    │  │  • Inventory            │  │
                    │  │  • Notification         │  │
                    │  └─────────────────────────┘  │
                    │  ┌─────────────────────────┐  │
                    │  │    Data Access Layer    │  │
                    │  └─────────────────────────┘  │
                    │             │                 │
                    └─────────────┼─────────────────┘
                                  │
                                  ▼
                        ┌──────────────────┐
                        │  Single Database │
                        │  (All Tables)    │
                        └──────────────────┘

⚠ Problems:
  • Deploy entire app for small change
  • Scale entire app even if only one feature needs it
  • Technology locked (one language, one framework)
  • Large codebase hard to maintain


┌─────────────────────────────────────────────────────────────────────────┐
│                  MICROSERVICES ARCHITECTURE                              │
└─────────────────────────────────────────────────────────────────────────┘

                        ┌─────────────────┐
User Request ──────────▶│   API Gateway   │
                        └─────────────────┘
                                │
            ┌───────────────────┼───────────────────┬───────────────┐
            │                   │                   │               │
            ▼                   ▼                   ▼               ▼
    ┌─────────────┐     ┌─────────────┐    ┌─────────────┐  ┌─────────────┐
    │   User      │     │   Order     │    │  Payment    │  │ Notification│
    │   Service   │     │   Service   │    │  Service    │  │  Service    │
    │             │     │             │    │             │  │             │
    │  - REST API │     │  - GraphQL  │    │  - gRPC     │  │  - Event    │
    │  - Node.js  │     │  - Java     │    │  - Python   │  │  - Go       │
    └──────┬──────┘     └──────┬──────┘    └──────┬──────┘  └──────┬──────┘
           │                   │                   │                │
           ▼                   ▼                   ▼                ▼
    ┌──────────┐        ┌──────────┐       ┌──────────┐     ┌──────────┐
    │ User DB  │        │ Order DB │       │ Payment  │     │ Email    │
    │(Postgres)│        │ (MongoDB)│       │   DB     │     │ Queue    │
    └──────────┘        └──────────┘       │(Postgres)│     │ (Kafka)  │
                                           └──────────┘     └──────────┘

✓ Benefits:
  • Independent deployment
  • Technology flexibility
  • Targeted scaling
  • Team autonomy
  • Fault isolation
```

---

## Complete Microservices Ecosystem

```
┌─────────────────────────────────────────────────────────────────────────┐
│                  COMPLETE MICROSERVICES ECOSYSTEM                        │
└─────────────────────────────────────────────────────────────────────────┘

                            ┌──────────┐
                            │  Client  │
                            │ (Web/App)│
                            └─────┬────┘
                                  │
                                  ▼
                        ┌─────────────────┐
                        │   CDN / Edge    │
                        └────────┬────────┘
                                 │
                                 ▼
                        ┌─────────────────┐
                        │ Load Balancer   │
                        └────────┬────────┘
                                 │
                                 ▼
                        ┌─────────────────────────┐
                        │     API Gateway         │
                        │  • Authentication       │
                        │  • Rate Limiting        │
                        │  • Request Routing      │
                        └────────┬────────────────┘
                                 │
        ┌────────────────────────┼────────────────────────┐
        │                        │                        │
        ▼                        ▼                        ▼
┌───────────────┐        ┌───────────────┐       ┌───────────────┐
│ User Service  │───────▶│ Order Service │──────▶│Payment Service│
│ Port: 8001    │  REST  │ Port: 8002    │ gRPC │ Port: 8003    │
└───────┬───────┘        └───────┬───────┘       └───────┬───────┘
        │                        │                       │
        │                        │                       │
        ▼                        ▼                       ▼
   ┌─────────┐             ┌─────────┐            ┌─────────┐
   │User DB  │             │Order DB │            │Payment  │
   │(PG)     │             │(Mongo)  │            │DB (PG)  │
   └─────────┘             └─────────┘            └─────────┘
        │
        │ Publish Events
        ▼
┌──────────────────────────────────────────────────────────────┐
│                    Message Bus (Kafka)                        │
│  Topics: user.created, order.placed, payment.processed       │
└───────────────────────┬──────────────────────────────────────┘
                        │ Subscribe
        ┌───────────────┼───────────────────┐
        │               │                   │
        ▼               ▼                   ▼
┌──────────────┐  ┌──────────────┐  ┌──────────────┐
│Notification  │  │  Analytics   │  │  Inventory   │
│  Service     │  │   Service    │  │   Service    │
└──────────────┘  └──────────────┘  └──────────────┘


            CROSS-CUTTING CONCERNS
            ──────────────────────
    ┌────────────────┐      ┌────────────────┐
    │ Service Mesh   │      │   Monitoring   │
    │ (Istio/Linkerd)│      │  (Prometheus)  │
    │ • mTLS         │      │  • Metrics     │
    │ • Traffic Mgmt │      │  • Alerts      │
    └────────────────┘      └────────────────┘

    ┌────────────────┐      ┌────────────────┐
    │ Service        │      │  Distributed   │
    │ Discovery      │      │    Tracing     │
    │ (Consul/Eureka)│      │    (Jaeger)    │
    └────────────────┘      └────────────────┘

    ┌────────────────┐      ┌────────────────┐
    │ Config Server  │      │  Log Aggre.    │
    │ (Spring Cloud) │      │     (ELK)      │
    └────────────────┘      └────────────────┘
```

---

## Communication Patterns

### 1. Synchronous Communication (REST/gRPC)

```
┌─────────────────────────────────────────────────────────────────┐
│              SYNCHRONOUS REQUEST-RESPONSE                        │
└─────────────────────────────────────────────────────────────────┘

Client                Order Service              Payment Service
  │                         │                          │
  │─── POST /orders ───────▶│                          │
  │                         │                          │
  │                         │─── POST /charge ────────▶│
  │                         │                          │
  │                         │                       Process
  │                         │                       Payment
  │                         │                          │
  │                         │◀─── 200 OK ──────────────│
  │                         │    {status: "paid"}      │
  │◀── 201 Created ─────────│                          │
  │    {order_id: "123"}    │                          │
  │                         │                          │

Timeline: 0ms ────── 100ms ────── 500ms ────── 600ms

✓ Simple, easy to understand
✓ Immediate response
✗ Tight coupling (if payment down, order fails)
✗ Cascading failures
```

### 2. Asynchronous Communication (Message Queue)

```
┌─────────────────────────────────────────────────────────────────┐
│           ASYNCHRONOUS EVENT-DRIVEN COMMUNICATION                │
└─────────────────────────────────────────────────────────────────┘

Client         Order Service       Message Queue      Payment Service
  │                  │                   │                   │
  │─ POST /orders ──▶│                   │                   │
  │                  │                   │                   │
  │                  │─ Publish Event ──▶│                   │
  │                  │  order.created    │                   │
  │◀─ 202 Accepted ──│                   │                   │
  │  (non-blocking)  │                   │                   │
  │                  │                   │◀── Poll ──────────│
  │                  │                   │                   │
  │                  │                   │─── Event ────────▶│
  │                  │                   │                   │
  │                  │                   │                Process
  │                  │                   │                Payment
  │                  │                   │                   │
  │                  │◀─ Publish Event ──│───────────────────│
  │                  │  payment.completed│                   │
  │                  │                   │                   │

Timeline: 0ms ─── 10ms (return) ─── 500ms (async processing)

✓ Loose coupling (services independent)
✓ Better fault tolerance
✓ Non-blocking
✗ Eventual consistency
✗ More complex
```

---

## Service Discovery Pattern

```
┌─────────────────────────────────────────────────────────────────┐
│                    SERVICE DISCOVERY                             │
└─────────────────────────────────────────────────────────────────┘

                    ┌───────────────────────┐
                    │ Service Registry      │
                    │ (Consul/Eureka)       │
                    │                       │
                    │ ┌───────────────────┐ │
                    │ │ Service: order    │ │
                    │ │ Instances:        │ │
                    │ │  - 10.0.1.5:8001  │ │
                    │ │  - 10.0.1.6:8001  │ │
                    │ │  - 10.0.1.7:8001  │ │
                    │ │ Health: healthy   │ │
                    │ └───────────────────┘ │
                    └───────────────────────┘
                         ▲            │
                    (2)  │            │ (3)
                  Register│            │Query
                         │            ▼
    ┌──────────────┐     │      ┌──────────────┐
    │Order Service │─────┘      │User Service  │
    │ Instance 1   │            │              │
    │ 10.0.1.5     │            └──────────────┘
    └──────────────┘                  │
                                      │ (4) Call
    ┌──────────────┐                  │
    │Order Service │◀─────────────────┘
    │ Instance 2   │   http://10.0.1.5:8001
    │ 10.0.1.6     │
    └──────────────┘

Flow:
─────
1. Order Service starts → Register with Service Registry
2. Health checks every 30s to confirm service is alive
3. User Service needs Order Service → Query Service Registry
4. Service Registry returns healthy instances
5. User Service calls one of the healthy instances
6. If instance becomes unhealthy → deregistered automatically
```

---

## Circuit Breaker Pattern

```
┌─────────────────────────────────────────────────────────────────┐
│                     CIRCUIT BREAKER PATTERN                      │
└─────────────────────────────────────────────────────────────────┘

STATE 1: CLOSED (Normal Operation)
──────────────────────────────────
Service A                               Service B
    │                                       │
    │─────── Request 1 ───────────────────▶│
    │◀────── Response ─────────────────────│
    │                                       │
    │─────── Request 2 ───────────────────▶│
    │◀────── Response ─────────────────────│

✓ All requests pass through
✓ Success count tracked


STATE 2: OPEN (Service B is down)
──────────────────────────────────
Service A                               Service B (DOWN)
    │                                       │
    │─────── Request 1 ───────────────────▶│ (timeout)
    │                                       │
    │─────── Request 2 ───────────────────▶│ (timeout)
    │                                       │
    │─────── Request 3 ───────────────────▶│ (timeout)
    │                                       │
    │ After 3 failures:                     │
    │ Circuit OPENS                         │
    │                                       │
    │─────── Request 4 ───────X             │
    │◀────── Fast Fail ────────┘            │
    │        (fallback response)            │

✓ Fast fail (no waiting for timeout)
✓ Prevent cascading failures
✓ Return cached/default response


STATE 3: HALF-OPEN (Testing Recovery)
──────────────────────────────────────
After 60 seconds...

Service A                               Service B (Recovering?)
    │                                       │
    │─────── Test Request ─────────────────▶│
    │◀────── Success! ──────────────────────│
    │                                       │
    │ Circuit CLOSES                        │
    │ Resume normal operation               │


┌─────────────────────────────────────────────────────────────┐
│                   CIRCUIT STATE DIAGRAM                      │
└─────────────────────────────────────────────────────────────┘

        Success Rate > 50%
    ┌──────────────────────────┐
    │                          │
    ▼                          │
┌────────┐  Failure Rate > 50% ┌─────────────┐
│ CLOSED │───────────────────▶│    OPEN     │
└────────┘                     └─────────────┘
                                      │
                                      │ After timeout (60s)
                                      ▼
                               ┌─────────────┐
                          ┌────│ HALF-OPEN   │
                          │    └─────────────┘
                          │           │
                          │ Success   │ Failure
                          └───────────┘

Implementation (Java - Resilience4j):
────────────────────────────────────
CircuitBreaker circuitBreaker = CircuitBreaker
    .ofDefaults("paymentService");

Supplier<String> supplier = CircuitBreaker
    .decorateSupplier(circuitBreaker, () -> {
        return callPaymentService();
    });

try {
    String result = supplier.get();
} catch (CallNotPermittedException e) {
    // Circuit is open, return fallback
    return "Payment service unavailable, try later";
}
```

---

## Database per Service Pattern

```
┌─────────────────────────────────────────────────────────────────┐
│                DATABASE PER SERVICE PATTERN                      │
└─────────────────────────────────────────────────────────────────┘

    ┌─────────────────┐         ┌─────────────────┐
    │  User Service   │         │  Order Service  │
    │                 │         │                 │
    │  • user CRUD    │         │  • order CRUD   │
    │  • auth logic   │         │  • validation   │
    └────────┬────────┘         └────────┬────────┘
             │                           │
             │ Private Access            │ Private Access
             │ (no other service         │ (no other service
             │  can access this DB)      │  can access this DB)
             ▼                           ▼
    ┌─────────────────┐         ┌─────────────────┐
    │   User DB       │         │   Order DB      │
    │   (Postgres)    │         │   (MongoDB)     │
    │                 │         │                 │
    │ Tables:         │         │ Collections:    │
    │  • users        │         │  • orders       │
    │  • profiles     │         │  • line_items   │
    └─────────────────┘         └─────────────────┘


✓ Benefits:
  • Service independence
  • Choose best DB for each service
  • Easy to scale independently
  • Fault isolation

✗ Challenges:
  • No foreign keys across services
  • No distributed transactions
  • Data consistency issues
  • Queries across services complex


PROBLEM: How to get User data when processing Order?
────────────────────────────────────────────────────

❌ BAD: Order Service directly queries User DB
┌──────────────┐  Direct DB Query   ┌─────────┐
│Order Service │───────────────────▶│ User DB │
└──────────────┘      (WRONG!)      └─────────┘

✓ GOOD: Order Service calls User Service API
┌──────────────┐   API Call    ┌──────────────┐
│Order Service │──────────────▶│ User Service │
└──────────────┘               └──────┬───────┘
                                      │
                                      ▼
                                 ┌─────────┐
                                 │ User DB │
                                 └─────────┘

✓ BETTER: Replicate needed data (Eventual Consistency)
┌──────────────┐               ┌──────────────┐
│Order Service │               │ User Service │
│              │  Event Bus    └──────┬───────┘
│ Cached Data: │◀─────────────────────┘
│  user_id:123 │  user.updated event
│  name:"John" │
│  email:"..."│
└──────────────┘

When user updated → Event published → Order Service updates cache
```

---

## Saga Pattern (Distributed Transactions)

```
┌─────────────────────────────────────────────────────────────────┐
│                    SAGA PATTERN (Choreography)                   │
└─────────────────────────────────────────────────────────────────┘

Scenario: Process Order (Reserve Inventory → Charge Payment → Ship)

SUCCESS FLOW:
─────────────

Order Service     Inventory Service    Payment Service    Shipping Service
      │                   │                   │                  │
      │─ create_order ────┼──────────────────▶│                  │
      │                   │                   │                  │
      │◀─ order_created ──┤                   │                  │
      │                   │                   │                  │
      │                   │─ reserve_inventory┼─────────────────▶│
      │                   │                   │                  │
      │                   │◀─ inventory_reserved                 │
      │                   │                   │                  │
      │                   │                   │─ charge_payment ─┼────▶
      │                   │                   │                  │
      │                   │                   │◀─ payment_success│
      │                   │                   │                  │
      │                   │                   │                  │─ ship_order
      │                   │                   │                  │
      │◀──────────────────┴───────────────────┴──────────────────│
      │                                          order_completed   │

✓ All steps succeeded


FAILURE FLOW (Payment Fails):
──────────────────────────────

Order Service     Inventory Service    Payment Service
      │                   │                   │
      │─ create_order ────┼──────────────────▶│
      │                   │                   │
      │                   │─ reserve_inventory┼─────▶
      │                   │                   │
      │                   │                   │─ charge_payment ─▶
      │                   │                   │
      │                   │                   │◀─ payment_failed ─┤
      │                   │                   │
      │                   │◀─ COMPENSATE ─────┤
      │                   │  unreserve_inventory
      │                   │                   │
      │◀─ COMPENSATE ─────┤                   │
      │  cancel_order     │                   │
      │                   │                   │

Each service implements:
• Transaction (forward action)
• Compensation (rollback action)


┌─────────────────────────────────────────────────────────────────┐
│                    SAGA PATTERN (Orchestration)                  │
└─────────────────────────────────────────────────────────────────┘

             ┌──────────────────────┐
             │  Saga Orchestrator   │
             │  (Order Coordinator) │
             └──────────┬───────────┘
                        │
        ┌───────────────┼───────────────┐
        │               │               │
        ▼               ▼               ▼
┌──────────────┐ ┌──────────────┐ ┌──────────────┐
│  Inventory   │ │   Payment    │ │   Shipping   │
│   Service    │ │   Service    │ │   Service    │
└──────────────┘ └──────────────┘ └──────────────┘

Orchestrator controls the flow:
1. Call Inventory → reserve()
2. If success, Call Payment → charge()
3. If success, Call Shipping → ship()
4. If any fails → call compensating transactions

✓ Central control
✓ Easier to understand
✗ Single point of failure
```

---

## API Gateway vs Service Mesh

```
┌─────────────────────────────────────────────────────────────────┐
│                      API GATEWAY (North-South)                   │
└─────────────────────────────────────────────────────────────────┘

External Clients (Web, Mobile, Partners)
                │
                ▼
        ┌───────────────┐
        │  API Gateway  │  ← Single Entry Point
        │               │
        │ • Auth        │
        │ • Rate Limit  │
        │ • Routing     │
        └───────┬───────┘
                │
    ┌───────────┼───────────┐
    ▼           ▼           ▼
  Service A  Service B  Service C


┌─────────────────────────────────────────────────────────────────┐
│                  SERVICE MESH (East-West)                        │
└─────────────────────────────────────────────────────────────────┘

Internal Service-to-Service Communication

┌──────────────┐         ┌──────────────┐         ┌──────────────┐
│  Service A   │         │  Service B   │         │  Service C   │
│              │         │              │         │              │
│  ┌────────┐  │         │  ┌────────┐  │         │  ┌────────┐  │
│  │ App    │  │         │  │ App    │  │         │  │ App    │  │
│  └────────┘  │         │  └────────┘  │         │  └────────┘  │
│  ┌────────┐  │         │  ┌────────┐  │         │  ┌────────┐  │
│  │ Sidecar│←─┼────────▶│  │ Sidecar│←─┼────────▶│  │ Sidecar│  │
│  │ Proxy  │  │         │  │ Proxy  │  │         │  │ Proxy  │  │
│  └────────┘  │         │  └────────┘  │         │  └────────┘  │
└──────────────┘         └──────────────┘         └──────────────┘
       ▲                        ▲                        ▲
       │                        │                        │
       └────────────────────────┴────────────────────────┘
                    Control Plane (Istio/Linkerd)
                    • mTLS encryption
                    • Traffic routing
                    • Load balancing
                    • Circuit breaking
                    • Observability

Sidecar handles all network concerns → App code stays clean
```

---

## Deployment Strategies

```
┌─────────────────────────────────────────────────────────────────┐
│                    BLUE-GREEN DEPLOYMENT                         │
└─────────────────────────────────────────────────────────────────┘

Step 1: Current Production (Blue)
──────────────────────────────────
Load Balancer ────▶ Blue Environment (v1.0)
                    ├─ Instance 1
                    ├─ Instance 2
                    └─ Instance 3

                    Green Environment (v2.0) - Not receiving traffic
                    ├─ Instance 1
                    ├─ Instance 2
                    └─ Instance 3


Step 2: Switch Traffic to Green
────────────────────────────────
Load Balancer ────▶ Green Environment (v2.0) ✓ LIVE
                    ├─ Instance 1
                    ├─ Instance 2
                    └─ Instance 3

                    Blue Environment (v1.0) - Standby for rollback


Step 3: Rollback if issues
───────────────────────────
Load Balancer ────▶ Blue Environment (v1.0) ← Quick rollback!

✓ Zero downtime
✓ Easy rollback
✗ 2x infrastructure cost


┌─────────────────────────────────────────────────────────────────┐
│                     CANARY DEPLOYMENT                            │
└─────────────────────────────────────────────────────────────────┘

Step 1: 95% v1.0, 5% v2.0
──────────────────────────
              Load Balancer
                    │
         ┌──────────┴──────────┐
      95%│                     │5%
         ▼                     ▼
   ┌──────────┐          ┌──────────┐
   │  v1.0    │          │  v2.0    │
   │ 19 pods  │          │  1 pod   │
   └──────────┘          └──────────┘
                         (canary)
   Monitor metrics:
   - Error rate
   - Latency
   - CPU usage


Step 2: 50% v1.0, 50% v2.0
───────────────────────────
If canary healthy → increase traffic

              Load Balancer
                    │
         ┌──────────┴──────────┐
      50%│                     │50%
         ▼                     ▼
   ┌──────────┐          ┌──────────┐
   │  v1.0    │          │  v2.0    │
   │ 10 pods  │          │ 10 pods  │
   └──────────┘          └──────────┘


Step 3: 0% v1.0, 100% v2.0
───────────────────────────
              Load Balancer
                    │
                    │100%
                    ▼
              ┌──────────┐
              │  v2.0    │
              │ 20 pods  │
              └──────────┘

✓ Gradual rollout
✓ Early issue detection
✓ Production testing with real users
```

---

## Real-World Example: Netflix Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                 NETFLIX MICROSERVICES (Simplified)               │
└─────────────────────────────────────────────────────────────────┘

                        ┌──────────┐
                        │  Client  │
                        └─────┬────┘
                              │
                              ▼
                     ┌─────────────────┐
                     │   Zuul (Edge)   │
                     │   API Gateway   │
                     └────────┬────────┘
                              │
        ┌─────────────────────┼─────────────────────┐
        │                     │                     │
        ▼                     ▼                     ▼
┌──────────────┐      ┌──────────────┐     ┌──────────────┐
│   User       │      │  Content     │     │  Playback    │
│   Service    │      │  Service     │     │  Service     │
└──────┬───────┘      └──────┬───────┘     └──────┬───────┘
       │                     │                     │
       ▼                     ▼                     ▼
┌──────────────┐      ┌──────────────┐     ┌──────────────┐
│Recommendation│      │   Encoding   │     │   CDN        │
│   Service    │      │   Service    │     │   Service    │
└──────────────┘      └──────────────┘     └──────────────┘

Technologies:
─────────────
• Zuul - API Gateway
• Eureka - Service Discovery
• Hystrix - Circuit Breaker
• Ribbon - Client-side Load Balancing
• Spring Cloud - Config Management
• Cassandra - NoSQL Database
• Kafka - Event Streaming

Scale:
──────
• 700+ microservices
• 1 billion+ requests/day
• Deploys 1000s times/day
```

---

## Microservices Challenges & Solutions

```
┌─────────────────────────────────────────────────────────────────┐
│                   CHALLENGES & SOLUTIONS                         │
└─────────────────────────────────────────────────────────────────┘

╔══════════════════╦════════════════════╦═══════════════════════╗
║   Challenge      ║     Problem        ║       Solution        ║
╠══════════════════╬════════════════════╬═══════════════════════╣
║ Data             ║ No joins across    ║ • API Composition     ║
║ Consistency      ║ services           ║ • CQRS Pattern        ║
║                  ║                    ║ • Event Sourcing      ║
╠══════════════════╬════════════════════╬═══════════════════════╣
║ Distributed      ║ No ACID across     ║ • Saga Pattern        ║
║ Transactions     ║ services           ║ • 2PC (avoid)         ║
║                  ║                    ║ • Eventual Consistency║
╠══════════════════╬════════════════════╬═══════════════════════╣
║ Network          ║ Services talk over ║ • Circuit Breaker     ║
║ Failures         ║ network (unreliable║ • Retry with backoff  ║
║                  ║                    ║ • Timeout configs     ║
╠══════════════════╬════════════════════╬═══════════════════════╣
║ Testing          ║ Complex integration║ • Contract Testing    ║
║                  ║ testing            ║ • Service Virtualization║
║                  ║                    ║ • Consumer-Driven Tests║
╠══════════════════╬════════════════════╬═══════════════════════╣
║ Monitoring       ║ Hard to trace      ║ • Distributed Tracing ║
║                  ║ requests across    ║   (Jaeger, Zipkin)    ║
║                  ║ services           ║ • Correlation IDs     ║
╠══════════════════╬════════════════════╬═══════════════════════╣
║ Deployment       ║ Complex deployment ║ • Kubernetes          ║
║ Complexity       ║ of many services   ║ • Docker Containers   ║
║                  ║                    ║ • CI/CD Pipelines     ║
╚══════════════════╩════════════════════╩═══════════════════════╝
```

---

## System Design Interview Answer

**Q: Design a microservices-based e-commerce system**

```
1. REQUIREMENTS
───────────────
• User management, product catalog, orders, payments
• 100k users, 10k orders/day
• High availability, scalable

2. MICROSERVICES BREAKDOWN
───────────────────────────
┌──────────────┬─────────────────────────────┐
│ Service      │ Responsibility              │
├──────────────┼─────────────────────────────┤
│ User         │ Auth, profile, preferences  │
│ Product      │ Catalog, search, inventory  │
│ Order        │ Cart, checkout, order mgmt  │
│ Payment      │ Payment processing, refunds │
│ Notification │ Email, SMS, push            │
│ Shipping     │ Delivery, tracking          │
└──────────────┴─────────────────────────────┘

3. COMMUNICATION
────────────────
• Sync: REST for user-facing (order → payment)
• Async: Kafka for events (order.created → notification)

4. DATA STORAGE
───────────────
• User: PostgreSQL (ACID for transactions)
• Product: MongoDB (flexible schema)
• Order: PostgreSQL (transactional)
• Cache: Redis (sessions, product cache)

5. INFRASTRUCTURE
─────────────────
• API Gateway: Kong
• Service Discovery: Consul
• Circuit Breaker: Resilience4j
• Monitoring: Prometheus + Grafana
• Tracing: Jaeger
• Container: Docker + Kubernetes

6. DEPLOYMENT
─────────────
• Blue-Green for critical services (payment)
• Canary for user-facing (frontend)
• Auto-scaling based on CPU/memory
```

---

## Key Takeaways

✓ **Independence**: Deploy, scale, fail independently
✓ **Technology Flexibility**: Best tool for each job
✓ **Team Autonomy**: Small teams own services
✓ **Resilience**: Fault isolation, graceful degradation
✓ **Scalability**: Scale specific services, not entire app

---

## When to Use Microservices

**Use When:**
- Large, complex application
- Multiple teams working independently
- Different parts need different scaling
- Need technology flexibility
- Long-term maintenance and evolution

**Don't Use When:**
- Small application (< 10k users)
- Single team
- Tight coupling required
- Simple CRUD operations
- Don't have DevOps maturity
