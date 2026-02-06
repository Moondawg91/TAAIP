import React, { useState, useEffect } from 'react';
import { Save, Plus, X, Edit, Trash2, CheckCircle, Calendar, DollarSign, AlertCircle, Users, Target } from 'lucide-react';
import { API_BASE } from '../config/api';

interface Project {
  project_id: string;
  name: string;
  status: string;
  start_date: string;
  target_date: string;
  owner_id: string;
  objectives: string;
  funding_amount: number;
  spent_amount: number;
  percent_complete: number;
  blockers?: string;
  risk_level?: string;
}

interface Task {
  task_id: string;
  title: string;
  description: string;
  assigned_to: string;
  due_date: string;
  status: string;
  priority: string;
}

interface Milestone {
  milestone_id: string;
  name: string;
  target_date: string;
  actual_date?: string;
}

export const ProjectEditor: React.FC<{ projectId: string; onClose: () => void }> = ({ projectId, onClose }) => {
  const [project, setProject] = useState<Project | null>(null);
  const [tasks, setTasks] = useState<Task[]>([]);
  const [milestones, setMilestones] = useState<Milestone[]>([]);
  const [activeTab, setActiveTab] = useState<'details' | 'tasks' | 'budget' | 'milestones' | 'participants' | 'emm'>('details');
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [message, setMessage] = useState<{ type: 'success' | 'error'; text: string } | null>(null);

  // Fetch project data
  useEffect(() => {
    fetchProjectData();
  }, [projectId]);

  const fetchProjectData = async () => {
    try {
      const res = await fetch(`${API_BASE}/api/v2/projects/${projectId}`);
      const data = await res.json();
      if (data.status === 'ok') {
        setProject(data.project);
        setTasks(data.tasks || []);
        setMilestones(data.milestones || []);
      }
    } catch (error) {
      console.error('Error fetching project:', error);
      setMessage({ type: 'error', text: 'Failed to load project data' });
    } finally {
      setLoading(false);
    }
  };

  const updateProject = async (updates: Partial<Project>) => {
    setSaving(true);
    try {
      const res = await fetch(`${API_BASE}/api/v2/projects/${projectId}`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(updates),
      });
      if (res.ok) {
        setMessage({ type: 'success', text: 'Project updated successfully!' });
        await fetchProjectData();
      } else {
        setMessage({ type: 'error', text: 'Failed to update project' });
      }
    } catch (error) {
      setMessage({ type: 'error', text: 'Network error' });
    } finally {
      setSaving(false);
    }
  };

  const createTask = async (taskData: Partial<Task>) => {
    try {
      const res = await fetch(`${API_BASE}/api/v2/projects/${projectId}/tasks`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(taskData),
      });
      if (res.ok) {
        setMessage({ type: 'success', text: 'Task created!' });
        await fetchProjectData();
      }
    } catch (error) {
      setMessage({ type: 'error', text: 'Failed to create task' });
    }
  };

  const updateTask = async (taskId: string, updates: Partial<Task>) => {
    try {
      const res = await fetch(`${API_BASE}/api/v2/projects/${projectId}/tasks/${taskId}`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(updates),
      });
      if (res.ok) {
        setMessage({ type: 'success', text: 'Task updated!' });
        await fetchProjectData();
      }
    } catch (error) {
      setMessage({ type: 'error', text: 'Failed to update task' });
    }
  };

  const createMilestone = async (milestoneData: { name: string; target_date: string }) => {
    try {
      const res = await fetch(`${API_BASE}/api/v2/projects/${projectId}/milestones`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(milestoneData),
      });
      if (res.ok) {
        setMessage({ type: 'success', text: 'Milestone created!' });
        await fetchProjectData();
      }
    } catch (error) {
      setMessage({ type: 'error', text: 'Failed to create milestone' });
    }
  };

  if (loading) {
    return <div className="p-8 text-center">Loading project...</div>;
  }

  if (!project) {
    return <div className="p-8 text-center text-red-600">Project not found</div>;
  }

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-xl shadow-2xl max-w-6xl w-full max-h-[90vh] overflow-hidden flex flex-col">
        {/* Header */}
        <div className="bg-blue-600 text-white p-6 flex justify-between items-center">
          <div>
            <h2 className="text-2xl font-bold">{project.name}</h2>
            <p className="text-blue-100 text-sm">Project ID: {project.project_id}</p>
          </div>
          <button onClick={onClose} className="text-white hover:text-gray-200">
            <X className="w-6 h-6" />
          </button>
        </div>

        {/* Message */}
        {message && (
          <div className={`px-6 py-3 ${message.type === 'success' ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'}`}>
            {message.text}
          </div>
        )}

        {/* Tabs */}
        <div className="flex border-b border-gray-200 px-6">
          {(['details', 'tasks', 'budget', 'milestones', 'participants', 'emm'] as const).map((tab) => (
            <button
              key={tab}
              onClick={() => setActiveTab(tab)}
              className={`px-4 py-3 font-medium capitalize ${
                activeTab === tab
                  ? 'border-b-2 border-blue-600 text-blue-600'
                  : 'text-gray-600 hover:text-gray-800'
              }`}
            >
              {tab}
            </button>
          ))}
        </div>

        {/* Content */}
        <div className="flex-1 overflow-y-auto p-6">
          {activeTab === 'details' && (
            <DetailsTab project={project} onUpdate={updateProject} saving={saving} />
          )}
          {activeTab === 'tasks' && (
            <TasksTab tasks={tasks} onCreate={createTask} onUpdate={updateTask} />
          )}
          {activeTab === 'budget' && (
            <BudgetTab project={project} onUpdate={updateProject} saving={saving} />
          )}
          {activeTab === 'milestones' && (
            <MilestonesTab milestones={milestones} onCreate={createMilestone} projectId={projectId} />
          )}
          {activeTab === 'participants' && (
            <ParticipantsTab projectId={projectId} />
          )}
          {activeTab === 'emm' && (
            <EmmTab projectId={projectId} />
          )}
        </div>
      </div>
    </div>
  );
};

