# Schema Evolution - Zero-Downtime Migrations Production Guide

> **Target**: 10+ Years Experienced Developer
> **Updated**: March 2026
> **Interview Ready**: Complete guide with SQL examples and migration strategies

---

## 📊 Problem Statement

Design **zero-downtime database schema migrations** for:
- **Production database**: 500GB+, 100M+ rows
- **High traffic**: 10,000 queries/second
- **24/7 availability**: No maintenance windows
- **Multiple app versions**: Rolling deployments (10-20 instances)
- **Safe rollbacks**: Ability to revert within 5 minutes
- **Long-running migrations**: >5GB table alterations

**Challenge**: Change schema without causing:
- ❌ Application errors (column not found)
- ❌ Downtime or read-only mode
- ❌ Data loss or corruption
- ❌ Performance degradation
- ❌ Lock timeouts

---

## 🎯 Functional Requirements

### Must Support
1. **Add columns** - Without locking table
2. **Remove columns** - After code deployment
3. **Rename columns** - Without breaking queries
4. **Change data types** - (e.g., VARCHAR(50) → VARCHAR(255))
5. **Add indexes** - On large tables (>100M rows)
6. **Split tables** - Normalize data
7. **Merge tables** - Denormalize for performance
8. **Add constraints** - (NOT NULL, UNIQUE, FK)

### Non-Functional Requirements
1. **Zero Downtime** - No service interruption
2. **Backward Compatible** - Old code continues working
3. **Forward Compatible** - New code works before migration completes
4. **Safe Rollback** - Revert within 5 minutes
5. **Performance** - No significant query slowdown
6. **Auditability** - Track all schema changes

---

## 🤔 Clarifying Questions (Interview Warm-up)

### Must Ask in Interview:
1. **Database Size**: How many GB? How many rows in largest table?
2. **Traffic**: How many QPS? Read-heavy or write-heavy?
3. **Deployment**: Rolling or blue-green? How many instances?
4. **Tolerance**: Can we accept brief read-only mode? Slight performance degradation?
5. **Database**: MySQL, PostgreSQL, or other? (Different capabilities)
6. **Backup**: Do we have recent backups? Point-in-time recovery?
7. **Testing**: Do we have staging with production-like data?

---

## 🏗️ Core Pattern: Expand-and-Contract (3-Phase Migration)

