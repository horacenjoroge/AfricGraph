# Backup and Disaster Recovery

This package provides comprehensive backup and disaster recovery capabilities for AfricGraph.

## Features

- **Neo4j Backups**: Full and incremental backups
- **PostgreSQL Backups**: Custom format dumps
- **Cloud Storage**: S3, GCS, and Azure integration
- **Retention Policies**: Automated cleanup based on age and frequency
- **Backup Testing**: Integrity validation and restore testing
- **API Integration**: RESTful API for backup management
- **CLI Tool**: Command-line interface for backup operations

## Components

### Core Modules

- `neo4j_backup.py`: Neo4j backup utilities
- `postgres_backup.py`: PostgreSQL backup utilities
- `cloud_storage.py`: Cloud storage integration
- `retention.py`: Retention policy management
- `orchestrator.py`: Backup orchestration
- `testing.py`: Backup testing and validation
- `cli.py`: Command-line interface

## Usage

### Python API

```python
from src.backup.orchestrator import BackupOrchestrator, CloudProvider
from src.backup.retention import RetentionPolicy

# Initialize orchestrator
orchestrator = BackupOrchestrator(
    backup_dir="/var/backups/africgraph",
    cloud_provider=CloudProvider.S3,
    cloud_config={
        "bucket": "africgraph-backups",
        "aws_access_key_id": "...",
        "aws_secret_access_key": "...",
    },
    retention_policy=RetentionPolicy(
        daily_retention=7,
        weekly_retention=4,
        monthly_retention=12,
        yearly_retention=5,
    ),
)

# Run full backup
results = orchestrator.run_full_backup()

# Run incremental backup
results = orchestrator.run_incremental_backup()
```

### CLI

```bash
# Run backup
python -m src.backup.cli backup --type full --cloud s3

# Test backup
python -m src.backup.cli test /path/to/backup

# List backups
python -m src.backup.cli list

# Get status
python -m src.backup.cli status

# Cleanup
python -m src.backup.cli cleanup
```

### REST API

```bash
# Trigger backup
curl -X POST http://localhost:8000/backup/run \
  -H "Content-Type: application/json" \
  -d '{"backup_type": "full", "cloud_upload": true}'

# Get status
curl http://localhost:8000/backup/status

# List backups
curl http://localhost:8000/backup/list

# Test backup
curl -X POST http://localhost:8000/backup/test/neo4j/neo4j_full_20240101.dump.gz
```

## Backup Strategy

### Schedule

- **Full Backups**: Weekly (Sunday 2 AM)
- **Incremental Backups**: Daily (2 AM)
- **Monthly Backups**: First of month
- **Yearly Backups**: January 1st

### Retention

- **Daily**: 7 days
- **Weekly**: 4 weeks
- **Monthly**: 12 months
- **Yearly**: 5 years

## Cloud Storage

### Supported Providers

1. **AWS S3**
   - Requires: `boto3`
   - Configuration: Access key, secret key, bucket, region

2. **Google Cloud Storage**
   - Requires: `google-cloud-storage`
   - Configuration: Project ID, bucket

3. **Azure Blob Storage**
   - Requires: `azure-storage-blob`
   - Configuration: Connection string, container

## Testing

### Automated Testing

Backups are automatically tested after creation:

```python
from src.backup.testing import BackupTester

tester = BackupTester()
results = tester.test_neo4j_backup("/path/to/backup")
```

### Manual Testing

```bash
./deployment/scripts/test-backup.sh /path/to/backup
```

## Disaster Recovery

See `deployment/DISASTER_RECOVERY_PLAN.md` for complete disaster recovery procedures.

## Configuration

See `deployment/BACKUP_CONFIG.md` for configuration details.

## Monitoring

Backup operations are logged and can be monitored via:

- Application logs
- Prometheus metrics (if configured)
- Cloud storage access logs
- Systemd journal (for automated backups)

## Troubleshooting

### Common Issues

1. **Backup Fails**: Check disk space, container status, permissions
2. **Cloud Upload Fails**: Verify credentials, network connectivity
3. **Restore Fails**: Test backup integrity first, check database connectivity
4. **Retention Not Working**: Verify retention policy configuration

### Debug Mode

Enable debug logging:

```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

## Best Practices

1. Test backups regularly
2. Monitor backup sizes and success rates
3. Store backups offsite (cloud storage)
4. Encrypt sensitive backups
5. Document restore procedures
6. Practice disaster recovery drills
7. Keep retention policies aligned with business needs
