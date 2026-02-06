import React, {useEffect, useState} from 'react';

export default function DataUploadManager(){
  const [datasets, setDatasets] = useState<any>({});
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState('');

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
      const r = await fetch(`/api/v2/data/ingest/${name}`, {method: 'POST'});
      const j = await r.json();
      if(r.ok){ setMessage(`Ingested: ${j.result.table} (${j.result.rows} rows)`); fetchList(); }
      else setMessage(j.detail || 'Ingest failed');
    }catch(e){ console.error(e); setMessage('Ingest request failed'); }
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
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </div>
  );
}
