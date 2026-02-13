// Node.js API Gateway (Express)
// Bridges the React frontend (port 3000) to FastAPI backend (port 8000)

import express from 'express';
import cors from 'cors';
import axios from 'axios';
import fs from 'fs';
import path from 'path';
import http from 'http';
import https from 'https';
import { ConfidentialClientApplication } from '@azure/msal-node';

const app = express();

const FASTAPI_URL = process.env.FASTAPI_URL || 'http://127.0.0.1:8000';
const PORT = process.env.PORT || 3000;
// Authentication is intentionally disabled for this deployment.
// To re-enable, set TAAIP_API_TOKEN and restore REQUIRE_AUTH logic.
const API_TOKEN = null;
const REQUIRE_AUTH = false;

app.use(express.json());
app.use(cors());

// Serve a local dashboard folder if present (developer convenience when not using Docker)
try {
  const localDashboard = path.join(process.cwd(), 'dashboard');
  if (fs.existsSync(localDashboard)) {
    console.log(`Serving dashboard static files from ${localDashboard}`);
    app.use('/dashboard', express.static(localDashboard));
    app.use('/assets', express.static(localDashboard));
    app.get('/favicon.ico', (req, res) => {
      const fav = path.join(localDashboard, 'favicon.ico');
      if (fs.existsSync(fav)) return res.sendFile(fav);
      res.status(404).send('Not found');
    });
  }
} catch (e) {
  console.warn('Local dashboard static serve setup failed:', e.message);
}

// Helper: safely forward axios error responses to the client.
function forwardUpstreamError(res, error) {
  const resp = error && error.response;
  if (!resp) return res.status(502).json({ message: 'Upstream service error' });
  const status = resp.status || 502;
  const data = resp.data;

  // If data is a stream (responseType: 'stream'), pipe it directly.
  if (data && typeof data.pipe === 'function') {
    res.status(status);
    return data.pipe(res);
  }

  // Try to send JSON safely; fall back to string if circular.
  try {
    return res.status(status).json(data);
  } catch (e) {
    try {
      return res.status(status).send(JSON.stringify(data));
    } catch (e2) {
      return res.status(status).send(String(data));
    }
  }
}

// Optional gateway-level auth enforcement (helps protect the gateway itself).
// Auth enforcement removed — gateway will forward requests without checking a token.

// Health check endpoint
app.get('/health', async (req, res) => {
  try {
    const response = await axios.get(`${FASTAPI_URL}/health`);
    res.json(response.data);
  } catch (error) {
    res.status(503).json({ status: 'error', message: 'FastAPI backend unreachable' });
  }
});

// Power BI (GCC) embed token endpoint
// Requires env vars: PBI_TENANT_ID, PBI_CLIENT_ID, PBI_CLIENT_SECRET
// Optional env: PBI_AUTHORITY_HOST (default login.microsoftonline.us), PBI_RESOURCE (default analysis.usgovcloudapi.net)
app.post('/api/powerbi/embedToken', async (req, res) => {
  try {
    const { reportId } = req.body || {};
    if (!reportId) {
      return res.status(400).json({ message: 'Missing reportId' });
    }

    const tenantId = process.env.PBI_TENANT_ID;
    const clientId = process.env.PBI_CLIENT_ID;
    const clientSecret = process.env.PBI_CLIENT_SECRET;
    const authorityHost = process.env.PBI_AUTHORITY_HOST || 'https://login.microsoftonline.us';
    const resource = process.env.PBI_RESOURCE || 'https://analysis.usgovcloudapi.net/powerbi/api/.default';
    const apiBase = process.env.PBI_API_BASE || 'https://api.powerbigov.us/v1.0/myorg';

    if (!tenantId || !clientId || !clientSecret) {
      return res.status(500).json({ message: 'Power BI credentials not configured on server' });
    }

    const msalConfig = {
      auth: {
        clientId,
        authority: `${authorityHost}/${tenantId}`,
        clientSecret
      }
    };

    const cca = new ConfidentialClientApplication(msalConfig);
    const tokenResponse = await cca.acquireTokenByClientCredential({ scopes: [resource] });
    if (!tokenResponse?.accessToken) {
      return res.status(502).json({ message: 'Failed to acquire AAD token for Power BI' });
    }
    const aadToken = tokenResponse.accessToken;

    // Get report details (to retrieve embedUrl and datasetId)
    const reportResp = await axios.get(`${apiBase}/reports/${reportId}`, {
      headers: { Authorization: `Bearer ${aadToken}` }
    });
    const report = reportResp.data;
    const embedUrl = report.embedUrl;
    const datasetId = report.datasetId;

    // Generate embed token for the report
    const genResp = await axios.post(
      `${apiBase}/reports/${reportId}/GenerateToken`,
      { accessLevel: 'view', allowSaveAs: false, datasets: datasetId ? [{ id: datasetId }] : undefined },
      { headers: { Authorization: `Bearer ${aadToken}` } }
    );

    const { token, expiration } = genResp.data;
    return res.json({ embedUrl, embedToken: token, tokenExpiration: expiration, reportId });
  } catch (error) {
    console.error('Power BI embed token error:', error?.response?.data || error.message);
    if (error.response) return forwardUpstreamError(res, error);
    return res.status(500).json({ message: 'Unexpected server error generating embed token' });
  }
});

