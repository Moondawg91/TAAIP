// Node.js API Gateway (Express)
// Bridges the React frontend (port 3000) to FastAPI backend (port 8000)

import express from 'express';
import cors from 'cors';
import axios from 'axios';
import { ConfidentialClientApplication } from '@azure/msal-node';

const app = express();

const FASTAPI_URL = process.env.FASTAPI_URL || 'http://127.0.0.1:8000';
const PORT = process.env.PORT || 3000;
const API_TOKEN = process.env.TAAIP_API_TOKEN || null;
const REQUIRE_AUTH = !!API_TOKEN;

app.use(express.json());
app.use(cors());

// Optional gateway-level auth enforcement (helps protect the gateway itself).
if (REQUIRE_AUTH) {
  console.log('API Gateway: requiring Bearer token for incoming requests');
  app.use((req, res, next) => {
    const auth = req.headers['authorization'];
    if (!auth || auth !== `Bearer ${API_TOKEN}`) return res.status(401).json({ detail: 'Unauthorized' });
    next();
  });
}

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
    if (error.response) {
      return res.status(error.response.status).json(error.response.data);
    }
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
    
    if (error.response) {
      // FastAPI returned an error
      res.status(error.response.status).json(error.response.data);
    } else {
      // Network or other error
      res.status(503).json({
        message: 'Failed to reach FastAPI backend. Ensure it is running on port 8000.'
      });
    }
  }
});

// Ingest lead (store + score)
app.post('/api/targeting/ingestLead', async (req, res) => {
  try {
    const response = await axios.post(`${FASTAPI_URL}/api/v1/ingestLead`, req.body, { headers: { authorization: req.headers['authorization'] } });
    res.json(response.data);
  } catch (error) {
    console.error('Ingest error:', error.message);
    if (error.response) return res.status(error.response.status).json(error.response.data);
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
    if (error.response) return res.status(error.response.status).json(error.response.data);
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
    if (error.response) return res.status(error.response.status).json(error.response.data);
    return res.status(503).json({ message: 'Failed to reach FastAPI backend.' });
  }
});

app.get('/api/targeting/pilotStatus', async (req, res) => {
  try {
    const response = await axios.get(`${FASTAPI_URL}/api/v1/pilotStatus`, { headers: { authorization: req.headers['authorization'] } });
    res.json(response.data);
  } catch (error) {
    console.error('PilotStatus error:', error.message);
    if (error.response) return res.status(error.response.status).json(error.response.data);
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
      headers: { authorization: req.headers['authorization'] },
      params: req.query,
    };
    
    if (req.method !== 'GET' && req.method !== 'HEAD') {
      config.data = req.body;
    }
    
    const response = await axios(config);
    res.status(response.status).json(response.data);
  } catch (error) {
    console.error(`API v2 proxy error [${req.method} ${req.originalUrl}]:`, error.message);
    if (error.response) {
      return res.status(error.response.status).json(error.response.data);
    }
    return res.status(503).json({ message: 'Failed to reach FastAPI backend.' });
  }
});

app.listen(PORT, () => {
  console.log(`API Gateway running on http://127.0.0.1:${PORT}`);
  console.log(`Proxying to FastAPI at ${FASTAPI_URL}`);
});
