# Backup Configuration Guide

## Overview

This guide explains how to configure and manage backups for AfricGraph.

## Configuration

### Environment Variables

Add these to your `.env` file:

```bash
# Backup Directory
BACKUP_DIR=/var/backups/africgraph

# Cloud Storage Provider (optional)
BACKUP_CLOUD_PROVIDER=s3  # s3, gcs, azure, or empty for local only

# AWS S3 Configuration
S3_BACKUP_BUCKET=africgraph-backups
AWS_ACCESS_KEY_ID=your_access_key
AWS_SECRET_ACCESS_KEY=your_secret_key
AWS_REGION=us-east-1

# Google Cloud Storage Configuration
GCS_BACKUP_BUCKET=africgraph-backups
GCP_PROJECT_ID=your_project_id

# Azure Blob Storage Configuration
AZURE_BACKUP_CONTAINER=africgraph-backups
AZURE_STORAGE_CONNECTION_STRING=your_connection_string

# Retention Policy
BACKUP_DAILY_RETENTION=7
BACKUP_WEEKLY_RETENTION=4
BACKUP_MONTHLY_RETENTION=12
BACKUP_YEARLY_RETENTION=5
```

## Backup Types

### Full Backup

Complete backup of all databases:

```bash
./deployment/scripts/backup-enhanced.sh full
```

Or via API:
```bash
curl -X POST http://localhost:8000/backup/run \
  -H "Content-Type: application/json" \
  -d '{"backup_type": "full", "cloud_upload": true}'
```

### Incremental Backup

Incremental backup (Neo4j only, PostgreSQL uses full):

```bash
./deployment/scripts/backup-enhanced.sh incremental
```

## Cloud Storage Setup

### AWS S3

1. Create S3 bucket:
```bash
aws s3 mb s3://africgraph-backups
```

2. Configure lifecycle policy:
```json
{
  "Rules": [
    {
      "Id": "DeleteOldBackups",
      "Status": "Enabled",
      "Expiration": {
        "Days": 365
      }
    }
  ]
}
```

3. Set environment variables in `.env`

### Google Cloud Storage

1. Create bucket:
```bash
gsutil mb gs://africgraph-backups
```

2. Set environment variables in `.env`

### Azure Blob Storage

1. Create storage account and container
2. Get connection string
3. Set environment variables in `.env`

## Automated Backups

### Systemd Timer

The systemd timer runs daily at 3 AM:

```bash
# Enable timer
sudo systemctl enable africgraph-backup.timer
sudo systemctl start africgraph-backup.timer

# Check status
sudo systemctl status africgraph-backup.timer
```

### Cron (Alternative)

Add to crontab:

```bash
# Daily incremental backup at 2 AM
0 2 * * * /opt/africgraph/deployment/scripts/backup-enhanced.sh incremental

# Weekly full backup on Sunday at 2 AM
0 2 * * 0 /opt/africgraph/deployment/scripts/backup-enhanced.sh full
```

## Backup Testing

### Test Backup Integrity

```bash
./deployment/scripts/test-backup.sh /path/to/backup
```

### List Backups

```bash
./deployment/scripts/list-backups.sh
```

### Check Backup Status

```bash
curl http://localhost:8000/backup/status
```

## Restore Procedures

### Restore from Backup

```bash
./deployment/scripts/restore-enhanced.sh /path/to/backup
```

### Restore Specific Database

```bash
# Neo4j only
./deployment/scripts/restore-enhanced.sh /path/to/neo4j_backup neo4j

# PostgreSQL only
./deployment/scripts/restore-enhanced.sh /path/to/postgres_backup postgres
```

## Monitoring

### Backup Success Alerts

Configure alerts in your monitoring system:

```yaml
# Prometheus alert rule
- alert: BackupFailed
  expr: backup_last_success_timestamp < (time() - 86400)
  for: 1h
  annotations:
    summary: "Backup has not succeeded in 24 hours"
```

### Backup Size Monitoring

Monitor backup sizes to detect anomalies:

```bash
# Check backup sizes
du -sh /var/backups/africgraph/*
```

## Troubleshooting

### Backup Fails

1. Check disk space:
```bash
df -h /var/backups
```

2. Check Docker containers:
```bash
docker ps
```

3. Check logs:
```bash
journalctl -u africgraph-backup.service
```

### Restore Fails

1. Test backup integrity first:
```bash
./deployment/scripts/test-backup.sh /path/to/backup
```

2. Check database connectivity:
```bash
docker exec africgraph-postgres pg_isready
docker exec africgraph-neo4j cypher-shell -u neo4j -p $NEO4J_PASSWORD "RETURN 1"
```

3. Check disk space:
```bash
df -h
```

### Cloud Upload Fails

1. Verify credentials:
```bash
aws s3 ls s3://africgraph-backups
```

2. Check network connectivity:
```bash
ping s3.amazonaws.com
```

3. Review cloud storage logs

## Best Practices

1. **Test Backups Regularly**: Run restore tests monthly
2. **Monitor Backup Sizes**: Detect data growth anomalies
3. **Verify Cloud Uploads**: Ensure backups are in cloud storage
4. **Document Restore Procedures**: Keep procedures up to date
5. **Regular DR Drills**: Practice disaster recovery quarterly
6. **Encrypt Backups**: Use encryption for sensitive data
7. **Offsite Storage**: Always store backups offsite (cloud)

## CLI Usage

The backup CLI tool provides additional functionality:

```bash
# Run backup
python -m src.backup.cli backup --type full --cloud s3

# Test backup
python -m src.backup.cli test /path/to/backup

# List backups
python -m src.backup.cli list

# Get status
python -m src.backup.cli status

# Cleanup old backups
python -m src.backup.cli cleanup
```

## API Endpoints

- `POST /backup/run` - Trigger backup
- `GET /backup/status` - Get backup status
- `GET /backup/list` - List all backups
- `POST /backup/test/{backup_file}` - Test backup integrity
- `POST /backup/cleanup` - Run retention cleanup
