# OpenAPI/Swagger Documentation

AfricGraph provides comprehensive OpenAPI 3.0 documentation for all REST API endpoints.

## Accessing Documentation

### Interactive Swagger UI

Visit `/docs` in your browser to access the interactive Swagger UI:
```
http://localhost:8000/docs
```

Features:
- Browse all endpoints
- View request/response schemas
- Try out endpoints directly
- Test authentication

### ReDoc Documentation

Visit `/redoc` for alternative documentation format:
```
http://localhost:8000/redoc
```

### OpenAPI JSON Schema

Get the raw OpenAPI specification:
```
http://localhost:8000/openapi.json
```

## Using the Interactive Documentation

### Authentication in Swagger

1. Click "Authorize" button
2. Enter your JWT token
3. Click "Authorize"
4. All requests will include the token

### Testing Endpoints

1. Find endpoint in the list
2. Click "Try it out"
3. Fill in parameters
4. Click "Execute"
5. View response

### Example: Creating a Business

1. Navigate to `POST /api/v1/businesses`
2. Click "Try it out"
3. Enter request body:
   ```json
   {
     "id": "business-123",
     "name": "Test Business",
     "registration_number": "REG123",
     "sector": "Technology"
   }
   ```
4. Click "Execute"
5. View response and status code

## OpenAPI Schema Structure

### Tags

Endpoints are organized by tags:
- `businesses`: Business management
- `risk`: Risk assessment
- `fraud`: Fraud detection
- `graph`: Graph operations
- `search`: Search functionality
- `workflows`: Workflow management
- `backup`: Backup operations
- `auth`: Authentication

### Schemas

Common schemas defined:
- `Business`: Business entity
- `Person`: Person entity
- `Transaction`: Transaction entity
- `RiskScoreResult`: Risk assessment result
- `FraudAlert`: Fraud alert
- `ErrorResponse`: Error format

### Security Schemes

- `BearerAuth`: JWT token authentication
- `OAuth2`: OAuth2 flow (if implemented)

## Generating Client Code

### Using OpenAPI Generator

```bash
# Install OpenAPI Generator
npm install -g @openapi-generator/cli

# Generate Python client
openapi-generator generate \
  -i http://localhost:8000/openapi.json \
  -g python \
  -o ./generated/python-client

# Generate TypeScript client
openapi-generator generate \
  -i http://localhost:8000/openapi.json \
  -g typescript-axios \
  -o ./generated/typescript-client
```

### Using Swagger Codegen

```bash
# Generate Java client
swagger-codegen generate \
  -i http://localhost:8000/openapi.json \
  -l java \
  -o ./generated/java-client
```

## API Versioning

The API uses URL versioning:
- `/api/v1/`: Current stable version
- Future versions: `/api/v2/`, etc.

## Response Formats

### Success Response

```json
{
  "id": "business-123",
  "name": "Acme Corporation",
  ...
}
```

### Error Response

```json
{
  "detail": "Business not found",
  "error_code": "BUSINESS_NOT_FOUND",
  "timestamp": "2024-01-15T10:00:00Z"
}
```

### Paginated Response

```json
{
  "items": [...],
  "total": 100,
  "limit": 20,
  "offset": 0
}
```

## Best Practices

1. **Use Interactive Docs**: Test endpoints before coding
2. **Check Schemas**: Understand request/response formats
3. **Review Examples**: See example requests/responses
4. **Validate Input**: Use schema validation
5. **Handle Errors**: Check error response formats

## Exporting Documentation

### Export OpenAPI Spec

```bash
curl http://localhost:8000/openapi.json > openapi.json
```

### Generate PDF

Use tools like:
- Swagger-to-PDF
- ReDoc CLI
- OpenAPI-to-PDF

## Customization

### Adding Examples

Add examples to Pydantic models:

```python
class BusinessCreate(BaseModel):
    id: str = Field(..., example="business-123")
    name: str = Field(..., example="Acme Corporation")
```

### Adding Descriptions

```python
@router.post(
    "/businesses",
    response_model=BusinessResponse,
    summary="Create a new business",
    description="Create a new business entity in the system",
    responses={
        201: {"description": "Business created successfully"},
        400: {"description": "Invalid input"},
    }
)
```

## Integration with Tools

### Postman

1. Import OpenAPI spec:
   - File → Import
   - Select `openapi.json`
   - Configure environment variables

### Insomnia

1. Import OpenAPI spec
2. Set up authentication
3. Test endpoints

### HTTPie

```bash
# Using OpenAPI spec
httpie --spec=openapi.json POST /api/v1/businesses id=business-123 name="Test"
```
