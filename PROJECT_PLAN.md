---
name: AfricGraph MVP Plan
overview: ""
todos: []
---

# AfricGraph - Ontology-Driven Decision Platform for SMEs

## Project Overview

Build an enterprise decision intelligence system for African SMEs with graph-based data modeling, multi-source data ingestion, ABAC permissions, risk scoring, fraud detection, and workflow automation. Deployed on VPS using Docker Compose (no Kubernetes).

## Excluded Technologies

- **ML**: Tasks 25 (credit scoring), 26 (anomaly detection) - deferred
- **Blockchain**: Task 36 (blockchain audit trail) - deferred  
- **Kubernetes**: Task 30 - replaced with Docker Compose for VPS deployment

## Architecture Overview

```
┌─────────────────┐
│   React Frontend │
│   (Port 3000)   │
└────────┬────────┘
         │
         │ REST/GraphQL
         │
┌────────▼─────────────────┐
│   FastAPI Backend         │
│   (Port 8000)             │
│   - ABAC Engine           │
│   - Risk Scoring          │
│   - Fraud Detection       │
│   - Workflow Engine       │
└────────┬──────────────────┘
         │
    ┌────┴────┬──────────┬──────────┬──────────┐
    │         │          │          │          │
┌───▼───┐ ┌──▼───┐ ┌───▼───┐ ┌───▼───┐ ┌───▼───┐
│ Neo4j │ │PostgreSQL│ │ Redis │ │RabbitMQ│ │Elastic│
│ Graph │ │  Audit   │ │ Cache │ │  Queue │ │Search │
└───────┘ └──────────┘ └───────┘ └────────┘ └───────┘
```

## Implementation Plan

### Phase 1: Core Foundation (Weeks 1-3)

#### Task 1: Project Setup & Infrastructure

**Files to create:**

- `docker-compose.yml` - Services: Neo4j, PostgreSQL, Redis, RabbitMQ, Elasticsearch
- `backend/requirements.txt` - Python dependencies
- `backend/Dockerfile` - Backend container
- `frontend/package.json` - React dependencies  
- `frontend/Dockerfile` - Frontend container
- `.env.example` - Environment template
- `backend/src/config/settings.py` - Configuration management
- `backend/src/infrastructure/logging.py` - Structured logging
- `backend/src/infrastructure/database/neo4j_client.py` - Neo4j connection manager with pooling
- `backend/src/infrastructure/database/postgres_client.py` - PostgreSQL client
- `backend/src/infrastructure/cache/redis_client.py` - Redis client
- `backend/src/infrastructure/queue/rabbitmq_client.py` - RabbitMQ client

**Key features:**

- Docker Compose orchestration (no Kubernetes)
- Connection pooling for Neo4j
- Structured logging with PII redaction
- Environment-based configuration
- Health check endpoints

#### Task 2: Ontology Design

**Files to create:**

- `backend/src/domain/ontology.py` - Ontology schema definitions
- `docs/ontology.md` - Ontology documentation

**Core entities (nodes):**

- Business, Person, Transaction, Invoice, Payment, Supplier, Customer, Product, BankAccount, Loan, Asset, Location

**Relationships:**

- OWNS, DIRECTOR_OF, BUYS_FROM, SELLS_TO, ISSUED, SETTLES, INVOLVES, HOLDS_ACCOUNT, GRANTED_TO

**Schema constraints:**

- Uniqueness constraints on IDs
- Required properties
- Relationship cardinality rules

#### Task 3: Neo4j Interface Layer

**Files to create:**

- `backend/src/infrastructure/database/neo4j_client.py` - Enhanced with CRUD operations
- `backend/src/infrastructure/database/cypher_queries.py` - Reusable Cypher query templates
- `backend/src/infrastructure/database/migrations/` - Schema migration scripts
- `backend/src/infrastructure/database/migrations/runner.py` - Migration execution engine
- `backend/src/infrastructure/database/migrations/001_create_constraints.cypher` - Initial constraints
- `backend/src/infrastructure/database/migrations/002_create_indexes.cypher` - Performance indexes

**Key methods:**