// Details Tab
const DetailsTab: React.FC<{ project: Project; onUpdate: (updates: Partial<Project>) => void; saving: boolean }> = ({ project, onUpdate, saving }) => {
  const [formData, setFormData] = useState(project);

  return (
    <div className="space-y-6">
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">Project Name</label>
          <input
            type="text"
            value={formData.name}
            onChange={(e) => setFormData({ ...formData, name: e.target.value })}
            className="w-full px-3 py-2 border border-gray-300 rounded-md"
          />
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">Status</label>
          <select
            value={formData.status}
            onChange={(e) => setFormData({ ...formData, status: e.target.value })}
            className="w-full px-3 py-2 border border-gray-300 rounded-md"
          >
            <option value="planning">Planning</option>
            <option value="in_progress">In Progress</option>
            <option value="at_risk">At Risk</option>
            <option value="blocked">Blocked</option>
            <option value="completed">Completed</option>
            <option value="on_hold">On Hold</option>
            <option value="canceled">Canceled</option>
          </select>
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">Owner</label>
          <input
            type="text"
            value={formData.owner_id}
            onChange={(e) => setFormData({ ...formData, owner_id: e.target.value })}
            className="w-full px-3 py-2 border border-gray-300 rounded-md"
          />
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">Progress (%)</label>
          <input
            type="number"
            min="0"
            max="100"
            value={formData.percent_complete}
            onChange={(e) => setFormData({ ...formData, percent_complete: parseInt(e.target.value) })}
            className="w-full px-3 py-2 border border-gray-300 rounded-md"
          />
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">Start Date</label>
          <input
            type="date"
            value={formData.start_date?.split('T')[0] || ''}
            onChange={(e) => setFormData({ ...formData, start_date: e.target.value })}
            className="w-full px-3 py-2 border border-gray-300 rounded-md"
          />
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">Target Date</label>
          <input
            type="date"
            value={formData.target_date?.split('T')[0] || ''}
            onChange={(e) => setFormData({ ...formData, target_date: e.target.value })}
            className="w-full px-3 py-2 border border-gray-300 rounded-md"
          />
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">Risk Level</label>
          <select
            value={formData.risk_level || ''}
            onChange={(e) => setFormData({ ...formData, risk_level: e.target.value })}
            className="w-full px-3 py-2 border border-gray-300 rounded-md"
          >
            <option value="">None</option>
            <option value="low">Low</option>
            <option value="medium">Medium</option>
            <option value="high">High</option>
            <option value="critical">Critical</option>
          </select>
        </div>
      </div>

      <div>
        <label className="block text-sm font-medium text-gray-700 mb-1">Objectives</label>
        <textarea
          value={formData.objectives}
          onChange={(e) => setFormData({ ...formData, objectives: e.target.value })}
          rows={4}
          className="w-full px-3 py-2 border border-gray-300 rounded-md"
        />
      </div>

      <div>
        <label className="block text-sm font-medium text-gray-700 mb-1">Blockers / Risks</label>
        <textarea
          value={formData.blockers || ''}
          onChange={(e) => setFormData({ ...formData, blockers: e.target.value })}
          rows={3}
          className="w-full px-3 py-2 border border-gray-300 rounded-md"
          placeholder="Describe any blockers or risks..."
        />
      </div>

      <button
        onClick={() => onUpdate(formData)}
        disabled={saving}
        className="w-full flex items-center justify-center px-6 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50"
      >
        <Save className="w-5 h-5 mr-2" />
        {saving ? 'Saving...' : 'Save Changes'}
      </button>
    </div>
  );
};

