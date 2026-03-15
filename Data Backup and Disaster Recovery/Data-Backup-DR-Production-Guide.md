# Data Backup & Disaster Recovery - Production Guide

> **Target**: 10+ Years Experienced Developer
> **Updated**: March 2026
> **Interview Ready**: Complete guide with RTO/RPO calculations and DR runbooks

---

## 📊 Problem Statement

Design **backup and disaster recovery (DR) system** for:
- **Production database**: 2TB PostgreSQL (user data, transactions)
- **File storage**: 10TB S3 (images, documents, videos)
- **Application state**: Kubernetes cluster (50 pods)
- **RTO (Recovery Time Objective)**: 4 hours
- **RPO (Recovery Point Objective)**: 15 minutes
- **Compliance**: GDPR, SOC2 (7-year retention, encryption)
- **Disaster scenarios**: Region failure, ransomware, data corruption

---

## 🎯 Key Concepts

### RTO vs RPO

```
┌─────────────────────────────────────────────────────────────────────────┐
│                      RTO vs RPO EXPLAINED                               │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  DISASTER OCCURS                                                        │
│        │                                                                │
│        ▼                                                                │
│  ┌────────────┐                                                         │
│  │ LAST BACKUP│◄───── RPO (Recovery Point Objective) ──────┐           │
│  │  Taken at  │                                             │           │
│  │  10:00 AM  │       "How much data can we afford to lose?"│           │
│  └────────────┘                                             │           │
│        │                                                     │           │
│        │                                                     │           │
│        ▼                                                     │           │
│  ┌────────────┐                                             │           │
│  │ DISASTER   │                                             │           │
│  │ HAPPENS at │                                             │           │
│  │ 10:15 AM   │◄────────────────────────────────────────────┘           │
│  └────────────┘                                                         │
│        │                                                                │
│        │  Detection + Decision + Restore Process                        │
│        │                                                                │
│        ▼                                                                │
│  ┌────────────┐                                                         │
│  │  SYSTEM    │◄───── RTO (Recovery Time Objective) ──────┐           │
│  │  RESTORED  │                                            │           │
│  │  at        │       "How long can we be down?"           │           │
│  │  2:15 PM   │                                            │           │
│  └────────────┘                                            │           │
│                                                            │           │
│  ┌──────────────────────────────────────────────────────┐ │           │
│  │  Data Lost: 15 minutes (10:00 AM - 10:15 AM)        │ │           │
│  │  RPO = 15 minutes                                    │ │           │
│  │                                                      │ │           │
│  │  Downtime: 4 hours (10:15 AM - 2:15 PM)            │ │           │
│  │  RTO = 4 hours                                       │◄┘           │
│  └──────────────────────────────────────────────────────┘             │
│                                                                         │
│  EXAMPLE RTO/RPO TIERS:                                                │
│                                                                         │
│  Tier 1 (Mission Critical):                                            │
│    - RTO: 1 hour                                                       │
│    - RPO: 5 minutes                                                    │
│    - Strategy: Multi-region active-active, continuous replication      │
│    - Cost: $$$$$                                                       │
│                                                                         │
│  Tier 2 (Business Critical):                                           │
│    - RTO: 4 hours                                                      │
│    - RPO: 15 minutes                                                   │
│    - Strategy: Warm standby, 15-min backups                            │
│    - Cost: $$$                                                         │
│                                                                         │
│  Tier 3 (Standard):                                                    │
│    - RTO: 24 hours                                                     │
│    - RPO: 1 hour                                                       │
│    - Strategy: Cold standby, hourly backups                            │
│    - Cost: $                                                           │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

### RTO/RPO Calculation Formulas

```
RTO Calculation:
-----------------
RTO = Detection Time + Decision Time + Restore Time + Verification Time

Example:
- Detection: 15 minutes (monitoring alerts)
- Decision: 30 minutes (incident commander approval)
- Restore: 3 hours (restore DB from backup, restart services)
- Verification: 15 minutes (smoke tests, health checks)
Total RTO = 4 hours


RPO Calculation:
-----------------
RPO = Backup Frequency

If backups every 15 minutes → RPO = 15 minutes
If backups every 1 hour → RPO = 1 hour

Continuous replication → RPO = near 0 (seconds)


Cost vs RTO/RPO:
-----------------
Lower RTO/RPO = Higher Cost

