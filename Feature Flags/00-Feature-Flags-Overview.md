# Feature Flags System - Overview (Senior Level, Easy English)

Target level: Senior (5-7 years)

## 1) What is a Feature Flags System?
A feature flag system turns features on/off without code deploys. It supports safe rollouts, experiments, and fast rollback.

## 2) Clarifying Questions (Interview Warm-up)
- Do we need gradual rollout or simple on/off?
- Is it per user, per tenant, or per region?
- How fast must changes propagate?
- How many flags and rules?
- Do we need audit trails?

## 3) Approaches to Implement Feature Flags

### Approach A: Static Config Flags
What it is:
- Flags stored in config files/env vars.

Pros:
- Very simple

Cons:
- Requires redeploy to change

### Approach B: DB-Backed Flags
What it is:
- Flags stored in database; apps read periodically.

Pros:
- Dynamic updates

Cons:
- DB load and caching needed

### Approach C: Cache + Polling
What it is:
- Flags stored in DB, cached in Redis, polled by services.

Pros:
- Low latency and scalable

Cons:
- Polling delay

### Approach D: Push-Based Flags (Streaming)
What it is:
- Flag changes pushed to clients via streaming.

Pros:
- Near real-time changes

Cons:
- More infra and complexity

### Approach E: SDK + Edge Evaluation
What it is:
- Clients evaluate flags locally using rules.

Pros:
- Very fast evaluation

Cons:
- Sensitive rules exposed to clients

### Approach F: Centralized Evaluation Service
What it is:
- Central service evaluates flags and returns results.

Pros:
- Single source of truth

Cons:
- Adds latency and dependency

### Approach G: Tenant-Aware Flags
What it is:
- Flags segmented by tenant or plan.

Pros:
- Supports SaaS tiers

Cons:
- Rule complexity grows

### Approach H: Experimentation (A/B)
What it is:
- Flags used for experimentation with metrics.

Pros:
- Data-driven rollout

Cons:
- Needs analytics integration

## 4) Common Technologies
- LaunchDarkly, Unleash, Split.io
- Redis + DB for custom solutions
- OpenFeature standard

## 5) Key Concepts (Interview Must-Know)
- Kill switches for rollback
- Flag lifecycle (create, rollout, retire)
- Evaluation consistency and caching
- Audit logs and governance

## 6) Production Checklist
- Limit number of stale flags
- Use default-safe values
- Flag changes with approval
- Monitor feature impact

## 7) Quick Interview Answer (30 seconds)
"Feature flags let us enable or disable features without deploying. Approaches include config-based, DB-backed with cache, push-based streaming, and centralized evaluation services. At scale, we use tenant-aware rules and A/B testing. The choice depends on rollout speed, scale, and governance needs."
