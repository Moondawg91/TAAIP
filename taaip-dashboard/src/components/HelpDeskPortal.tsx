import React, { useState } from 'react';
import { HelpCircle, Send, CheckCircle, AlertCircle, User, Shield, Eye, Edit, Database } from 'lucide-react';
import { API_BASE } from '../config/api';

export type AccessLevel = 'tier_1' | 'tier_2' | 'tier_3' | 'tier_4';

export interface UserAccess {
  userId: string;
  name: string;
  email: string;
  dodId: string;
  accessLevel: AccessLevel;
  permissions: {
    canView: boolean;
    canEdit: boolean;
    canCreate: boolean;
    canDelete: boolean;
    canExport: boolean;
    canManageUsers: boolean;
    canAccessAdmin: boolean;
  };
}

interface HelpdeskRequest {
  id?: string;
  type: 'access_request' | 'feature_request' | 'bug_report' | 'upgrade_request' | 'training' | 'other';
  priority: 'low' | 'medium' | 'high' | 'critical';
  title: string;
  description: string;
  requestedAccessLevel?: AccessLevel;
  currentAccessLevel?: AccessLevel;
  status?: 'pending' | 'in_progress' | 'resolved' | 'rejected';
  submittedBy?: string;
  submittedAt?: string;
}

const ACCESS_LEVEL_INFO: Record<AccessLevel, { label: string; icon: React.ReactNode; color: string; description: string }> = {
  tier_1: {
    label: 'Tier 1 Access',
    icon: <Eye className="w-4 h-4" />,
    color: 'bg-gray-100 text-gray-700 border-gray-400',
    description: 'Can view dashboards and reports. Limited export permissions.'
  },
  tier_2: {
    label: 'Tier 2 Access',
    icon: <User className="w-4 h-4" />,
    color: 'bg-gray-100 text-gray-700 border-gray-400',
    description: 'Can view all data, export reports, create filters, and save custom views.'
  },
  tier_3: {
    label: 'Tier 3 Access',
    icon: <Edit className="w-4 h-4" />,
    color: 'bg-gray-100 text-gray-700 border-gray-400',
    description: 'Can edit data, create/modify projects, and manage team tasks.'
  },
  tier_4: {
    label: 'Tier 4 Access',
    icon: <Shield className="w-4 h-4" />,
    color: 'bg-gray-100 text-gray-700 border-gray-400',
    description: 'Full system access including user management, configuration, and database administration.'
  }
};