RTO 1 hour, RPO 5 min = Multi-region active-active = $10,000/month
RTO 4 hours, RPO 15 min = Warm standby = $2,000/month
RTO 24 hours, RPO 1 hour = Cold standby = $500/month
```

---

## 🏗️ High-Level DR Architecture

```
┌─────────────────────────────────────────────────────────────────────────┐
│               DISASTER RECOVERY ARCHITECTURE (AWS)                      │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  PRIMARY REGION (us-east-1)                                             │
│  ┌──────────────────────────────────────────────────────────┐          │
│  │  Production Environment                                  │          │
│  │  ┌────────────────────────────────────────────────┐      │          │
│  │  │  Application Tier                              │      │          │
│  │  │  • EKS Cluster (50 pods)                       │      │          │
│  │  │  • Auto-scaling: 10-50 instances               │      │          │
│  │  │  • Multi-AZ deployment                         │      │          │
│  │  └────────────────────────────────────────────────┘      │          │
│  │                                                           │          │
│  │  ┌────────────────────────────────────────────────┐      │          │
│  │  │  Database Tier                                 │      │          │
│  │  │  • RDS PostgreSQL Multi-AZ (2TB)              │      │          │
│  │  │  • Read Replicas (3)                          │      │          │
│  │  │  • Automated backups every 15 min             │      │          │
│  │  │  • Point-in-time recovery (PITR)              │      │          │
│  │  └────────────────────────────────────────────────┘      │          │
│  │                                                           │          │
│  │  ┌────────────────────────────────────────────────┐      │          │
│  │  │  Storage Tier                                  │      │          │
│  │  │  • S3 (10TB) with versioning                   │      │          │
│  │  │  • Cross-region replication → us-west-2       │      │          │
│  │  │  • Lifecycle: Standard → IA → Glacier         │      │          │
│  │  └────────────────────────────────────────────────┘      │          │
│  └──────────────────────────────────────────────────────────┘          │
│                      │                                                  │
│                      │ Continuous Replication                           │
│                      ▼                                                  │
│  ┌──────────────────────────────────────────────────────────┐          │
│  │  Backup Storage (us-east-1)                              │          │
│  │  ┌────────────────────────────────────────────────┐      │          │
│  │  │  S3 Backup Bucket (Versioned, Encrypted)       │      │          │
│  │  │  • DB snapshots (every 15 min)                 │      │          │
│  │  │  • EKS manifests + secrets                     │      │          │
│  │  │  • Retention: 7 years (compliance)             │      │          │
│  │  │  • Lifecycle: Glacier Deep Archive after 90d   │      │          │
│  │  └────────────────────────────────────────────────┘      │          │
│  └──────────────────────────────────────────────────────────┘          │
│                      │                                                  │
│                      │ Cross-Region Replication                         │
│                      ▼                                                  │
│  ┌──────────────────────────────────────────────────────────┐          │
│  │  DR REGION (us-west-2) - WARM STANDBY                    │          │
│  │  ┌────────────────────────────────────────────────┐      │          │
│  │  │  Application Tier (Minimal)                    │      │          │
│  │  │  • EKS Cluster (5 pods) - health check only    │      │          │
│  │  │  • Can scale to 50 pods in 30 minutes          │      │          │
│  │  └────────────────────────────────────────────────┘      │          │
│  │                                                           │          │
│  │  ┌────────────────────────────────────────────────┐      │          │
│  │  │  Database Tier (Read Replica)                  │      │          │
│  │  │  • RDS Read Replica (cross-region)            │      │          │
│  │  │  • Can be promoted to primary in 5 minutes     │      │          │
│  │  └────────────────────────────────────────────────┘      │          │
│  │                                                           │          │
│  │  ┌────────────────────────────────────────────────┐      │          │
│  │  │  Storage Tier (Replica)                        │      │          │
│  │  │  • S3 Replica Bucket (CRR)                     │      │          │
│  │  │  • Updated within seconds of primary           │      │          │
│  │  └────────────────────────────────────────────────┘      │          │
│  └──────────────────────────────────────────────────────────┘          │
│                                                                         │
│  FAILOVER PROCESS:                                                     │
│  1. Detect primary region failure (CloudWatch alarms)                  │
│  2. Incident commander approves DR activation                          │
│  3. Promote read replica to primary (5 min)                            │
│  4. Scale EKS cluster from 5 → 50 pods (30 min)                        │
│  5. Update Route53 to point to us-west-2 (2 min)                       │
│  6. Run smoke tests and verify (15 min)                                │
│                                                                         │
│  Total RTO: ~1 hour                                                    │
│  Total RPO: ~15 minutes                                                │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## 💾 Backup Strategies

