# Cross-Questions (Wrong vs Correct)

**Target level**: Senior (5-7 years), 2026

1. ❌ **Wrong**: "Just add more servers."
   ✅ **Correct**: "Scale only after isolating the bottleneck; if DB is the limit, more app servers will not help."

2. ❌ **Wrong**: "Check CPU and restart the app."
   ✅ **Correct**: "Use thread dumps and latency percentiles to confirm whether CPU, threads, or IO is the constraint."

3. ❌ **Wrong**: "Increase DB pool size to fix timeouts."
   ✅ **Correct**: "Only increase pool if DB has headroom; otherwise reduce query load or add indexes."

4. ❌ **Wrong**: "Use caching everywhere."
   ✅ **Correct**: "Cache hot, read-heavy paths with clear invalidation; measure hit rate and stampede risk."

5. ❌ **Wrong**: "We should switch to reactive to fix latency."
   ✅ **Correct**: "Reactive helps only when IO wait is dominant; measure before re-architecture."

6. ❌ **Wrong**: "Timeouts should be high so requests succeed."
   ✅ **Correct**: "Set timeouts to bound tail latency and avoid thread starvation."

7. ❌ **Wrong**: "GC tuning always fixes latency."
   ✅ **Correct**: "GC tuning helps if allocation pressure is the root cause; verify with GC logs."

8. ❌ **Wrong**: "The DB is always the problem."
   ✅ **Correct**: "Correlate DB latency with app p95; if no correlation, look elsewhere."

9. ❌ **Wrong**: "We should add retries for reliability."
   ✅ **Correct**: "Retries can amplify load; use bounded retries with circuit breakers."

10. ❌ **Wrong**: "Just run a profiler in production."
    ✅ **Correct**: "Use low-overhead diagnostics first; profile in a staging mirror when possible."

11. ❌ **Wrong**: "Add indexes to all columns."
    ✅ **Correct**: "Index only for high-selectivity filters and common query patterns."

12. ❌ **Wrong**: "Scale read replicas to fix write latency."
    ✅ **Correct**: "Writes are limited by primary; consider batching or partitioning."

13. ❌ **Wrong**: "Monitor only CPU and memory."
    ✅ **Correct**: "Monitor saturation, latency percentiles, queue depth, and dependency SLOs."

14. ❌ **Wrong**: "If p50 is fine, users are happy."
    ✅ **Correct**: "Tail latency (p95/p99) drives user pain; optimize the tail."

## Simple English
Interviewers ask follow-ups to see if you can defend your decision with real evidence, not guesses.

## Real example
If they ask, "Why not just scale?" you answer, "Because the DB lock wait is the bottleneck, and scaling app nodes will not reduce that."

## Why it happens
Production systems fail in predictable ways. Follow-up questions test if you understand those patterns.

## Wrong vs Right (code)
❌ **Wrong**: ignore timeouts in clients
```java
RestTemplate restTemplate = new RestTemplate();
```

✅ **Right**: set connect and read timeouts
```java
HttpComponentsClientHttpRequestFactory factory = new HttpComponentsClientHttpRequestFactory();
factory.setConnectTimeout(2000);
factory.setReadTimeout(3000);
RestTemplate restTemplate = new RestTemplate(factory);
```

## Interview tip
Answer follow-ups with evidence: "I would check X metric, confirm Y, then do Z."

## Quick checklist
- Tail latency focus (p95/p99)
- Bottleneck domain mapping
- Evidence before fixes
- Reversible changes first

## Critical pitfalls and follow-up Q&A
**Pitfalls**:
- Over-optimizing before confirming root cause
- Using retries without bounds

**Follow-up Q&A**:
**Q**: What if dependency latency is high but your SLA is strict?
**A**: Add circuit breaker, timeouts, and partial fallbacks to protect tail latency.

**Q**: What if the issue appears only during peak?
**A**: Capture peak-time metrics and simulate traffic to reproduce the threshold.
