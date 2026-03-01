# Spring Boot Performance Triage Under Load

**Target level**: Senior (5-7 years), 2026

## Problem statement
When traffic spikes, the Spring Boot application becomes slow. The interviewer wants a production-grade diagnosis and fix plan that avoids guessing and prioritizes root cause isolation.

## What the interviewer is testing
- **Systems thinking** under pressure (not just scale-up reflex)
- **Root cause discipline** using evidence and hypotheses
- **Failure mode knowledge** across app, DB, and dependencies
- **Prevention mindset** with observability and capacity planning

## Interview framing
Typical question:
- "What would you do if your Spring Boot app becomes slow when traffic increases?"
- "Production is slow during peak load. How will you diagnose and fix it?"

## High-level flow
- **Detect**: confirm user impact, SLO breach, and scope
- **Triage**: identify the bottleneck domain (threads, DB, GC, dependency)
- **Isolate**: validate a root cause with data
- **Fix**: apply the smallest safe change first
- **Prevent**: add guardrails and capacity planning

See the diagnosis flow diagram: [Spring-Boot-Performance-Triage/mermaid/diagnosis-flow.mmd](Spring-Boot-Performance-Triage/mermaid/diagnosis-flow.mmd)

## Key deliverables in your answer
- A **repeatable workflow**, not just a list of tools
- **Signals** that differentiate thread vs DB vs dependency latency
- **Safe fixes** and **long-term prevention**

## Simple English
When traffic is high and the app is slow, do not guess. First find which part is slow (threads, database, garbage collection, or another service). Then fix that exact bottleneck and add monitoring so it does not happen again.

## Real example
During a peak sale, p95 latency jumped. The team checked thread dumps and DB locks, found a missing index, added it safely, and latency returned to normal without scaling blindly.

## Why it happens
Under load, small inefficiencies multiply. A slow query, a blocked thread, or a slow dependency can make every request wait, which causes a queue and tail latency explosion.

## Wrong vs Right (code)
❌ **Wrong**: no timeouts, unlimited wait
```yaml
spring:
	datasource:
		hikari:
			maximum-pool-size: 200
```

✅ **Right**: timeouts and a safe pool size
```yaml
spring:
	datasource:
		hikari:
			maximum-pool-size: 30
			connection-timeout: 3000
```

## Interview tip
Say the workflow out loud: confirm impact → classify bottleneck → validate evidence → minimal safe fix → prevent recurrence.

## Quick checklist
- Confirm p95/p99 and error rate
- Identify the slowest endpoint and tenant
- Check threads, DB, GC, and dependencies
- Apply the smallest safe fix
- Add alerts and capacity guardrails

## Critical pitfalls and follow-up Q&A
**Pitfalls**:
- Scaling app servers when DB is the bottleneck
- Increasing pools without DB headroom
- Ignoring tail latency and focusing only on p50

**Follow-up Q&A**:
**Q**: What if the DB is already at 90% CPU?
**A**: Reduce query load first (indexes, caching, or query rewrite) before scaling the app.

**Q**: What if latency is only on one endpoint?
**A**: Focus on that endpoint's query plan, thread usage, and dependency calls instead of global tuning.
