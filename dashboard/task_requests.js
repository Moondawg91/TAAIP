// Use the existing backend helpdesk API
const apiEndpoint = '/api/v2/helpdesk/requests';

function loadPending(){
  const raw = localStorage.getItem('task_requests_pending');
  const list = raw ? JSON.parse(raw) : [];
  const el = document.getElementById('pending');
  if(!el) return;
  if(list.length === 0){ el.innerHTML = '<em>No pending requests</em>'; return; }
  el.innerHTML = '';
  list.forEach((r, i)=>{
    const d = document.createElement('div');
    d.className = 'request';
    d.innerHTML = `<strong>${r.title}</strong> — <em>${r.priority}</em><div>${r.description||''}</div><div style="margin-top:6px">Assignee: ${r.assignee||'—'} | Due: ${r.dueDate||'—'}</div>`;
    const resend = document.createElement('button');
    resend.textContent = 'Resend';
    resend.style.marginRight = '6px';
    resend.addEventListener('click', ()=> resendRequest(i));
    const remove = document.createElement('button');
    remove.textContent = 'Remove';
    remove.addEventListener('click', ()=> removeRequest(i));
    d.appendChild(resend);
    d.appendChild(remove);
    el.appendChild(d);
  });
}

function savePending(list){
  localStorage.setItem('task_requests_pending', JSON.stringify(list));
  loadPending();
}

function addPending(req){
  const raw = localStorage.getItem('task_requests_pending');
  const list = raw ? JSON.parse(raw) : [];
  list.push(req);
  savePending(list);
}

function removeRequest(index){
  const raw = localStorage.getItem('task_requests_pending');
  const list = raw ? JSON.parse(raw) : [];
  list.splice(index,1);
  savePending(list);
}

async function resendRequest(index){
  const raw = localStorage.getItem('task_requests_pending');
  const list = raw ? JSON.parse(raw) : [];
  const req = list[index];
  if(!req) return;
  try{
    const r = await fetch(apiEndpoint, {method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(req)});
    if(r.ok){
      list.splice(index,1);
      savePending(list);
      document.getElementById('status').innerHTML = '<div class="notice">Resent and accepted by API.</div>';
    }else{
      const text = await r.text();
      document.getElementById('status').innerHTML = `<div class="error">API rejected request: ${text}</div>`;
    }
  }catch(e){
    document.getElementById('status').innerHTML = '<div class="error">Failed to send — offline or API unavailable.</div>';
  }
}

  // Fetch recent requests from backend and render
  async function fetchRequests(){
    const el = document.getElementById('serverRequests');
    el.innerHTML = '<em>Loading...</em>';
    try{
      const r = await fetch(apiEndpoint + '?status=pending');
      if(!r.ok){ el.innerHTML = `<div class="error">Server returned ${r.status}</div>`; return; }
      const j = await r.json();
      const list = j.requests || [];
      if(list.length === 0){ el.innerHTML = '<em>No requests found</em>'; return; }
      el.innerHTML = '';
      list.forEach(req=>{
        const d = document.createElement('div');
        d.className = 'request';
        d.innerHTML = `<strong>${req.title}</strong> — <em>${req.priority}</em><div>${req.description||''}</div><div style="margin-top:6px">Submitted by: ${req.submitted_by||req.submittedBy||'—'} | At: ${req.submitted_at||req.submittedAt||req.created_at||'—'}</div>`;
        el.appendChild(d);
      });
    }catch(e){
      el.innerHTML = '<div class="error">Failed to fetch — offline or API blocked.</div>';
    }
  }

  document.getElementById('fetchRequests').addEventListener('click', fetchRequests);

document.getElementById('taskForm').addEventListener('submit', async (evt)=>{
  evt.preventDefault();
  // Build payload compatible with backend `HelpdeskRequest` model
  const req = {
    type: 'feature_request', // default type for dashboard task requests
    priority: document.getElementById('priority').value.toLowerCase(),
    title: document.getElementById('title').value.trim(),
    description: document.getElementById('description').value.trim(),
    requestedAccessLevel: null,
    currentAccessLevel: null,
    submittedBy: (window.TAAIP && window.TAAIP.currentUser) || 'web.dashboard',
    submittedAt: new Date().toISOString(),
    // extra metadata retained locally (not part of API model)
    meta: {
      assignee: document.getElementById('assignee').value.trim(),
      dueDate: document.getElementById('dueDate').value,
      actions: document.getElementById('actions').value.trim(),
      created_at: new Date().toISOString()
    }
  };

  try{
    const r = await fetch(apiEndpoint, {method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(req)});
    if(r.ok){
      document.getElementById('status').innerHTML = '<div class="notice">Task submitted to API successfully.</div>';
      document.getElementById('taskForm').reset();
      return;
    }
    const body = await r.text();
    document.getElementById('status').innerHTML = `<div class="error">API error: ${body}</div>`;
    // fallthrough: save locally
  }catch(e){
    // network or CORS error — save locally
  }

  // Save a compact copy to pending list for resend (keep API fields and meta)
  addPending(req);
  document.getElementById('status').innerHTML = '<div class="notice">API unavailable — saved locally. Resend from Pending.</div>';
  document.getElementById('taskForm').reset();
});

loadPending();
