# User Manual

Welcome to AfricGraph! This guide will help you navigate and use the platform effectively.

## Getting Started

### Accessing the Platform

1. Navigate to your AfricGraph instance (e.g., `https://yourdomain.com`)
2. Log in with your credentials
3. You'll be taken to the Dashboard

### Dashboard Overview

The Dashboard provides:
- **Key Metrics**: Total businesses, high-risk alerts, pending workflows
- **Recent Alerts**: Latest fraud and risk alerts
- **Quick Actions**: Common tasks and shortcuts

## Business Management

### Searching for Businesses

1. Navigate to **Business Search**
2. Enter search terms (name, registration number)
3. Apply filters (sector, risk level)
4. Click on a business to view details

### Viewing Business Details

The Business Detail page shows:
- **Profile**: Basic information, registration details
- **Risk Score**: Composite risk score with breakdown
- **Graph Visualization**: Interactive 3D graph of relationships
- **Transactions**: Recent payment history
- **Owners**: Business ownership structure

### Understanding Risk Scores

Risk scores range from 0-100:
- **0-30**: Low Risk (Green)
- **31-70**: Medium Risk (Yellow)
- **71-100**: High Risk (Red)

Risk factors include:
- Payment behavior
- Supplier concentration
- Ownership complexity
- Cash flow health
- Network exposure

## Graph Explorer

### Navigating the Graph

1. Go to **Graph Explorer**
2. The graph shows businesses, people, and relationships
3. **Click** on nodes to see details
4. **Drag** to rotate the view
5. **Scroll** to zoom in/out

### Node Colors

- **Blue**: Businesses
- **Green**: People
- **Orange**: Transactions
- **Red**: High-risk entities

### Finding Relationships

1. Use the search to find entities
2. Click "Find Connections" to see how entities are related
3. View relationship paths and strength scores

## Risk Analysis

### Viewing Risk Assessment

1. Navigate to a business
2. Click **Risk Analysis** tab
3. View:
   - Composite risk score
   - Factor breakdown (Radar chart)
   - Risk explanation
   - Historical trends

### Cash Flow Health

View cash flow analysis:
- **Health Score**: Overall cash flow health (0-100)
- **Burn Rate**: Monthly cash consumption
- **Runway**: Months until cash runs out
- **Forecast**: 3-6 month projection

### Supplier Risk

Analyze supplier relationships:
- **Concentration**: Supplier dependency
- **Shared Directors**: Potential conflicts
- **Late Payments**: Payment behavior
- **Health**: Supplier financial health

## Fraud Detection

### Viewing Fraud Alerts

1. Go to **Fraud Alerts** page
2. Alerts are categorized by severity:
   - **Critical**: Immediate attention required
   - **High**: Review within 24 hours
   - **Medium**: Review within 7 days
   - **Low**: Informational

### Understanding Fraud Patterns

Common patterns detected:
- **Circular Payments**: Money flowing in circles
- **Shell Companies**: Businesses with no real operations
- **Duplicate Invoices**: Same invoice multiple times
- **Invoice Fraud**: Suspicious invoice patterns
- **Structuring**: Breaking large payments into small ones
- **Round Amounts**: Suspicious round-number transactions

### Acknowledging Alerts

1. Click on an alert to view details
2. Review the pattern and context
3. Mark as **False Positive** if not fraud
4. Escalate if action is needed

## Workflows

### Approval Workflows

View pending approvals:
1. Go to **Workflows** page
2. See list of pending approvals
3. Click on a workflow to review
4. **Approve** or **Reject** with comments

### Workflow Types

- **Supplier Onboarding**: New supplier approval
- **Large Payment**: Payments above threshold
- **Credit Limit Increase**: Credit limit changes
- **High-Risk Business Review**: Manual review required

## Audit Logs

### Viewing Audit Logs

1. Navigate to **Audit Logs**
2. Filter by:
   - User
   - Action type
   - Date range
   - Resource type
3. Export logs if needed

## Settings

### User Profile

Update your profile:
- Name, email, phone
- Password
- Notification preferences

### Preferences

Configure:
- Dashboard layout
- Default filters
- Notification settings

## Tips and Best Practices

### Efficient Searching

- Use specific terms for better results
- Combine filters for precise searches
- Save frequent searches

### Understanding Risk

- Review factor breakdowns
- Check historical trends
- Compare with industry benchmarks

### Graph Exploration

- Start with 1-2 hop neighborhoods
- Use filters to focus on specific relationship types
- Export graphs for reports

### Fraud Investigation

- Review all pattern details
- Check related entities
- Follow relationship paths
- Document findings

## Keyboard Shortcuts

- `Ctrl+K` or `Cmd+K`: Quick search
- `Esc`: Close modals/panels
- `?`: Show keyboard shortcuts

## Getting Help

- **Documentation**: See [Developer Guide](./developer-guide.md)
- **Support**: Contact your administrator
- **Feedback**: Use the feedback button in the UI

## Frequently Asked Questions

### Q: How often are risk scores updated?
A: Risk scores are calculated on-demand and cached for 30 minutes. They update automatically when new data is ingested.

### Q: Can I export data?
A: Yes, you can export business data, risk reports, and graph visualizations from the respective pages.

### Q: How do I report a bug?
A: Contact your administrator or use the feedback feature in the application.

### Q: What browsers are supported?
A: Modern browsers (Chrome, Firefox, Safari, Edge) with JavaScript enabled.