export const HelpDeskPortal: React.FC<{ currentUser?: UserAccess }> = ({ currentUser }) => {
  const [showForm, setShowForm] = useState(false);
  const [formData, setFormData] = useState<HelpdeskRequest>({
    type: 'access_request',
    priority: 'medium',
    title: '',
    description: '',
    requestedAccessLevel: 'tier_2',
    currentAccessLevel: currentUser?.accessLevel || 'tier_1'
  });
  const [submitted, setSubmitted] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    try {
      const response = await fetch(`${API_BASE}/api/v2/helpdesk/requests`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          ...formData,
          submittedBy: currentUser?.dodId || 'anonymous',
          submittedAt: new Date().toISOString()
        })
      });

      if (response.ok) {
        setSubmitted(true);
        setTimeout(() => {
          setSubmitted(false);
          setShowForm(false);
          setFormData({
            type: 'access_request',
            priority: 'medium',
            title: '',
            description: '',
            requestedAccessLevel: 'tier_2',
            currentAccessLevel: currentUser?.accessLevel || 'tier_1'
          });
        }, 3000);
      }
    } catch (error) {
      console.error('Error submitting helpdesk request:', error);
    }
  };

  return (
    <div className="bg-white rounded-xl shadow-md border-2 border-gray-200">
      {/* Header */}
      <div className="bg-gradient-to-r from-blue-600 to-blue-800 text-white px-6 py-4 border-b-2 border-blue-900 rounded-t-xl">
        <h2 className="text-xl font-bold uppercase tracking-wider flex items-center gap-2">
          <HelpCircle className="w-6 h-6 text-blue-200" />
          Help Desk Portal
        </h2>
        <p className="text-sm text-blue-100 mt-1">Submit requests for support, access, features, or upgrades</p>
      </div>

      {!showForm && !submitted ? (
        <>
          {/* Access Level Info */}
          {currentUser && (
            <div className="p-6 border-b border-gray-200 bg-gray-50">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-gray-600 mb-1">Your Current Access Level</p>
                  <div className={`inline-flex items-center gap-2 px-4 py-2 rounded-lg border-2 font-semibold ${ACCESS_LEVEL_INFO[currentUser.accessLevel].color}`}>
                    {ACCESS_LEVEL_INFO[currentUser.accessLevel].icon}
                    {ACCESS_LEVEL_INFO[currentUser.accessLevel].label}
                  </div>
                  <p className="text-xs text-gray-600 mt-2">{ACCESS_LEVEL_INFO[currentUser.accessLevel].description}</p>
                </div>
                <div className="text-right">
                  <p className="text-xs text-gray-500">DOD ID</p>
                  <p className="font-mono font-semibold text-gray-800">{currentUser.dodId}</p>
                </div>
              </div>
            </div>
          )}

          {/* Request Types */}
          <div className="p-6">
            <h3 className="text-lg font-bold text-gray-800 mb-4">What do you need help with?</h3>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              <button
                onClick={() => {
                  setFormData({ ...formData, type: 'access_request' });
                  setShowForm(true);
                }}
                className="p-4 border-2 border-gray-300 rounded-lg hover:border-blue-500 hover:bg-blue-50 transition-all text-left"
                title="Request access level upgrade or change permissions"
              >
                <Shield className="w-8 h-8 text-blue-600 mb-2" />
                <h4 className="font-bold text-gray-800">Access Request</h4>
                <p className="text-sm text-gray-600 mt-1">Request higher access level or permissions</p>
              </button>

              <button
                onClick={() => {
                  setFormData({ ...formData, type: 'feature_request' });
                  setShowForm(true);
                }}
                className="p-4 border-2 border-gray-300 rounded-lg hover:border-green-500 hover:bg-green-50 transition-all text-left"
                title="Suggest new features or enhancements"
              >
                <Edit className="w-8 h-8 text-green-600 mb-2" />
                <h4 className="font-bold text-gray-800">Feature Request</h4>
                <p className="text-sm text-gray-600 mt-1">Suggest new features or improvements</p>
              </button>

              <button
                onClick={() => {
                  setFormData({ ...formData, type: 'upgrade_request' });
                  setShowForm(true);
                }}
                className="p-4 border-2 border-gray-300 rounded-lg hover:border-purple-500 hover:bg-purple-50 transition-all text-left"
                title="Request system upgrades or enhancements"
              >
                <Database className="w-8 h-8 text-purple-600 mb-2" />
                <h4 className="font-bold text-gray-800">Upgrade Request</h4>
                <p className="text-sm text-gray-600 mt-1">Request system upgrades or enhancements</p>
              </button>

              <button
                onClick={() => {
                  setFormData({ ...formData, type: 'bug_report' });
                  setShowForm(true);
                }}
                className="p-4 border-2 border-gray-300 rounded-lg hover:border-red-500 hover:bg-red-50 transition-all text-left"
                title="Report technical issues or bugs"
              >
                <AlertCircle className="w-8 h-8 text-red-600 mb-2" />
                <h4 className="font-bold text-gray-800">Bug Report</h4>
                <p className="text-sm text-gray-600 mt-1">Report technical issues or problems</p>
              </button>

              <button
                onClick={() => {
                  setFormData({ ...formData, type: 'training' });
                  setShowForm(true);
                }}
                className="p-4 border-2 border-gray-300 rounded-lg hover:border-yellow-500 hover:bg-yellow-50 transition-all text-left"
                title="Request training or assistance"
              >
                <User className="w-8 h-8 text-yellow-600 mb-2" />
                <h4 className="font-bold text-gray-800">Training Request</h4>
                <p className="text-sm text-gray-600 mt-1">Request training or user assistance</p>
              </button>

              <button
                onClick={() => {
                  setFormData({ ...formData, type: 'other' });
                  setShowForm(true);
                }}
                className="p-4 border-2 border-gray-300 rounded-lg hover:border-gray-500 hover:bg-gray-50 transition-all text-left"
                title="Other support requests"
              >
                <HelpCircle className="w-8 h-8 text-gray-600 mb-2" />
                <h4 className="font-bold text-gray-800">Other</h4>
                <p className="text-sm text-gray-600 mt-1">General support or other requests</p>
              </button>
            </div>
          </div>

          {/* Access Level Guide */}
          <div className="p-6 bg-gray-50 border-t border-gray-200 rounded-b-xl">
            <h3 className="text-sm font-bold text-gray-700 uppercase mb-3">Access Level Guide</h3>
            <div className="space-y-2">
              {(Object.keys(ACCESS_LEVEL_INFO) as AccessLevel[]).map((level) => (
                <div key={level} className="flex items-start gap-3 text-sm">
                  <div className={`px-3 py-1 rounded border ${ACCESS_LEVEL_INFO[level].color} flex items-center gap-1`}>
                    {ACCESS_LEVEL_INFO[level].icon}
                    <span className="font-semibold">{ACCESS_LEVEL_INFO[level].label}</span>
                  </div>
                  <p className="text-gray-600 flex-1">{ACCESS_LEVEL_INFO[level].description}</p>
                </div>
              ))}
            </div>
          </div>
        </>
      ) : submitted ? (
        <div className="p-12 text-center">
          <CheckCircle className="w-16 h-16 text-green-500 mx-auto mb-4" />
          <h3 className="text-2xl font-bold text-gray-800 mb-2">Request Submitted!</h3>
          <p className="text-gray-600 mb-4">Your request has been received and will be reviewed by our team.</p>
          <p className="text-sm text-gray-500">You'll receive a notification once there's an update.</p>
        </div>
      ) : (
        <form onSubmit={handleSubmit} className="p-6">
          <div className="mb-4">
            <button
              type="button"
              onClick={() => setShowForm(false)}
              className="text-blue-600 hover:text-blue-700 text-sm font-medium"
            >
              ← Back to request types
            </button>
          </div>

          <div className="space-y-4">
            <div>
              <label className="block text-sm font-semibold text-gray-700 mb-2">Request Type</label>
              <select
                value={formData.type}
                onChange={(e) => setFormData({ ...formData, type: e.target.value as any })}
                className="w-full px-4 py-2 border border-gray-300 rounded-lg"
                required
              >
                <option value="access_request">Access Request</option>
                <option value="feature_request">Feature Request</option>
                <option value="upgrade_request">Upgrade Request</option>
                <option value="bug_report">Bug Report</option>
                <option value="training">Training Request</option>
                <option value="other">Other</option>
              </select>
            </div>

            {formData.type === 'access_request' && (
              <div>
                <label className="block text-sm font-semibold text-gray-700 mb-2">Requested Access Level</label>
                <select
                  value={formData.requestedAccessLevel}
                  onChange={(e) => setFormData({ ...formData, requestedAccessLevel: e.target.value as AccessLevel })}
                  className="w-full px-4 py-2 border border-gray-300 rounded-lg"
                  required
                >
                  <option value="standard">Standard User</option>
                  <option value="editor">Editor</option>
                  <option value="admin">Administrator</option>
                  <option value="super_admin">Super Admin</option>
                </select>
                <p className="text-xs text-gray-600 mt-1">
                  {formData.requestedAccessLevel && ACCESS_LEVEL_INFO[formData.requestedAccessLevel].description}
                </p>
              </div>
            )}

            <div>
              <label className="block text-sm font-semibold text-gray-700 mb-2">Priority</label>
              <select
                value={formData.priority}
                onChange={(e) => setFormData({ ...formData, priority: e.target.value as any })}
                className="w-full px-4 py-2 border border-gray-300 rounded-lg"
                required
              >
                <option value="low">Low - Not urgent</option>
                <option value="medium">Medium - Normal priority</option>
                <option value="high">High - Important</option>
                <option value="critical">Critical - Urgent</option>
              </select>
            </div>

            <div>
              <label className="block text-sm font-semibold text-gray-700 mb-2">Title</label>
              <input
                type="text"
                value={formData.title}
                onChange={(e) => setFormData({ ...formData, title: e.target.value })}
                className="w-full px-4 py-2 border border-gray-300 rounded-lg"
                placeholder="Brief description of your request"
                required
              />
            </div>

            <div>
              <label className="block text-sm font-semibold text-gray-700 mb-2">Detailed Description</label>
              <textarea
                value={formData.description}
                onChange={(e) => setFormData({ ...formData, description: e.target.value })}
                className="w-full px-4 py-2 border border-gray-300 rounded-lg h-32"
                placeholder="Provide detailed information about your request..."
                required
              />
            </div>

            <div className="flex gap-3 pt-4">
              <button
                type="submit"
                className="flex-1 flex items-center justify-center gap-2 px-6 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors font-semibold"
              >
                <Send className="w-5 h-5" />
                Submit Request
              </button>
              <button
                type="button"
                onClick={() => setShowForm(false)}
                className="px-6 py-3 bg-gray-200 text-gray-700 rounded-lg hover:bg-gray-300 transition-colors font-semibold"
              >
                Cancel
              </button>
            </div>
          </div>
        </form>
      )}
    </div>
  );
};