- `create_node()`, `create_relationship()`, `find_node()`, `traverse()`, `find_path()`, `batch_create()`, `execute_cypher()`
- Transaction management, retry logic, pagination, health checks

**Migration features:**

- Versioned schema migrations
- Rollback support
- Migration tracking in PostgreSQL
- Idempotent migrations

#### Task 4: Entity Models

**Files to create:**

- `backend/src/domain/models/business.py`
- `backend/src/domain/models/person.py`
- `backend/src/domain/models/transaction.py`
- `backend/src/domain/models/invoice.py`
- `backend/src/domain/models/payment.py`
- `backend/src/domain/models/supplier.py`
- `backend/src/domain/models/customer.py`
- `backend/src/domain/models/product.py`
- `backend/src/domain/models/bank_account.py`
- `backend/src/domain/models/loan.py`
- `backend/src/domain/models/asset.py`
- `backend/src/domain/models/location.py`
- `backend/src/domain/models/__init__.py` - Model exports

**Features:**

- Pydantic models with validation
- Enum types for status fields
- Custom validators for business logic
- Serialization/deserialization
- Relationship property models

#### Task 5: Audit Logging

**Files to create:**

- `backend/src/infrastructure/audit/audit_logger.py` - PostgreSQL-backed audit logger
- `backend/src/infrastructure/audit/models.py` - Audit event models
- `backend/src/infrastructure/audit/middleware.py` - Request/response logging middleware

**Event types:**

- Access, Modification, Permission, Decision, System events
- Immutable append-only log
- Compliance report generation

#### Task 5a: Authentication & User Management

**Files to create:**

- `backend/src/auth/models.py` - User, Role models
- `backend/src/auth/service.py` - Authentication service
- `backend/src/auth/jwt_handler.py` - JWT token generation/validation
- `backend/src/auth/password.py` - Password hashing utilities
- `backend/src/api/routes/auth.py` - Login, register, refresh endpoints
- `backend/src/infrastructure/database/migrations/001_create_users.sql` - User table migration

**Features:**

- JWT-based authentication
- Password hashing (bcrypt)
- Role-based user management
- Token refresh mechanism
- User registration/login endpoints

### Phase 2: Data Ingestion (Weeks 4-6)

#### Task 6: Mobile Money Connectors

**Files to create:**

- `backend/src/ingestion/connectors/mobile_money/mpesa.py`
- `backend/src/ingestion/connectors/mobile_money/mtn.py`
- `backend/src/ingestion/connectors/mobile_money/airtel.py`
- `backend/src/ingestion/parsers/csv_parser.py`
- `backend/src/ingestion/classifiers/transaction_classifier.py`

**Features:**

- CSV parsing for M-Pesa, MTN, Airtel
- Transaction classification
- Counterparty extraction
- Duplicate detection

#### Task 7: Accounting System Connectors

**Files to create:**

- `backend/src/ingestion/connectors/xero/__init__.py`
- `backend/src/ingestion/connectors/quickbooks/__init__.py`
- `backend/src/ingestion/connectors/odoo/__init__.py`
- `backend/src/ingestion/connectors/base.py` - Base connector interface
- `backend/src/ingestion/oauth/oauth_manager.py` - OAuth2 token management

**Features:**

- OAuth2 integration
- Incremental sync
- Rate limiting
- Error retry logic

#### Task 8: Data Normalization

**Files to create:**

- `backend/src/ingestion/normalizers/base.py`
- `backend/src/ingestion/normalizers/mobile_money_normalizer.py`
- `backend/src/ingestion/normalizers/accounting_normalizer.py`
- `backend/src/ingestion/resolvers/entity_resolver.py` - Entity deduplication
- `backend/src/ingestion/utils/fuzzy_match.py` - Fuzzy matching utilities

**Features:**

- Currency conversion
- Date/time standardization
- Phone/address normalization
- Entity resolution

#### Task 9: Ingestion Pipeline

**Files to create:**

- `backend/src/ingestion/pipeline/ingestion_pipeline.py`
- `backend/src/ingestion/pipeline/tasks.py` - Celery tasks
- `backend/src/ingestion/pipeline/validators.py`
- `backend/src/ingestion/pipeline/graph_writer.py`
- `backend/src/ingestion/pipeline/dead_letter_queue.py`

