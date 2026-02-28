# Schema Evolution (Zero-Downtime Migrations) - Overview (Senior Level, Easy English)

Target level: Senior (5-7 years)

## 1) What is Schema Evolution?
Schema evolution means changing database schema without breaking live traffic. Zero-downtime migrations keep the system running while changes roll out.

## 2) Clarifying Questions (Interview Warm-up)
- How big is the database (TB)?
- Is it read-heavy or write-heavy?
- Can we tolerate brief read-only windows?
- Are we using blue-green deployments?
- How often do schema changes happen?

## 3) Approaches to Zero-Downtime Migrations

### Approach A: Backward-Compatible Changes Only
What it is:
- Add columns, avoid dropping/renaming immediately.

Pros:
- Safest approach
- Minimal risk

Cons:
- Old columns linger

### Approach B: Expand and Contract (2-Phase)
What it is:
- Phase 1: Add new fields, write both old and new.
- Phase 2: Switch reads, then remove old fields later.

Pros:
- Most reliable for large systems

Cons:
- Needs coordination and cleanup

### Approach C: Online DDL / Non-Blocking Migrations
What it is:
- Use DB features for online schema changes.

Pros:
- Faster migrations

Cons:
- DB-specific and not always safe

### Approach D: Shadow Tables
What it is:
- Create new table, backfill, then swap.

Pros:
- Clear rollback path

Cons:
- Requires double writes

### Approach E: Blue-Green Schema
What it is:
- Maintain two schema versions and switch traffic.

Pros:
- Safe rollback

Cons:
- Higher infrastructure cost

### Approach F: API/DB Versioning
What it is:
- Keep multiple schema versions for a period.

Pros:
- Supports multiple app versions

Cons:
- Operational complexity

### Approach G: Batch Backfill
What it is:
- Gradually fill new columns with a background job.

Pros:
- Safe for large datasets

Cons:
- Takes time

### Approach H: Use Migration Tools
What it is:
- Liquibase/Flyway manage versions and rollbacks.

Pros:
- Repeatable and controlled

Cons:
- Needs discipline and testing

## 4) Common Technologies
- Migration tools: Flyway, Liquibase
- Online DDL: MySQL Online DDL, PostgreSQL (CONCURRENTLY)
- Backfill: Spark, background workers

## 5) Key Concepts (Interview Must-Know)
- Backward compatibility
- Feature flags for schema changes
- Dual writes and safe rollbacks
- Long-running migrations and locks

## 6) Production Checklist
- Always test migrations on staging
- Run migrations during low traffic
- Monitor locks and slow queries
- Keep rollback scripts ready

## 7) Quick Interview Answer (30 seconds)
"Zero-downtime schema evolution means changing the DB without breaking live traffic. The safest pattern is expand-and-contract: add new columns, dual-write, switch reads, then remove old fields later. Online DDL and backfill jobs help at scale. Tools like Flyway/Liquibase make this repeatable."
