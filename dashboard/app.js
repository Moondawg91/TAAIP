const base = window.API_BASE || '';
async function loadFunnel(){
  try{
    const r = await fetch(`${base}/api/v2/funnel/stages`);
    const j = await r.json();
    const stages = j.stages || [];
    let html = '<table><tr><th>Order</th><th>Stage ID</th><th>Stage Name</th><th>Description</th></tr>';
    stages.forEach(s=>{
      html += `<tr><td>${s.sequence_order}</td><td>${s.stage_id}</td><td>${s.stage_name}</td><td>${s.description}</td></tr>`;
    });
    html += '</table>';
    document.getElementById('funnel').innerHTML = html;
  }catch(e){ document.getElementById('funnel').innerText = 'Failed to load funnel'; }
}

async function loadAnalytics(){
  const eventId = document.getElementById('eventId').value;
  try{
    const r = await fetch(`${base}/api/v2/marketing/analytics?event_id=${encodeURIComponent(eventId)}`);
    const j = await r.json();
    if(j.status !== 'ok'){ document.getElementById('analytics').innerText = JSON.stringify(j); return; }
    const html = `
      <table>
        <tr><th>Total Impressions</th><td>${j.total_impressions}</td></tr>
        <tr><th>Total Engagement</th><td>${j.total_engagement}</td></tr>
        <tr><th>Avg Awareness</th><td>${j.avg_awareness}</td></tr>
        <tr><th>Total Activations</th><td>${j.total_activations}</td></tr>
      </table>
    `;
    document.getElementById('analytics').innerHTML = html;
  }catch(e){ document.getElementById('analytics').innerText = 'Failed to load analytics'; }
}

document.getElementById('loadAnalytics').addEventListener('click', loadAnalytics);
loadFunnel();

// CSV upload handling
function parseCSV(text){
  const lines = text.split(/\r?\n/).filter(l=>l.trim());
  if(lines.length < 2) return [];
  const headers = lines[0].split(',').map(h=>h.trim());
  return lines.slice(1).map(line=>{
    const cols = line.split(',').map(c=>c.trim());
    const obj = {};
    headers.forEach((h,i)=> obj[h]=cols[i]===undefined?"":cols[i]);
    return obj;
  });
}

async function postMetrics(eventId, payload){
  try{
    const res = await fetch(`${base}/api/v2/events/${encodeURIComponent(eventId)}/metrics`,{
      method:'POST', headers:{'Content-Type':'application/json'}, body: JSON.stringify(payload)
    });
    return await res.json();
  }catch(e){ return {error: String(e)}; }
}

document.getElementById('csvUploadBtn')?.addEventListener('click', async ()=>{
  const input = document.getElementById('csvFile');
  const status = document.getElementById('uploadStatus');
  if(!input || !input.files || input.files.length===0){ status.innerText='No file selected'; return; }
  const file = input.files[0];
  status.innerText = 'Reading file...';
  const text = await file.text();
  const rows = parseCSV(text);
  if(rows.length===0){ status.innerText='No data rows found'; return; }
  status.innerText = `Uploading ${rows.length} rows...`;
  let success=0, failed=0;
  for(const r of rows){
    const eventId = r.event_id || r.eventId || r.event || r.event_id;
    if(!eventId){ failed++; continue; }
    const payload = {
      date: r.date || r.date_occurred || '',
      leads_generated: r.leads_generated ? Number(r.leads_generated) : (r.leads?Number(r.leads):0),
      conversion_count: r.conversion_count ? Number(r.conversion_count) : (r.conversions?Number(r.conversions):0),
      roi: r.roi ? Number(r.roi) : (r.return_on_investment?Number(r.return_on_investment):null)
    };
    const res = await postMetrics(eventId, payload);
    if(res && res.status==='ok' || res && !res.error) success++; else failed++;
    status.innerText = `Uploading ${rows.indexOf(r)+1}/${rows.length}... (s:${success} f:${failed})`;
  }
  status.innerText = `Upload complete — success: ${success}, failed: ${failed}`;
});