```
┌─────────────────────────────────────────────────────────────────────────┐
│              EXPAND-AND-CONTRACT MIGRATION PATTERN                      │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  SCENARIO: Rename column "email" to "email_address"                    │
│                                                                         │
│  ┌────────────────────────────────────────────────────────────┐        │
│  │  PHASE 1: EXPAND (Add new column)                          │        │
│  │  Duration: 1 deployment cycle                              │        │
│  └────────────────────────────────────────────────────────────┘        │
│                                                                         │
│  Database Before:                                                       │
│  ┌───────────────────────────┐                                         │
│  │  users                    │                                         │
│  ├───────────┬───────────────┤                                         │
│  │  user_id  │  email        │                                         │
│  ├───────────┼───────────────┤                                         │
│  │  1        │  alice@ex.com │                                         │
│  │  2        │  bob@ex.com   │                                         │
│  └───────────┴───────────────┘                                         │
│                                                                         │
│  Step 1.1: Add new column (nullable, no default)                       │
│  ┌─────────────────────────────────────────────────┐                   │
│  │  ALTER TABLE users ADD COLUMN email_address     │                   │
│  │  VARCHAR(255) NULL;                             │                   │
│  └─────────────────────────────────────────────────┘                   │
│                                                                         │
│  Database After Step 1.1:                                              │
│  ┌──────────────────────────────────────────────────┐                  │
│  │  users                                           │                  │
│  ├───────────┬───────────────┬──────────────────────┤                  │
│  │  user_id  │  email        │  email_address       │                  │
│  ├───────────┼───────────────┼──────────────────────┤                  │
│  │  1        │  alice@ex.com │  NULL                │                  │
│  │  2        │  bob@ex.com   │  NULL                │                  │
│  └───────────┴───────────────┴──────────────────────┘                  │
│                                                                         │
│  Step 1.2: Backfill new column from old column                         │
│  ┌─────────────────────────────────────────────────┐                   │
│  │  UPDATE users SET email_address = email         │                   │
│  │  WHERE email_address IS NULL;                   │                   │
│  └─────────────────────────────────────────────────┘                   │
│                                                                         │
│  Step 1.3: Deploy app v2 (dual-write)                                  │
│  ┌─────────────────────────────────────────────────┐                   │
│  │  // Write to BOTH columns                       │                   │
│  │  UPDATE users                                   │                   │
│  │  SET email = ?, email_address = ?               │                   │
│  │  WHERE user_id = ?                              │                   │
│  └─────────────────────────────────────────────────┘                   │
│                                                                         │
│  ┌────────────────────────────────────────────────────────────┐        │
│  │  PHASE 2: CONTRACT (Switch reads)                          │        │
│  │  Duration: 1 week (monitor for issues)                     │        │
│  └────────────────────────────────────────────────────────────┘        │
│                                                                         │
│  Step 2.1: Deploy app v3 (read from new column, write to both)         │
│  ┌─────────────────────────────────────────────────┐                   │
│  │  // Read from new column                        │                   │
│  │  SELECT user_id, email_address FROM users       │                   │
│  │                                                  │                   │
│  │  // Still write to both (safety)                │                   │
│  │  UPDATE users                                   │                   │
│  │  SET email = ?, email_address = ?               │                   │
│  └─────────────────────────────────────────────────┘                   │
│                                                                         │
│  Step 2.2: Monitor for 1 week                                          │
│  - Check logs for any "email" column references                        │
│  - Verify data consistency (email == email_address)                    │
│  - Monitor error rates and latency                                     │
│                                                                         │
│  ┌────────────────────────────────────────────────────────────┐        │
│  │  PHASE 3: CLEANUP (Remove old column)                      │        │
│  │  Duration: 1 deployment cycle                              │        │
│  └────────────────────────────────────────────────────────────┘        │
│                                                                         │
│  Step 3.1: Deploy app v4 (stop writing to old column)                  │
│  ┌─────────────────────────────────────────────────┐                   │
│  │  // Write only to new column                    │                   │
│  │  UPDATE users                                   │                   │
│  │  SET email_address = ?                          │                   │
│  │  WHERE user_id = ?                              │                   │
│  └─────────────────────────────────────────────────┘                   │
│                                                                         │
│  Step 3.2: Drop old column                                             │
│  ┌─────────────────────────────────────────────────┐                   │
│  │  ALTER TABLE users DROP COLUMN email;           │                   │
│  └─────────────────────────────────────────────────┘                   │
│                                                                         │
│  Final Database:                                                       │
│  ┌─────────────────────────────────────────────┐                       │
│  │  users                                      │                       │
│  ├───────────┬─────────────────────────────────┤                       │
│  │  user_id  │  email_address                  │                       │
│  ├───────────┼─────────────────────────────────┤                       │
│  │  1        │  alice@ex.com                   │                       │
│  │  2        │  bob@ex.com                     │                       │
│  └───────────┴─────────────────────────────────┘                       │
│                                                                         │
│  ✅ ZERO DOWNTIME: Old code worked throughout migration                │
│  ✅ SAFE ROLLBACK: Could revert at any phase                           │
│  ✅ DATA INTEGRITY: Both columns always in sync                        │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## 🚀 Flyway Migration Scripts (Production Examples)

### Migration Tool Setup

```xml
<!-- pom.xml -->
<dependency>
    <groupId>org.flywaydb</groupId>
    <artifactId>flyway-core</artifactId>
    <version>9.22.0</version>
</dependency>
```

```yaml
# application.yml
spring:
  flyway:
    enabled: true
    locations: classpath:db/migration
    baseline-on-migrate: true
    validate-on-migrate: true
    out-of-order: false
```

### Example 1: Add Column (Safe, No Downtime)

**File**: `V1__add_phone_number_column.sql`

```sql
-- Phase 1: Add nullable column (instant, no lock)
ALTER TABLE users
ADD COLUMN phone_number VARCHAR(20) NULL;

