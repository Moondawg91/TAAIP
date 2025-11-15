const API_BASE = 'http://127.0.0.1:3000'; // use API Gateway

const form = document.getElementById('leadForm');
const resultArea = document.getElementById('resultArea');
const healthBtn = document.getElementById('checkHealth');
const metricsBtn = document.getElementById('getMetrics');
const startPilotBtn = document.getElementById('startPilot');

function setLoading(isLoading){
  const btn = form.querySelector('button[type="submit"]');
  btn.disabled = isLoading;
  btn.textContent = isLoading ? 'Scoring...' : 'Get Score';
}

form.addEventListener('submit', async (e) => {
  e.preventDefault();
  const payload = {
    lead_id: document.getElementById('lead_id').value || `lead-${Date.now()}`,
    age: parseInt(document.getElementById('age').value, 10),
    education_level: document.getElementById('education_level').value,
    cbsa_code: document.getElementById('cbsa_code').value || '',
    campaign_source: document.getElementById('campaign_source').value || ''
  };

  setLoading(true);
  resultArea.textContent = '';
  try{
    const res = await fetch(`${API_BASE}/api/v1/scoreLead`, {
      method: 'POST',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify(payload)
    });

    if(!res.ok){
      const text = await res.text();
      throw new Error(`Server error: ${res.status} ${text}`);
    }

    const data = await res.json();
    renderResult(data);
  }catch(err){
    resultArea.innerHTML = `<div class="error">Error: ${err.message}</div>`;
  }finally{
    setLoading(false);
  }
});

healthBtn.addEventListener('click', async () => {
  resultArea.textContent = 'Checking service health...';
  try{
    const res = await fetch(`${API_BASE}/health`);
    const j = await res.json();
    resultArea.innerHTML = `<pre>${JSON.stringify(j, null, 2)}</pre>`;
  }catch(err){
    resultArea.textContent = `Health check failed: ${err.message}`;
  }
});

// Metrics button
if (metricsBtn) {
  metricsBtn.addEventListener('click', async () => {
    resultArea.textContent = 'Fetching metrics...';
    try {
      const res = await fetch(`${API_BASE}/api/targeting/metrics`);
      const j = await res.json();
      resultArea.innerHTML = `<pre>${JSON.stringify(j, null, 2)}</pre>`;
    } catch (err) {
      resultArea.textContent = `Metrics request failed: ${err.message}`;
    }
  });
}

// Start Pilot (demo)
if (startPilotBtn) {
  startPilotBtn.addEventListener('click', async () => {
    resultArea.textContent = 'Starting pilot...';
    const config = {
      name: '2-CBSA Trial',
      duration_days: 90,
      cbsa_list: ['41884','37980'],
      objective: 'Validate lead scoring and reduce CPL by >=15%'
    };
    try {
      const res = await fetch(`${API_BASE}/api/targeting/startPilot`, {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify(config)
      });
      const j = await res.json();
      resultArea.innerHTML = `<pre>${JSON.stringify(j, null, 2)}</pre>`;
    } catch (err) {
      resultArea.textContent = `Start pilot failed: ${err.message}`;
    }
  });
}

function renderResult(d){
  resultArea.innerHTML = `
    <div>
      <div><strong>Lead ID:</strong> ${escapeHtml(d.lead_id)}</div>
      <div class="result-score">Score: ${d.score}/100</div>
      <div class="result-prob">Probability: ${(d.predicted_probability*100).toFixed(1)}%</div>
      <div style="margin-top:8px"><strong>Recommendation:</strong> ${escapeHtml(d.recommendation)}</div>
    </div>
  `;
}

function escapeHtml(s){
  return String(s)
    .replaceAll('&','&amp;')
    .replaceAll('<','&lt;')
    .replaceAll('>','&gt;')
    .replaceAll('"','&quot;')
    .replaceAll("'","&#39;");
}
