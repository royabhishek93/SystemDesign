# Load Balancer + Failover - Overview (Senior Level, Easy English)

Target level: Senior (5-7 years)

## 1) What is a Load Balancer?
A load balancer sits in front of servers and spreads traffic to keep systems fast and reliable. It also detects unhealthy servers and fails over to healthy ones.

## 2) Clarifying Questions (Interview Warm-up)
- What traffic pattern (steady vs spikes)?
- Is it HTTP, gRPC, TCP, or WebSocket?
- Do we need global traffic routing (multi-region)?
- What is the acceptable downtime (RTO/RPO)?
- Do we need sticky sessions?

## 3) Approaches to Implement Load Balancing + Failover

### Approach A: DNS-Based Load Balancing
What it is:
- DNS returns multiple IPs; clients pick one.

Pros:
- Very simple and cheap
- Works globally

Cons:
- Slow failover due to DNS caching
- Limited traffic control

### Approach B: Layer 4 (TCP/UDP) Load Balancer
What it is:
- Routes based on IP/port. No HTTP awareness.

Pros:
- Very fast
- Good for TCP and non-HTTP protocols

Cons:
- No URL-based routing
- Limited observability

### Approach C: Layer 7 (HTTP) Load Balancer
What it is:
- Understands HTTP headers, paths, cookies.

Pros:
- Smart routing (path/host-based)
- Supports WAF, SSL termination

Cons:
- Slightly higher latency
- More complex config

### Approach D: Active-Active Failover (Multi-Region)
What it is:
- Multiple regions handle traffic at the same time.

Pros:
- Lowest latency globally
- Best resilience

Cons:
- Harder data consistency
- Expensive

### Approach E: Active-Passive Failover
What it is:
- One region is primary, other is standby.

Pros:
- Simpler data setup
- Lower cost

Cons:
- Failover time can be minutes
- Wastes standby capacity

### Approach F: Anycast-Based Global LB
What it is:
- Same IP announced in many regions; traffic goes to nearest.

Pros:
- Very fast failover
- Excellent performance

Cons:
- Needs specialized infrastructure
- Harder to debug routing

### Approach G: Client-Side Load Balancing
What it is:
- Client chooses server (using service discovery).

Pros:
- Removes centralized LB bottleneck
- Works well with microservices

Cons:
- More client complexity
- Version skew issues

### Approach H: Hybrid (Global + Regional)
What it is:
- Global LB routes to regions, then regional LB routes to servers.

Pros:
- Scales well for large systems
- Clear separation of concerns

Cons:
- More components to manage
- Requires good observability

## 4) Common Algorithms (Interview Must-Know)
- Round Robin
- Least Connections
- Weighted Round Robin
- IP Hash / Consistent Hashing (for stickiness)

## 5) Failover Signals (How we detect health)
- Health checks (HTTP 200, TCP handshake)
- Circuit breakers
- Outlier detection
- Error rate and latency thresholds

## 6) Production Checklist
- Health check strategy and timeout tuning
- Global vs regional routing decisions
- Sticky session vs stateless services
- TLS termination and certificate rotation
- Capacity buffer for failover

## 7) Quick Interview Answer (30 seconds)
"A load balancer spreads traffic across servers and removes unhealthy ones. For failover, you can do DNS-based, L4/L7 load balancers, or global active-active/active-passive setups. At scale, a hybrid model works best: global LB picks the region, regional LB routes inside. The choice depends on latency, consistency, and cost."
