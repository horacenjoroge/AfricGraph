# API Reference

AfricGraph provides a comprehensive REST API for interacting with the platform. The API follows RESTful principles and uses JSON for data exchange.

## Base URL

```
Production: https://yourdomain.com/api/v1
Development: http://localhost:8000/api/v1
```

## Authentication

Most endpoints require authentication using JWT tokens.

### Obtaining a Token

```http
POST /api/auth/login
Content-Type: application/json

{
  "username": "your_username",
  "password": "your_password"
}
```

**Response:**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "expires_in": 86400
}
```

### Using the Token

Include the token in the Authorization header:

```http
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

## API Endpoints

### Business Management

#### Create Business

```http
POST /api/v1/businesses
Content-Type: application/json
Authorization: Bearer {token}

{
  "id": "business-123",
  "name": "Acme Corporation",
  "registration_number": "REG123456",
  "sector": "Technology",
  "founded_date": "2020-01-01",
  "country": "KE"
}
```

**Response:** `201 Created`
```json
{
  "id": "business-123",
  "name": "Acme Corporation",
  "registration_number": "REG123456",
  "sector": "Technology",
  "founded_date": "2020-01-01",
  "country": "KE",
  "created_at": "2024-01-15T10:00:00Z"
}
```

#### Get Business

```http
GET /api/v1/businesses/{business_id}
Authorization: Bearer {token}
```

**Response:** `200 OK`
```json
{
  "id": "business-123",
  "name": "Acme Corporation",
  "registration_number": "REG123456",
  "sector": "Technology",
  "risk_score": 45.5,
  "created_at": "2024-01-15T10:00:00Z"
}
```

#### Search Businesses

```http
GET /api/v1/businesses/search?query=acme&sector=Technology&limit=20&offset=0
Authorization: Bearer {token}
```

**Response:** `200 OK`
```json
{
  "items": [
    {
      "id": "business-123",
      "name": "Acme Corporation",
      "sector": "Technology"
    }
  ],
  "total": 1,
  "limit": 20,
  "offset": 0
}
```

#### Get Business Graph

```http
GET /api/v1/businesses/{business_id}/graph?max_hops=2
Authorization: Bearer {token}
```

**Response:** `200 OK`
```json
{
  "nodes": [
    {
      "id": "business-123",
      "labels": ["Business"],
      "properties": {
        "name": "Acme Corporation"
      }
    }
  ],
  "relationships": [
    {
      "id": "rel-1",
      "type": "OWNS",
      "startNodeId": "person-1",
      "endNodeId": "business-123",
      "properties": {
        "share_percentage": 50.0
      }
    }
  ]
}
```

### Risk Assessment

#### Get Risk Assessment

```http
GET /api/v1/risk/{business_id}
Authorization: Bearer {token}
```

**Response:** `200 OK`
```json
{
  "business_id": "business-123",
  "composite_score": 45.5,
  "factor_scores": [
    {
      "name": "payment_behavior",
      "score": 30.0,
      "details": {
        "on_time_ratio": 0.9,
        "late_count": 10
      }
    },
    {
      "name": "supplier_concentration",
      "score": 60.0,
      "details": {
        "hhi_index": 0.4
      }
    }
  ],
  "explanation": "Business shows good payment behavior but high supplier concentration.",
  "timestamp": "2024-01-15T10:00:00Z"
}
```

#### Get Cash Flow Health

```http
GET /api/v1/risk/cashflow/{business_id}?horizon_months=6
Authorization: Bearer {token}
```

**Response:** `200 OK`
```json
{
  "business_id": "business-123",
  "health_score": 75.0,
  "burn_rate": 50000.0,
  "runway_months": 12,
  "has_negative_trend": false,
  "series": [
    {
      "month": "2024-01",
      "inflow": 100000.0,
      "outflow": 50000.0,
      "net": 50000.0
    }
  ],
  "forecast": [
    {
      "month": "2024-07",
      "inflow": 110000.0,
      "outflow": 55000.0,
      "net": 55000.0
    }
  ]
}
```

#### Get Supplier Risk

```http
GET /api/v1/risk/suppliers/{business_id}
Authorization: Bearer {token}
```

**Response:** `200 OK`
```json
{
  "business_id": "business-123",
  "concentration": {
    "hhi_index": 0.4,
    "top_supplier_percentage": 40.0,
    "single_point_of_failure": true
  },
  "shared_directors": [
    {
      "director_id": "person-1",
      "director_name": "John Doe",
      "businesses": ["business-123", "supplier-1"]
    }
  ],
  "late_payments": {
    "late_ratio": 0.1,
    "average_days_late": 5
  },
  "supplier_health": "moderate"
}
```

