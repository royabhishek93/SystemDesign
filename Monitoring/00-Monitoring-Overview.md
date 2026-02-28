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

## 7) Quick Interview Answer (30 seconds)
"Monitoring keeps services healthy by collecting metrics, logs, and traces. At scale, we combine all three into an observability stack with good alerting and SLOs. Prometheus + Grafana for metrics, ELK/Loki for logs, and OpenTelemetry + Jaeger for traces are common."
