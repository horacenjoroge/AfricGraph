# Architecture Overview

## System Architecture

AfricGraph is an ontology-driven decision platform for SMEs built on a graph database foundation. The system is designed to provide risk assessment, fraud detection, and relationship analysis capabilities.

## High-Level Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                        Frontend Layer                        │
│  React + TypeScript + Vite + Tailwind CSS                   │
│  - Dashboard, Graph Explorer, Risk Analysis                  │
└──────────────────────┬──────────────────────────────────────┘
                        │ HTTPS
┌───────────────────────▼──────────────────────────────────────┐
│                      API Gateway                               │
│  FastAPI + Nginx (Reverse Proxy + SSL)                        │
│  - REST API (/api/v1)                                         │
│  - GraphQL API (/graphql)                                     │
│  - Authentication & Authorization                             │
└───────┬───────────────────────────────────────┬──────────────┘
        │                                       │
┌───────▼────────┐                    ┌─────────▼──────────┐
│  Application   │                    │   Background Jobs   │
│    Services    │                    │   (Celery)          │
│                │                    │                     │
│  - Risk        │                    │  - Data Ingestion   │
│  - Fraud       │                    │  - ML Training      │
│  - Workflows   │                    │  - Cache Warming    │
│  - Alerts      │                    │                     │
└───────┬────────┘                    └─────────┬──────────┘
        │                                       │
┌───────▼───────────────────────────────────────▼──────────┐
│                    Data Layer                                │
│                                                              │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐   │
│  │  Neo4j   │  │PostgreSQL│  │  Redis   │  │Elastic-  │   │
│  │  Graph   │  │  Relational│ │  Cache   │  │  search  │   │
│  │ Database │  │  Database │  │          │  │  Search  │   │
│  └──────────┘  └──────────┘  └──────────┘  └──────────┘   │
│                                                              │
└──────────────────────────────────────────────────────────────┘
```

## Component Architecture

### Frontend

- **Framework**: React 18 with TypeScript
- **Build Tool**: Vite
- **Styling**: Tailwind CSS with custom "Deep Space" theme
- **Visualization**: react-force-graph-3d for 3D graph visualization
- **Charts**: Recharts for data visualization
- **Animations**: Framer Motion for transitions

### Backend

- **Framework**: FastAPI (Python 3.11)
- **API**: REST (OpenAPI/Swagger) and GraphQL (Strawberry)
- **Authentication**: JWT tokens
- **Authorization**: ABAC (Attribute-Based Access Control)

### Data Layer

#### Neo4j (Graph Database)
- **Purpose**: Store business relationships, transactions, ownership structures
- **Features**: APOC procedures, Cypher queries, graph algorithms
- **Use Cases**: 
  - Relationship traversal
  - Pattern detection (fraud, circular payments)
  - Network analysis
  - Path finding

#### PostgreSQL (Relational Database)
- **Purpose**: Store structured data, audit logs, workflow state
- **Use Cases**:
  - User management
  - Audit logs
  - Workflow instances
  - ML model metadata
  - Risk score history

#### Redis (Cache)
- **Purpose**: Performance optimization, session management
- **Use Cases**:
  - Graph query results (5-30 min TTL)
  - Permission decisions (1 hour TTL)
  - Risk scores (30 min TTL)
  - User sessions (24 hour TTL)
  - API responses (variable TTL)

#### Elasticsearch (Search)
- **Purpose**: Full-text search and indexing
- **Use Cases**:
  - Business search
  - Person search
  - Transaction search
  - Autocomplete
  - Geospatial search

### Message Queue

- **RabbitMQ**: Asynchronous task processing
- **Celery**: Task queue for background jobs
- **Use Cases**:
  - Data ingestion
  - ML model training
  - Cache warming
  - Email notifications

## Data Flow

### Risk Assessment Flow

```
User Request → API Gateway → Risk Service
                                    │
                                    ├─→ Neo4j (Query payment history)
                                    ├─→ Neo4j (Query supplier data)
                                    ├─→ Neo4j (Query ownership structure)
                                    ├─→ PostgreSQL (Get cash flow data)
                                    │
                                    └─→ Calculate Composite Risk Score
                                         │
                                         ├─→ Cache Result (Redis)
                                         └─→ Return to User
