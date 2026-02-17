// Minimal development API gateway proxy
import express from 'express';
import { createProxyMiddleware } from 'http-proxy-middleware';

const app = express();

const FASTAPI_URL = process.env.FASTAPI_URL || 'http://127.0.0.1:8000';
const FRONTEND_URL = process.env.FRONTEND_URL || 'http://localhost:5173';
const PORT = process.env.PORT_HTTP || process.env.PORT || 3000;

// Proxy API calls to FastAPI
// Keep the `/api` prefix when proxying so backend routes remain `/api/...`
app.use('/api', createProxyMiddleware({ target: FASTAPI_URL, changeOrigin: true, ws: true }));

// Proxy remaining traffic to the frontend dev server
app.use('/', createProxyMiddleware({ target: FRONTEND_URL, changeOrigin: true, ws: true }));

app.listen(PORT, () => {
  console.log(`Gateway listening on ${PORT} -> API: ${FASTAPI_URL}, UI: ${FRONTEND_URL}`);
});
