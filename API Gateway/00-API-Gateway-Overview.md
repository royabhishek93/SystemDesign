# API Gateway - Overview (Senior Level, Easy English)

Target level: Senior (5-7 years)

## 1) What is an API Gateway?
An API Gateway is the front door for all client requests. It routes, secures, and shapes traffic before it reaches backend services.

Typical responsibilities:
- Routing and load balancing to microservices
- Authentication and authorization
- Rate limiting and quotas
- Request/response transformation
- Caching and compression
- Observability (logs, metrics, tracing)

## 2) Clarifying Questions (Interview Warm-up)
Ask these early:
- Who are the clients (web, mobile, partner, internal)?
- How many requests per second (RPS) and peak traffic?
- Is latency more important than feature flexibility?
- Do we need global routing (multi-region)?
- What auth standards are required (OAuth, JWT, mTLS)?
- Do we need versioning and backward compatibility?

## 3) Approaches to Implement an API Gateway
Below are common production approaches. Each is valid depending on scale, team size, and compliance needs.

### Approach A: Simple Reverse Proxy (NGINX / HAProxy)
What it is:
- A fast L7 proxy that routes requests to services.

When to use:
- Small to medium systems
- Simple routing needs

Pros:
- Very fast and stable
- Easy to operate

Cons:
- Limited features (auth, rate limiting) without extra modules
- Harder to build complex logic

### Approach B: Managed API Gateway (Cloud Vendor)
Examples:
- AWS API Gateway, Azure API Management, GCP API Gateway

When to use:
- Want fast time-to-market
- Standard enterprise features needed

Pros:
- Built-in auth, throttling, analytics, caching
- Strong security features and SLAs

Cons:
- Vendor lock-in
- Cost grows with traffic

### Approach C: Service Mesh + Edge Gateway
What it is:
- Use a lightweight edge gateway plus a service mesh inside (Envoy + Istio).

When to use:
- Large microservice architecture
- Need strong traffic policies and observability

Pros:
- Fine-grained traffic control (canary, circuit breaking)
- Strong telemetry and policy enforcement

Cons:
- Operational complexity
- Requires platform expertise

### Approach D: Custom Gateway (Spring Cloud Gateway / Node / Go)
What it is:
- Build your own gateway with frameworks.

When to use:
- Special business rules (custom auth, custom routing)
- Need full control

Pros:
- Full customization
- Easier to integrate with internal logic

Cons:
- You must maintain and scale it
- Security mistakes are risky

### Approach E: API Management Layer on Top of Proxy
What it is:
- Combine proxy (NGINX/Envoy) with a management layer (Kong, Tyk).

When to use:
- Need developer portal, API keys, analytics

Pros:
- Good balance of features and control
- Supports plugins and policies

Cons:
- More components to run
- Plugin compatibility issues

### Approach F: Multi-Region Global Gateway
What it is:
- A global gateway that routes to the nearest region.

When to use:
- Global users, strict latency requirements
- Need region failover

Pros:
- Lower latency, regional isolation
- Better resilience

Cons:
- Complex routing and config
- Data residency challenges

### Approach G: Edge Gateway with CDN Integration
What it is:
- Gateway at the edge + CDN for caching static or even API responses.

When to use:
- High read traffic, public APIs

Pros:
- Excellent performance
- Reduces backend load

Cons:
- Cache invalidation complexity
- Not ideal for strict consistency

### Approach H: BFF (Backend For Frontend) Gateways
What it is:
- Separate gateways per client type (web, iOS, Android).

When to use:
- Many client-specific needs

Pros:
- Tailored responses, less over-fetching
- Faster front-end development

Cons:
- More services to manage
- Risk of duplicated logic

## 4) Core Building Blocks (What Interviewers Expect)
- Routing: path-based, header-based, version-based
- Auth: JWT validation, OAuth2, mTLS
- Rate limiting: token bucket or leaky bucket
- Observability: logs, metrics, traces
- Resilience: retries, timeouts, circuit breakers
- Caching: response cache for safe endpoints

## 5) Common Trade-offs (Easy English)
- More features = more latency
- More flexibility = more operational complexity
- Managed gateways = less control but faster delivery
- Custom gateways = full control but higher risk

## 6) Production Checklist
- Secure auth validation and key rotation
- Global rate limits + per-tenant quotas
- Canary deploys and rollback strategy
- WAF and DDoS protection
- Audit logging for sensitive APIs

## 7) Quick Interview Answer (30 seconds)
"An API Gateway is the front door for all clients. It routes traffic, enforces auth, rate limits, and provides observability. In production, you can implement it as a reverse proxy (simple), a managed gateway (fast to launch), a custom gateway (full control), or a gateway with service mesh for advanced traffic policies. The right choice depends on scale, compliance, and how much control the team needs."