// Lead scoring proxy endpoint
app.post('/api/targeting/scoreLead', async (req, res) => {
  try {
    const { lead_id, age, education_level, cbsa_code, campaign_source } = req.body;

    // Validate input
    if (!lead_id || !age || !education_level || !cbsa_code || !campaign_source) {
      return res.status(400).json({
        message: 'Missing required fields: lead_id, age, education_level, cbsa_code, campaign_source'
      });
    }

    // Forward to FastAPI backend (pass through Authorization header)
    const response = await axios.post(`${FASTAPI_URL}/api/v1/scoreLead`, {
      lead_id,
      age: parseInt(age, 10),
      education_level,
      cbsa_code,
      campaign_source
    }, { headers: { authorization: req.headers['authorization'] } });

    res.json(response.data);
  } catch (error) {
    console.error('Scoring error:', error.message);
    if (error.response) return forwardUpstreamError(res, error);
    return res.status(503).json({ message: 'Failed to reach FastAPI backend. Ensure it is running on port 8000.' });
  }
});

// Ingest lead (store + score)
app.post('/api/targeting/ingestLead', async (req, res) => {
  try {
    const response = await axios.post(`${FASTAPI_URL}/api/v1/ingestLead`, req.body, { headers: { authorization: req.headers['authorization'] } });
    res.json(response.data);
  } catch (error) {
    console.error('Ingest error:', error.message);
    if (error.response) return forwardUpstreamError(res, error);
    return res.status(503).json({ message: 'Failed to reach FastAPI backend.' });
  }
});

// Metrics endpoint
app.get('/api/targeting/metrics', async (req, res) => {
  try {
    const response = await axios.get(`${FASTAPI_URL}/api/v1/metrics`, { headers: { authorization: req.headers['authorization'] } });
    res.json(response.data);
  } catch (error) {
    console.error('Metrics error:', error.message);
    if (error.response) return forwardUpstreamError(res, error);
    return res.status(503).json({ message: 'Failed to reach FastAPI backend.' });
  }
});

// Pilot control
app.post('/api/targeting/startPilot', async (req, res) => {
  try {
    const response = await axios.post(`${FASTAPI_URL}/api/v1/startPilot`, req.body, { headers: { authorization: req.headers['authorization'] } });
    res.json(response.data);
  } catch (error) {
    console.error('StartPilot error:', error.message);
    if (error.response) return forwardUpstreamError(res, error);
    return res.status(503).json({ message: 'Failed to reach FastAPI backend.' });
  }
});