### Strategy 1: Database Backups (RDS PostgreSQL)

```yaml
Automated Snapshots:
  Frequency: Every 15 minutes (continuous backup)
  Retention: 35 days
  RPO: 15 minutes
  Storage: S3 (automated by RDS)
  Encryption: AES-256 (AWS KMS)
  Cost: ~$115/month (for 2TB DB)

Point-in-Time Recovery (PITR):
  Granularity: Per second
  Window: Last 35 days
  Use case: Restore to exact moment before corruption
  Example: Restore to 2023-03-15 14:37:22 UTC

Manual Snapshots:
  Frequency: Before major deployments
  Retention: 7 years (compliance)
  Lifecycle: Glacier Deep Archive after 90 days
  Cost: $10/TB/month (S3), $1/TB/month (Glacier)
```

**AWS CLI Commands:**

```bash
# Create manual snapshot before deployment
aws rds create-db-snapshot \
  --db-instance-identifier prod-postgres \
  --db-snapshot-identifier manual-snapshot-2026-03-15

# List available snapshots
aws rds describe-db-snapshots \
  --db-instance-identifier prod-postgres

# Restore from snapshot
aws rds restore-db-instance-from-db-snapshot \
  --db-instance-identifier prod-postgres-restored \
  --db-snapshot-identifier manual-snapshot-2026-03-15

# Point-in-time restore
aws rds restore-db-instance-to-point-in-time \
  --source-db-instance-identifier prod-postgres \
  --target-db-instance-identifier prod-postgres-pitr \
  --restore-time 2026-03-15T14:37:22Z
```

---

### Strategy 2: S3 Backup with Lifecycle Policies

```json
{
  "Rules": [
    {
      "Id": "MoveToGlacierAfter90Days",
      "Status": "Enabled",
      "Transitions": [
        {
          "Days": 30,
          "StorageClass": "STANDARD_IA"
        },
        {
          "Days": 90,
          "StorageClass": "GLACIER"
        },
        {
          "Days": 365,
          "StorageClass": "DEEP_ARCHIVE"
        }
      ],
      "Expiration": {
        "Days": 2555
      },
      "NoncurrentVersionExpiration": {
        "NoncurrentDays": 90
      }
    }
  ]
}
```

**S3 Versioning + Cross-Region Replication:**

```bash
# Enable versioning
aws s3api put-bucket-versioning \
  --bucket prod-data-backup \
  --versioning-configuration Status=Enabled

# Configure cross-region replication
aws s3api put-bucket-replication \
  --bucket prod-data-backup \
  --replication-configuration file://replication-config.json
```

```json
{
  "Role": "arn:aws:iam::123456789012:role/S3ReplicationRole",
  "Rules": [
    {
      "Status": "Enabled",
      "Priority": 1,
      "DeleteMarkerReplication": { "Status": "Enabled" },
      "Filter": {},
      "Destination": {
        "Bucket": "arn:aws:s3:::prod-data-dr-us-west-2",
        "ReplicationTime": {
          "Status": "Enabled",
          "Time": { "Minutes": 15 }
        }
      }
    }
  ]
}
```

---

### Strategy 3: Kubernetes Cluster Backup (Velero)

```yaml
# Install Velero
velero install \
  --provider aws \
  --plugins velero/velero-plugin-for-aws:v1.8.0 \
  --bucket velero-backups-prod \
  --backup-location-config region=us-east-1 \
  --snapshot-location-config region=us-east-1 \
  --secret-file ./credentials-velero

# Create backup schedule (every 6 hours)
velero schedule create prod-cluster-backup \
  --schedule="0 */6 * * *" \
  --include-namespaces production,default \
  --ttl 720h

# Manual backup before deployment
velero backup create pre-deployment-backup-2026-03-15 \
  --include-namespaces production

# Restore from backup
velero restore create --from-backup prod-cluster-backup-20260315
```

**What Velero Backs Up:**
- Kubernetes resources (Deployments, Services, ConfigMaps)
- Secrets (encrypted)
- PersistentVolumes (EBS snapshots)
- Custom Resource Definitions (CRDs)

---

## 🚨 Disaster Recovery Runbook

