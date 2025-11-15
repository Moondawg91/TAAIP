Frontend demo for the TAAIP Lead Scoring service.

Quick run (from project root):

1. Serve the frontend folder as static files (Python built-in server):

```bash
cd frontend
python3 -m http.server 3000
```

2. Open the demo in your browser:

http://127.0.0.1:3000

Notes:
- The backend must be running at `http://127.0.0.1:8000` (the demo calls that URL).
- The backend has permissive CORS configured for development. Restrict origins before deploying to production.
