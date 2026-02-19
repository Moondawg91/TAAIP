import React, { useState } from 'react';

export default function SystemSelfCheckPage() {
  const [running, setRunning] = useState(false);
  const [result, setResult] = useState<any>(null);
  const [error, setError] = useState<string | null>(null);

  const runCheck = async () => {
    setRunning(true);
    setError(null);
    setResult(null);
    try {
      const res = await fetch('/api/system/self-check');
      const j = await res.json();
      setResult(j);
    } catch (e: any) {
      setError(e.message || String(e));
    } finally {
      setRunning(false);
    }
  };

  return (
    <div className="p-6 bg-gray-900 text-gray-100 min-h-screen">
      <h1 className="text-2xl font-bold mb-4">System Health / Self Check</h1>
      <p className="mb-4 text-sm text-gray-300">Run a lightweight system verification. This UI is dark-themed (no white surfaces).</p>
      <button onClick={runCheck} disabled={running} className="px-4 py-2 bg-blue-600 rounded text-white">
        {running ? 'Running…' : 'Run Self Check'}
      </button>

      {error && <div className="mt-4 p-3 bg-red-800 text-red-100 rounded">Error: {error}</div>}

      {result && (
        <pre className="mt-4 p-4 bg-gray-800 text-sm rounded overflow-auto">{JSON.stringify(result, null, 2)}</pre>
      )}
    </div>
  );
}