### Fraud Detection

#### Scan Business for Fraud

```http
POST /api/v1/fraud/business/{business_id}/scan
Authorization: Bearer {token}
```

**Response:** `200 OK`
```json
{
  "business_id": "business-123",
  "patterns": [
    {
      "pattern": "circular_payments",
      "description": "Circular payment detected",
      "score_contribution": 50.0,
      "context": {
        "cycle": ["business-1", "business-2", "business-3", "business-1"]
      }
    }
  ],
  "alert": {
    "id": "alert-1",
    "severity": "HIGH",
    "score": 75.0,
    "description": "Multiple fraud patterns detected",
    "created_at": "2024-01-15T10:00:00Z"
  }
}
```

#### List Fraud Alerts

```http
GET /api/v1/fraud/alerts?status=active&severity=HIGH&limit=20&offset=0
Authorization: Bearer {token}
```

**Response:** `200 OK`
```json
{
  "items": [
    {
      "id": "alert-1",
      "business_id": "business-123",
      "severity": "HIGH",
      "score": 75.0,
      "status": "ACTIVE",
      "created_at": "2024-01-15T10:00:00Z"
    }
  ],
  "total": 1,
  "limit": 20,
  "offset": 0
}
```

### Graph Operations

#### Extract Subgraph

```http
GET /api/v1/graph/subgraph/{node_id}?max_hops=2&rel_types=OWNS,SUPPLIES
Authorization: Bearer {token}
```

#### Find Shortest Path

```http
GET /api/v1/graph/path/shortest?start_id={start}&end_id={end}&max_depth=10
Authorization: Bearer {token}
```

#### Find Relationships

```http
GET /api/v1/relationships/connect/{entity_a_id}/{entity_b_id}?max_depth=4
Authorization: Bearer {token}
```

**Response:** `200 OK`
```json
{
  "connections": [
    {
      "path": {
        "nodes": [
          {"id": "entity-a", "labels": ["Business"]},
          {"id": "entity-b", "labels": ["Business"]}
        ],
        "relationships": [
          {"type": "OWNS", "id": "rel-1"}
        ]
      },
      "strength": 0.8,
      "connection_type": "direct_ownership"
    }
  ]
}
```

### Search

#### Full-Text Search

```http
GET /api/v1/search?q=acme&index=businesses&limit=20
Authorization: Bearer {token}
```

#### Autocomplete

```http
GET /api/v1/search/autocomplete?q=acm&index=businesses
Authorization: Bearer {token}
```

### Workflows

#### List Workflows

```http
GET /api/v1/workflows?status=pending&limit=20
Authorization: Bearer {token}
```

#### Approve Workflow Step

```http
POST /api/v1/workflows/{instance_id}/approve
Content-Type: application/json
Authorization: Bearer {token}

{
  "user_id": "user-123"
}
```

### Backup

#### Trigger Backup

```http
POST /api/v1/backup/run
Content-Type: application/json
Authorization: Bearer {token}

{
  "backup_type": "full",
  "cloud_upload": true
}
```

#### Get Backup Status

```http
GET /api/v1/backup/status
Authorization: Bearer {token}
```

## Error Responses

All errors follow a consistent format:

```json
{
  "detail": "Error message",
  "error_code": "ERROR_CODE",
  "timestamp": "2024-01-15T10:00:00Z"
}
```

### HTTP Status Codes

- `200 OK` - Request successful
- `201 Created` - Resource created
- `400 Bad Request` - Invalid request
- `401 Unauthorized` - Authentication required
- `403 Forbidden` - Insufficient permissions
- `404 Not Found` - Resource not found
- `422 Unprocessable Entity` - Validation error
- `500 Internal Server Error` - Server error

## Rate Limiting

API requests are rate-limited to 60 requests per minute per IP address. Rate limit headers are included in responses:

```
X-RateLimit-Limit: 60
X-RateLimit-Remaining: 59
X-RateLimit-Reset: 1642248000
```

## Pagination

List endpoints support pagination:

- `limit`: Number of items per page (default: 20, max: 100)
- `offset`: Number of items to skip (default: 0)

## Filtering and Sorting

Many endpoints support filtering and sorting:

```
GET /api/v1/businesses/search?query=acme&sector=Technology&sort=name&order=asc
```

## Interactive API Documentation

Visit `/docs` for interactive Swagger UI documentation with:
- All endpoints
- Request/response schemas
- Try-it-out functionality
- Authentication testing

## OpenAPI Specification

The complete OpenAPI 3.0 specification is available at `/openapi.json`.
