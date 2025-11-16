import React, { useState, useEffect } from 'react';
import {
  TrendingUp, Cpu, RefreshCw, Users, BarChart3, ChevronRight,
  Calendar, FileText, Menu, X, PieChart, Activity
} from 'lucide-react';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';
import axios from 'axios';

// API Client
const apiClient = axios.create({
  baseURL: '/api/v2',
  headers: { 'X-API-KEY': 'devtoken123' }
});

// === TYPES ===
interface FunnelStage {
  stage: string;
  count: number;
  conversionRate: number;
}

interface ModelStatus {
  accuracy: number;
  training_samples: number;
  last_updated: string | null;
  model_path: string;
}

interface LMSStats {
  total_courses: number;
  total_enrollments: number;
  completed_enrollments: number;
  average_progress: number;
  completion_rate: number;
}

interface Enrollment {
  enrollment_id: string;
  course_id: string;
  title: string;
  progress_percent: number;
  status: string;
}

// === FUSION TEAM ROLE COMPONENTS ===

const FusionTeamDashboard = () => {
  const roles = [
    { role: 'XO', title: 'Fusion Operations Head', responsibilities: ['Coordinate fusion process', 'Track BDE deadlines', 'Manage paperwork workflow'] },
    { role: '420T', title: 'Trend Assessment', responsibilities: ['Monitor market trends', 'QC events', 'Performance validation'] },
    { role: 'MMA', title: 'Market & Message Analysis', responsibilities: ['Market intelligence', 'Competitor analysis', 'Future targeting'] },
    { role: 'S3', title: 'Schedule & Support', responsibilities: ['Manage calendar', 'Track assets/events', '30/60/90 planning'] },
    { role: 'ESS', title: 'Enlisted Source Strength', responsibilities: ['Track by CO', 'ALRL monitoring', 'Source analysis'] },
    { role: 'APA', title: 'Army Program Administrator', responsibilities: ['Event coordination', 'Paperwork mgmt', 'Budget tracking', 'EMM management'] },
  ];

  return (
    <div className="space-y-6 p-6">
      <h2 className="text-3xl font-bold text-gray-900">Fusion Team Structure & Roles</h2>
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {roles.map((r, i) => (
          <div key={i} className="bg-white p-6 rounded-lg shadow-lg border-l-4 border-blue-500">
            <div className="flex items-center mb-3">
              <div className="w-12 h-12 bg-blue-100 rounded-full flex items-center justify-center">
                <span className="font-bold text-blue-600">{r.role}</span>
              </div>
              <h3 className="ml-3 font-bold text-gray-900">{r.title}</h3>
            </div>
            <ul className="space-y-2">
              {r.responsibilities.map((resp, j) => (
                <li key={j} className="text-sm text-gray-600 flex items-start">
                  <ChevronRight className="w-4 h-4 mr-2 mt-0.5 flex-shrink-0 text-blue-500" />
                  {resp}
                </li>
              ))}
            </ul>
          </div>
        ))}
      </div>
    </div>
  );
};

