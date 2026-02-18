import React, { useState } from 'react';

export default function AdminQuery(){
  const [sql, setSql] = useState('SELECT name FROM sqlite_master WHERE type="table" LIMIT 20');
  const [limit, setLimit] = useState(100);
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<any>(null);
  const [error, setError] = useState<string | null>(null);

  async function runQuery(){
    setLoading(true);
    setError(null);
    setResult(null);
    try{
      const resp = await fetch('/api/v2/admin/query', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({ sql, limit })
      });
      const data = await resp.json();
      if(!resp.ok){
        setError(data.detail || JSON.stringify(data));
      } else {
        setResult(data);
      }
    }catch(e:any){
      setError(e.message || String(e));
    }finally{ setLoading(false); }
  }

  return (
    <div className="p-4 bg-white rounded shadow">
      <h2 className="text-lg font-bold mb-2">Admin SQL Query</h2>
      <textarea className="w-full border p-2 mb-2" rows={4} value={sql} onChange={e=>setSql(e.target.value)} />
      <div className="flex items-center gap-2 mb-4">
        <label className="text-sm">Limit</label>
        <input className="border p-1 w-24" type="number" value={limit} onChange={e=>setLimit(Number(e.target.value))} />
        <button className="ml-4 px-3 py-1 bg-yellow-500 text-black rounded" onClick={runQuery} disabled={loading}>{loading? 'Running...' : 'Run'}</button>
      </div>
      {error && <div className="text-red-600 mb-2">Error: {error}</div>}
      {result && (
        <div>
          <div className="mb-2 text-sm text-gray-600">Query: <code>{result.query}</code></div>
          <pre className="bg-gray-100 p-2 max-h-96 overflow-auto text-sm">{JSON.stringify(result.rows, null, 2)}</pre>
        </div>
      )}
    </div>
  );
}