app.get('/api/targeting/pilotStatus', async (req, res) => {
  try {
    const response = await axios.get(`${FASTAPI_URL}/api/v1/pilotStatus`, { headers: { authorization: req.headers['authorization'] } });
    res.json(response.data);
  } catch (error) {
    console.error('PilotStatus error:', error.message);
    if (error.response) return forwardUpstreamError(res, error);
    return res.status(503).json({ message: 'Failed to reach FastAPI backend.' });
  }
});

// Catch-all proxy for /api/v2/* endpoints (420T, TWG, Events, Calendar, etc.)
app.all('/api/v2/*', async (req, res) => {
  try {
    const url = `${FASTAPI_URL}${req.originalUrl}`;
    const config = {
      method: req.method,
      url: url,
      headers: { ...req.headers, authorization: req.headers['authorization'] },
      params: req.query,
    };
    
    if (req.method !== 'GET' && req.method !== 'HEAD') {
      config.data = req.body;
    }
    
    const response = await axios(config);
    // Forward status and JSON data; avoid copying hop-by-hop headers
    res.status(response.status).json(response.data);
  } catch (error) {
    console.error(`API v2 proxy error [${req.method} ${req.originalUrl}]:`, error.message);
    if (error.response) return forwardUpstreamError(res, error);
    return res.status(503).json({ message: 'Failed to reach FastAPI backend.' });
  }
});

// Special proxy for multipart/form-data uploads (stream-preserving)
// This ensures file uploads are forwarded to the FastAPI backend without
// relying on Express body parsers which would consume the stream.
app.post('/api/v2/imports/upload', (req, res) => {
  try {
    const target = `${FASTAPI_URL}${req.originalUrl}`;
    const parsed = new URL(target);
    const options = {
      hostname: parsed.hostname,
      port: parsed.port || (parsed.protocol === 'https:' ? 443 : 80),
      path: parsed.pathname + (parsed.search || ''),
      method: 'POST',
      headers: { ...req.headers }
    };

    const proxyReq = http.request(options, (upstreamRes) => {
      res.writeHead(upstreamRes.statusCode, upstreamRes.headers);
      upstreamRes.pipe(res);
    });

    proxyReq.on('error', (err) => {
      console.error('Upload proxy error:', err.message || err);
      try { res.status(502).json({ message: 'Upload proxy failed' }); } catch (e) { /* ignore */ }
    });

    // Pipe raw request body (multipart stream) directly to backend
    req.pipe(proxyReq);
  } catch (e) {
    console.error('Upload proxy exception:', e.message || e);
    res.status(500).json({ message: 'Upload proxy error' });
  }
});

// Explicit proxy for /api/v2/upload/actions/* to avoid accidental route collisions
app.all('/api/v2/upload/actions/*', async (req, res) => {
  try {
    console.log(`Forwarding actions path to FastAPI: ${req.method} ${req.originalUrl}`);
    const url = `${FASTAPI_URL}${req.originalUrl}`;
    const config = {
      method: req.method,
      url: url,
      headers: { ...req.headers, authorization: req.headers['authorization'] },
      params: req.query,
    };

    // Preserve body for non-GET requests. If body is empty, axios will handle it.
    if (req.method !== 'GET' && req.method !== 'HEAD') {
      config.data = req.body;
    }

    const response = await axios(config);
    res.status(response.status).json(response.data);
  } catch (error) {
    console.error(`Actions proxy error [${req.method} ${req.originalUrl}]:`, error.message);
    if (error.response) return forwardUpstreamError(res, error);
    return res.status(503).json({ message: 'Failed to reach FastAPI backend (actions proxy).' });
  }
});

// Alias /api/actions -> /api/v2/actions to support older frontend calls
app.use('/api/actions', async (req, res, next) => {
  try {
    // Rewrite path and delegate to the v2 proxy handler
    req.url = req.url.replace(/^\/api\/actions/, '/api/v2/actions');
    req.originalUrl = req.originalUrl.replace(/^\/api\/actions/, '/api/v2/actions');
    return app._router.handle(req, res, next);
  } catch (e) {
    console.error('Actions alias error:', e?.message || e);
    return res.status(500).json({ message: 'Gateway internal error processing actions alias' });
  }
});