**Features:**

- Celery task queue
- ETL pipeline with validation
- Failed job handling
- Scheduled ingestion (cron)
- Status tracking API

#### Task 10: Entity Deduplication

**Files to create:**

- `backend/src/ingestion/deduplication/detector.py`
- `backend/src/ingestion/deduplication/merger.py`
- `backend/src/ingestion/deduplication/similarity.py` - Levenshtein, phone matching

**Features:**

- Fuzzy name matching
- Merge candidates API
- Manual merge approval
- Merge history tracking

### Phase 3: Permissions & Security (Weeks 7-8)

#### Task 11: ABAC Engine

**Files to create:**

- `backend/src/security/abac/engine.py` - Policy evaluation engine
- `backend/src/security/abac/policies.py` - Policy definitions
- `backend/src/security/abac/attributes.py` - Subject/Resource/Environment attributes
- `backend/src/security/abac/cache.py` - Permission caching

**Features:**

- Policy evaluation logic
- Query-level permission filtering
- Audit all permission decisions
- Time/IP-based restrictions

#### Task 12: Permission-Aware Queries

**Files to create:**

- `backend/src/security/middleware/permission_middleware.py`
- `backend/src/security/query_rewriter.py` - Inject permission clauses
- `backend/src/security/filters/node_filter.py`
- `backend/src/security/filters/relationship_filter.py`

**Features:**

- Automatic permission clause injection
- Result filtering
- Permission-aware pagination

### Phase 4: Risk & Fraud Detection (Weeks 9-11)

#### Task 13: Risk Scoring Engine

**Files to create:**

- `backend/src/risk/scoring/engine.py` - Main risk calculator
- `backend/src/risk/scoring/payment_analyzer.py`
- `backend/src/risk/scoring/supplier_analyzer.py`
- `backend/src/risk/scoring/ownership_analyzer.py`
- `backend/src/risk/scoring/cashflow_analyzer.py`
- `backend/src/risk/scoring/network_analyzer.py`
- `backend/src/risk/scoring/explainer.py` - Risk explanation generator

**Risk factors (weights):**

- Payment behavior: 40%
- Supplier concentration: 25%
- Ownership complexity: 15%
- Cash flow health: 15%
- Network exposure: 5%

#### Task 14: Fraud Detection

**Files to create:**

- `backend/src/fraud/detector.py` - Pattern detection engine
- `backend/src/fraud/patterns/circular_payments.py`
- `backend/src/fraud/patterns/shell_companies.py`
- `backend/src/fraud/patterns/duplicate_invoices.py`
- `backend/src/fraud/patterns/invoice_fraud.py`
- `backend/src/fraud/patterns/structuring.py`
- `backend/src/fraud/alerts.py` - Alert generation

**Patterns:**

- Circular payments (A→B→C→A)
- Shell companies
- Duplicate invoices
- Invoice fraud
- Structuring/smurfing

#### Task 15: Cash Health Calculator

**Files to create:**

- `backend/src/risk/cashflow/calculator.py`
- `backend/src/risk/cashflow/forecaster.py`
- `backend/src/risk/cashflow/trend_analyzer.py`

**Features:**

- Cash flow trend calculation
- Runway estimation
- Burn rate
- Health score (0-100)

#### Task 16: Supplier Risk Analysis

**Files to create:**

- `backend/src/risk/supplier/analyzer.py`
- `backend/src/risk/supplier/concentration.py` - HHI index
- `backend/src/risk/supplier/dependency_graph.py`

**Features:**

- Supplier concentration ratio
- Shared director detection
- Single point of failure identification

### Phase 5: Workflow Engine (Weeks 12-13)

#### Task 17: Workflow Engine

**Files to create:**

- `backend/src/workflows/engine.py` - State machine
- `backend/src/workflows/models.py` - Workflow definitions
- `backend/src/workflows/executor.py` - Step execution
- `backend/src/workflows/approval.py` - Approval system
- `backend/src/workflows/notifications.py` - Email/SMS/Slack
- `backend/src/workflows/templates.py` - Pre-built workflows

**Workflows:**

- Supplier onboarding
- Large payment approval
- Credit limit increase
- High-risk business review

