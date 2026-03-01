# Requirements and Clarifying Questions

**Target level**: Senior (5-7 years), 2026

## Clarifying questions (ask early)
1. **Impact**: Is latency high for all endpoints or a subset? Any error rate spike?
2. **SLOs**: What are p50, p95, p99 targets? What are current values?
3. **Traffic profile**: sudden spike or gradual growth? Any known marketing event?
4. **Change history**: recent deploys, config changes, schema migrations?
5. **Infrastructure**: container vs VM, autoscaling enabled? current capacity?
6. **Dependencies**: DB type, cache, external services, queues?
7. **Backpressure**: timeouts, circuit breakers, retries configured?
8. **Observability**: do we have tracing, metrics, and logs correlation?
9. **Data characteristics**: hot keys, skewed tenant load, large payloads?
10. **Concurrency model**: servlet threads or reactive? thread pool sizes?

## What you will assume if unanswered
- **Environment**: production, autoscaling available but not tuned
- **Stack**: Spring Boot (Tomcat), PostgreSQL, Redis, 2-3 downstream APIs
- **Observability**: Prometheus/Grafana + logs, no full tracing

## Success criteria
- **SLO restored** at p95/p99 within safe change window
- **Root cause documented** with evidence
- **Preventive actions** in backlog with measurable outcomes

## Simple English
Ask clear questions before fixing anything. If you do not know what is slow, you can fix the wrong thing.

## Real example
If only the checkout endpoint is slow, you focus on its DB queries and payment calls, not on the entire app.

## Why it happens
Production issues look similar from the outside. Without scoping by endpoint, tenant, and time, you cannot find the real root cause.

## Beginner glossary (easy English)
**What are p50, p95, p99 targets?**
- Think of response time as a list of numbers. If you sort them:
	- **p50** is the middle value (50% of requests are faster than this)
	- **p95** means 95% are faster, 5% are slower
	- **p99** means 99% are faster, 1% are slower
- Example: p50 = 100 ms, p95 = 900 ms, p99 = 2,500 ms
	- Most users are fine, but a small group waits a long time.

**What does "focusing only on p50" mean?**
- If you only look at p50, you ignore slow users.
- Example: p50 is good, but p99 is very high. Users still complain.

**What does "tracing, metrics, and logs correlation" mean?**
- **Metrics** show trends (latency, errors, CPU).
- **Logs** show details for specific errors.
- **Tracing** shows one request across services.
- Correlation means you can connect them with a request or trace ID.
- Example: a trace shows checkout took 2.3 s, metrics show DB latency spike, logs show "lock timeout".

**How to check threads, DB, GC, and dependencies**
- **Threads**: Are requests waiting because all workers are busy?
	- Example signal: high queue size, low CPU, many blocked threads.
- **DB**: Is the database slow or locked?
	- Example signal: slow query logs and lock waits spike.
- **GC**: Is the JVM pausing a lot?
	- Example signal: GC pause time spikes match latency spikes.
- **Dependencies**: Are external services slow?
	- Example signal: payment API p95 goes up, your checkout p95 goes up.

**What does this Spring Boot config do?**
```yaml
spring:
	datasource:
		hikari:
			maximum-pool-size: 30
			connection-timeout: 3000
```
- Pool size is the max DB connections allowed at once.
- Connection timeout means "wait 3 seconds, then fail fast" if no DB connection is free.

```yaml
spring:
	mvc:
		async:
			request-timeout: 30000
```
- Spring Boot async request timeout means "stop waiting after 30 seconds" so threads do not get stuck.

## Wrong vs Right (code)
❌ **Wrong**: missing Spring Boot timeouts (requests can hang forever)
```yaml
spring:
	mvc:
		async:
			request-timeout: 0
```

✅ **Right**: Spring Boot timeout to protect threads
```yaml
spring:
	mvc:
		async:
			request-timeout: 30000
```

## Interview tip
Say you always start with clarifying questions to reduce scope and avoid guessing.

## Quick checklist
- Impact scope (endpoints, tenants)
- SLOs and current percentiles
- Recent deploys or config changes
- Dependency list and timeouts

## Critical pitfalls and follow-up Q&A
**Pitfalls**:
- Starting to scale without knowing where the latency comes from
- Treating all endpoints as equal

**Follow-up Q&A**:
**Q**: What if the issue started right after a deploy?
**A**: Compare config and code changes, and consider rollback before deeper tuning.

**Q**: What if only one tenant is slow?
**A**: Look for hot key data patterns, cache misses, or large payloads for that tenant.
