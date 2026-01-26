// Drop global unique constraints on id to allow multi-tenant isolation
// Neo4j doesn't support composite unique constraints (id + tenant_id),
// so we rely on MERGE queries with tenant_id to ensure uniqueness per tenant.
// This allows the same transaction ID to exist in different tenants.

// Drop constraints if they exist (idempotent)
DROP CONSTRAINT transaction_id IF EXISTS;
DROP CONSTRAINT person_id IF EXISTS;
DROP CONSTRAINT business_id IF EXISTS;
DROP CONSTRAINT invoice_id IF EXISTS;
DROP CONSTRAINT payment_id IF EXISTS;
DROP CONSTRAINT supplier_id IF EXISTS;
DROP CONSTRAINT customer_id IF EXISTS;
DROP CONSTRAINT product_id IF EXISTS;
DROP CONSTRAINT bank_account_id IF EXISTS;
DROP CONSTRAINT loan_id IF EXISTS;
DROP CONSTRAINT asset_id IF EXISTS;
DROP CONSTRAINT location_id IF EXISTS;

// Note: We rely on MERGE (n:Label {id: $id, tenant_id: $tenant_id}) 
// to ensure uniqueness per tenant. The application layer enforces this.
