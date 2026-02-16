# Command Center (apps/web)

Start the UI:

```bash
cd apps/web
npm install
REACT_APP_API_BASE=http://localhost:8000 npm start
```

Usage:
- Open http://localhost:3000
- Paste a JWT token from `/api/auth/login` into the "Paste JWT token" box and click Save Token.
- Pick a scope and optionally a value, then click Apply to refresh data.

Example scopes/values:
- USAREC (leave value blank)
- BDE "1"
- BN "1A"
- CO "1A1"
- STN "1A1D"

Notes:
- The UI polls every 15s and shows Last Refresh.
- If API endpoints return wrapped `{status:'ok', data:...}` the client will normalize it.

Notes:
- This dashboard connects to a real API only. It does NOT create demo domain data. If your API has no domain rows (events, funnel, burden, LOEs), the UI will show clear empty states and guidance messages.
- Paste a JWT token from `/api/auth/login` into the token box and click Save.

If the UI shows empty states, import your organization's RSIDs and ZIPs and ingest domain exports using the backend ingest tools so the charts and tables render real values.

© 2025 Maroon Moon, LLC. All rights reserved.