// Tasks Tab
const TasksTab: React.FC<{ tasks: Task[]; onCreate: (task: Partial<Task>) => void; onUpdate: (taskId: string, updates: Partial<Task>) => void }> = ({ tasks, onCreate, onUpdate }) => {
  const [showForm, setShowForm] = useState(false);
  const [newTask, setNewTask] = useState<Partial<Task>>({
    title: '',
    description: '',
    assigned_to: '',
    due_date: '',
    status: 'open',
    priority: 'medium',
  });

  const handleCreate = () => {
    onCreate(newTask);
    setNewTask({ title: '', description: '', assigned_to: '', due_date: '', status: 'open', priority: 'medium' });
    setShowForm(false);
  };

  return (
    <div className="space-y-4">
      <div className="flex justify-between items-center">
        <h3 className="text-lg font-semibold">Tasks ({tasks.length})</h3>
        <button
          onClick={() => setShowForm(!showForm)}
          className="flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
        >
          <Plus className="w-4 h-4" />
          Add Task
        </button>
      </div>

      {showForm && (
        <div className="bg-gray-50 rounded-lg p-4 space-y-3">
          <input
            type="text"
            placeholder="Task title"
            value={newTask.title}
            onChange={(e) => setNewTask({ ...newTask, title: e.target.value })}
            className="w-full px-3 py-2 border border-gray-300 rounded-md"
          />
          <textarea
            placeholder="Description"
            value={newTask.description}
            onChange={(e) => setNewTask({ ...newTask, description: e.target.value })}
            rows={2}
            className="w-full px-3 py-2 border border-gray-300 rounded-md"
          />
          <div className="grid grid-cols-2 gap-3">
            <input
              type="text"
              placeholder="Assigned to"
              value={newTask.assigned_to}
              onChange={(e) => setNewTask({ ...newTask, assigned_to: e.target.value })}
              className="px-3 py-2 border border-gray-300 rounded-md"
            />
            <input
              type="date"
              value={newTask.due_date}
              onChange={(e) => setNewTask({ ...newTask, due_date: e.target.value })}
              className="px-3 py-2 border border-gray-300 rounded-md"
            />
            <select
              value={newTask.priority}
              onChange={(e) => setNewTask({ ...newTask, priority: e.target.value })}
              className="px-3 py-2 border border-gray-300 rounded-md"
            >
              <option value="low">Low Priority</option>
              <option value="medium">Medium Priority</option>
              <option value="high">High Priority</option>
            </select>
            <button
              onClick={handleCreate}
              className="px-4 py-2 bg-green-600 text-white rounded-md hover:bg-green-700"
            >
              Create Task
            </button>
          </div>
        </div>
      )}

      <div className="space-y-2">
        {tasks.map((task) => (
          <div key={task.task_id} className="bg-white border border-gray-200 rounded-lg p-4">
            <div className="flex justify-between items-start">
              <div className="flex-1">
                <h4 className="font-medium text-gray-800">{task.title}</h4>
                {task.description && <p className="text-sm text-gray-600 mt-1">{task.description}</p>}
                <div className="flex gap-4 mt-2 text-xs text-gray-500">
                  <span>👤 {task.assigned_to || 'Unassigned'}</span>
                  <span>📅 {task.due_date ? new Date(task.due_date).toLocaleDateString() : 'No due date'}</span>
                  <span className={`font-semibold ${
                    task.priority === 'high' ? 'text-red-600' :
                    task.priority === 'medium' ? 'text-yellow-600' :
                    'text-gray-600'
                  }`}>
                    {task.priority?.toUpperCase()}
                  </span>
                </div>
              </div>
              <select
                value={task.status}
                onChange={(e) => onUpdate(task.task_id, { status: e.target.value })}
                className={`px-3 py-1 text-sm rounded-full border ${
                  task.status === 'completed' ? 'bg-green-100 text-green-800 border-green-300' :
                  task.status === 'in_progress' ? 'bg-blue-100 text-blue-800 border-blue-300' :
                  task.status === 'blocked' ? 'bg-red-100 text-red-800 border-red-300' :
                  'bg-gray-100 text-gray-800 border-gray-300'
                }`}
              >
                <option value="open">Open</option>
                <option value="in_progress">In Progress</option>
                <option value="blocked">Blocked</option>
                <option value="completed">Completed</option>
              </select>
            </div>
          </div>
        ))}
        {tasks.length === 0 && (
          <p className="text-gray-500 text-center py-8">No tasks yet. Click "Add Task" to create one.</p>
        )}
      </div>
    </div>
  );
};

