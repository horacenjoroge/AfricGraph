# Developer Guide

This guide helps developers set up, understand, and contribute to the AfricGraph codebase.

## Development Setup

### Prerequisites

- Python 3.11+
- Node.js 18+
- Docker and Docker Compose
- PostgreSQL 15+
- Neo4j 5.15+
- Redis 7+
- Elasticsearch 8.11+

### Local Development

#### 1. Clone Repository

```bash
git clone https://github.com/yourusername/AfricGraph.git
cd AfricGraph
```

#### 2. Backend Setup

```bash
cd backend

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Set up environment variables
cp .env.example .env
# Edit .env with your local configuration
```

#### 3. Frontend Setup

```bash
cd frontend

# Install dependencies
npm install

# Start development server
npm run dev
```

#### 4. Start Services with Docker

```bash
# From project root
docker-compose up -d
```

This starts:
- Neo4j (port 7474, 7687)
- PostgreSQL (port 5432)
- Redis (port 6379)
- RabbitMQ (port 5672, 15672)
- Elasticsearch (port 9200)

#### 5. Run Backend

```bash
cd backend
uvicorn src.api.main:app --reload --host 0.0.0.0 --port 8000
```

## Project Structure

```
AfricGraph/
├── backend/
│   ├── src/
│   │   ├── api/              # API routes and schemas
│   │   ├── auth/             # Authentication
│   │   ├── security/         # ABAC, permissions
│   │   ├── risk/             # Risk scoring
│   │   ├── fraud/            # Fraud detection
│   │   ├── graph/            # Graph operations
│   │   ├── graphql/          # GraphQL API
│   │   ├── ml/               # Machine learning
│   │   ├── monitoring/       # Metrics and monitoring
│   │   ├── backup/           # Backup utilities
│   │   └── infrastructure/   # Database, cache, queue clients
│   ├── tests/                # Test suite
│   └── requirements.txt      # Python dependencies
├── frontend/
│   ├── src/
│   │   ├── components/       # React components
│   │   ├── pages/            # Page components
│   │   ├── utils/            # Utilities
│   │   └── hooks/            # React hooks
│   └── package.json          # Node dependencies
└── deployment/               # Deployment scripts and configs
```

## Code Style

### Python

- Follow PEP 8
- Use type hints
- Maximum line length: 100 characters
- Use `black` for formatting (optional)

### TypeScript/React

- Use TypeScript strict mode
- Follow React best practices
- Use functional components with hooks
- ESLint configuration provided

## Testing

### Running Tests

```bash
# All tests
pytest

# Unit tests only
pytest -m unit

# Integration tests
pytest -m integration

# With coverage
pytest --cov=src --cov-report=html
```

### Writing Tests

1. **Unit Tests**: Test individual functions
2. **Integration Tests**: Test API endpoints and database
3. **E2E Tests**: Test complete user journeys

Example:

```python
@pytest.mark.unit
def test_my_function():
    """Test my function."""
    result = my_function(input)
    assert result == expected
```

## Database Development

### Neo4j

Access Neo4j Browser: `http://localhost:7474`

Example Cypher query:

```cypher
MATCH (b:Business {id: "business-123"})
RETURN b
```

### PostgreSQL

Connect:
```bash
psql -h localhost -U africgraph -d africgraph
```

### Running Migrations

```bash
# Alembic migrations (if using)
alembic upgrade head
```

## API Development

### Adding a New Endpoint

1. Create route in `src/api/routes/`
2. Define Pydantic schemas in `src/api/schemas/`
3. Implement service logic in `src/api/services/`
4. Add tests in `tests/integration/`

Example:

```python
# src/api/routes/my_feature.py
from fastapi import APIRouter
from src.api.schemas.my_feature import MyFeatureRequest, MyFeatureResponse

router = APIRouter(prefix="/my-feature", tags=["my-feature"])

@router.post("", response_model=MyFeatureResponse)
def create_feature(request: MyFeatureRequest):
    # Implementation
    pass
```

## GraphQL Development

### Adding a New Query

1. Define type in `src/graphql/types/`
2. Add resolver in `src/graphql/resolvers/`
3. Update schema in `src/graphql/schema.py`

Example:

```python
# src/graphql/types/my_type.py
import strawberry

@strawberry.type
class MyType:
    id: str
    name: str

# src/graphql/resolvers/queries.py
@strawberry.field
def my_query(self, id: str) -> MyType:
    # Implementation
    pass
```

## Adding New Features

### Risk Scoring

1. Create analyzer in `src/risk/scoring/`
2. Add to `src/risk/scoring/engine.py`
3. Update weights if needed
4. Add tests

### Fraud Detection

1. Create pattern detector in `src/fraud/patterns/`
2. Add to `src/fraud/detector.py`
3. Define pattern in `src/fraud/models.py`
4. Add tests

### Graph Operations

1. Add Cypher queries in `src/infrastructure/database/cypher_queries.py`
2. Create functions in `src/graph/`
3. Add API endpoints
4. Add tests

## Debugging

### Backend Debugging

```bash
# Run with debug logging
LOG_LEVEL=DEBUG uvicorn src.api.main:app --reload

# Use Python debugger
import pdb; pdb.set_trace()
```

### Frontend Debugging

- Use React DevTools browser extension
- Check browser console
- Use `console.log()` for debugging

### Database Debugging

- Enable query logging in Neo4j
- Check PostgreSQL logs
- Use EXPLAIN ANALYZE for slow queries

## Performance Optimization

### Caching

- Use `@cached_risk_score` for risk calculations
- Use `@cached_graph_query` for graph queries
- Configure TTL in `src/cache/config.py`

### Database Optimization

- Add indexes in Neo4j
- Optimize Cypher queries
- Use connection pooling

### Frontend Optimization

- Use React.memo for expensive components
- Lazy load routes
- Optimize bundle size

## Contributing

### Workflow

1. Create a feature branch
2. Make changes
3. Write tests
4. Ensure tests pass
5. Submit pull request

### Pull Request Checklist

- [ ] Tests added/updated
- [ ] Documentation updated
- [ ] Code follows style guide
- [ ] All tests pass
- [ ] Coverage maintained (85%+)

## Common Tasks

### Adding Dependencies

```bash
# Python
pip install package-name
pip freeze > requirements.txt

# Node
npm install package-name
```

### Database Schema Changes

1. Update domain models
2. Create migration (if using Alembic)
3. Update tests
4. Document changes

### Environment Variables

Add to:
- `backend/.env.example`
- `deployment/env.template`
- Documentation

## Resources

- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [Neo4j Cypher Manual](https://neo4j.com/docs/cypher-manual/)
- [React Documentation](https://react.dev/)
- [GraphQL Documentation](https://graphql.org/)

## Getting Help

- Check existing documentation
- Review code comments
- Ask in team chat
- Open an issue on GitHub
