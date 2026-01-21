# GraphQL Schema Documentation

AfricGraph provides a flexible GraphQL API for querying and manipulating data. GraphQL allows clients to request exactly the data they need, reducing over-fetching and enabling efficient data loading.

## GraphQL Endpoint

```
Production: https://yourdomain.com/graphql
Development: http://localhost:8000/graphql
```

## Interactive Playground

Visit `/graphql` in your browser to access the GraphQL Playground, an interactive IDE for exploring the schema and executing queries.

## Schema Overview

### Core Types

#### Business

```graphql
type Business {
  id: ID!
  name: String!
  registrationNumber: String
  sector: String
  riskScore: Float
  owners: [Person!]!
  transactions: [Transaction!]!
  suppliers: [Business!]!
  createdAt: DateTime!
}
```

#### Person

```graphql
type Person {
  id: ID!
  name: String!
  email: String
  phone: String
  businesses: [Business!]!
}
```

#### Transaction

```graphql
type Transaction {
  id: ID!
  amount: Float!
  currency: String!
  description: String
  date: DateTime!
  from: Business
  to: Business
}
```

#### Relationship

```graphql
type Relationship {
  id: ID!
  type: String!
  from: Node!
  to: Node!
  properties: JSON
}
```

#### Path

```graphql
type Path {
  nodes: [Node!]!
  relationships: [Relationship!]!
  length: Int!
}
```

## Queries

### Get Business

```graphql
query GetBusiness {
  business(id: "business-123") {
    id
    name
    registrationNumber
    sector
    riskScore
    owners {
      id
      name
      email
    }
    transactions(limit: 10) {
      id
      amount
      description
      date
    }
  }
}
```

### Search Businesses

```graphql
query SearchBusinesses {
  businesses(query: "acme", sector: "Technology", limit: 20) {
    id
    name
    sector
    riskScore
  }
}
```

### Get Business Graph

```graphql
query GetBusinessGraph {
  business(id: "business-123") {
    id
    name
    subgraph(maxHops: 2) {
      nodes {
        id
        labels
        properties
      }
      relationships {
        id
        type
        from {
          id
        }
        to {
          id
        }
      }
    }
  }
}
```

### Find Connections

```graphql
query FindConnections {
  connections(
    entityA: "business-1"
    entityB: "business-2"
    maxDepth: 3
  ) {
    path {
      nodes {
        id
        labels
      }
      relationships {
        type
      }
      length
    }
    strength
    connectionType
  }
}
```

### Get Risk Assessment

```graphql
query GetRiskAssessment {
  business(id: "business-123") {
    id
    name
    riskAssessment {
      compositeScore
      factorScores {
        name
        score
        details
      }
      explanation
      timestamp
    }
  }
}
```

## Mutations

### Create Business

```graphql
mutation CreateBusiness {
  createBusiness(input: {
    id: "business-123"
    name: "Acme Corporation"
    registrationNumber: "REG123456"
    sector: "Technology"
  }) {
    id
    name
    createdAt
  }
}
```

### Update Business

```graphql
mutation UpdateBusiness {
  updateBusiness(
    id: "business-123"
    input: {
      name: "Updated Name"
      sector: "Finance"
    }
  ) {
    id
    name
    sector
  }
}
```

## Subscriptions

### Business Updates

```graphql
subscription BusinessUpdates {
  businessUpdates(businessId: "business-123") {
    id
    name
    riskScore
    updatedAt
  }
}
```

### Risk Score Updates

```graphql
subscription RiskScoreUpdates {
  riskScoreUpdates(businessId: "business-123") {
    businessId
    compositeScore
    timestamp
  }
}
```

## Nested Queries

GraphQL allows nested queries for efficient data fetching:

```graphql
query GetBusinessWithRelations {
  business(id: "business-123") {
    id
    name
    owners {
      id
      name
      businesses {
        id
        name
        riskScore
      }
    }
    suppliers {
      id
      name
      owners {
        id
        name
      }
    }
  }
}
```

## DataLoader Optimization

The GraphQL API uses DataLoader to prevent N+1 query problems. Related data is automatically batched and cached.

## Permissions

All queries and mutations respect ABAC (Attribute-Based Access Control) rules:

- **Admins**: Full access to all data
- **Owners**: Access to their own business data
- **Analysts**: Read-only access to non-sensitive data
- **Auditors**: Read-only access to all data

## Error Handling

GraphQL returns errors in a structured format:

```json
{
  "errors": [
    {
      "message": "Not authorized to access this business",
      "extensions": {
        "code": "PERMISSION_DENIED",
        "path": ["business"]
      }
    }
  ],
  "data": null
}
```

## Best Practices

1. **Request Only Needed Fields**: Don't over-fetch data
2. **Use Fragments**: Reuse common field selections
3. **Batch Related Queries**: Use nested queries efficiently
4. **Handle Errors**: Always check for errors in responses
5. **Use Variables**: Parameterize queries for security

## Example: Complete Business Analysis

```graphql
query CompleteBusinessAnalysis($businessId: ID!) {
  business(id: $businessId) {
    id
    name
    registrationNumber
    sector
    riskScore
    
    riskAssessment {
      compositeScore
      factorScores {
        name
        score
        details
      }
      explanation
    }
    
    owners {
      id
      name
      email
      businesses {
        id
        name
      }
    }
    
    transactions(limit: 50) {
      id
      amount
      description
      date
      to {
        id
        name
      }
    }
    
    subgraph(maxHops: 2) {
      nodes {
        id
        labels
        properties
      }
      relationships {
        type
        from {
          id
        }
        to {
          id
        }
      }
    }
  }
}
```

Variables:
```json
{
  "businessId": "business-123"
}
```
