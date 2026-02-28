# Rate Limiter - Overview (Senior Level, Easy English)

Target level: Senior (5-7 years)

## 1) What is a Rate Limiter?
A rate limiter controls how many requests a client can make in a time window. It protects services from abuse and keeps the system stable.

## 2) Clarifying Questions (Interview Warm-up)
- Limit per user, per API key, or per IP?
- Global limit or per-region?
- What is the burst allowance?
- Hard block or soft throttle?
- Is strict accuracy required?

## 3) Approaches to Implement a Rate Limiter

### Approach A: Fixed Window Counter
What it is:
- Count requests in a fixed time window.

Pros:
- Simple and fast

Cons:
- Burst at window edges (double-spike problem)

### Approach B: Sliding Window Log
What it is:
- Store timestamps of requests.

Pros:
- Accurate limits

Cons:
- High memory cost

### Approach C: Sliding Window Counter
What it is:
- Approximate sliding using two windows.

Pros:
- Good balance of accuracy and cost

Cons:
- Small approximation error

### Approach D: Token Bucket
What it is:
- Tokens added over time; each request consumes a token.

Pros:
- Handles bursts smoothly
- Common in production

Cons:
- Needs careful refill tuning

### Approach E: Leaky Bucket
What it is:
- Requests queue and leak at a constant rate.

Pros:
- Smooths traffic

Cons:
- Can add latency

### Approach F: Distributed Rate Limiter (Redis)
What it is:
- Central counter store used by all servers.

Pros:
- Consistent across instances

Cons:
- Redis latency and hot keys

### Approach G: Local + Global Hybrid
What it is:
- Local limiter for speed + global limiter for safety.

Pros:
- Low latency with consistency

Cons:
- More complex

### Approach H: API Gateway-Managed Limiting
What it is:
- Use gateway built-in rate limiting policies.

Pros:
- Easy to enforce

Cons:
- Limited flexibility

## 4) Common Technologies
- Redis (most common store)
- Envoy / NGINX (edge enforcement)
- Cloud API gateways (AWS, Azure, GCP)

## 5) Key Concepts (Interview Must-Know)
- Burst control
- Token refill rate
- Per-tenant quotas
- 429 response handling
- Distributed consistency vs performance

## 6) Production Checklist
- Use Redis Lua scripts for atomicity
- Handle clock skew in distributed systems
- Monitor 429 rates and top offenders
- Allow emergency override for critical clients

## 7) Quick Interview Answer (30 seconds)
"A rate limiter protects services by controlling request volume. Common algorithms are fixed window, sliding window, token bucket, and leaky bucket. In production we often use Redis for distributed limits or gateway-level policies. The choice depends on accuracy, burst handling, and latency."
