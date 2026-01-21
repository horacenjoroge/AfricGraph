# Temporal and Time-Travel Queries

This module provides time-travel query capabilities, allowing you to query the graph state at any point in time, view change history, and restore to previous states.

## Features

- **Versioning**: All nodes and relationships are automatically versioned
- **Temporal Queries**: Query graph state at any point in time
- **Snapshots**: Create point-in-time snapshots of the graph
- **Change History**: Track all changes with full history
- **Restore**: Restore graph to previous states

## Architecture

### Storage

- **PostgreSQL**: Stores versioned nodes, relationships, snapshots, and change history
- **Neo4j**: Current graph state (non-versioned)

### Versioning Strategy

- **Valid Time**: Each version has `valid_from` and `valid_to` timestamps
- **Current Version**: Version with `valid_to = NULL` is the current version
- **Automatic Versioning**: New versions created on create/update operations

## Usage

### Query at Point in Time

```python
from datetime import datetime
from src.temporal.queries import TemporalQueryEngine

engine = TemporalQueryEngine()
result = engine.query_at_time(
    timestamp=datetime(2024, 1, 15, 10, 0, 0),
    labels=["Business"],
)

print(f"Found {result.total_nodes} nodes at that time")
```

### Create Snapshot

```python
from src.temporal.snapshots import SnapshotManager

manager = SnapshotManager()
snapshot = manager.create_snapshot(
    timestamp=datetime(2024, 1, 15, 10, 0, 0),
    description="Before major update",
)
```

### View Change History

```python
from src.temporal.history import ChangeHistoryManager

history_manager = ChangeHistoryManager()
history = history_manager.get_entity_history(
    entity_id="business-123",
    entity_type="node",
)
```

### Restore to Previous State

```python
from src.temporal.restore import RestoreManager

restore_manager = RestoreManager()
result = restore_manager.restore_to_timestamp(
    timestamp=datetime(2024, 1, 15, 10, 0, 0),
    dry_run=True,  # Simulate first
)
```

## API Endpoints

### Query at Time

```http
POST /temporal/query
Content-Type: application/json

{
  "timestamp": "2024-01-15T10:00:00Z",
  "labels": ["Business"]
}
```

### Get Node History

```http
GET /temporal/node/{node_id}/history?start_time=2024-01-01T00:00:00Z
```

### Create Snapshot

```http
POST /temporal/snapshots
Content-Type: application/json

{
  "timestamp": "2024-01-15T10:00:00Z",
  "description": "Before update"
}
```

### Restore

```http
POST /temporal/restore
Content-Type: application/json

{
  "timestamp": "2024-01-15T10:00:00Z",
  "dry_run": true
}
```

## Performance Considerations

### Storage Impact

- **Versioning Overhead**: Each change creates a new version
- **Storage Growth**: Historical data accumulates over time
- **Retention Policy**: Consider implementing data retention policies

### Query Performance

- **Indexes**: Temporal tables are indexed on `(entity_id, valid_from, valid_to)`
- **Query Complexity**: Temporal queries can be slower than current-state queries
- **Caching**: Consider caching frequently accessed historical states

### Optimization Strategies

1. **Partitioning**: Partition temporal tables by time ranges
2. **Archiving**: Archive old versions to separate storage
3. **Selective Versioning**: Only version entities that need history
4. **Compression**: Compress old version data

## Limitations

- **Storage Explosion**: All versions are stored, can grow large
- **Query Complexity**: Temporal queries are more complex than current queries
- **Performance Impact**: Versioning adds overhead to write operations
- **Restore Complexity**: Full restores require careful transaction management

## Future Enhancements

- [ ] Incremental snapshots
- [ ] Compression of old versions
- [ ] Partitioning by time ranges
- [ ] Selective versioning (configurable per entity type)
- [ ] Change diff visualization
- [ ] Temporal graph visualization
