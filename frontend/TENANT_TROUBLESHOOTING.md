# Tenant Data Visibility & Dashboard Troubleshooting

## Issue 1: Can't See Data

### Symptoms
- Dashboard shows 0 businesses, 0 transactions
- Business search returns no results
- Graph explorer shows empty

### Solutions

#### 1. Check Tenant Selection
- Look at the top-right corner of the screen
- You should see a tenant selector dropdown
- If it says "Select Tenant", click it and select a tenant
- The system will auto-select the first available tenant if none is selected

#### 2. Verify Tenant Has Data
- Go to **Settings → Performance** tab
- Check the "Health Status" section
- Look at "Nodes" and "Relationships" counts
- If both are 0, the tenant has no data yet

#### 3. Check Browser Console
- Open browser DevTools (F12)
- Check Console tab for errors
- Look for messages about tenant context
- Check Network tab to see if `X-Tenant-ID` header is being sent

#### 4. Verify Tenant Context
- Go to **Settings → Tenant** tab
- You should see your current tenant information
- If it shows "No tenant selected", select one from the dropdown

### Quick Fixes

1. **Refresh the page** after selecting a tenant
2. **Clear localStorage** and select tenant again:
   ```javascript
   localStorage.removeItem('current_tenant_id')
   window.location.reload()
   ```
3. **Check if tenant exists**:
   - Go to Admin panel (if you have admin access)
   - Check Tenant Management
   - Verify tenant is active

## Issue 2: Can't See Tenant Analytics Dashboard

### Solution

The Tenant Performance Dashboard is now available in:

**Settings → Performance Tab**

1. Click on **Settings** in the sidebar
2. Click on the **Performance** tab
3. You'll see:
   - Health Status (healthy/unhealthy, node count, relationship count)
   - Usage Metrics (operations, active days)
   - Resource Quotas (with progress bars)
   - Performance Trends (placeholder for charts)

### If Dashboard Shows "No Tenant Selected"

1. Select a tenant from the dropdown in the top-right
2. The dashboard will automatically refresh
3. If still not showing, check browser console for errors

## How Tenant Selection Works

1. **Tenant Selector** (top-right corner):
   - Shows current tenant name
   - Click to see all available tenants
   - Select a tenant to switch context
   - Page reloads automatically after selection

2. **Auto-Selection**:
   - If no tenant is selected, the system auto-selects the first available tenant
   - This happens automatically when tenants are loaded

3. **Tenant Context**:
   - Stored in `localStorage` as `current_tenant_id`
   - Sent as `X-Tenant-ID` header in all API requests
   - Required for all data queries

## Verifying Tenant Context

### Method 1: Browser DevTools
1. Open DevTools (F12)
2. Go to Application/Storage → Local Storage
3. Look for `current_tenant_id` key
4. Check Network tab → Headers → Request Headers
5. Verify `X-Tenant-ID` header is present

### Method 2: Settings Page
1. Go to Settings → Tenant tab
2. Should show current tenant information
3. If blank, no tenant is selected

### Method 3: Console Logs
Open browser console and run:
```javascript
console.log('Tenant ID:', localStorage.getItem('current_tenant_id'))
```

## Creating Test Data

If your tenant has no data:

1. **Via API** (requires authentication):
   ```bash
   # Set tenant header
   export TENANT_ID="your-tenant-id"
   
   # Create a business
   curl -X POST http://localhost:8000/api/v1/businesses \
     -H "Authorization: Bearer <token>" \
     -H "X-Tenant-ID: $TENANT_ID" \
     -H "Content-Type: application/json" \
     -d '{
       "id": "BIZ001",
       "name": "Test Business",
       "registration_number": "REG123"
     }'
   ```

2. **Via Admin Panel**:
   - Go to Admin → Tenant Management
   - Create test data for the tenant

## Common Issues

### Issue: "No tenants available"
- **Cause**: No tenants exist in the system
- **Fix**: Create a tenant via API or Admin panel

### Issue: "Authentication required"
- **Cause**: Not logged in or token expired
- **Fix**: Log in again

### Issue: Data shows for one tenant but not another
- **Cause**: Normal behavior - data is isolated per tenant
- **Fix**: This is expected. Each tenant only sees their own data.

### Issue: Dashboard shows 0 for everything
- **Cause**: Tenant has no data yet
- **Fix**: Create data for that tenant (businesses, transactions, etc.)

## Debugging Steps

1. ✅ Check tenant is selected (top-right dropdown)
2. ✅ Verify tenant exists (Settings → Tenant tab)
3. ✅ Check tenant has data (Settings → Performance tab)
4. ✅ Verify API calls include `X-Tenant-ID` header (Network tab)
5. ✅ Check browser console for errors
6. ✅ Verify backend is running and accessible
7. ✅ Check if tenant is active (not suspended)

## Getting Help

If issues persist:
1. Check browser console for errors
2. Check Network tab for failed requests
3. Check backend logs for tenant-related errors
4. Verify tenant exists in database
5. Try selecting a different tenant
6. Clear browser cache and localStorage
