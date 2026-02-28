# Distributed Transactions / Consistency - Overview (Senior Level, Easy English)

Target level: Senior (5-7 years)

## 1) What is Distributed Transactions / Consistency?
When a business action touches multiple services or databases, you need a way to keep data consistent. Distributed transactions handle this across systems.

## 2) Clarifying Questions (Interview Warm-up)
- Strong consistency or eventual consistency?
- How many services are involved?
- Is rollback acceptable to users?
- Any regulatory constraints (audit, financial)?
- What is acceptable failure behavior?

## 3) Approaches to Implement Consistency

### Approach A: 2-Phase Commit (2PC)
What it is:
- Coordinator asks all services to prepare, then commit.

Pros:
- Strong consistency

Cons:
- Slow and fragile at scale
- Coordinator is a single point of failure

### Approach B: Saga (Choreography)
What it is:
- Services emit events; each reacts and does its part.

Pros:
- Scales well
- Loose coupling

Cons:
- Complex debugging
- Compensation logic needed

### Approach C: Saga (Orchestration)
What it is:
- Central orchestrator directs each step.

Pros:
- Easier to observe and control

Cons:
- Orchestrator can become bottleneck

### Approach D: Outbox Pattern
What it is:
- Write business data and events in one DB transaction.

Pros:
- Prevents dual-write issues
- Reliable event publishing

Cons:
- Adds processing pipeline

### Approach E: Event Sourcing
What it is:
- Store events as source of truth and rebuild state.

Pros:
- Full audit trail
- Easy replay

Cons:
- Complex model and tooling

### Approach F: Idempotency + Retries
What it is:
- Make operations safe to retry.

Pros:
- Simple and practical

Cons:
- Doesn't solve all consistency problems

### Approach G: Read-Your-Writes (RYW)
What it is:
- Guarantees user sees their own writes.

Pros:
- Better UX in eventually consistent systems

Cons:
- Adds session or routing complexity

### Approach H: CRDT / Conflict-Free Replication
What it is:
- Data types that merge without conflicts.

Pros:
- Great for multi-region writes

Cons:
- Limited data models

## 4) Common Technologies
- Orchestration: Temporal, Cadence, AWS Step Functions
- Eventing: Kafka, Pulsar
- Outbox: Debezium, CDC tools
- Databases with strong consistency: Spanner, Cosmos DB (strong)

## 5) Key Concepts (Interview Must-Know)
- Exactly-once vs at-least-once
- Compensation vs rollback
- Idempotency keys
- Consistency vs availability trade-offs

## 6) Production Checklist
- Define failure and retry policy
- Use idempotency keys for external calls
- Monitor saga state and stuck workflows
- Run chaos tests for partial failures

## 7) Quick Interview Answer (30 seconds)
"Distributed transactions keep data consistent across services. Strong consistency uses 2PC but is slow and fragile. Most modern systems use sagas with compensation, plus outbox and idempotent retries. Choice depends on latency, scale, and tolerance for eventual consistency."