// Budget Tab
const BudgetTab: React.FC<{ project: Project; onUpdate: (updates: Partial<Project>) => void; saving: boolean }> = ({ project, onUpdate, saving }) => {
  const [fundingAmount, setFundingAmount] = useState(project.funding_amount || 0);
  const [spentAmount, setSpentAmount] = useState(project.spent_amount || 0);
  const [wsConnected, setWsConnected] = useState(false);

  // Listen for live budget updates via websocket
  React.useEffect(() => {
    let ws: WebSocket | null = null;

    try {
      const base = API_BASE.startsWith('https') ? API_BASE.replace(/^https/, 'wss') : API_BASE.replace(/^http/, 'ws');
      ws = new WebSocket(`${base}/api/v2/projects/${project.project_id}/ws/budget`);
      ws.onopen = () => setWsConnected(true);
      ws.onmessage = (ev) => {
        try {
          const msg = JSON.parse(ev.data);
          if (msg && msg.type === 'snapshot') {
            if (typeof msg.funding_amount !== 'undefined') setFundingAmount(Number(msg.funding_amount) || 0);
            if (typeof msg.spent_amount !== 'undefined') setSpentAmount(Number(msg.spent_amount) || 0);
          }
        } catch (e) {
          // ignore parse errors
        }
      };
      ws.onclose = () => setWsConnected(false);
      ws.onerror = () => setWsConnected(false);
    } catch (e) {
      // ignore
    }

    return () => {
      try { ws && ws.close(); } catch (e) {}
    };
  }, [project.project_id]);

  const remaining = fundingAmount - spentAmount;
  const utilization = fundingAmount > 0 ? (spentAmount / fundingAmount * 100) : 0;

  const handleSave = () => {
    onUpdate({ funding_amount: fundingAmount, spent_amount: spentAmount });
  };

  return (
    <div className="space-y-6">
      <div className="bg-blue-50 border border-blue-200 rounded-lg p-6">
        <h3 className="text-lg font-semibold text-blue-900 mb-4 flex items-center gap-2">
          <DollarSign className="w-5 h-5" />
          Budget Overview
        </h3>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-4">
          <div>
            <p className="text-sm text-blue-700">Total Budget</p>
            <p className="text-2xl font-bold text-blue-900">${fundingAmount.toLocaleString()}</p>
          </div>
          <div>
            <p className="text-sm text-blue-700">Spent</p>
            <p className="text-2xl font-bold text-blue-900">${spentAmount.toLocaleString()}</p>
          </div>
          <div>
            <p className="text-sm text-blue-700">Remaining</p>
            <p className="text-2xl font-bold text-green-600">${remaining.toLocaleString()}</p>
          </div>
        </div>
        <div>
          <div className="flex justify-between text-sm mb-2">
            <span className="text-blue-700">Budget Utilization</span>
            <span className="font-semibold text-blue-900">{utilization.toFixed(1)}%</span>
          </div>
          <div className="w-full bg-gray-200 rounded-full h-4">
            <div
              className={`h-4 rounded-full transition-all ${
                utilization > 90 ? 'bg-red-500' :
                utilization > 75 ? 'bg-yellow-500' :
                'bg-green-500'
              }`}
              style={{ width: `${Math.min(utilization, 100)}%` }}
            />
          </div>
        </div>
      </div>

      <div className="space-y-4">
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">Total Funding Amount</label>
          <input
            type="number"
            min="0"
            step="0.01"
            value={fundingAmount}
            onChange={(e) => setFundingAmount(parseFloat(e.target.value) || 0)}
            className="w-full px-3 py-2 border border-gray-300 rounded-md text-lg"
          />
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">Amount Spent</label>
          <input
            type="number"
            min="0"
            step="0.01"
            value={spentAmount}
            onChange={(e) => setSpentAmount(parseFloat(e.target.value) || 0)}
            className="w-full px-3 py-2 border border-gray-300 rounded-md text-lg"
          />
        </div>

        <button
          onClick={handleSave}
          disabled={saving}
          className="w-full flex items-center justify-center px-6 py-3 bg-green-600 text-white rounded-lg hover:bg-green-700 disabled:opacity-50"
        >
          <Save className="w-5 h-5 mr-2" />
          {saving ? 'Saving Budget...' : 'Update Budget'}
        </button>
      </div>
    </div>
  );
};