#### Task 18: Alert System

**Files to create:**

- `backend/src/alerts/engine.py` - Alert rule engine
- `backend/src/alerts/rules.py` - Alert rule definitions
- `backend/src/alerts/routing.py` - Email/Slack/webhook routing
- `backend/src/alerts/cooldown.py` - Prevent spam

**Alert types:**

- High risk score (>80)
- Payment default
- Fraud pattern
- Negative cash flow
- Supplier concentration risk

### Phase 6: Graph Reasoning (Week 14)

#### Task 19: Graph Traversal API

**Files to create:**

- `backend/src/graph/traversal.py` - Advanced graph queries
- `backend/src/graph/path_finding.py`
- `backend/src/graph/metrics.py` - Centrality, PageRank
- `backend/src/graph/export.py` - Visualization export

**Features:**

- Subgraph extraction (N-hop)
- Path finding
- Cycle detection
- Connected components

#### Task 20: Relationship Search

**Files to create:**

- `backend/src/graph/relationship_search.py`
- `backend/src/graph/common_ownership.py`
- `backend/src/graph/shared_directors.py`

**Features:**

- "How are X and Y connected?" queries
- Indirect relationship paths
- Relationship strength scoring

### Phase 7: API Layer (Weeks 15-16)

#### Task 21: REST API

**Files to create:**

- `backend/src/api/main.py` - FastAPI app
- `backend/src/api/routes/businesses.py`
- `backend/src/api/routes/ingestion.py`
- `backend/src/api/routes/risk.py`
- `backend/src/api/routes/fraud.py`
- `backend/src/api/routes/workflows.py`
- `backend/src/api/routes/audit.py`
- `backend/src/api/routes/relationships.py`
- `backend/src/api/middleware/auth.py` - JWT authentication
- `backend/src/api/middleware/rate_limit.py`
- `backend/src/api/schemas/` - Pydantic request/response schemas

**Endpoints:**

- `/api/v1/businesses` - CRUD operations
- `/api/v1/businesses/:id/graph` - Subgraph
- `/api/v1/ingest/mobile-money` - CSV upload
- `/api/v1/ingest/xero` - Trigger sync
- `/api/v1/risk/:business_id` - Risk assessment
- `/api/v1/fraud/:business_id` - Fraud alerts
- `/api/v1/workflows` - Workflow management
- `/api/v1/audit` - Audit log queries
- `/api/v1/relationships` - Relationship search

#### Task 22: GraphQL API

**Files to create:**

- `backend/src/api/graphql/schema.py` - GraphQL schema
- `backend/src/api/graphql/resolvers/` - Resolvers for all entities
- `backend/src/api/graphql/dataloader.py` - N+1 query optimization
- `backend/src/api/graphql/subscriptions.py` - Real-time updates

### Phase 8: Frontend (Week 17)

#### Task 23: React Dashboard

**Files to create:**

- `frontend/src/App.jsx` - Main app
- `frontend/src/pages/Dashboard.jsx`
- `frontend/src/pages/BusinessSearch.jsx`
- `frontend/src/pages/BusinessDetail.jsx`
- `frontend/src/pages/GraphExplorer.jsx`
- `frontend/src/pages/RiskAnalysis.jsx`
- `frontend/src/pages/FraudAlerts.jsx`
- `frontend/src/pages/Workflows.jsx`
- `frontend/src/pages/AuditLogs.jsx`
- `frontend/src/components/GraphVisualization.jsx` - Force-directed graph
- `frontend/src/components/RiskGauge.jsx`
- `frontend/src/components/DataTable.jsx`
- `frontend/src/services/api.js` - API client
- `frontend/src/services/websocket.js` - Real-time updates

**Tech stack:**

- React, React Router, React Hook Form
- react-force-graph (graph visualization)
- Recharts (charts)
- Axios (HTTP client)

#### Task 24: Graph Visualization

**Files to create:**

- `frontend/src/components/GraphVisualization/ForceGraph.jsx`
- `frontend/src/components/GraphVisualization/NodeDetails.jsx`
- `frontend/src/components/GraphVisualization/Controls.jsx`

**Features:**

