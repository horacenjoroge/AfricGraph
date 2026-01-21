# AfricGraph Disaster Recovery Plan

## Overview

This document outlines the disaster recovery procedures for AfricGraph, including backup strategies, recovery procedures, and business continuity measures.

## Recovery Objectives

### Recovery Time Objective (RTO)
- **Critical Systems**: 4 hours
- **Non-Critical Systems**: 24 hours

### Recovery Point Objective (RPO)
- **Database**: 24 hours (daily backups)
- **Application**: 1 hour (real-time replication)

## Backup Strategy

### Backup Schedule

1. **Full Backups**
   - Frequency: Weekly (Sunday 2 AM)
   - Retention: 4 weeks
   - Location: Local + Cloud Storage

2. **Incremental Backups**
   - Frequency: Daily (2 AM)
   - Retention: 7 days
   - Location: Local + Cloud Storage

3. **Monthly Backups**
   - Frequency: First of each month
   - Retention: 12 months
   - Location: Cloud Storage only

4. **Yearly Backups**
   - Frequency: January 1st
   - Retention: 5 years
   - Location: Cloud Storage only

### Backup Components

1. **Neo4j Database**
   - Full database dumps
   - Transaction logs (for point-in-time recovery)
   - Backup format: `.dump.gz`

2. **PostgreSQL Database**
   - Custom format dumps (pg_dump -Fc)
   - Backup format: `.dump`

3. **Application Data**
   - Configuration files
   - Environment variables (encrypted)
   - SSL certificates

4. **Infrastructure**
   - Docker Compose configurations
   - Nginx configurations
   - Systemd service files

## Disaster Scenarios

### Scenario 1: Database Corruption

**Symptoms:**
- Database queries fail
- Data inconsistencies
- Application errors

**Recovery Steps:**

1. **Stop Application**
   ```bash
   docker-compose -f docker-compose.prod.yml stop backend celery
   ```

2. **Identify Latest Valid Backup**
   ```bash
   ./deployment/scripts/list-backups.sh
   ```

3. **Test Backup Integrity**
   ```bash
   ./deployment/scripts/test-backup.sh /path/to/backup
   ```

4. **Restore Database**
   ```bash
   ./deployment/scripts/restore-backup.sh /path/to/backup
   ```

5. **Verify Data Integrity**
   ```bash
   ./deployment/scripts/health-check.sh
   ```

6. **Restart Application**
   ```bash
   docker-compose -f docker-compose.prod.yml start backend celery
   ```

**Estimated Recovery Time:** 2-4 hours

### Scenario 2: Complete Server Failure

**Symptoms:**
- Server unreachable
- All services down
- No local backups available

**Recovery Steps:**

1. **Provision New Server**
   - Use same VPS provider or alternative
   - Minimum specs: 4GB RAM, 2 CPU, 50GB disk

2. **Setup Server**
   ```bash
   ./deployment/scripts/setup-vps.sh
   ```

3. **Clone Repository**
   ```bash
   cd /opt/africgraph
   git clone <repository-url> .
   ```

4. **Configure Environment**
   ```bash
   cp deployment/env.template .env
   # Edit .env with production values
   ```

5. **Download Backups from Cloud**
   ```bash
   # Configure cloud credentials
   export AWS_ACCESS_KEY_ID=...
   export AWS_SECRET_ACCESS_KEY=...
   
   # Download latest backup
   aws s3 cp s3://africgraph-backups/latest/neo4j_full_*.dump.gz ./
   aws s3 cp s3://africgraph-backups/latest/postgres_*.dump ./
   ```

6. **Restore Databases**
   ```bash
   ./deployment/scripts/restore-backup.sh ./backup.tar.gz
   ```

7. **Start Services**
   ```bash
   ./deployment/scripts/deploy.sh production
   ```

8. **Verify System**
   ```bash
   ./deployment/scripts/health-check.sh
   ```

**Estimated Recovery Time:** 4-8 hours

### Scenario 3: Data Loss (Accidental Deletion)

**Symptoms:**
- Specific data missing
- User reports missing records
- Audit logs show deletion

