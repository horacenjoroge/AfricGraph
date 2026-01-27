# Entity Relationship Diagram (ERD)

This document provides a comprehensive view of the AfricGraph database schema, including both PostgreSQL relational tables and Neo4j graph database structure.

> **📊 Diagrams**: All diagrams in this document use simple text-based ASCII art for easy viewing in any editor.

## Table of Contents

1. [PostgreSQL Schema](#postgresql-schema)
2. [Neo4j Graph Schema](#neo4j-graph-schema)
3. [Cross-Database Relationships](#cross-database-relationships)
4. [Table Descriptions](#table-descriptions)

---

## PostgreSQL Schema

### Core Tables

```
┌─────────────────────────────────────────────────────────────┐
│                        users                                 │
├─────────────────────────────────────────────────────────────┤
│ UUID id (PK)                                                │
│ VARCHAR email (UK)                                          │
│ VARCHAR password_hash                                       │
│ VARCHAR role                                                │
│ BOOLEAN is_active                                           │
│ TIMESTAMPTZ created_at                                      │
│ TIMESTAMPTZ updated_at                                      │
└───────────────┬─────────────────────────────────────────────┘
                │ creates
                │
                ▼
┌─────────────────────────────────────────────────────────────┐
│                    audit_events                             │
├─────────────────────────────────────────────────────────────┤
│ BIGSERIAL id (PK)                                           │
│ TIMESTAMPTZ created_at                                      │
│ VARCHAR event_type                                          │
│ VARCHAR action                                              │
│ VARCHAR actor_id                                            │
│ VARCHAR actor_type                                          │
│ VARCHAR resource_type                                       │
│ VARCHAR resource_id                                         │
│ VARCHAR outcome                                             │
│ TEXT reason                                                 │
│ JSONB before_snapshot                                       │
│ JSONB after_snapshot                                        │
│ JSONB extra                                                 │
│ VARCHAR ip_address                                          │
│ VARCHAR user_agent                                          │
│ VARCHAR event_hash                                          │
└─────────────────────────────────────────────────────────────┘
                ▲
                │ isolates
                │
┌───────────────┴─────────────────────────────────────────────┐
│                      tenants                                │
├─────────────────────────────────────────────────────────────┤
│ VARCHAR tenant_id (PK)                                      │
│ VARCHAR name                                                │
│ VARCHAR domain                                              │
│ VARCHAR status                                              │
│ JSONB config                                                │
│ TIMESTAMP created_at                                        │
│ TIMESTAMP updated_at                                        │
└───────────────┬─────────────────────────────────────────────┘
                │ has
                │
                ▼
┌─────────────────────────────────────────────────────────────┐
│                  tenant_configs                             │
├─────────────────────────────────────────────────────────────┤
│ VARCHAR tenant_id (PK, FK → tenants.tenant_id)             │
│ VARCHAR key (PK)                                            │
│ JSONB value                                                 │
│ TEXT description                                            │
│ TIMESTAMP updated_at                                        │
└─────────────────────────────────────────────────────────────┘
```

### Workflow Tables

```
┌─────────────────────────────────────────────────────────────┐
│              workflow_definitions                            │
├─────────────────────────────────────────────────────────────┤
│ BIGSERIAL id (PK)                                           │
│ VARCHAR key                                                 │
│ INT version                                                 │
│ VARCHAR name                                                │
│ TEXT description                                            │
│ JSONB definition                                            │
│ TIMESTAMPTZ created_at                                      │
└───────────────┬─────────────────────────────────────────────┘
                │ defines
                │
                ▼
┌─────────────────────────────────────────────────────────────┐
│              workflow_instances                             │
├─────────────────────────────────────────────────────────────┤
│ BIGSERIAL id (PK)                                           │
│ VARCHAR definition_key                                      │
│ INT definition_version                                      │
│ VARCHAR business_id                                         │
│ VARCHAR entity_type                                         │
│ VARCHAR entity_id                                           │
│ VARCHAR status                                              │
│ INT current_step_index                                      │
│ JSONB steps                                                 │
│ JSONB context                                               │
│ TIMESTAMPTZ created_at                                      │
│ TIMESTAMPTZ updated_at                                      │
└───────────────┬─────────────────────────────────────────────┘
                │ generates
                │
                ▼
┌─────────────────────────────────────────────────────────────┐
│              workflow_history                               │
├─────────────────────────────────────────────────────────────┤
│ BIGSERIAL id (PK)                                           │
│ BIGINT instance_id (FK → workflow_instances.id)             │
│ VARCHAR event_type                                          │
│ JSONB payload                                               │
│ TIMESTAMPTZ created_at                                      │
└─────────────────────────────────────────────────────────────┘
```

### Risk & Fraud Tables

```
┌─────────────────────────────────────────────────────────────┐
│                    risk_scores                              │
├─────────────────────────────────────────────────────────────┤
│ BIGSERIAL id (PK)                                           │
│ VARCHAR business_id                                         │
│ NUMERIC score                                               │
│ JSONB factors                                               │
│ TEXT explanation                                            │
│ TIMESTAMPTZ created_at                                      │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│                   fraud_alerts                             │
├─────────────────────────────────────────────────────────────┤
│ BIGSERIAL id (PK)                                           │
│ VARCHAR business_id                                         │
│ VARCHAR pattern                                             │
│ VARCHAR severity                                            │
│ NUMERIC score                                               │
│ TEXT description                                            │
│ JSONB metadata                                              │
│ BOOLEAN is_false_positive                                   │
│ VARCHAR status                                              │
│ TIMESTAMPTZ created_at                                      │
│ TIMESTAMPTZ updated_at                                      │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│                       alerts                                │
├─────────────────────────────────────────────────────────────┤
│ VARCHAR id (PK)                                             │
│ VARCHAR rule_id                                             │
│ VARCHAR alert_type                                          │
│ VARCHAR severity                                            │
│ VARCHAR status                                              │
│ VARCHAR business_id                                         │
│ VARCHAR entity_type                                         │
│ VARCHAR entity_id                                           │
│ TEXT message                                                │
│ JSONB details                                               │
│ TIMESTAMPTZ created_at                                      │
│ TIMESTAMPTZ acknowledged_at                                 │
│ VARCHAR acknowledged_by                                     │
│ TIMESTAMPTZ resolved_at                                     │
│ VARCHAR resolved_by                                          │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│                  anomaly_alerts                             │
├─────────────────────────────────────────────────────────────┤
│ VARCHAR id (PK)                                             │
│ VARCHAR entity_id                                           │
│ VARCHAR entity_type                                         │
│ FLOAT anomaly_score                                         │
│ VARCHAR severity                                            │
│ TEXT description                                            │
│ TIMESTAMP detected_at                                       │
│ BOOLEAN acknowledged                                        │
│ TIMESTAMP acknowledged_at                                   │
│ TIMESTAMP created_at                                        │
└─────────────────────────────────────────────────────────────┘
```

### Data Management Tables

```
┌─────────────────────────────────────────────────────────────┐
│                  ingestion_jobs                             │
├─────────────────────────────────────────────────────────────┤
│ UUID id (PK)                                                │
│ VARCHAR source                                              │
│ JSONB source_params                                         │
│ VARCHAR status                                              │
│ TIMESTAMPTZ started_at                                      │
│ TIMESTAMPTZ finished_at                                     │
│ TEXT error_message                                          │
│ JSONB stats                                                 │
│ TIMESTAMPTZ created_at                                      │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│                   merge_history                             │
├─────────────────────────────────────────────────────────────┤
│ UUID id (PK)                                                │
│ VARCHAR merged_id                                           │
│ VARCHAR survivor_id                                         │
│ VARCHAR label                                               │
│ TIMESTAMPTZ merged_at                                       │
│ VARCHAR merged_by                                           │
│ FLOAT confidence                                            │
│ JSONB details                                               │
│ TIMESTAMPTZ undone_at                                      │
│ VARCHAR undone_by                                           │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│                  temporal_nodes                             │
├─────────────────────────────────────────────────────────────┤
│ VARCHAR node_id (PK)                                        │
│ INT version (PK)                                            │
│ TIMESTAMP valid_from                                        │
│ TIMESTAMP valid_to                                          │
│ TEXT[] labels                                               │
│ JSONB properties                                            │
│ TIMESTAMP created_at                                        │
│ VARCHAR created_by                                          │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│            temporal_relationships                           │
├─────────────────────────────────────────────────────────────┤
│ VARCHAR relationship_id (PK)                               │
│ INT version (PK)                                            │
│ TIMESTAMP valid_from                                        │
│ TIMESTAMP valid_to                                          │
│ VARCHAR type                                                │
│ VARCHAR from_node_id                                        │
│ VARCHAR to_node_id                                          │
│ JSONB properties                                            │
│ TIMESTAMP created_at                                        │
│ VARCHAR created_by                                          │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│                  change_history                             │
├─────────────────────────────────────────────────────────────┤
│ VARCHAR change_id (PK)                                      │
│ VARCHAR entity_id                                           │
│ VARCHAR entity_type                                         │
│ VARCHAR change_type                                         │
│ TIMESTAMP timestamp                                         │
│ INT version                                                 │
│ JSONB old_properties                                        │
│ JSONB new_properties                                        │
│ VARCHAR changed_by                                          │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│                 graph_snapshots                             │
├─────────────────────────────────────────────────────────────┤
│ VARCHAR snapshot_id (PK)                                    │
│ TIMESTAMP timestamp                                         │
│ TEXT description                                            │
│ INTEGER node_count                                          │
│ INTEGER relationship_count                                 │
│ TIMESTAMP created_at                                        │
│ VARCHAR created_by                                          │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│                  ml_predictions                            │
├─────────────────────────────────────────────────────────────┤
│ SERIAL id (PK)                                              │
│ VARCHAR business_id                                         │
│ VARCHAR model_version                                       │
│ TIMESTAMP prediction_date                                   │
│ FLOAT default_probability                                   │
│ VARCHAR risk_category                                       │
│ BOOLEAN actual_default                                      │
│ TIMESTAMP actual_default_date                               │
│ TIMESTAMP created_at                                        │
└─────────────────────────────────────────────────────────────┘
```

### Complete PostgreSQL ERD

```
┌─────────────┐         ┌──────────────┐
│    users    │────────▶│audit_events  │
└─────────────┘ creates └──────────────┘
                              ▲
                              │ isolates
┌─────────────┐               │
│   tenants   │───────────────┘
└──────┬──────┘
       │ has
       ▼
┌──────────────────┐
│ tenant_configs   │
└──────────────────┘

┌──────────────────────┐
│ workflow_definitions │
└──────────┬────────────┘
           │ defines
           ▼
┌──────────────────────┐
│ workflow_instances   │
└──────────┬────────────┘
           │ generates
           ▼
┌──────────────────────┐
│  workflow_history    │
└──────────────────────┘

┌──────────────┐  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐
│ risk_scores │  │fraud_alerts  │  │   alerts     │  │anomaly_alerts│
└──────────────┘  └──────────────┘  └──────────────┘  └──────────────┘

┌──────────────┐  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐
│ingestion_   │  │merge_history │  │temporal_     │  │temporal_     │
│   jobs      │  │              │  │   nodes      │  │relationships │
└──────────────┘  └──────────────┘  └──────────────┘  └──────────────┘

┌──────────────┐  ┌──────────────┐  ┌──────────────┐
│change_history│  │graph_        │  │ml_predictions│
│              │  │snapshots     │  │              │
└──────────────┘  └──────────────┘  └──────────────┘
```

---

## Neo4j Graph Schema

### Node Labels

The Neo4j graph database contains the following node types (all nodes include `tenant_id` for multi-tenancy):

```
┌─────────────────────────────────────────────────────────────┐
│                    Neo4j Node Types                         │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  Business          (id, name, tenant_id, registration_number)│
│  Person            (id, name, tenant_id, email, phone)       │
│  Transaction       (id, amount, currency, date, tenant_id)  │
│  Invoice           (id, number, amount, status, tenant_id)  │
│  Payment           (id, amount, currency, date, tenant_id)  │
│  Supplier          (id, name, tenant_id)                    │
│  Customer          (id, name, tenant_id)                    │
│  Product           (id, name, tenant_id)                    │
│  BankAccount       (id, account_number, bank_name, tenant_id)│
│  Loan              (id, principal, currency, status, tenant)│
│  Asset             (id, name, type, tenant_id)              │
│  Location          (id, address, country, tenant_id)        │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### Relationship Types

```
Person ──────OWNS─────────▶ Business
Person ───DIRECTOR_OF─────▶ Business
Business ───BUYS_FROM─────▶ Supplier
Business ───SELLS_TO──────▶ Customer
Business ────ISSUED───────▶ Invoice
Payment ────SETTLES───────▶ Invoice
Transaction ─INVOLVES─────▶ Person
Person ───HOLDS_ACCOUNT───▶ BankAccount
Business ──GRANTED_TO─────▶ Loan
Person ──────OWNS─────────▶ Asset
Business ─────OWNS─────────▶ Asset
```

### Complete Neo4j Graph Schema

```
                    ┌──────────┐
                    │  Person  │
                    └────┬─────┘
                         │
         ┌───────────────┼───────────────┐
         │               │               │
         │ OWNS          │ DIRECTOR_OF   │ INVOLVES
         ▼               ▼               ▼
    ┌──────────┐    ┌──────────┐    ┌──────────┐
    │ Business │    │ Business │    │Transaction│
    └────┬─────┘    └────┬─────┘    └──────────┘
         │               │
         │               │
    ┌────┼────┬───────────┼───────────┬────┐
    │    │    │           │           │    │
    │    │    │           │           │    │
    ▼    ▼    ▼           ▼           ▼    ▼
┌─────┐┌─────┐┌─────┐┌─────┐┌─────┐┌─────┐
│Trans││Invo ││Loan ││Asset││Bank ││Suppl│
│act  ││ice  ││     ││     ││Acct ││ier  │
└─────┘└──┬──┘└─────┘└─────┘└─────┘└─────┘
          │
          │ SETTLES
          ▼
    ┌──────────┐
    │ Payment  │
    └──────────┘

Key Properties:
- All nodes have: id (PK), tenant_id, created_at
- Business: name, registration_number, sector
- Person: name, email, phone
- Transaction: amount, currency, date, description
- Invoice: number, amount, currency, issue_date, status
- Payment: amount, currency, date
- Loan: principal, currency, start_date, status
- Asset: name, type
- BankAccount: account_number, bank_name, currency
```

---

## Cross-Database Relationships

The system uses both PostgreSQL and Neo4j, with logical relationships between them:

```
┌─────────────────────────────────────────────────────────────┐
│              PostgreSQL (Relational Data)                    │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  users                                                      │
│  tenants ──────tenant_id isolation──────────┐              │
│  tenant_configs                              │              │
│  workflow_instances ──business_id reference─┐│              │
│  risk_scores ─────────business_id reference─┼┐             │
│  fraud_alerts ────────business_id reference─┼┤             │
│  alerts                                        │             │
│  audit_events ───────resource_id reference──┼┤             │
│  anomaly_alerts                                │             │
│  ingestion_jobs                                 │             │
│  merge_history                                  │             │
│  temporal_nodes                                 │             │
│  temporal_relationships                         │             │
│  change_history                                 │             │
│  graph_snapshots                                │             │
│  ml_predictions                                 │             │
│                                                             │
└─────────────────────────────────────────────────────────────┘
         │                    │                    │
         │                    │                    │
         │ tenant_id          │ business_id        │ resource_id
         │                    │                    │
         ▼                    ▼                    ▼
┌─────────────────────────────────────────────────────────────┐
│                  Neo4j (Graph Data)                         │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  Business ◄───────────────────────────────────────────────┐│
│  Person ◄─────────────────────────────────────────────────┼┤
│  Transaction ◄───────────────────────────────────────────┘│
│  Invoice                                                    │
│  Payment                                                    │
│  Supplier                                                   │
│  Customer                                                   │
│  Product                                                    │
│  BankAccount                                                │
│  Loan                                                       │
│  Asset                                                      │
│  Location                                                   │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

**Key Relationships:**
- `tenants.tenant_id` → All Neo4j nodes have `tenant_id` property for isolation
- `workflow_instances.business_id` → References `Business.id` in Neo4j
- `risk_scores.business_id` → References `Business.id` in Neo4j
- `fraud_alerts.business_id` → References `Business.id` in Neo4j
- `audit_events.resource_id` → Can reference any Neo4j node `id`

---

## Table Descriptions

### Authentication & Authorization

#### `users`
- **Purpose**: User accounts for authentication
- **Key Fields**: `id` (UUID), `email` (unique), `password_hash`, `role`
- **Indexes**: `idx_users_email` (unique)

#### `tenants`
- **Purpose**: Multi-tenant isolation configuration
- **Key Fields**: `tenant_id` (primary key), `name`, `domain`, `status`, `config` (JSONB)
- **Indexes**: `idx_tenants_status`, `idx_tenants_domain`

#### `tenant_configs`
- **Purpose**: Per-tenant configuration key-value pairs
- **Key Fields**: `tenant_id` (FK to tenants), `key`, `value` (JSONB)
- **Relationships**: Foreign key to `tenants.tenant_id` with CASCADE delete

### Audit & Logging

#### `audit_events`
- **Purpose**: Append-only audit log for all system operations
- **Key Fields**: `id`, `event_type`, `action`, `actor_id`, `resource_type`, `resource_id`, `before_snapshot` (JSONB), `after_snapshot` (JSONB)
- **Indexes**: `idx_audit_events_created_at`, `idx_audit_events_event_type`, `idx_audit_events_actor_id`, `idx_audit_events_resource`

### Workflow Management

#### `workflow_definitions`
- **Purpose**: Workflow templates/definitions
- **Key Fields**: `id`, `key`, `version`, `definition` (JSONB)
- **Indexes**: `idx_workflow_definitions_key_version` (unique)

#### `workflow_instances`
- **Purpose**: Active workflow execution instances
- **Key Fields**: `id`, `definition_key`, `definition_version`, `business_id`, `status`, `steps` (JSONB), `context` (JSONB)
- **Relationships**: References `workflow_definitions` via `definition_key` and `definition_version`

#### `workflow_history`
- **Purpose**: Event log for workflow instances
- **Key Fields**: `id`, `instance_id` (FK), `event_type`, `payload` (JSONB)
- **Relationships**: Foreign key to `workflow_instances.id`

### Risk & Fraud

#### `risk_scores`
- **Purpose**: Historical risk score calculations
- **Key Fields**: `id`, `business_id`, `score`, `factors` (JSONB), `explanation`
- **Indexes**: `idx_risk_scores_business` (business_id, created_at DESC)

#### `fraud_alerts`
- **Purpose**: Fraud pattern detection alerts
- **Key Fields**: `id`, `business_id`, `pattern`, `severity`, `score`, `metadata` (JSONB), `status`
- **Indexes**: `idx_fraud_alerts_business`, `idx_fraud_alerts_status`

#### `alerts`
- **Purpose**: General alert system (rule-based)
- **Key Fields**: `id`, `rule_id`, `alert_type`, `severity`, `status`, `business_id`, `details` (JSONB)
- **Indexes**: `idx_alerts_business_id`, `idx_alerts_created_at`, `idx_alerts_status`, `idx_alerts_rule_id`

#### `anomaly_alerts`
- **Purpose**: ML-based anomaly detection alerts
- **Key Fields**: `id`, `entity_id`, `entity_type`, `anomaly_score`, `severity`, `acknowledged`
- **Indexes**: `idx_anomaly_alerts_entity`, `idx_anomaly_alerts_severity`, `idx_anomaly_alerts_acknowledged`

### Data Management

#### `ingestion_jobs`
- **Purpose**: Track data ingestion job status
- **Key Fields**: `id` (UUID), `source`, `source_params` (JSONB), `status`, `stats` (JSONB)
- **Indexes**: `idx_ingestion_jobs_status`, `idx_ingestion_jobs_created_at`

#### `merge_history`
- **Purpose**: Track entity deduplication/merging operations
- **Key Fields**: `id` (UUID), `merged_id`, `survivor_id`, `label`, `details` (JSONB), `undone_at`
- **Indexes**: `idx_merge_history_label_merged_at`, `idx_merge_history_survivor`, `idx_merge_history_undone`

### Temporal Versioning

#### `temporal_nodes`
- **Purpose**: Version history for graph nodes
- **Key Fields**: `node_id`, `version` (composite PK), `valid_from`, `valid_to`, `labels` (array), `properties` (JSONB)
- **Indexes**: `idx_temporal_nodes_id_time`

#### `temporal_relationships`
- **Purpose**: Version history for graph relationships
- **Key Fields**: `relationship_id`, `version` (composite PK), `valid_from`, `valid_to`, `type`, `from_node_id`, `to_node_id`, `properties` (JSONB)
- **Indexes**: `idx_temporal_relationships_id_time`

#### `change_history`
- **Purpose**: Audit trail of graph changes
- **Key Fields**: `change_id`, `entity_id`, `entity_type`, `change_type`, `old_properties` (JSONB), `new_properties` (JSONB)
- **Indexes**: `idx_change_history_entity`, `idx_change_history_timestamp`

#### `graph_snapshots`
- **Purpose**: Point-in-time snapshots of the graph
- **Key Fields**: `snapshot_id`, `timestamp`, `node_count`, `relationship_count`
- **Indexes**: `idx_snapshots_timestamp`

### Machine Learning

#### `ml_predictions`
- **Purpose**: Track ML model predictions and outcomes
- **Key Fields**: `id`, `business_id`, `model_version`, `prediction_date`, `default_probability`, `risk_category`, `actual_default`
- **Indexes**: `idx_ml_predictions_business`, `idx_ml_predictions_date`

---

## Index Strategy

### PostgreSQL Indexes

#### B-Tree Indexes (Default)
- Primary keys (automatic)
- Foreign keys
- Frequently queried columns (`created_at`, `status`, `business_id`)
- Composite indexes for common query patterns

#### Recommended GIN Indexes (Not Yet Implemented)
For optimal JSONB query performance, consider adding:
- `audit_events.before_snapshot` (GIN)
- `audit_events.after_snapshot` (GIN)
- `audit_events.extra` (GIN)
- `tenants.config` (GIN)
- `tenant_configs.value` (GIN)
- `workflow_definitions.definition` (GIN)
- `workflow_instances.steps` (GIN)
- `workflow_instances.context` (GIN)
- `fraud_alerts.metadata` (GIN)
- `merge_history.details` (GIN)

### Neo4j Indexes

#### Node Indexes
- `tenant_id` on all node labels (for multi-tenancy)
- Composite indexes: `(tenant_id, id)`, `(tenant_id, name)`, `(tenant_id, date)`

#### Relationship Indexes
- `tenant_id` on relationships (where applicable)

---

## Data Flow Summary

1. **User Authentication**: `users` table → JWT tokens
2. **Tenant Isolation**: `tenants` → All Neo4j nodes filtered by `tenant_id`
3. **Graph Operations**: Neo4j stores business relationships, transactions, ownership
4. **Risk Calculation**: Neo4j queries → `risk_scores` table
5. **Fraud Detection**: Neo4j pattern matching → `fraud_alerts` table
6. **Workflow Execution**: `workflow_definitions` → `workflow_instances` → `workflow_history`
7. **Audit Trail**: All operations → `audit_events` table
8. **Temporal Queries**: `temporal_nodes`, `temporal_relationships` for historical graph state

---

## Notes

- All Neo4j nodes include `tenant_id` property for multi-tenant isolation
- PostgreSQL tables use JSONB for flexible schema (configs, metadata, snapshots)
- Foreign key relationships are enforced in PostgreSQL
- Neo4j relationships are logical (no foreign key constraints)
- Cross-database references use `business_id`, `entity_id` as string identifiers
- Temporal versioning allows querying graph state at any point in time