// === MAIN DASHBOARD ===
const App = () => {
  const [activeTab, setActiveTab] = useState<'dashboard' | 'funnel' | 'events' | 'scoring' | 'fusion' | 'powerbi' | 'ai' | 'lms'>('dashboard');
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);
  const [funnelData, setFunnelData] = useState<FunnelStage[]>([]);
  const [kpiData, setKpiData] = useState<any>(null);
  const [loading, setLoading] = useState(false);

  // Fetch funnel data
  useEffect(() => {
    const fetchFunnelData = async () => {
      try {
        setLoading(true);
        const res = await apiClient.get('/funnel/stages');
        setFunnelData(res.data.stages || []);
      } catch (err) {
        console.error('Error fetching funnel:', err);
      } finally {
        setLoading(false);
      }
    };
    fetchFunnelData();
  }, []);

  // Fetch KPI data
  useEffect(() => {
    const fetchKpis = async () => {
      try {
        const res = await apiClient.get('/kpis');
        setKpiData(res.data);
      } catch (err) {
        console.error('Error fetching KPIs:', err);
      }
    };
    fetchKpis();
  }, []);

  const dashboardTabs = [
    { id: 'dashboard', label: 'Dashboard', icon: <BarChart3 /> },
    { id: 'funnel', label: 'Recruiting Funnel', icon: <TrendingUp /> },
    { id: 'events', label: 'Event Calendar', icon: <Calendar /> },
    { id: 'scoring', label: 'Lead Scoring', icon: <Cpu /> },
    { id: 'fusion', label: 'Fusion Team', icon: <Users /> },
    { id: 'powerbi', label: 'Power BI', icon: <PieChart /> },
    { id: 'ai', label: 'AI Pipeline', icon: <Activity /> },
    { id: 'lms', label: 'LMS', icon: <FileText /> },
  ];

  return (
    <div className="min-h-screen bg-gray-100">
      {/* Header */}
      <header className="bg-white shadow-md sticky top-0 z-20">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4 flex justify-between items-center">
          <h1 className="text-2xl font-bold text-gray-900">TAAIP 2.0</h1>
          <button
            onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
            className="lg:hidden p-2 rounded-md hover:bg-gray-100"
          >
            {mobileMenuOpen ? <X /> : <Menu />}
          </button>
        </div>
      </header>

      {/* Tab Navigation */}
      <nav className="bg-white border-b overflow-x-auto">
        <div className="max-w-7xl mx-auto px-4 flex space-x-1 sm:space-x-2">
          {dashboardTabs.map((tab) => (
            <button
              key={tab.id}
              onClick={() => { setActiveTab(tab.id as any); setMobileMenuOpen(false); }}
              className={`flex items-center px-3 py-3 text-sm font-medium whitespace-nowrap transition ${
                activeTab === tab.id
                  ? 'border-b-4 border-blue-600 text-blue-600'
                  : 'text-gray-600 hover:text-gray-900'
              }`}
            >
              {tab.icon}
              <span className="ml-1 hidden sm:inline">{tab.label}</span>
            </button>
          ))}
        </div>
      </nav>

      {/* Content */}
      <main className="max-w-7xl mx-auto p-6">
        {activeTab === 'dashboard' && <DashboardView kpiData={kpiData} loading={loading} />}
        {activeTab === 'funnel' && <FunnelView funnelData={funnelData} loading={loading} />}
        {activeTab === 'events' && <EventCalendarView />}
        {activeTab === 'scoring' && <LeadScoringView />}
        {activeTab === 'fusion' && <FusionTeamDashboard />}
        {activeTab === 'powerbi' && <PowerBIView />}
        {activeTab === 'ai' && <AIView />}
        {activeTab === 'lms' && <LMSView />}
      </main>
    </div>
  );
};

// === VIEW COMPONENTS ===

const DashboardView = ({ kpiData, loading }: any) => (
  <div className="space-y-6">
    <h2 className="text-3xl font-bold text-gray-900">Executive Dashboard</h2>
    {loading ? (
      <div className="text-center py-12"><RefreshCw className="w-8 h-8 animate-spin mx-auto" /></div>
    ) : (
      <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
        <div className="bg-white p-6 rounded-lg shadow">
          <p className="text-gray-600 text-sm">Total Cost</p>
          <p className="text-2xl font-bold text-blue-600">${kpiData?.total_cost?.toFixed(2) || 0}</p>
        </div>
        <div className="bg-white p-6 rounded-lg shadow">
          <p className="text-gray-600 text-sm">Cost Per Lead</p>
          <p className="text-2xl font-bold text-green-600">${kpiData?.cpl?.toFixed(2) || 0}</p>
        </div>
        <div className="bg-white p-6 rounded-lg shadow">
          <p className="text-gray-600 text-sm">Cost Per Engagement</p>
          <p className="text-2xl font-bold text-yellow-600">${kpiData?.cpe?.toFixed(2) || 0}</p>
        </div>
        <div className="bg-white p-6 rounded-lg shadow">
          <p className="text-gray-600 text-sm">Cost Per Conversion</p>
          <p className="text-2xl font-bold text-red-600">${kpiData?.cpc?.toFixed(2) || 0}</p>
        </div>
      </div>
    )}
  </div>
);