### DR Scenario 1: Region Failure (us-east-1 down)

```
┌─────────────────────────────────────────────────────────────────────────┐
│                    DR RUNBOOK: REGION FAILURE                           │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  STEP 1: DETECTION (Target: 5 minutes)                                 │
│  ───────────────────────────────────────────────────────────────────    │
│  □ CloudWatch alarm triggers: "Primary region unhealthy"                │
│  □ PagerDuty alerts on-call engineer                                    │
│  □ Verify: Check AWS Status Dashboard                                  │
│  □ Confirm: Multiple availability zones down                            │
│                                                                         │
│  Command:                                                              │
│    aws cloudwatch describe-alarms --state-value ALARM                   │
│                                                                         │
│  ──────────────────────────────────────────────────────────────────    │
│                                                                         │
│  STEP 2: DECISION (Target: 15 minutes)                                 │
│  ───────────────────────────────────────────────────────────────────    │
│  □ Incident Commander (IC) evaluates severity                           │
│  □ Decision: Activate DR (yes/no)                                       │
│  □ Notify stakeholders (Slack, Email)                                   │
│  □ Start DR activation war room (Zoom)                                  │
│                                                                         │
│  Decision Criteria:                                                    │
│    • Region down > 30 minutes                                          │
│    • AWS ETA > 1 hour                                                  │
│    • Business impact > $10K/hour                                       │
│                                                                         │
│  ──────────────────────────────────────────────────────────────────    │
│                                                                         │
│  STEP 3: DATABASE FAILOVER (Target: 5 minutes)                         │
│  ───────────────────────────────────────────────────────────────────    │
│  □ Promote read replica in us-west-2 to primary                         │
│                                                                         │
│  Command:                                                              │
│    aws rds promote-read-replica \                                       │
│      --db-instance-identifier prod-postgres-replica-west \              │
│      --backup-retention-period 35                                       │
│                                                                         │
│  □ Wait for status = available (2-5 minutes)                            │
│  □ Verify: Run smoke test queries                                       │
│                                                                         │
│  Verification:                                                         │
│    SELECT COUNT(*) FROM users; -- Should return expected count          │
│    SELECT NOW();               -- Verify DB is writable                 │
│                                                                         │
│  ──────────────────────────────────────────────────────────────────    │
│                                                                         │
│  STEP 4: SCALE APPLICATION (Target: 30 minutes)                        │
│  ───────────────────────────────────────────────────────────────────    │
│  □ Update EKS cluster in us-west-2 from 5 → 50 pods                     │
│                                                                         │
│  Command:                                                              │
│    kubectl scale deployment app-deployment \                            │
│      --replicas=50 \                                                    │
│      --namespace=production \                                           │
│      --context=us-west-2                                                │
│                                                                         │
│  □ Wait for pods to become Ready (10-20 minutes)                        │
│  □ Verify: Check pod status                                             │
│                                                                         │
│  Command:                                                              │
│    kubectl get pods -n production -o wide                               │
│                                                                         │
│  ──────────────────────────────────────────────────────────────────    │
│                                                                         │
│  STEP 5: UPDATE DNS (Target: 2 minutes)                                │
│  ───────────────────────────────────────────────────────────────────    │
│  □ Update Route53 to point to us-west-2 load balancer                   │
│                                                                         │
│  Command:                                                              │
│    aws route53 change-resource-record-sets \                            │
│      --hosted-zone-id Z123456789ABC \                                   │
│      --change-batch file://route53-change.json                          │
│                                                                         │
│  route53-change.json:                                                  │
│  {                                                                     │
│    "Changes": [{                                                       │
│      "Action": "UPSERT",                                               │
│      "ResourceRecordSet": {                                            │
│        "Name": "api.example.com",                                      │
│        "Type": "CNAME",                                                │
│        "TTL": 60,                                                      │
│        "ResourceRecords": [                                            │
│          {"Value": "lb-west.elb.amazonaws.com"}                        │
│        ]                                                               │
│      }                                                                 │
│    }]                                                                  │
│  }                                                                     │
│                                                                         │
│  □ Verify: DNS propagation (can take 5-60 seconds)                      │
│                                                                         │
│  ──────────────────────────────────────────────────────────────────    │
│                                                                         │
│  STEP 6: VERIFICATION (Target: 15 minutes)                             │
│  ───────────────────────────────────────────────────────────────────    │
│  □ Run automated smoke tests                                            │
│  □ Test critical user flows (login, checkout, etc.)                     │
│  □ Check error rates (should be <1%)                                    │
│  □ Check latency (p99 < 500ms)                                          │
│  □ Verify monitoring dashboards                                         │
│                                                                         │
│  Smoke Tests:                                                          │
│    curl -f https://api.example.com/health                               │
│    curl -f https://api.example.com/users/1                              │
│                                                                         │
│  ──────────────────────────────────────────────────────────────────    │
│                                                                         │
│  STEP 7: COMMUNICATION (Ongoing)                                       │
│  ───────────────────────────────────────────────────────────────────    │
│  □ Update status page: "Failover to DR region complete"                 │
│  □ Notify customers via email                                           │
│  □ Post-mortem: Document incident timeline                              │
│                                                                         │
│  ──────────────────────────────────────────────────────────────────    │
│                                                                         │
│  TOTAL RTO: ~1 hour (5 + 15 + 5 + 30 + 2 + 15 = 72 minutes)            │
│  RPO: 15 minutes (last backup interval)                                │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

---

### DR Scenario 2: Ransomware Attack

```bash
# 1. Identify affected databases/buckets
aws rds describe-db-instances --query 'DBInstances[*].[DBInstanceIdentifier,LatestRestorableTime]'