**Recovery Steps:**

1. **Identify Affected Data**
   - Check audit logs
   - Identify deletion timestamp
   - Determine backup to restore from

2. **Create Point-in-Time Recovery**
   ```bash
   # Restore to specific timestamp
   ./deployment/scripts/restore-backup.sh --timestamp "2024-01-15 14:30:00"
   ```

3. **Extract Specific Data**
   - Query restored database
   - Export affected records
   - Import to production (if safe)

4. **Verify Data Integrity**
   - Compare with audit logs
   - Validate relationships
   - Test application functionality

**Estimated Recovery Time:** 2-6 hours (depending on data volume)

### Scenario 4: Security Breach

**Symptoms:**
- Unauthorized access detected
- Suspicious activity in logs
- Data exfiltration suspected

**Recovery Steps:**

1. **Immediate Response**
   - Isolate affected systems
   - Preserve logs and evidence
   - Notify security team

2. **Assess Damage**
   - Review audit logs
   - Identify compromised data
   - Determine attack vector

3. **Clean Environment**
   - Rotate all credentials
   - Update SSL certificates
   - Patch vulnerabilities

4. **Restore from Clean Backup**
   - Use backup from before breach
   - Verify backup integrity
   - Restore to isolated environment

5. **Validate and Deploy**
   - Test restored system
   - Verify data integrity
   - Deploy with enhanced security

**Estimated Recovery Time:** 8-24 hours

## Backup Testing

### Automated Testing

Backups are automatically tested after creation:

```bash
./deployment/scripts/test-backup.sh /path/to/backup
```

### Manual Testing Schedule

- **Weekly**: Test latest full backup
- **Monthly**: Test restore to staging environment
- **Quarterly**: Full disaster recovery drill

### Test Procedure

1. Create test environment
2. Restore backup
3. Verify data integrity
4. Test application functionality
5. Document results

## Backup Retention Policy

### Local Backups
- Daily: 7 days
- Weekly: 4 weeks
- Monthly: 12 months (cloud only)

### Cloud Backups
- Daily: 30 days
- Weekly: 12 weeks
- Monthly: 12 months
- Yearly: 5 years

### Cleanup

Retention policy is automatically enforced:

```bash
# Manual cleanup
python3 -c "
from src.backup.retention import RetentionPolicy
policy = RetentionPolicy()
policy.cleanup('/var/backups/africgraph')
"
```

## Monitoring and Alerts

### Backup Monitoring

- Backup success/failure alerts
- Backup size monitoring
- Storage quota alerts
- Backup age warnings

### Health Checks

- Daily backup verification
- Weekly restore testing
- Monthly disaster recovery drill

## Communication Plan

### Internal Team

- **On-Call Engineer**: Primary responder
- **DevOps Lead**: Escalation point
- **CTO**: Critical incidents

### External Communication

- **Customers**: Status page updates
- **Vendors**: Service provider notifications
- **Regulators**: Compliance notifications (if required)

## Post-Recovery Procedures

1. **Document Incident**
   - Root cause analysis
   - Timeline of events
   - Actions taken

2. **Review and Improve**
   - Identify gaps in procedures
   - Update documentation
   - Enhance monitoring

3. **Lessons Learned**
   - Team review meeting
   - Process improvements
   - Training updates

## Contact Information

### On-Call Engineer
- Phone: [On-Call Number]
- Email: oncall@africgraph.com

### Escalation
- DevOps Lead: [Contact]
- CTO: [Contact]

## Appendix

### Backup Locations

- **Local**: `/var/backups/africgraph`
- **S3**: `s3://africgraph-backups/`
- **GCS**: `gs://africgraph-backups/`
- **Azure**: `africgraph-backups` container

### Recovery Scripts

- `restore-backup.sh`: Restore from backup
- `test-backup.sh`: Test backup integrity
- `list-backups.sh`: List available backups
- `backup-enhanced.sh`: Run enhanced backup

### Documentation

- Deployment Guide: `deployment/README.md`
- Backup Procedures: This document
- Monitoring Guide: `backend/monitoring/README.md`