const FunnelView = ({ funnelData, loading }: any) => (
  <div className="space-y-6">
    <h2 className="text-3xl font-bold text-gray-900">USAREC Recruiting Funnel</h2>
    {loading ? (
      <div className="text-center py-12"><RefreshCw className="w-8 h-8 animate-spin mx-auto" /></div>
    ) : (
      <div className="bg-white p-6 rounded-lg shadow-lg">
        <ResponsiveContainer width="100%" height={400}>
          <BarChart data={funnelData}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis dataKey="stage" />
            <YAxis />
            <Tooltip />
            <Legend />
            <Bar dataKey="count" fill="#3b82f6" name="Count" />
            <Bar dataKey="conversionRate" fill="#10b981" name="Conversion %" />
          </BarChart>
        </ResponsiveContainer>
      </div>
    )}
  </div>
);

const EventCalendarView = () => (
  <div className="space-y-6">
    <h2 className="text-3xl font-bold text-gray-900">Event Calendar & Lead Capturing</h2>
    <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
      <div className="bg-white p-6 rounded-lg shadow-lg">
        <h3 className="text-xl font-bold mb-4">Upcoming Events</h3>
        <div className="space-y-3">
          {[
            { name: 'High School Career Fair', date: '2025-11-20', leads: 45 },
            { name: 'College Recruitment Drive', date: '2025-11-25', leads: 78 },
            { name: 'Sports Event Activation', date: '2025-12-01', leads: 32 },
          ].map((e, i) => (
            <div key={i} className="p-3 bg-blue-50 rounded-lg border-l-4 border-blue-500">
              <p className="font-semibold text-gray-900">{e.name}</p>
              <p className="text-sm text-gray-600">{e.date} • {e.leads} leads captured</p>
            </div>
          ))}
        </div>
      </div>
      <div className="bg-white p-6 rounded-lg shadow-lg">
        <h3 className="text-xl font-bold mb-4">Lead Capture Pipeline</h3>
        <div className="space-y-2 text-sm text-gray-600">
          <p>✓ QR Code scanning at events</p>
          <p>✓ Digital forms integration</p>
          <p>✓ Real-time lead validation</p>
          <p>✓ Auto-sync to CRM</p>
          <p>✓ Propensity scoring</p>
        </div>
      </div>
    </div>
  </div>
);

const LeadScoringView = () => (
  <div className="space-y-6">
    <h2 className="text-3xl font-bold text-gray-900">AI-Powered Lead Scoring</h2>
    <div className="bg-white p-6 rounded-lg shadow-lg">
      <p className="text-gray-600 mb-4">Tier 1 leads prioritized for immediate recruiter action</p>
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        {[
          { tier: 'Tier 1', count: 234, action: 'Call/Walk-In' },
          { tier: 'Tier 2', count: 567, action: 'Email/Text' },
          { tier: 'Tier 3', count: 890, action: 'Nurture Campaign' },
        ].map((t, i) => (
          <div key={i} className="p-6 bg-gradient-to-br from-blue-50 to-blue-100 rounded-lg">
            <p className="font-bold text-lg text-gray-900">{t.tier}</p>
            <p className="text-3xl font-bold text-blue-600">{t.count}</p>
            <p className="text-sm text-gray-600">{t.action}</p>
          </div>
        ))}
      </div>
    </div>
  </div>
);