# 2. Find last known good snapshot (before encryption)
aws rds describe-db-snapshots \
  --db-instance-identifier prod-postgres \
  --query 'DBSnapshots | sort_by(@, &SnapshotCreateTime) | [-10:]'

# 3. Restore from clean snapshot
aws rds restore-db-instance-from-db-snapshot \
  --db-instance-identifier prod-postgres-clean \
  --db-snapshot-identifier snapshot-before-attack-2026-03-15-08-00

# 4. Verify data integrity
psql -h prod-postgres-clean.xxx.rds.amazonaws.com -U admin -d prod \
  -c "SELECT COUNT(*) FROM users WHERE created_at > '2026-03-14';"

# 5. Forensics: Preserve encrypted DB for analysis
aws rds create-db-snapshot \
  --db-instance-identifier prod-postgres-encrypted \
  --db-snapshot-identifier forensics-snapshot-ransomware-2026-03-15

# 6. Switch application to clean DB
# Update connection string in Kubernetes secrets
kubectl edit secret db-credentials -n production
```

---

## 🧪 Backup Validation & Testing

### Monthly Restore Drill

```bash
#!/bin/bash
# restore-drill.sh - Run monthly restore drill

set -e

echo "Starting monthly restore drill..."

# 1. Create test environment
aws rds restore-db-instance-from-db-snapshot \
  --db-instance-identifier restore-drill-$(date +%Y%m%d) \
  --db-snapshot-identifier $(aws rds describe-db-snapshots \
    --db-instance-identifier prod-postgres \
    --query 'DBSnapshots | sort_by(@, &SnapshotCreateTime) | [-1].DBSnapshotIdentifier' \
    --output text)

echo "Waiting for DB to become available..."
aws rds wait db-instance-available \
  --db-instance-identifier restore-drill-$(date +%Y%m%d)

# 2. Run validation queries
DB_ENDPOINT=$(aws rds describe-db-instances \
  --db-instance-identifier restore-drill-$(date +%Y%m%d) \
  --query 'DBInstances[0].Endpoint.Address' \
  --output text)

psql -h $DB_ENDPOINT -U admin -d prod << EOF
  -- Check row counts
  SELECT 'users' AS table_name, COUNT(*) AS row_count FROM users
  UNION ALL
  SELECT 'orders', COUNT(*) FROM orders
  UNION ALL
  SELECT 'payments', COUNT(*) FROM payments;

  -- Check data freshness
  SELECT MAX(created_at) AS latest_record FROM orders;

  -- Check critical queries work
  SELECT COUNT(DISTINCT user_id) AS active_users
  FROM user_sessions
  WHERE created_at > NOW() - INTERVAL '7 days';
EOF

# 3. Calculate RPO
LATEST_ORDER=$(psql -h $DB_ENDPOINT -U admin -d prod -t -c \
  "SELECT MAX(created_at) FROM orders;")

RPO_SECONDS=$(( $(date +%s) - $(date -d "$LATEST_ORDER" +%s) ))
echo "RPO: $RPO_SECONDS seconds ($((RPO_SECONDS / 60)) minutes)"

