# AfricGraph Ontology

Graph schema for the AfricGraph SME decision platform. The ontology defines node types (labels), relationship types, required properties, uniqueness constraints, and relationship cardinality.

## Node Labels (Entities)

| Label        | Description                    | Required properties                                  |
|-------------|--------------------------------|------------------------------------------------------|
| Business    | Registered company or venture  | id, name, created_at                                 |
| Person      | Individual (director, owner)   | id, name, created_at                                 |
| Transaction | Money or value movement        | id, amount, currency, date, created_at               |
| Invoice     | Billing document               | id, number, amount, currency, issue_date, status, created_at |
| Payment     | Settlement of an obligation    | id, amount, currency, date, created_at               |
| Supplier    | Entity that sells to a business| id, name, created_at                                 |
| Customer    | Entity that buys from a business| id, name, created_at                                |
| Product     | Good or service                | id, name, created_at                                 |
| BankAccount | Financial account              | id, account_number, bank_name, currency, created_at  |
| Loan        | Credit facility                | id, principal, currency, start_date, status, created_at |
| Asset       | Owned resource (physical, etc.)| id, name, type, created_at                           |
| Location    | Physical or registered address | id, address, country, created_at                     |

## Relationships

| Type          | From        | To          | Properties       | Description                              |
|---------------|-------------|-------------|------------------|------------------------------------------|
| OWNS          | Person      | Business    | percentage, since| Ownership share and start date           |
| OWNS          | Person, Business | Asset   | percentage, since| Ownership of an asset                    |
| DIRECTOR_OF   | Person      | Business    | role, since      | Directorship role and start date         |
| BUYS_FROM     | Business    | Supplier    | since            | Procurement start date                   |
| SELLS_TO      | Business    | Customer    | -                | Sales relationship                       |
| ISSUED        | Business    | Invoice     | -                | Invoice issuer                           |
| ISSUED        | Supplier    | Invoice     | -                | Invoice issuer                           |
| SETTLES       | Payment     | Invoice     | -                | Payment settles invoice(s)               |
| INVOLVES      | Transaction | Business    | role             | Party role in transaction                |
| INVOLVES      | Transaction | Person      | role             | Party role in transaction                |
| INVOLVES      | Transaction | BankAccount | role             | Account role in transaction              |
| HOLDS_ACCOUNT | Business    | BankAccount | -                | Account holder                           |
| HOLDS_ACCOUNT | Person      | BankAccount | -                | Account holder                           |
| GRANTED_TO    | Loan        | Business    | -                | Loan borrower                            |
| GRANTED_TO    | Loan        | Person      | -                | Loan borrower                            |

## Schema Constraints

- Uniqueness constraints on IDs
- Required properties enforcement (per node label)
- Relationship cardinality rules
- Data type validation (node and relationship properties)

### Uniqueness

The `id` property is unique per label across the graph. Use it as the business or external identifier when creating and matching nodes.

| Label        | Unique property |
|-------------|-----------------|
| Business    | id              |
| Person      | id              |
| Transaction | id              |
| Invoice     | id              |
| Payment     | id              |
| Supplier    | id              |
| Customer    | id              |
| Product     | id              |
| BankAccount | id              |
| Loan        | id              |
| Asset       | id              |
| Location    | id              |

### Relationship Cardinality

| Relationship  | From side | To side  | Notes                                      |
|---------------|-----------|----------|--------------------------------------------|
| OWNS          | many      | one      | One asset has one owner; owner may have many |
| DIRECTOR_OF   | many      | many     | Person can direct many; business has many  |
| BUYS_FROM     | many      | many     | Many-to-many                               |
| SELLS_TO      | many      | many     | Many-to-many                               |
| ISSUED        | many      | one      | One invoice has one issuer                 |
| SETTLES       | one       | many     | One payment can settle many invoices       |
| INVOLVES      | one       | many     | One transaction involves many parties      |
| HOLDS_ACCOUNT | many      | one      | One account has one holder (or joint)      |
| GRANTED_TO    | one       | one/many | One loan to one borrower                   |

### Data Type Validation

Node and relationship properties have defined data types used for validation:

- **string**: text
- **int**: integer
- **float**: decimal number (e.g. amount, percentage)
- **date**: ISO date (YYYY-MM-DD)
- **datetime**: ISO datetime (e.g. created_at)
- **boolean**: true/false

Node types (e.g. amount, currency, status) and relationship properties (e.g. percentage, since, role) are defined in `ontology.py` as `NODE_PROPERTY_TYPES` and `RELATIONSHIP_PROPERTIES`. Enforcement is applied in the Neo4j interface layer and API.

## Implementation

- Definitions: `backend/src/domain/ontology.py`
- Constraints and indexes are applied via Neo4j migrations (Task 3).