// Proxy all /dashboard requests to the frontend container (serves static SPA)
app.all('/dashboard/*', async (req, res) => {
  try {
    const forwardPath = req.originalUrl.replace(/^\/dashboard/, '') || '/';
    const url = `http://frontend${forwardPath}`;

    const config = {
      method: req.method,
      url,
      headers: { ...req.headers },
      responseType: 'stream'
    };
    if (req.method !== 'GET' && req.method !== 'HEAD') {
      config.data = req.body;
    }

    const response = await axios(config);

    // Forward status and headers (exclude hop-by-hop headers)
    res.status(response.status);
    Object.entries(response.headers || {}).forEach(([k, v]) => {
      const name = k.toLowerCase();
      if (!['transfer-encoding', 'connection', 'keep-alive', 'proxy-authenticate', 'proxy-authorization', 'te', 'trailers', 'upgrade'].includes(name)) {
        res.setHeader(k, v);
      }
    });

    response.data.pipe(res);
  } catch (error) {
    console.error('Dashboard proxy error:', error?.response?.data || error.message);
    if (error.response) return forwardUpstreamError(res, error);
    return res.status(502).json({ message: 'Frontend unreachable via gateway' });
  }
});

// Proxy static asset requests to frontend container (Vite build assets)
app.all('/assets/*', async (req, res) => {
  try {
    const forwardPath = req.originalUrl; // keep /assets/ path
    const url = `http://frontend${forwardPath}`;

    const config = {
      method: req.method,
      url,
      headers: { ...req.headers },
      responseType: 'stream'
    };
    if (req.method !== 'GET' && req.method !== 'HEAD') {
      config.data = req.body;
    }

    const response = await axios(config);
    res.status(response.status);
    Object.entries(response.headers || {}).forEach(([k, v]) => {
      const name = k.toLowerCase();
      if (!['transfer-encoding', 'connection', 'keep-alive', 'proxy-authenticate', 'proxy-authorization', 'te', 'trailers', 'upgrade'].includes(name)) {
        res.setHeader(k, v);
      }
    });
    response.data.pipe(res);
  } catch (error) {
    console.error('Assets proxy error:', error?.response?.data || error.message);
    if (error.response) return forwardUpstreamError(res, error);
    return res.status(502).json({ message: 'Frontend assets unreachable via gateway' });
  }
});

// Proxy favicon
app.get('/favicon.ico', async (req, res) => {
  try {
    const response = await axios.get('http://frontend/favicon.ico', { responseType: 'stream' });
    res.status(response.status);
    response.data.pipe(res);
  } catch (error) {
    console.error('Favicon proxy error:', error?.message || error);
    return res.status(404).send('Not found');
  }
});

// Start both HTTP and HTTPS servers. Do not perform HTTP->HTTPS redirects.
const HTTP_PORT = parseInt(process.env.PORT_HTTP || '80', 10);
const HTTPS_PORT = 443;

const startHttpServer = () => {
  const server = http.createServer(app);
  server.listen(HTTP_PORT, '0.0.0.0', () => {
    console.log(`API Gateway HTTP running on http://0.0.0.0:${HTTP_PORT}`);
    console.log(`Proxying to FastAPI at ${FASTAPI_URL}`);
  });
};

const startHttpsServer = () => {
  const SSL_CERT = process.env.SSL_CERT || '/etc/letsencrypt/live/taaip.app/fullchain.pem';
  const SSL_KEY = process.env.SSL_KEY || '/etc/letsencrypt/live/taaip.app/privkey.pem';
  try {
    const cert = fs.readFileSync(SSL_CERT);
    const key = fs.readFileSync(SSL_KEY);
    const server = https.createServer({ key, cert }, app);
    server.listen(HTTPS_PORT, '0.0.0.0', () => {
      console.log(`API Gateway HTTPS running on https://0.0.0.0:${HTTPS_PORT}`);
    });
    return true;
  } catch (e) {
    console.warn('HTTPS not started (cert/key not found or unreadable):', e.message);
    return false;
  }
};

// Start servers
startHttpServer();
startHttpsServer();