const PowerBIView = () => (
  <div className="space-y-6">
    <h2 className="text-3xl font-bold text-gray-900">Power BI Integration</h2>
    <div className="bg-white p-6 rounded-lg shadow-lg">
      <div className="aspect-video bg-gray-200 rounded-lg flex items-center justify-center">
        <p className="text-gray-600">
          <iframe
            title="TAAIP KPI Dashboard"
            src="https://app.powerbi.com/view?r=eyJrIjoiYWJjZGVmZ2hpamtsbW5vcCIsInQiOiJhYmNkZWZnIn0%3D"
            frameBorder="0"
            allowFullScreen
            width="100%"
            height="100%"
            className="rounded-lg"
          />
        </p>
      </div>
      <p className="text-sm text-gray-500 mt-4">Configure Power BI embedding in settings. Add service principal credentials for authentication.</p>
    </div>
  </div>
);

const AIView: React.FC = () => {
  const [modelStatus, setModelStatus] = useState<ModelStatus | null>(null);
  const [loading, setLoading] = useState(false);
  const [training, setTraining] = useState(false);
  const [message, setMessage] = useState('');

  useEffect(() => {
    fetchModelStatus();
  }, []);

  const fetchModelStatus = async () => {
    try {
      setLoading(true);
      const res = await apiClient.get('/ai/model-status');
      setModelStatus(res.data.model);
    } catch (err) {
      console.error('Error fetching model status:', err);
      setMessage('Failed to fetch model status');
    } finally {
      setLoading(false);
    }
  };

  const triggerTraining = async () => {
    try {
      setTraining(true);
      setMessage('Training model...');
      const res = await apiClient.post('/ai/train', {});
      setMessage(`✓ Model trained: ${res.data.accuracy}% accuracy on ${res.data.training_samples} samples`);
      await fetchModelStatus();
    } catch (err) {
      setMessage('Failed to train model: ' + (err as any).message);
    } finally {
      setTraining(false);
    }
  };

  return (
    <div className="space-y-6">
      <h2 className="text-3xl font-bold text-gray-900">AI Predictive Pipeline</h2>
      {loading ? (
        <div className="text-center py-12"><RefreshCw className="w-8 h-8 animate-spin mx-auto" /></div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <div className="bg-white p-6 rounded-lg shadow-lg">
            <h3 className="text-xl font-bold mb-4">Model Status</h3>
            <div className="space-y-3">
              <div className="flex items-center justify-between p-3 bg-green-50 rounded-lg">
                <span>Training Data</span>
                <span className="text-green-600 font-bold">{modelStatus?.training_samples?.toLocaleString() || '0'} records</span>
              </div>
              <div className="flex items-center justify-between p-3 bg-green-50 rounded-lg">
                <span>Model Accuracy</span>
                <span className="text-green-600 font-bold">{((modelStatus?.accuracy || 0) * 100).toFixed(1)}%</span>
              </div>
              <div className="flex items-center justify-between p-3 bg-yellow-50 rounded-lg">
                <span>Last Trained</span>
                <span className="text-yellow-600">{modelStatus?.last_updated ? new Date(modelStatus.last_updated).toLocaleDateString() : 'Never'}</span>
              </div>
            </div>
          </div>
          <div className="bg-white p-6 rounded-lg shadow-lg">
            <h3 className="text-xl font-bold mb-4">Training Controls</h3>
            <p className="text-gray-600 mb-4">Retrain on historical lead data</p>
            <button 
              onClick={triggerTraining}
              disabled={training}
              className="w-full bg-blue-600 text-white py-2 rounded-lg hover:bg-blue-700 disabled:opacity-50"
            >
              {training ? 'Training...' : 'Trigger Retraining'}
            </button>
            {message && (
              <p className="text-sm mt-4 p-3 bg-blue-50 text-blue-700 rounded-lg">{message}</p>
            )}
          </div>
        </div>
      )}
    </div>
  );
};