// Milestones Tab
const MilestonesTab: React.FC<{ milestones: Milestone[]; onCreate: (milestone: { name: string; target_date: string }) => void; projectId: string }> = ({ milestones, onCreate, projectId }) => {
  const [showForm, setShowForm] = useState(false);
  const [newMilestone, setNewMilestone] = useState({ name: '', target_date: '' });

  const handleCreate = () => {
    onCreate(newMilestone);
    setNewMilestone({ name: '', target_date: '' });
    setShowForm(false);
  };

  return (
    <div className="space-y-4">
      <div className="flex justify-between items-center">
        <h3 className="text-lg font-semibold">Milestones ({milestones.length})</h3>
        <button
          onClick={() => setShowForm(!showForm)}
          className="flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
        >
          <Plus className="w-4 h-4" />
          Add Milestone
        </button>
      </div>

      {showForm && (
        <div className="bg-gray-50 rounded-lg p-4 space-y-3">
          <input
            type="text"
            placeholder="Milestone name"
            value={newMilestone.name}
            onChange={(e) => setNewMilestone({ ...newMilestone, name: e.target.value })}
            className="w-full px-3 py-2 border border-gray-300 rounded-md"
          />
          <div className="flex gap-3">
            <input
              type="date"
              value={newMilestone.target_date}
              onChange={(e) => setNewMilestone({ ...newMilestone, target_date: e.target.value })}
              className="flex-1 px-3 py-2 border border-gray-300 rounded-md"
            />
            <button
              onClick={handleCreate}
              className="px-6 py-2 bg-green-600 text-white rounded-md hover:bg-green-700"
            >
              Create
            </button>
          </div>
        </div>
      )}

      <div className="space-y-2">
        {milestones.map((milestone) => (
          <div key={milestone.milestone_id} className="bg-white border border-gray-200 rounded-lg p-4 flex items-center gap-4">
            <div className={`w-3 h-3 rounded-full ${milestone.actual_date ? 'bg-green-500' : 'bg-gray-300'}`} />
            <div className="flex-1">
              <h4 className="font-medium text-gray-800">{milestone.name}</h4>
              <p className="text-sm text-gray-600">
                Target: {new Date(milestone.target_date).toLocaleDateString()}
                {milestone.actual_date && ` | Completed: ${new Date(milestone.actual_date).toLocaleDateString()}`}
              </p>
            </div>
            {milestone.actual_date && <CheckCircle className="w-5 h-5 text-green-500" />}
          </div>
        ))}
        {milestones.length === 0 && (
          <p className="text-gray-500 text-center py-8">No milestones yet. Click "Add Milestone" to create one.</p>
        )}
      </div>
    </div>
  );
};

