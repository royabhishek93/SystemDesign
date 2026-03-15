# Monitoring System - Overview (Senior Level, Easy English)

Target level: Senior (5-7 years)

## 1) What is Monitoring?
Monitoring tells you if the system is healthy. It collects metrics, logs, and traces so you can detect issues and fix them fast.

## 2) Clarifying Questions (Interview Warm-up)
- What are the top SLOs (latency, error rate, availability)?
- How much data (events/sec)?
- Retention requirements (7 days, 30 days, 1 year)?
- Do we need real-time alerts?
- Is it multi-region?

## 3) Approaches to Implement Monitoring

### Approach A: Metrics-First Monitoring
What it is:
- Focus on time-series metrics and dashboards.

Pros:
- Fast alerting
- Low cost

Cons:
- Limited request-level detail

### Approach B: Logs-First Monitoring
What it is:
- Centralized log aggregation.

Pros:
- Rich debugging context

Cons:
- High storage cost
- Slow for real-time alerts

### Approach C: Traces-First Monitoring
What it is:
- Distributed tracing to follow a request across services.

Pros:
- Best for microservices debugging

Cons:
- More instrumentation work

### Approach D: Full Observability Stack (Metrics + Logs + Traces)
What it is:
- Combine all three for deep visibility.

Pros:
- Complete picture

Cons:
- Highest cost and complexity

### Approach E: Agent-Based Collection
What it is:
- Install agents on each host to collect data.

Pros:
- Detailed system metrics

Cons:
- Agent maintenance overhead

### Approach F: Sidecar/DaemonSet Collection (K8s)
What it is:
- Collect data using sidecars or DaemonSets.

Pros:
- Standard for Kubernetes

Cons:
- More moving parts

### Approach G: Sampling + Adaptive Sampling
What it is:
- Only keep a subset of traces/logs.

Pros:
- Controls cost

Cons:
- May miss rare issues

### Approach H: Managed Observability Platforms
What it is:
- Use SaaS tools.

Pros:
- Fast setup
- Powerful UI

Cons:
- Vendor lock-in
- Cost grows with scale

## 4) Common Technologies
- Metrics: Prometheus, CloudWatch, Datadog
- Logs: ELK (Elasticsearch, Logstash, Kibana), Loki
- Traces: Jaeger, Zipkin, OpenTelemetry
- Managed: Datadog, New Relic, Grafana Cloud

## 5) Key Concepts (Interview Must-Know)
- Golden signals: latency, traffic, errors, saturation
- SLIs / SLOs / SLAs
- Alert fatigue and paging policies
- Correlation IDs and trace context

## 6) Production Checklist
- Define SLOs and error budgets
- Create runbooks for common alerts
- Alert on symptoms, not just causes
- Monitor customer journey (synthetics)

## 7) Architecture Diagram

### Full Observability Stack (Metrics + Logs + Traces)