- Force-directed layout
- Node coloring by type/risk
- Node sizing by importance
- Export as image

### Phase 9: Production Ready (Weeks 18-20)

#### Task 27: Caching Layer

**Files to create:**

- `backend/src/infrastructure/cache/strategies.py` - Cache-aside, write-through
- `backend/src/infrastructure/cache/invalidation.py`
- `backend/src/infrastructure/cache/warming.py`

**Cache targets:**

- Graph query results (5-30 min TTL)
- Permission decisions (1 hour TTL)
- Risk scores (30 min TTL)
- User sessions (24 hour TTL)

#### Task 28: Elasticsearch Integration

**Files to create:**

- `backend/src/infrastructure/search/elasticsearch_client.py`
- `backend/src/infrastructure/search/indexer.py`
- `backend/src/api/routes/search.py`

**Features:**

- Full-text search
- Faceted search
- Autocomplete
- Geospatial search

#### Task 29: Monitoring & Observability

**Files to create:**

- `backend/src/infrastructure/monitoring/metrics.py` - Prometheus metrics
- `docker-compose.monitoring.yml` - Prometheus + Grafana
- `grafana/dashboards/` - Pre-built dashboards

**Metrics:**

- API request rate, latency, errors
- Neo4j query time
- Cache hit rate
- Ingestion job success/failure

#### Task 31: Backup & Disaster Recovery

**Files to create:**

- `scripts/backup_neo4j.sh`
- `scripts/backup_postgres.sh`
- `scripts/restore.sh`
- `docker-compose.backup.yml` - Automated backup service

**Features:**

- Daily Neo4j backups
- PostgreSQL backups
- S3/cloud storage integration
- Restore procedures

#### Task 32: Comprehensive Testing

**Files to create:**

- `backend/tests/unit/` - Unit tests
- `backend/tests/integration/` - Integration tests
- `backend/tests/e2e/` - End-to-end tests
- `backend/pytest.ini` - Test configuration
- `locustfile.py` - Load testing

**Coverage goal:** 85%+

#### Task 33: Documentation

**Files to create:**

- `README.md` - Project overview
- `docs/architecture.md` - Architecture diagrams
- `docs/api.md` - API reference
- `docs/deployment.md` - VPS deployment guide
- `docs/development.md` - Developer guide
- `docs/runbooks.md` - Operational procedures
- `docs/ontology.md` - Graph ontology reference
- `docs/security.md` - Security and compliance guide

#### Task 33a: Database Seeding & Sample Data

**Files to create:**

- `backend/scripts/seed_data.py` - Data seeding script
- `backend/scripts/sample_data/` - Sample data files (CSV, JSON)
- `backend/scripts/fixtures/` - Test fixtures

**Features:**

- Sample businesses, persons, transactions
- Test user accounts
- Demo workflows
- Sample risk scores
- Development/test data generation

### Bonus Tasks (Deferred)

#### Task 34: Time-Travel Queries

- Version all nodes/relationships
- Point-in-time graph snapshots
- **Note:** Complex, defer if time-constrained

#### Task 35: Multi-Tenancy

- Tenant isolation in graph
- Cross-tenant analytics
- **Note:** Can be added later if needed

#### Task 37: Natural Language Queries

- NLP parser for business questions
- Query generation from natural language
- LLM integration (GPT-4) - **Deferred until ML phase**
- Query validation
- Result explanation
- **Note:** Requires ML/NLP expertise, defer for now

## Deployment Strategy (VPS)

**Docker Compose Setup:**

- Single `docker-compose.yml` file for all services
- Service dependencies and startup order
- Health checks for all services
- Volume mounts for persistent data
- Environment variable management

**Files to create:**

- `docker-compose.yml` - Main orchestration file
- `docker-compose.prod.yml` - Production overrides
- `nginx/nginx.conf` - Reverse proxy configuration
- `nginx/Dockerfile` - Nginx container
- `.env.example` - Environment template
- `scripts/deploy.sh` - Deployment script
- `scripts/health_check.sh` - Health check script

**Service Configuration:**