// Participants Tab
const ParticipantsTab: React.FC<{ projectId: string }> = ({ projectId }) => {
  const [participants, setParticipants] = React.useState<any[]>([]);
  const [personId, setPersonId] = React.useState('');
  const [role, setRole] = React.useState('');

  const load = async () => {
    try {
      let res = await fetch(`${API_BASE}/api/v2/projects_pm/projects/${projectId}/participants`);
      if (!res.ok) res = await fetch(`${API_BASE}/api/v2/projects/${projectId}/participants`);
      const data = await res.json();
      if (data && Array.isArray(data)) setParticipants(data);
      else if (data && data.status === 'ok' && Array.isArray(data.participants)) setParticipants(data.participants);
    } catch (e) {
      console.error('Failed loading participants', e);
    }
  };

  React.useEffect(() => { load(); }, [projectId]);

  const add = async () => {
    try {
      const res = await fetch(`${API_BASE}/api/v2/projects_pm/projects/${projectId}/participants`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ person_id: personId, role }),
      });
      if (res.ok) { setPersonId(''); setRole(''); await load(); }
    } catch (e) { console.error(e); }
  };

  return (
    <div className="space-y-4">
      <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
        <input value={personId} onChange={(e) => setPersonId(e.target.value)} placeholder="Person ID" className="px-3 py-2 border rounded-md" />
        <input value={role} onChange={(e) => setRole(e.target.value)} placeholder="Role" className="px-3 py-2 border rounded-md" />
        <button onClick={add} className="px-4 py-2 bg-blue-600 text-white rounded-md">Add Participant</button>
      </div>
      <div className="bg-white rounded-md shadow p-4">
        <h4 className="font-semibold mb-2">Participants ({participants.length})</h4>
        <ul className="space-y-2">
          {participants.map((p) => (
            <li key={p.participant_id || p.id || JSON.stringify(p)} className="flex justify-between">
              <div>
                <div className="font-medium">{p.person_id || p.person || 'unknown'}</div>
                <div className="text-sm text-gray-500">{p.role || p.unit || ''}</div>
              </div>
            </li>
          ))}
        </ul>
      </div>
    </div>
  );
};

// EMM Tab
const EmmTab: React.FC<{ projectId: string }> = ({ projectId }) => {
  const [mappings, setMappings] = React.useState<any[]>([]);
  const [payload, setPayload] = React.useState('');

  const load = async () => {
    try {
      let res = await fetch(`${API_BASE}/api/v2/projects_pm/projects/${projectId}/emm`);
      if (!res.ok) res = await fetch(`${API_BASE}/api/v2/projects/${projectId}/emm`);
      const data = await res.json();
      if (data && data.status === 'ok') setMappings(data.mappings || data.mappings || []);
    } catch (e) { console.error(e); }
  };

  React.useEffect(() => { load(); }, [projectId]);

  const doImport = async () => {
    try {
      const obj = payload ? JSON.parse(payload) : {};
      const res = await fetch(`${API_BASE}/api/v2/projects_pm/projects/${projectId}/emm/import`, {
        method: 'POST', headers: {'Content-Type':'application/json'}, body: JSON.stringify(obj)
      });
      if (res.ok) { setPayload(''); await load(); }
    } catch (e) { console.error(e); }
  };

  return (
    <div className="space-y-4">
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-1">EMM JSON Payload</label>
        <textarea value={payload} onChange={(e) => setPayload(e.target.value)} rows={6} className="w-full border rounded-md px-3 py-2" />
        <div className="flex justify-end mt-2">
          <button onClick={doImport} className="px-4 py-2 bg-indigo-600 text-white rounded-md">Import</button>
        </div>
      </div>

      <div className="bg-white rounded-md shadow p-4">
        <h4 className="font-semibold mb-2">Mappings ({mappings.length})</h4>
        <ul className="space-y-2">
          {mappings.map((m) => (
            <li key={m.mapping_id || JSON.stringify(m)} className="flex justify-between">
              <div>
                <div className="font-medium">{m.mapping_id}</div>
                <div className="text-sm text-gray-500">{JSON.stringify(m.payload || m.raw_payload || {})}</div>
              </div>
            </li>
          ))}
        </ul>
      </div>
    </div>
  );
};