# 4. Cleanup
aws rds delete-db-instance \
  --db-instance-identifier restore-drill-$(date +%Y%m%d) \
  --skip-final-snapshot

echo "Restore drill completed successfully!"
```

---

## 📊 Backup Monitoring & Alerts

### CloudWatch Alarms

```json
{
  "AlarmName": "RDS-Backup-Failed",
  "MetricName": "BackupRetentionPeriodStorageUsed",
  "Namespace": "AWS/RDS",
  "Statistic": "Average",
  "Period": 3600,
  "EvaluationPeriods": 1,
  "Threshold": 0,
  "ComparisonOperator": "LessThanThreshold",
  "AlarmActions": ["arn:aws:sns:us-east-1:123456789012:backup-alerts"],
  "TreatMissingData": "breaching"
}
```

### Daily Backup Report (Lambda)

```python
import boto3
from datetime import datetime, timedelta

def lambda_handler(event, context):
    rds = boto3.client('rds')
    sns = boto3.client('sns')

    # Get recent snapshots
    response = rds.describe_db_snapshots(
        DBInstanceIdentifier='prod-postgres',
        SnapshotType='automated'
    )

    snapshots_today = [s for s in response['DBSnapshots']
                      if s['SnapshotCreateTime'].date() == datetime.now().date()]

    # Alert if no backups today
    if len(snapshots_today) < 96:  # Expect 96 snapshots (every 15 min for 24h)
        sns.publish(
            TopicArn='arn:aws:sns:us-east-1:123456789012:backup-alerts',
            Subject='⚠️ Missing Backups Alert',
            Message=f'Only {len(snapshots_today)} backups created today. Expected 96.'
        )
    else:
        print(f"✅ Backup health: {len(snapshots_today)} snapshots created today")

    return {'statusCode': 200, 'body': 'Backup check complete'}
```

---

## 💰 Cost Optimization

### Backup Cost Breakdown

```
Database Backups (2TB):
  - Automated snapshots (35 days): $115/month
  - Manual snapshots → Glacier (7 years): $24/month
  Total: $139/month

S3 Backups (10TB):
  - Standard (0-30 days): $230/month
  - Intelligent-Tiering (30-90 days): $100/month
  - Glacier (90-365 days): $40/month
  - Deep Archive (1-7 years): $10/month
  Total: $380/month

Cross-Region Replication:
  - Data transfer: $20/month
  - Storage in DR region: $250/month
  Total: $270/month

Kubernetes Backups (Velero):
  - EBS snapshots (500GB): $25/month
  - S3 storage (100GB): $2/month
  Total: $27/month

───────────────────────────────
TOTAL BACKUP COST: $816/month
```

---

## 📋 Interview Q&A

### Q1: How do you calculate RTO and RPO?

**Answer:**
```
RTO = Detection + Decision + Restore + Verification
Example: 5min + 15min + 3hr + 15min = 4 hours

RPO = Backup Frequency
Example: Backups every 15 minutes → RPO = 15 minutes

Continuous replication → RPO near 0 seconds
```

### Q2: What's the difference between warm and cold standby?

**Answer:**
```
Warm Standby:
- DR environment running at reduced capacity
- Database read replica active
- Can failover in minutes
- Higher cost (~50% of primary)

Cold Standby:
- DR environment offline
- Restore from snapshots
- Can failover in hours
- Lower cost (~10% of primary)