-- Index for lookups (create CONCURRENTLY to avoid locks)
CREATE INDEX CONCURRENTLY idx_users_phone_number
ON users(phone_number)
WHERE phone_number IS NOT NULL;

-- Audit log
INSERT INTO schema_changes (migration_version, description, applied_at)
VALUES ('V1', 'Add phone_number column', NOW());
```

**Application Code (Backward Compatible):**

```java
@Entity
@Table(name = "users")
public class User {
    @Id
    private Long userId;

    private String email;

    @Column(name = "phone_number")
    private String phoneNumber;  // New field (nullable)

    // Getters/setters
}

// Code continues working even if phone_number doesn't exist yet
```

---

### Example 2: Rename Column (Expand-and-Contract)

**File**: `V2__rename_email_to_email_address_phase1.sql`

```sql
-- PHASE 1: EXPAND - Add new column
ALTER TABLE users
ADD COLUMN email_address VARCHAR(255) NULL;

-- Backfill new column from old column (batch update to avoid long lock)
-- For large tables, use background job instead

-- Small table (<1M rows): Direct update
UPDATE users
SET email_address = email
WHERE email_address IS NULL;

-- Large table (>1M rows): Batch update in application code
-- (See background job example below)
```

**Application Code v2 (Dual Write):**

```java
@Transactional
public void updateUser(Long userId, String newEmail) {
    String sql = """
        UPDATE users
        SET email = ?,
            email_address = ?
        WHERE user_id = ?
    """;
    jdbcTemplate.update(sql, newEmail, newEmail, userId);
}
```

**File**: `V3__rename_email_to_email_address_phase2.sql`

```sql
-- PHASE 2: CONTRACT - No schema change, just code deployment
-- Application now reads from email_address, still writes to both
```

**Application Code v3 (Read from new, write to both):**

```java
public User getUser(Long userId) {
    String sql = """
        SELECT user_id, email_address, created_at
        FROM users
        WHERE user_id = ?
    """;
    return jdbcTemplate.queryForObject(sql, userRowMapper, userId);
}

@Transactional
public void updateUser(Long userId, String newEmail) {
    String sql = """
        UPDATE users
        SET email = ?,            -- Still write to old (safety)
            email_address = ?
        WHERE user_id = ?
    """;
    jdbcTemplate.update(sql, newEmail, newEmail, userId);
}
```

**File**: `V4__rename_email_to_email_address_phase3.sql`

```sql
-- PHASE 3: CLEANUP - Drop old column
ALTER TABLE users
DROP COLUMN email;

-- Update audit log
INSERT INTO schema_changes (migration_version, description, applied_at)
VALUES ('V4', 'Completed email → email_address migration', NOW());
```

---

### Example 3: Change Data Type (VARCHAR(50) → VARCHAR(255))

**File**: `V5__expand_email_length.sql`

```sql
-- MySQL: Online DDL (non-blocking in MySQL 5.7+)
ALTER TABLE users
MODIFY COLUMN email VARCHAR(255) NOT NULL,
ALGORITHM=INPLACE,
LOCK=NONE;

-- PostgreSQL: Two-step approach for large tables
-- Step 1: Add new column
ALTER TABLE users
ADD COLUMN email_new VARCHAR(255);

-- Step 2: Backfill (batch update)
UPDATE users
SET email_new = email
WHERE email_new IS NULL;

-- Step 3: Swap columns (next migration)
-- ALTER TABLE users DROP COLUMN email;
-- ALTER TABLE users RENAME COLUMN email_new TO email;
```

---

### Example 4: Add NOT NULL Constraint (Safe Pattern)

**File**: `V6__make_phone_required_phase1.sql`

```sql
-- Step 1: Ensure no NULL values exist
UPDATE users
SET phone_number = 'UNKNOWN'
WHERE phone_number IS NULL;

-- Step 2: Add constraint with VALIDATE (PostgreSQL)
ALTER TABLE users
ADD CONSTRAINT phone_number_not_null
CHECK (phone_number IS NOT NULL) NOT VALID;

