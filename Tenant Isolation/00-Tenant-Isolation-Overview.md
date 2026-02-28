# Tenant Isolation System - Overview (Senior Level, Easy English)

Target level: Senior (5-7 years)

## 1) What is Tenant Isolation?
Tenant isolation ensures one customer (tenant) cannot access another tenant's data or resources. It is critical for SaaS security, compliance, and performance fairness.

## 2) Clarifying Questions (Interview Warm-up)
- How strict is isolation (legal/compliance)?
- Is data residency required per tenant?
- Does the tenant have high or low traffic?
- Any customizations per tenant?
- How many tenants today and in 2 years?

## 3) Approaches to Implement Tenant Isolation

### Approach A: Shared Database, Shared Schema (Row-Level Isolation)
What it is:
- All tenants share tables, separated by tenant_id.

Pros:
- Cheapest and simplest
- Easy to onboard new tenants

Cons:
- Highest risk if query filtering fails
- Noisy-neighbor problems

### Approach B: Shared Database, Separate Schema
What it is:
- Each tenant has its own schema in the same DB.

Pros:
- Better isolation than shared schema
- Easier to manage than many DBs

Cons:
- Schema migrations are more complex
- Still shared DB resources

### Approach C: Separate Database Per Tenant
What it is:
- Each tenant gets its own database.

Pros:
- Strong isolation
- Easier compliance and data residency

Cons:
- Higher operational cost
- Harder to manage at scale

### Approach D: Sharded Tenants (Group Tenants per DB)
What it is:
- Tenants grouped into shards to balance cost and isolation.

Pros:
- Scales better than per-tenant DB
- Limits blast radius

Cons:
- Routing complexity
- Hot shard risk

### Approach E: Hybrid Isolation (Tiered Tenants)
What it is:
- Small tenants share DB, large tenants get dedicated DB.

Pros:
- Cost efficient
- Premium isolation for big customers

Cons:
- Multi-model complexity

### Approach F: Compute Isolation (Dedicated Pods)
What it is:
- Each tenant runs in separate compute.

Pros:
- Strong runtime isolation

Cons:
- More infrastructure cost

### Approach G: Namespace/Account Isolation
What it is:
- Separate cloud accounts or Kubernetes namespaces.

Pros:
- Strong administrative isolation

Cons:
- Harder centralized management

### Approach H: Policy-Based Isolation
What it is:
- Enforce isolation via policy engine (OPA/Cedar).

Pros:
- Centralized security rules

Cons:
- Adds latency and policy complexity

## 4) Common Technologies
- Database isolation: Postgres schemas, MySQL databases, Citus
- Routing: AbstractRoutingDataSource, ShardingSphere
- Policy: OPA, AWS Cedar
- Cloud: Separate accounts/projects for strong isolation

## 5) Key Concepts (Interview Must-Know)
- Tenant context propagation
- Noisy neighbor mitigation
- Per-tenant rate limits and quotas
- Data residency and compliance

## 6) Production Checklist
- Strict tenant_id enforcement in queries
- Automated tests for cross-tenant access
- Per-tenant metrics and alerts
- Backup/restore per tenant

## 7) Quick Interview Answer (30 seconds)
"Tenant isolation keeps one customer from seeing another's data. Common approaches are shared schema with tenant_id, separate schema, or separate database per tenant. At scale, a hybrid model is best: small tenants share, big tenants get dedicated DBs. Choice depends on compliance, scale, and cost."