```
┌────────────────────────────────────────────────────────────────────────┐
│                    MONITORING & OBSERVABILITY SYSTEM                   │
├────────────────────────────────────────────────────────────────────────┤
│                                                                        │
│  ┌──────────────┐     ┌──────────────┐     ┌──────────────┐          │
│  │  Service A   │     │  Service B   │     │  Service C   │          │
│  │  (Backend)   │     │  (API)       │     │  (Database)  │          │
│  └──────┬───────┘     └──────┬───────┘     └──────┬───────┘          │
│         │                    │                    │                   │
│         │ Instrumented with: │                    │                   │
│         │ • Prometheus       │                    │                   │
│         │ • Logback          │                    │                   │
│         │ • OpenTelemetry    │                    │                   │
│         │                    │                    │                   │
│  ┌──────┼────────────────────┼────────────────────┼──────┐            │
│  │      │   OBSERVABILITY    │   PILLARS          │      │            │
│  │      │                    │                    │      │            │
│  │      ▼                    ▼                    ▼      │            │
│  │  ┌────────────┐  ┌────────────────┐  ┌────────────┐ │            │
│  │  │  METRICS   │  │     LOGS       │  │   TRACES   │ │            │
│  │  └─────┬──────┘  └────────┬───────┘  └─────┬──────┘ │            │
│  └────────┼──────────────────┼─────────────────┼────────┘            │
│           │                  │                 │                     │
│           ▼                  ▼                 ▼                     │
│  ┌────────────────┐ ┌────────────────┐ ┌────────────────┐           │
│  │ Metrics Store  │ │   Log Store    │ │  Trace Store   │           │
│  │  (Prometheus)  │ │  (Elasticsearch│ │   (Jaeger /    │           │
│  │  Time-series   │ │   / Loki)      │ │   Tempo)       │           │
│  │  DB            │ │  Full-text     │ │  Distributed   │           │
│  │                │ │  search        │ │  trace data    │           │
│  │  Retention:    │ │  Retention:    │ │  Retention:    │           │
│  │  30 days       │ │  7 days        │ │  7 days        │           │
│  │                │ │  (raw logs)    │ │  (sampled)     │           │
│  └───────┬────────┘ └───────┬────────┘ └───────┬────────┘           │
│          │                  │                  │                     │
│          └──────────────────┼──────────────────┘                     │
│                             │                                        │
│                             ▼                                        │
│  ┌──────────────────────────────────────────────────────┐             │
│  │          Visualization & Alerting Layer              │             │
│  │                                                      │             │
│  │  ┌────────────────────────────────────────┐          │             │
│  │  │  Grafana Dashboards                    │          │             │
│  │  │  • Service health (RED metrics)        │          │             │
│  │  │  • Infrastructure (CPU, memory, disk)  │          │             │
│  │  │  • Business metrics (orders/sec)       │          │             │
│  │  └────────────────────────────────────────┘          │             │
│  │                                                      │             │
│  │  ┌────────────────────────────────────────┐          │             │
│  │  │  Alert Manager                         │          │             │
│  │  │  • High error rate (> 5%)              │          │             │
│  │  │  • High latency (p95 > 500ms)          │          │             │
│  │  │  • Service down                        │          │             │
│  │  └────────────────┬───────────────────────┘          │             │
│  │                   │                                  │             │
│  └───────────────────┼──────────────────────────────────┘             │
│                      │                                                │
│                      ▼                                                │
│  ┌──────────────────────────────────────────────────────┐             │
│  │          Incident Response                           │             │
│  │  • PagerDuty                                         │             │
│  │  • Slack notifications                               │             │
│  │  • On-call engineer                                  │             │
│  └──────────────────────────────────────────────────────┘             │
│                                                                        │
└────────────────────────────────────────────────────────────────────────┘
```

### Monitoring Flow - From Signal to Action