-- Step 3: Validate constraint (can run later, non-blocking)
ALTER TABLE users
VALIDATE CONSTRAINT phone_number_not_null;

-- Step 4: Convert to proper NOT NULL (after validation)
ALTER TABLE users
ALTER COLUMN phone_number SET NOT NULL;
```

---

### Example 5: Add Index on Large Table (>100M rows)

**File**: `V7__add_email_index.sql`

```sql
-- PostgreSQL: CONCURRENTLY (no table lock)
CREATE INDEX CONCURRENTLY idx_users_email
ON users(email);

-- MySQL: Online DDL
CREATE INDEX idx_users_email
ON users(email)
ALGORITHM=INPLACE,
LOCK=NONE;

-- If index creation fails (e.g., timeout), rollback is automatic
-- Can retry with smaller batch or during low-traffic window
```

---

## 🔄 Background Job: Batch Backfill for Large Tables

### Java Background Job (Spring Boot)

```java
@Service
public class EmailBackfillJob {

    @Autowired
    private JdbcTemplate jdbcTemplate;

    private static final int BATCH_SIZE = 1000;
    private static final int SLEEP_MS = 100;  // Avoid overwhelming DB

    /**
     * Backfill email_address from email column
     * For large tables, run as background job to avoid long-running transaction
     */
    @Scheduled(cron = "0 0 2 * * *")  // Run at 2 AM daily
    public void backfillEmailAddresses() {
        log.info("Starting email backfill job");

        long totalRows = getTotalRowsToBackfill();
        long processedRows = 0;

        while (processedRows < totalRows) {
            int rowsUpdated = backfillBatch();
            processedRows += rowsUpdated;

            log.info("Backfilled {}/{} rows ({:.2f}%)",
                     processedRows, totalRows,
                     (processedRows * 100.0 / totalRows));

            if (rowsUpdated == 0) {
                break;  // No more rows to update
            }

            try {
                Thread.sleep(SLEEP_MS);  // Throttle to avoid DB overload
            } catch (InterruptedException e) {
                Thread.currentThread().interrupt();
                break;
            }
        }

        log.info("Email backfill job completed: {} rows", processedRows);
    }

    private long getTotalRowsToBackfill() {
        String sql = """
            SELECT COUNT(*)
            FROM users
            WHERE email_address IS NULL
        """;
        return jdbcTemplate.queryForObject(sql, Long.class);
    }

    @Transactional
    private int backfillBatch() {
        String sql = """
            UPDATE users
            SET email_address = email
            WHERE user_id IN (
                SELECT user_id
                FROM users
                WHERE email_address IS NULL
                LIMIT ?
            )
        """;
        return jdbcTemplate.update(sql, BATCH_SIZE);
    }
}
```

---

## 🎨 Blue-Green Schema Migration

```
┌─────────────────────────────────────────────────────────────────────────┐
│                  BLUE-GREEN SCHEMA MIGRATION                            │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  Step 1: Current State (Blue Environment)                              │
│  ┌────────────────────────────────────────────────────────┐            │
│  │  Load Balancer → App v1 (10 instances)                 │            │
│  │                      ↓                                  │            │
│  │                  Database v1 (old schema)               │            │
│  │  ┌──────────────────────────────────────┐              │            │
│  │  │  users:                              │              │            │
│  │  │  - user_id                           │              │            │
│  │  │  - email                             │              │            │
│  │  │  - created_at                        │              │            │
│  │  └──────────────────────────────────────┘              │            │
│  └────────────────────────────────────────────────────────┘            │
│                                                                         │
│  Step 2: Setup Green Environment                                       │
│  ┌────────────────────────────────────────────────────────┐            │
│  │  App v2 (10 new instances) - NOT IN LOAD BALANCER      │            │
│  │                      ↓                                  │            │
│  │                  Database v2 (new schema)               │            │
│  │  ┌──────────────────────────────────────┐              │            │
│  │  │  users:                              │              │            │
│  │  │  - user_id                           │              │            │
│  │  │  - email_address (renamed)           │              │            │
│  │  │  - phone_number (new)                │              │            │
│  │  │  - created_at                        │              │            │
│  │  └──────────────────────────────────────┘              │            │
│  │                                                         │            │
│  │  Replicate data from v1 → v2 (continuous sync)         │            │
│  └────────────────────────────────────────────────────────┘            │
│                                                                         │
│  Step 3: Switch Traffic (Green Environment)                            │
│  ┌────────────────────────────────────────────────────────┐            │
│  │  Load Balancer → App v2 (10 instances)                 │            │
│  │                      ↓                                  │            │
│  │                  Database v2 (new schema)               │            │
│  └────────────────────────────────────────────────────────┘            │
│                                                                         │
│  If issues: Instant rollback to Blue environment                       │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## ⚠️ Edge Cases & Failure Scenarios

