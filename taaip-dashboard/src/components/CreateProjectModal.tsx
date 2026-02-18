import React, { useState } from 'react';
import { X, Save } from 'lucide-react';
import { API_BASE } from '../config/api';

export const CreateProjectModal: React.FC<{ onClose: () => void }> = ({ onClose }) => {
  const [name, setName] = useState('');
  const [owner, setOwner] = useState('');
  const [startDate, setStartDate] = useState('');
  const [targetDate, setTargetDate] = useState('');
  const [saving, setSaving] = useState(false);
  const [message, setMessage] = useState<string | null>(null);

  const handleCreate = async () => {
    if (!name || !owner || !startDate || !targetDate) {
      setMessage('Please fill required fields');
      return;
    }
    setSaving(true);
    try {
      const payload = {
        name,
        start_date: startDate,
        target_date: targetDate,
        owner_id: owner,
      } as any;

      const res = await fetch(`${API_BASE}/api/v2/projects_pm/projects`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
      });

      const data = await res.json();
      if (res.ok && data.status === 'ok') {
        setMessage('Project created');
        onClose();
      } else {
        setMessage('Failed to create project');
        console.error('Create project error', data);
      }
    } catch (e) {
      console.error(e);
      setMessage('Network error');
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-xl shadow-2xl max-w-2xl w-full overflow-hidden">
        <div className="flex items-center justify-between px-6 py-4 bg-blue-600 text-white">
          <h3 className="font-bold">Create New Project</h3>
          <button onClick={onClose} className="text-white"><X /></button>
        </div>
        <div className="p-6 space-y-4">
          {message && <div className="text-sm text-red-600">{message}</div>}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Project Name</label>
            <input autoFocus value={name} onChange={(e) => setName(e.target.value)} className="w-full px-3 py-2 border rounded-md" />
          </div>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Owner ID</label>
              <input value={owner} onChange={(e) => setOwner(e.target.value)} className="w-full px-3 py-2 border rounded-md" />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Start Date</label>
              <input type="date" value={startDate} onChange={(e) => setStartDate(e.target.value)} className="w-full px-3 py-2 border rounded-md" />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Target Date</label>
              <input type="date" value={targetDate} onChange={(e) => setTargetDate(e.target.value)} className="w-full px-3 py-2 border rounded-md" />
            </div>
          </div>

          <div className="flex justify-end">
            <button onClick={handleCreate} disabled={saving} className="flex items-center gap-2 px-4 py-2 bg-green-600 text-white rounded-md">
              <Save /> {saving ? 'Creating...' : 'Create Project'}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};
