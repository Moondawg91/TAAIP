import React, {useEffect, useState} from 'react';
import { API_BASE } from '../config/api';

export default function DataUploadManager(){
  const [datasets, setDatasets] = useState<any>({});
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState('');
  const [editingDataset, setEditingDataset] = useState<string | null>(null);
  const [mappingEdits, setMappingEdits] = useState<Record<string,string>>({});

  useEffect(()=>{ fetchList(); }, []);

  async function fetchList(){
    setLoading(true);
    try{
      const controller = new AbortController();
      const timeoutId = window.setTimeout(() => controller.abort(), 10000);
      const r = await fetch(`${API_BASE}/api/v2/data/list`, { signal: controller.signal });
      window.clearTimeout(timeoutId);

      if (!r.ok) {
        setMessage(`Failed to load datasets (HTTP ${r.status})`);
        setDatasets({});
        return;
      }

      const text = await r.text();
      const j = text ? JSON.parse(text) : {};
      setDatasets(j.datasets || {});
      setMessage('');
    }catch(e){
      console.error(e);
      setDatasets({});
      setMessage('Failed to load datasets');
    } finally {
      setLoading(false);
    }
  }

  async function ingest(name:string){
    setMessage('Ingesting...');
    try{
      // Try direct ingest route first
      let r = await fetch(`${API_BASE}/api/v2/data/ingest/${name}`, {method: 'POST'});
      if(r.status === 404){
        // Fallback: call server-side ingest action to create uploaded_{dataset} table
        const actionResp = await fetch(`${API_BASE}/api/v2/upload/actions/ingest_dataset`, {method: 'POST', headers: {'Content-Type':'application/json'}, body: JSON.stringify({dataset_name: name})});
        const aj = await actionResp.json().catch(()=>({detail: 'No JSON response'}));
        if(actionResp.ok){ setMessage(`Ingested via server action: ${aj.result.table} (${aj.result.rows} rows)`); fetchList(); }
        else setMessage(aj.detail || 'Server-side ingest failed');
        return;
      }
      const j = await r.json().catch(()=>({detail: 'No JSON response'}));
      if(r.ok){ setMessage(`Ingested: ${j.result.table} (${j.result.rows} rows)`); fetchList(); }
      else setMessage(j.detail || 'Ingest failed');
    }catch(e){ console.error(e); setMessage('Ingest request failed'); }
  }

  async function editMapping(name:string){
    setMessage('Loading mapping...');
    try{
      const r = await fetch(`${API_BASE}/api/v2/data/${name}`);
      const j = await r.json();
      if(r.ok && j.dataset){
        const mapping = j.dataset.mapping || {};
        setMappingEdits(mapping);
        setEditingDataset(name);
        setMessage('');
      } else {
        setMessage('Failed to load mapping');
      }
    }catch(e){ console.error(e); setMessage('Failed to load mapping'); }
  }

  async function saveMapping(name:string){
    setMessage('Saving mapping...');
    try{
      // Try JSON API first
      let r = await fetch(`${API_BASE}/api/v2/data/save_mapping/${name}`, {method: 'POST', headers: {'Content-Type':'application/json'}, body: JSON.stringify({mapping: mappingEdits})});
      if(r.status === 404){
        // Fallback to legacy upload save_mapping (expects form fields: data_type, mapping)
        const form = new FormData();
        form.append('data_type', name);
        form.append('mapping', JSON.stringify(mappingEdits));
        r = await fetch(`${API_BASE}/api/v2/upload/save_mapping`, {method: 'POST', body: form});
      }
      const j = await r.json().catch(()=>({detail: 'No JSON response'}));
      if(r.ok){ setMessage('Mapping saved'); setEditingDataset(null); fetchList(); }
      else setMessage(j.detail || 'Save failed');
    }catch(e){ console.error(e); setMessage('Save request failed'); }
  }

  function updateMappingKey(orig:string, val:string){
    setMappingEdits(prev=>({ ...prev, [orig]: val }));
  }

  return (
    <div style={{padding:20}}>
      <div style={{display:'flex', alignItems:'center', justifyContent:'space-between', marginBottom:8}}>
        <h2 style={{margin:0}}>Data Upload Manager</h2>
        <button onClick={fetchList} disabled={loading}>Refresh List</button>
      </div>
      {message && <div style={{marginBottom:10}}>{message}</div>}
      {loading ? <div style={{ padding: 20, color: '#6b7280' }}>Loading...</div> : (
        <table style={{width:'100%', borderCollapse:'collapse'}}>
          <thead><tr><th>Dataset</th><th>Rows</th><th>Actions</th></tr></thead>
          <tbody>
            {Object.keys(datasets).length === 0 && (
              <tr>
                <td colSpan={3} style={{padding:16, color:'#6b7280'}}>No datasets loaded. Verify upload service connectivity, then refresh.</td>
              </tr>
            )}
            {Object.entries(datasets).map(([k,v]:any)=> (
              <tr key={k}>
                <td style={{padding:8}}>{v.display_name || k}</td>
                <td style={{padding:8}}>{v.row_count || 0}</td>
                <td style={{padding:8}}>
                  <button onClick={()=>ingest(k)}>Ingest</button>
                  <button style={{marginLeft:8}} onClick={()=>editMapping(k)}>Edit Mapping</button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
      {editingDataset && (
        <div style={{marginTop:20, padding:12, border:'1px solid #ddd', borderRadius:6, background:'#fff'}}>
          <h3>Editing mapping for {editingDataset}</h3>
          <div style={{display:'grid', gap:8}}>
            <div style={{fontSize:12, color:'#666'}}>Preview (first two rows):</div>
            {Object.entries(mappingEdits).map(([orig,mapped])=> (
              <div key={orig} style={{display:'flex', gap:8, alignItems:'center'}}>
                <div style={{minWidth:200}}>{orig}</div>
                <input value={mapped} onChange={(e)=>updateMappingKey(orig, e.target.value)} style={{flex:1, padding:6}} />
              </div>
            ))}
          </div>
          <div style={{marginTop:12}}>
            <button disabled={Object.values(mappingEdits).some(v=>!v||v.trim()==='')} onClick={()=>saveMapping(editingDataset)}>Save Mapping</button>
            <button style={{marginLeft:8}} onClick={()=>{ setEditingDataset(null); setMessage(''); }}>Cancel</button>
          </div>
        </div>
      )}
    </div>
  );
}