Hot Standby (Active-Active):
- Both environments serving traffic
- Instant failover
- Highest cost (2x primary)
```

### Q3: How do you test backups without impacting production?

**Answer:**
```
1. Monthly restore drill to test environment
2. Restore from snapshot to separate DB instance
3. Run validation queries (row counts, data freshness)
4. Measure RPO (time difference between backup and now)
5. Document any issues
6. Delete test instance after validation
7. Automate with Lambda + CloudWatch Events
```

### Q4: How do you protect against ransomware?

**Answer:**
```
1. Immutable backups (S3 Object Lock, Vault Lock)
2. Separate AWS account for backups (no cross-account delete)
3. MFA required for backup deletion
4. Automated snapshots (can't be manually deleted)
5. Multi-region replication
6. 7-year retention (compliance)
7. Regular restore drills to verify clean backups
```

### Q5: What's your RTO/RPO for a database with 2TB?

**Answer:**
```
Tier 1 (Mission Critical):
- RTO: 1 hour (multi-region read replica)
- RPO: 5 minutes (continuous replication)
- Cost: $2,000/month

Tier 2 (Business Critical):
- RTO: 4 hours (warm standby)
- RPO: 15 minutes (automated snapshots)
- Cost: $500/month

Tier 3 (Standard):
- RTO: 24 hours (restore from snapshot)
- RPO: 1 hour (hourly snapshots)
- Cost: $100/month
```

### Q6: How do you handle backup encryption?

**Answer:**
```
1. Enable encryption at rest (AWS KMS)
2. Automated snapshots inherit encryption
3. Separate KMS key per environment
4. Cross-region replication: Re-encrypt in target region
5. Key rotation: Every 90 days
6. Access: IAM policies + KMS key policies
7. Audit: CloudTrail logs all key usage
```

### Q7: What metrics do you monitor for backups?

**Answer:**
```
1. Backup success rate (>99.9%)
2. Backup duration (should be consistent)
3. Storage growth rate (detect anomalies)
4. Restore time (measure during drills)
5. RPO achieved (time since last backup)
6. Cost per GB (optimize lifecycle policies)
7. Failed backup alerts (PagerDuty)
```

### Q8: How do you failover to DR region?

**Answer:**
```
1. Detect: CloudWatch alarm (region unhealthy)
2. Decide: Incident commander approves
3. Promote: Read replica → primary (5 min)
4. Scale: EKS pods 5 → 50 (30 min)
5. DNS: Route53 → DR region (2 min)
6. Verify: Smoke tests + monitoring
Total: ~1 hour RTO
```

### Q9: How often do you run restore drills?

**Answer:**
```
Monthly: Full restore drill (DB + app)
Quarterly: DR failover exercise (all teams)
Annually: Full disaster simulation (war game)

Automate monthly drill:
- Lambda function
- Restore latest snapshot to test environment
- Run validation queries
- Report RPO/RTO metrics
- Cleanup test resources
```

### Q10: What's your backup retention policy?

**Answer:**
```
By Tier:
- Automated snapshots: 35 days (RDS default)
- Manual snapshots: 7 years (compliance: SOC2, GDPR)
- Application logs: 90 days (CloudWatch)
- Access logs: 1 year (security)

Lifecycle:
- 0-30 days: S3 Standard ($0.023/GB)
- 30-90 days: S3 IA ($0.0125/GB)
- 90-365 days: Glacier ($0.004/GB)
- 1-7 years: Deep Archive ($0.001/GB)
```

---

## 🎯 The Perfect 2-Minute Interview Answer

> **Interviewer:** "Design a backup and disaster recovery system for a production database."

**Your Answer:**

"I'll design a backup and DR system meeting **RTO 4 hours, RPO 15 minutes** for a 2TB database.

**Architecture (Multi-region):**

**Primary Region (us-east-1):**
- RDS PostgreSQL Multi-AZ
- Automated snapshots every 15 minutes
- Point-in-time recovery (35-day window)
- Cross-region read replica in us-west-2

**DR Region (us-west-2) - Warm Standby:**
- Read replica (continuous replication)
- Minimal EKS cluster (5 pods, can scale to 50)
- S3 cross-region replication

**Backup Strategy:**

**Database**: 15-min snapshots → S3 → Glacier (90 days) → Deep Archive (7 years)

**Storage**: S3 versioning + cross-region replication

**Kubernetes**: Velero backups every 6 hours

**Disaster Recovery Process:**

1. **Detection** (5 min): CloudWatch alarms trigger
2. **Decision** (15 min): Incident commander approves DR
3. **Database failover** (5 min): Promote read replica to primary
4. **Scale app** (30 min): EKS 5→50 pods
5. **DNS update** (2 min): Route53 to DR region
6. **Verify** (15 min): Smoke tests

**Total RTO: 1 hour, RPO: 15 minutes**

**Testing:**
- Monthly restore drills (automated Lambda)
- Quarterly DR failover exercises
- Annual full disaster simulation

**Cost:** ~$800/month (database $140, storage $380, DR region $270, K8s $27)

**Compliance**: Encryption (AWS KMS), 7-year retention (GDPR, SOC2), immutable backups (ransomware protection)

This design balances cost, recovery speed, and compliance requirements."

---

**Last Updated**: March 2026
**Status**: ✅ Production Ready
**For**: 10+ Years Experienced Developer
