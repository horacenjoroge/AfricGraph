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

| Type          | From        | To          | Description                              |
|---------------|-------------|-------------|------------------------------------------|
| OWNS          | Person, Business | Asset, Business | Ownership of an asset or business    |
| DIRECTOR_OF | Person      | Business    | Directorship                             |
| BUYS_FROM     | Business    | Supplier    | Procurement relationship                 |
| SELLS_TO      | Business    | Customer    | Sales relationship                       |
| ISSUED        | Supplier, Business | Invoice  | Invoice issuer                           |
| SETTLES       | Payment     | Invoice     | Payment settles invoice(s)               |
| INVOLVES      | Transaction | Person, Business, BankAccount | Party to a transaction     |
| HOLDS_ACCOUNT | Person, Business | BankAccount | Account holder                       |
| GRANTED_TO    | Loan        | Person, Business | Loan borrower                        |

## Schema Constraints

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

## Implementation

- Definitions: `backend/src/domain/ontology.py`
- Constraints and indexes are applied via Neo4j migrations (Task 3).
