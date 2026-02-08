import React, { useState, useEffect } from 'react';

const API_BASE = 'http://127.0.0.1:3000/api/v2';

export default function ProjectManagement() {
  const [projects, setProjects] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [form, setForm] = useState({ name: '', event_id: '', start_date: '', target_date: '', owner_id: '' });

  const fetchProjects = async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await fetch(`${API_BASE}/projects`);
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const data = await res.json();
      setProjects(data.projects || data || []);
    } catch (e) {
      setError(e.message);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { fetchProjects(); }, []);

  const handleChange = (e) => setForm(prev => ({ ...prev, [e.target.name]: e.target.value }));

  const handleCreate = async (e) => {
    e.preventDefault();
    setError(null);
    try {
      const res = await fetch(`${API_BASE}/projects`, {
        method: 'POST', headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(form)
      });
      if (!res.ok) throw new Error(`Create failed ${res.status}`);
      await fetchProjects();
      setForm({ name: '', event_id: '', start_date: '', target_date: '', owner_id: '' });
    } catch (e) { setError(e.message); }
  };

  return (
    <div className="max-w-4xl w-full mx-auto p-6 bg-white rounded-lg shadow">
      <h2 className="text-xl font-semibold mb-4">Project Management</h2>
      {error && <div className="p-2 mb-3 text-sm text-red-700 bg-red-50">{error}</div>}

      <section className="mb-6">
        <form onSubmit={handleCreate} className="grid grid-cols-2 gap-3">
          <input name="name" placeholder="Project name" value={form.name} onChange={handleChange} className="p-2 border rounded" />
          <input name="event_id" placeholder="Event ID" value={form.event_id} onChange={handleChange} className="p-2 border rounded" />
          <input name="start_date" placeholder="Start date" value={form.start_date} onChange={handleChange} className="p-2 border rounded" />
          <input name="target_date" placeholder="Target date" value={form.target_date} onChange={handleChange} className="p-2 border rounded" />
          <input name="owner_id" placeholder="Owner ID" value={form.owner_id} onChange={handleChange} className="p-2 border rounded col-span-2" />
          <button className="col-span-2 bg-blue-600 text-white p-2 rounded">Create Project</button>
        </form>
      </section>

      <section>
        <div className="mb-3 flex items-center justify-between">
          <h3 className="font-medium">Projects</h3>
          <button onClick={fetchProjects} className="text-sm text-blue-600">Refresh</button>
        </div>
        {loading ? (
          <div>Loading…</div>
        ) : (
          <ul className="space-y-2">
            {projects.length === 0 && <li className="text-sm text-gray-500">No projects</li>}
            {projects.map(p => (
              <li key={p.project_id || p.projectId || p.id} className="p-3 border rounded flex justify-between items-center">
                <div>
                  <div className="font-medium">{p.name || p.project_name || p.projectId}</div>
                  <div className="text-xs text-gray-500">ID: {p.project_id || p.projectId || '—'}</div>
                </div>
                <div className="text-sm text-gray-600">Status: {p.status || 'n/a'}</div>
              </li>
            ))}
          </ul>
        )}
      </section>
    </div>
  );
}
