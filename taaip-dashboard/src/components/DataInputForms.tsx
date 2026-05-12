import React, { useState } from 'react';
import { PlusCircle, Save, Calendar, DollarSign, Users, MapPin, AlertCircle } from 'lucide-react';
import { API_BASE } from '../config/api';

interface EventFormData {
  event_id: string;
  name: string;
  type: string;
  location: string;
  start_date: string;
  end_date: string;
  budget: number;
  team_size: number;
  targeting_principles: string;
  status: string;
}

interface ProjectFormData {
  project_id: string;
  name: string;
  event_id: string;
  start_date: string;
  target_date: string;
  owner_id: string;
  status: string;
  objectives: string;
  funding_amount: number;
}

export const DataInputForms: React.FC = () => {
  const [activeForm, setActiveForm] = useState<'event' | 'project'>('event');
  const [submitStatus, setSubmitStatus] = useState<{ type: 'success' | 'error' | null; message: string }>({
    type: null,
    message: '',
  });

  // Event Form
  const EventForm: React.FC = () => {
    const [eventData, setEventData] = useState<EventFormData>({
      event_id: `EVT-${Date.now()}`,
      name: '',
      type: 'recruitment_event',
      location: '',
      start_date: '',
      end_date: '',
      budget: 0,
      team_size: 0,
      targeting_principles: '',
      status: 'planned',
    });
    const [loading, setLoading] = useState(false);

    const handleSubmit = async (e: React.FormEvent) => {
      e.preventDefault();
      setLoading(true);
      setSubmitStatus({ type: null, message: '' });

      try {
        const response = await fetch(`${API_BASE}/api/v2/events`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(eventData),
        });

        if (response.ok) {
          const result = await response.json();
          setSubmitStatus({
            type: 'success',
            message: `Event "${eventData.name}" created successfully! ID: ${result.event_id}`,
          });
          // Reset form
          setEventData({
            event_id: `EVT-${Date.now()}`,
            name: '',
            type: 'recruitment_event',
            location: '',
            start_date: '',
            end_date: '',
            budget: 0,
            team_size: 0,
            targeting_principles: '',
            status: 'planned',
          });
        } else {
          const error = await response.json();
          setSubmitStatus({ type: 'error', message: error.detail || 'Failed to create event' });
        }
      } catch (err) {
        setSubmitStatus({ type: 'error', message: 'Network error. Is backend running?' });
      } finally {
        setLoading(false);
      }
    };

    return (
      <form onSubmit={handleSubmit} className="space-y-6">
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Event Name *</label>
            <input
              type="text"
              required
              value={eventData.name}
              onChange={(e) => setEventData({ ...eventData, name: e.target.value })}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500"
              placeholder="e.g., Spring Recruitment Fair"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Event Type</label>
            <select
              value={eventData.type}
              onChange={(e) => setEventData({ ...eventData, type: e.target.value })}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500"
            >
              <option value="recruitment_event">Recruitment Event</option>
              <option value="job_fair">Job Fair</option>
              <option value="college_visit">College Visit</option>
              <option value="community_outreach">Community Outreach</option>
              <option value="sporting_event">Sporting Event</option>
            </select>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              <MapPin className="inline w-4 h-4 mr-1" />
              Location *
            </label>
            <input
              type="text"
              required
              value={eventData.location}
              onChange={(e) => setEventData({ ...eventData, location: e.target.value })}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500"
              placeholder="City, State or DMA"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              <Users className="inline w-4 h-4 mr-1" />
              Team Size
            </label>
            <input
              type="number"
              min="1"
              value={eventData.team_size}
              onChange={(e) => setEventData({ ...eventData, team_size: parseInt(e.target.value) })}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              <Calendar className="inline w-4 h-4 mr-1" />
              Start Date *
            </label>
            <input
              type="date"
              required
              value={eventData.start_date}
              onChange={(e) => setEventData({ ...eventData, start_date: e.target.value })}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              <Calendar className="inline w-4 h-4 mr-1" />
              End Date *
            </label>
            <input
              type="date"
              required
              value={eventData.end_date}
              onChange={(e) => setEventData({ ...eventData, end_date: e.target.value })}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              <DollarSign className="inline w-4 h-4 mr-1" />
              Budget ($)
            </label>
            <input
              type="number"
              min="0"
              step="0.01"
              value={eventData.budget}
              onChange={(e) => setEventData({ ...eventData, budget: parseFloat(e.target.value) })}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Status</label>
            <select
              value={eventData.status}
              onChange={(e) => setEventData({ ...eventData, status: e.target.value })}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500"
            >
              <option value="planned">Planned</option>
              <option value="in_progress">In Progress</option>
              <option value="completed">Completed</option>
              <option value="cancelled">Cancelled</option>
            </select>
          </div>
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">Targeting Principles</label>
          <textarea
            value={eventData.targeting_principles}
            onChange={(e) => setEventData({ ...eventData, targeting_principles: e.target.value })}
            rows={3}
            className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500"
            placeholder="USAREC cycle phases or targeting rationale..."
          />
        </div>

        <button
          type="submit"
          disabled={loading}
          className="w-full flex items-center justify-center px-6 py-3 bg-green-600 text-white rounded-lg hover:bg-green-700 disabled:opacity-50 transition"
        >
          <Save className="w-5 h-5 mr-2" />
          {loading ? 'Creating Event...' : 'Create Event'}
        </button>
      </form>
    );
  };

  // Project Form
  const ProjectForm: React.FC = () => {
    const [projectData, setProjectData] = useState<ProjectFormData>({
      project_id: `PRJ-${Date.now()}`,
      name: '',
      event_id: '',
      start_date: '',
      target_date: '',
      owner_id: '',
      status: 'planning',
      objectives: '',
      funding_amount: 0,
    });
    const [loading, setLoading] = useState(false);

    const handleSubmit = async (e: React.FormEvent) => {
      e.preventDefault();
      setLoading(true);
      setSubmitStatus({ type: null, message: '' });

      try {
        const response = await fetch(`${API_BASE}/api/v2/projects`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(projectData),
        });

        if (response.ok) {
          const result = await response.json();
          setSubmitStatus({
            type: 'success',
            message: `Project "${projectData.name}" created successfully!`,
          });
          setProjectData({
            project_id: `PRJ-${Date.now()}`,
            name: '',
            event_id: '',
            start_date: '',
            target_date: '',
            owner_id: '',
            status: 'planning',
            objectives: '',
            funding_amount: 0,
          });
        } else {
          const error = await response.json();
          setSubmitStatus({ type: 'error', message: error.detail || 'Failed to create project' });
        }
      } catch (err) {
        setSubmitStatus({ type: 'error', message: 'Network error. Is backend running?' });
      } finally {
        setLoading(false);
      }
    };

    return (
      <form onSubmit={handleSubmit} className="space-y-6">
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Project Name *</label>
            <input
              type="text"
              required
              value={projectData.name}
              onChange={(e) => setProjectData({ ...projectData, name: e.target.value })}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500"
              placeholder="e.g., Q1 Digital Campaign"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Owner/Manager *</label>
            <input
              type="text"
              required
              value={projectData.owner_id}
              onChange={(e) => setProjectData({ ...projectData, owner_id: e.target.value })}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500"
              placeholder="Name or ID"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Start Date *</label>
            <input
              type="date"
              required
              value={projectData.start_date}
              onChange={(e) => setProjectData({ ...projectData, start_date: e.target.value })}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Target Date *</label>
            <input
              type="date"
              required
              value={projectData.target_date}
              onChange={(e) => setProjectData({ ...projectData, target_date: e.target.value })}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Funding Amount ($)</label>
            <input
              type="number"
              min="0"
              step="0.01"
              value={projectData.funding_amount}
              onChange={(e) => setProjectData({ ...projectData, funding_amount: parseFloat(e.target.value) })}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Status</label>
            <select
              value={projectData.status}
              onChange={(e) => setProjectData({ ...projectData, status: e.target.value })}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500"
            >
              <option value="planning">Planning</option>
              <option value="in_progress">In Progress</option>
              <option value="on_hold">On Hold</option>
              <option value="at_risk">At Risk</option>
              <option value="completed">Completed</option>
            </select>
          </div>

          <div className="md:col-span-2">
            <label className="block text-sm font-medium text-gray-700 mb-1">Event ID (Optional)</label>
            <input
              type="text"
              value={projectData.event_id}
              onChange={(e) => setProjectData({ ...projectData, event_id: e.target.value })}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500"
              placeholder="Link to existing event (e.g., EVT-12345)"
            />
          </div>
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">Objectives *</label>
          <textarea
            required
            value={projectData.objectives}
            onChange={(e) => setProjectData({ ...projectData, objectives: e.target.value })}
            rows={3}
            className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500"
            placeholder="Project goals and success criteria..."
          />
        </div>

        <button
          type="submit"
          disabled={loading}
          className="w-full flex items-center justify-center px-6 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 transition"
        >
          <Save className="w-5 h-5 mr-2" />
          {loading ? 'Creating Project...' : 'Create Project'}
        </button>
      </form>
    );
  };

  return (
    <div className="p-4 md:p-8 space-y-6">
      <div className="flex items-center justify-between border-b pb-4">
        <h2 className="text-3xl font-extrabold text-gray-900">
          <PlusCircle className="inline-block mr-2 w-7 h-7 text-green-600" />
          Data Input Center
        </h2>
      </div>

      {/* Tab Navigation */}
      <div className="flex space-x-2 border-b">
        <button
          onClick={() => setActiveForm('event')}
          className={`px-4 py-3 font-medium transition ${
            activeForm === 'event'
              ? 'border-b-4 border-green-600 text-green-700'
              : 'text-gray-600 hover:text-gray-800'
          }`}
        >
          Create Event
        </button>
        <button
          onClick={() => setActiveForm('project')}
          className={`px-4 py-3 font-medium transition ${
            activeForm === 'project'
              ? 'border-b-4 border-blue-600 text-blue-700'
              : 'text-gray-600 hover:text-gray-800'
          }`}
        >
          Create Project
        </button>
      </div>

      {/* Status Messages */}
      {submitStatus.type && (
        <div
          className={`p-4 rounded-lg flex items-start ${
            submitStatus.type === 'success' ? 'bg-green-50 border border-green-200' : 'bg-red-50 border border-red-200'
          }`}
        >
          <AlertCircle
            className={`w-5 h-5 mr-2 mt-0.5 ${submitStatus.type === 'success' ? 'text-green-600' : 'text-red-600'}`}
          />
          <p className={`text-sm ${submitStatus.type === 'success' ? 'text-green-800' : 'text-red-800'}`}>
            {submitStatus.message}
          </p>
        </div>
      )}

      {/* Form Content */}
      <div className="bg-white p-6 rounded-xl shadow-lg">
        {activeForm === 'event' && <EventForm />}
        {activeForm === 'project' && <ProjectForm />}
      </div>

      {/* Help Text */}
      <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
        <h4 className="font-semibold text-blue-900 mb-2">💡 Quick Tips:</h4>
        <ul className="text-sm text-blue-800 space-y-1 list-disc list-inside">
          <li>All data is saved to your database automatically</li>
          <li>Required fields are marked with *</li>
          <li>IDs are auto-generated but can be customized</li>
          <li>Backend must be running on port 8000</li>
        </ul>
      </div>
    </div>
  );
};
