// Performance indexes for common filters and lookups. Idempotent (IF NOT EXISTS).

// name lookups
CREATE INDEX business_name IF NOT EXISTS FOR (n:Business) ON (n.name);
CREATE INDEX person_name IF NOT EXISTS FOR (n:Person) ON (n.name);
CREATE INDEX supplier_name IF NOT EXISTS FOR (n:Supplier) ON (n.name);
CREATE INDEX customer_name IF NOT EXISTS FOR (n:Customer) ON (n.name);
CREATE INDEX product_name IF NOT EXISTS FOR (n:Product) ON (n.name);
CREATE INDEX asset_name IF NOT EXISTS FOR (n:Asset) ON (n.name);

// date and time range queries
CREATE INDEX transaction_date IF NOT EXISTS FOR (n:Transaction) ON (n.date);
CREATE INDEX invoice_issue_date IF NOT EXISTS FOR (n:Invoice) ON (n.issue_date);
CREATE INDEX invoice_status IF NOT EXISTS FOR (n:Invoice) ON (n.status);
CREATE INDEX payment_date IF NOT EXISTS FOR (n:Payment) ON (n.date);
CREATE INDEX loan_start_date IF NOT EXISTS FOR (n:Loan) ON (n.start_date);
CREATE INDEX loan_status IF NOT EXISTS FOR (n:Loan) ON (n.status);

// composite for common filters
CREATE INDEX transaction_date_currency IF NOT EXISTS FOR (n:Transaction) ON (n.date, n.currency);
