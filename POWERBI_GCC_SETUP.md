## Power BI GCC Integration Setup

This app embeds Power BI Government (GCC) reports via a secure backend token service.

### 1) Azure AD App (GCC / login.microsoftonline.us)
- Create an App Registration in your GCC tenant
- Note the following values:
  - `PBI_TENANT_ID`
  - `PBI_CLIENT_ID`
  - `PBI_CLIENT_SECRET`
- Grant API permissions to the Power BI Service (Application permissions)
  - For embedding: `Tenant.Read.All`, `Report.Read.All`, `Dataset.Read.All` (as needed)
  - Admin consent required
- In Power BI Admin portal (GCC), enable service principals for embed

### 2) Server Environment Variables (api-gateway)
Set these in your shell or process manager for the API Gateway:

```bash
export PBI_TENANT_ID="<your-tenant-guid>"
export PBI_CLIENT_ID="<app-registration-client-id>"
export PBI_CLIENT_SECRET="<client-secret>"
export PBI_AUTHORITY_HOST="https://login.microsoftonline.us"
export PBI_RESOURCE="https://analysis.usgovcloudapi.net/powerbi/api/.default"
export PBI_API_BASE="https://api.powerbigov.us/v1.0/myorg"
```

Restart the API gateway:
```bash
npm run dev   # from /Users/ambermooney/Desktop/TAAIP
```

### 3) Frontend Usage
Open the app and navigate to: Operations → "Power BI (GCC)". The provided report IDs are preloaded.

### Notes
- If your tenant requires `groupId`, adjust the API route to call `groups/{groupId}/reports/{reportId}` and include the group in token generation. Current route uses `myorg/reports/{reportId}` which works for many scenarios.
- Users must have appropriate access to the reports for the service principal.
- If token generation fails, check API permissions and Admin Portal settings for service principals.