const LMSView: React.FC = () => {
  const [courses, setCourses] = useState<any[]>([]);
  const [stats, setStats] = useState<LMSStats | null>(null);
  const [loading, setLoading] = useState(false);
  const [selectedUser, setSelectedUser] = useState('');
  const [userEnrollments, setUserEnrollments] = useState<Enrollment[]>([]);

  useEffect(() => {
    fetchLMSData();
  }, []);

  const fetchLMSData = async () => {
    try {
      setLoading(true);
      const [coursesRes, statsRes] = await Promise.all([
        apiClient.get('/lms/courses'),
        apiClient.get('/lms/stats')
      ]);
      setCourses(coursesRes.data.courses || []);
      setStats(statsRes.data.stats || {});
    } catch (err) {
      console.error('Error fetching LMS data:', err);
    } finally {
      setLoading(false);
    }
  };

  const fetchUserEnrollments = async (userId: string) => {
    if (!userId) return;
    try {
      const res = await apiClient.get(`/lms/enrollments/${userId}`);
      setUserEnrollments(res.data.enrollments || []);
    } catch (err) {
      console.error('Error fetching enrollments:', err);
    }
  };

  const handleUserChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const userId = e.target.value;
    setSelectedUser(userId);
    fetchUserEnrollments(userId);
  };

  return (
    <div className="space-y-6">
      <h2 className="text-3xl font-bold text-gray-900">Learning Management System</h2>
      
      {loading ? (
        <div className="text-center py-12"><RefreshCw className="w-8 h-8 animate-spin mx-auto" /></div>
      ) : (
        <>
          {/* LMS Stats */}
          <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-6">
            <div className="bg-white p-6 rounded-lg shadow">
              <p className="text-gray-600 text-sm">Total Courses</p>
              <p className="text-2xl font-bold text-blue-600">{stats?.total_courses || 0}</p>
            </div>
            <div className="bg-white p-6 rounded-lg shadow">
              <p className="text-gray-600 text-sm">Total Enrollments</p>
              <p className="text-2xl font-bold text-green-600">{stats?.total_enrollments || 0}</p>
            </div>
            <div className="bg-white p-6 rounded-lg shadow">
              <p className="text-gray-600 text-sm">Completed</p>
              <p className="text-2xl font-bold text-yellow-600">{stats?.completed_enrollments || 0}</p>
            </div>
            <div className="bg-white p-6 rounded-lg shadow">
              <p className="text-gray-600 text-sm">Completion Rate</p>
              <p className="text-2xl font-bold text-red-600">{((stats?.completion_rate || 0) * 100).toFixed(1)}%</p>
            </div>
          </div>

          {/* Available Courses */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <div className="bg-white p-6 rounded-lg shadow-lg">
              <h3 className="text-xl font-bold mb-4">Available Courses</h3>
              <div className="space-y-3">
                {courses.map((course, i) => (
                  <div key={i} className="p-4 bg-gray-50 rounded-lg border-l-4 border-blue-500">
                    <p className="font-semibold text-gray-900">{course.title}</p>
                    <p className="text-sm text-gray-600">{course.description}</p>
                  </div>
                ))}
              </div>
            </div>

            {/* User Enrollments */}
            <div className="bg-white p-6 rounded-lg shadow-lg">
              <h3 className="text-xl font-bold mb-4">User Enrollments</h3>
              <input
                type="text"
                placeholder="Enter user ID (e.g., user_001)"
                value={selectedUser}
                onChange={handleUserChange}
                className="w-full px-4 py-2 border rounded-lg mb-4 focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
              <div className="space-y-3">
                {userEnrollments.length > 0 ? (
                  userEnrollments.map((e, i) => (
                    <div key={i} className="p-3 bg-blue-50 rounded-lg">
                      <p className="font-semibold text-gray-900">{e.title}</p>
                      <div className="w-full bg-gray-200 rounded-full h-2 my-2">
                        <div className="bg-green-600 h-2 rounded-full" style={{ width: `${e.progress_percent}%` }} />
                      </div>
                      <p className="text-sm text-gray-600">{e.progress_percent}% • {e.status}</p>
                    </div>
                  ))
                ) : (
                  <p className="text-gray-600 text-sm">Enter a user ID to see enrollments</p>
                )}
              </div>
            </div>
          </div>
        </>
      )}
    </div>
  );
};

export default App;