### 1. Migration Fails Midway

**Problem**: Migration script fails after updating 50% of rows

**Solution**:
```sql
-- Use transactions with savepoints
BEGIN;

SAVEPOINT before_backfill;

UPDATE users
SET email_address = email
WHERE email_address IS NULL;

-- If error occurs, rollback to savepoint
ROLLBACK TO SAVEPOINT before_backfill;

-- Fix issue, retry
COMMIT;
```

### 2. Long-Running Migration Blocks Traffic

**Problem**: ALTER TABLE on 100M row table takes 2 hours, locks table

**Solution**:
```sql
-- Option 1: Use online DDL (PostgreSQL CONCURRENTLY, MySQL ALGORITHM=INPLACE)
ALTER TABLE users
ADD COLUMN phone_number VARCHAR(20) NULL,
ALGORITHM=INPLACE,
LOCK=NONE;

-- Option 2: Shadow table approach
CREATE TABLE users_new LIKE users;
ALTER TABLE users_new ADD COLUMN phone_number VARCHAR(20);

-- Copy data in batches (background job)
INSERT INTO users_new SELECT *, NULL FROM users WHERE user_id BETWEEN 1 AND 1000;
INSERT INTO users_new SELECT *, NULL FROM users WHERE user_id BETWEEN 1001 AND 2000;
-- ... continue in batches

-- Swap tables (brief lock)
RENAME TABLE users TO users_old, users_new TO users;
```

### 3. Deployment Rollback After Schema Change

**Problem**: Deploy app v2 with new schema, then need to rollback app to v1

**Solution**:
```sql
-- Always keep old columns until app rollback window expires
-- Example: Keep email column for 7 days after deploying email_address

-- App v2: Dual write
UPDATE users SET email = ?, email_address = ? WHERE user_id = ?;

-- If rollback to v1: Still has email column, works fine
-- After 7 days: Safe to drop email column
```

### 4. Data Type Change Causes App Crashes

**Problem**: Change age from INT to VARCHAR, app code expects integer

**Solution**:
```sql
-- Option 1: Create new column, migrate gradually
ALTER TABLE users ADD COLUMN age_str VARCHAR(10);
UPDATE users SET age_str = CAST(age AS VARCHAR);

-- App v2: Read from age_str
-- After full rollout: Drop age column

-- Option 2: Use database views for compatibility
CREATE VIEW users_v1 AS
SELECT user_id, CAST(age_str AS INT) AS age
FROM users;

-- Old code uses users_v1 view, new code uses users table
```

---

## 📊 Monitoring & Rollback Procedures

### Pre-Migration Checklist

```yaml
Before Running Migration:
  - [ ] Test on staging with production-like data size
  - [ ] Estimate migration time (dry run)
  - [ ] Check current database locks (SHOW PROCESSLIST)
  - [ ] Backup database (or verify recent backup exists)
  - [ ] Prepare rollback script
  - [ ] Schedule during low-traffic window (if possible)
  - [ ] Alert on-call team
  - [ ] Monitor dashboard ready (queries/sec, lock wait time)
```

### Rollback Script Template

