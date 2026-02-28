# Data Backup + Disaster Recovery - Overview (Senior Level, Easy English)

Target level: Senior (5-7 years)

## 1) What is Backup and DR?
Backups store copies of data for recovery. Disaster Recovery (DR) is the plan to restore systems when a major outage happens.

## 2) Clarifying Questions (Interview Warm-up)
- Required RTO (recovery time) and RPO (data loss)?
- Single region or multi-region?
- What data is most critical?
- Compliance requirements (retention, encryption)?
- How often do we test restores?

## 3) Approaches to Backup + DR

### Approach A: Periodic Full Backups
What it is:
- Full snapshot every day/week.

Pros:
- Simple to restore

Cons:
- Large storage and time

### Approach B: Incremental Backups
What it is:
- Save only changes since last backup.

Pros:
- Faster and cheaper

Cons:
- Restore chain is longer

### Approach C: Continuous Backup (Point-in-Time)
What it is:
- Capture changes continuously.

Pros:
- Low RPO

Cons:
- More storage and complexity

### Approach D: Cross-Region Replication
What it is:
- Replicate data to another region.

Pros:
- Faster DR

Cons:
- Higher cost

### Approach E: Warm Standby
What it is:
- Secondary region is running at reduced capacity.

Pros:
- Faster failover

Cons:
- Ongoing cost

### Approach F: Cold Standby
What it is:
- Secondary region is offline until needed.

Pros:
- Lowest cost

Cons:
- Slowest recovery

### Approach G: Backup Vault + Immutable Storage
What it is:
- Store backups in WORM/immutable storage.

Pros:
- Protects against ransomware

Cons:
- Harder to delete quickly

### Approach H: DR as Code + Runbooks
What it is:
- Automate DR steps using scripts and IaC.

Pros:
- Reliable and repeatable

Cons:
- Requires maintenance

## 4) Common Technologies
- Databases: RDS snapshots, Aurora backups
- Storage: S3 versioning + Glacier
- Tools: Velero (K8s), Restic
- DR orchestration: AWS Backup, Azure Site Recovery

## 5) Key Concepts (Interview Must-Know)
- RTO vs RPO
- Backup frequency vs recovery speed
- Restore validation and drills
- Encryption and access control

## 6) Production Checklist
- Regular restore tests
- Store backups in a separate account
- Monitor backup success/failure
- Keep runbooks and failover scripts updated

## 7) Quick Interview Answer (30 seconds)
"Backups protect data, DR restores the system after a major outage. Common approaches include full and incremental backups, continuous point-in-time backup, and cross-region replication with warm or cold standby. The right plan depends on RTO/RPO, cost, and compliance." 
