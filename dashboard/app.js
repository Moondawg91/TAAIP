const base = '';
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