```sql
-- Rollback script for V5__expand_email_length.sql
-- If app crashes after deploying email change

-- Step 1: Stop app instances

-- Step 2: Revert schema change
ALTER TABLE users
MODIFY COLUMN email VARCHAR(50) NOT NULL;

-- Step 3: Truncate data if needed (if new values too long)
UPDATE users
SET email = LEFT(email, 50)
WHERE LENGTH(email) > 50;

-- Step 4: Restart app instances (old version)

-- Step 5: Update Flyway schema history (mark as rolled back)
DELETE FROM flyway_schema_history
WHERE version = '5';
```

### Monitoring Queries

```sql
-- PostgreSQL: Check for long-running migrations
SELECT
    pid,
    now() - query_start AS duration,
    query
FROM pg_stat_activity
WHERE state = 'active'
  AND query LIKE 'ALTER TABLE%'
ORDER BY duration DESC;

-- MySQL: Check for table locks
SHOW PROCESSLIST;

-- Check index creation progress (PostgreSQL)
SELECT
    phase,
    tuples_done,
    tuples_total,
    ROUND(100.0 * tuples_done / NULLIF(tuples_total, 0), 2) AS percent_done
FROM pg_stat_progress_create_index;
```

---

## 📋 Interview Q&A

### Q1: How do you rename a column without downtime?

**Answer:**
```
Use expand-and-contract pattern:
1. Add new column (email_address)
2. Deploy app v2: dual-write to both columns
3. Backfill new column from old column
4. Deploy app v3: read from new, write to both
5. Monitor for 1 week
6. Deploy app v4: stop writing to old column
7. Drop old column

Total time: 2-3 weeks (safe, zero downtime)
```

### Q2: How do you add an index on a 100M row table?

**Answer:**
```
PostgreSQL:
  CREATE INDEX CONCURRENTLY idx_name ON table(column);
  - Builds index without blocking writes
  - Takes longer but no downtime

MySQL:
  CREATE INDEX idx_name ON table(column)
  ALGORITHM=INPLACE, LOCK=NONE;
  - Online DDL in MySQL 5.7+

If fails: Break into smaller batches or use shadow table
```

### Q3: What if a migration fails halfway through?

**Answer:**
```
1. Migrations should be in transactions (when possible)
2. Use savepoints for partial rollback
3. For ALTER TABLE: Use online DDL (non-blocking)
4. For large updates: Batch process (1000 rows at a time)
5. Always have rollback script ready
6. Test on staging with production-size data first
```

### Q4: How do you handle deployment rollbacks after schema changes?

**Answer:**
```
Keep old columns until rollback window expires:
- Deploy app v2 with new schema
- Keep old columns for 7 days (dual-write)
- If rollback needed: Old app still works (old columns exist)
- After 7 days: Safe to drop old columns

Forward compatibility: New schema works with old app
Backward compatibility: Old schema works with new app
```

### Q5: How do you change a column's data type?

**Answer:**
```
Option 1: Create new column
  ALTER TABLE users ADD COLUMN age_new VARCHAR(10);
  UPDATE users SET age_new = CAST(age AS VARCHAR);
  -- Gradual rollout, then drop old column

Option 2: Shadow table
  CREATE TABLE users_new WITH new schema;
  Backfill data in batches;
  RENAME TABLE users TO users_old, users_new TO users;

Option 3: Database views for compatibility
  CREATE VIEW users_v1 AS SELECT CAST(age_str AS INT) AS age FROM users;
```

### Q6: How do you add a NOT NULL constraint safely?

**Answer:**
```
1. Ensure no NULL values exist
   UPDATE users SET phone = 'UNKNOWN' WHERE phone IS NULL;

2. Add constraint as NOT VALID (PostgreSQL)
   ALTER TABLE users ADD CONSTRAINT phone_not_null CHECK (phone IS NOT NULL) NOT VALID;

3. Validate constraint (can run later)
   ALTER TABLE users VALIDATE CONSTRAINT phone_not_null;

4. Convert to proper NOT NULL
   ALTER TABLE users ALTER COLUMN phone SET NOT NULL;

This avoids long table lock on large tables
```

### Q7: How do you test migrations before production?

**Answer:**
```
1. Staging environment with production-like data size
2. Clone prod DB to staging (with anonymized PII)
3. Run migration, measure time
4. Test app with old + new code versions
5. Test rollback procedure
6. Load test to check performance impact
7. Dry-run checklist review
```

