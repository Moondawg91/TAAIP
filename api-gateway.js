// Node.js API Gateway (Express)
// Bridges the React frontend (port 3000) to FastAPI backend (port 8000)

import express from 'express';
import cors from 'cors';
import axios from 'axios';

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

app.listen(PORT, () => {
  console.log(`API Gateway running on http://127.0.0.1:${PORT}`);
  console.log(`Proxying to FastAPI at ${FASTAPI_URL}`);
});