```

### Fraud Detection Flow

```
Scheduled Job → Fraud Detector
                    │
                    ├─→ Pattern 1: Circular Payments (Neo4j)
                    ├─→ Pattern 2: Shell Companies (Neo4j)
                    ├─→ Pattern 3: Duplicate Invoices (Neo4j)
                    ├─→ Pattern 4: Invoice Fraud (Neo4j)
                    ├─→ Pattern 5: Structuring (Neo4j)
                    ├─→ Pattern 6: Round Amounts (Neo4j)
                    └─→ Pattern 7: Unusual Patterns (Neo4j)
                         │
                         └─→ Aggregate Scores → Create Alert
                              │
                              └─→ Alert System → Notify (Email/Slack)
```

### Graph Query Flow

```
GraphQL/REST Request → Query Rewriter (ABAC)
                            │
                            └─→ Inject Permission Filters
                                 │
                                 └─→ Neo4j Query
                                      │
                                      └─→ Cache Result (if applicable)
                                           │
                                           └─→ Return to Client
```

## Security Architecture

### Authentication
- JWT tokens with configurable expiration
- Password hashing with bcrypt
- Session management in Redis

### Authorization (ABAC)
- Subject attributes (user, role, business_id)
- Resource attributes (type, id, owner, sensitivity)
- Environment attributes (time, IP, location)
- Policy engine evaluates access based on attributes

### Data Protection
- Encryption at rest (database level)
- Encryption in transit (TLS/SSL)
- Sensitive data masking in logs
- Audit logging for all access

## Scalability

### Horizontal Scaling
- Stateless API servers (can scale horizontally)
- Load balancer (Nginx) for request distribution
- Database read replicas (Neo4j, PostgreSQL)

### Caching Strategy
- Multi-layer caching (Redis, application-level)
- Cache warming for frequently accessed data
- Cache invalidation on updates

### Performance Optimization
- Graph query result caching
- Permission decision caching
- Database connection pooling
- Async task processing

## Monitoring & Observability

### Metrics (Prometheus)
- API request rate, latency, errors
- Database query performance
- Cache hit rates
- System resources (CPU, memory, disk)

### Logging
- Structured logging (JSON format)
- Log levels (DEBUG, INFO, WARNING, ERROR)
- Centralized log aggregation

### Alerting
- High error rates
- Slow queries
- High-risk businesses
- System failures

## Deployment Architecture

### Production Environment
- VPS with Docker Compose
- Nginx reverse proxy with SSL
- Systemd services for auto-start
- Automated backups (daily)
- Health checks and monitoring

### CI/CD Pipeline
- GitHub Actions for automated testing
- Automated deployment on merge to main
- Health checks after deployment
- Rollback capability

## Technology Stack Summary

| Layer | Technology |
|-------|-----------|
| Frontend | React, TypeScript, Vite, Tailwind CSS |
| Backend | FastAPI, Python 3.11 |
| Graph DB | Neo4j 5.15 |
| Relational DB | PostgreSQL 15 |
| Cache | Redis 7 |
| Search | Elasticsearch 8.11 |
| Message Queue | RabbitMQ 3, Celery |
| ML | Scikit-learn, XGBoost, SHAP |
| Monitoring | Prometheus, Grafana |
| Deployment | Docker, Docker Compose, Nginx |

## Design Principles

1. **Graph-First**: Leverage graph database for relationship analysis
2. **Security by Design**: ABAC for fine-grained access control
3. **Performance**: Multi-layer caching and optimization
4. **Observability**: Comprehensive monitoring and logging
5. **Scalability**: Stateless services, horizontal scaling
6. **Reliability**: Automated backups, health checks, disaster recovery