```
┌────────────────────────────────────────────────────────────────────────┐
│                    MONITORING FLOW DIAGRAM                             │
├────────────────────────────────────────────────────────────────────────┤
│                                                                        │
│  1. COLLECTION LAYER                                                  │
│  ──────────────────                                                   │
│                                                                        │
│  ┌────────────┐   Metrics (counter, gauge, histogram)                │
│  │  Services  │ ─────────────────────────────────────▶ Prometheus    │
│  │            │                                                       │
│  │            │   Logs (JSON structured)                              │
│  │            │ ─────────────────────────────────────▶ Fluentd        │
│  │            │                                        │               │
│  │            │   Traces (spans with context)          │               │
│  │            │ ─────────────────────────────────────▶ OpenTelemetry  │
│  └────────────┘                                                       │
│                                                                        │
│  2. STORAGE LAYER                                                     │
│  ─────────────────                                                    │
│                                                                        │
│  Prometheus  ──▶  Time-series DB (Thanos for long-term)              │
│  Fluentd     ──▶  Elasticsearch / Loki                                │
│  OpenTelem.  ──▶  Jaeger / Tempo                                      │
│                                                                        │
│  3. ANALYSIS LAYER                                                    │
│  ──────────────────                                                   │
│                                                                        │
│  PromQL Queries:                                                      │
│    rate(http_requests_total[5m])     → Requests per second           │
│    histogram_quantile(0.95, ...)     → P95 latency                   │
│                                                                        │
│  Log Queries:                                                         │
│    level:ERROR AND service:api       → Error logs from API           │
│                                                                        │
│  Trace Analysis:                                                      │
│    traceId:abc123                    → End-to-end request flow        │
│                                                                        │
│  4. ALERT RULES                                                       │
│  ──────────────                                                       │
│                                                                        │
│  alert: HighErrorRate                                                 │
│    expr: rate(errors[5m]) > 0.05     → Fire if > 5% errors           │
│    for: 2m                            → Must persist 2 minutes        │
│    severity: critical                                                 │
│                                                                        │
│  alert: HighLatency                                                   │
│    expr: http_p95 > 500ms            → Fire if p95 > 500ms           │
│    for: 5m                                                            │
│    severity: warning                                                  │
│                                                                        │
│  5. INCIDENT RESPONSE                                                 │
│  ────────────────────                                                 │
│                                                                        │
│  Alert triggers → PagerDuty → On-call engineer                       │
│                                                                        │
│  Engineer uses:                                                       │
│  • Grafana dashboard to see graphs                                    │
│  • Logs to find error messages                                        │
│  • Traces to identify slow dependency                                 │
│  • Runbook to apply known fix                                         │
│                                                                        │
└────────────────────────────────────────────────────────────────────────┘
```

### Golden Signals (Four Key Metrics)

```
┌────────────────────────────────────────────────────────────────────────┐
│                    GOLDEN SIGNALS OF MONITORING                        │
├────────────────────────────────────────────────────────────────────────┤
│                                                                        │
│  1. LATENCY (How fast?)                                               │
│  ───────────────────────                                              │
│     Metric: http_request_duration_seconds                             │
│     Query:  histogram_quantile(0.95, rate(http_duration[5m]))        │
│     SLO:    P95 < 200ms                                               │
│                                                                        │
│     ┌─────────────────────────────────────┐                           │
│     │  Latency Histogram                  │                           │
│     │  P50: 50ms                           │                           │
│     │  P95: 180ms  ✅                      │                           │
│     │  P99: 450ms                          │                           │
│     └─────────────────────────────────────┘                           │
│                                                                        │
│  2. TRAFFIC (How busy?)                                               │
│  ────────────────────                                                 │
│     Metric: http_requests_total                                       │
│     Query:  rate(http_requests_total[5m])                             │
│     Normal: 1000 req/s                                                │
│     Current: 2500 req/s (spike detected)                              │
│                                                                        │
│  3. ERRORS (What's failing?)                                          │
│  ─────────────────────────                                            │
│     Metric: http_requests_total{status=~"5.."}                        │
│     Query:  rate(errors[5m]) / rate(total[5m])                        │
│     SLO:    < 0.1% (99.9% success rate)                               │
│     Current: 0.05% ✅                                                 │
│                                                                        │
│  4. SATURATION (How full?)                                            │
│  ───────────────────────                                              │
│     Metrics:                                                          │
│     • CPU:      80%  (approaching limit)                              │
│     • Memory:   70%  ✅                                               │
│     • DB Conn:  90%  ⚠️ (need to scale)                              │
│     • Disk I/O: 40%  ✅                                               │
│                                                                        │
│  ┌──────────────────────────────────────────────────────────┐         │
│  │  WHEN ANY SIGNAL DEGRADES → INVESTIGATE & ALERT          │         │
│  └──────────────────────────────────────────────────────────┘         │
│                                                                        │
└────────────────────────────────────────────────────────────────────────┘
```

## 8) Quick Interview Answer (30 seconds)
"Monitoring keeps services healthy by collecting metrics, logs, and traces. At scale, we combine all three into an observability stack with good alerting and SLOs. Prometheus + Grafana for metrics, ELK/Loki for logs, and OpenTelemetry + Jaeger for traces are common."