### Q8: What tools do you use for schema migrations?

**Answer:**
```
Flyway (Java):
  - Version-controlled SQL migrations
  - Automatic rollback tracking
  - Repeatable migrations
  - Works with Spring Boot

Liquibase:
  - XML/YAML/SQL format
  - Advanced rollback support
  - Database-agnostic

gh-ost (GitHub):
  - Online schema migrations for MySQL
  - No blocking, pausable
  - For very large tables

pt-online-schema-change (Percona):
  - MySQL online DDL alternative
  - Triggers for consistency
```

### Q9: How long should migrations take?

**Answer:**
```
Rule of thumb:
- Small table (<1M rows): <30 seconds
- Medium table (1M-10M rows): 1-5 minutes
- Large table (10M-100M rows): 5-30 minutes
- Very large (>100M rows): Use online DDL or shadow table (hours)

If migration > 5 minutes:
- Use CONCURRENTLY or ALGORITHM=INPLACE
- Batch updates (1000 rows at a time)
- Schedule during low traffic
- Monitor locks and query latency
```

### Q10: What metrics do you monitor during migrations?

**Answer:**
```
1. Query latency (p50, p99)
2. Lock wait time
3. Queries per second (should not drop)
4. Table lock percentage
5. Replication lag (if using replicas)
6. Error rate (4xx, 5xx)
7. Migration progress (% complete)
8. Disk I/O and CPU usage
```

---

## 🎯 The Perfect 2-Minute Interview Answer

> **Interviewer:** "How do you handle zero-downtime schema migrations?"

**Your Answer:**

"Zero-downtime schema migrations require **backward and forward compatibility** between old and new code.

**Core Pattern: Expand-and-Contract (3-phase)**

**Phase 1 - Expand:** Add new column (nullable), dual-write to both old and new

**Phase 2 - Contract:** Switch reads to new column, still write to both (safety buffer)

**Phase 3 - Cleanup:** Drop old column after monitoring period (1 week)

**Example: Rename email → email_address**

1. Add email_address column (NULL)
2. Backfill: UPDATE users SET email_address = email
3. Deploy app v2: Write to both columns
4. Deploy app v3: Read from email_address, write to both
5. Monitor for 1 week
6. Deploy app v4: Stop writing to email
7. Drop email column

**For Large Tables (>100M rows):**
- Use CONCURRENTLY (PostgreSQL) or ALGORITHM=INPLACE (MySQL)
- Batch backfill (1000 rows/sec) to avoid long locks
- Shadow table approach: Create new table, backfill, swap

**Tools:** Flyway/Liquibase for version control, gh-ost for MySQL

**Rollback:** Keep old columns for 7 days (rollback window)

**Monitoring:** Query latency, lock wait time, replication lag

**Key Principle:** Never break old code. Old and new versions must coexist during rolling deployments."

---

## 📚 Production Migration Examples

### Scenario: Split Name into First/Last Name

```sql
-- Current schema
CREATE TABLE users (
    user_id BIGINT PRIMARY KEY,
    name VARCHAR(255),
    email VARCHAR(255)
);

-- Migration V8: Phase 1 - Add new columns
ALTER TABLE users
ADD COLUMN first_name VARCHAR(100),
ADD COLUMN last_name VARCHAR(100);

-- Backfill (background job)
UPDATE users
SET
    first_name = SPLIT_PART(name, ' ', 1),
    last_name = SPLIT_PART(name, ' ', 2)
WHERE first_name IS NULL;

-- Application code: Dual write
@Entity
public class User {
    private String name;           // Old field (keep for now)
    private String firstName;      // New field
    private String lastName;       // New field

    @PrePersist
    @PreUpdate
    public void syncFields() {
        // Dual write: Keep name in sync
        this.name = firstName + " " + lastName;
    }
}

-- Migration V9: Phase 2 - Drop old column (after 2 weeks)
ALTER TABLE users DROP COLUMN name;
```

---

**Last Updated**: March 2026
**Status**: ✅ Production Ready
**For**: 10+ Years Experienced Developer
