import { renderMissionAdjustment } from './missionAdjustmentRenderer.js';

const API_BASE = 'http://127.0.0.1:3000';

const form = document.getElementById('majForm');
const slideContainer = document.getElementById('majSlideContainer');
const statusEl = document.getElementById('majStatus');
const printButton = document.getElementById('majPrint');

function setStatus(message, tone = 'neutral') {
  statusEl.className = `maj-status maj-status-${tone}`;
  statusEl.textContent = message;
}

function setLoading(loading) {
  const submit = form.querySelector('button[type="submit"]');
  submit.disabled = loading;
  submit.textContent = loading ? 'Generating...' : 'Generate One-Slide Brief';
}

function parseErrorBody(body) {
  if (!body || typeof body !== 'object') {
    return null;
  }
  const detail = body.detail;
  if (typeof detail === 'string') {
    return detail;
  }
  if (detail && typeof detail === 'object') {
    return detail.message || detail.code || JSON.stringify(detail);
  }
  return body.message || null;
}

form.addEventListener('submit', async (event) => {
  event.preventDefault();
  setLoading(true);
  slideContainer.innerHTML = '';

  const payload = {
    org_id: document.getElementById('org_id').value.trim(),
    period_start: document.getElementById('period_start').value,
    period_end: document.getElementById('period_end').value,
    baseline_start: document.getElementById('baseline_start').value || undefined,
    baseline_end: document.getElementById('baseline_end').value || undefined,
    include_evidence: document.getElementById('include_evidence').checked,
    force_refresh: document.getElementById('force_refresh').checked,
  };

  try {
    // Note: Backend endpoint is still named mission-decrease-justification for backwards compatibility.
    // Frontend treats this as a generalized mission adjustment endpoint.
    const response = await fetch(`${API_BASE}/api/v2/decision-output/mission-decrease-justification`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
    });

    const body = await response.json().catch(() => ({}));

    if (response.status === 403) {
      setStatus('Forbidden scope. Your user scope cannot request this org_id.', 'error');
      return;
    }

    if (!response.ok) {
      const message = parseErrorBody(body) || `Request failed with status ${response.status}`;
      setStatus(message, 'error');
      return;
    }

    if (!body || body.status !== 'ok' || !body.data) {
      setStatus('No data returned for this request.', 'warning');
      renderMissionAdjustment(null, slideContainer);
      return;
    }

    renderMissionAdjustment(body.data, slideContainer);
    setStatus('Briefing slide generated successfully.', 'ok');
  } catch (error) {
    setStatus(`Network error: ${error.message}`, 'error');
  } finally {
    setLoading(false);
  }
});

printButton.addEventListener('click', () => {
  window.print();
});
