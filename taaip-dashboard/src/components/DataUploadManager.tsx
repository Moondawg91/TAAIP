import React, {useEffect, useState} from 'react';

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
      const r = await fetch('/api/v2/data/list');
      const j = await r.json();
      setDatasets(j.datasets || {});
    }catch(e){ console.error(e); setMessage('Failed to load datasets'); }
    setLoading(false);
  }

  async function ingest(name:string){
    setMessage('Ingesting...');
    try{
      // Try direct ingest route first
      let r = await fetch(`/api/v2/data/ingest/${name}`, {method: 'POST'});
      if(r.status === 404){
        // Fallback: fetch the processed dataset and post to universal upload endpoint
        const ds = await (await fetch(`/api/v2/data/${name}`)).json();
        const rows = (ds && ds.dataset && ds.dataset.rows) ? ds.dataset.rows : [];
        if(rows.length === 0){ setMessage('No rows to ingest'); return; }
        const uploadResp = await fetch('/api/v2/upload/uploaded', {method: 'POST', headers: {'Content-Type':'application/json'}, body: JSON.stringify({data: rows, category: 'uploaded'})});
        const uj = await uploadResp.json().catch(()=>({detail: 'No JSON response'}));
        if(uploadResp.ok){ setMessage(`Imported ${uj.rows_processed || uj.rows_processed} rows to category 'uploaded'`); fetchList(); }
        else setMessage(uj.detail || 'Universal upload failed');
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
      const r = await fetch(`/api/v2/data/${name}`);
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
      let r = await fetch(`/api/v2/data/save_mapping/${name}`, {method: 'POST', headers: {'Content-Type':'application/json'}, body: JSON.stringify({mapping: mappingEdits})});
      if(r.status === 404){
        // Fallback to legacy upload save_mapping (expects form fields: data_type, mapping)
        const form = new FormData();
        form.append('data_type', name);
        form.append('mapping', JSON.stringify(mappingEdits));
        r = await fetch('/api/v2/upload/save_mapping', {method: 'POST', body: form});
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
      <h2>Data Upload Manager</h2>
      {message && <div style={{marginBottom:10}}>{message}</div>}
      {loading ? <div>Loading...</div> : (
        <table style={{width:'100%', borderCollapse:'collapse'}}>
          <thead><tr><th>Dataset</th><th>Rows</th><th>Actions</th></tr></thead>
          <tbody>
            {Object.entries(datasets).map(([k,v]:any)=> (
              <tr key={k}>
                <td style={{padding:8}}>{k} — {v.filename}</td>
                <td style={{padding:8}}>{v.rows}</td>
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