```yaml
Services:
 - neo4j: Graph database (port 7474, 7687)
 - postgres: Audit logs (port 5432)
 - redis: Caching (port 6379)
 - rabbitmq: Message queue (port 5672, 15672)
 - elasticsearch: Search (port 9200)
 - backend: FastAPI app (port 8000)
 - frontend: React app (port 3000)
 - nginx: Reverse proxy (port 80, 443)
 - celery: Background workers
```

**Deployment Steps:**

1. **VPS Requirements:**
   - Minimum: 4GB RAM, 2 CPU cores, 50GB storage
   - Recommended: 8GB RAM, 4 CPU cores, 100GB storage
   - Ubuntu 22.04 LTS or Debian 11+

2. **Initial Setup:**
   ```bash
   # Install Docker and Docker Compose
   curl -fsSL https://get.docker.com -o get-docker.sh
   sh get-docker.sh
   sudo apt-get install docker-compose-plugin
   
   # Clone repository
   git clone <repo-url>
   cd AfricGraph
   
   # Configure environment
   cp .env.example .env
   # Edit .env with your configuration
   ```

3. **Start Services:**
   ```bash
   # Start all services
   docker compose up -d
   
   # Check service health
   ./scripts/health_check.sh
   
   # View logs
   docker compose logs -f
   ```

4. **Nginx Configuration:**
   - SSL certificate setup (Let's Encrypt)
   - Reverse proxy to backend (port 8000)
   - Static file serving for frontend
   - Rate limiting configuration

5. **Database Initialization:**
   ```bash
   # Run Neo4j migrations
   docker compose exec backend python -m backend.src.infrastructure.database.migrations.run_migrations
   
   # Seed initial data (optional)
   docker compose exec backend python -m backend.scripts.seed_data
   ```

6. **Monitoring Setup:**
   ```bash
   # Start monitoring stack
   docker compose -f docker-compose.monitoring.yml up -d
   
   # Access Grafana: http://your-vps-ip:3001
   ```

**Environment Variables (.env):**

```bash
# Database
NEO4J_URI=bolt://neo4j:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=<secure-password>
POSTGRES_HOST=postgres
POSTGRES_DB=africgraph
POSTGRES_USER=africgraph
POSTGRES_PASSWORD=<secure-password>

# Redis
REDIS_HOST=redis
REDIS_PORT=6379

# RabbitMQ
RABBITMQ_HOST=rabbitmq
RABBITMQ_USER=africgraph
RABBITMQ_PASSWORD=<secure-password>

# Elasticsearch
ELASTICSEARCH_HOST=elasticsearch
ELASTICSEARCH_PORT=9200

# JWT
JWT_SECRET_KEY=<generate-secure-key>
JWT_ALGORITHM=HS256
JWT_EXPIRATION_HOURS=24

# API
API_HOST=0.0.0.0
API_PORT=8000
CORS_ORIGINS=http://localhost:3000,https://yourdomain.com

# Email (for notifications)
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=<email>
SMTP_PASSWORD=<app-password>

# OAuth (for accounting connectors)
XERO_CLIENT_ID=<xero-client-id>
XERO_CLIENT_SECRET=<xero-client-secret>
QUICKBOOKS_CLIENT_ID=<quickbooks-client-id>
QUICKBOOKS_CLIENT_SECRET=<quickbooks-client-secret>
```

**Backup Strategy:**

- Daily automated backups via cron
- Neo4j: `neo4j-admin backup` command
- PostgreSQL: `pg_dump` command
- Backup retention: 30 days local, 90 days cloud
- Test restore procedures monthly

**Security Considerations:**

- Firewall rules (UFW): Only allow ports 80, 443, 22
- SSL/TLS certificates (Let's Encrypt)
- Regular security updates
- Database password rotation
- JWT secret key rotation
- Rate limiting on API endpoints
- CORS configuration
- Input validation and sanitization

**Scaling Considerations:**

- Horizontal scaling: Multiple backend instances behind nginx
- Redis cluster for distributed caching
- RabbitMQ cluster for high availability
- Neo4j cluster (Enterprise) for production
- Load balancer for multiple VPS instances

**Maintenance:**

- Log rotation configuration
- Disk space monitoring
- Database optimization (indexes, query tuning)
- Regular dependency updates
- Security patch management
